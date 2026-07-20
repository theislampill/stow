"""Topology-consistency gate.

Pins the public documentation's topology claims to on-disk reality so a stale
count or an outdated architecture phrase cannot ship:

  * README carries no "one module per rule" claim (the topology is grouped
    anchored modules now);
  * the corpus module count stated in prose is derived from the on-disk module
    count, not merely a hardcoded number;
  * AGENTS.md describes the packaged runtime allowlist truthfully against
    ``build_skill.RUNTIME_ALLOW`` (a selector reference, or a count that matches
    the allowlist size);
  * ``dist/manifest.json`` entry count equals the packaged file walk count;
  * ``plugin.json`` version equals the top released CHANGELOG section version.

Source-name-free: names none of the external projects the rules derive from.
"""

import importlib.util
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

INT_TO_WORD = {
    1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six",
    7: "seven", 8: "eight", 9: "nine", 10: "ten", 11: "eleven", 12: "twelve",
    13: "thirteen", 14: "fourteen", 15: "fifteen", 16: "sixteen",
    17: "seventeen", 18: "eighteen", 19: "nineteen", 20: "twenty",
    21: "twenty-one", 22: "twenty-two", 23: "twenty-three", 24: "twenty-four",
}


def _read(relpath):
    with open(os.path.join(REPO, relpath), encoding="utf-8") as handle:
        return handle.read()


def _load_build():
    spec = importlib.util.spec_from_file_location(
        "build_skill_for_topology", os.path.join(REPO, "tools", "build_skill.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _corpus_module_count():
    """Count corpus modules on disk (the topology's grouped modules)."""
    root = os.path.join(REPO, "skills", "stow", "corpus")
    total = 0
    for _dirpath, _dirnames, filenames in os.walk(root):
        total += sum(1 for name in filenames if name.endswith(".md"))
    return total


# --------------------------------------------------------------------------- #
# README topology claims
# --------------------------------------------------------------------------- #

def test_readme_has_no_one_module_per_rule_claim():
    assert "one module per rule" not in _read("README.md"), (
        "README still claims 'one module per rule'; the topology is grouped "
        "anchored modules now")


def test_corpus_module_count_prose_is_dynamic_and_agrees():
    """The corpus-topology count stated in prose must equal the on-disk count.

    Derived dynamically: the assertion recomputes the module count from disk and
    checks that the word form is the one the readiness sheet publishes, so a
    module added or removed without a doc update fails here."""
    n = _corpus_module_count()
    word = INT_TO_WORD[n]
    text = _read("docs/REWRITE-READINESS.md").lower()
    assert ("%s anchored corpus modules" % word) in text, (
        "REWRITE-READINESS.md must state %r anchored corpus modules to match the "
        "%d on-disk modules" % (word, n))


# --------------------------------------------------------------------------- #
# AGENTS.md runtime allowlist claim
# --------------------------------------------------------------------------- #

def test_agents_runtime_allowlist_claim_is_accurate():
    build = _load_build()
    n = len(build.RUNTIME_ALLOW)
    text = _read("AGENTS.md")
    match = re.search(r"([A-Za-z-]+)\s+allowlisted runtime modules", text)
    if match:
        assert INT_TO_WORD.get(n) == match.group(1).lower(), (
            "AGENTS.md hardcodes a runtime-module count that disagrees with "
            "RUNTIME_ALLOW size %d" % n)
    else:
        assert "RUNTIME_ALLOW" in text, (
            "AGENTS.md must name build_skill.RUNTIME_ALLOW or state a count that "
            "matches its size")


# --------------------------------------------------------------------------- #
# Manifest and version consistency
# --------------------------------------------------------------------------- #

def test_manifest_entry_count_matches_package_walk():
    build = _load_build()
    entries = build.collect_entries(build.repo_root())
    manifest = json.loads(_read(os.path.join("dist", "manifest.json")))
    assert manifest["entry_count"] == len(entries), (
        "manifest entry_count %d != packaged walk count %d"
        % (manifest["entry_count"], len(entries)))
    assert len(manifest["entries"]) == len(entries), (
        "manifest entries list length != packaged walk count")


def test_plugin_version_matches_top_released_changelog_section():
    version = json.loads(_read(os.path.join(".claude-plugin", "plugin.json")))["version"]
    changelog = _read("CHANGELOG.md")
    match = re.search(r"^## \[(\d+\.\d+\.\d+)\]", changelog, re.MULTILINE)
    assert match, "no released version heading found in CHANGELOG.md"
    assert match.group(1) == version, (
        "plugin.json version %s != top released CHANGELOG section %s"
        % (version, match.group(1)))
