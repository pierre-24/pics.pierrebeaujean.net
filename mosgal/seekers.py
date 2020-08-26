import pathlib
from typing import Iterable
from PIL import Image as PILImage
import re

from mosgal.base_models import BaseFile


class Image(BaseFile):
    """Extension of ``File`` to handle PIL object.
    """

    def __init__(self, source_path: pathlib.Path):
        super().__init__(source_path)
        self.pil_object = None

    def open_PIL(self) -> None:
        """Open the PIL object"""
        self.pil_object = PILImage.open(self.final_path)

    def close_PIL(self) -> None:
        """Close the PIL object"""
        self.pil_object.close()
        self.pil_object = None

    def opened(self) -> bool:
        """

        :return: True if the PIL object is opened, False otherwise
        """
        return self.pil_object is None


class ImageSeeker:
    """
    Seek for files in a given directory (and all subdirectories), and select them based on their extension
    """

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
