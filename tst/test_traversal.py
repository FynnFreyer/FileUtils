from util.traversal import traverse_file_tree, translate_glob_patterns, compile_glob_patterns


class TestFileTreeTraversal:
    def test_gitignore_excludes_basic_pattern_in_topdir(self, file_tree_with_gitignore):
        results = traverse_file_tree(file_tree_with_gitignore, include_gitignore=True)
        assert file_tree_with_gitignore / 'anywhere_ignored_file' not in results
        assert file_tree_with_gitignore / 'anywhere_ignored_dir' not in results

    def test_gitignore_excludes_basic_pattern_in_subdir(self, file_tree_with_gitignore):
        results = traverse_file_tree(file_tree_with_gitignore, include_gitignore=True)
        assert file_tree_with_gitignore / 'not_ignored_dir' / 'anywhere_ignored_file' not in results
        assert file_tree_with_gitignore / 'not_ignored_dir' / 'anywhere_ignored_dir' not in results

    def test_gitignore_excludes_top_level_pattern_in_topdir(self, file_tree_with_gitignore):
        results = traverse_file_tree(file_tree_with_gitignore, include_gitignore=True)
        assert file_tree_with_gitignore / 'toplevel_ignored_file' not in results
        assert file_tree_with_gitignore / 'toplevel_ignored_dir' not in results

    def test_gitignore_keeps_top_level_pattern_in_subdir(self, file_tree_with_gitignore):
        results = traverse_file_tree(file_tree_with_gitignore, include_gitignore=True)
        assert file_tree_with_gitignore / 'not_ignored_dir' / 'toplevel_ignored_file' in results
        assert file_tree_with_gitignore / 'not_ignored_dir' / 'toplevel_ignored_dir' in results

    def test_gitignore_middle_slash_causes_top_level_pattern(self, file_tree_with_gitignore):
        results = traverse_file_tree(file_tree_with_gitignore, include_gitignore=True)
        assert file_tree_with_gitignore / 'another' / 'toplevel_ignored_file' not in results
        assert file_tree_with_gitignore / 'another' / 'toplevel_ignored_dir' not in results
        # should only exclude the pattern at top level
        assert file_tree_with_gitignore / 'another' / 'another' / 'toplevel_ignored_file' in results
        assert file_tree_with_gitignore / 'another' / 'another' / 'toplevel_ignored_dir' in results

    def test_basic_regard_pattern_includes_regarded_files(self, file_tree):
        results = traverse_file_tree(file_tree, regard_patterns=['not_ignored_file'])
        assert file_tree / 'not_ignored_file' in results

    def test_basic_regard_pattern_excludes_unregarded_files(self, file_tree):
        results = traverse_file_tree(file_tree, regard_patterns=['not_ignored_file'])
        assert file_tree / 'anywhere_ignored_file' not in results

    def test_basic_regard_pattern_includes_unregarded_dirs(self, file_tree):
        results = traverse_file_tree(file_tree, regard_patterns=['not_ignored_file'])
        assert file_tree / 'not_ignored_dir' in results

    def test_basic_regard_pattern_excludes_unregarded_dirs_with_concerns_dirs_option(self, file_tree):
        results = traverse_file_tree(file_tree, regard_patterns=['not_ignored_file'], regard_patterns_concern_dirs=True)
        assert file_tree / 'not_ignored_dir' not in results

    def test_regard_pattern_includes_files_with_glob(self, file_tree):
        results = traverse_file_tree(file_tree, regard_patterns=['not_ignored_*'])
        assert file_tree / 'not_ignored_file' in results

    def test_regard_pattern_includes_dirs_with_glob_and_concerns_dirs(self, file_tree):
        results = traverse_file_tree(file_tree, regard_patterns=['not_ignored_*'], regard_patterns_concern_dirs=True)
        assert file_tree / 'not_ignored_dir' in results

    def test_ignore_pattern_excludes_ignored_in_toplevel(self, file_tree):
        results = traverse_file_tree(file_tree, ignore_patterns=['anywhere_ignored_file'])
        assert file_tree / 'anywhere_ignored_file' not in results

    def test_ignore_pattern_excludes_ignored_in_subdir(self, file_tree):
        results = traverse_file_tree(file_tree, ignore_patterns=['anywhere_ignored_file'])
        assert file_tree / 'not_ignored_dir' / 'anywhere_ignored_file' not in results

    def test_ignore_pattern_includes_unignored_files_and_dirs(self, file_tree):
        results = traverse_file_tree(file_tree, ignore_patterns=['anywhere_ignored_file'])
        assert file_tree / 'not_ignored_file' in results
        assert file_tree / 'not_ignored_dir' in results


class TestGlobPatterns:

    def test_double_asterisk_matches_top_level_dir(self):
        pattern = compile_glob_patterns(['/path/to/**/foo'])[0]
        assert pattern.match('/path/to/foo')

    def test_double_asterisk_matches_sub_dir(self):
        pattern = compile_glob_patterns(['/path/to/**/foo'])[0]
        assert pattern.match('/path/to/another/foo')

    def test_single_asterisk_matches_subdir(self):
        pattern = compile_glob_patterns(['/path/to/*/foo'])[0]
        assert pattern.match('/path/to/another/foo')

    def test_single_asterisk_respects_separators(self):
        pattern = compile_glob_patterns(['/path/to/*/foo'])[0]
        assert not pattern.match('/path/to/yet/another/foo')

    def test_patterns_dont_extend_past_definition(self):
        pattern = compile_glob_patterns(['/path/to/foo'])[0]
        assert pattern.match('/path/to/foo')
        assert not pattern.match('/path/to/foobar')
