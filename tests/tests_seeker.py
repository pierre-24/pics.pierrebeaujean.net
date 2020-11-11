import pathlib

from mosgal.seekers import ImageSeeker

from tests import MosgalTestCase


class TestSeeker(MosgalTestCase):

    def setUp(self) -> None:
        self.files = [
            ('im1.JPEG', 'im1/im1.JPEG'),
            ('im2.JPEG', 'im2/im2.JPEG'),
            ('im3.JPEG', 'im3/im3.JPEG'),
        ]

        for source, loc in self.files:
            p = pathlib.Path(self.temporary_directory, loc)
            p.parent.mkdir()
            self.copy_to_temporary_directory(source, loc)

        pathlib.Path(self.temporary_directory, 'im1/tmp.xyz').touch()

    def test_image_seeker(self):
        # seek for JPEG
        seeker = ImageSeeker(pathlib.Path(self.temporary_directory), extensions=['JPEG'])
        found_images = list(seeker())

        self.assertEqual(len(found_images), 3)
        for source, loc in self.files:
            self.assertIn(
                pathlib.Path(self.temporary_directory, loc),
                list(i.path for i in found_images)
            )

        # exclude a file
        seeker = ImageSeeker(pathlib.Path(self.temporary_directory), extensions=['JPEG'], exclude=[self.files[0][0]])
        found_images = list(seeker())

        self.assertEqual(len(found_images), 2)
        for source, loc in self.files[1:]:
            self.assertIn(
                pathlib.Path(self.temporary_directory, loc),
                list(i.path for i in found_images)
            )
