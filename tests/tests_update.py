import pathlib
import tempfile

from tests import GCTestCase

from PIL import Image
from gallery_generator.thumbnail import ScalePicture, CropPicture, ScaleAndCropPicture, Thumbnailer
from gallery_generator.database import Picture, Thumbnail
from gallery_generator.script import command_crawl
from gallery_generator.files import Page, PAGE_DIR_NAME, CONFIG_DIR_NAME

from tests.tests_crawl import DispatchPictureFixture


class PageTestCase(GCTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.pages_dir = self.root / CONFIG_DIR_NAME / PAGE_DIR_NAME

    def test_page_create_ok(self):
        title = 'title'
        content = 'content'
        slug = 'test'
        path = self.pages_dir / '{}.md'.format(slug)

        page_ctn = '# {}\n{}'.format(title, content)

        with path.open('w') as f:
            f.write(page_ctn)

        page = Page.create_from_file(path)
        self.assertEqual(page.title, title)
        self.assertEqual(page.content, page_ctn)
        self.assertEqual(page.slug, slug)

    def test_page_only_title_ok(self):
        title = 'title'
        slug = 'test'
        path = self.pages_dir / '{}.md'.format(slug)

        page_ctn = '# {}'.format(title)

        with path.open('w') as f:
            f.write(page_ctn)

        page = Page.create_from_file(path)
        self.assertEqual(page.title, title)
        self.assertEqual(page.content, page_ctn)
        self.assertEqual(page.slug, slug)

    def test_page_only_content_ok(self):
        content = 'content'
        slug = 'test'
        path = self.pages_dir / '{}.md'.format(slug)

        page_ctn = content

        with path.open('w') as f:
            f.write(page_ctn)

        page = Page.create_from_file(path)
        self.assertEqual(page.title, slug)
        self.assertEqual(page.content, page_ctn)
        self.assertEqual(page.slug, slug)


class ImageTransformTestCase(GCTestCase, DispatchPictureFixture):
    def setUp(self) -> None:
        super().setUp()
        self.dispatch_one_pic(pic='im2.JPEG')

    def test_image_transform_ok(self):
        sz = 200

        with Image.open(self.pic) as im:
            self.assertTrue(im.width > im.height)

            # rotate
            im = ScalePicture(width=sz).rotate_with_tag(im)
            self.assertTrue(im.width < im.height)

            # scale
            scaled_im = ScalePicture(width=sz).transform(im)
            self.assertEqual(scaled_im.width, sz)
            self.assertNotEqual(scaled_im.height, sz)
            self.assertTrue(scaled_im.height > sz)

            self.assertAlmostEqual(scaled_im.width / scaled_im.height, im.width / im.height)  # ratio kept!

            # scale with two sizes
            scaled_im2 = ScalePicture(width=sz, height=sz).transform(im)
            self.assertTrue(scaled_im2.width < sz)
            self.assertEqual(scaled_im2.height, sz)

            self.assertAlmostEqual(scaled_im2.width / scaled_im2.height, im.width / im.height, delta=0.01)

            # crop
            cropped_im = CropPicture(sz, sz).transform(im)
            self.assertEqual(cropped_im.width, sz)
            self.assertEqual(cropped_im.height, sz)

            self.assertNotAlmostEqual(cropped_im.width / cropped_im.height, im.width / im.height)  # ratio destroyed!


class ThumbnailerTestCase(GCTestCase, DispatchPictureFixture):
    def setUp(self) -> None:
        super().setUp()
        self.dispatch_one_pic()

        command_crawl(self.root, self.db)

        # set up target
        self.target = pathlib.Path(tempfile.mkdtemp())
        (self.target / Thumbnailer.THUMBNAIL_DIRECTORY).mkdir()

        self.thumb_types = {
            'small_square': ScaleAndCropPicture(128, 128),
            'large_square': ScaleAndCropPicture(200, 200),
        }

    def test_thumbnail_one_pic_ok(self):
        TTYPE, TTYPE2 = self.thumb_types.keys()

        with self.db.make_session() as session:
            self.assertEqual(session.execute(Picture.count()).scalar_one(), 1)
            self.assertEqual(session.execute(Thumbnail.count()).scalar_one(), 0)

            picture = session.execute(Picture.select()).scalar_one()

            # generate a thumbnail
            thumbnailer = Thumbnailer(self.root, self.target, session, thumb_types=self.thumb_types)
            thumb_small = thumbnailer.get_thumbnail(picture, TTYPE)

            self.assertEqual(thumb_small.picture, picture)
            self.assertEqual(thumb_small.type, TTYPE)

            self.assertTrue((self.target / thumb_small.path).exists())
            self.assertEqual(session.execute(Thumbnail.count()).scalar_one(), 1)

            picture = session.execute(Picture.select()).scalar_one()
            self.assertEqual(len(picture.thumbnails), 1)
            self.assertEqual(picture.thumbnails[0], thumb_small)

            # ask for existing thumbnail gives the same thumb
            self.assertEqual(thumbnailer.get_thumbnail(picture, TTYPE), thumb_small)
            self.assertEqual(session.execute(Thumbnail.count()).scalar_one(), 1)

            # ask for another thumb gives a new one
            thumb_large = thumbnailer.get_thumbnail(picture, TTYPE2)
            self.assertEqual(session.execute(Thumbnail.count()).scalar_one(), 2)
            self.assertNotEqual(thumb_large, thumb_small)
            self.assertEqual(thumb_large.type, TTYPE2)

    def test_thumbnail_delete_recreate_ok(self):
        TTYPE = 'small_square'

        with self.db.make_session() as session:
            self.assertEqual(session.execute(Picture.count()).scalar_one(), 1)
            self.assertEqual(session.execute(Thumbnail.count()).scalar_one(), 0)

            picture = session.execute(Picture.select()).scalar_one()

            # generate a thumbnail
            thumbnailer = Thumbnailer(self.root, self.target, session, thumb_types=self.thumb_types)
            thumb_small = thumbnailer.get_thumbnail(picture, TTYPE)
            path = self.target / thumb_small.path
            self.assertEqual(session.execute(Thumbnail.count()).scalar_one(), 1)

            self.assertTrue(path.exists())

            # delete
            path.unlink()
            self.assertFalse(path.exists())

            # request
            thumbnailer.get_thumbnail(picture, TTYPE)
            self.assertEqual(session.execute(Thumbnail.count()).scalar_one(), 1)
            self.assertTrue(path.exists())
