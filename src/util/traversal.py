import os
import re

from pathlib import Path
from functools import reduce

from fnmatch import translate


def gitignore_to_glob_pattern(root: str, pattern: str) -> str:
    """
    Takes the absolute root of a git repo, and gitignore patterns, and translates them into absolute glob patterns.
    """
    starting_slash = pattern.startswith('/')
    trailing_slash = pattern.endswith('/')

    parts = pattern.split('/')
    non_empty_parts = [part for part in parts if part != '']

    middle_slash = len(non_empty_parts) >= 2

    relative_to_root = starting_slash or middle_slash
    only_dirs = trailing_slash

    # make sure root has trailing slash
    root = root + os.sep  if not root.endswith(os.sep) else root

    # make sure pattern has no starting slash
    pattern = pattern.lstrip('/') if pattern.startswith('/') else pattern
    # replace / in pattern with os.sep
    pattern = pattern.replace('/', os.sep)

    if relative_to_root:
        return root + pattern
    else:
        return root + '**' + pattern

def translate_glob_patterns(patterns: list[str] | None) -> list[str]:
    """
    Take glob-style patterns and translate them into regexes.
    For correct handling of directory patterns (trailing slash),
    regexes must be used on path strings with slash appended in case
    of directories, this must be done externally by the caller.

    :param patterns: An iterable of glob-style patterns to convert to regex patterns.
    :return: An iterator of strings, corresponding to regexes matching the same content the passed glob style patterns would.
    """

    patterns = patterns if patterns is not None else []
    translated_patterns = []

    for pattern in patterns:
        # patterns get translated part by part, parts being delineated by occurences of '**'
        translated_parts = []
        parts = pattern.split('**')
        for i, part in enumerate(parts):
            # fnmatch.translate transforms the patterns in a way, that make it not easy to work with it,
            # so we do some housekeeping beforehand, this will make more sense if taken in context with the rest
            #
            # consider r'/path/to/**/foo' -> r'(s:/path/to/)(s:.*)(s:/foo)', what about '/path/to/foo'?
            # it would not be matched, because part 1 consumes the leading /, that part 3 also expects
            #
            # we could lstrip from part 1 or rstrip from part 3, but ending on / limits to directories,
            # so we take the leading / from the next pattern instead of the trailing from last
            #
            # TLDR; we lstrip('/') on parts EXCEPT the first

            first_iteration = i == 0
            translated_part = part.lstrip('/') if not first_iteration else part

            # TODO
            #  if fnmatch.translate accounts for os.sep, we want to strip os.sep, not '/'
            #  if not we want to account for it, by doing translated_part.replace('/', os.sep)

            # we translate the pattern with the fnmatch function
            translated_part = translate(translated_part)

            # pattern was split on '**', so '.*' patterns must have been produced by '*'
            # we don't want these to match os.sep, so we replace appropriately:
            #     the pattern that matches everything '.*' is replaced by
            #     the pattern that matches everything but os.sep rf'[^{os.sep}]*'
            translated_part = translated_part.replace(r'.*', rf'[^{os.sep}]*')

            # fnmatch appends r'\Z' (matches end of string) to the end, so we strip that off the parts
            translated_part = translated_part.rstrip(r'\Z')

            # part should have been appropriately translated now
            translated_parts.append(translated_part)

        # now we want to combine this into the full pattern again,
        # '**' should match everything, also past directory borders, so we join with r'.*'
        # fnmatch wraps patterns in r'(s:<pattern>)', to avoid adding matching groups (?), we just copy that behaviour
        translated_pattern = r'(?s:.*)'.join(translated_parts)

        # since we want to exclude longer matches, but have a trailing seperator be optional for matching directories,
        # we append rf'{os.sep}?' to the pattern, to optionally match a single seperator
        if not translated_pattern.endswith(os.sep):
            # TODO
            #  doing so should actually be unnecessary, because str(dir_path) does not come with a trailing slash,
            #  but how do we ensure the opposite, that a trailing slash only matches dirs,
            #  instead of just excluding everything?
            translated_pattern += rf'{os.sep}?'

        # now we append r'\Z' to the pattern to avoid matches with longer strings
        translated_pattern += r'\Z'

        translated_patterns.append(translated_pattern)

    return translated_patterns


