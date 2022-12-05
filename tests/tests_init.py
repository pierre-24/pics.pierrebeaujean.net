from tests import GCTestCase

from gallery_generator import CONFIG_DIR_NAME
from gallery_generator.controllers.database import GalleryDatabase
from sqlalchemy import inspect


class InitTestCase(GCTestCase):

    def assert_init_ok(self, root):

        # check that files are there
        must_exists_files = [
            root / CONFIG_DIR_NAME,
            root / CONFIG_DIR_NAME / GalleryDatabase.DATABASE_NAME,
            root / CONFIG_DIR_NAME / 'tags',
            root / CONFIG_DIR_NAME / 'pages',
        ]

        for f in must_exists_files:
            self.assertTrue(f.exists())

        # check that database is ok by checking tables
        db = GalleryDatabase(root)
        table_names = inspect(db._engine()).get_table_names()

        must_exists_tables = ['category', 'tag', 'picture', 'thumbnail']

        for table in must_exists_tables:
            self.assertIn(table, table_names)

    def test_init_ok(self):
        self.assert_init_ok(self.root)
