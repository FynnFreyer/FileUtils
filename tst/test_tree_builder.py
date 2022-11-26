from subprocess import run


def test_tree_builder(tree_builder):
    root = tree_builder.from_yaml('assets/test_tree_builder.yaml')
    proc = run(['tree', '-a', str(root)], capture_output=True, check=True)
    out = proc.stdout.decode()
    assert '13 directories, 12 files' in out.splitlines()[-1]

