from util.traversal import traverse_file_tree


class TestTraversal:

    def test_file_tree_traversal_gitignore_matches_subdirs(self, file_tree_with_gitignore):
        root = file_tree_with_gitignore
        results = traverse_file_tree(root, include_gitignore=True)

        assert root / 'some_file' in results
        assert root / 'some_dir' in results

        assert root / 'another_file' in results
        assert root / 'another_dir' in results

        assert not root / 'sub_dir' / 'another_file' in results
        assert not root / 'sub_dir' / 'another_dir' in results

    def test_file_tree_traversal_regard_pattern_excludes_unregarded(self, file_tree):
        assert False

    def test_file_tree_traversal_regard_pattern_includes_regarded(self, file_tree):
        assert False

    def test_file_tree_traversal_ignore_pattern_excludes_ignored(self, file_tree):
        assert False

    def test_file_tree_traversal_ignore_pattern_includes_unignored(self, file_tree):
        assert False

