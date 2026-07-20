#!/usr/bin/env python3
"""Generate the README rule-class table and the complete primary-rule catalog
from the registry.

Two marked regions in README.md are owned by this generator:

  <!-- RULE-CLASSES:BEGIN --> ... <!-- RULE-CLASSES:END -->
  <!-- CATALOG:BEGIN -->      ... <!-- CATALOG:END -->

Everything between each marker pair is replaced wholesale; everything outside
is authored prose. Deterministic (registry order within each category), so
``--check`` proves the committed README matches the registry.

The catalog prints no per-category totals and no numeric rule counts: the
integrity test derives every total dynamically from the registry instead.
"""

import io
import os
import sys

from ruamel.yaml import YAML

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
REGISTRY = os.path.join(REPO, "skills", "stow", "rules", "registry.yaml")
README = os.path.join(REPO, "README.md")

# Category -> (heading, one-line reader description). Order is presentation
# order in the catalog.
CATEGORIES = (
    ("action-shaping",  "Action and task shaping",
     "How a reply opens, closes, tracks progress, and stays actionable."),
    ("prose-integrity", "Prose integrity",
     "No filler, no fabricated specificity, no synthetic voice."),
    ("words",           "Words and terminology",
     "Word choice and consistent naming under the controlled profile."),
    ("multiword-nouns", "Multi-word nouns",
     "Length and clarity limits for noun clusters."),
    ("verbs",           "Verbs and voice",
     "Verb forms, tense, and the active voice."),
    ("sentences",       "Sentences and paragraphs",
     "Sentence completeness, length discipline, and paragraph focus."),
    ("procedures",      "Procedures",
     "Instruction shape and sentence limits for executable steps."),
    ("descriptions",    "Descriptive writing",
     "Structure and length discipline for explanatory text."),
    ("safety",          "Safety instructions",
     "Complete, correctly formed warnings, cautions, and notes."),
    ("punctuation",     "Punctuation and word counting",
     "Punctuation limits and how words are counted against caps."),
    ("style",           "Writing style",
     "Rewriting guidance when a word-for-word fix is not enough."),
    ("general",         "General writing practice",
     "Cross-cutting recommendations for controlled technical text."),
)

STATUS_LABEL = {
    "callable": "Callable",
    "planned": "Planned",
    "review-fallback": "Review-fallback",
}


def _records():
    yaml = YAML(typ="safe")
    with open(REGISTRY, encoding="utf-8") as fh:
        return yaml.load(fh)["records"]


def applies_when(record):
    activation = record["activation"]
    # Prefer the STOW-authored applicability qualifier when present; append the
    # exception so the catalog states the real condition, not just a family bucket.
    applicability = activation.get("applicability")
    if applicability:
        text = applicability.strip()
        exception = activation.get("exception")
        if exception:
            text = "%s; exception: %s" % (text, exception.strip())
        return text
    if record["precedence"] == "system":
        return "Safety notices"
    if activation.get("always_on_for_prose"):
        return "All prose (always on)"
    predicate = activation["predicate"]
    if predicate.startswith("A controlled-technical writing profile is active"):
        return "Controlled profile"
    if "heading" in predicate:
        return "Section headings"
    if "quote" in predicate:
        return "Quoted sources"
    return "Conditional"


def build_rule_classes():
    lines = ["", "| Rule class | What it governs |", "|---|---|"]
    for _cat, heading, desc in CATEGORIES:
        lines.append("| %s | %s |" % (heading, desc))
    lines.append("")
    return "\n".join(lines)


def build_catalog():
    records = _records()
    by_cat = {}
    for record in records:
        by_cat.setdefault(record["category"], []).append(record)
    parts = [""]
    for cat, heading, _desc in CATEGORIES:
        group = by_cat.get(cat, [])
        first = group[0]["id"].replace("STOW-", "", 1)
        last = group[-1]["id"].replace("STOW-", "", 1)
        parts.append("<details>")
        parts.append("<summary><b>%s</b> (%s through %s)</summary>"
                     % (heading, first, last))
        parts.append("")
        parts.append("| Rule | Summary | Applies when | Status |")
        parts.append("|---|---|---|---|")
        for record in group:
            parts.append("| `%s` | %s | %s | %s |" % (
                record["id"],
                record["title"].strip().rstrip("."),
                applies_when(record),
                STATUS_LABEL[record["enforcement"]["status"]],
            ))
        parts.append("")
        parts.append("</details>")
        parts.append("")
    return "\n".join(parts)


def _splice(text, begin, end, body):
    b = text.index(begin) + len(begin)
    e = text.index(end)
    return text[:b] + "\n" + body + text[e:]


def render(text):
    text = _splice(text, "<!-- RULE-CLASSES:BEGIN -->", "<!-- RULE-CLASSES:END -->",
                   build_rule_classes())
    text = _splice(text, "<!-- CATALOG:BEGIN -->", "<!-- CATALOG:END -->",
                   build_catalog())
    return text


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    with io.open(README, encoding="utf-8", newline="") as fh:
        current = fh.read()
    rendered = render(current)
    if "--check" in argv:
        if current != rendered:
            print("README catalog is STALE relative to the registry -- regenerate")
            return 1
        print("README catalog is current")
        return 0
    with io.open(README, "w", encoding="utf-8", newline="") as fh:
        fh.write(rendered)
    print("wrote the README rule-class table and catalog")
    return 0


if __name__ == "__main__":
    sys.exit(main())
