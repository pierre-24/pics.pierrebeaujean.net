from typing import Callable, Iterable
import io
import datetime

import colorsys

from PIL import ExifTags, Image as PILImage
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


def base_target_name(file: Image, target_attribute: str, suffix: str, file_format: str):
    return 'images/{}_{}.{}'.format(file.path.stem, suffix, file_format)


class BaseImageTransform(BaseTransformer):
    """Base image transformer"""

    def __init__(
            self,
            target_attribute: str = 'transformed',
            suffix: str = 'x',
            name_target: Callable = base_target_name,
            output_format: str = 'JPEG',
            encoder_options: dict = {'quality': 85},
            keep_exif: bool = True
    ):
        super().__init__()

        self.target_attribute = target_attribute
        self.suffix = suffix
        self.output_format = output_format
        self.encoder_options = encoder_options
        self.keep_exif = keep_exif
        self.name_target = name_target

    def transform(self, file: Image) -> PILImage:
        raise NotImplementedError()

    def __call__(self, file: Image, *args, **kwargs) -> None:
        image = self.transform(file)
        path = file.path.with_suffix('.{}.{}'.format(self.suffix, self.output_format))

        image.save(
            path,
            self.output_format,
            **self.encoder_options,
            exif=file.pil_object.info['exif'] if self.keep_exif else b'')

        file.attributes[self.target_attribute + '_' + self.suffix] = str(path)
        file.attributes[self.target_attribute + '_' + self.suffix + '_target'] = str(
            self.name_target(file, self.target_attribute, self.suffix, self.output_format))


class Resize(BaseImageTransform):
    """
    Resize the base image if its width (height) is larger than ``max_width`` (``max_height``).
    Image ratio is conserved.
    """

    def __init__(
            self,
            max_width: int = -1,
            max_height: int = -1,
            suffix='x',
            name_target: Callable = base_target_name,
            encoder_options: dict = {'quality': 85, 'optimize': True},
            keep_exif: bool = True):

        super().__init__(
            suffix=suffix,
            target_attribute='resized',
            encoder_options=encoder_options,
            keep_exif=keep_exif,
            name_target=name_target)

        self.max_width = max_width
        self.max_height = max_height

    def transform(self, file: Image) -> PILImage:

        size = file.pil_object.size
        exif_rotated = file.pil_object._getexif()[0x0112] in [3, 6, 8]  # take into account EXIF "rotation" tag

        if exif_rotated:
            size = size[1], size[0]

        new_size = (-1, -1)
        new_size_w = self.max_width, int(size[1] / size[0] * self.max_width)
        new_size_h = int(size[0] / size[1] * self.max_height), self.max_height
        resize = True

        is_portrait = size[0] > size[1]

        if (self.max_height < 0 or is_portrait) and size[0] > self.max_width:
            new_size = new_size_w
        elif (self.max_width < 0 or not is_portrait) and size[1] > self.max_height:
            new_size = new_size_h
        else:
            resize = False

        if resize:
            if exif_rotated:
                new_size = new_size[1], new_size[0]

            return file.pil_object.resize(new_size)
        else:
            return file.pil_object


class Thumbnail(BaseImageTransform):
    """
    Thumbnail base image.
    Ensure that the image will have exactly the specified size, by resizing then cropping the original one.
    """

    def __init__(
            self,
            width: int,
            height: int,
            suffix='x',
            name_target: Callable = base_target_name,
            encoder_options: dict = {'quality': 75, 'optimize': True},
    ):

        super().__init__(
            name_target=name_target,
            target_attribute='thumbnail',
            encoder_options=encoder_options,
            suffix=suffix,
            keep_exif=False)

        self.width = width
        self.height = height
        self.ratio = width / height

    def transform(self, file: Image) -> PILImage:
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

        return image.crop(crop)


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


def rgb_to_hsv(r: int, g: int, b: int) -> tuple:
    """Convert an RGB color (from 0 to 255) to HSV equivalent (from 0 to 1)
    """
    return colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)


class AddDominantColorsAttribute(BaseTransformer):
    """
    Determine the dominant color, based on a reduced 150x150 version
    of the image. Get the name based on the CSS colors.
    """

    PALETTE = {
        # RGB pure
        'redish': (
            rgb_to_hsv(255, 0, 0),
            rgb_to_hsv(128, 0, 0),  # maroon
            rgb_to_hsv(210, 105, 30),  # brown
        ),
        'greenish': (
            rgb_to_hsv(0, 255, 0),
            rgb_to_hsv(0, 128, 0),  # dark green
            rgb_to_hsv(128, 128, 0),  # olive
            rgb_to_hsv(0, 255, 128),  # spring green
            rgb_to_hsv(75, 0, 130),  # indigo
        ),
        'blueish': (
            rgb_to_hsv(0, 0, 255),
            rgb_to_hsv(0, 255, 255),  # cyan
            rgb_to_hsv(0, 0, 128),  # navy
            rgb_to_hsv(0, 128, 128),  # teal
            rgb_to_hsv(64, 224, 208),  # turquoise
            rgb_to_hsv(70, 100, 180),  # deep blue
        ),
        'grayish': (
            rgb_to_hsv(128, 128, 128),
            rgb_to_hsv(75, 75, 75),
            rgb_to_hsv(75, 75, 75),
        ),
        'pink': (
            rgb_to_hsv(255, 0, 255),
            rgb_to_hsv(255, 0, 128),  # deep pink
            rgb_to_hsv(128, 0, 128),  # purple
        ),
        # few extra colors:
        'black': (
            rgb_to_hsv(0, 0, 0),
        ),
        'yellow': (
            rgb_to_hsv(255, 255, 0),
        ),
        'white': (
            rgb_to_hsv(255, 255, 255),
        ),
        'orange': (
            rgb_to_hsv(255, 128, 0),
        ),
    }

    def __init__(
            self,
            color_count: int = 10,
            reduced_to: int = 5,
            quality: int = 5,
            color_source: dict = PALETTE,
            im_size: int = 250):
        super().__init__()

        self.color_count = color_count
        self.quality = quality
        self.reduce_to = reduced_to
        self.color_source = color_source
        self.im_size = im_size

    def _find_closest(self, r: int, g: int, b: int) -> str:
        min_colors = {}
        h, s, v = rgb_to_hsv(r, g, b)
        for name, colors in self.color_source.items():
            for color in colors:
                min_colors[sum((x - y) ** 2 for x, y in zip(color, (h, s, v)))] = name
        return min_colors[min(min_colors.keys())]

    def __call__(self, file: Image, *args, **kwargs) -> None:

        sz = file.pil_object.size
        ratio = sz[0] / sz[1]
        sz_dim = (int(self.im_size * ratio), self.im_size) if ratio < 1 else (self.im_size, int(self.im_size/ratio))

        im = file.pil_object.resize(sz_dim)
        f = io.BytesIO()
        im.save(f, 'JPEG')

        palette = ColorThief(f).get_palette(
            color_count=self.color_count, quality=self.quality)[:self.reduce_to]

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
    "large" (<= 40), "normal" (40-100) or "zoom" (>= 100) class.
    """

    classes = {
        'large': (0, 40),
        'normal': (40, 100),
        'zoom': (100, 5000)
    }

    def __call__(self, file: Image, *args, **kwargs) -> None:
        f_length = file.pil_object.getexif()[0xA405]

        for c, l in self.classes:
            if l[0] <= f_length <= l[1]:
                file.attributes['focal_class'] = c
