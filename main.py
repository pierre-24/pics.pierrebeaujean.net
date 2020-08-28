import pathlib

from mosgal.base_models import BaseTransformer, BaseFile
from mosgal.seekers import ImageSeeker
from mosgal.transformers import WithPIL, Resize, AddExifAttribute, ResizeMaxWidth, AddDominantColorsAttribute, \
    AddDirectoryNameAttribute, AddMonthYearAttribute, AddOrientationAttribute, TransformIf
from mosgal.classifiers import AttributeClassifier
from mosgal.writers import BuildDirectory, WriteIndex
from mosgal.pipelines import simple_pipeline

from mosgal.ext.database import ImageDB, AddToImageDB, UpdateFromImageDB, WriteImageDB


class Logger(BaseTransformer):
    def __init__(self, show_attributes: bool = False):
        super().__init__()

        self.show_attributes = show_attributes

    def __call__(self, f: BaseFile, *args, **kwargs):
        print(f.source)

        if self.show_attributes:
            for k, v in f.attributes.items():
                print('  -', k, ':', v)


if __name__ == '__main__':

    db = ImageDB()

    db_path = pathlib.Path('./images.json')
    if db_path.exists():
        with db_path.open() as f:
            db.load(f)

    pipeline = simple_pipeline(
        pathlib.Path('./html'),
        seek=ImageSeeker(
            pathlib.Path('pictures'),
            extensions=['jpg', 'JPG', 'jpeg', 'JPEG'],
            exclude=['.rs.JPG', '.th.JPG'],
        ),
        transformers=[
            TransformIf(
                db.has,
                if_false=[
                    WithPIL([
                        Resize(750, 500, suffix='rs'),  # resized image (ratio=4:3)
                        ResizeMaxWidth(300, suffix='th'),  # thumbnail (width=300px)
                        AddExifAttribute(),
                        AddDominantColorsAttribute(),
                        AddDirectoryNameAttribute(),
                        AddMonthYearAttribute(),
                        AddOrientationAttribute(),
                        AddToImageDB(db),
                    ])
                ],
                if_true=[
                    UpdateFromImageDB(db)
                ]
            ),
            Logger(),
        ],
        organizer=lambda l: sorted(l, key=lambda k: k.attributes['date_taken']),
        classifiers=[
            AttributeClassifier('parent_directory', name='Albums'),
            AttributeClassifier('month_year', name='Date'),
            AttributeClassifier('dominant_color_names', name='Colors', exclude=['lightgray', 'darkgray'])
        ],
        writers=[
            BuildDirectory(pathlib.Path('./_build'), writers=[
                WriteIndex(),
                WriteImageDB(db, db_path),
            ])
        ]
    )

    pipeline()
