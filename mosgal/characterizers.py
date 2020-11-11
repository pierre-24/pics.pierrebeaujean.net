from typing import Callable
from slugify import slugify
from markdown import markdown

from mosgal.base_models import BaseCharacterizer, Collection, Element


class SortElements(BaseCharacterizer):
    """Sort the elements into a collection given a certain attribute of a given file
    """
    def __init__(self, file_attribute: str, file_position: int = -1):
        super().__init__()

        self.file_attribute = file_attribute
        self.file_position = file_position

    def __call__(self, collection: Collection, *args, **kwargs) -> None:
        collection.elements.sort(key=lambda e: e.files[self.file_position].attributes[self.file_attribute])


def get_target(collection: Collection, element: Element):
    return '{}__{}.html'.format(slugify(collection.name), slugify(element.name))


class AddTargetCharacteristic(BaseCharacterizer):
    """Add a ``target_file`` characteristic to elements, based on the name of the collection and of the element
    """

    def __init__(self, get_target: Callable = get_target):
        super().__init__()
        self.get_target = get_target

    def __call__(self, collection: Collection, *args, **kwargs) -> None:

        for element in collection.elements:
            element.characteristics['target_file'] = self.get_target(collection, element)


class AddThumbnailCharacteristic(BaseCharacterizer):
    """Select a file to be into the ``thumbnail`` characteristic
    """

    def __init__(self, file_attribute: str, file_position: int = -1):
        super().__init__()

        self.file_attribute = file_attribute
        self.file_position = file_position

    def __call__(self, collection: Collection, *args, **kwargs) -> None:
        for element in collection.elements:
            element.characteristics['thumbnail'] = element.files[self.file_position].attributes[self.file_attribute]


class AddAlbumCharacteristics(BaseCharacterizer):
    """Extract some extra characteristics of an element into a ``index.md`` file found in the same directory as
    the images.

    If it exists, it can start by:

    + ``Title: xxx``, which changes the name of the element to ``xxx``,
    + ``Thumbnail: xxx``, which changes the ``thumbnail`` characteristic of the element to the corresponding thumbnail.

    The rest is taken as the ``description`` characteristic, formatted in Markdown.
    """

    def __init__(self, collection_name: str, thumbnail_file_attribute: str):
        super().__init__()

        self.collection_name = collection_name
        self.thumbnail_file_attribute = thumbnail_file_attribute

    def __call__(self, collection: Collection, *args, **kwargs) -> None:
        if collection.name != self.collection_name:
            return

        for element in collection.elements:
            # try to find a index.md file
            path = element.files[-1].path.parent.joinpath('index.md')
            if path.exists():
                with path.open() as f:
                    content = f.read()

                lines = content.splitlines()

                index = 0
                has_description = False
                for index, line in enumerate(lines):
                    if ':' not in line:
                        has_description = True
                        break

                    key, val = line.split(':', maxsplit=1)
                    if key == 'Title':
                        element.name = val.strip()
                    elif key == 'Thumbnail':
                        file = next(filter(lambda fi: fi.path.name == val.strip(), element.files))
                        element.characteristics['thumbnail'] = file.attributes[self.thumbnail_file_attribute]
                    else:
                        has_description = True
                        break

                if index < len(lines) - 1 or has_description:
                    element.characteristics['description'] = markdown('\n'.join(lines[index:]))
