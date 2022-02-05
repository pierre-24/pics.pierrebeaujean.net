from mosgal2.picture import Picture
from typing import List


class Filter:
    def select(self, item: Picture) -> bool:
        raise NotImplementedError()

    def __call__(self, item) -> bool:
        return self.select(item)


class And(Filter):
    def __init__(self, filters: List[Filter]):
        self.filters = filters

    def select(self, item: Picture) -> bool:
        return all(f(item) for f in self.filters)


class Or(And):
    def select(self, item: Picture) -> bool:
        return any(f(item) for f in self.filters)


class Data(Filter):
    def __init__(self, field: str = None):
        self.field = field

    def select(self, item: Picture) -> bool:
        if self.field not in item.data:
            return False
        else:
            return self.select_on_data(item.data[self.field])

    def select_on_data(self, data) -> bool:
        raise NotImplementedError()


class Is(Data):
    def __init__(self, value, field: str = None):
        super().__init__(field)
        self.value = value

    def select_on_data(self, data) -> bool:
        return data == self.value


class In(Data):
    def __init__(self, values: list, field: str = None):
        super().__init__(field)
        self.values = values

    def select_on_data(self, data) -> bool:
        return data in self.values
