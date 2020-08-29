from typing import Callable, Iterable, List

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
            description: str = '',
            target: str = '',
            get_element_name: Callable = lambda n: n,
            get_element_description: Callable = lambda n: '',
            get_element_target: Callable = lambda n: '',
            exclude: Iterable[str] = ()):
        super().__init__(name=name if name is not None else attribute, description=description, target=target)

        self.attribute = attribute
        self.get_element_name = get_element_name
        self.get_element_description = get_element_description
        self.get_element_target = get_element_target
        self.exclude = exclude

    def __call__(self, files: List[BaseFile], *args, **kwargs) -> Collection:
        elements = {}

        def treat_values(val_, file_):
            if val_ in self.exclude:
                return

            if val_ not in elements:
                name = self.get_element_name(val_)
                el = Element(
                    name, description=self.get_element_description(val_), target=self.get_element_target(name))
                elements[val_] = el

            elements[val_].append(file_)

        for f in files:
            value = f.attributes.get(self.attribute, None)

            if value is None:
                continue

            if type(value) in [list, tuple, set]:
                list(treat_values(v, f) for v in value)
            else:
                treat_values(value, f)

        return Collection(
            self.name, description=self.description, elements=list(elements.values()), target=self.target)
