from slugify import slugify

from mosgal.base_models import BaseCharacterizer, Collection


class SortElements(BaseCharacterizer):
    """Sort the elements into a collection given a certain attribute of a given file
    """
    def __init__(self, file_attribute: str, file_position: int = -1):
        super().__init__()

        self.file_attribute = file_attribute
        self.file_position = file_position

    def __call__(self, collection: Collection, *args, **kwargs) -> None:
        collection.elements.sort(key=lambda e: e.files[self.file_position].attributes[self.file_attribute])


class AddTargetCharacteristic(BaseCharacterizer):
    """Add a ``target_file`` characteristic to elements, based on the name of the collection and the element
    """

    def __call__(self, collection: Collection, *args, **kwargs) -> None:
        collection_slug = slugify(collection.name)

        for element in collection.elements:
            element.characteristics['target_file'] = '{}__{}.html'.format(collection_slug, slugify(element.name))


class AddThumbnailCharacteristic(BaseCharacterizer):
    """Select a file to be into the ``thumbnail`` characteristic
    """

    def __init__(self, file_position: int = -1):
        super().__init__()

        self.file_position = file_position

    def __call__(self, collection: Collection, *args, **kwargs) -> None:
        for element in collection.elements:
            element.characteristics['thumbnail'] = element.files[self.file_position]
