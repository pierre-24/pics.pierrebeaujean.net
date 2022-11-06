import pathlib
import re

from typing import Iterable

CONFIG_DIR_NAME = '.gallery'

CONFIG_DIRS = [
    '{}'.format(CONFIG_DIR_NAME),        # dir itself

    '{}/tags'.format(CONFIG_DIR_NAME),   # tags
    '{}/pages'.format(CONFIG_DIR_NAME),  # extra pages
]


def create_config_dirs(root: pathlib.Path) -> None:
    """Create the required (sub)directories if they don't exist, following `CONFIG_DIRS`.
    """

    for dir in CONFIG_DIRS:
        path = root / dir
        if not path.exists():
            path.mkdir()


PICTURE_EXTENSIONS = ('jpg', 'JPG', 'JPEG', 'jpeg')
PICTURE_EXCLUDE_DIRS = ()


def seek_pictures(
        root: pathlib.Path,
        extensions: Iterable[str] = PICTURE_EXTENSIONS,
        exclude_dirs: Iterable[str] = PICTURE_EXCLUDE_DIRS
) -> Iterable[pathlib.Path]:
    """Look in subdirectories of `root` for all pictures, recognized by their extension.

    Return an iterable of path to pictures, relative to `root`.
    """

    r = re.compile(r'.*\.({})'.format('|'.join(extensions)))

    for dir in root.iterdir():
        if dir.name in exclude_dirs:
            continue

        for f in dir.glob('*.*'):
            if r.match(str(f)):
                yield f.relative_to(root)
