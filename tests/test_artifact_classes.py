"""Owner-class gate for the packaged STOW artifact.

``skills/stow/rules/artifact-classes.yaml`` classifies every file that
``tools/build_skill.py`` packages into exactly one of eight owner classes and
binds each class to the checks that govern it. This module proves the
classification is complete and honest against the actual package walk.

Gates:
  * classification exactly covers the packaged file set (nothing unclassified,
    nothing classified that is not packaged),
  * every file is in exactly one class,
  * every class binds at least one check, and every named check file exists,
  * every generated-artifact file names an existing generator tool,
  * every kernel or operational-reference file is present in the self-dogfood
    walker set (imported from tests/test_self_dogfood.py, not duplicated).

Source-name-free: names none of the external projects the rules derive from.
"""

import importlib.util
import os

from ruamel.yaml import YAML

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
CLASSES_PATH = os.path.join(REPO, "skills", "stow", "rules", "artifact-classes.yaml")

REQUIRED_CLASSES = frozenset({
    "kernel", "operational-reference", "protected-corpus", "profile-or-rule-data",
    "runtime-code", "schema", "template", "generated-artifact",
})
DOGFOOD_CLASSES = frozenset({"kernel", "operational-reference"})


# --------------------------------------------------------------------------- #
# Loaders
# --------------------------------------------------------------------------- #

def _load_yaml(path):
    yaml = YAML(typ="safe")
    with open(path, encoding="utf-8") as handle:
        return yaml.load(handle)


def _load_module(name, relpath):
    spec = importlib.util.spec_from_file_location(name, os.path.join(REPO, relpath))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CLASSES = _load_yaml(CLASSES_PATH)["classes"]


def _packaged_set():
    """The exact file set build_skill.py packages, as repo-relative paths."""
    build = _load_module("build_skill_for_classes", os.path.join("tools", "build_skill.py"))
    out = set()
    for _abs, arc in build.collect_entries(build.repo_root()):
        # arc == "stow/<rel>"; repo-relative is "skills/stow/<rel>".
        out.add("skills/stow/" + arc.split("/", 1)[1])
    return out


def _class_file_paths(entry):
    """Normalise a class's ``files`` list to plain path strings. A
    generated-artifact entry is a {path, generator} map; others are strings."""
    paths = []
    for item in CLASSES[entry].get("files") or []:
        paths.append(item["path"] if isinstance(item, dict) else item)
    return paths


def _all_classified_paths():
    paths = []
    for name in CLASSES:
        paths.extend(_class_file_paths(name))
    return paths


PACKAGED = _packaged_set()


# --------------------------------------------------------------------------- #
# Structure
# --------------------------------------------------------------------------- #

def test_all_eight_classes_present():
    assert set(CLASSES) == REQUIRED_CLASSES, (
        "class set mismatch: missing=%r extra=%r"
        % (sorted(REQUIRED_CLASSES - set(CLASSES)),
           sorted(set(CLASSES) - REQUIRED_CLASSES)))


def test_every_class_binds_at_least_one_check():
    for name, body in CLASSES.items():
        checks = body.get("checks") or []
        assert checks, "class %r binds zero checks" % name
        for check in checks:
            assert os.path.isfile(os.path.join(REPO, check)), (
                "class %r names a check that does not exist: %s" % (name, check))


# --------------------------------------------------------------------------- #
# Completeness: classification == packaged set, each file once
# --------------------------------------------------------------------------- #

def test_every_file_classified_exactly_once():
    classified = _all_classified_paths()
    dupes = sorted({p for p in classified if classified.count(p) > 1})
    assert not dupes, "files classified in more than one class: %r" % dupes


def test_no_packaged_file_is_unclassified():
    classified = set(_all_classified_paths())
    unclassified = sorted(PACKAGED - classified)
    assert not unclassified, "packaged files with no class: %r" % unclassified


def test_no_classified_file_is_unpackaged():
    classified = set(_all_classified_paths())
    phantom = sorted(classified - PACKAGED)
    assert not phantom, "classified paths that are not packaged: %r" % phantom


def test_classified_files_exist_on_disk():
    for path in _all_classified_paths():
        assert os.path.isfile(os.path.join(REPO, path)), (
            "classified path does not exist: %s" % path)


# --------------------------------------------------------------------------- #
# Generated artifacts carry a generator
# --------------------------------------------------------------------------- #

def test_generated_artifacts_name_an_existing_generator():
    files = CLASSES["generated-artifact"].get("files") or []
    assert files, "generated-artifact class lists no files"
    for item in files:
        assert isinstance(item, dict), (
            "generated-artifact entry must be a {path, generator} map: %r" % item)
        assert item.get("generator"), (
            "generated-artifact file %r lacks a named generator" % item.get("path"))
        tool = item["generator"].split()[0]
        assert os.path.isfile(os.path.join(REPO, tool)), (
            "generated-artifact %s names a missing generator tool: %s"
            % (item["path"], tool))


# --------------------------------------------------------------------------- #
# Authored prose surfaces are covered by the self-dogfood walker
# --------------------------------------------------------------------------- #

def test_kernel_and_reference_files_are_in_dogfood_set():
    dogfood = _load_module("self_dogfood_for_classes",
                           os.path.join("tests", "test_self_dogfood.py"))
    covered = {rel for rel, _profile in dogfood.SURFACES}
    for cls in DOGFOOD_CLASSES:
        for path in _class_file_paths(cls):
            assert path in covered, (
                "%s file %s is absent from the self-dogfood walker set" % (cls, path))


def test_no_em_dash_in_artifact_classes():
    with open(CLASSES_PATH, encoding="utf-8") as handle:
        assert "—" not in handle.read(), "artifact-classes.yaml contains an em dash"
