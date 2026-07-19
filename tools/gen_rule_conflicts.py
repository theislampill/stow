#!/usr/bin/env python3
"""Generate docs/rule-conflicts.md from skills/stow/rules/conflicts.yaml.

The conflict registry is the machine-readable source of truth for cross-rule
conflict resolutions; the human document is derived from it, never edited by
hand. Deterministic (entries in id order), so ``--check`` proves the committed
document matches the registry.
"""

import os
import sys

from ruamel.yaml import YAML

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
CONFLICTS = os.path.join(REPO, "skills", "stow", "rules", "conflicts.yaml")
OUT = os.path.join(REPO, "docs", "rule-conflicts.md")

HEADER = (
    "# Cross-rule conflict resolutions\n"
    "\n"
    "GENERATED FILE -- do not edit. Source: `skills/stow/rules/conflicts.yaml`\n"
    "via `tools/gen_rule_conflicts.py`; regenerate after any registry change.\n"
    "\n"
    "Authority: entries marked *registry* mirror the per-record `conflicts[]`\n"
    "edges in `skills/stow/rules/registry.yaml`, which stay canonical for those\n"
    "pairs. Entries marked *composition* are canonical here. Every resolution is\n"
    "terminal: it names the winning band, the losing behavior, and the permitted\n"
    "substitute. `deterministic` means band order or an enumerated substitution\n"
    "decides; `semantic-review` means the entry states the operational test a\n"
    "reviewer applies.\n"
)


def _load():
    yaml = YAML(typ="safe")
    with open(CONFLICTS, encoding="utf-8") as fh:
        data = yaml.load(fh)
    entries = sorted(data["conflicts"], key=lambda c: c["id"])
    return data, entries


def _participants(entry):
    parts = []
    for p in entry["participants"]:
        if p["kind"] == "rule":
            parts.append("`%s`" % p["ref"])
        else:
            parts.append("%s `%s`" % (p["kind"], p["ref"]))
    return " vs ".join(parts)


def build():
    _data, entries = _load()
    parts = [HEADER]
    for entry in entries:
        parts.append("## %s -- %s" % (entry["id"], _participants(entry)))
        parts.append("")
        parts.append("- Origin: %s. Resolution kind: %s."
                     % (entry["origin"], entry["resolution_kind"]))
        parts.append("- Fires when: %s" % entry["activation_predicate"])
        winner = entry["winner"]
        parts.append("- Winner: band `%s` (`%s`)." % (winner["band"], winner["ref"]))
        parts.append("- Losing behavior: %s" % entry["losing_behavior"])
        parts.append("- Permitted substitute: %s" % entry["permitted_substitute"])
        if entry.get("registry_resolution"):
            parts.append("- Registry resolution (canonical, verbatim): %s"
                         % entry["registry_resolution"])
        if entry.get("tie_break"):
            parts.append("- Tie-break: %s" % entry["tie_break"])
        fixtures = entry.get("fixtures", {})
        if fixtures.get("positive"):
            parts.append("- Fixture (conforming): %s" % fixtures["positive"])
        if fixtures.get("adversarial"):
            parts.append("- Fixture (violating): %s" % fixtures["adversarial"])
        if fixtures.get("expected_rewrite"):
            parts.append("- Expected rewrite of the violation: %s"
                         % fixtures["expected_rewrite"])
        parts.append("- Evidence: %s" % entry["evidence"])
        parts.append("")
    return "\n".join(parts).rstrip("\n") + "\n", len(entries)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    text, count = build()
    if "--check" in argv:
        current = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else None
        if current != text:
            print("rule-conflicts.md is STALE relative to conflicts.yaml -- regenerate")
            return 1
        print("rule-conflicts.md is current (%d conflict entries)" % count)
        return 0
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print("wrote %s (%d conflict entries)" % (OUT, count))
    return 0


if __name__ == "__main__":
    sys.exit(main())
