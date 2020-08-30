from typing import Callable, Iterable
import io
import datetime

from PIL import ExifTags
from PIL.TiffImagePlugin import IFDRational
from colorthief import ColorThief

from mosgal.base_models import BaseTransformer, BaseFile
from mosgal.seekers import Image


class TransformIf(BaseTransformer):
    def __init__(
            self, test: Callable, if_true: Iterable[BaseTransformer] = (), if_false: Iterable[BaseTransformer] = ()):

        super().__init__()

        self.test = test
        self.if_true = if_true
        self.if_false = if_false

    def __call__(self, file: BaseFile, *args, **kwargs) -> None:
        transformers = self.if_true if self.test(file) else self.if_false
        for transform in transformers:
            transform(file)


class WithPIL(BaseTransformer):
    """Make everything ensuring that the PIL object is opened in the beginning (and closed in the end)
    """
    def __init__(self, transformers: Iterable[BaseTransformer] = ()):
        super().__init__()

        self.transformers = transformers

    def __call__(self, file: Image, *args, **kwargs) -> None:
        file.open_PIL()
        for transform in self.transformers:
            transform(file)

        file.close_PIL()


class Resize(BaseTransformer):
    """
    Resize the base image if its width (height) is larger than ``max_width`` (``max_height``).
    Image ratio is conserved.
    """

    def __init__(
            self,
            max_width: int,
            max_height: int,
            suffix='x',
            encoder_options: dict = {'quality': 85, 'optimize': True},
            keep_exif: bool = True):

        super().__init__()

        self.max_width = max_width
        self.max_height = max_height
        self.encoder_options = encoder_options
        self.keep_exif = keep_exif  # TODO: only keep SOME exif data?
        self.suffix = suffix

    def __call__(self, file: Image, *args, **kwargs) -> None:
        size = file.pil_object.size
        exif_rotated = file.pil_object._getexif()[0x0112] != 1  # take into account EXIF "rotation" tag

        if exif_rotated:
            size = size[1], size[0]

        is_portrait = size[0] > size[1]

        if (is_portrait and size[0] <= self.max_width) or (not is_portrait and size[1] <= self.max_height):
            file.resized_path = file.path

        else:
            if is_portrait:
                new_size = self.max_width, int(size[1] / size[0] * self.max_width)
            else:
                new_size = int(size[0] / size[1] * self.max_height), self.max_height

            if exif_rotated:
                new_size = new_size[1], new_size[0]

            i = file.pil_object.resize(new_size)
            path = file.path.with_suffix('.{}.JPG'.format(self.suffix))

            i.save(
                path, 'JPEG',
                **self.encoder_options,
                exif=file.pil_object.info['exif'] if self.keep_exif else b'')

            file.attributes['resized_' + self.suffix] = str(path)


class ResizeMaxWidth(BaseTransformer):
    """
    Resize the base image if its width is larger than ``max_width``.
    Image ratio is conserved.
    """

    def __init__(
            self,
            max_width: int,
            suffix='x',
            encoder_options: dict = {'quality': 85, 'optimize': True},
            keep_exif: bool = True):

        super().__init__()

        self.max_width = max_width
        self.encoder_options = encoder_options
        self.keep_exif = keep_exif  # TODO: only keep SOME exif data?
        self.suffix = suffix

    def __call__(self, file: Image, *args, **kwargs) -> None:
        size = file.pil_object.size
        exif_rotated = file.pil_object._getexif()[0x0112] != 1  # take into account EXIF "rotation" tag

        if exif_rotated:
            size = size[1], size[0]

        if size[0] <= self.max_width:
            file.resized_path = file.path

        else:
            new_size = self.max_width, int(size[1] / size[0] * self.max_width)

            if exif_rotated:
                new_size = new_size[1], new_size[0]

            i = file.pil_object.resize(new_size)
            path = file.path.with_suffix('.{}.JPG'.format(self.suffix))

            i.save(
                path, 'JPEG',
                **self.encoder_options,
                exif=file.pil_object.info['exif'] if self.keep_exif else b'')

            file.attributes['resized_' + self.suffix] = str(path)


class Thumbnail(BaseTransformer):
    """
    Thumbnail base image.
    Ensure that the image will have exactly the specified size, by resizing then cropping the original one.
    """

    def __init__(
            self,
            width: int,
            height: int,
            suffix='x',
            encoder_options: dict = {'quality': 75, 'optimize': True}):

        super().__init__()

        self.width = width
        self.height = height
        self.ratio = width / height
        self.encoder_options = encoder_options
        self.suffix = suffix

    def __call__(self, file: Image, *args, **kwargs) -> None:
        # rotate file based on the exif tag, if any
        rot = file.pil_object._getexif()[0x0112]
        rotate = {3: 180, 6: 270, 8: 90}

        if rot in rotate:
            image = file.pil_object.rotate(rotate[rot], expand=True)
        else:
            image = file.pil_object

        # get the new size and resize
        size = image.size
        ratio = size[0] / size[1]

        if ratio > self.ratio:  # then the height is used
            new_size = int(self.height * ratio), self.height
        else:
            new_size = self.width, int(self.width / ratio)

        image = image.resize(new_size)

        # crop
        if ratio > self.ratio:
            offset = int((new_size[0] - self.width) / 2)
            crop = (offset, 0, offset + self.width, self.height)
        else:
            offset = int((new_size[1] - self.height) / 2)
            crop = (0, offset, self.width, offset + self.height)

        image = image.crop(crop)

        # save
        path = file.path.with_suffix('.{}.JPG'.format(self.suffix))

        image.save(path, 'JPEG', **self.encoder_options)
        file.attributes['thumbnail_' + self.suffix] = str(path)


