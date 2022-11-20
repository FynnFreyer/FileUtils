import sys
import re

from pathlib import Path
from util.hashing import get_dir_hash_map


def find_duplicate_files(root: Path,
                         regard_patterns: list[str] = None,
                         regard_patterns_concern_dirs: bool = False,
                         ignore_patterns: list[str] = None,
                         include_gitignore: bool = False,
                         regex_flags: list[re.RegexFlag] = None,
                         processes: int = 1,
                         print_results: bool = False) -> dict[str, list[Path]]:
    """
    Find duplicate files under a directory by hash.
    Parameters largely correspond to the ones for traverse_file_tree.

    :param root: directory under which to search
    :param regard_patterns: list of glob style patterns of files to include in the results, if set others are ignored
    :param regard_patterns_concern_dirs: whether regard_patterns concern directories as well
    :param ignore_patterns: list of glob style patterns of files or directories to exclude from the results
    :param include_gitignore: whether to include .gitignore files in the ignore_patterns
    :param regex_flags: flags for the pattern lists, like re.IGNORECASE or re.DOTALL
    :param processes: how many processes to fork for file hashing
    :param print_results: whether to print duplicates as csv, where each line contains files that are duplicates of one another
    :return: list of lists, where each sublist represents files that are duplicates of one another
    """

    # find all duplicate files that match the given criteria
    # file hash is kept, so we can extend the results later
    duplicates = {
        file_hash: file_list
        for file_hash, file_list
        in get_dir_hash_map(root=root,
                            regard_patterns=regard_patterns,
                            regard_patterns_concern_dirs=regard_patterns_concern_dirs,
                            ignore_patterns=ignore_patterns,
                            include_gitignore=include_gitignore,
                            regex_flags=regex_flags,
                            name='sha256',
                            processes=processes).items()
        if len(file_list) > 1
    }

    # output results as csv if requested
    if print_results:
        for file_list in duplicates.values():
            # if " in name it's gotta be doubled, or invalid csv will be produced
            double_quote, escaped_double_quote = '"', '""'
            csv_row = ', '.join(
                [f'"{str(file).replace(double_quote, escaped_double_quote)}"' for file in file_list])

            # issue a warning for all files with potential naming issues to stderr
            naming_issues = [file for file in file_list if '"' in str(file)]
            if naming_issues:
                print('WARNING: double quote found in', *naming_issues, file=sys.stderr)

            # output the hopefully valid csv
            print(csv_row)

    return duplicates


def compute_duplicate_statistics(duplicates: list[list[Path]]) -> ():
    pass


def destructive_shallow_merge_folders(dir_source, dir_target):
    """Merge source into target. Move files, remove duplicates, rename on conflict. Do not recurse! Chokes on dirs"""

    source_path = Path(dir_source).resolve()
    target_path = Path(dir_target).resolve()

    for file in source_path.iterdir():
        target_file = target_path / file.name

        if target_file.exists():
            # compare file hashes with sum
            # only take first two fields, third is path
            source_sum = ''
            target_sum = '$(sum @ (target_path / file.name)).split()[:2]'

            if source_sum == target_sum:
                print('removing duplicate', file, target_file)
                # rm @ (file)
            else:
                i = 0
                while True:
                    candidate = Path(f'{target_file}_{i}')
                    if not candidate.exists():
                        target_file = candidate
                        break
                    i += 1
                print('moving', file, 'to', target_file)
                # mv @ (file) @ (target_file)
