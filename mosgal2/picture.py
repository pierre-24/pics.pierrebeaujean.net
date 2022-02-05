from typing import Dict, Union


class Picture:
    def __init__(self, pk: str, data: Dict[str, Union[int, float, str]]):
        self.pk = pk
        self.data = data

        if 'pk' in self.data:
            del self.data['pk']

    def dump(self) -> dict:
        data = {'pk': self.pk}
        data.update(**self.data)
        return data
