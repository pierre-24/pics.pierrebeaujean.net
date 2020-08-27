from typing import Iterable
import pathlib

from mosgal.base_models import BaseTransformer, BaseFile, BaserWriter, Collection
from mosgal.seekers import ImageSeeker
from mosgal.transformers import WithPIL, Resize, AddExifAttribute, ResizeMaxWidth, AddDominantColorsAttribute, \
    AddDirectoryNameAttribute, AddMonthYearAttribute, AddOrientationAttribute
from mosgal.classifiers import AttributeClassifier
from mosgal.pipelines import simple_pipeline


class Logger(BaseTransformer):
    def __init__(self, show_attributes: bool = False):
        super().__init__()

        self.show_attributes = show_attributes

    def __call__(self, f: BaseFile, *args, **kwargs):
        print(f.source_path)

        if self.show_attributes:
            for k, v in f.attributes.items():
                print('  -', k, ':', v)


class Wri(BaserWriter):
    def __call__(self, collections: Iterable[Collection], *args, **kwargs) -> None:
        for c in collections:
            print(c.name)
            for e in c.elements:
                print('-', e.name, list(i.source_path for i in e.files))


if __name__ == '__main__':
    pipeline = simple_pipeline(
        seek=ImageSeeker(
            pathlib.Path('pictures'),
            extensions=['jpg', 'JPG', 'jpeg', 'JPEG'],
            exclude=['.rs.JPG', '.th.JPG'],
        ),
        transformers=[
            WithPIL([
                Resize(750, 500, suffix='rs'),  # resized image (ratio=4:3)
                ResizeMaxWidth(300, suffix='th'),  # thumbnail (width=300px)
                AddExifAttribute(),
                AddDominantColorsAttribute(),
                AddDirectoryNameAttribute(),
                AddMonthYearAttribute(),
                AddOrientationAttribute(),
            ]),
            Logger(),
        ],
        classifiers=[
            AttributeClassifier('parent_directory', name='Albums'),
            AttributeClassifier('month_year', name='Date'),
            AttributeClassifier('orientation', name='Orientation'),
            AttributeClassifier('dominant_color_names', name='Colors', exclude=['lightgray', 'darkgray'])
        ],
        writers=[
            Wri()
        ]
    )

    pipeline()
