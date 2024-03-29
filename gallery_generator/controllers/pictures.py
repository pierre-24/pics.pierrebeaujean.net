import pathlib
import re
from typing import Iterable

from exif import Image as EImage
from PIL import Image as PILImage
import datetime

from gallery_generator.models import Picture


def seek_pictures(
        root: pathlib.Path,
        extensions: Iterable[str],
        exclude_dirs: Iterable[str]
) -> Iterable[pathlib.Path]:
    """Look in subdirectories of `root` for all pictures, recognized by their extension.

    Return an iterable of path to pictures, relative to `root`.
    """

    r = re.compile(r'.*\.({})'.format('|'.join(extensions)))

    for dir in root.iterdir():
        if dir.name in exclude_dirs:
            continue

        for f in dir.glob('*.*'):
            if r.match(str(f)):
                yield f.relative_to(root)


def create_picture_object(root: pathlib.Path, path: pathlib.Path) -> Picture:
    """Create a picture object.
    Extract some EXIF info if they exist thanks to the `exif` library.
    """

    full_path = root / path
    if not full_path.exists():
        raise FileNotFoundError(full_path)

    with full_path.open('rb') as fp:
        with PILImage.open(fp) as im:
            pic = Picture.create(str(path), (im.width, im.height), full_path.stat().st_size)

        fp.seek(0)
        im = EImage(fp)
        if im.has_exif:
            pic.exif_make = im.get('make')
            pic.exif_model = im.get('model')
            pic.exif_f_number = im.get('f_number')
            pic.exif_exposure_time = im.get('exposure_time')
            pic.exif_focal_length = im.get('focal_length')
            pic.exif_iso_speed = im.get('photographic_sensitivity')
            pic.exif_datetime_original = datetime.datetime.strptime(im.get('datetime_original'), '%Y:%m:%d %H:%M:%S')
            pic.exif_orientation = im.get('orientation')

    return pic
