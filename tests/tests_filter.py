from mosgal2.picture import Picture
from mosgal2 import filters

from tests import Mosgal2TestCase


class FilterTests(Mosgal2TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.pic1 = Picture('x', {'a': 1, 'b': 1})
        self.pic2 = Picture('y', {'a': 2, 'b': 1})
        self.pic3 = Picture('y', {'a': 1, 'b': 2})

        self.pics = [self.pic1, self.pic2, self.pic3]

    def filter(self, fltr: filters.Filter, pics: list) -> list:
        return list(filter(fltr, pics))

    def test_is_filter(self):
        # match one
        matched = self.filter(filters.Is(2, 'a'), self.pics)
        self.assertEqual(len(matched), 1)
        self.assertEqual(matched[0], self.pic2)

        # match none
        matched = self.filter(filters.Is(5, 'a'), self.pics)
        self.assertEqual(len(matched), 0)

    def test_or_filter(self):
        # match all
        matched = self.filter(filters.Or([filters.Is(1, 'a'), filters.Is(1, 'b')]), self.pics)
        self.assertEqual(len(matched), 3)

    def test_and_filter(self):
        # match one
        matched = self.filter(filters.And([filters.Is(1, 'a'), filters.Is(1, 'b')]), self.pics)
        self.assertEqual(len(matched), 1)
        self.assertEqual(matched[0], self.pic1)

    def test_in_filter(self):
        # match one
        matched = self.filter(filters.In([2, 4], 'a'), self.pics)
        self.assertEqual(len(matched), 1)
        self.assertEqual(matched[0], self.pic2)

        # match all
        matched = self.filter(filters.In([1, 2], 'a'), self.pics)
        self.assertEqual(len(matched), 3)

        # match none
        matched = self.filter(filters.In([4, 5], 'a'), self.pics)
        self.assertEqual(len(matched), 0)