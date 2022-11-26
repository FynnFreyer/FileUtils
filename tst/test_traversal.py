from util.traversal import traverse_file_tree, translate_glob_patterns, compile_glob_patterns


class TestFileTreeTraversal:
    """
    # file and dir here and in sub dirs
    anywhere_ignored_file
    anywhere_ignored_dir/
    """

    def test_gitignore_excludes_basic_pattern_in_topdir(self, file_tree_with_gitignore):
        results = traverse_file_tree(file_tree_with_gitignore, include_gitignore=True)

        assert file_tree_with_gitignore / 'anywhere_ignored_file' not in results
        assert file_tree_with_gitignore / 'anywhere_ignored_dir' not in results

    def test_gitignore_excludes_basic_pattern_in_subdir(self, file_tree_with_gitignore):
        """
        # file and dir here and in sub dirs
        anywhere_ignored_file
        anywhere_ignored_dir/
        """
        results = traverse_file_tree(file_tree_with_gitignore, include_gitignore=True)

        assert file_tree_with_gitignore / 'not_ignored_dir' / 'anywhere_ignored_file' not in results
        assert file_tree_with_gitignore / 'not_ignored_dir' / 'anywhere_ignored_dir' not in results

    def test_gitignore_excludes_top_level_pattern_in_topdir(self, file_tree_with_gitignore):
        results = traverse_file_tree(file_tree_with_gitignore, include_gitignore=True)

        assert file_tree_with_gitignore / 'toplevel_ignored_file' not in results
        assert file_tree_with_gitignore / 'toplevel_ignored_dir' not in results

    def test_gitignore_keeps_top_level_pattern_in_subdir(self, file_tree_with_gitignore):
        results = traverse_file_tree(file_tree_with_gitignore, include_gitignore=True)

        assert file_tree_with_gitignore / 'toplevel_ignored_file' not in results
        assert file_tree_with_gitignore / 'toplevel_ignored_dir' not in results

        assert file_tree_with_gitignore / 'not_ignored_dir' / 'toplevel_ignored_file' in results
        assert file_tree_with_gitignore / 'not_ignored_dir' / 'toplevel_ignored_dir' in results

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
        assert pattern.match('/path/to/foo')

    def test_double_asterisk_matches_sub_dir(self):
        pattern = compile_glob_patterns(['/path/to/**/foo'])[0]
        # not just '/path/to//foo'
        assert pattern.match('/path/to/another/foo')

    def test_single_asterisk_respects_separators(self):
        pattern = compile_glob_patterns(['/path/to/*/foo'])[0]
        assert pattern.match('/path/to/another/foo')
        assert not pattern.match('/path/to/yet/another/foo')

    def test_patterns_dont_extend_past_definition(self):
        pattern = compile_glob_patterns(['/path/to/foo'])[0]
        assert pattern.match('/path/to/foo')
        assert not pattern.match('/path/to/foobar')
