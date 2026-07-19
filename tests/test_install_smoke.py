"""Tier-A install-smoke gate for the shipped skill package.

This exercises the install property as a real, deterministic, model-free gate.
The built artifact is extracted into a throwaway temporary directory (NEVER a
real user skill home), and the runtime that shipped inside it is driven from the
extracted location with the repository root off the import path.

The gate proves four end-to-end properties of a fresh install:

* SHAPE     -- the artifact extracts to a single top-level ``stow/`` root.
* FIDELITY  -- the installed bytes equal the source bytes (the build's only text
               transform is LF normalisation) for SKILL.md, a corpus module, and
               both runtime modules.
* CLOSURE   -- each shipped ``runtime/*.py`` runs in a subprocess whose
               ``sys.path`` is the extracted tree only (the repo root is asserted
               absent), driving its real CLI to a sane exit.
* DECISION  -- the extracted validator accepts a structured file that shipped in
               the artifact and rejects a malformed one, from the installed path.

No source-project name, path, URL, or hash appears in this file.
"""

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
TOOLS = os.path.join(REPO, "tools")
BUILD_PATH = os.path.join(TOOLS, "build_skill.py")
SRC = os.path.join(REPO, "skills", "stow")   # the packaged source subtree

TOP = "stow"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build_skill = _load("build_skill", BUILD_PATH)


def _read(path):
    with open(path, "rb") as handle:
        return handle.read()


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


# --------------------------------------------------------------------------- #
# Install fixture: build -> extract into a throwaway temp dir (built once)
# --------------------------------------------------------------------------- #

class Installed:
    def __init__(self, result, extract_root, names, base):
        self.result = result
        self.extract_root = extract_root
        self.names = names
        self.base = base

    def path(self, *parts):
        return os.path.join(self.extract_root, *parts)

    def inputs(self, *parts):
        return os.path.join(self.base, "inputs", *parts)


@pytest.fixture(scope="module")
def installed():
    # tempfile only -- the extraction target is a disposable directory under the
    # system temp root, never a real ``~/.claude`` skill home.
    base = tempfile.mkdtemp(prefix="stow-install-smoke-")
    try:
        out_dir = os.path.join(base, "dist")
        os.makedirs(out_dir)
        result = build_skill.build(root=REPO, out_dir=out_dir)

        extract_root = os.path.join(base, "skillhome")
        os.makedirs(extract_root)
        with zipfile.ZipFile(result["artifact_path"]) as archive:
            names = archive.namelist()
            archive.extractall(extract_root)

        yield Installed(result, extract_root, names, base)
    finally:
        shutil.rmtree(base, ignore_errors=True)


# --------------------------------------------------------------------------- #
# Safety: the install target is a throwaway temp dir, not a real home
# --------------------------------------------------------------------------- #

def test_install_target_is_a_throwaway_temp_dir(installed):
    root = os.path.abspath(installed.extract_root)
    tmp_root = os.path.abspath(tempfile.gettempdir())
    assert root.startswith(tmp_root + os.sep), root
    # Never anywhere near a real skill home.
    assert ".claude" not in root.replace("\\", "/").lower()


# --------------------------------------------------------------------------- #
# SHAPE: one top-level stow/ root
# --------------------------------------------------------------------------- #

def test_single_top_level_root_is_stow(installed):
    top_level = {name.split("/", 1)[0] for name in installed.names}
    assert top_level == {TOP}
    # And on disk the extraction produced exactly one entry: stow/.
    assert os.listdir(installed.extract_root) == [TOP]


# --------------------------------------------------------------------------- #
# FIDELITY: installed bytes == source bytes for a representative sample
# --------------------------------------------------------------------------- #

def _sample_corpus_arcname(names):
    for name in sorted(names):
        if name.startswith("stow/corpus/") and name.endswith(".md"):
            return name
    raise AssertionError("no corpus module found in the artifact")


def test_installed_bytes_equal_source_bytes(installed):
    sample_arcnames = [
        "stow/SKILL.md",
        _sample_corpus_arcname(installed.names),
        "stow/runtime/validate.py",
        "stow/runtime/lint_prose.py",
    ]
    for arcname in sample_arcnames:
        assert arcname in installed.names, arcname
        rel = arcname.split("/", 1)[1]              # strip the 'stow/' top level
        installed_bytes = _read(installed.path(*arcname.split("/")))
        source_bytes = _read(os.path.join(SRC, *rel.split("/")))
        # The build's ONLY text transform is LF normalisation; comparing the
        # source under that same normalisation is the exact installed==source
        # invariant (and reduces to a raw byte match on an LF checkout).
        assert installed_bytes == build_skill.normalize_lf(source_bytes), arcname


