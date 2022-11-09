from tests import GCTestCase

from PIL import Image

from gallery_generator.script import command_crawl
from gallery_generator.database import Picture
from gallery_generator.thumbnail import ScalePicture, CropPicture


class UpdateTestCase(GCTestCase):
    def setUp(self) -> None:
        super().setUp()

        # create directories and dispatch pictures in it
        self.dirs = ['dir1', 'dir2']
        self.ndirs = len(self.dirs)

        for d in self.dirs:
            path = self.root / d
            path.mkdir()

        self.pic1 = self.copy_to_temporary_directory('im1.JPEG', self.dirs[0] + '/im1.jpg')
        self.pic2 = self.copy_to_temporary_directory('im2.JPEG', self.dirs[1] + '/im2.JPG')
        self.pic3 = self.copy_to_temporary_directory('im3.JPEG', self.dirs[1] + '/im3.JPEG')

        # crawl in that
        command_crawl(self.root, self.db)

        with self.db.session() as session:
            self.assertEqual(session.execute(Picture.count()).scalar_one(), 3)

    def test_image_transform_ok(self):
        sz = 200

        with Image.open(self.pic2) as im:
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
