import yaml
from typing import Dict, TextIO, List

from mosgal2.picture import Picture
from mosgal2 import filters


class Library:
    def __init__(self):
        self.data: Dict[str, Picture] = {}

    def read(self, fp: TextIO):
        data = yaml.load(fp, Loader=yaml.Loader)

        if type(data) is not list:
            raise Exception('Library should be a list')

        for item in data:
            if 'pk' not in item:
                raise Exception('no pk in {}'.format(item))

            self.data[item['pk']] = Picture(item['pk'], item)

    def write(self, fp: TextIO):
        data = []
        for pic in self.data.values():
            data.append(pic.dump())

        yaml.dump(data, fp, Dumper=yaml.Dumper)

    def select(self, **kwargs) -> List[Picture]:

        fltrs = []

        for key, val in kwargs.items():
            if issubclass(type(val), filters.Data):
                val.field = key
                fltrs.append(val)
            else:
                fltrs.append(filters.Is(val, key))

        request = filters.And(fltrs)

        return list(filter(request, self.data.values()))
