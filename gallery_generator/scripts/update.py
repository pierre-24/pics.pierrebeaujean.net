import pathlib
from datetime import datetime

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy import select, func

from gallery_generator import logger, CONFIG_PAGE_GEN
from gallery_generator.controllers.thumbnails import TRANSFORMER_TYPES
from gallery_generator.models import Category, tag_picture_at, Picture, Tag
from gallery_generator.controllers.database import GalleryDatabase
from gallery_generator.files import CONFIG_DIR_NAME, PAGE_DIR_NAME, Page
from gallery_generator.tag import TagManager
from gallery_generator.thumbnail import Thumbnailer


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
    template_page = env.get_template('page.html')

    # TODO: CSS
    # TODO: additional pages

    # create thumb types
    thumb_types = {}
    for key, conf in CONFIG_PAGE_GEN['thumbnails'].items():
        transformer_type = conf.pop('type')
        thumb_types[key] = TRANSFORMER_TYPES[transformer_type](**conf)

    with db.make_session() as session:
        # create thumbnailer
        thumbnailer = Thumbnailer(root, target, session, thumb_types)

        # common
        common_kwargs = {'thumbnailer': thumbnailer, 'now': datetime.now().strftime('%d/%m/%Y')}
        common_kwargs.update(**CONFIG_PAGE_GEN['page_content'])

        # create thumbnail directory
        path_thumbnail = target / thumbnailer.THUMBNAIL_DIRECTORY
        if not path_thumbnail.exists():
            path_thumbnail.mkdir()

        # -- FETCH
        tags_per_cat_dic = {}
        thumbnails_dic = {}
        categories_dic = {}
        pages_dic = {}

        # fetch pages
        for path in (root / CONFIG_DIR_NAME / PAGE_DIR_NAME).glob('*.md'):
            logger.info('FETCH {}'.format(path))
            page = Page.create_from_file(path)
            pages_dic[page.slug] = page

        common_kwargs['pages'] = pages_dic

        # fetch categories & tags
        categories = session.scalars(Category.select().order_by(Category.id)).all()

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

            # update tags
            for tag in tags_per_cat_dic[category.slug]:
                tag.update_from_file(root / CONFIG_DIR_NAME / TagManager.TAG_DIRECTORY)

        common_kwargs['categories'] = categories_dic
        common_kwargs['tags_per_cat'] = tags_per_cat_dic
        common_kwargs['thumbnails'] = thumbnails_dic

        # -- GENERATE
        for category in categories:

            # create directory for category
            path_category = target / category.get_directory()
            if not path_category.exists():
                path_category.mkdir()

            for tag in tags_per_cat_dic[category.slug]:
                logger.info('GENERATE {}'.format(tag.get_url()))

                # update tag
                tag.update_from_file(root / CONFIG_DIR_NAME / TagManager.TAG_DIRECTORY)

                # get pictures in correct order
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

        # generate pages
        for page in pages_dic.values():
            logger.info('GENERATE {}'.format(page.get_url()))
            with (target / page.get_url()).open('w') as f:
                f.write(template_page.render(
                    **common_kwargs,
                    page=page
                ))

        # generate index
        logger.info('GENERATE index.html')
        with (target / 'index.html').open('w') as f:
            f.write(template_index.render(
                **common_kwargs,
                categories_to_show=('album', 'date')
            ))
