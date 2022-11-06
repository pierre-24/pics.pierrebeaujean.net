import unittest
import pathlib
import tempfile
import shutil

from gallery_generator.database import GalleryDatabase
from gallery_generator.script import command_init


class GCTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.tests_files_directory = pathlib.Path(pathlib.Path(__file__).parent, 'tests_files')

        self.root = pathlib.Path(tempfile.mkdtemp())
        self.db = GalleryDatabase(self.root)

        # create schema
        command_init(self.root, self.db)

    def tearDown(self):
        shutil.rmtree(self.root)

    def copy_to_temporary_directory(self, file_in_test_dir: str, new_name: str = '') -> pathlib.Path:
        """Copy the content of a file from the ``test_file_directory`` to the temporary directory

        :param file_in_test_dir: path to the file to copy
        :param new_name: the new name of the file in the temporary directory (if blank, the one from path is used)
        """

        path_in_test = pathlib.Path(self.tests_files_directory, file_in_test_dir)

        if not path_in_test.exists():
            raise FileNotFoundError(path_in_test)

        if not new_name:
            new_name = path_in_test.name

        path_in_temp = pathlib.Path(self.root, new_name)

        if path_in_temp.exists():
            raise FileExistsError(path_in_temp)

        with path_in_temp.open('wb') as f:
            with path_in_test.open('rb') as fx:
                f.write(fx.read())

        return path_in_temp
