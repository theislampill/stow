"""Cold-path contracts learned from the normal installed-skill runtime probe."""

import os

from ruamel.yaml import YAML


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KERNEL = os.path.join(ROOT, "skills", "stow", "SKILL.md")
ROUTING = os.path.join(ROOT, "skills", "stow", "rules", "routing.yaml")


def _read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def _routes():
    with open(ROUTING, encoding="utf-8") as handle:
        return YAML(typ="safe").load(handle)["routes"]


def test_ordinary_prose_uses_the_loaded_kernel_without_an_extra_reference_turn():
    kernel = _read(KERNEL)
    line = next(
        line for line in kernel.splitlines()
        if "ordinary editable user-facing prose ->" in line
    )
    assert "section 4 of this kernel" in line
    assert "no reference read" in line

    route = next(route for route in _routes() if route["mode"] == "always-on-prose")
    assert route["references"] == []
    assert route["validator"] is None


def test_generated_always_on_detail_is_cold_and_explicit():
    route = next(route for route in _routes() if route["mode"] == "always-on-detail")
    assert route["references"] == ["references/always-on.md"]
    assert "explicit" in route["predicate"].casefold()
    assert route["validator"] is None


def test_normal_prose_does_not_probe_or_materialize_runtime_candidates():
    kernel = " ".join(_read(KERNEL).split()).casefold()
    for phrase in (
        "do not list the runtime directory",
        "do not probe a checker with --help",
        "do not create a temporary candidate",
        "do not run the advisory prose linter",
    ):
        assert phrase in kernel


def test_kernel_carries_the_ordinary_action_and_descriptive_digest():
    kernel = " ".join(_read(KERNEL).split()).casefold()
    for phrase in (
        "number ordered multi-step instructions",
        "lists rather than tables for action sequences",
        "semantic repetition",
        "empty metadiscourse",
        "manufactured contrast",
        "drop an evaluative label that has no supporting fact or criterion",
        "mechanical symmetry or fragmentation",
        "unnecessary sectioning",
        "epistemic opacity",
        "lexical inflation",
    ):
        assert phrase in kernel
