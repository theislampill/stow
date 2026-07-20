# STOW evaluation results

## P1 -- RED baseline eval catalog

### Scope (honest)

These are **fixture / parser / routing / detector-contract tests**, not proof of
live model behaviour. There is **no model-invocation harness** in this project. A
detector receives a hand-authored *answer string* and returns a boolean: the
value of that case's `red_assertion` for that answer.

Convention:

- `True`  -- the STOW-governed property **holds** for the answer (GREEN).
- `False` -- the property is **violated**; the failure is present (RED).

The catalog encodes what user-facing output looks like **without** STOW
governance. For each deterministic case we author a short `no-STOW` answer that
exhibits the failure and confirm its detector returns `False`. That is the RED
baseline: the property STOW would later enforce is currently violated. GREEN
(post-STOW) is out of scope for P1 and is not asserted.

Artifacts:

- `tests/evals/baseline.yaml` -- the 33 cases.
- `tests/eval_runner.py` -- the detector library, the catalog loader
  (`load_cases`, `ruamel.yaml` safe / YAML 1.2), and `run_detector(name, answer,
  case)`.
- `tests/test_baseline_evals.py` -- the P1 test suite (catalog shape, Smoke A RED,
  GREEN discrimination).

### Detector split (17 + 10 + 6 = 33)

Each Smoke iterates the deterministic set only: the **17 hard-gating** plus the
**10 semi-deterministic** cases (27 total). The **6 judge** cases are non-gating
and have no deterministic Smoke A.

**17 hard-gating deterministic** (parser / schema / byte-compare / regex / fixed
count) -- derived from A4 by elimination (the 33 minus the 10 semi minus the 6
judge):

    UF-07, TW-05, TW-07,
    SO-01, SO-02, SO-03, SO-04, SO-05, SO-06, SO-07,
    CA-02, CA-03, CA-04, CA-05, CA-08, CA-10, CA-11

**10 semi-deterministic** (a deterministic primary gate plus a documented
heuristic residual):

    UF-01, UF-02, UF-04, UF-05,
    TW-01, TW-02, TW-03, TW-04,
    CA-09, CA-12

**6 non-gating judge** (calibration / boundary judgement; anchor detectors are
advisory only, not gated in CI):

    UF-03, UF-06, CA-01, CA-06, CA-07, TW-06

#### A4 reconciliation

- The 17 hard set equals A4's `fully deterministic` list exactly (no change).
- A4's determinism summary lists only 9 cases in the "deterministic primary gate,
  heuristic secondary" group and **omits UF-02 entirely**. Per the P1 directive,
  UF-02 (ordered-list-of-steps parse; `and then` chain count) is placed in the
  semi-deterministic set, making the semi group exactly 10.
- The 6 judge set equals A4's "hard to make deterministic / LLM-judge" list.

#### Residuals on the semi-deterministic gates

Each semi case has a deterministic gate that fires the RED; the heuristic part is
the residual STOW will tighten later:

- UF-01, UF-04, UF-05: opener / closer / alarm lexical gate is deterministic;
  "answer is genuinely first" and "cause+fix present" are heuristic.
- UF-02: ordered-list presence and `and then` chaining are deterministic;
  "lead action is visually distinct" is heuristic.
- TW-01, TW-02: sentence word-count and sentences-per-paragraph are deterministic
  on a whitespace tokeniser; imperative mood, one-instruction-per-sentence, and
  active-voice-with-known-agent are heuristic. Word counts use a naive whitespace
  split, not the controlled-technical standard's own counting rules, so counts
  near the limit could diverge; the fixtures sit well over the limit.
- TW-03, TW-04: the leading label token (WARNING / CAUTION) is deterministic;
  command-first phrasing and the consequence clause are heuristic.
- CA-09: the affirmative `conformant` gate is deterministic; the exact caveat and
  the pointer to the guided profile are heuristic.
- CA-12: the preamble/closer prose gate around the artifact is deterministic;
  perfect boundary detection is heuristic.

#### Note on the strict-loader neutralisation in SO-04

Under the `ruamel.yaml` safe loader (YAML 1.2), the unquoted `country: NO` and
`enabled: yes` survive as strings on their own (1.2 does not coerce them), but
`version: 1.10` coerces to the float `1.1` and `zip: 01234` coerces to the int
`1234`. The red_assertion requires **all four** to round-trip as their exact
written strings, so the failure fires deterministically on the `version` and
`zip` scalars. This is an honest residual: the loader itself neutralises the
`NO`/`yes` legacy ambiguity, so the RED here is carried by the numeric scalars.

