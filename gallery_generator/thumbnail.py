import pathlib
from enum import Enum
from typing import Dict
from sqlalchemy.orm import Session

from PIL import Image as PILImage

from gallery_generator.database import Picture, Thumbnail


class BaseImageTransform:
    EXIF_ROT_TAG = 0x0112

    def __init__(self, output_format: str = 'JPEG', encoder_options: dict = {'quality': 85}):
        self.output_format = output_format
        self.encoder_options = encoder_options
        self._rotate = True

    def _get_subname(self) -> str:
        raise NotImplementedError()

    def get_name(self, base: str):
        return '{}_{}.{}'.format(base, self._get_subname(), self.output_format)

    def transform(self, im: PILImage, *args, **kwargs) -> PILImage:
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
        self.transform(im, *args, **kwargs).save(path_out, self.output_format, **self.encoder_options)


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

    def _get_subname(self) -> str:
        if not self.width:
            return 'sh{}'.format(self.height)
        elif not self.height:
            return 'sw{}'.format(self.width)
        else:
            return 's{}x{}'.format(self.width, self.height)

    def transform(self, im: PILImage, *args, **kwargs) -> PILImage:
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

    def _get_subname(self) -> str:
        return 'c{}x{}'.format(self.width, self.height)

    def transform(self, im: PILImage, *args, **kwargs) -> PILImage:
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

    def _get_subname(self) -> str:
        return 'sc{}x{}'.format(self.width, self.height)

    def transform(self, im: PILImage, *args, **kwargs) -> PILImage:
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

    THUMBNAIL_DIRECTORY = pathlib.Path('thumb')

    def __init__(
        self, root: pathlib.Path, target: pathlib.Path, session: Session, thumb_types: Dict[str, BaseImageTransform]
    ):
        self.root = root
        self.target = target
        self.session = session
        self.thumb_types = thumb_types

    def _create_thumbnail(self, picture: Picture, ttype: str) -> Thumbnail:
        transformer: BaseImageTransform = self.thumb_types[ttype]
        name = transformer.get_name('{}_id{}'.format(pathlib.Path(picture.path).parent.name, picture.id))

        transformer(self.root / picture.path, self.target / self.THUMBNAIL_DIRECTORY / name)

        thumb = Thumbnail.create(picture.id, str(self.THUMBNAIL_DIRECTORY / name), ttype)
        picture.thumbnails.append(thumb)
        self.session.add(thumb)
        self.session.commit()

        return thumb

    def get_thumbnail(self, picture: Picture, ttype: str) -> Thumbnail:
        if ttype not in self.thumb_types:
            raise ValueError('`{}` is not a valid thumbnail type'.format(ttype))

        for thumb in picture.thumbnails:
            if thumb.type == ttype:
                return thumb

        return self._create_thumbnail(picture, ttype)
