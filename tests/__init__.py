import unittest
import pathlib
import tempfile
import shutil

from sqlalchemy import create_engine
from gallery_generator.models import Base


class GCTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.tests_files_directory = pathlib.Path(pathlib.Path(__file__).parent, 'tests_files')
        self.temporary_directory = pathlib.Path(tempfile.mkdtemp())

        # use temporary database
        self.db_file = 'sqlite:///{}/temp.db'.format(self.temporary_directory)
        self.engine = create_engine(self.db_file, echo=True, future=True)

        # create schema
        Base.metadata.create_all(self.engine)

    def tearDown(self):
        shutil.rmtree(self.temporary_directory)

    def copy_to_temporary_directory(self, file_in_test_dir: str, new_name: str = ''):
        """Copy the content of a file from the ``test_file_directory`` to the temporary directory

        :param file_in_test_dir: path to the file to copy
        :param new_name: the new name of the file in the temporary directory (if blank, the one from path is used)
        :rtype: str
        """

        path_in_test = pathlib.Path(self.tests_files_directory, file_in_test_dir)

        if not path_in_test.exists():
            raise FileNotFoundError(path_in_test)

        if not new_name:
            new_name = path_in_test.name

        path_in_temp = pathlib.Path(self.temporary_directory, new_name)

        if path_in_temp.exists():
            raise FileExistsError(path_in_temp)

        with path_in_temp.open('wb') as f:
            with path_in_test.open('rb') as fx:
                f.write(fx.read())

        return path_in_temp
