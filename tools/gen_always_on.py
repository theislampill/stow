#!/usr/bin/env python3
"""Generate skills/stow/references/always-on.md from the registry.

The always-on module is the operational form of every rule flagged
``activation.always_on_for_prose: true`` (the action-shaping and unconditional
prose-integrity families). It is loaded on every user-facing PROSE turn so the
always-on rules actually govern ordinary output; protected regions are excluded.

Only STOW-authored fields (``title``, ``category``, ``corpus_ref``) are emitted,
so the generated file is source-name-free. Deterministic (sorted by id), so
``--check`` proves the committed file matches the registry.
"""

import os
import sys

from ruamel.yaml import YAML

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
REGISTRY = os.path.join(REPO, "skills", "stow", "rules", "registry.yaml")
OUT = os.path.join(REPO, "skills", "stow", "references", "always-on.md")

HEADER = (
    "# Always-on operational checks\n"
    "\n"
    "Apply these on every user-facing PROSE turn. They are the operational form of\n"
    "the always-on rule families. Protected regions -- raw JSON, JSONL, YAML, code,\n"
    "quotations, identifiers, and paths -- are excluded: apply none of these inside\n"
    "them. For the full statement, definitions, qualifications, and worked examples\n"
    "of any check, load its corpus module.\n"
)


def _records():
    yaml = YAML(typ="safe")
    with open(REGISTRY, encoding="utf-8") as fh:
        reg = yaml.load(fh)
    recs = reg.get("records") or reg.get("rules")
    on = [r for r in recs if (r.get("activation") or {}).get("always_on_for_prose")]
    on.sort(key=lambda r: r["id"])
    return on


def build():
    on = _records()
    action = [r for r in on if r["id"].startswith("STOW-ACT-")]
    prose = [r for r in on if r["id"].startswith("STOW-PRO-")]
    parts = [HEADER, ""]
    for heading, group in (("## Action shaping", action), ("## Prose integrity", prose)):
        parts.append(heading)
        parts.append("")
        for r in group:
            parts.append("- %s  (see %s)" % (r["title"].strip(), r["corpus_ref"]))
        parts.append("")
    return "\n".join(parts).rstrip("\n") + "\n", len(action), len(prose)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    text, n_action, n_prose = build()
    if "--check" in argv:
        current = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else None
        if current != text:
            print("always-on.md is STALE relative to the registry -- regenerate")
            return 1
        print("always-on.md is current (%d action + %d prose)" % (n_action, n_prose))
        return 0
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print("wrote %s (%d action + %d prose = %d always-on checks)"
          % (OUT, n_action, n_prose, n_action + n_prose))
    return 0


if __name__ == "__main__":
    sys.exit(main())
