import pathlib

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from gallery_generator import CONFIG_DIR_NAME
from gallery_generator.models import Base


class GalleryDatabase:

    DATABASE_NAME = 'gallery.sqlite3'

    def __init__(self, root: pathlib.Path):
        self.path = root / CONFIG_DIR_NAME / self.DATABASE_NAME
        self.db_file = 'sqlite:///{}'.format(self.path)

    def exists(self) -> bool:
        return self.path.exists()

    def _engine(self):
        return create_engine(self.db_file)

    def create_schema(self):
        Base.metadata.create_all(self._engine())

    def make_session(self) -> Session:
        return Session(self._engine())
