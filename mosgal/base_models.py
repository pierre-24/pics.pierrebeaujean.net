"""
The idea behind this is simple:

1) A "fetcher" find some files (through a "seeker") and apply a bunch of transformations on them
   (which populates their attributes)
2) Based on that, a "collector" get the files and apply a bunch of classifiers on them
   (which sort the files into different "element" of a "collection")
3) Based on that, a "publisher" get the collection and apply a bunch of writers on them
   (which write stuffs based on that).
"""

from typing import Callable, Iterator, Iterable, List
import pathlib


class BaseFile:
    """Represent a file, with a path and some attributes"""
    def __init__(self, source_path: pathlib.Path):
        self.source_path = source_path
        self.final_path = source_path
        self.attributes = {}


class BaseSeeker:
    """Seek for ``BaseFile``
    """
    def __init__(self):
        pass

    def __call__(self, *args, **kwargs) -> Iterator[BaseFile]:
        raise NotImplementedError()


class BaseTransformer:
    """ "Transform" a ``BaseFile`` (modify its attributes)
    """
    def __init__(self):
        pass

    def __call__(self, file: BaseFile, *args, **kwargs) -> None:
        raise NotImplementedError


class BaseFetcher:
    """Fetch files trough a seeker, and apply a bunch of transformation to them
    """
    def __init__(
            self,
            seeker: BaseSeeker = BaseSeeker(),
            transformers: Iterable[BaseTransformer] = ()):

        self.seek = seeker
        self.transformers = transformers

    def __call__(self, *args, **kwargs) -> Iterator[BaseFile]:
        for f in self.seek():
            for transform in self.transformers:
                transform(f)
            yield f


class Element:
    """Element of a ``Collection``, which contains files.
    """
    def __init__(self, name: str, files: List[BaseFile] = (), description: str = ''):
        self.name = name
        self.description = description
        self.files = list(files)

    def append(self, file_: BaseFile) -> None:
        self.files.append(file_)


class Collection:
    """Collection of ``Element`` (probably based on a sorting criterion)
    """
    def __init__(self, name: str, elements: List[Element] = (), description: str = ''):
        self.name = name
        self.description = description
        self.elements = list(elements)

    def append(self, element: Element) -> None:
        self.elements.append(element)


class BaseClassifier:
    """Classify files into a ``Collection``.
    """
    def __init__(self, name: str, description: str = ''):
        self.name = name
        self.description = description

    def __call__(self, files: List[BaseFile], *args, **kwargs) -> Collection:
        raise NotImplementedError()


class AttributeClassifier(BaseClassifier):
    """"
    Classify files based on a given attribute
    (all files with the same value for said attribute end up in the same ``Element``)
    """

    def __init__(
            self,
            attribute: str,
            name: str = None,
            description: str = '',
            get_element_name: Callable = lambda n: n,
            get_element_description: Callable = lambda n: ''):
        super().__init__(name=name if name is not None else attribute, description=description)

        self.attribute = attribute
        self.get_element_name = get_element_name
        self.get_element_description = get_element_description

    def __call__(self, files: List[BaseFile], *args, **kwargs) -> Collection:
        elements = {}

        for f in files:
            value = f.attributes.get(self.attribute, None)
            if value not in elements:
                elements[value] = Element(
                    self.get_element_name(value), description=self.get_element_description(value))

            elements[value].append(f)

        return Collection(self.name, description=self.description, elements=list(elements.values()))


class BaseCollector:
    """Collect files (through fetcher) and apply a bunch of ``BaseClassifier`` on them.
    """

    def __init__(self, fetcher: BaseFetcher = BaseFetcher(), classifiers: Iterable[BaseClassifier] = ()):
        self.fetch = fetcher
        self.classifiers = classifiers

    def __call__(self, *args, **kwargs) -> Iterator[Collection]:
        files = list(self.fetch())

        for classify in self.classifiers:
            yield classify(files)


class BaserWriter:
    """Write stuffs, based on the different collections
    """
    def __init__(self):
        pass

    def __call__(self, collections: Iterable[Collection], *args, **kwargs) -> None:
        raise NotImplementedError()


class CollectionWriter(BaserWriter):
    """Write stuffs for a given collection (selected by its name)
    """
    def __init__(self, collection_name):
        super().__init__()
        self.collection_name = collection_name

    def write_collection(self, collection: Collection):
        raise NotImplementedError()

    def __call__(self, collections: Iterable[Collection], *args, **kwargs) -> None:
        for collection in collections:
            if collection.name == self.collection_name:
                self.write_collection(collection)


class BasePublisher:
    """Get collections (from collector) and apply a bunch of ``BaseWriter`` on them.
    """

    def __init__(self, collector: BaseCollector = BaseCollector(), writers: Iterable[BaserWriter] = ()):
        self.collect = collector
        self.writers = writers

    def __call__(self, *args, **kwargs) -> None:
        collections = list(self.collect())

        for write in self.writers:
            write(collections)

