"""Gates for the always-on activation architecture.

The always-on rule families (action shaping + unconditional prose integrity) must
actually govern ordinary user-facing prose turns. v0.1 loaded them only behind a
vague "deep guidance" predicate, so they never applied on the turns they exist to
govern. These gates prove the repaired architecture STRUCTURALLY:

  1. a generated operational module exists, is registry-derived, and is current;
  2. every always-on rule is represented in it;
  3. the kernel routes ordinary prose turns to it and excludes protected regions;
  4. the ordinary-turn footprint stays bounded;
  5. the kernel still carries its byte-exact no-greedy-loading rule.

HONEST SCOPE: these are structural/routing contracts over the shipped files. There
is no model-invocation harness here, so they prove the kernel *instructs* the load
and the module is complete -- not that a live model performed it.
"""

import os
import re
import subprocess
import sys

import tiktoken
from ruamel.yaml import YAML

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SKILL_DIR = os.path.join(REPO, "skills", "stow")
KERNEL = os.path.join(SKILL_DIR, "SKILL.md")
ALWAYS_ON = os.path.join(SKILL_DIR, "references", "always-on.md")
REGISTRY = os.path.join(SKILL_DIR, "rules", "registry.yaml")
GEN = os.path.join(REPO, "tools", "gen_always_on.py")

ALWAYS_ON_TOKEN_CAP = 900
KERNEL_TOKEN_CEILING = 1500
ORDINARY_TURN_CAP = 2200  # kernel + always-on must stay bounded

KERNEL_ALONE_LINE = (
    "Do not read every reference or corpus module. "
    "When no predicate is true, answer from this kernel alone."
)


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _tokens(text):
    return len(tiktoken.get_encoding("o200k_base").encode(text))


def _always_on_records():
    yaml = YAML(typ="safe")
    with open(REGISTRY, encoding="utf-8") as fh:
        reg = yaml.load(fh)
    recs = reg.get("records") or reg.get("rules")
    return [r for r in recs if (r.get("activation") or {}).get("always_on_for_prose")]


# --------------------------------------------------------------------------- #
# 1. the module exists, is generated, and is current
# --------------------------------------------------------------------------- #

def test_always_on_module_exists():
    assert os.path.isfile(ALWAYS_ON), "always-on.md is missing"
    assert _read(ALWAYS_ON).strip(), "always-on.md is empty"


def test_always_on_is_current_with_registry():
    """Regeneration is deterministic: the committed file matches the registry."""
    result = subprocess.run([sys.executable, GEN, "--check"],
                            capture_output=True, text=True)
    assert result.returncode == 0, "always-on.md is stale: %s" % result.stdout


# --------------------------------------------------------------------------- #
# 2. every always-on rule is represented
# --------------------------------------------------------------------------- #

def test_every_always_on_rule_is_present():
    text = _read(ALWAYS_ON)
    records = _always_on_records()
    assert records, "no records carry activation.always_on_for_prose"
    missing = [r["id"] for r in records if r["title"].strip() not in text]
    assert not missing, "always-on rules absent from the module: %s" % missing


def test_module_bullet_count_matches_selector():
    bullets = [ln for ln in _read(ALWAYS_ON).splitlines() if ln.startswith("- ")]
    assert len(bullets) == len(_always_on_records())


def test_every_bullet_cites_its_corpus_module():
    """Full statement/examples stay Tier-3: each check points at its corpus module."""
    for line in _read(ALWAYS_ON).splitlines():
        if line.startswith("- "):
            assert re.search(r"\(see corpus/[\w./-]+\.md\)", line), line


# --------------------------------------------------------------------------- #
# 3. the kernel routes ordinary prose turns here, and excludes protected regions
# --------------------------------------------------------------------------- #

def test_kernel_activates_always_on_for_prose_turns():
    kernel = _read(KERNEL)
    assert "references/always-on.md" in kernel, "kernel never routes to always-on.md"
    line = next(ln for ln in kernel.splitlines() if "references/always-on.md" in ln)
    assert re.search(r"\bprose turn\b", line, re.I), line


def test_kernel_excludes_protected_regions_from_always_on():
    """A raw artifact must NOT pull the prose checks in."""
    line = next(ln for ln in _read(KERNEL).splitlines()
                if "references/always-on.md" in ln)
    assert re.search(r"exclud", line, re.I), line
    for token in ("JSON", "code"):
        assert token in line, "protected-region exclusion does not name %s" % token


def test_kernel_routes_meta_code_artifacts():
    assert "references/meta-code.md" in _read(KERNEL)


# --------------------------------------------------------------------------- #
# 4/5. bounded footprint + the no-greedy-loading rule survives
# --------------------------------------------------------------------------- #

def test_always_on_module_within_budget():
    assert _tokens(_read(ALWAYS_ON)) <= ALWAYS_ON_TOKEN_CAP


def test_kernel_within_ceiling():
    assert _tokens(_read(KERNEL)) <= KERNEL_TOKEN_CEILING


def test_ordinary_prose_turn_footprint_is_bounded():
    total = _tokens(_read(KERNEL)) + _tokens(_read(ALWAYS_ON))
    assert total <= ORDINARY_TURN_CAP, "ordinary prose turn costs %d tokens" % total


def test_kernel_keeps_no_greedy_loading_rule():
    assert KERNEL_ALONE_LINE in _read(KERNEL)


def test_kernel_does_not_inline_corpus():
    """Tier-3 material must not be pulled into the always-loaded kernel."""
    kernel = _read(KERNEL)
    assert not re.search(r"corpus/[\w./-]+\.md", kernel), \
        "kernel inlines a concrete corpus module path"
