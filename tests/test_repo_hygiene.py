"""Repository and artifact hygiene gates.

Two properties held by discipline until this pass; both are now machine
enforced:

  * the TRACKED tree carries no cache, bytecode, or editor droppings -- a
    filesystem copy of a checkout must never smuggle junk into an archive of
    tracked content;
  * the COMMITTED dist/ artifact set (archive + sidecar + manifest) is exactly
    what a fresh build of the current tree produces. A stale or hand-edited
    committed artifact fails here instead of shipping. On a Linux CI runner
    this same test doubles as the cross-platform reproducibility proof for the
    Windows-built committed bytes.

Self-contained: no source-project name, path, hash, or URL appears here.
"""

import hashlib
import importlib.util
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DIST = os.path.join(REPO, "dist")

JUNK_FRAGMENTS = (
    "__pycache__", ".pyc", ".pyo", ".pytest_cache", ".DS_Store", "Thumbs.db",
    ".swp", ".orig", ".rej", ".bak", ".tmp", "~",
)


def _git(args):
    proc = subprocess.run(["git"] + args, capture_output=True, text=True,
                          cwd=REPO)
    if proc.returncode != 0:
        pytest.skip("git unavailable: %s" % proc.stderr.strip())
    return proc.stdout


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_tracked_tree_is_junk_free():
    """A junk fragment matches as a basename suffix or a directory segment,
    never as an innocent substring of a real name."""
    tracked = _git(["ls-files"]).splitlines()
    assert tracked, "git ls-files returned nothing"
    offenders = []
    for path in tracked:
        segments = path.split("/")
        base = segments[-1]
        for fragment in JUNK_FRAGMENTS:
            if base.endswith(fragment) or fragment in segments[:-1]:
                offenders.append((path, fragment))
    assert not offenders, "junk tracked in git: %s" % offenders


def test_committed_dist_matches_a_fresh_build(tmp_path):
    build_skill = _load("build_skill_for_hygiene",
                        os.path.join(REPO, "tools", "build_skill.py"))
    result = build_skill.build(root=REPO, out_dir=str(tmp_path))

    committed_artifact = os.path.join(DIST, "STOW.skill")
    with open(committed_artifact, "rb") as fh:
        committed_bytes = fh.read()
    with open(result["artifact_path"], "rb") as fh:
        fresh_bytes = fh.read()
    assert committed_bytes == fresh_bytes, (
        "committed dist/STOW.skill differs from a fresh build of this tree "
        "(committed sha256 %s, fresh %s) -- rebuild and commit dist/"
        % (hashlib.sha256(committed_bytes).hexdigest()[:12],
           result["sha256"][:12]))

    for name in ("STOW.skill.sha256", "manifest.json"):
        with open(os.path.join(DIST, name), "rb") as fh:
            committed = fh.read().replace(b"\r\n", b"\n")
        with open(os.path.join(str(tmp_path), name), "rb") as fh:
            fresh = fh.read().replace(b"\r\n", b"\n")
        assert committed == fresh, "committed dist/%s is stale" % name
