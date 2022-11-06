from tests import GCTestCase

from gallery_generator.files import seek_pictures, PICTURE_EXCLUDE_DIRS
from gallery_generator.picture import create_picture_object
from gallery_generator.database import Picture


class CrawlTestCase(GCTestCase):
    def setUp(self) -> None:
        super().setUp()

        # create directories
        self.dirs = ['dir1', 'dir2']
        self.ndirs = len(self.dirs)

        for d in self.dirs:
            path = self.root / d
            path.mkdir()

        # dispatch pictures in it
        self.pic1 = self.copy_to_temporary_directory('im1.JPEG', self.dirs[0] + '/im1.jpg')
        self.pic2 = self.copy_to_temporary_directory('im2.JPEG', self.dirs[1] + '/im2.JPG')
        self.pic3 = self.copy_to_temporary_directory('im3.JPEG', self.dirs[1] + '/im3.JPEG')

    def test_seek_pictures_ok(self):
        found_pictures = list(seek_pictures(self.root))

        for pic in [self.pic1, self.pic2, self.pic3]:
            self.assertIn(pic.relative_to(self.root), found_pictures)

    def test_seek_pictures_exclude_dir_ok(self):
        found_pictures = list(seek_pictures(self.root, exclude_dirs=PICTURE_EXCLUDE_DIRS + (self.dirs[1], )))

        self.assertIn(self.pic1.relative_to(self.root), found_pictures)
        self.assertNotIn(self.pic2.relative_to(self.root), found_pictures)
        self.assertNotIn(self.pic3.relative_to(self.root), found_pictures)

    def test_seek_pictures_extensions_ok(self):
        found_pictures = list(seek_pictures(self.root, extensions=('JPG', )))

        self.assertNotIn(self.pic1.relative_to(self.root), found_pictures)
        self.assertIn(self.pic2.relative_to(self.root), found_pictures)
        self.assertNotIn(self.pic3.relative_to(self.root), found_pictures)

    def test_create_picture_object_ok(self):
        picture = create_picture_object(self.root, self.pic3.relative_to(self.root))
        exif_info = picture.get_exif_info()

        to_check = {  # those are the info from im3.JPEG
            'model': 'NIKON D5600',
            'f_number': 2.8,
            'iso_speed': 360,
            'exposure_time': 1 / 60,
            'focal_length': 35
        }

        for k, v in to_check.items():
            self.assertEqual(exif_info[k], v)

        with self.db.session() as session:
            self.assertEqual(session.execute(Picture.count()).scalar_one(), 0)

            session.add(picture)
            session.commit()

            self.assertEqual(session.execute(Picture.count()).scalar_one(), 1)
