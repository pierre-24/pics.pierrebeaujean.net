import pathlib

from mosgal.base_models import BaseTransformer, BaseFile
from mosgal.seekers import ImageSeeker
from mosgal.transformers import WithPIL, Resize, AddExifData, Thumbnail, DominantColors
from mosgal.pipelines import simple_pipeline


class Logger(BaseTransformer):
    def __call__(self, f: BaseFile, *args, **kwargs):
        print(f.source_path)
        for k, v in f.attributes.items():
            print('  -', k, ':', v)


if __name__ == '__main__':
    pipeline = simple_pipeline(
        seek=ImageSeeker(
            pathlib.Path('pictures'),
            extensions=['jpg', 'JPG', 'jpeg', 'JPEG'],
            exclude=['.rs.JPG', '.th.JPG']
        ),
        transformers=[
            WithPIL([
                # AddExifData(),
                Resize(750, 500, suffix='rs'),  # resized image (ratio=4:3)
                Thumbnail(150, 150, suffix='th'),  # thumbnail image (ratio=1:1)
                DominantColors()
            ]),
            Logger()
        ]
    )

    pipeline()
