from typing import Iterable, List

from mosgal.base_models import BaseClassifier, BaseFile, Collection, Element


class AttributeClassifier(BaseClassifier):
    """"
    Classify files based on a given attribute
    (all files with the same value for said attribute end up in the same ``Element``)
    """

    def __init__(
            self,
            attribute: str,
            name: str = None,
            exclude: Iterable[str] = ()):
        super().__init__(name=name if name is not None else attribute)

        self.attribute = attribute
        self.exclude = exclude

    def __call__(self, files: List[BaseFile], *args, **kwargs) -> Collection:
        elements = {}
        collection = Collection(self.name)

        def treat_values(val_, file_):
            if val_ in self.exclude:
                return

            if val_ not in elements:
                elements[val_] = Element(val_)

            elements[val_].append(file_)

        for f in files:
            value = f.attributes.get(self.attribute, None)

            if value is None:
                continue

            if type(value) in [list, tuple, set]:
                list(treat_values(v, f) for v in value)
            else:
                treat_values(value, f)

        collection.elements = list(elements.values())
        return collection
