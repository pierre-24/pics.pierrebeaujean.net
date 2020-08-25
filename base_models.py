from typing import Callable, Iterator, Iterable, List
import pathlib
import re


class BaseFile:
    def __init__(self, source_path: pathlib.Path):
        self.source_path = source_path
        self.final_path = source_path
        self.attributes = {}


class BaseSeeker:
    def __init__(self):
        pass

    def __call__(self, *args, **kwargs) -> Iterator[BaseFile]:
        raise NotImplementedError()


class FileSeeker:
    def __init__(self, directory: pathlib.Path, extensions: Iterable[str] = ()):
        self.directory = directory
        self.extensions = extensions

    def __call__(self, *args, **kwargs):
        r = re.compile(r'.*\.({})'.format('|'.join(self.extensions)))
        for fname in self.directory.glob('**/*.*'):
            if r.match(str(fname)):
                yield BaseFile(fname)


class BaseTransformer:
    def __init__(self):
        pass

    def __call__(self, file: BaseFile, *args, **kwargs) -> None:
        raise NotImplementedError


class BaseFetcher:
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
    def __init__(self, name: str, files: List[BaseFile] = (), description: str = ''):
        self.name = name
        self.description = description
        self.files = list(files)

    def append(self, file_: BaseFile) -> None:
        self.files.append(file_)


class Collection:
    def __init__(self, name: str, elements: List[Element] = (), description: str = ''):
        self.name = name
        self.description = description
        self.elements = list(elements)

    def append(self, element: Element) -> None:
        self.elements.append(element)


class BaseClassifier:
    def __init__(self, name: str, description: str = ''):
        self.name = name
        self.description = description

    def __call__(self, files: List[BaseFile], *args, **kwargs) -> Collection:
        raise NotImplementedError()


class AttributeClassifier(BaseClassifier):
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
    def __init__(self, fetcher: BaseFetcher = BaseFetcher(), classifiers: Iterable[BaseClassifier] = ()):
        self.fetch = fetcher
        self.classifiers = classifiers

    def __call__(self, *args, **kwargs) -> Iterator[Collection]:
        files = list(self.fetch())

        for classify in self.classifiers:
            yield classify(files)


class BaserWriter:
    def __init__(self):
        pass

    def __call__(self, collections: Iterable[Collection], *args, **kwargs) -> None:
        raise NotImplementedError()


class CollectionWriter(BaserWriter):
    def __init__(self, collection_name):
        super().__init__()
        self.collection_name = collection_name

    def write_collection(self, collection: Collection):
        raise NotImplementedError()

    def __call__(self, collections: Iterable[Collection], *args, **kwargs) -> None:
        for collection in collections:
            if collection.name == self.collection_name:
                self.write_collection(collection)


class BasePipeline:
    def __init__(self, collector: BaseCollector = BaseCollector(), writers: Iterable[BaserWriter] = ()):
        self.collect = collector
        self.writers = writers

    def __call__(self, *args, **kwargs) -> None:
        collections = list(self.collect())

        for write in self.writers:
            write(collections)

