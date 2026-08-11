#!/usr/bin/env python3
"""Generate skills/stow/references/always-on.md from the registry.

The ordinary path keeps individually qualified action checks and a compact
taxonomy of observable prose harms. The generator validates that every prose
record selected by ``activation.always_on_for_prose`` belongs to the taxonomy;
closed punctuation and lexical matchers remain callable advisory tools without
being universal generation instructions.

Only STOW-authored registry fields and STOW-native taxonomy text are emitted.
Output is deterministic, so ``--check`` proves the committed file is current.
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
    "Apply these to editable user-facing prose. Protected regions -- raw JSON,\n"
    "JSONL, YAML, code, quotations, identifiers, and paths -- are excluded.\n"
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

# The digest groups every active prose record by observable effect. The record
# ids are validation data only and are not emitted into the ordinary path.
DESCRIPTIVE_GROUPS = (
    ("semantic repetition",
     "remove repeated meaning when it adds no function",
     ("STOW-PRO-006",)),
    ("empty metadiscourse",
     "cut framing and process narration that do not advance the answer",
     ("STOW-PRO-011",)),
    ("manufactured contrast or escalation",
     "keep intensity, urgency, and enthusiasm proportional to evidence",
     ("STOW-PRO-009",)),
    ("hollow evaluation",
     "replace unsupported verdicts with the fact or criterion behind them",
     ("STOW-PRO-005",)),
    ("mechanical symmetry or fragmentation",
     "combine or vary repeated shapes when they obscure the content",
     ("STOW-PRO-007",)),
    ("heading opacity or unnecessary sectioning",
     "use sections only when they help navigation, and name their contents",
     ()),
    ("lexical inflation or cliché clusters",
     "prefer exact ordinary wording unless a term has a needed technical sense",
     ()),
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
    # The every-turn digest points at the corpus MODULE (per the header, "load its
    # corpus module"); the bullet already leads with the rule id, so the section
    # anchor in corpus_ref is redundant here. The full module#anchor form is kept
    # in the registry (the source of truth).
    module = record["corpus_ref"].split("#", 1)[0]
    line += "  (see %s)" % module
    return line


def _descriptive_digest(prose_records):
    active_ids = {record["id"] for record in prose_records}
    grouped_ids = {rule_id for _label, _summary, ids in DESCRIPTIVE_GROUPS
                   for rule_id in ids}
    if active_ids != grouped_ids:
        raise ValueError(
            "descriptive taxonomy does not cover the active prose selector: "
            "missing=%r extra=%r" %
            (sorted(active_ids - grouped_ids), sorted(grouped_ids - active_ids)))

    lines = [
        "## Descriptive prose digest",
        "",
        "Authorship is irrelevant. Review the observable effect in context:",
        "",
    ]
    for label, summary, _ids in DESCRIPTIVE_GROUPS:
        lines.append("- %s: %s." % (label, summary))
    lines.extend([
        "",
        "When a contextual prose-quality review is requested, load",
        "`references/descriptive-prose.md` for applicability, legitimate",
        "counterexamples, rewrite principles, and mechanisms.",
    ])
    return lines


def build():
    on = _records()
    action = [r for r in on if r["id"].startswith("STOW-ACT-")]
    prose = [r for r in on if r["id"].startswith("STOW-PRO-")]
    parts = [HEADER, ROUTER, "", "## Action shaping", ""]
    for record in action:
        parts.append(_bullet(record))
    parts.extend([""] + _descriptive_digest(prose) + [""])
    return ("\n".join(parts).rstrip("\n") + "\n",
            len(action), len(DESCRIPTIVE_GROUPS))


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    text, n_action, n_leaves = build()
    if "--check" in argv:
        current = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else None
        if current != text:
            print("always-on.md is STALE relative to the registry -- regenerate")
            return 1
        print("always-on.md is current (%d action + %d descriptive leaves)" %
              (n_action, n_leaves))
        return 0
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print("wrote %s (%d action + %d descriptive leaves)"
          % (OUT, n_action, n_leaves))
    return 0


if __name__ == "__main__":
    sys.exit(main())
