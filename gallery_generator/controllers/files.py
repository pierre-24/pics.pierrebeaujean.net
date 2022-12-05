import pathlib

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
