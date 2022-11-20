#!/usr/bin/env python3

import argparse
import os
import sys

from pathlib import Path
from string import ascii_letters, digits

POSIX_PORTABLE_FILENAME_CHARACTERS = ascii_letters + digits + '._-'


def parse_args(args: list[str] = None):
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(description='Logs filenames, under a '
                                                 'directory, whose naming includes '
                                                 'characters, that are not in the POSIX '
                                                 'portable file name character set')

    parser.add_argument('path', nargs='?', type=Path, default=os.getcwd(),
                        help='the path under which to search, defaults to cwd')
    parser.add_argument('-e', '--excluded', nargs='+', type=Path,
                        help='exclude these paths')
    parser.add_argument('-s', '--symbols', help='a string of allowed characters')

    return parser.parse_args(args)


def offending_paths(top: str | Path,
                    excluded: list[str | Path] = None,
                    allowed_chars: str = POSIX_PORTABLE_FILENAME_CHARACTERS):
    # initialise excluded paths if not passed explicitly
    excluded = [] if excluded is None else excluded

    # make sure paths are properly resolved and absolute
    top = Path(top).resolve()
    excluded = [Path(ex).resolve() for ex in excluded]

    # if the passed path does not exist we can't proceed
    if not top.exists():
        raise ValueError(f'{top} does not exist')

    # if the passed path is a file
    if not top.is_dir():
        file = top
        # we walk the parent directory instead
        top = file.parent
        # but exclude everything except the file itself
        excluded.extend([path.resolve() for path in top.iterdir()
                         if not file.samefile(path)])

    # walk the directory
    for (dirpath, dirnames, filenames) in os.walk(top):
        # we modify dirnames and filenames in place to limit walk
        for ex in excluded:
            # resolve dir and file names
            dirpaths = [Path(top, dirpath, name) for name in dirnames]
            filepaths = [Path(top, dirpath, name) for name in filenames]

            # if they are excluded, remove them
            if ex in dirpaths: dirnames.remove(ex.name)
            if ex in filepaths: filenames.remove(ex.name)

        # for not excluded names
        for name in dirnames + filenames:
            # if a name does not conform, we yield the corresponding path
            # checking against names is better, because if we have an invalid
            # subdir name we only yield it once and not also all paths under it
            if not all([char in allowed_chars for char in name]):
                offending_path = Path(top, dirpath, name)
                yield offending_path


def main():
    args = parse_args()

    top = args.path
    excluded = [] if args.excluded is None else args.excluded
    allowed_chars = POSIX_PORTABLE_FILENAME_CHARACTERS if args.symbols is None else args.symbols

    offended = False
    try:
        for offending_path in offending_paths(top, excluded, allowed_chars):
            print(offending_path, file=sys.stderr)
            offended = True
    except (KeyboardInterrupt, SystemExit):
        offended = True
        print()

    sys.exit(1 if offended else 0)


if __name__ == '__main__':
    main()
