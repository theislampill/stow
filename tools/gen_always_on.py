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
    "\n"
    "These checks yield to safety, the output contract, and factual accuracy: keep\n"
    "justified uncertainty, disclose a material limitation or failed verification\n"
    "in one clause, and honor a requested hypothetical that is labeled as one. Cross-rule\n"
    "collisions resolve per rules/conflicts.yaml. Open the turn per the\n"
    "request-mode router below.\n"
)

# Request-mode router: what leads the response, by request intent. Lines are
# indented (not list bullets) so the bullet-count selector below stays exact.
# A raw-artifact turn never loads this file (the kernel excludes protected
# regions); its row is kept so the router reads complete on its own.
ROUTER = (
    "## Request-mode router\n"
    "\n"
    "Open with what the request type demands:\n"
    "\n"
    "  informational question: the answer or result first\n"
    "  explanation: the thesis first\n"
    "  actionable task: the next bounded action first\n"
    "  requested artifact: the artifact itself first\n"
    "  raw artifact: the raw artifact alone, composed once: no wrapper, no"
    " draft-then-correction, no validation notes in the reply\n"
    "  progress update: current state and completed results first\n"
    "  error report: cause, then effect, then correction\n"
    "  completed work: the result; invent no next action\n"
    "  open work: one concrete next action may close the turn\n"
)


def _records():
    yaml = YAML(typ="safe")
    with open(REGISTRY, encoding="utf-8") as fh:
        reg = yaml.load(fh)
    recs = reg.get("records") or reg.get("rules")
    on = [r for r in recs if (r.get("activation") or {}).get("always_on_for_prose")]
    on.sort(key=lambda r: r["id"])
    return on


def _bullet(record):
    """One operational check: short id, title, applicability, exception,
    corpus pointer. The qualifier fields are STOW-authored registry fields
    (activation.applicability / activation.exception); a rule whose source
    carries a condition must not appear here as a bare title."""
    short_id = record["id"].replace("STOW-", "", 1)
    activation = record.get("activation") or {}
    line = "- %s %s" % (short_id, record["title"].strip())
    clauses = []
    if activation.get("applicability"):
        clauses.append("when: %s" % activation["applicability"])
    if activation.get("exception"):
        clauses.append("except: %s" % activation["exception"])
    if clauses:
        line += " -- " + "; ".join(clauses)
    line += "  (see %s)" % record["corpus_ref"]
    return line


def build():
    on = _records()
    action = [r for r in on if r["id"].startswith("STOW-ACT-")]
    prose = [r for r in on if r["id"].startswith("STOW-PRO-")]
    parts = [HEADER, ROUTER, ""]
    for heading, group in (("## Action shaping", action), ("## Prose integrity", prose)):
        parts.append(heading)
        parts.append("")
        for r in group:
            parts.append(_bullet(r))
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
