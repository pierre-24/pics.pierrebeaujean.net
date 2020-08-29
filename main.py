import pathlib

from slugify import slugify

from mosgal.base_models import BaseTransformer, BaseFile, Collection, Element
from mosgal.seekers import ImageSeeker, Image
from mosgal.transformers import WithPIL, Resize, AddExifAttributes, ResizeMaxWidth, AddDominantColorsAttribute, \
    AddDirectoryNameAttribute, AddMonthYearAttribute, AddOrientationAttribute, TransformIf, Thumbnail, \
    AddFocalClassAttribute
from mosgal.classifiers import AttributeClassifier
from mosgal.writers import BuildDirectory, WriteIndex, WriteImages
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


indices = {}


def image_name(image: Image, attribute: str) -> str:
    type_ = attribute.split('_')[-1]
    parent_directory = image.attributes['parent_directory']

    index = parent_directory + '_' + type_
    if index not in indices:
        indices[index] = 0

    indices[index] += 1

    return '{}_{}_{}.JPG'.format(parent_directory, indices[index], type_)


def element_target(name: str) -> str:
    return '/{}.html'.format(slugify(name))


if __name__ == '__main__':

    db = ImageDB()

    db_path = pathlib.Path('./images.json')
    if db_path.exists():
        with db_path.open() as f:
            db.load(f)

    pipeline = simple_pipeline(
        destination=pathlib.Path('./html'),
        seek=ImageSeeker(
            pathlib.Path('pictures'),
            extensions=['jpg', 'JPG', 'jpeg', 'JPEG'],
            exclude=['.rs.JPG', '.lth.JPG', '.th.JPG'],
        ),
        transformers=[
            TransformIf(
                db.has,
                if_false=[
                    WithPIL([
                        Resize(750, 500, suffix='rs'),  # resized image (ratio=4:3)
                        ResizeMaxWidth(300, suffix='lth'),  # thumbnail (width=300px)
                        Thumbnail(300, 3*75, suffix='th'),  # thumbnail (width=300px)
                        AddExifAttributes(),
                        AddDominantColorsAttribute(),
                        AddDirectoryNameAttribute(),
                        AddMonthYearAttribute(),
                        AddFocalClassAttribute(),
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
            AttributeClassifier('parent_directory', name='Albums', target='albums', get_element_target=element_target),
            AttributeClassifier('month_year', name='Dates', target='dates', get_element_target=element_target),
            AttributeClassifier('focal_class', 'Focals', target='focals', get_element_target=element_target),
            AttributeClassifier(
                'dominant_color_names',
                name='Colors',
                exclude=['lightgray', 'darkgray'],
                target='colors',
                get_element_target=element_target
            )
        ],
        writers=[
            BuildDirectory(pathlib.Path('./_build'), writers=[
                WriteImages(
                    pathlib.Path('images/'),
                    'Albums',
                    ['resized_lth', 'thumbnail_th', 'resized_rs'],
                    image_name
                ),
                WriteIndex(['Albums', 'Dates'], 'thumbnail_th_final', sorting_criterion='date_taken'),
                WriteImageDB(db, db_path),
            ])
        ]
    )

    pipeline()
