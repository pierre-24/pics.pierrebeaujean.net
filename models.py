import pathlib
from typing import Iterable, Callable
from PIL import Image as PILImage, ExifTags
import re

from base_models import BaseTransformer, BaseFile


class Image(BaseFile):
    def __init__(self, source_path: pathlib.Path):
        super().__init__(source_path)
        self.pil_object = None

        self.other_path = {}

    def open_PIL(self) -> None:
        self.pil_object = PILImage.open(self.final_path)

    def close_PIL(self) -> None:
        self.pil_object.close()
        self.pil_object = None

    def opened(self) -> bool:
        return self.pil_object is None


# seeker
class FileSeeker:
    def __init__(self, directory: pathlib.Path, extensions: Iterable[str] = (), exclude: Iterable[str] = ()):
        self.directory = directory
        self.extensions = extensions
        self.exclude = exclude

    def __call__(self, *args, **kwargs):
        r = re.compile(r'.*\.({})'.format('|'.join(self.extensions)))

        for fname in self.directory.glob('**/*.*'):
            sfname = str(fname)

            if any(e in sfname for e in self.exclude):
                continue

            if r.match(sfname):
                yield Image(fname)


# Transformers
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


class OpenPILImage(BaseTransformer):
    def __call__(self, file: Image, *args, **kwargs) -> None:
        file.open_PIL()


class ClosePILImage(BaseTransformer):
    def __call__(self, file: Image, *args, **kwargs) -> None:
        file.close_PIL()


class Resize(BaseTransformer):
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

            file.other_path[self.suffix] = path
