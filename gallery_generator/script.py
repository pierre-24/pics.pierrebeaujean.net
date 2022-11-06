import argparse
import pathlib
import sys

from gallery_generator.files import create_config_dirs
from gallery_generator.database import GalleryDatabase, Picture
from gallery_generator.files import seek_pictures
from gallery_generator.tag import TagManager
from gallery_generator.picture import create_picture_object


def exit_failure(msg: str, code: int = -1):
    print(msg, file=sys.stderr)
    return sys.exit(code)


def command_init(root: pathlib.Path, db: GalleryDatabase):
    """Create the config directories and database"""

    # create config dirs
    create_config_dirs(root)

    # remove existing db and create a new one
    if db.path.exists():
        db.path.unlink()

    db.create_schema()


def command_crawl(root: pathlib.Path, db: GalleryDatabase):
    """Go through all accessible pictures in the root directory, then for each of them

    - check if they are already in the database, and if not,
    - add them to the database, gathering the infos
    - tag them accordingly, creating tags if required
    """

    if not db.exists():
        raise FileNotFoundError('database file `{}` does not exists'.format(db.path))

    with db.session() as session:
        tag_manager = TagManager(root, session)
        for path in seek_pictures(root):
            if session.execute(Picture.count().where(Picture.path == str(path))).scalar_one() == 0:
                picture = create_picture_object(root, path)
                tag_manager.tag_picture(picture)
                session.add(picture)
                session.commit()


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
        return exit_failure('source directory `{}` does not exists'.format(args.source))

    db = GalleryDatabase(args.source)

    try:
        if args.init:
            command_init(args.source, db)
        elif args.crawl:
            command_crawl(args.source, db)
    except Exception as e:
        return exit_failure('Error while executing command: {}'.format(e))


if __name__ == '__main__':
    main()
