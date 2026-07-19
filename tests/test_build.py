"""P7 tests for the deterministic skill package builder (tools/build_skill.py).

These tests prove the four properties the build promises:

* REPRODUCIBILITY -- two builds of the same content are byte-identical.
* SHAPE -- one top-level ``stow/`` directory, the runtime allowlist, and none
  of the repo-only surfaces (tools, tests, provenance, pattern data, the leak
  checker) leak into the artifact.
* SELF-CONTAINMENT -- each shipped runtime module imports with the repo root
  OFF ``sys.path`` (only the extracted tree plus installed packages), so the
  artifact runs standalone.
* RE-VALIDATION -- the extracted tree re-passes the structured-output
  validator, the context-budget ceiling, and BOTH anti-leak gates.

No source-project name appears in this file; the only 64-hex value it handles is
the artifact's own digest, computed at run time (never a literal).
"""

import importlib.util
import os
import subprocess
import sys
import zipfile

import pytest
from ruamel.yaml import YAML

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
TOOLS = os.path.join(REPO, "tools")
BUILD_PATH = os.path.join(TOOLS, "build_skill.py")
CHECKER = os.path.join(TOOLS, "check_provenance_leak.py")
MEASURE = os.path.join(TOOLS, "measure_context.py")
FIX = os.path.join(HERE, "fixtures")
PATTERNS_PATH = os.path.abspath(os.path.join(REPO, os.pardir, "leak-patterns-private.yaml"))

TOP = "stow"
RUNTIME_ALLOW = {"stow/runtime/validate.py", "stow/runtime/lint_prose.py",
                 "stow/runtime/profiles.py"}
HARD_CEILING = 1500

# Surfaces that must never appear inside the shipped artifact.
FORBIDDEN_SUBSTRINGS = (
    "tools/",
    "tests/",
    "check_provenance_leak",
    "leak-patterns",
    "provenance",
    "hash-positions",
    "measure_context",
    "__pycache__",
    ".pyc",
)


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build_skill = _load("build_skill", BUILD_PATH)


# --------------------------------------------------------------------------- #
# Shared build/extract fixture (built once for the module)
# --------------------------------------------------------------------------- #

class Built:
    def __init__(self, result, extract_root, names):
        self.result = result
        self.extract_root = extract_root
        self.names = names
        self.digest = result["sha256"]

    def path(self, *parts):
        return os.path.join(self.extract_root, *parts)

    def extracted_files(self):
        collected = []
        for dirpath, _dirs, filenames in os.walk(self.extract_root):
            for filename in filenames:
                collected.append(os.path.abspath(os.path.join(dirpath, filename)))
        return collected


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out_dir = tmp_path_factory.mktemp("dist")
    result = build_skill.build(root=REPO, out_dir=str(out_dir))

    extract_root = str(tmp_path_factory.mktemp("extract"))
    with zipfile.ZipFile(result["artifact_path"]) as archive:
        names = archive.namelist()
        archive.extractall(extract_root)

    return Built(result, extract_root, names)


# --------------------------------------------------------------------------- #
# Reproducibility
# --------------------------------------------------------------------------- #

def test_two_builds_are_byte_identical():
    first, _entries1 = build_skill.build_archive_bytes(REPO)
    second, _entries2 = build_skill.build_archive_bytes(REPO)
    assert first == second


def test_two_builds_have_identical_sha256(tmp_path):
    a = build_skill.build(root=REPO, out_dir=str(tmp_path / "a"))
    b = build_skill.build(root=REPO, out_dir=str(tmp_path / "b"))
    assert a["sha256"] == b["sha256"]
    # The on-disk artifacts match byte-for-byte, not merely their digests.
    with open(a["artifact_path"], "rb") as fh_a, open(b["artifact_path"], "rb") as fh_b:
        assert fh_a.read() == fh_b.read()


def test_sidecar_and_manifest_report_the_archive_digest(built):
    with open(built.result["sha256_path"], encoding="utf-8") as fh:
        sidecar = fh.read()
    assert sidecar.split()[0] == built.digest
    assert "STOW.skill" in sidecar

    yaml = YAML(typ="safe")
    with open(built.result["manifest_path"], encoding="utf-8") as fh:
        manifest = yaml.load(fh)
    assert manifest["artifact_sha256"] == built.digest
    assert manifest["entry_count"] == len(built.names)
    assert set(manifest["entries"]) == set(built.names)
    for key in ("python", "zlib", "platform"):
        assert manifest["versions"][key]


# --------------------------------------------------------------------------- #
# Archive shape
# --------------------------------------------------------------------------- #

def test_single_top_level_directory_is_stow(built):
    top_level = {name.split("/", 1)[0] for name in built.names}
    assert top_level == {TOP}


def test_skill_md_is_present(built):
    assert "stow/SKILL.md" in built.names


def test_corpus_tree_is_present(built):
    assert any(name.startswith("stow/corpus/") for name in built.names)


