import argparse
import pathlib

from gallery_generator.controllers.database import GalleryDatabase
from gallery_generator.scripts import exit_failure
from gallery_generator.scripts.crawl import command_crawl
from gallery_generator.scripts.init import command_init
from gallery_generator.scripts.update import command_update


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('source', help='source directory', type=pathlib.Path)

    parser.add_argument('-i', '--init', action='store_true', help='Initialize')
    parser.add_argument('-c', '--crawl', action='store_true', help='Update the database with new pictures')
    parser.add_argument('-u', '--update', type=pathlib.Path, help='Create a static website')

    args = parser.parse_args()

    # check path
    if not args.source.exists():
        return exit_failure('source directory `{}` does not exists'.format(args.source))

    db = GalleryDatabase(args.source)

    try:
        if args.init:
            command_init(args.source, db)
        if args.crawl:
            command_crawl(args.source, db)
        if args.update:
            command_update(args.source, db, args.update)
    except (FileNotFoundError, ValueError) as e:
        return exit_failure('Error while executing command: {}'.format(e))


if __name__ == '__main__':
    main()
