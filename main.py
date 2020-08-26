import pathlib

from base_models import BaseTransformer, BaseFile
from models import FileSeeker, Resize, OpenPILImage, ClosePILImage
from maker import make


class Printer(BaseTransformer):
    def __call__(self, f: BaseFile, *args, **kwargs):
        print(f.source_path)


if __name__ == '__main__':
    make(
        seek=FileSeeker(
            pathlib.Path('pictures'),
            extensions=['jpg', 'JPG', 'jpeg', 'JPEG'],
            exclude=['.rs.JPG', '.th.JPG']
        ),
        transformers=[
            Printer(),
            OpenPILImage(),
            Resize(750, 500, suffix='rs'),  # resized image (ratio=4:3)
            Resize(150, 150, suffix='th'),  # thumbnail image (ratio=1:1)
            ClosePILImage()
        ]
    )