def test_runtime_is_exactly_the_allowlist(built):
    runtime = {name for name in built.names if name.startswith("stow/runtime/")}
    assert runtime == RUNTIME_ALLOW


def test_no_forbidden_surfaces_in_archive(built):
    for name in built.names:
        for needle in FORBIDDEN_SUBSTRINGS:
            assert needle not in name, "forbidden %r in archived %r" % (needle, name)


def test_deterministic_zip_metadata(built):
    with zipfile.ZipFile(built.result["artifact_path"]) as archive:
        for info in archive.infolist():
            assert info.compress_type == zipfile.ZIP_STORED
            assert info.create_system == 3
            assert info.external_attr == (0o644 << 16)
            assert info.date_time == (1980, 1, 1, 0, 0, 0)
            assert info.flag_bits == 0
            assert info.extra == b""
    assert archive.comment == b""


# --------------------------------------------------------------------------- #
# Corpus references resolve inside the extracted tree
# --------------------------------------------------------------------------- #

def test_every_corpus_ref_resolves_inside_extracted_tree(built):
    yaml = YAML(typ="safe")
    with open(built.path("stow", "rules", "registry.yaml"), encoding="utf-8") as fh:
        registry = yaml.load(fh)

    records = registry["records"]
    assert records, "registry carries no records"

    for record in records:
        ref = record["corpus_ref"]  # e.g. corpus/words/stow-wrd-001.md
        member = built.path("stow", *ref.split("/"))
        assert os.path.isfile(member), "corpus_ref %r missing in artifact" % ref
        # The resolved member stays inside the extracted tree (no traversal).
        root = os.path.abspath(built.extract_root)
        assert os.path.abspath(member).startswith(root + os.sep)


# --------------------------------------------------------------------------- #
# Import-closure: runtime modules import with the repo root OFF sys.path
# --------------------------------------------------------------------------- #

_IMPORT_CLOSURE_BOOTSTRAP = r"""
import importlib.util, os, sys
repo = os.path.abspath(sys.argv[1])
target = os.path.abspath(sys.argv[2])
# sys.path becomes the extract only: drop cwd sentinels and the repo root, keep
# the runtime dir plus stdlib / site-packages so installed deps still resolve.
kept = []
for entry in sys.path:
    if entry in ("", "."):
        continue
    if os.path.abspath(entry) == repo:
        continue
    kept.append(entry)
sys.path = [os.path.dirname(target)] + kept
assert repo not in [os.path.abspath(p) for p in sys.path], "repo root still on path"
name = os.path.splitext(os.path.basename(target))[0]
spec = importlib.util.spec_from_file_location(name, target)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
sys.stdout.write("IMPORT_OK")
"""


def _run_import_closure(module_path):
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)  # do not smuggle the repo back onto the path
    return subprocess.run(
        [sys.executable, "-c", _IMPORT_CLOSURE_BOOTSTRAP, REPO, module_path],
        capture_output=True, text=True, cwd=os.path.dirname(module_path), env=env)


def test_runtime_modules_are_import_closed(built):
    runtime_dir = built.path("stow", "runtime")
    modules = sorted(
        os.path.join(runtime_dir, f)
        for f in os.listdir(runtime_dir) if f.endswith(".py"))
    assert len(modules) == 3

    for module_path in modules:
        proc = _run_import_closure(module_path)
        assert proc.returncode == 0, "import failed for %s: %s" % (module_path, proc.stderr)
        assert proc.stdout.strip().endswith("IMPORT_OK")


# --------------------------------------------------------------------------- #
# Re-validation of the extracted tree
# --------------------------------------------------------------------------- #

def test_extracted_validator_accepts_a_valid_fixture(built):
    validate_py = built.path("stow", "runtime", "validate.py")
    fixture = os.path.join(FIX, "yaml", "valid.yaml")
    proc = subprocess.run(
        [sys.executable, validate_py, "--format", "yaml", fixture],
        capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr


def test_extracted_skill_md_is_within_context_ceiling(built):
    skill_md = built.path("stow", "SKILL.md")
    proc = subprocess.run(
        [sys.executable, MEASURE, skill_md], capture_output=True, text=True)
    # measure_context exits nonzero only when over the 1500-token hard ceiling.
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "hard ceiling %d: OK" % HARD_CEILING in proc.stdout


_HAS_PATTERNS = os.path.isfile(PATTERNS_PATH)


@pytest.mark.skipif(not _HAS_PATTERNS,
                    reason="private pattern file absent (weak/CI environment)")
def test_extracted_tree_and_manifest_repass_both_leak_gates(built):
    targets = built.extracted_files()
    targets.append(built.result["manifest_path"])
    targets.append(built.result["artifact_path"])  # binary; skipped by the gate

    proc = subprocess.run(
        [sys.executable, CHECKER, "--local"] + targets,
        capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "LEAK CHECK PASSED" in proc.stdout
