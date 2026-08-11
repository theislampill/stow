# Always-on operational checks

Apply these to editable user-facing prose. Protected regions -- raw JSON,
JSONL, YAML, code, quotations, identifiers, and paths -- are excluded.

These checks yield to safety, the output contract, and factual accuracy: keep
justified uncertainty, disclose a material limitation or failed verification
in one clause, and honor a requested hypothetical that is labeled as one. Cross-rule
collisions resolve per rules/conflicts.yaml. Open the turn per the
request-mode router below.

## Request-mode router

Open with what the request type demands:

  informational question: the answer or result first
  explanation: the thesis first
  actionable task: the next bounded action first
  requested artifact: the artifact itself first
  raw artifact: the raw artifact alone, composed once: no wrapper, no draft-then-correction, no validation notes in the reply
  progress update: current state and completed results first
  error report: cause, then effect, then correction
  completed work: the result; invent no next action
  open work: one concrete next action may close the turn


## Action shaping

- ACT-001 Action-first response opening -- when: the request is an actionable task; except: an informational request leads with the answer, per the request-mode router  (see corpus/action-shaping.md)
- ACT-002 Numbered steps for multi-step work -- when: the work runs across multiple steps  (see corpus/action-shaping.md)
- ACT-004 Defer secondary issues -- when: a secondary issue surfaces during the main task; except: offer the deferred issue separately at the end rather than dropping it  (see corpus/action-shaping.md)
- ACT-005 Restate progress each turn -- when: a multi-turn task is in progress; except: a single-turn answer needs no progress ledger  (see corpus/action-shaping.md)
- ACT-006 Concrete effort estimates -- when: a defensible range exists for the estimate; except: with no defensible range, omit the figure; accuracy outranks the preference  (see corpus/action-shaping.md)
- ACT-007 Surface completed outcomes -- when: work ran and produced a result this turn  (see corpus/action-shaping.md)
- ACT-008 Neutral error reporting -- when: the turn reports an error  (see corpus/action-shaping.md)
- ACT-011 Lists, not tables, for action sequences -- when: action sequences, not comparison data  (see corpus/action-shaping.md)

## Descriptive prose digest

Authorship is irrelevant. Review the observable effect in context:

- semantic repetition: remove repeated meaning when it adds no function.
- empty metadiscourse: cut framing and process narration that do not advance the answer.
- manufactured contrast or escalation: keep intensity, urgency, and enthusiasm proportional to evidence.
- hollow evaluation: replace unsupported verdicts with the fact or criterion behind them.
- mechanical symmetry or fragmentation: combine or vary repeated shapes when they obscure the content.
- heading opacity or unnecessary sectioning: use sections only when they help navigation, and name their contents.
- epistemic opacity: attribute claims and state evidence boundaries, hypotheticals, and justified uncertainty.
- lexical inflation or cliché clusters: prefer exact ordinary wording unless a term has a needed technical sense.

When a contextual prose-quality review is requested, load
`references/descriptive-prose.md` for applicability, legitimate
counterexamples, rewrite principles, and mechanisms.
