import argparse
import pathlib
import sys
from datetime import datetime
from jinja2 import Environment, select_autoescape, FileSystemLoader
from sqlalchemy import select, func

from gallery_generator import logger

from gallery_generator.files import create_config_dirs, CONFIG_DIR_NAME
from gallery_generator.database import GalleryDatabase, Picture, Category, Tag, tag_picture_at
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

    # TODO: CSS

    # create thumb types
    thumb_types = {}
    for key, conf in CONFIG['thumbnails'].items():
        transformer_type = conf.pop('type')
        thumb_types[key] = TRANSFORMER_TYPES[transformer_type](**conf)

    with db.make_session() as session:
        # create thumbnailer
        thumbnailer = Thumbnailer(root, target, session, thumb_types)

        # common
        common_kwargs = {'thumbnailer': thumbnailer, 'now': datetime.now().strftime('%d/%m/%Y')}
        common_kwargs.update(**CONFIG['page_content'])

        # create thumbnail directory
        path_thumbnail = target / thumbnailer.THUMBNAIL_DIRECTORY
        if not path_thumbnail.exists():
            path_thumbnail.mkdir()

        # fetch categories & tags
        categories = session.scalars(Category.select().order_by(Category.id)).all()
        tags_per_cat_dic = {}
        thumbnails_dic = {}
        categories_dic = {}

        for category in categories:
            subq = select(
                tag_picture_at.c.left_id,
                tag_picture_at.c.right_id,
                func.max(Picture.exif_datetime_original)
            )\
                .join(Picture, tag_picture_at.c.right_id == Picture.id)\
                .group_by(tag_picture_at.c.left_id).subquery()

            q = select(Tag, Picture)\
                .where(Tag.category_id == category.id)\
                .join(subq, subq.c.left_id == Tag.id)\
                .join(Picture, subq.c.right_id == Picture.id)\
                .order_by(Picture.exif_datetime_original.desc())

            categories_dic[category.slug] = category
            tag_and_thumb = session.execute(q).all()
            tags_per_cat_dic[category.slug] = [c[0] for c in tag_and_thumb]
            thumbnails_dic.update(**dict((t.slug, p) for t, p in tag_and_thumb))

        common_kwargs['categories'] = categories_dic
        common_kwargs['tags_per_cat'] = tags_per_cat_dic
        common_kwargs['thumbnails'] = thumbnails_dic

        # generate pages for category and tags
        for category in categories:

            # create directory for category
            path_category = target / category.get_directory()
            if not path_category.exists():
                path_category.mkdir()

            for tag in tags_per_cat_dic[category.slug]:
                logger.info('GENERATE {}'.format(tag.get_url()))

                # update tag
                tag.update_from_file(root / CONFIG_DIR_NAME / TagManager.TAG_DIRECTORY)

                # get pictures
                pictures = session.scalars(
                    Picture.select()
                    .join(tag_picture_at, tag_picture_at.c.right_id == Picture.id)
                    .join(Tag, Tag.id == tag_picture_at.c.left_id)
                    .where(Tag.id == tag.id)
                    .order_by(Picture.exif_datetime_original)
                ).all()

                # render
                path_tag = target / tag.get_url()
                with path_tag.open('w') as f:
                    f.write(template_tag.render(
                        **common_kwargs,
                        tag=tag,
                        pictures=pictures
                    ))

        # generate index
        logger.info('GENERATE index.html')
        with (target / 'index.html').open('w') as f:
            f.write(template_index.render(
                **common_kwargs,
                categories_to_show=('album', 'date')
            ))

        # TODO: additional pages


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
