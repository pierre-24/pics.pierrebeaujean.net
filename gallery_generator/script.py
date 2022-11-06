import argparse
import pathlib
import sys

from gallery_generator.files import create_config_dirs
from gallery_generator.database import GalleryDatabase


def exit_failure(msg: str, code: int = -1):
    print(msg, file=sys.stderr)
    return sys.exit(code)


def command_init(root: pathlib.Path, db: GalleryDatabase):
    """Create the config directories and database"""

    # create config dirs
    create_config_dirs(root)

    # create schema
    db.create_schema()


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('source', help='source directory', type=pathlib.Path)

    meg = parser.add_mutually_exclusive_group()

    meg.add_argument('-i', '--init', action='store_true', help='Initialize')
    meg.add_argument('-c', '--crawl', action='store_true', help='Update the database with new pictures')
    meg.add_argument('-o', '--output', type=pathlib.Path, help='Create a static website')

    args = parser.parse_args()

    # check path
    if not args.source.exists():
        return exit_failure('source `{}` does not exists'.format(args.source))

    db = GalleryDatabase(args.source)

    # init
    if args.init:
        try:
            command_init(args.source, db)
        except Exception as e:
            return exit_failure(str(e))


if __name__ == '__main__':
    main()
