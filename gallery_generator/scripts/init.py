import pathlib

from gallery_generator import logger
from gallery_generator.controllers.database import GalleryDatabase
from gallery_generator.controllers.files import create_config_dirs


def command_init(root: pathlib.Path, db: GalleryDatabase):
    """Create the config directories and database"""

    logger.info('Create config dir in `{}`'.format(root))

    # create config dirs
    create_config_dirs(root)

    # remove existing db and create a new one
    logger.info('Create database in `{}`'.format(db.path))

    if db.path.exists():
        db.path.unlink()

    # create schema
    logger.info('Create schema')

    db.create_schema()
