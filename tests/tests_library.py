from mosgal2.picture import Picture
from mosgal2.library import Library
from mosgal2 import filters

from tests import Mosgal2TestCase


class LibraryTests(Mosgal2TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.library = Library()

        self.pic1 = Picture('x', {'a': 1, 'b': 1})
        self.library.data[self.pic1.pk] = self.pic1

        self.pic2 = Picture('y', {'a': 2, 'b': 1})
        self.library.data[self.pic2.pk] = self.pic2

        self.pic3 = Picture('y', {'a': 1, 'b': 2})
        self.library.data[self.pic3.pk] = self.pic3

    def test_request(self):
        # select using indirect "is"
        matched = self.library.select(a=1, b=1)
        self.assertEqual(len(matched), 1)
        self.assertEqual(matched[0], self.pic1)

        # select using filters
        matched = self.library.select(a=filters.In([1, 3]), b=1)
        self.assertEqual(len(matched), 1)
        self.assertEqual(matched[0], self.pic1)

        # select using filters
        matched = self.library.select(a=filters.Is(1) | filters.Is(3), b=1)
        self.assertEqual(len(matched), 1)
        self.assertEqual(matched[0], self.pic1)
