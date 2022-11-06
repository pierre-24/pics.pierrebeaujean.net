import pathlib
from exif import Image as EImage
from PIL import Image as PILImage
import datetime

from gallery_generator.database import Picture


def create_picture_object(root: pathlib.Path, path: pathlib.Path) -> Picture:
    """Create a picture object. Either use the `exif` library (and the full extent of exif tags it provides)
    or fall back to `Pillow` if there does not seem to be EXIF tags.
    """

    full_path = root / path
    if not full_path.exists():
        raise FileNotFoundError(full_path)

    with full_path.open('rb') as fp:
        im = EImage(fp)
        if im.has_exif:
            pic = Picture.create(str(path), (im.image_width, im.image_height), full_path.stat().st_size)

            pic.exif_make = im.get('make')
            pic.exif_model = im.get('model')
            pic.exif_f_number = im.get('f_number')
            pic.exif_exposure_time = im.get('exposure_time')
            pic.exif_focal_length = im.get('focal_length')
            pic.exif_iso_speed = im.get('photographic_sensitivity')
            pic.exif_datetime_original = datetime.datetime.strptime(im.get('datetime_original'), '%Y:%m:%d %H:%M:%S')
        else:
            fp.seek(0)
            im = PILImage.open(fp)
            pic = Picture.create(str(path), (im.width, im.height), full_path.stat().st_size)

    return pic
