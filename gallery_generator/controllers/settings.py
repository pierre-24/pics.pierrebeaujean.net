from schema import Schema, Optional

from typing import List

SETTINGS_BASE = {
    'crawl_phase': {
        'picture_exts': ['jpg', 'JPG', 'JPEG', 'jpeg'],
        'excluded_dirs': [],
    },
    'update_phase': {
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
        'page_context': {
            'site_name': 'Gallery test',
            'index_categories_to_show': ['album', 'date']
        }
    }
}

SETTINGS_VALIDATION_SCHEMA = Schema({
    'crawl_phase': {
        'picture_exts': [str],
        'excluded_dirs': [str]
    },
    'update_phase': {
        'thumbnails': {str: {'type': str, 'width': int, Optional('height'): int}},
        'page_context': {
            'site_name': str,
            'index_categories_to_show': [str]
        }
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
