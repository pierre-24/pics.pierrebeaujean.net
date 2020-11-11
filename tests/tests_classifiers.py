import pathlib

from mosgal.base_models import BaseFetcher
from mosgal.seekers import ImageSeeker
from mosgal.transformers import AddDirectoryNameAttribute
from mosgal.classifiers import AttributeClassifier

from tests import MosgalTestCase


class TestClassifiers(MosgalTestCase):

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

        self.fetch = BaseFetcher(seeker=ImageSeeker(self.temporary_directory, extensions=['JPEG']), transformers=[
            AddDirectoryNameAttribute()
        ])

    def test_attribute_classifier(self):

        classify = AttributeClassifier('parent_directory', name='per_directory')

        collection = classify(self.fetch())
        self.assertEqual(collection.name, 'per_directory')
        self.assertEqual(len(collection.elements), 3)

        for e in collection.elements:
            self.assertEqual(e.name, e.files[0].attributes['parent_directory'])
