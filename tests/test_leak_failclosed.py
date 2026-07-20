"""Fail-closed and tree-scan behavior of the anti-leak gate.

These run in weak mode (no private pattern file needed), so they execute in CI
as well as locally. They pin the guarantee that a whole-tree scan matching zero
files can never masquerade as a clean PASS, and that the explicit --tree walk
scans the filesystem without git.
"""

import importlib.util
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
CHECKER = os.path.join(REPO, "tools", "check_provenance_leak.py")


def _load():
    spec = importlib.util.spec_from_file_location("check_provenance_leak_fc", CHECKER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


mod = _load()


def test_default_tracked_zero_files_fails_closed(monkeypatch, capsys):
    """When git yields no tracked files (not a checkout), the default scan must
    exit nonzero and must NOT print the PASS banner."""
    monkeypatch.setattr(mod, "targets_tracked", lambda: [])
    code = mod.run([])
    captured = capsys.readouterr()
    assert code != 0, "empty tracked scan must fail closed"
    assert "LEAK CHECK PASSED" not in captured.out
    assert "zero files" in captured.err


def test_tree_zero_files_fails_closed(monkeypatch):
    monkeypatch.setattr(mod, "targets_tree", lambda: [])
    assert mod.run(["--tree"]) != 0


def test_tree_scan_finds_files_and_passes_weak():
    """The real filesystem tree is non-empty and clean under the weak gate."""
    code = mod.run(["--tree"])
    assert code == 0, "weak --tree scan of the repo tree should pass"


def test_tree_target_set_is_non_empty():
    targets = mod.targets_tree()
    assert len(targets) > 10
    names = {rel for rel, _content in targets}
    assert "AGENTS.md" in names
    # The git directory is skipped by the tree walk.
    assert not any(rel.startswith(".git/") for rel in names)
