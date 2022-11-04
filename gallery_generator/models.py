from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class BaseModel(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True)
    date_created = Column(DateTime, default=func.current_timestamp())
    date_modified = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())


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


class Tag(BaseModel):
    __tablename__ = 'tag'

    name = Column(String)
    description = Column(String)

    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship('Category', back_populates='tags')

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
