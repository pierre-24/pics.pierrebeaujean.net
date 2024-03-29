import pathlib

from markdown import markdown
from slugify import slugify

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Table, select, func
from sqlalchemy.orm import declarative_base, relationship

from typing import Tuple

Base = declarative_base()


class BaseModel(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True)
    date_obj_created = Column(DateTime, default=func.current_timestamp())
    date_obj_modified = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())

    @classmethod
    def select(cls):
        return select(cls)

    @classmethod
    def count(cls):
        return select(func.count()).select_from(cls)


class Category(BaseModel):
    __tablename__ = 'category'

    name = Column(String)
    slug = Column(String)
    tags = relationship('Tag')

    @classmethod
    def create(cls, name: str):
        o = cls()
        o.name = name
        o.slug = slugify(name)
        return o

    def __repr__(self):
        return 'Category(id={}, name={})'.format(
            repr(self.id), repr(self.name)
        )

    def get_directory(self):
        return pathlib.Path(self.slug)

    def get_url(self):
        """Get URL
        """

        return self.category.get_directory() / 'index.html'


tag_picture_at = Table(
    'tag_picture_at',
    Base.metadata,
    Column('left_id', ForeignKey('tag.id'), primary_key=True),
    Column('right_id', ForeignKey('picture.id'), primary_key=True),
)


class Tag(BaseModel):
    __tablename__ = 'tag'

    name = Column(String)
    slug = Column(String)

    display_name: str = None
    description: str = None

    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship('Category', back_populates='tags')

    pictures = relationship(
        'Picture', secondary=tag_picture_at, back_populates='tags'
    )

    @classmethod
    def create(cls, category: Category, name: str):
        o = cls()

        o.category_id = category.id
        o.name = name
        o.slug = slugify(name)

        return o

    def __repr__(self):
        return 'Tag(id={}, name={}, category_id={})'.format(
            repr(self.id), repr(self.name), repr(self.category_id)
        )

    def get_input_file(self):
        """Get path to the file where the info are stored
        """

        return self.category.get_directory() / '{}.md'.format(self.slug)

    def get_url(self):
        """Get URL
        """

        return self.category.get_directory() / '{}.html'.format(self.slug)

    def update_from_file(self, tag_directory: pathlib.Path):
        """Read `tag_directory / self.get_file()` and update `display_name` and `description` from it
        """

        path = tag_directory / self.get_input_file()
        self.display_name = self.name

        if path.exists():
            with path.open('r') as f:
                content = f.read()
                if content[0] == '#':
                    next_line = content.find('\n')
                    if next_line < 0:
                        next_line = len(content)

                    self.display_name = content[1:next_line].strip()
                    self.description = content[next_line + 1:]
                else:
                    self.description = content

    def to_html(self) -> str:
        return markdown(self.description)


class Picture(BaseModel):
    __tablename__ = 'picture'

    path = Column(String)

    width = Column(Integer)
    height = Column(Integer)
    size = Column(Integer)

    exif_datetime_original = Column(DateTime)
    exif_exposure_time = Column(Float)
    exif_f_number = Column(Float)
    exif_make = Column(String)
    exif_model = Column(String)
    exif_iso_speed = Column(Integer)
    exif_focal_length = Column(Float)
    exif_orientation = Column(Integer)

    tags = relationship(
        'Tag', secondary=tag_picture_at, back_populates='pictures'
    )

    thumbnails = relationship('Thumbnail')

    @classmethod
    def create(cls, path: str, dimension: Tuple[int, int], size: int):
        o = cls()
        o.path = path
        o.width, o.height = dimension
        o.size = size

        return o

    def get_exif_info(self) -> dict:
        info = [
            'exposure_time', 'f_number', 'make', 'model', 'iso_speed', 'focal_length', 'datetime_original',
            'orientation'
        ]

        return dict((a, b) for a, b in ((i, getattr(self, 'exif_{}'.format(i))) for i in info))

    def __repr__(self):
        return 'Picture(id={},path={})'.format(repr(self.id), repr(self.path))


class Thumbnail(BaseModel):
    __tablename__ = 'thumbnail'

    path = Column(String)
    type = Column(String)

    picture_id = Column(Integer, ForeignKey('picture.id'))
    picture = relationship('Picture', back_populates='thumbnails')

    @classmethod
    def create(cls, picture: int, path: str, ttype: str):
        o = cls()
        o.picture_id = picture
        o.path = path
        o.type = ttype

        return o


class Page:
    def __init__(self, title: str, slug: str, content: str):
        self.title = title
        self.slug = slug
        self.content = content

    def to_html(self) -> str:
        return markdown(self.content)

    def get_url(self) -> str:
        return '{}.html'.format(self.slug)

    @classmethod
    def create_from_file(cls, path: pathlib.Path):
        with path.open() as f:
            content = f.read()
            title = slug = '.'.join(path.name.split('.')[:-1])

            if content[0] == '#':
                end = content.find('\n')
                if end < 0:
                    end = len(content)

                title = content[1:end].strip()

        return cls(title, slug, content)
