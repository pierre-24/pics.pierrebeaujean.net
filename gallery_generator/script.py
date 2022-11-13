import argparse
import pathlib
import sys
from datetime import datetime
from jinja2 import Environment, select_autoescape, FileSystemLoader

from gallery_generator import logger

from gallery_generator.files import create_config_dirs, CONFIG_DIR_NAME
from gallery_generator.database import GalleryDatabase, Picture, Category, Tag
from gallery_generator.files import seek_pictures
from gallery_generator.tag import TagManager
from gallery_generator.picture import create_picture_object
from gallery_generator.thumbnail import Thumbnailer, ScalePicture, ScaleAndCropPicture, CropPicture


# config
TRANSFORMER_TYPES = {
    'Scale': ScalePicture,
    'Crop': CropPicture,
    'ScaleAndCrop': ScaleAndCropPicture
}


CONFIG = {
    'thumbnails': {
        'gallery_small': {
            'type': 'Scale',
            'width': 300
        },
        'gallery_large': {
            'type': 'Scale',
            'width': 1920,
            'height': 1920
        },
        'tag_thumbnail': {
            'type': 'ScaleAndCrop',
            'width': 300,
            'height': 225
        }
    },
    'page_content': {
        'site_name': 'Gallery test'
    }
}


def exit_failure(msg: str, code: int = -1):
    print(msg, file=sys.stderr)
    return sys.exit(code)


def status(root, db: GalleryDatabase):
    if db.path.exists():
        with db.make_session() as session:
            print('Database `{}` exists:'.format(db.path))
            print('- {} Picture(s)'.format(session.execute(Picture.count()).scalar_one()))
            print('- {} Category(ies)'.format(session.execute(Category.count()).scalar_one()))
            print('- {} Tags(s)'.format(session.execute(Tag.count()).scalar_one()))
    else:
        print('Database `{}` does not exists.'.format(db.path))


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


def command_crawl(root: pathlib.Path, db: GalleryDatabase):
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

        for path in seek_pictures(root):
            logger.info('FOUND {}'.format(path))

            if session.execute(Picture.count().where(Picture.path == str(path))).scalar_one() == 0:
                logger.info('NEW PICTURE {}'.format(path))

                picture = create_picture_object(root, path)
                tag_manager.tag_picture(picture)

                logger.info('[{}]'.format(', '.join(t.name for t in picture.tags)))

                session.add(picture)
                session.commit()


def command_update(root: pathlib.Path, db: GalleryDatabase, target: pathlib.Path):
    """Update/create the static website:

    - Compile SCSS into CSS
    - Create a page for each tag that contains an image
    - Create index
    - Create additional page(s)
    """

    logger.info('* Update phase *')

    if not target.exists():
        raise FileNotFoundError('Target directory `{}` does not exists'.format(target))

    # load templates
    env = Environment(
        loader=FileSystemLoader(pathlib.Path(__file__).parent / 'templates'),
        autoescape=select_autoescape(['html', 'xml'])
    )

    template_index = env.get_template('index.html')
    template_tag = env.get_template('tag.html')

    now = datetime.now().strftime('%d/%m/%Y')

    # TODO: CSS

    # create thumb types
    thumb_types = {}
    for key, conf in CONFIG['thumbnails'].items():
        transformer_type = conf.pop('type')
        thumb_types[key] = TRANSFORMER_TYPES[transformer_type](**conf)

    with db.make_session() as session:
        # create thumbnailer
        thumbnailer = Thumbnailer(root, target, session, thumb_types)

        # create thumbnail directory
        path_thumbnail = target / thumbnailer.THUMBNAIL_DIRECTORY
        if not path_thumbnail.exists():
            path_thumbnail.mkdir()

        # go through all categories
        categories = session.scalars(Category.select()).all()
        for category in categories:

            # create directory for category
            path_category = target / category.get_directory()
            if not path_category.exists():
                path_category.mkdir()

            for tag in category.tags:
                logger.info('GENERATE {}'.format(tag.get_url()))
                # update tag
                tag.update_from_file(root / CONFIG_DIR_NAME / TagManager.TAG_DIRECTORY)

                # render
                path_tag = target / tag.get_url()
                with path_tag.open('w') as f:
                    f.write(template_tag.render(
                        thumbnailer=thumbnailer,
                        now=now,
                        **CONFIG['page_content'],
                        tag=tag
                    ))

        logger.info('GENERATE index.html')
        with (target / 'index.html').open('w') as f:
            f.write(template_index.render(
                thumbnailer=thumbnailer,
                now=now,
                **CONFIG['page_content'],
                categories=categories
            ))


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('source', help='source directory', type=pathlib.Path)

    meg = parser.add_mutually_exclusive_group(required=True)

    meg.add_argument('-s', '--status', action='store_true', help='Get status')
    meg.add_argument('-i', '--init', action='store_true', help='Initialize')
    meg.add_argument('-c', '--crawl', action='store_true', help='Update the database with new pictures')
    meg.add_argument('-u', '--update', type=pathlib.Path, help='Create a static website')

    args = parser.parse_args()

    # check path
    if not args.source.exists():
        return exit_failure('source directory `{}` does not exists'.format(args.source))

    db = GalleryDatabase(args.source)

    try:
        if args.init:
            command_init(args.source, db)
        elif args.crawl:
            command_crawl(args.source, db)
        elif args.update:
            command_update(args.source, db, args.update)
        elif args.status:
            status(args.source, db)
    except Exception as e:
        return exit_failure('Error while executing command: {}'.format(e))


if __name__ == '__main__':
    main()
