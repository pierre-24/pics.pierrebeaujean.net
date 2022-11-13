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


logging.basicConfig(level=logging.WARNING)

logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get('LOGLEVEL', 'WARNING'))
logger.info('This is {} v{}'.format(__name__, __version__))
