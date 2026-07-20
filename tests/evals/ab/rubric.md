# Enabled-versus-disabled evaluation: rubric and computation spec

Frozen before the first scored round; any later edit is a version bump
recorded in the governed run record, and both rounds of a comparison use one
version. Evaluators score blind (case, rep) pairs labeled Output X and
Output Y; the arm mapping is randomized per pair with a recorded seed and
lives only in the run record. Evaluators score the rubric only; they never
infer or report which system produced an output, and no score field exists
for that guess. Bundles contain final output text only.

## Dimensions (0 to 4; 1 and 3 interpolate)

| Id | Dimension | 0 anchor | 2 anchor | 4 anchor |
|---|---|---|---|---|
| R1 | Output-contract compliance | Ignores an explicit contract term (fence on raw, wrapper, missing artifact) | Honors the main contract with lapses (extra commentary, partial shape) | Every explicit and implied contract term honored exactly |
| R2 | Answer/result/action placement | The needed thing never leads; reader digs | Leads eventually after preamble or detour | The answer, result, or next action is the first substantive content |
| R3 | Actionability | Reader cannot act without re-deriving steps | Actionable with gaps (unordered, missing verification) | Bounded, ordered, verifiable actions ready to execute |
| R4 | Clarity | Confusing structure; reader rereads | Understandable with effort | Scannable, precise, no rereads needed |
| R5 | Concision without omitted requirements | Bloated or truncates required content | Some filler or minor omissions | Everything required, nothing else |
| R6 | Prose integrity | Multiple banned patterns (filler, synthetic voice, fabricated flavor) | Occasional lapses | Clean under the always-on prose checks |
| R7 | Factual restraint and uncertainty | Invents facts or flattens real doubt into confidence | Mostly restrained; uncertainty present but muddled | States only supportable facts; justified uncertainty kept, once, with its reason |
| R8 | Terminology consistency | Renames the same thing repeatedly | Minor drift | One term per concept throughout |
| R9 | Profile correctness | Wrong register for the artifact class (chatty procedure, controlled casual reply) | Mostly right with slips | The applicable profile's discipline is visible and correct |
| R10 | Protected-region fidelity | Alters an identifier, quote, or literal | Preserves them with cosmetic drift nearby | Byte-exact literals, quotes, and identifiers |
| R11 | Structured/schema validity | Does not parse | Parses with contract violations | Parses and validates clean |
| R12 | Meta-code executability | A fresh executor could not act on it | Actionable with guesswork | A cold reader can execute or verify it as-is |
| R13 | Naturalness | Robotic, chopped, or template-stiff | Serviceable but mechanical in places | Reads like a competent human wrote it plainly |
| R14 | Absence of self-betrayal | Violates rules the output itself states or teaches | Minor tension with its own guidance | Fully consistent with the rules it carries |

Dims scored by two roles (R4, R6, R8) enter as the mean of the two.

## Applicability matrix (binding; no ad-hoc not-applicable calls)

- R11: AB-09, AB-10, AB-11, AB-17, AB-18, AB-19, AB-20 only.
- R12: AB-17, AB-18, AB-19, AB-20 only.
- R10: AB-15, AB-16 only.
- R9: AB-13, AB-14 and the raw cases AB-09, AB-10, AB-11, AB-20 (contract shape).
- R3: not applicable on AB-01, AB-02, AB-12.
- All other dims apply to all cases. Not-applicable dims leave the
  denominator. A score returned for a not-applicable dim is discarded; a
  missing applicable score triggers one batch re-query, after which the rep
  is invalid and re-run.

## Roles

- A cold-reader/efficacy: R2, R3, R4, R5, R8.
- B adversarial rule and conflict: R1, R6, R7, R9, R10, R14, R8; flags
  judgment invariants with quoted evidence.
- C weak-executor/meta-code: R11, R12.
- D anti-slop/naturalness: R4, R6, R13.
Every score of 1 or 0 requires quoted evidence from the output.

## Critical invariants (pass/fail, never averaged)

Mechanical (ground truth from validators/runner): raw artifact parses;
no wrapper on requested raw output; protected literals byte-unchanged;
AB-07 completeness; schema validity; conformance-overclaim phrase list;
validate-repair loop observed (stow arm, from telemetry, graded unblinded by
the runner). Judgment (union with mechanical failures; mechanical green
never clears a judgment flag): no fabricated fact or attribution (role B:
verbatim quote plus the contradicting ground truth, else it downgrades to an
R7 score); safety completeness on AB-13/AB-14 (roles B and C independently;
fails only on a named missing critical hazard class with justification;
disagreement goes to owner adjudication in the run record).

## Computation spec (normative)

Strata: G = AB-01..AB-16; K = AB-17..AB-20 (reported as per-arm validator
pass-rates, never folded into G); H = the sealed hold-outs (final round only,
non-gating, sign-compared).
Run r = (case c, arm a, rep k); S(r) = mean of applicable dim scores;
m(c, a) = median over reps (two valid reps: mean; fewer: re-run);
D(c) = m(c, stow) minus m(c, base);
D_d(c) = median-over-reps dim delta for applicable (c, d).
Primary gate (G, unweighted): pass when median D(c) > 0, or when
median D(c) = 0 and mean D(c) > 0 and wins exceed losses
(wins = cases with D(c) > 0; ties count neither side).
Regression gate: for every protected dim d in {R1, R7, R10} and applicable
case, D_d(c) >= -0.5; zero stow-arm critical-invariant failures on
raw/protected/safety cases.
Material improvement: median applicable-G D_3(c) >= +0.5 and
median applicable-G D_6(c) >= +0.5; meta-code executability is mechanical:
stow schema-valid final outputs >= 10 of 12 K-runs and strictly more than
the base count.
Any stow-arm critical failure fails the package gate unless traced to a
harness error, documented, and re-run once with the original retained.

## Reproducibility and limits

Committed: this rubric, prompts.yaml, the runner, the aggregation code.
Archived in the run record: raw outputs, transcripts, mappings, seeds,
per-evaluator scores, telemetry. The procedure reproduces; exact numbers
depend on the model snapshot (ids and dates recorded). Evaluator and
generator share a model family, so deltas are the unit of inference.
Medians, deltas, and win/tie/loss counts are reported descriptively with no
significance claims. Blinding is real for prose cases and limited for
schema-bearing outputs, whose provenance is structurally recognizable; that
is why every schema and format verdict comes from mechanical validators.
