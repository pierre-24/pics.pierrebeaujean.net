import pathlib
import re

from typing import Iterable

from gallery_generator import CONFIG_DIR_NAME, CONFIG_DIRS


def create_config_dirs(root: pathlib.Path) -> None:
    """Create the required (sub)directories if they don't exist, following `CONFIG_DIRS`.
    """

    # add tags
    from gallery_generator.controllers.tags import TagManager
    CONFIG_DIRS.append('{}/{}'.format(CONFIG_DIR_NAME, TagManager.TAG_DIRECTORY))

    # create dirs
    for dir in CONFIG_DIRS:
        path = root / dir
        if not path.exists():
            path.mkdir()


def seek_pictures(
        root: pathlib.Path,
        extensions: Iterable[str],
        exclude_dirs: Iterable[str]
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
