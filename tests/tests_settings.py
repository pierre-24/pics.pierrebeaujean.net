from gallery_generator.controllers.settings import merge_settings, SETTINGS_VALIDATION_SCHEMA, SETTINGS_BASE
from tests import GCTestCase


class SettingsTestCase(GCTestCase):
    def test_settings_merge_ok(self):

        # different settings
        self.assertEqual(
            merge_settings([{'a': 1}, {'b': 2}]),
            {'a': 1, 'b': 2}
        )

        # sub-dict
        self.assertEqual(
            merge_settings([{'a': 1}, {'b': {'x': 1}}]),
            {'a': 1, 'b': {'x': 1}}
        )

        # update same value
        self.assertEqual(
            merge_settings([{'a': 1}, {'a': 2}]),
            {'a': 2}
        )

        # update same value with dict
        self.assertEqual(
            merge_settings([{'a': 1}, {'a': {'x': 1}}]),
            {'a': {'x': 1}}
        )

        # update same value with normal
        self.assertEqual(
            merge_settings([{'a': {'x': 1}}, {'a': 1}]),
            {'a': 1}
        )

        # nested different
        self.assertEqual(
            merge_settings([{'x': {'a': 1}}, {'y': {'b': 2}}]),
            {'x': {'a': 1}, 'y': {'b': 2}}
        )

        self.assertEqual(
            merge_settings([{'x': {'a': 1}}, {'x': {'b': 2}}]),
            {'x': {'a': 1, 'b': 2}}
        )

        self.assertEqual(
            merge_settings([{'x': {'a': 1}}, {'x': {'a': 2}}]),
            {'x': {'a': 2}}
        )

    def test_base_config_valid(self):
        self.assertTrue(SETTINGS_VALIDATION_SCHEMA.is_valid(SETTINGS_BASE))
