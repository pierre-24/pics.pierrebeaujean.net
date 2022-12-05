"""
Generate a static website with a gallery
"""

import logging
import os

__version__ = '0.1'
__author__ = 'Pierre Beaujean'
__maintainer__ = 'Pierre Beaujean'
__email__ = 'pierreb24@gmail.com'
__status__ = 'Development'


# logging
logging.basicConfig(level=logging.WARNING)

logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get('LOGLEVEL', 'WARNING'))
logger.info('This is {} v{}'.format(__name__, __version__))

# config
CONFIG_DIR_NAME = '.gallery'
PAGE_DIR_NAME = 'pages'

CONFIG_DIRS = [
    '{}'.format(CONFIG_DIR_NAME),  # dir itself
    '{}/{}'.format(CONFIG_DIR_NAME, PAGE_DIR_NAME),  # extra pages
]

CONFIG = {
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
        'picture_exts': ('jpg', 'JPG', 'JPEG', 'jpeg'),
        'excluded_dirs': (),
    },
    'update': {
        'site_name': 'Gallery test',
        'index_categories_to_show': ('album', 'date')
    }
}
