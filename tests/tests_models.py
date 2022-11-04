from tests import GCTestCase

from sqlalchemy import select
from sqlalchemy.orm import Session

from gallery_generator.models import Category, Tag


class ModelsTestCase(GCTestCase):

    def setUp(self) -> None:
        super().setUp()

        with Session(self.engine) as session:
            c = Category.create('Test')
            session.add(c)
            session.commit()

            t1 = Tag.create(c, 'tag1')
            session.add(t1)

            t2 = Tag.create(c, 'tag2')
            session.add(t2)
            session.commit()

    def test_create_models(self):

        with Session(self.engine) as session:
            print(session.execute(select(Category)).all())
            print(session.execute(select(Category)).first()[0].tags)