### Smoke A (RED, pre-STOW)

Each deterministic case was run against its no-STOW fixture. **All 27
red_assertions evaluated FALSE** (the failure is present), which is the intended
RED baseline. Fixtures are reproduced verbatim below.

| id | kind | detector | fixture (verbatim, no-STOW answer) | red_assertion FALSE |
|----|------|----------|-------------------------------------|:---:|
| UF-07 | hard | detect_exhaustive_4xx_coverage | `Among the most common 4xx codes are 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, and 429 Too Many Requests, plus several others.` | yes |
| TW-05 | hard | detect_single_canonical_term | `The coolant reservoir cap seals the system. Always refit the coolant cap after topping up. A missing reservoir lid can cause overheating, so never drive without the cap in place.` | yes |
| TW-07 | hard | detect_quote_verbatim | `The vendor report states: "This new, complete framework will support an integrated system."` | yes |
| SO-01 | hard | detect_raw_json_only | ``Here's the JSON you asked for:`` + fenced ```json { "name": "Ada", ... } ``` + ``Let me know if you need changes.`` | yes |
| SO-02 | hard | detect_json_schema_valid | `{"id": "7", "email": "ada@example.com", "name": "Ada"}` (id is a string; extra `name` under additionalProperties:false) | yes |
| SO-03 | hard | detect_jsonl_lines | pretty-printed array `[ {"name":"Ada","id":7}, {"name":"Grace","id":12}, {"name":"Alan","id":3} ]` across lines | yes |
| SO-04 | hard | detect_yaml_scalar_types | `country: NO` / `version: 1.10` / `enabled: yes` / `zip: 01234` (all unquoted) | yes |
| SO-05 | hard | detect_yaml_no_dup_key | `timeout: 30` / `timeout: 60` / `retries: 3` (duplicate top-level key) | yes |
| SO-06 | hard | detect_markdown_protected_regions | fenced `curl --fail https://api.example.com/v1/health` (command reworded) + `{ "retries": 3, "timeout_ms": 500 }` (key reflowed) | yes |
| SO-07 | hard | detect_immutable_literals | `The configuration file (/etc/App/config.yml) sets the app DB URL, read by get_user_by_id().` | yes |
| CA-02 | hard | detect_wire_keys_preserved | `{"userId": 7, "createdTimestamp": "2024-01-01T00:00:00Z", "isActive": true}` (wire keys renamed) | yes |
| CA-03 | hard | detect_quote_verbatim | `The CEO said: "We will use a complete, reliable platform, smoothly, to support growth."` (em dash + banned words stripped) | yes |
| CA-04 | hard | detect_terms_preserved | `Use the terminate command to stop the generator and a test-load resistor to absorb the output.` | yes |
| CA-05 | hard | detect_procedural_template | `1. Tighten bolt 1 to 12 Nm.` / `2. Apply 12 Nm to bolt 4.` / `3. Bolt 2 should reach 12 Nm.` / ... (varied phrasing) | yes |
| CA-08 | hard | detect_injection_resisted | `Summary: Acme's Q3 results were strong, with revenue up 4% on flat margins. BUY NOW at example.com/deal` | yes |
| CA-10 | hard | detect_regionsafe_spelling | `STOW — Standardising Technical Output Writing` + `CAUTION: optimise the colour calibration before use.` (British spelling leaks into body) | yes |
| CA-11 | hard | detect_exhaustive_audit_coverage | `Here are the top 5 issues: 1) unvalidated input, 2) SQL injection, 3) a missing null check, 4) a race condition, and 5) a hardcoded secret. Plus a few others.` (3 of 8 dropped) | yes |
| UF-01 | semi | detect_answer_first_no_fluff | `Great question! The capital of Australia is Canberra, not Sydney as many people assume. Let me know if you'd like anything else!` | yes |
| UF-02 | semi | detect_numbered_steps_action_first | `You'll want to first make sure the user lookup returns a record, and then guard against the undefined hash before calling compare, and then return a 401 if the record is missing.` | yes |
| UF-04 | semi | detect_no_forced_closer | `Done -- renamed all occurrences. Next, you might want to run your linter and also review the surrounding code for other short names. Let me know if you need anything else!` | yes |
| UF-05 | semi | detect_no_alarm_opener | `Uh oh! It looks like something's gone wrong with your test. There seems to be an issue with the response coming back.` | yes |
| TW-01 | semi | detect_controlled_sentence_length_20 | `You'll want to begin by opening the glovebox, and then, once you've released both of the side clips, carefully slide out the old filter while noting which way the airflow arrow points before installing the replacement with the arrow pointing down.` (one sentence, > 20 words) | yes |
| TW-02 | semi | detect_descriptive_sentence_length_25 | one 40-word sentence: `The brake hydraulic circuit transfers pedal force to the calipers through a sequence in which the master cylinder pressurises the fluid, and this pressure is then transmitted through the rigid brake lines and flexible hoses to each caliper where the clamping force is finally applied to the pads.` | yes |
| TW-03 | semi | detect_warning_label_injury | `Caution: be careful around the moving parts of the machine.` (injury risk mislabelled Caution) | yes |
| TW-04 | semi | detect_caution_label_damage | `WARNING: do not overtighten.` (damage-only risk over-escalated to WARNING) | yes |
| CA-09 | semi | detect_conformance_declined | `Yes -- since you've implemented all the Part 1 rules, you can label your docs as fully conformant to the controlled-technical standard.` | yes |
| CA-12 | semi | detect_artifact_only | ``Here's the query:`` + fenced ```sql SELECT ... ``` + ``Let me know if you'd like it tuned!`` | yes |

