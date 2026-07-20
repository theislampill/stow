"""Self-dogfood gate: STOW's own authored surfaces obey STOW's own
deterministic checks.

Scope: the committed authored prose surfaces, each linted under its mapped
profile through the shipped linter (whose masking already protects fenced
blocks, inline code, block quotes, and identifiers). The gate covers the
DETERMINISTIC subset that must be zero:

  * the em-dash check (always-on),
  * every lexical term-table check (intensifiers, transitions, filler,
    weasel phrases, verbs, academic tells, the opener),
  * the scare-quote and hedging-cluster checks,
  * for the executable-procedure template only: the controlled-profile
    checks (semicolons, contractions, sentence caps).

The list-length advisory is NOT in the gate: exhaustive reference
enumerations are a recorded contract exception (see the conflict registry's
exhaustive-list entry), and list intent is context a linter cannot read.

Never scanned: the protected corpus, rule data, runtime and tool sources,
tests, and dist. Those are data or code surfaces, not authored prose.
"""

import importlib.util
import os

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
RUNTIME = os.path.join(REPO, "skills", "stow", "runtime")

CLARITY = "technical-clarity"
GUIDED = "controlled-technical-guided"

# The gate is never averaged away: these checks must report ZERO findings on
# every surface below. (list-length is deliberately absent.)
GATED_RULES = frozenset({
    "em-dash", "intensifier", "scare-quote", "filler-phrase",
    "whether-youre-opener", "weasel-phrase", "ai-transition", "ai-verb",
    "academic-tell", "metaphorical-noun", "overused-adjective", "hedging",
})
GATED_RULES_GUIDED = GATED_RULES | frozenset({
    "semicolon", "contraction",
    "procedural-sentence-length", "descriptive-sentence-length",
})


def _surfaces():
    out = []
    for name in ("README.md", "AGENTS.md", "CHANGELOG.md"):
        out.append((name, CLARITY))
    for base, _dirs, files in os.walk(os.path.join(REPO, "docs")):
        for f in sorted(files):
            if f.endswith(".md"):
                rel = os.path.relpath(os.path.join(base, f), REPO)
                out.append((rel.replace(os.sep, "/"), CLARITY))
    out.append(("skills/stow/SKILL.md", CLARITY))
    refs = os.path.join(REPO, "skills", "stow", "references")
    for f in sorted(os.listdir(refs)):
        if f.endswith(".md"):
            out.append(("skills/stow/references/" + f, CLARITY))
    templates = os.path.join(REPO, "skills", "stow", "templates")
    for f in sorted(os.listdir(templates)):
        if f.endswith(".md"):
            profile = GUIDED if f == "RUNBOOK.md" else CLARITY
            out.append(("skills/stow/templates/" + f, profile))
    return out


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


lint_prose = _load("lint_prose_for_dogfood", os.path.join(RUNTIME, "lint_prose.py"))
TABLES = lint_prose.load_banned_lists()
SURFACES = _surfaces()


def test_surface_list_is_complete():
    names = [s for s, _p in SURFACES]
    assert "README.md" in names and "skills/stow/SKILL.md" in names
    assert not any(n.startswith("skills/stow/corpus/") for n in names)
    assert len(names) > 30


@pytest.mark.parametrize("rel,profile", SURFACES, ids=[s for s, _p in SURFACES])
def test_authored_surface_passes_its_own_deterministic_checks(rel, profile):
    with open(os.path.join(REPO, rel), encoding="utf-8") as fh:
        text = fh.read()
    gated = GATED_RULES_GUIDED if profile == GUIDED else GATED_RULES
    findings = [a for a in lint_prose.lint(text, profile=profile, tables=TABLES)
                if a.rule in gated]
    assert findings == [], (
        "%s betrays its own rules under %s: %r"
        % (rel, profile, [(a.line, a.rule, a.message[:50]) for a in findings]))