class AddExifAttributes:
    """Add some EXIF data to attributes
    """

    EXIF_TAGS = [
        'ExposureTime', 'FNumber', 'Make', 'Model', 'ISOSpeedRatings', 'FocalLength'
    ]

    def __init__(self, which: Iterable[str] = EXIF_TAGS):
        self.which = which

    def __call__(self, file: Image, *args, **kwargs) -> None:
        data = {
            ExifTags.TAGS[k]: float(v) if type(v) is IFDRational else v
            for k, v in file.pil_object.getexif().items()
            if k in ExifTags.TAGS and ExifTags.TAGS[k] in self.which
        }

        exposure = '{:n}s'.format(
            data['ExposureTime']) if data['ExposureTime'] > 1 else '1/{:n}s'.format(1 / data['ExposureTime'])

        data['characteristics'] = '{} @ {}nm, ISO {}, {}, f/{}'.format(
            data['Model'], data['FocalLength'], data['ISOSpeedRatings'], exposure, data['FNumber']
        )

        file.attributes.update(**data)


class AddDominantColorsAttribute(BaseTransformer):
    """
    Determine the dominant color, based on a reduced 150x150 version
    of the image. Get the name based on the CSS colors.
    """

    # TODO: a custom palette would do a better job here, I think

    PALETTE = {
        # RGB pure
        'red': (255, 0, 0),
        'green': (0, 255, 0),
        'blue': (0, 0, 255),
        'black': (0, 0, 0),
        # mixes
        'yellow': (255, 255, 0),
        'cyan': (0, 255, 255),
        'pink': (255, 0, 255),
        'white': (255, 255, 255),
        # half-tones
        'maroon': (128, 0, 0),
        'darkgreen': (0, 128, 0),
        'navy': (0, 0, 128),
        # half-tones mixes
        'teal': (0, 128, 128),
        'olive': (128, 128, 0),
        'purple': (128, 0, 128),
        'gray': (128, 128, 128),
        # extra grays
        'darkgray': (75, 75, 75),
        'lightgray': (192, 192, 192),
        # extra colors:
        'orange': (255, 128, 0),
        'deeppink': (255, 0, 128),
        'springgreen': (0, 255, 128),
        'turquoise': (64, 224, 208),
        'indigo': (75, 0, 130),
        'brown': (210, 105, 30),
        'deepblue': (70, 100, 180),
    }

    def __init__(self, color_count: int = 10, quality: int = 10, color_source: dict = PALETTE, im_size=150):
        super().__init__()

        self.color_count = color_count
        self.quality = quality
        self.color_source = color_source
        self.im_size = im_size

    def _find_closest(self, r: int, g: int, b: int) -> str:
        min_colours = {}
        for name, colour in self.color_source.items():
            r_c, g_c, b_c = colour
            rd = (r_c - r) ** 2
            gd = (g_c - g) ** 2
            bd = (b_c - b) ** 2
            min_colours[(rd + gd + bd)] = name
        return min_colours[min(min_colours.keys())]

    def __call__(self, file: Image, *args, **kwargs) -> None:

        sz = file.pil_object.size
        ratio = sz[0] / sz[1]
        sz_dim = (int(self.im_size * ratio), self.im_size) if ratio < 1 else (self.im_size, int(self.im_size/ratio))

        im = file.pil_object.resize(sz_dim)
        f = io.BytesIO()
        im.save(f, 'JPEG')

        palette = ColorThief(f).get_palette(
            color_count=self.color_count, quality=self.quality)[:self.color_count]

        dominants = list((c, self._find_closest(*c)) for c in palette)
        file.attributes['dominant_color_names'] = list(set(c[1] for c in dominants))
        file.attributes['dominant_colors'] = ['#{:02X}{:02X}{:02X}'.format(*c[0]) for c in dominants]


class AddDirectoryNameAttribute:
    """Add the parent directory as an attribute (``parent_directory``)
    """

    def __call__(self, file: Image, *args, **kwargs) -> None:
        file.attributes['parent_directory'] = file.path.parts[-2]


class AddMonthYearAttribute:
    """
    Add the date taken (``date_taken`` attribute) from the ``DateTimeOriginal`` EXIF tag,
    and extract a ``month_year`` attribute out of it.
    """

    def __call__(self, file: Image, *args, **kwargs) -> None:
        dt = file.pil_object.getexif()[0x9003]
        file.attributes['date_taken'] = dt
        file.attributes['month_year'] = datetime.datetime.strptime(dt, '%Y:%m:%d %H:%M:%S').strftime('%B %Y')


class AddFocalClassAttribute:
    """Add a ``focal_class`` attribute, that cast the (35mm film equivalent) focal length into a
    "large" (< 40), "normal" (40-100) or "zoom" (> 100) class.
    """

    def __call__(self, file: Image, *args, **kwargs) -> None:
        f_length = file.pil_object.getexif()[0xA405]
        file.attributes['focal_class'] = 'large' if f_length < 40 else 'normal' if f_length < 100 else 'zoom'
