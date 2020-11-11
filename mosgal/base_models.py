"""
The idea behind this is simple:

1) A "fetcher" find some files (through a "seeker") and apply a bunch of transformations on them
   (which populates their attributes)
2) Based on that, a "collector" get the files and apply a bunch of classifiers on them
   (which sort the files into different "element" of a "collection")
3) Based on that, a "publisher" get the collection and apply a bunch of writers on them
   (which write stuffs based on that).
"""

from typing import Iterator, Iterable, List, Callable
import pathlib


class BaseFile:
    """
    Represent a file, with a path and some attributes

    Note that ``source`` is a free format string,
    while ``path`` should correspond to the actual location of the file (in the local filesystem).
    """

    def __init__(self, source: str, path: pathlib.Path):
        self.source = source
        self.path = path
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
    """Element of a ``Collection``, which contains files and has ``attributes``
    """

    def __init__(self, name: str, files: List[BaseFile] = ()):
        self.name = name
        self.characteristics = {}

        self.files = list(files)

    def append(self, file_: BaseFile) -> None:
        self.files.append(file_)


class Collection:
    """Collection of ``Element`` (probably based on a sorting criterion)
    """
    def __init__(self, name: str, elements: List[Element] = ()):
        self.name = name
        self.characteristics = {}

        self.elements = list(elements)

    def append(self, element: Element) -> None:
        self.elements.append(element)


class BaseClassifier:
    """Classify files into a ``Collection``.
    """
    def __init__(self, name: str):
        self.name = name

    def __call__(self, files: List[BaseFile], *args, **kwargs) -> Collection:
        raise NotImplementedError()


class BaseCharacterizer:
    """Characterize a collection (add attributes)
    """

    def __init__(self):
        pass

    def __call__(self, collection: Collection, *args, **kwargs) -> None:
        pass


class BaseCollector:
    """Collect files (through fetcher) and apply a bunch of ``BaseClassifier`` on them.
    """

    def __init__(
            self,
            fetcher: BaseFetcher = BaseFetcher(),
            classifiers: Iterable[BaseClassifier] = (),
            characterizers: Iterable[BaseCharacterizer] = (),
            organizer: Callable = lambda li: li):
        self.fetch = fetcher
        self.classifiers = classifiers
        self.characterizers = characterizers
        self.organize = organizer

    def __call__(self, *args, **kwargs) -> Iterator[Collection]:
        files = self.organize(self.fetch())

        for classify in self.classifiers:
            c = classify(files)
            for characterize in self.characterizers:
                characterize(c)
            yield c


class BaserWriter:
    """Write stuffs, based on the different collections
    """

    def __init__(self):
        pass

    def __call__(self, collections: Iterable[Collection], destination: pathlib.Path, *args, **kwargs) -> None:
        raise NotImplementedError()


class BasePublisher:
    """Get collections (from collector) and apply a bunch of ``BaseWriter`` on them.
    """

    def __init__(
            self,
            destination: pathlib.Path,
            collector: BaseCollector = BaseCollector(),
            writers: Iterable[BaserWriter] = ()):

        self.destination = destination
        self.collect = collector
        self.writers = writers

    def __call__(self, *args, **kwargs) -> None:
        collections = list(self.collect())

        for write in self.writers:
            write(collections, self.destination)
