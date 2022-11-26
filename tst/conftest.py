import pytest
from pathlib import Path
from yaml import safe_load as load, safe_dump as dump
from copy import deepcopy


# example YAML for FileTreeBuilder
"""
name/:
 Name:
 name3/:
   name:
   name:
name2:
"""


class FileTreeBuilder:
    def __init__(self, tmp_path_factory):
        self.tmp_path_factory = tmp_path_factory

    def from_yaml(self, yaml, root: Path | None = None):
        tree_root = self.tmp_path_factory.mktemp("root") if root is None else root
        path = Path(yaml).resolve()

        with path.open() as p:
            file_tree = load(p.read())

        self.build_tree(file_tree, tree_root)
        return tree_root

    def build_tree(self, tree: dict, root: Path):
        for node, children in tree.items():
            node_path = root / node
            if node[-1] == '/':
                # quit on cycles
                node_path.mkdir(exist_ok=False)
                new_root = root / node_path
                if children is not None:
                    self.build_tree(children, new_root)
            else:
                # quit on cycles
                node_path.touch(exist_ok=False)


@pytest.fixture(scope="session")
def tree_builder(tmp_path_factory):
    return FileTreeBuilder(tmp_path_factory)

@pytest.fixture
def file_tree_with_gitignore(yaml_path, gitignore_path):
    ...
