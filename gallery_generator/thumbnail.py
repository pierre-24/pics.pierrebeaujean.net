import pathlib
from enum import Enum
from typing import Dict
from sqlalchemy.orm import Session

from PIL import Image as PILImage

from gallery_generator.database import Picture


class BaseImageTransform:
    EXIF_ROT_TAG = 0x0112

    def __init__(self, output_format: str = 'JPEG', encoder_options: dict = {'quality': 85}):
        self.output_format = output_format
        self.encoder_options = encoder_options
        self._rotate = True

    def transform(self, im: PILImage) -> PILImage:
        raise NotImplementedError()

    def rotate_with_tag(self, im: PILImage):
        """Rotate according to tag"""

        # avoid double rotation
        if not self._rotate:
            return im

        self._rotate = False

        # get rotation tag, if any
        rot = im.getexif().get(BaseImageTransform.EXIF_ROT_TAG)
        rotate_angle = {3: 180, 6: 270, 8: 90}

        # rotate
        if rot in rotate_angle:
            return im.rotate(rotate_angle[rot], expand=True)
        else:
            return im

    def __call__(self, path_in: pathlib.Path, path_out: pathlib.Path, *args, **kwargs):
        im = PILImage.open(path_in)

        # rotate if needed
        im = self.rotate_with_tag(im)

        # transform and save
        return self.transform(im).save(path_out, self.output_format, **self.encoder_options)


class ScalePicture(BaseImageTransform):
    """Resize, but keep the aspect ratio.
    If one size is provided, then the image has exactly this size in its corresponding dimension.
    If two sizes are provided, then `im.width <= width and im.height <= height`.
    """

    def __init__(self, width: int = -1, height: int = -1, *args, **kwargs):
        if width < 0 and height < 0:
            raise ValueError('must provide a positive width and/or height')

        super().__init__(*args, **kwargs)

        self.width = width
        self.height = height

    def transform(self, im: PILImage) -> PILImage:
        # resize
        size = im.size
        new_size_w = self.width, int(size[1] / size[0] * self.width)
        new_size_h = int(size[0] / size[1] * self.height), self.height

        if self.width < 0:
            new_size = new_size_h
        elif self.height < 0:
            new_size = new_size_w
        else:
            if size[0] < size[1]:  # portrait
                new_size = new_size_h
            else:
                new_size = new_size_w

        if new_size[0] <= size[0] and new_size[1] <= size[1]:
            return im.resize(new_size)
        else:
            return im


class Anchor(Enum):
    CENTER = (0, 0)
    NORTH_WEST = (-1, -1)
    NORTH_EAST = (1, -1)
    SOUTH_WEST = (-1, 1)
    SOUTH_EAST = (1, 1)
    NORTH = (0, -1)
    SOUTH = (0, 1)
    WEST = (-1, 0)
    EAST = (1, 0)


class CropPicture(BaseImageTransform):
    """Crop
    """

    def __init__(self, width: int, height: int, anchor: Anchor = Anchor.CENTER, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.width = width
        self.height = height
        self.anchor = anchor

    def transform(self, im: PILImage) -> PILImage:
        # crop
        size = im.size
        offset_x, offset_y = 0, 0

        if self.anchor.value[0] == 0:
            offset_x = int((size[0] - self.width) / 2)
        elif self.anchor.value[0] == 1:
            offset_x = size[0] - self.width

        if self.anchor.value[1] == 0:
            offset_y = int((size[1] - self.height) / 2)
        elif self.anchor.value[1] == 1:
            offset_y = size[1] - self.height

        return im.crop((offset_x, offset_y, offset_x + self.width, offset_y + self.height))


class ScaleAndCropPicture(CropPicture):
    """Resize while keeping the aspect ratio, then crop the largest dimension to meet the crop requirements
    """

    def transform(self, im: PILImage) -> PILImage:
        # resize
        size = im.size
        ratio = size[0] / size[1]
        target_ratio = self.width / self.height

        if ratio > target_ratio:
            new_size = int(self.height * ratio), self.height
        else:
            new_size = self.width, int(self.width / ratio)

        im = im.resize(new_size)

        # crop
        return super().transform(im)


class Thumbnailer:

    THUMBNAIL_DIRECTORY = 'thumb'

    def __init__(
            self, root: pathlib.Path, target: pathlib.Path, session: Session, ttypes: Dict[str, BaseImageTransform]
    ):
        self.root = root
        self.target = target
        self.session = session
        self.thumb_types = ttypes

    def get_thumbnail(self, picture: Picture, ttype: str):
        if ttype not in self.thumb_types:
            raise ValueError('`{}` is not a valid thumbnail type'.format(ttype))

        pass
