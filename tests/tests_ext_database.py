from typing import Any
import pathlib

from mosgal.base_models import BaseFetcher, BaseTransformer
from mosgal.seekers import ImageSeeker, Image
from mosgal.transformers import TransformIf

from mosgal.ext.database import ImageDB, AddToImageDB, UpdateFromImageDB

from tests import MosgalTestCase


class AddAttribute(BaseTransformer):

    def __init__(self, attribute: str, value: Any):
        super().__init__()
        self.attribute = attribute
        self.value = value

    def __call__(self, file: Image, *args, **kwargs):
        file.attributes[self.attribute] = self.value


class TestExtDatabase(MosgalTestCase):

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

        self.seek = ImageSeeker(self.temporary_directory, extensions=['JPEG'])
        self.db = ImageDB()
        self.transformer = AddAttribute('x', 'y')

    def test_add_to_database(self):
        self.assertEqual(len(self.db.from_source), 0)

        images = list(BaseFetcher(seeker=self.seek, transformers=[
            self.transformer,
            AddToImageDB(self.db)
        ])())

        self.assertEqual(len(self.db.from_source), 3)

        for image in images:
            self.assertIn(image.source, self.db.from_source)
            self.assertEqual(self.db.from_source[image.source], image)

    def test_write_read_db(self):

        list(BaseFetcher(seeker=self.seek, transformers=[
            self.transformer,
            AddToImageDB(self.db)
        ])())

        p = pathlib.Path(self.temporary_directory, 'db.json')

        self.assertFalse(p.exists())

        with p.open('w') as f:
            self.db.dump(f)

        self.assertTrue(p.exists())

        db2 = ImageDB()
        with p.open() as f:
            db2.load(f)

        self.assertEqual(len(db2.from_source), 3)

        for source, image in db2.from_source.items():
            image_base = self.db.from_source[source]
            self.assertEqual(image.path, image_base.path)
            self.assertEqual(image.attributes, image_base.attributes)

    def test_update_from_db(self):
        list(BaseFetcher(seeker=ImageSeeker(self.temporary_directory, exclude=['im1']), transformers=[
            self.transformer,
            AddToImageDB(self.db)
        ])())

        self.assertEqual(len(self.db.from_source), 2)
        self.assertNotIn('im1.JPEG', [i.path.name for i in self.db.from_source.values()])

        images = list(BaseFetcher(seeker=self.seek, transformers=[
            TransformIf(self.db.has, if_true=[
                UpdateFromImageDB(self.db)
            ], if_false=[
                self.transformer,
                AddToImageDB(self.db)
            ])
        ])())

        self.assertEqual(len(images), 3)
        self.assertIn('im1.JPEG', [i.path.name for i in images])
        self.assertTrue(all(i.attributes['x'] == 'y' for i in images))  # all attributes are there

        self.assertEqual(len(self.db.from_source), 3)
        self.assertIn('im1.JPEG', [i.path.name for i in self.db.from_source.values()])  # the missing image is in the DB

    def test_move_file(self):
        images = list(BaseFetcher(seeker=self.seek, transformers=[
            self.transformer,
            AddToImageDB(self.db)
        ])())

        self.assertEqual(len(self.db.from_source), 3)

        np = pathlib.Path(images[0].path.parent.parent, 'im2', images[0].path.name)
        op = images[0].path
        op.rename(np)

        self.assertTrue(np.exists())
        self.assertFalse(images[0].path.exists())

        images = list(BaseFetcher(seeker=self.seek, transformers=[
            TransformIf(self.db.has, if_true=[
                UpdateFromImageDB(self.db)
            ], if_false=[
                self.transformer,
                AddToImageDB(self.db)
            ])
        ])())

        self.assertIn(np, [i.path for i in images])
        self.assertNotIn(op, [i.path for i in images])
