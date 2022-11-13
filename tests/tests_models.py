from tests import GCTestCase

from gallery_generator.database import Category, Tag, Picture


class ModelsTestCase(GCTestCase):
    """To be removed in the future, just there to check stuffs
    """

    def setUp(self) -> None:
        super().setUp()

        with self.db.make_session() as session:
            c = Category.create('Test')
            session.add(c)
            session.commit()

            t1 = Tag.create(c, 'tag1')
            session.add(t1)

            t2 = Tag.create(c, 'tag2')
            session.add(t2)
            session.commit()

            pic = Picture.create('/tmp', (158, 15), 5)

            pic.tags.append(t1)

            session.add(pic)
            session.commit()

    def test_create_models(self):

        with self.db.make_session() as session:
            print(session.execute(Category.select()).scalar_one().tags)
            print(session.execute(Category.select().where(Category.id.is_(1))).scalar())
