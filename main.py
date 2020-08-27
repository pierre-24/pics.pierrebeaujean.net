import pathlib

from mosgal.base_models import BaseTransformer, BaseFile, BaserWriter, Collection
from mosgal.seekers import ImageSeeker
from mosgal.transformers import WithPIL, Resize, AddExifAttribute, ResizeMaxWidth, AddDominantColorsAttribute, \
    AddDirectoryNameAttribute, AddMonthYearAttribute, AddOrientationAttribute
from mosgal.classifiers import AttributeClassifier
from mosgal.writers import BuildDirectory, WriteIndex
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


if __name__ == '__main__':
    pipeline = simple_pipeline(
        pathlib.Path('./html'),
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
        organizer=lambda l: sorted(l, key=lambda k: k.attributes['date_taken']),
        classifiers=[
            AttributeClassifier('parent_directory', name='Albums'),
            AttributeClassifier('month_year', name='Date'),
            AttributeClassifier('orientation', name='Orientation'),
            AttributeClassifier('dominant_color_names', name='Colors', exclude=['lightgray', 'darkgray'])
        ],
        writers=[
            BuildDirectory(pathlib.Path('./_build'), writers=[
                WriteIndex(),
            ])
        ]
    )

    pipeline()