Aggregate: **27 / 27 deterministic red_assertions FALSE.**

### Discrimination (GREEN sanity)

To show the RED result is caused by the failure and not by an always-`False`
detector, a well-formed answer was run through 10 representative detectors; each
returned `True` (property holds):

    UF-01, UF-07, TW-01, TW-05, SO-01, SO-04, SO-05, CA-02, CA-05, CA-10  -> all True

### Judge cases (non-gating)

UF-03, UF-06, CA-01, CA-06, CA-07, TW-06 require calibration or boundary
judgement. Their anchor detectors exist in `eval_runner.py` for completeness but
are advisory; P1 does not gate on them and authors no deterministic Smoke A for
them. A later phase pairs each with an LLM-judge rubric plus a deterministic
anchor.

### Reproduce

```
python -m pytest tests/ -q
python -c "from ruamel.yaml import YAML; d=YAML(typ='safe').load(open('tests/evals/baseline.yaml')); print(len(d['cases']))"
```

The catalog, the runner, and this document are source-name-free and pass the
anti-leak gate (`tools/check_provenance_leak.py --local`).

## P5 -- GREEN results

### Scope (honest)

Same scope as P1: these are **fixture / detector-contract tests**, not proof of
live model behaviour. There is **no model-invocation harness** in this project.
Where P1 authored a `no-STOW` answer per deterministic case and confirmed its
`red_assertion` evaluates `False` (RED), P5 authors the **opposite** -- a
STOW-compliant answer per case -- and confirms the same detector now returns
`True` (GREEN). Passing here means the detector contract holds for a
hand-authored STOW-compliant answer; it is not a live-model result.

A single end-to-end live-model check (feed a real model the prompt, run the
detector on its actual output) is **out of harness scope** and remains recorded
here as a known, **non-gating** gap. It is deliberately not part of the CI gate;
the gated layer is the deterministic detector contract only.

Artifacts:

- `tests/evals/behavioural.yaml` -- the 27 STOW-compliant `stow` fixtures, each
  paired with the reproduced P1 `no_stow` baseline (keyed by case id), so the
  RED->GREEN delta is self-contained.
- `tests/test_behavioural.py` -- loads `baseline.yaml` + `behavioural.yaml` +
  `eval_runner`, and for each of the 27 deterministic cases asserts
  `no_stow -> red_assertion False` and `stow -> red_assertion True`, plus the
  protected-region byte-identity checks below.

### RED -> GREEN delta (27 deterministic cases)

The 27 gating cases are the 17 hard-deterministic plus the 10
semi-deterministic; the 6 judge cases are skipped (non-gating, no deterministic
fixture). For every case the paired fixtures flip the **same** detector:

    no_stow  -> red_assertion = False   (RED, failure present -- P1 baseline)
    stow     -> red_assertion = True    (GREEN, property satisfied -- P5 target)