def compile_glob_patterns(patterns: list[str] | None, regex_flags: list[re.RegexFlag] = None) -> list[re.Pattern]:
    """
    Take a list of glob-style patterns and compile them into regexes, accounting for passed flags.

    :param patterns: list of glob-style patterns to convert to regexes
    :param regex_flags: list of regex flags, will be reduced to a single flag and compiled into regexes
    :return: list of compiled regexes, corresponding to the passed glob style patterns
    """
    # reduction might as well be done in argparse, or on the caller side, this might be preferable
    flags = reduce(lambda x, y: x | y, regex_flags) if regex_flags is not None else 0

    # used to be done with
    # [re.compile(fnmatch.translate(pattern), flags=flag) for pattern in patterns]
    # but this does not properly treat '*' and '**' with regard to directory separators,
    # so now there is a dedicated function

    return [re.compile(translated_pattern, flags=flags) for translated_pattern in translate_glob_patterns(patterns)]


def traverse_file_tree(root: str | bytes | os.PathLike | Path,
                       regard_patterns: list[str] = None,
                       regard_patterns_concern_dirs: bool = False,
                       ignore_patterns: list[str] = None,
                       include_gitignore: bool = False,
                       regex_flags: list[re.RegexFlag] = None) -> set[Path]:
    """
    Traverse a file tree according to specified parameters.
    Returns fully resolved paths.
    Beware, gitignore inclusions has strict limitations with regard to supported patterns.
    So far no negation is possible.

    :param root: directory under which to start
    :param regard_patterns: list of glob style patterns of files to include in the results, if set others are ignored
    :param regard_patterns_concern_dirs: whether regard_patterns concern directories as well
    :param ignore_patterns: list of glob style patterns of files or directories to exclude from the results
    :param include_gitignore: whether to include .gitignore files in the ignore_patterns
    :param regex_flags: list of regex flags, will be reduced to a single flag and compiled into regexes
    :return: the set of all paths under root in accordance with the passed rules
    """

    # resolve the starting point
    root = Path(root).resolve()

    # guard against non-directory starting points
    if not root.is_dir():
        raise NotADirectoryError(f'{root} is not a directory')

    # initialize the result set
    paths = set()

    # regard and ignore patterns are assumed to be glob/fnmatch style strings
    # we translate them to regexes and compile them with the appropriate regex flags
    regard_patterns: list[re.Pattern] = compile_glob_patterns(regard_patterns, regex_flags)
    ignore_patterns: list[re.Pattern] = compile_glob_patterns(ignore_patterns, regex_flags)

    # iterate over the file tree
    for (dirpath, dirnames, filenames) in os.walk(root):
        # lists must be modified in place

        # if include_gitignore is set and a .gitignore file is found, include
        # its contents in our ignore patterns, we ensure that the new patterns
        # only match under this dir by prepending dirpath to them
        # see also https://git-scm.com/docs/gitignore
        if include_gitignore and '.gitignore' in filenames:
            with Path(dirpath, '.gitignore').open() as ignore_file:
                new_patterns = []
                for line in ignore_file:
                    # contrary to normal gitignore interpretation rules (as far as I understand them),
                    # we will ONLY MATCH UNDER the current dir, and not up to the repository root
                    # also NO UNIGNORING PATHS with '!' is possible

                    # ignore empty lines and comments
                    line = line.strip()
                    if line == '' or line.startswith('#'):
                        continue

                    new_pattern = gitignore_to_glob_pattern(dirpath, line)
                    new_patterns.append(new_pattern)

            ignore_patterns.extend(compile_glob_patterns(new_patterns, regex_flags))

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
                # TODO this logic should probably be extracted to a separate function
                #   removing stuff from a list in this fashion happens four times in here
                # do the same thing for directories
                dirs_to_remove = []
                for dirname in dirnames:
                    # match against the unresolved dir name  and mark it for removal
                    # dirs need trailing slash
                    if not any([pattern.search(dirname + os.sep) for pattern in regard_patterns]):
                        dirs_to_remove.append(dirname)

                # remove those dirs
                for dirname in dirs_to_remove: dirnames.remove(dirname)

        # exclude files and dirs that match any ignore pattern
        for ignore_pattern in ignore_patterns:
            # match against the unresolved dir name  and mark it for removal
            # dirs need trailing slash
            dirs_to_remove = [dirname for dirname in dirnames
                              if ignore_pattern.search(os.path.join(dirpath, dirname) + os.sep)]

            files_to_remove = [filename for filename in filenames
                               if ignore_pattern.search(os.path.join(dirpath, filename))]

            for dirname in dirs_to_remove: dirnames.remove(dirname)
            for filename in files_to_remove: filenames.remove(filename)

        # include the paths that have not been ignored
        paths.update([Path(dirpath, fn).resolve() for fn in dirnames + filenames])

    return paths
