import functools
import os
import re
import hashlib

from pathlib import Path
from util.traversal import traverse_file_tree
from multiprocessing import Pool
from collections import defaultdict


def get_file_hash(file: str | bytes | os.PathLike | Path, name: str = 'sha256') -> str:
    """
    Compute the hash of a file.

    :param file: path to the file
    :param name: name of the hash algorithm
    :return: string corresponding to the hex digest of the file hash
    """

    # make sure path is properly resolved Path object
    path = Path(file).resolve()

    # ensure the requested algorithm is available
    if name not in hashlib.algorithms_available:
        raise ValueError(f'Hash algorithm "{name}" is not available on this system.')
    # guard against non files
    elif not path.is_file():
        raise ValueError(f'Can only hash files. "{file}" is not a file.')
    # hashing algorithm is available and a file was passed
    else:
        hash_object = hashlib.new(name)
        # compute the hash
        with path.open('rb') as f:
            # file_digest is only available in >= 3.11
            # file_hash = hashlib.file_digest(f, name).hexdigest()

            # read the file in 64 kib chunks and update the hash
            CHUNK_SIZE = 65536
            while chunk := f.read(CHUNK_SIZE):
                hash_object.update(chunk)

            file_hash = hash_object.hexdigest()

        # sanity check the file hash and abort on mismatches -> better safe than sorry
        # should be unnecessary here, only interesting when using xonsh shenanigans
        assert len(file_hash) == 2 * hash_object.digest_size, 'Computed file hash failed sanity check, aborting.'

    return file_hash


def get_hash_tuple(file: str | bytes | os.PathLike | Path,
                   name: str = 'sha256') -> tuple[str | bytes | os.PathLike | Path, str]:
    """
    Uses get_file_hash to compute the hash of a file,
    but returns the file as well, making it suitable for e.g. using in parallel.

    :param file: path to the file
    :param name: name of the hash algorithm
    :return: tuple with first element being the hashed file and second the file hash
    """
    return file, get_file_hash(file, name=name)


def get_dir_hash_map(root: Path,
                     regard_patterns: list[str] = None,
                     regard_patterns_concern_dirs: bool = False,
                     ignore_patterns: list[str] = None,
                     include_gitignore: bool = False,
                     regex_flags: list[re.RegexFlag] = None,
                     name: str = 'sha256',
                     processes: int = 1) -> dict[str, list[Path]]:
    """
    Compute a map of file hashes to files that produced those hashes under a directory.
    Parameters largely correspond to the ones for traverse_file_tree and get_file_hash.

    :param root: directory under which to search
    :param regard_patterns: list of glob style patterns of files to include in the results, if set others are ignored
    :param regard_patterns_concern_dirs: whether regard_patterns concern directories as well
    :param ignore_patterns: list of glob style patterns of files or directories to exclude from the results
    :param include_gitignore: whether to include .gitignore files in the ignore_patterns
    :param regex_flags: flags for the pattern lists, like re.IGNORECASE or re.DOTALL
    :param processes: how many processes to fork for file hashing
    :param name: name of the hash algorithm
    :return: list of lists, where each sublist represents files that are duplicates of one another
    """

    # find all file paths that match the criteria
    files = [path for path in traverse_file_tree(root=root,
                                                 regard_patterns=regard_patterns,
                                                 regard_patterns_concern_dirs=regard_patterns_concern_dirs,
                                                 ignore_patterns=ignore_patterns,
                                                 include_gitignore=include_gitignore,
                                                 regex_flags=regex_flags)
             if path.is_file()]

    # compute the hashes in parallel
    with Pool(processes=processes) as pool:
        # partially apply the hash name
        work = functools.partial(get_hash_tuple, name=name)
        file_and_hash_pairs = pool.map(work, files)

    # register the files to their hashes
    register: dict[str, list[Path]] = defaultdict(list)
    for file, file_hash in file_and_hash_pairs:
        register[file_hash].append(file)

    return register