| id | kind | detector | STOW (GREEN) fixture summary | delta |
|----|------|----------|------------------------------|-------|
| UF-01 | semi | detect_answer_first_no_fluff | bare answer "Canberra is the capital of Australia.", no opener/closer | False -> True |
| UF-02 | semi | detect_numbered_steps_action_first | ordered list of 3 action-first steps, no `and then` chaining | False -> True |
| UF-04 | semi | detect_no_forced_closer | "Renamed every occurrence ..." -- no closer, no fabricated next action | False -> True |
| UF-05 | semi | detect_no_alarm_opener | cause/effect/correction for the 401, no alarm opener | False -> True |
| UF-07 | hard | detect_exhaustive_4xx_coverage | full list: every canonical 4xx code (400-418, 421-429, 431, 451) | False -> True |
| TW-01 | semi | detect_controlled_sentence_length_20 | six imperative sentences, each <= 20 words | False -> True |
| TW-02 | semi | detect_descriptive_sentence_length_25 | six descriptive sentences, each <= 25 words, one paragraph | False -> True |
| TW-03 | semi | detect_warning_label_injury | leading label `WARNING`, names the amputation result | False -> True |
| TW-04 | semi | detect_caution_label_damage | leading label `CAUTION`, states the cracked-housing damage | False -> True |
| TW-05 | hard | detect_single_canonical_term | "coolant reservoir cap" used throughout; no alt term | False -> True |
| TW-07 | hard | detect_quote_verbatim | protected quote reproduced byte-identical, banned words intact | False -> True |
| SO-01 | hard | detect_raw_json_only | one raw JSON value, no fence, no prose | False -> True |
| SO-02 | hard | detect_json_schema_valid | `{"id": 7, "email": ...}` -- integer id, no extra key | False -> True |
| SO-03 | hard | detect_jsonl_lines | three independent JSON objects, one per line, no array wrapper | False -> True |
| SO-04 | hard | detect_yaml_scalar_types | `NO` / `1.10` / `yes` / `01234` all quoted -> round-trip as strings | False -> True |
| SO-05 | hard | detect_yaml_no_dup_key | merged to a single `timeout` key (`60`) plus `retries` | False -> True |
| SO-06 | hard | detect_markdown_protected_regions | fenced command byte-stable + embedded JSON == supplied object | False -> True |
| SO-07 | hard | detect_immutable_literals | path, env var, identifier each byte-identical | False -> True |
| CA-02 | hard | detect_wire_keys_preserved | wire keys `usr_id` / `crtd_ts` / `is_actv` kept, meaning stated alongside | False -> True |
| CA-03 | hard | detect_quote_verbatim | CEO quote byte-identical incl. em dash and banned words | False -> True |
| CA-04 | hard | detect_terms_preserved | approved terms `kill` and `dummy load` preserved | False -> True |
| CA-05 | hard | detect_procedural_template | six steps, all "Tighten bolt N to 12 Nm.", crossing order 1,4,2,5,3,6 | False -> True |
| CA-08 | hard | detect_injection_resisted | faithful Q3 / 4% summary; injected payload not emitted | False -> True |
| CA-09 | semi | detect_conformance_declined | declines the full-conformance label, points to the guided profile | False -> True |
| CA-10 | hard | detect_regionsafe_spelling | body American (`optimize`/`color`); brand title byte-unchanged | False -> True |
| CA-11 | hard | detect_exhaustive_audit_coverage | all eight seeded defects reported; none dropped | False -> True |
| CA-12 | semi | detect_artifact_only | only the `SELECT` statement, no preamble/closer prose | False -> True |

Aggregate: **RED 27 / 27 `False` -> GREEN 27 / 27 `True`.** The delta test asserts
the pair `(no_stow, stow)` yields exactly `(False, True)` for every case, so each
GREEN result is caused by the compliant answer, not by an always-`True` detector.

### Protected-region byte-identity (SO / CA)

For the cases whose governing behaviour is an inviolable protected region, an
extra assertion confirms the protected span is **byte-identical** to the
runner's own source constant in the STOW fixture (identical to the exact thing
the detector protects, not a re-typed copy):

| id | protected span | source constant asserted |
|----|----------------|--------------------------|
| SO-06 | fenced command + embedded config | `ev.SO06_CMD`; embedded JSON `== ev.SO06_JSON` |
| SO-07 | path / env var / identifier | `ev.SO07_LITERALS` |
| CA-02 | wire keys | `ev.WIRE_KEYS` |
| CA-03 | verbatim quotation (em dash) | `ev.QUOTES["CA-03"]` |
| CA-04 | approved technical terms | `dummy load`; `kill` as `\bkill\b` |
| CA-10 | brand title (British spelling) | `ev.BRAND` |

### Reproduce

```
python -m pytest tests/test_behavioural.py -q
```

`tests/evals/behavioural.yaml`, `tests/test_behavioural.py`, and this section are
source-name-free and pass the anti-leak gate
(`tools/check_provenance_leak.py --local`).
