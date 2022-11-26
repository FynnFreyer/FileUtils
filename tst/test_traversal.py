import pytest
import os

from util.traversal import traverse_file_tree

from pathlib import Path
from subprocess import run
from shutil import copyfile

def test_tree_builder(tree_builder):
    root = tree_builder.from_yaml('assets/test_traversal.yaml')
    proc = run(['tree', '-a', str(root)], capture_output=True, check=True)
    out = proc.stdout.decode()
    assert '12 directories, 12 files' in out.splitlines()[-1]


class TestTraversal:

    def test_file_tree_traversal_gitignore_matches_subdirs(self, tree_builder):
        root = tree_builder.from_yaml('assets/test_traversal.yaml')
        copyfile(Path('assets/test_traversal.gitignore'), root / '.gitignore')

        results = traverse_file_tree(root, include_gitignore=True)

        assert root / 'some_file' in results
        assert root / 'some_dir' in results

        assert root / 'another_file' in results
        assert root / 'another_dir' in results


        assert not root / 'sub_dir' / 'another_file' in results
        assert not root / 'sub_dir' / 'another_dir' in results

    def test_file_tree_traversal_regard_pattern_excludes_unregarded(self, tree_builder):
        root = tree_builder.from_yaml('assets/test_traversal_regard_pattern.yaml')
        assert False

    def test_file_tree_traversal_regard_pattern_includes_regarded(self, tree_builder):
        root = tree_builder.from_yaml('assets/test_traversal_regard_pattern.yaml')
        assert False

    def test_file_tree_traversal_ignore_pattern_excludes_ignored(self, tree_builder):
        root = tree_builder.from_yaml('assets/test_traversal_regard_pattern.yaml')
        assert False

    def test_file_tree_traversal_ignore_pattern_includes_unignored(self, tree_builder):
        root = tree_builder.from_yaml('assets/test_traversal_regard_pattern.yaml')
        assert False
