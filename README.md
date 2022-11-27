[![Tests on Linux | MacOS | Windows](https://github.com/FynnFreyer/FileUtils/actions/workflows/test.yml/badge.svg)](https://github.com/FynnFreyer/FileUtils/actions/workflows/test.yml)

# FileUtils

Some utilities to manage files.

Works with **Python >= 3.10**

## Working:

- Traverse file trees, excluding stuff mentioned in your gitignore, or specified via glob-style patters.
- Find files and directories with improper (not POSIX-conform) naming
- Find duplicate files by hash.

## Todo

- dry run
- handle negation in gitignore
- proper tests
  - cross platform tests
  - traversal
    - more gitignore szenarios
    - ignore/regard patterns
    - regard_concerns_dirs
  - duplicates
  - naming
  - hashing
- more documentation
  - inline is good **so far**, but readme, and maybe integrate with readthedocs?
- integrate naming with traverse.py
- merge directories according to strategy
- rename files according to strategy
- main script with subcommands
