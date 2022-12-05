import pathlib
import re

from typing import Iterable

from markdown import markdown

from gallery_generator import CONFIG_DIR_NAME, CONFIG_DIRS, PICTURE_EXTENSIONS, PICTURE_EXCLUDE_DIRS


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


class Page:
    def __init__(self, title: str, slug: str, content: str):
        self.title = title
        self.slug = slug
        self.content = content

    def to_html(self) -> str:
        return markdown(self.content)

    def get_url(self) -> str:
        return '{}.html'.format(self.slug)

    @classmethod
    def create_from_file(cls, path: pathlib.Path):
        with path.open() as f:
            content = f.read()
            title = slug = '.'.join(path.name.split('.')[:-1])

            if content[0] == '#':
                end = content.find('\n')
                if end < 0:
                    end = len(content)

                title = content[1:end].strip()

        return cls(title, slug, content)
