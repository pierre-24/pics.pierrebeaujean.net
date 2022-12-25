import argparse
import pathlib
import yaml

from gallery_generator import CONFIG_DIR_NAME
from gallery_generator.controllers.database import GalleryDatabase
from gallery_generator.scripts import exit_failure
from gallery_generator.scripts.crawl import command_crawl
from gallery_generator.scripts.init import command_init
from gallery_generator.scripts.update import command_update
from gallery_generator.controllers.settings import SETTINGS_BASE, merge_settings, SETTINGS_VALIDATION_SCHEMA


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('source', help='source directory', type=pathlib.Path)

    parser.add_argument('-i', '--init', action='store_true', help='Initialize')
    parser.add_argument('-c', '--crawl', action='store_true', help='Update the database with new pictures')
    parser.add_argument('-u', '--update', type=pathlib.Path, help='Create a static website in a folder')

    args = parser.parse_args()

    # check path
    if not args.source.exists():
        return exit_failure('source directory `{}` does not exists'.format(args.source))

    if not args.source.is_dir():
        return exit_failure('source `{}` is not a directory'.format(args.source))

    # fetch settings, if any
    settings = SETTINGS_BASE
    path_settings = args.source / CONFIG_DIR_NAME / 'settings.yml'

    if path_settings.exists():
        with path_settings.open() as f:
            new_settings = yaml.load(f, Loader=yaml.Loader)
            settings = SETTINGS_VALIDATION_SCHEMA.validate(merge_settings([settings, new_settings]))

    # database
    db = GalleryDatabase(args.source)

    # do stuffs
    if args.init:
        command_init(args.source, db)
    if args.crawl:
        command_crawl(args.source, settings, db)
    if args.update:
        if not args.update.exists():
            args.update.mkdir()

        command_update(args.source, settings, db, args.update)


if __name__ == '__main__':
    main()
