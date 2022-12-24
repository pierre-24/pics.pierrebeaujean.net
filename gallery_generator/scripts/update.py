import pathlib
from datetime import datetime
from typing import Dict, List

from sqlalchemy.orm import Session
from sqlalchemy import select, func

from gallery_generator import logger, CONFIG_DIR_NAME, PAGE_DIR_NAME
from gallery_generator.controllers.database import GalleryDatabase
from gallery_generator.controllers.tags import TagManager
from gallery_generator.controllers.thumbnails import TRANSFORMER_TYPES, Thumbnailer
from gallery_generator.models import Category, tag_picture_at, Picture, Tag, Page, Thumbnail
from gallery_generator.views import TagView, PageView, IndexView


class CommandUpdate:
    def __init__(self):
        self.thumb_types = {}
        self.thumbnailer: Thumbnailer = None

        self.page_context = {}

        self.pages_dic: Dict[str, Page] = {}
        self.categories_dic: Dict[str, Category] = {}
        self.tags_per_cat_dic: Dict[str, List[Tag]] = {}
        self.thumbnails_dic: Dict[str, Thumbnail] = {}

    @property
    def common_context(self) -> dict:
        return dict(
            # required
            thumbnailer=self.thumbnailer,
            pages=self.pages_dic,
            categories=self.categories_dic,
            tags_per_cat=self.tags_per_cat_dic,
            now=datetime.now().strftime('%d/%m/%Y'),
            # others
            **self.page_context
        )

    def fetch_all(self, root: pathlib.Path, session: Session):

        # fetch pages
        for path in (root / CONFIG_DIR_NAME / PAGE_DIR_NAME).glob('*.md'):
            logger.info('FETCH {}'.format(path))
            page = Page.create_from_file(path)
            self.pages_dic[page.slug] = page

        # fetch categories... And others:
        categories = session.scalars(Category.select().order_by(Category.id)).all()

        for category in categories:
            subq = select(
                tag_picture_at.c.left_id,
                tag_picture_at.c.right_id,
                func.max(Picture.exif_datetime_original)
            ) \
                .join(Picture, tag_picture_at.c.right_id == Picture.id) \
                .group_by(tag_picture_at.c.left_id).subquery()

            q = select(Tag, Picture) \
                .where(Tag.category_id == category.id) \
                .join(subq, subq.c.left_id == Tag.id) \
                .join(Picture, subq.c.right_id == Picture.id) \
                .order_by(Picture.exif_datetime_original.desc())

            self.categories_dic[category.slug] = category
            tag_and_thumb = session.execute(q).all()
            self.tags_per_cat_dic[category.slug] = [c[0] for c in tag_and_thumb]
            self.thumbnails_dic.update(**dict((t.slug, p) for t, p in tag_and_thumb))

            # update tags
            for tag in self.tags_per_cat_dic[category.slug]:
                tag.update_from_file(root / CONFIG_DIR_NAME / TagManager.TAG_DIRECTORY)

    def render_all(self, target: pathlib.Path, session: Session):

        # make directory for thumbnails
        path_thumbnail = target / self.thumbnailer.THUMBNAIL_DIRECTORY
        if not path_thumbnail.exists():
            path_thumbnail.mkdir()

        # renders categories and tags
        for category in self.categories_dic.values():

            # create directory for category
            path_category = target / category.get_directory()
            if not path_category.exists():
                path_category.mkdir()

            for tag in self.tags_per_cat_dic[category.slug]:
                logger.info('GENERATE {}'.format(tag.get_url()))

                # get pictures (in correct order)
                pictures = session.scalars(
                    Picture.select()
                    .join(tag_picture_at, tag_picture_at.c.right_id == Picture.id)
                    .join(Tag, Tag.id == tag_picture_at.c.left_id)
                    .where(Tag.id == tag.id)
                    .order_by(Picture.exif_datetime_original)
                ).all()

                # render
                view = TagView(tag, pictures, self.common_context)
                view.render(target)

        # generate pages
        for page in self.pages_dic.values():
            logger.info('GENERATE {}'.format(page.get_url()))
            view = PageView(page, self.common_context)
            view.render(target)

        # generate index
        logger.info('GENERATE index.html')
        view = IndexView(self.thumbnails_dic, self.common_context)
        view.render(target)

    def __call__(self, root: pathlib.Path, settings: dict, db: GalleryDatabase, target: pathlib.Path):
        for key, conf in settings['update_phase']['thumbnails'].items():
            conf = conf.copy()
            transformer_type = conf.pop('type')
            self.thumb_types[key] = TRANSFORMER_TYPES[transformer_type](**conf)

        self.page_context = settings['update_phase']['page_context']

        with db.make_session() as session:

            # create thumbnailer
            self.thumbnailer = Thumbnailer(root, target, session, self.thumb_types)

            # fetch other
            self.fetch_all(root, session)

            # render
            self.render_all(target, session)


command_update = CommandUpdate()
