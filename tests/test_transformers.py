import pathlib
import datetime
from PIL import ExifTags, Image as PILImage

from mosgal.seekers import ImageSeeker
from mosgal.base_models import BaseTransformer
from mosgal.transformers import AddExifAttributes, WithPIL, AddMonthYearAttribute, AddFocalClassAttribute, TransformIf

from tests import MosgalTestCase

rev_exif_tags = dict((b, a) for a, b in ExifTags.TAGS.items())


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

        self.images = list(ImageSeeker(self.temporary_directory)())

    def test_transform_if(self):
        """Test the TransformIf transformer
        """

        class Tr(BaseTransformer):
            def __init__(self, v):
                super().__init__()
                self.v = v

            def __call__(self, im, *args, **kwargs):
                im.attributes['test'] = self.v

        def test(im):
            return 'im3' in im.source

        transform = TransformIf(
            test=test,
            if_true=[Tr(True)],
            if_false=[Tr(False)],
        )

        for image in self.images:
            self.assertFalse('test' in image.attributes)
            transform(image)
            self.assertEqual(test(image), image.attributes['test'])

    def test_add_exif(self):
        """Test add exif attributes"""

        transform = WithPIL(transformers=[AddExifAttributes()])

        for image in self.images:
            self.assertFalse(any(a in image.attributes for a in AddExifAttributes.EXIF_TAGS))
            transform(image)

            # fetch EXIFS
            im = PILImage.open(image.path)
            exifs = im.getexif()
            im.close()

            # check attributes
            for a in AddExifAttributes.EXIF_TAGS:
                self.assertAlmostEqual(image.attributes[a], exifs[rev_exif_tags[a]])

    def test_add_month_year(self):
        """Test add month_year attribute"""
        fmt = '%B-%Y'
        transform = WithPIL(transformers=[AddMonthYearAttribute(fmt=fmt)])

        for image in self.images:
            self.assertFalse(any(a in image.attributes for a in ['date_taken', 'month_year']))
            transform(image)

            # fetch date
            im = PILImage.open(image.path)
            date = im.getexif()[rev_exif_tags['DateTimeOriginal']]
            im.close()

            # check attributes
            self.assertEqual(date, image.attributes['date_taken'])
            self.assertEqual(
                datetime.datetime.strptime(date, '%Y:%m:%d %H:%M:%S').strftime(fmt), image.attributes['month_year'])

    def test_add_focal_class(self):
        """Test add focal_class attribute"""

        focal_classes = {'large': (0, 50), 'small': (50, 2000)}
        transform = WithPIL(transformers=[AddFocalClassAttribute(focal_classes)])

        for image in self.images:
            self.assertFalse(any(a in image.attributes for a in ['focal_class']))
            transform(image)

            # fetch date
            im = PILImage.open(image.path)
            fnumber = im.getexif()[rev_exif_tags['FocalLengthIn35mmFilm']]
            im.close()

            if fnumber <= 50:
                self.assertEqual(image.attributes['focal_class'], 'large')
            else:
                self.assertEqual(image.attributes['focal_class'], 'small')
