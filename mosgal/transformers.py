from typing import Callable, Iterable
import io
import webcolors

from PIL import ExifTags
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
    """Make everything ensuring that the PIL object is opened in the begining (and closed in the end)
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
            file.resized_path = file.final_path

        else:
            if is_portrait:
                new_size = self.max_width, int(size[1] / size[0] * self.max_width)
            else:
                new_size = int(size[0] / size[1] * self.max_height), self.max_height

            if exif_rotated:
                new_size = new_size[1], new_size[0]

            i = file.pil_object.resize(new_size)
            path = file.final_path.with_suffix('.{}.JPG'.format(self.suffix))

            i.save(
                path, 'JPEG',
                **self.encoder_options,
                exif=file.pil_object.info['exif'] if self.keep_exif else b'')

            file.attributes['resized_' + self.suffix] = path


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
        path = file.final_path.with_suffix('.{}.JPG'.format(self.suffix))

        image.save(path, 'JPEG', **self.encoder_options)
        file.attributes['thumbnail_' + self.suffix] = path


class AddExifData:
    """Add EXIF data (as ``exif``) to attributes
    """

    def __call__(self, file: Image, *args, **kwargs) -> None:
        file.attributes['exif'] = {
            ExifTags.TAGS[k]: v
            for k, v in file.pil_object.getexif().items()
            if k in ExifTags.TAGS
        }


class DominantColors(BaseTransformer):
    """
    Determine the dominant color, based on a reduced 150x150 version
    of the image. Get the name based on the CSS colors.
    """

    # TODO: a custom palette would do a better job here, I think

    def __init__(self, color_count: int = 5, quality: int = 5, color_source: dict = webcolors.CSS21_HEX_TO_NAMES):
        super().__init__()

        self.color_count = color_count
        self.quality = quality
        self.color_source = color_source

    def _find_closest(self, r: int, g: int, b: int) -> str:
        min_colours = {}
        for key, name in self.color_source.items():
            r_c, g_c, b_c = webcolors.hex_to_rgb(key)
            rd = (r_c - r) ** 2
            gd = (g_c - g) ** 2
            bd = (b_c - b) ** 2
            min_colours[(rd + gd + bd)] = name
        return min_colours[min(min_colours.keys())]

    def __call__(self, file: Image, *args, **kwargs) -> None:

        im = file.pil_object.resize((150, 150))
        f = io.BytesIO()
        im.save(f, 'PNG')

        palette = ColorThief(f).get_palette(
            color_count=self.color_count + 3, quality=self.quality)[:self.color_count]

        file.attributes['dominant_colors'] = list((c, self._find_closest(*c)) for c in palette)
        file.attributes['dominant_color_names'] = list(set(c[1] for c in file.attributes['dominant_colors']))
