from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Table
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship

from typing import Tuple

Base = declarative_base()


class BaseModel(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True)
    date_obj_created = Column(DateTime, default=func.current_timestamp())
    date_obj_modified = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())


class Category(BaseModel):
    __tablename__ = 'category'

    name = Column(String)
    tags = relationship('Tag')

    @classmethod
    def create(cls, name: str):
        o = cls()
        o.name = name
        return o

    def __repr__(self):
        return 'Category(id={}, name={})'.format(
            repr(self.id), repr(self.name)
        )


tag_picture_at = Table(
    'tag_picture_at',
    Base.metadata,
    Column('left_id', ForeignKey('tag.id'), primary_key=True),
    Column('right_id', ForeignKey('picture.id'), primary_key=True),
)


class Tag(BaseModel):
    __tablename__ = 'tag'

    name = Column(String)
    description = Column(String)

    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship('Category', back_populates='tags')

    pictures = relationship(
        'Picture', secondary=tag_picture_at, back_populates='tags'
    )

    @classmethod
    def create(cls, category: Category, name: str, description: str = ''):
        o = cls()

        o.category_id = category.id
        o.name = name
        o.description = description

        return o

    def __repr__(self):
        return 'Tag(id={}, name={}, description={}, category_id={})'.format(
            repr(self.id), repr(self.name), repr(self.description), repr(self.category_id)
        )


class Picture(BaseModel):
    __tablename__ = 'picture'

    path = Column(String)

    width = Column(Integer)
    height = Column(Integer)

    exif_DateTimeOriginal = Column(DateTime)
    exif_ExposureTime = Column(Float)
    exif_FNumber = Column(Float)
    exif_Make = Column(String)
    exif_Model = Column(String)
    exif_ISOSpeedRatings = Column(Integer)
    exif_FocalLength = Column(Float)

    tags = relationship(
        'Tag', secondary=tag_picture_at, back_populates='pictures'
    )

    @classmethod
    def create(cls, path: str, dimension: Tuple[int, int]):
        o = cls()
        o.path = path
        o.width, o.height = dimension

        return o


class Thumbnail(BaseModel):
    __tablename__ = 'thumbnail'

    path = Column(String)
    type = Column(String)

    picture_id = Column(Integer, ForeignKey('picture.id'))
    picture = relationship('Picture')
