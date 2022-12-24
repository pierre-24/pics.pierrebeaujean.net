from schema import Schema, Optional

from typing import List

CONFIG_BASE = {
    'thumbnails': {
        'gallery_small': {
            'type': 'Scale',
            'width': 300
        },
        'gallery_large': {
            'type': 'Scale',
            'width': 1920,
            'height': 1920
        },
        'tag_thumbnail': {
            'type': 'ScaleAndCrop',
            'width': 300,
            'height': 225
        }
    },
    'crawl': {
        'picture_exts': ['jpg', 'JPG', 'JPEG', 'jpeg'],
        'excluded_dirs': [],
    },
    'update': {
        'site_name': 'Gallery test',
        'index_categories_to_show': ['album', 'date']
    }
}

CONFIG_SCHEMA = Schema({
    'thumbnails': {str: {'type': str, 'width': int, Optional('height'): int}},
    'crawl': {
        'picture_exts': [str],
        'excluded_dirs': [str]
    },
    'update': {
        'site_name': str,
        'index_categories_to_show': [str]
    }
})


def _walk_and_update(base: dict, other: dict):
    for k in other:
        if k in base and type(base[k]) is dict and type(other[k]) is dict:
            _walk_and_update(base[k], other[k])
        else:
            base[k] = other[k]


def merge_settings(settings: List[dict]) -> dict:
    if len(settings) == 0:
        return {}

    base = settings[0]

    for other in settings[1:]:
        _walk_and_update(base, other)

    return base
