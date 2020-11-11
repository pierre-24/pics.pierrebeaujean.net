import pathlib
from slugify import slugify

from mosgal.base_models import BaseFetcher
from mosgal.seekers import ImageSeeker
from mosgal.transformers import AddDirectoryNameAttribute, Thumbnail, WithPIL
from mosgal.classifiers import AttributeClassifier
from mosgal.characterizers import AddTargetCharacteristic, AddThumbnailCharacteristic, AddAlbumCharacteristics

from tests import MosgalTestCase


class TestCharacterizers(MosgalTestCase):

    def setUp(self) -> None:
        self.files = [
            ('im1.JPEG', 'im1/im1.JPEG'),
            ('im2.JPEG', 'im2/im2.JPEG'),
            ('im3.JPEG', 'im3/im3.JPEG'),
        ]

        for source, loc in self.files:
            p = pathlib.Path(self.temporary_directory, loc)
            p.parent.mkdir()
            self.copy_to_temporary_directory(source, loc)

        fetch = BaseFetcher(seeker=ImageSeeker(self.temporary_directory, extensions=['JPEG']), transformers=[
            AddDirectoryNameAttribute(),
            WithPIL([Thumbnail(25, 25, 'th')]),
        ])

        classify = AttributeClassifier('parent_directory', name='per_directory')
        self.collection = classify(fetch())

    def test_add_target_characteristic(self):
        """Test add target characteristic
        """

        def get_target(collection, element):
            return '{}-{}'.format(slugify(collection.name), slugify(element.name))

        characterize = AddTargetCharacteristic(get_target=get_target)
        characterize(self.collection)

        for e in self.collection.elements:
            self.assertEqual(e.characteristics['target_file'], get_target(self.collection, e))

    def test_add_thumbnail(self):
        """Add thumbnail attribute to element"""

        target = 'thumbnail_th_target'
        pos = -1

        characterize = AddThumbnailCharacteristic(target, file_position=pos)
        characterize(self.collection)

        for e in self.collection.elements:
            self.assertEqual(e.characteristics['thumbnail'], e.files[pos].attributes[target])

    def test_add_album_characteristics(self):
        """Check if the hand-crafted index.md is read correctly
        """

        characteristics = {
            'im1.JPEG': {'description': 'test'},
            'im2.JPEG': {'name': 'im2-mod', 'thumbnail': 'im2.JPEG', 'description': 'tmpx'},
            'im3.JPEG': {'name': 'im3-mod', 'description': 'test: test'}
        }

        for source, loc in self.files:
            p = pathlib.Path(self.temporary_directory, pathlib.Path(loc).parent, 'index.md')
            c = characteristics[source]
            with p.open('w') as f:
                if 'name' in c:
                    f.write('Title: {}\n'.format(c['name']))
                if 'thumbnail' in c:
                    f.write('Thumbnail: {}\n'.format(c['thumbnail']))
                if 'description' in c:
                    f.write(c['description'])

        target = 'thumbnail_th_target'
        characterize = AddAlbumCharacteristics('per_directory', target)
        characterize(self.collection)

        for e in self.collection.elements:
            fe = e.files[0].path.name
            c = characteristics[fe]

            if 'name' in c:
                self.assertEqual(e.name, c['name'])

            if 'thumbnail' in c:
                self.assertEqual(
                    e.characteristics['thumbnail'],
                    next(i.attributes[target] for i in e.files if i.path.name == c['thumbnail']))

            if 'description' in c:
                self.assertIn(c['description'], e.characteristics['description'])
