import os
import re
import fnmatch

from pathlib import Path
from functools import reduce


def compile_fnmatch_patterns(patterns: list[str] = None, regex_flags: list[re.RegexFlag] = None) -> list[re.Pattern]:
    f"""
    Take a list of glob-style patterns and compile them into regexes, accounting for passed flags.

    :param patterns: list of glob-style patterns to convert to regexes
    :param regex_flags: list of regex flags, will be reduced to a single flag and compiled into regexes
    :return: list of compiled regexes, corresponding to the passed glob style patterns
    """

    # make sure regex flags and patterns are properly initialized, even if not passed explicitly
    patterns = patterns if patterns is not None else []

    # reduction might as well be done in argparse, or on the caller side, this would probably be preferable
    flags = reduce(lambda x, y: x | y, regex_flags) if regex_flags is not None else 0

    return [re.compile(fnmatch.translate(pattern), flags=flags) for pattern in patterns]


def traverse_file_tree(root: Path = Path().home(),
                       regard_patterns: list[str] = None,
                       regard_patterns_concern_dirs: bool = False,
                       ignore_patterns: list[str] = None,
                       include_gitignore: bool = False,
                       regex_flags: list[re.RegexFlag] = None) -> set[Path]:
    f"""
    Traverse a file tree according to specified parameters.
    Returns fully resolved paths.

    :param root: directory under which to start
    :param regard_patterns: list of glob style patterns of files to include in the results, if set others are ignored
    :param regard_patterns_concern_dirs: whether regard_patterns concern directories as well
    :param ignore_patterns: list of glob style patterns of files or directories to exclude from the results
    :param include_gitignore: whether to include .gitignore files in the ignore_patterns
    :param regex_flags: list of regex flags, will be reduced to a single flag and compiled into regexes
    :return: the set of all paths under root in accordance with the passed rules
    """

    # resolve the starting point
    start = Path(root).resolve()

    # guard against non-directory starting points
    if not start.is_dir():
        raise NotADirectoryError(f'{start} is not a directory')

    # initialize the result set
    paths = set()

    # regard and ignore patterns are assumed to be glob/fnmatch style strings
    # we translate them to regexes and compile them with the appropriate regex flags
    regard_patterns: list[re.Pattern] = compile_fnmatch_patterns(regard_patterns, regex_flags)
    ignore_patterns: list[re.Pattern] = compile_fnmatch_patterns(ignore_patterns, regex_flags)

    # iterate over the file tree
    for (dirpath, dirnames, filenames) in os.walk(start):
        # lists must be modified in place

        # if include_gitignore is set and a .gitignore file is found, include
        # its contents in the ignore patterns, we ensure that the new patterns
        # only match under this dir by prepending dirpath to them
        # see also https://git-scm.com/docs/gitignore
        if include_gitignore and '.gitignore' in filenames:
            with Path(dirpath, '.gitignore').open() as ignore_file:
                lines = ignore_file.readlines()
                new_patterns = []
                for line in lines:
                    # ignore empty lines and comments
                    line = line.strip()
                    if line == '' or line.startswith('#'):
                        continue

                    # contrary to normal gitignore interpretation rules, we will only match UNDER the current dir
                    new_patterns.append(os.path.join(dirpath, line))

            ignore_patterns.extend(compile_fnmatch_patterns(new_patterns, regex_flags))

        # exclude files don't match any regard pattern, if there are regard patterns
        if regard_patterns:
            # regard patterns don't concern directories
            # get files that do not match any regard pattern
            files_to_remove = []
            for filename in filenames:
                # match against the unresolved file name and mark it for removal
                if not any([pattern.search(filename) for pattern in regard_patterns]):
                    files_to_remove.append(filename)

            # remove those files
            for filename in files_to_remove: filenames.remove(filename)

            # this might be a pretty roundabout way of doing it, but editing lists while you are
            # iterating over them is almost never a good idea, and seldom necessary, so I don't

            if regard_patterns_concern_dirs:
                # TODO this logic should be extracted to a function
                # do the same thing for directories
                dirs_to_remove = []
                for dirname in dirnames:
                    # match against the unresolved dir name  and mark it for removal
                    if not any([pattern.search(dirname) for pattern in regard_patterns]):
                        dirs_to_remove.append(dirname)

                # remove those dirs
                for dirname in dirs_to_remove: dirnames.remove(dirname)

        # exclude files and dirs that match any ignore pattern
        for ignore_pattern in ignore_patterns:
            dirs_to_remove = [dirname for dirname in dirnames
                              if ignore_pattern.search(os.path.join(dirpath, dirname))]

            files_to_remove = [filename for filename in filenames
                               if ignore_pattern.search(os.path.join(dirpath, filename))]

            for dirname in dirs_to_remove: dirnames.remove(dirname)
            for filename in files_to_remove: filenames.remove(filename)

        # include the paths that have not been ignored
        paths.update([Path(dirpath, fn).resolve() for fn in dirnames + filenames])

    return paths