# --------------------------------------------------------------------------- #
# CLOSURE: each runtime module runs with sys.path == the extract only
# --------------------------------------------------------------------------- #

# Runs a shipped module by absolute path in a child interpreter whose sys.path
# is reduced to the extracted tree (plus stdlib / site-packages for installed
# deps such as ruamel.yaml). The repo root and cwd sentinels are removed and
# their absence is asserted BEFORE the module executes, so a green run proves
# import-closure. The module's real CLI is then driven via ``runpy`` so its
# ``__main__`` block runs and its exit code propagates to this process.
_RUN_CLOSED_BOOTSTRAP = r"""
import os, runpy, sys
repo = os.path.abspath(sys.argv[1])
extract = os.path.abspath(sys.argv[2])
target = os.path.abspath(sys.argv[3])
argv_rest = sys.argv[4:]

forbidden = {repo, os.path.join(repo, "tests"), os.path.join(repo, "tools")}
kept = []
for entry in sys.path:
    if entry in ("", "."):
        continue
    if os.path.abspath(entry) in forbidden:
        continue
    kept.append(entry)
sys.path = [os.path.dirname(target)] + kept

on_path = [os.path.abspath(p) for p in sys.path]
assert repo not in on_path, "repo root leaked onto sys.path"
for p in on_path:
    inside_repo = (p == repo) or p.startswith(repo + os.sep)
    inside_extract = (p == extract) or p.startswith(extract + os.sep)
    assert (not inside_repo) or inside_extract, ("repo path on sys.path: %s" % p)

sys.argv = [target] + argv_rest
runpy.run_path(target, run_name="__main__")
"""


def _run_closed(installed, target_parts, argv):
    target = installed.path(*target_parts)
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)   # do not smuggle the repo back onto the path
    return subprocess.run(
        [sys.executable, "-c", _RUN_CLOSED_BOOTSTRAP,
         REPO, installed.extract_root, target] + list(argv),
        capture_output=True, text=True,
        cwd=installed.extract_root, env=env)


def test_every_runtime_module_runs_import_closed(installed):
    runtime_dir = installed.path("stow", "runtime")
    modules = sorted(f for f in os.listdir(runtime_dir) if f.endswith(".py"))
    assert modules, "no runtime modules shipped in the artifact"

    # Each shipped runtime module is driven through its real CLI on inputs that
    # themselves shipped in the artifact. A module with no drive entry is a new,
    # un-smoke-tested runtime surface and fails here by KeyError.
    drives = {
        "validate.py": (
            ["--format", "yaml", installed.path("stow", "rules", "registry.yaml")],
            0, "VALID"),
        "lint_prose.py": (
            [installed.path("stow", "SKILL.md")],
            0, "lint_prose"),
        "profiles.py": (
            ["resolve", "controlled-technical"],
            0, "controlled-technical-guided"),
    }

    for module in modules:
        argv, expect_code, expect_text = drives[module]
        proc = _run_closed(installed, ("stow", "runtime", module), argv)
        assert proc.returncode == expect_code, \
            "%s rc=%s\nstdout=%s\nstderr=%s" % (
                module, proc.returncode, proc.stdout, proc.stderr)
        assert expect_text in (proc.stdout + proc.stderr), \
            "%s: %r / %r" % (module, proc.stdout, proc.stderr)


# --------------------------------------------------------------------------- #
# DECISION: the installed validator accepts a shipped fixture and rejects junk
# --------------------------------------------------------------------------- #

def test_installed_validator_accepts_a_fixture_from_the_extract(installed):
    # Input and validator both come from the extract: registry.yaml shipped in
    # the artifact and is validated by the runtime that shipped alongside it.
    shipped = installed.path("stow", "rules", "registry.yaml")
    assert os.path.isfile(shipped)
    proc = _run_closed(
        installed, ("stow", "runtime", "validate.py"),
        ["--format", "yaml", shipped])
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "VALID" in proc.stdout


def test_installed_validator_rejects_a_malformed_file(installed):
    # A self-authored malformed input (duplicate object key) kept OUTSIDE the
    # extract tree so the installed surface stays pristine.
    bad = installed.inputs("dup_key.json")
    _write(bad, '{"k": 1, "k": 2}\n')
    proc = _run_closed(
        installed, ("stow", "runtime", "validate.py"),
        ["--format", "json", bad])
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "INVALID" in proc.stderr
