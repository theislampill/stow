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
import json
import os

import pytest
from ruamel.yaml import YAML

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
RUNTIME = os.path.join(REPO, "skills", "stow", "runtime")
RULES = os.path.join(REPO, "skills", "stow", "rules")
SCHEMAS = os.path.join(REPO, "skills", "stow", "schemas")

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


# --------------------------------------------------------------------------- #
# YAML/JSONL template comments carry authored prose that the .md self-dogfood
# scan never reaches (those files are data surfaces, not .md). A comment is
# still authored English, so it must obey the em-dash rule and the lexical
# subset below. This closes the governance gap where an em dash or an AI tell
# could hide in a template comment.
# --------------------------------------------------------------------------- #

YAML_TEMPLATE_FILES = ("task-packet.yaml", "event-stream.jsonl")

# The deterministic prose checks meaningful for a short comment line.
COMMENT_GATED_RULES = frozenset({
    "em-dash", "intensifier", "filler-phrase", "whether-youre-opener",
    "weasel-phrase", "ai-transition", "ai-verb", "academic-tell",
})


def _comment_prose(path):
    """The authored prose of a YAML/JSONL file: its comment lines, joined."""
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh.read().splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                out.append(stripped.lstrip("#").strip())
    return "\n".join(out)


@pytest.mark.parametrize("name", YAML_TEMPLATE_FILES)
def test_yaml_template_comments_have_no_em_dash(name):
    path = os.path.join(REPO, "skills", "stow", "templates", name)
    assert "—" not in _comment_prose(path), (
        "%s has an em dash in a comment" % name)


@pytest.mark.parametrize("name", YAML_TEMPLATE_FILES)
def test_yaml_template_comments_pass_lexical_subset(name):
    path = os.path.join(REPO, "skills", "stow", "templates", name)
    text = _comment_prose(path)
    findings = [a for a in lint_prose.lint(text, profile=CLARITY, tables=TABLES)
                if a.rule in COMMENT_GATED_RULES]
    assert findings == [], (
        "%s comment prose betrays a lexical rule: %r"
        % (name, [(a.line, a.rule, a.message[:50]) for a in findings]))


# --------------------------------------------------------------------------- #
# Structured-field prose coverage. The .md scan above reaches authored Markdown;
# it never reaches the prose that lives INSIDE the structured rule data and the
# schema files -- a profile note or auto-context, a routing predicate or reason,
# a conflict's activation / behavior / substitute wording, a schema title or
# description. Those strings are authored English and must obey the same em-dash
# and banned-lexical subset. This closes that governance gap.
#
# Fixture strings in the conflict registry (positive / adversarial /
# expected_rewrite) are DELIBERATE demonstrations: the adversarial ones embody
# the very patterns the rules forbid. They are the structured analog of the
# quotations the linter already masks, so they are never scanned -- exactly the
# masked-quote discipline the .md gate relies on.
# --------------------------------------------------------------------------- #

# em-dash + every banned-lexical check. No profile-gated or scare-quote checks:
# these are short data strings and the scanned subset is em-dash + banned
# lexical.
STRUCTURED_FIELD_RULES = frozenset({
    "em-dash", "intensifier", "filler-phrase", "whether-youre-opener",
    "weasel-phrase", "ai-transition", "ai-verb", "academic-tell",
    "metaphorical-noun", "overused-adjective", "hedging",
})

# The conflict-registry keys that carry STOW-authored advisory prose. The
# fixtures block is intentionally absent (protected demonstration content).
CONFLICT_PROSE_KEYS = (
    "activation_predicate", "losing_behavior", "permitted_substitute",
    "registry_resolution", "tie_break", "evidence",
)


def _safe_yaml(path):
    with open(path, encoding="utf-8") as fh:
        return YAML(typ="safe").load(fh)


def _walk_schema_prose(node, path, out):
    """Collect (label, string) for every title/description anywhere in a schema
    document. Source-neutral: it keys on the field names, not on content."""
    if isinstance(node, dict):
        for key in ("title", "description"):
            value = node.get(key)
            if isinstance(value, str):
                out.append(("%s.%s" % (path, key), value))
        for key, value in node.items():
            _walk_schema_prose(value, "%s.%s" % (path, key), out)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            _walk_schema_prose(value, "%s[%d]" % (path, index), out)


def _structured_prose_fields():
    """Every STOW-authored prose string carried inside the structured rule data
    and schema files, as a list of (label, text). Source-neutral: it walks the
    known prose-bearing fields by name, so it works regardless of which rules
    those files carry."""
    out = []

    with open(os.path.join(RULES, "profiles.json"), encoding="utf-8") as fh:
        profiles_data = json.load(fh)
    for profile in profiles_data.get("profiles", []):
        pid = profile.get("id", "?")
        note = profile.get("notes")
        if isinstance(note, str):
            out.append(("profiles.json profiles[%s].notes" % pid, note))
        for index, ctx in enumerate(profile.get("auto_contexts", []) or []):
            if isinstance(ctx, str):
                out.append(("profiles.json profiles[%s].auto_contexts[%d]"
                            % (pid, index), ctx))

    routing = _safe_yaml(os.path.join(RULES, "routing.yaml")) or {}
    for route in routing.get("routes", []) or []:
        pred = route.get("predicate")
        if isinstance(pred, str):
            out.append(("routing.yaml routes[%s].predicate"
                        % route.get("mode", "?"), pred))
    for entry in routing.get("unrouted", []) or []:
        reason = entry.get("reason")
        if isinstance(reason, str):
            out.append(("routing.yaml unrouted[%s].reason"
                        % entry.get("reference", "?"), reason))

    conflicts = _safe_yaml(os.path.join(RULES, "conflicts.yaml")) or {}
    for conflict in conflicts.get("conflicts", []) or []:
        cid = conflict.get("id", "?")
        for key in CONFLICT_PROSE_KEYS:
            value = conflict.get(key)
            if isinstance(value, str):
                out.append(("conflicts.yaml %s.%s" % (cid, key), value))
        # fixtures[] are deliberate rule-violating demonstrations; not scanned.

    for name in sorted(os.listdir(SCHEMAS)):
        if name.endswith(".json"):
            with open(os.path.join(SCHEMAS, name), encoding="utf-8") as fh:
                schema = json.load(fh)
            _walk_schema_prose(schema, name, out)

    return out


STRUCTURED_FIELDS = _structured_prose_fields()


def test_structured_field_extractor_reaches_every_source():
    labels = [label for label, _text in STRUCTURED_FIELDS]
    assert any("profiles.json" in l for l in labels)
    assert any("routing.yaml routes" in l for l in labels)
    assert any("routing.yaml unrouted" in l for l in labels)
    assert any("conflicts.yaml" in l for l in labels)
    assert any(l.endswith(".description") or l.endswith(".title")
               for l in labels)
    # A conflict fixture string must NEVER be extracted: protected demonstration.
    assert not any("fixtures" in l for l in labels)
    assert len(STRUCTURED_FIELDS) > 40


@pytest.mark.parametrize("label,text", STRUCTURED_FIELDS,
                         ids=[label for label, _text in STRUCTURED_FIELDS])
def test_structured_field_passes_deterministic_prose_subset(label, text):
    findings = [a for a in lint_prose.lint(text, profile=CLARITY, tables=TABLES)
                if a.rule in STRUCTURED_FIELD_RULES]
    assert findings == [], (
        "%s betrays the em-dash / banned-lexical subset: %r"
        % (label, [(a.rule, a.message[:50]) for a in findings]))
