import pathlib

CONFIG_DIR_NAME = '.gallery'

CONFIG_DIRS = [
    '{}'.format(CONFIG_DIR_NAME),        # dir itself

    '{}/tags'.format(CONFIG_DIR_NAME),   # tags
    '{}/pages'.format(CONFIG_DIR_NAME),  # extra pages
]


def create_config_dirs(root: pathlib.Path) -> None:
    """Create the directories"""

    for dir in CONFIG_DIRS:
        path = root / dir
        if not path.exists():
            path.mkdir()
