import pathlib
from datetime import datetime

from mosgal.base_models import BaseTransformer, BaseFile
from mosgal.seekers import ImageSeeker, Image
from mosgal.transformers import WithPIL, Resize, AddExifAttributes, AddDominantColorsAttribute, \
    AddDirectoryNameAttribute, AddMonthYearAttribute, TransformIf, Thumbnail, AddFocalClassAttribute
from mosgal.classifiers import AttributeClassifier
from mosgal.characterizers import SortElements, AddTargetCharacteristic, AddThumbnailCharacteristic, \
    AddAlbumCharacteristics
from mosgal.writers import BuildDirectory, WriteIndex, WriteImages, WriteCollections, WriteExtraFiles, WriteAbout
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


def target_name(file: Image, target_attribute: str, suffix: str, file_format: str):
    parent_directory = file.path.parts[-2]
    index = parent_directory + '_' + suffix
    if index not in indices:
        indices[index] = 0

    indices[index] += 1

    return 'images/{}_{}_{}.{}'.format(parent_directory, indices[index], suffix, file_format)


if __name__ == '__main__':

    db = ImageDB()

    db_path = pathlib.Path('./pictures/images.json')
    if db_path.exists():
        with db_path.open() as f:
            db.load(f)

    default_context = {
        'site_name': "Pierre's pictures",
        'footer': '<a rel="license" href="http://creativecommons.org/licenses/by/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by/4.0/88x31.png" /></a><br />This work (and <strong>all the images</strong>) is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by/4.0/">Creative Commons Attribution 4.0 International License</a>.<br />',
        'now': datetime.now().strftime('%d/%m/%Y (at %H:%M)')
    }

    pipeline = simple_pipeline(
        destination=pathlib.Path('./html'),
        seek=ImageSeeker(
            pathlib.Path('pictures'),
            extensions=['jpg', 'JPG', 'jpeg', 'JPEG'],
            exclude=['.rs.JPEG', '.lth.JPEG', '.th.JPEG'],
        ),
        transformers=[
            TransformIf(
                db.has,
                if_false=[
                    WithPIL([
                        Resize(1920, 1440, suffix='rs', name_target=target_name),  # resized image (ratio=4:3)
                        Resize(max_width=300, suffix='lth', name_target=target_name),  # thumbnail (width=300px)
                        Thumbnail(300, 3 * 75, suffix='th', name_target=target_name),  # thumbnail (width=300px)
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
            AttributeClassifier('parent_directory', name='Album'),
            AttributeClassifier('month_year', name='Date'),
            AttributeClassifier('focal_class', 'Focal'),
            AttributeClassifier(
                'dominant_color_names',
                name='Colors',
                exclude=['lightgray', 'darkgray']
            )
        ],
        characterizers=[
            SortElements('date_taken'),
            AddThumbnailCharacteristic('thumbnail_th_target'),
            AddAlbumCharacteristics('Album', 'thumbnail_th_target'),
            AddTargetCharacteristic(),
        ],
        writers=[
            BuildDirectory(pathlib.Path('./_build'), writers=[
                WriteImages(
                    pathlib.Path('images/'),
                    'Album',
                    [
                        ('resized_lth', 'resized_lth_target'),
                        ('thumbnail_th', 'thumbnail_th_target'),
                        ('resized_rs', 'resized_rs_target')
                    ]
                ),
                WriteIndex(['Album', 'Date'], default_context=default_context),
                WriteCollections(default_context=default_context),
                WriteAbout(pathlib.Path('./pictures/about.md'), default_context=default_context),
                WriteExtraFiles([pathlib.Path('./templates/style.css')]),
                WriteImageDB(db, db_path),
            ])
        ]
    )

    pipeline()
