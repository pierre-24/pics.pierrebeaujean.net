import argparse
import pathlib
import sys

from gallery_generator.files import create_config_dirs
from gallery_generator.database import GalleryDatabase, Picture, Category, Tag
from gallery_generator.files import seek_pictures
from gallery_generator.tag import TagManager
from gallery_generator.picture import create_picture_object


def exit_failure(msg: str, code: int = -1):
    print(msg, file=sys.stderr)
    return sys.exit(code)


CHAR_PER_LINE = 70


def print_title(title: str):
    print('--- ', end='')
    print(title, end='')
    print('', '-' * (CHAR_PER_LINE - 5 - len(title)))


def status(root, db: GalleryDatabase):
    print_title('Status')
    if db.path.exists():
        with db.make_session() as session:
            print('Database `{}` exists:'.format(db.path))
            print('- {} Picture(s)'.format(session.execute(Picture.count()).scalar_one()))
            print('- {} Category(ies)'.format(session.execute(Category.count()).scalar_one()))
            print('- {} Tags(s)'.format(session.execute(Tag.count()).scalar_one()))
    else:
        print('Database `{}` does not exists.'.format(db.path))

    print('-' * CHAR_PER_LINE)
    print()


def command_init(root: pathlib.Path, db: GalleryDatabase, verbose: bool = False):
    """Create the config directories and database"""

    if verbose:
        print_title('Initialization phase')
        print('Create config dir in `{}`'.format(root), end='')

    # create config dirs
    create_config_dirs(root)

    if verbose:
        print(' [OK]')

    # remove existing db and create a new one
    if verbose:
        print('Create database in `{}`'.format(db.path), end='')

    if db.path.exists():
        db.path.unlink()

    if verbose:
        print(' [OK]')

    # create schema
    if verbose:
        print('Create schema', end='')

    db.create_schema()

    if verbose:
        print(' [OK]')
        print('-' * CHAR_PER_LINE)
        print()


def command_crawl(root: pathlib.Path, db: GalleryDatabase, verbose: bool = False):
    """Go through all accessible pictures in the root directory, then for each of them

    - check if they are already in the database, and if not,
    - add them to the database, gathering the infos
    - tag them accordingly, creating tags if required
    """

    if not db.exists():
        raise FileNotFoundError('database file `{}` does not exists'.format(db.path))

    if verbose:
        print_title('Crawling phase')

    with db.make_session() as session:
        tag_manager = TagManager(root, session, verbose=verbose)

        for path in seek_pictures(root):
            if verbose:
                print('Found {}'.format(path), end='')

            if session.execute(Picture.count().where(Picture.path == str(path))).scalar_one() == 0:
                picture = create_picture_object(root, path)
                tag_manager.tag_picture(picture)
                session.add(picture)
                session.commit()

                if verbose:
                    print(' [ADD]')

            elif verbose:
                print(' [DB]')

    if verbose:
        print('-' * CHAR_PER_LINE)
        print()


def command_update(root: pathlib.Path, db: GalleryDatabase, out=pathlib.Path, verbose: bool = False):
    """Update/create the static website:
    - Compile SCSS into CSS
    - Create a page for each tag that contains an image
    - Create index
    - Create additional page(s)
    """

    if verbose:
        print_title('Update phase')

    if verbose:
        print('-' * CHAR_PER_LINE)
        print()


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('source', help='source directory', type=pathlib.Path)
    parser.add_argument('-v', '--verbose', action='store_true', help='verbose output')

    meg = parser.add_mutually_exclusive_group(required=True)

    meg.add_argument('-s', '--status', action='store_true', help='Get status')
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
            command_init(args.source, db, args.verbose)
        elif args.crawl:
            command_crawl(args.source, db, args.verbose)
        elif args.update:
            command_update(args.source, db, args.update, args.verbose)
        elif args.status:
            status(args.source, db)
    except Exception as e:
        return exit_failure('Error while executing command: {}'.format(e))


if __name__ == '__main__':
    main()
