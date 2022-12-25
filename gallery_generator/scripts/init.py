import pathlib

from gallery_generator import logger
from gallery_generator.controllers.database import GalleryDatabase
from gallery_generator.controllers.files import create_config_dirs


l_logger = logger.getChild('scripts.init')


def command_init(root: pathlib.Path, db: GalleryDatabase):
    """Create the config directories and database"""

    l_logger.info('Create config dir in `{}`'.format(root))

    # create config dirs
    create_config_dirs(root)

    # remove existing db and create a new one
    l_logger.info('Create database in `{}`'.format(db.path))

    if db.path.exists():
        db.path.unlink()

    # create schema
    l_logger.info('Create schema')

    db.create_schema()
