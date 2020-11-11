import pathlib
import datetime
import colorsys
from PIL import ExifTags, Image as PILImage, ImageDraw

from mosgal.seekers import ImageSeeker, Image
from mosgal.base_models import BaseTransformer
from mosgal.transformers import AddExifAttributes, WithPIL, AddMonthYearAttribute, AddFocalClassAttribute, \
    TransformIf, AddDominantColorsAttribute, AddDirectoryNameAttribute, Resize, Thumbnail

from tests import MosgalTestCase

rev_exif_tags = dict((b, a) for a, b in ExifTags.TAGS.items())


class TestTransformers(MosgalTestCase):

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

        self.images = list(ImageSeeker(self.temporary_directory, extensions=['JPEG'])())

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

    def test_add_dominant_colors(self):
        """Test dominant colors"""

        transform = AddDominantColorsAttribute()

        # only one color
        colors = ['reds', 'greens', 'yellows']

        for c in colors:
            im = PILImage.new(
                'RGB',
                (150, 150),
                tuple(int(c * 255) for c in colorsys.hsv_to_rgb(*AddDominantColorsAttribute.PALETTE[c][0])))

            image = Image('tmp.jpg', pathlib.Path('tmp.jpg'))
            image.pil_object = im

            transform(image)
            self.assertEqual(len(image.attributes['dominant_color_names']), 1)
            self.assertEqual(image.attributes['dominant_color_names'][0], c)

        # two colors
        colors = [
            ('reds', 'greens'),
            ('yellows', 'greens')
        ]

        for c1, c2 in colors:
            im = PILImage.new(
                'RGB',
                (150, 150),
                tuple(int(c * 255) for c in colorsys.hsv_to_rgb(*AddDominantColorsAttribute.PALETTE[c1][0])))

            draw = ImageDraw.Draw(im)
            draw.rectangle(
                (50, 50, 100, 100),
                fill=tuple(int(c * 255) for c in colorsys.hsv_to_rgb(*AddDominantColorsAttribute.PALETTE[c2][0])))

            image = Image('tmp.jpg', pathlib.Path('tmp.jpg'))
            image.pil_object = im

            transform(image)
            self.assertEqual(len(image.attributes['dominant_color_names']), 2)
            self.assertIn(c1, image.attributes['dominant_color_names'])
            self.assertIn(c2, image.attributes['dominant_color_names'])

    def test_add_directory(self):
        """Test add directory"""
        transform = AddDirectoryNameAttribute()

        for image in self.images:
            self.assertFalse(any(a in image.attributes for a in ['parent_directory']))
            transform(image)

            self.assertEqual(image.attributes['parent_directory'], image.path.parts[-2])

    def test_resize(self):
        """Test the resize transformer"""

        class Tr(BaseTransformer):
            def __call__(self, im: Image, *args, **kwargs):
                im.attributes['ratio'] = im.pil_object.size[0] / im.pil_object.size[1]
                im.attributes['is_rotated'] = im.pil_object._getexif()[0x0112] in [3, 6, 8]

        # transform with max_width
        suffix = 'rs1'
        transform = WithPIL(transformers=[Tr(), Resize(max_width=300, suffix=suffix)])

        for image in self.images:
            transform(image)
            p = pathlib.Path(image.attributes['resized_' + suffix])
            self.assertTrue(p.exists())

            im = PILImage.open(p)
            w = 1 if image.attributes['is_rotated'] else 0  # keep rotation
            self.assertEqual(im.size[w], 300)
            self.assertAlmostEqual(im.size[0] / im.size[1], image.attributes['ratio'], places=1)  # keep ratio

            im.close()

        # transform with max_height
        suffix = 'rs2'
        transform = WithPIL(transformers=[Tr(), Resize(max_height=300, suffix=suffix)])

        for image in self.images:
            transform(image)
            p = pathlib.Path(image.attributes['resized_' + suffix])
            self.assertTrue(p.exists())

            im = PILImage.open(p)
            h = 0 if image.attributes['is_rotated'] else 1  # keep rotation
            self.assertEqual(im.size[h], 300)
            self.assertAlmostEqual(im.size[0] / im.size[1], image.attributes['ratio'], places=1)  # keep ratio

            im.close()

        # transform with max_height
        suffix = 'rs3'
        transform = WithPIL(transformers=[Tr(), Resize(max_width=300, max_height=300, suffix=suffix)])

        for image in self.images:
            transform(image)
            p = pathlib.Path(image.attributes['resized_' + suffix])
            self.assertTrue(p.exists())

            im = PILImage.open(p)
            self.assertTrue(im.size[0] <= 300)
            self.assertTrue(im.size[1] <= 300)
            self.assertAlmostEqual(im.size[0] / im.size[1], image.attributes['ratio'], places=1)  # keep ratio

            im.close()

    def test_thumbnail(self):
        """Test thumbnail"""

        suffix = 'th'
        sz = (300, 200)
        transform = WithPIL(transformers=[Thumbnail(width=sz[0], height=sz[1], suffix=suffix)])

        for image in self.images:
            transform(image)
            p = pathlib.Path(image.attributes['thumbnail_' + suffix])
            self.assertTrue(p.exists())

            im = PILImage.open(p)
            self.assertEqual(im.size, sz)

            im.close()
