import pathlib

from sqlalchemy.orm import Session

from gallery_generator import logger
from gallery_generator.database import Category, Tag, Picture
from gallery_generator.files import CONFIG_DIR_NAME


class TaggingMeta(type):
    def __new__(mcs, name, bases, attrs):
        taggers = list()

        # extend parent taggers
        for base in bases:
            if isinstance(base, TaggingMeta):
                taggers.extend(base.__taggers__)

        # add taggers
        attrs['__taggers__'] = taggers
        attrs['taggers'] = property(lambda obj: taggers)
        cls = super().__new__(mcs, name, bases, attrs)
        return cls

    def add_tagger(cls, callback):
        """register callback
        :param key: key
        :type key: str
        :param callback: callback function
        :type callback: function
        """

        cls.__taggers__.append(callback)
        return callback

    def tagger(cls):
        """decorator @Class.register()
        :param key: key
        :type key: str
        """
        def wrapper(callback):
            return cls.add_tagger(callback)
        return wrapper


class TagManager(metaclass=TaggingMeta):
    """Tag manager, tag pictures and create tags accordingly. Can be extended with `@TagManager.tagger()`
    """

    TAG_DIRECTORY = 'tags'

    def __init__(self, root: pathlib.Path, session: Session):
        self.root = root
        self.session = session

        self.categories = {}
        self.tags = {}

    def get_tag_directory(self) -> pathlib.Path:
        return self.root / CONFIG_DIR_NAME / TagManager.TAG_DIRECTORY

    def _create_category(self, name: str) -> Category:
        """Create a new category
        """

        logger.info('NEW CATEGORY {}'.format(name))

        # add object in database
        category = Category.create(name)
        self.session.add(category)
        self.session.commit()

        # create directory to store tags latter on
        path = self.get_tag_directory() / category.get_directory()
        if not path.exists():
            path.mkdir()

        return category

    def _create_tag(self, category: Category, name: str) -> Tag:
        """Create a new tag in category
        """

        logger.info('NEW TAG {}/{}'.format(category.name, name))

        # add object in database
        tag = Tag.create(category=category, name=name)
        self.session.add(tag)
        self.session.commit()

        # create file
        path = self.get_tag_directory() / tag.get_input_file()
        if not path.exists():
            with path.open('w') as f:
                f.write('# {}'.format(name))

        return tag

    def get_tag_or_create(self, category_name: str, name: str) -> Tag:
        """Get an existing tag or create a new one. Also create the corresponding category if needed.
        """

        # 1. Get category (or create)
        try:
            category = self.categories[category_name]
        except KeyError:
            # try in database and if not, create from scratch
            category = self.session.execute(Category.select().where(Category.name == category_name)).scalar()
            if not category:
                category = self._create_category(category_name)
            self.categories[category_name] = category
            self.tags[category_name] = dict((t.name, t) for t in category.tags)

        # 2. Get tag (or create)
        try:
            tag = self.tags[category_name][name]
        except KeyError:
            tag = self.session.execute(Tag.select().where(Tag.category_id == category.id, Tag.name == name)).scalar()
            if not tag:
                tag = self._create_tag(category, name)
            self.tags[category_name][name] = tag

        return tag

    def tag_picture(self, picture: Picture):
        for tagger in self.taggers:
            tagger(self, picture)


@TagManager.tagger()
def tag_album(manager: TagManager, picture: Picture):
    """Tag album thanks to directory name"""

    tag = manager.get_tag_or_create('Album', pathlib.Path(picture.path).parent.name)
    picture.tags.append(tag)


@TagManager.tagger()
def tag_date(manager: TagManager, picture: Picture, fmt: str = '%B %Y'):
    """Tag date with `fmt` thanks to `exif_datetime_original`.
    """

    if picture.exif_datetime_original:
        tag = manager.get_tag_or_create('Date', picture.exif_datetime_original.strftime(fmt))
        picture.tags.append(tag)


FOCAL_CLASSES = {
    'Large': (0, 40),
    'Normal': (40, 100),
    'Zoom': (100, 5000)
}


@TagManager.tagger()
def tag_focal(manager: TagManager, picture: Picture, classes: dict = FOCAL_CLASSES):
    """Tag focal class with `classes` thanks to `exif_focal_length`.
    """

    if picture.exif_focal_length:
        # get focal class
        focal_class = None
        for k, limits in classes.items():
            if limits[0] <= picture.exif_focal_length < limits[1]:
                focal_class = k

        # if found, tag
        if focal_class:
            tag = manager.get_tag_or_create('Focal', focal_class)
            picture.tags.append(tag)
