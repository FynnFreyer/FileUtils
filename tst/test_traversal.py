from util.traversal import traverse_file_tree, translate_glob_patterns, compile_glob_patterns


class TestFileTreeTraversal:

    def test_gitignore_matches_subdirs(self, file_tree_with_gitignore):
        root = file_tree_with_gitignore
        results = traverse_file_tree(root, include_gitignore=True)

        assert root / 'some_file' in results
        assert root / 'some_dir' in results

        assert root / 'another_file' in results
        assert root / 'another_dir' in results

        assert not root / 'sub_dir' / 'another_file' in results
        assert not root / 'sub_dir' / 'another_dir' in results

    def test_regard_pattern_excludes_unregarded(self, file_tree):
        assert False

    def test_regard_pattern_includes_regarded(self, file_tree):
        assert False

    def test_ignore_pattern_excludes_ignored(self, file_tree):
        assert False

    def test_ignore_pattern_includes_unignored(self, file_tree):
        assert False


class TestGlobPatterns:

    def test_double_asterisk_matches_top_level_dir(self):
        pattern = compile_glob_patterns(['/path/to/**/foo'])[0]
        # not just '/path/to//foo'
        assert pattern.match('/path/to/foo')
