import pathlib

from gallery_generator import logger
from gallery_generator.models import Picture
from gallery_generator.controllers.database import GalleryDatabase
from gallery_generator.controllers.pictures import create_picture_object, seek_pictures
from gallery_generator.controllers.tags import TagManager


def command_crawl(root: pathlib.Path, settings: dict, db: GalleryDatabase):
    """Go through all accessible pictures in the root directory, then for each of them

    - check if they are already in the database, and if not,
    - add them to the database, gathering the infos
    - tag them accordingly, creating tags if required
    """

    if not db.exists():
        raise FileNotFoundError('Database file `{}` does not exists'.format(db.path))

    logger.info('* Crawling phase *')

    with db.make_session() as session:
        tag_manager = TagManager(root, session)

        existing_pictures = dict((p.path, [p, False]) for p in session.scalars(Picture.select()).all())

        # add new pictures
        for path in seek_pictures(
                root,
                extensions=settings['crawl_phase']['picture_exts'],
                exclude_dirs=settings['crawl_phase']['excluded_dirs']
        ):

            path_str = str(path)
            logger.info('FOUND {}'.format(path))

            if path_str not in existing_pictures:
                logger.info('NEW PICTURE {}'.format(path))

                picture = create_picture_object(root, path)
                tag_manager.tag_picture(picture)

                logger.info('[{}]'.format(', '.join(t.name for t in picture.tags)))

                session.add(picture)
                session.commit()
            else:
                existing_pictures[path_str][1] = True

        # check if there is pictures to remove
        for picture, found in existing_pictures.values():
            if not found:
                session.delete(picture)

        session.commit()
