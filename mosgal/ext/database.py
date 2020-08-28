import io
import json
import pathlib

from mosgal.seekers import Image
from mosgal.base_models import BaserWriter, BaseTransformer


class ImageDB:
    """
    Database for images.
    Assumes that every attributes has a JSON representation.
    """

    def __init__(self):
        self.from_source = {}

    def load(self, fp: io.FileIO) -> None:
        images = json.load(fp)

        for im in images:
            im_object = Image(im.get('source'), pathlib.Path(im.get('path')))
            im_object.attributes.update(im.get('attributes'))

            if im_object.path.exists():
                self.from_source[im['source']] = im_object

    def dump(self, fp: io.FileIO) -> None:
        images = []

        for im in self.from_source.values():
            images.append({
                'source': str(im.source),
                'path': str(im.path),
                'attributes': im.attributes
            })

        json.dump(images, fp, indent=2)

    def append(self, image: Image) -> None:
        self.from_source[image.source] = image

    def has(self, image) -> bool:
        return image.source in self.from_source


class AddToImageDB(BaseTransformer):
    """
    Add the image to database
    """

    def __init__(self, db: ImageDB):
        super().__init__()

        self.db = db

    def __call__(self, file: Image, *args, **kwargs) -> None:
        self.db.append(file)


class UpdateFromImageDB(BaseTransformer):
    """
    Update attributes out of the database
    """

    def __init__(self, db: ImageDB):
        super().__init__()

        self.db = db

    def __call__(self, file: Image, *args, **kwargs) -> None:
        file.attributes.update(**self.db.from_source[file.source].attributes)


class WriteImageDB(BaserWriter):

    def __init__(self, db: ImageDB, destination: pathlib.Path):
        super().__init__()

        self.db = db
        self.destination = destination

    def __call__(self, *args, **kwargs):
        with self.destination.open('w') as f:
            self.db.dump(f)
