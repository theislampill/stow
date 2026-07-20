# Conformance guidance (no overclaim)

This reference governs how STOW may describe its own output against the underlying controlled-technical writing standard. It is application guidance, not a restatement of any rule. For the normative text of a cited rule, open its `corpus_ref`.

STOW gives **guided** alignment, never certification. The strict, fully conformant profile is **locked and unavailable in v0.1**: the controlled dictionary, the approved terminology set, the official directives, and the full validation suite do not ship. Because those inputs are absent, STOW must never state that its output fully conforms to the controlled-technical writing standard on the basis of the rule set alone. The correct phrasing is that output is *guided by the controlled-technical rules*, with the unavailable checks named.

Each group below lists: the observable **Trigger**, the output **Region** it applies to, how STOW **Checks** it (or why the check is unavailable), and a `corpus_ref` **Reference** for the full rule text.

## 1. Conformance-claim guard

- **Trigger:** the assistant is about to label, certify, or otherwise describe output as meeting the controlled-technical writing standard, or a user asks whether output conforms.
- **Region:** assistant statements about output status, not the prose itself.
- **Check:** STOW asserts only guided alignment. It emits no conformance certificate. Any claim of full or strict conformance is downgraded to *guided, partial*, because the strict profile is locked in v0.1. STOW names which checks ran and which are unavailable instead of making a blanket claim.
- **Reference:** the profile-gated rule set as a whole; representative see corpus/words/selection.md#STOW-WRD-001.

## 2. Dictionary-dependent checks: reported UNAVAILABLE

- **Trigger:** prose under an active controlled-technical profile whose evaluation would require looking a word up in the controlled dictionary, confirming its approved sense, part of speech, or inflection, testing technical-noun or technical-verb category membership, checking approved connectors, company or industry terminology, phrasal-verb admissibility, or false-friend status.
- **Region:** all-prose, including procedural and descriptive prose; excludes code, structured data, quoted text, and identifiers.
- **Check:** unavailable in v0.1. Without the shipped dictionary, approved terminology, and directives, STOW cannot confirm these rules are satisfied. It marks each as *not checked: dictionary unavailable* and never counts them toward a conformance claim.
- **Reference:** see corpus/words/selection.md#STOW-WRD-001, corpus/words/approved-tables.md#STOW-WRD-005, corpus/verbs/technical-verbs.md#STOW-VRB-001, corpus/sentences.md#STOW-SEN-004, corpus/style/consistency.md#STOW-STY-002, corpus/style/economy.md#STOW-STY-003, corpus/general-practice.md#STOW-GEN-005.

## 3. Structural and mechanical checks: AVAILABLE (guided)

- **Trigger:** surface features STOW can read directly: words per sentence, sentences per paragraph, length of a multi-word noun, presence of a semicolon, presence of a contraction or an omitted word, and the token-counting mechanics those measures rely on.
- **Region:** procedural, descriptive, and all-prose regions; excludes code, structured data, quoted text, and identifiers.
- **Check:** STOW measures these deterministically over the rendered prose and flags any item outside the bound the rule sets. Results support a guided assessment only. Passing them does not establish conformance, because the dictionary-dependent rules in Group 2 stay unverified.
- **Reference:** see corpus/procedures.md#STOW-PRC-001, corpus/procedures.md#STOW-PRC-005, corpus/descriptions.md#STOW-DSC-003, corpus/descriptions.md#STOW-DSC-006, corpus/multiword-nouns.md#STOW-MWN-001, corpus/punctuation.md#STOW-PCT-001, corpus/punctuation.md#STOW-PCT-004, corpus/punctuation.md#STOW-PCT-006, corpus/sentences.md#STOW-SEN-002.

## 4. Grammar and construction checks: PARTIAL (best-effort, guided)

- **Trigger:** procedural or descriptive prose where clause shape can be read from the text: whether an instruction opens in the imperative, whether a sentence carries more than one instruction, whether a leading condition is separated by a comma, which verb tense and voice appear, and whether an action is expressed as a nominalization.
- **Region:** procedural and descriptive prose.
- **Check:** STOW inspects sentence structure and flags likely deviations. These are judgment calls, not certified parses, so STOW reports them as guidance rather than pass or fail.
- **Reference:** see corpus/procedures.md#STOW-PRC-002, corpus/procedures.md#STOW-PRC-003, corpus/procedures.md#STOW-PRC-004, corpus/verbs/technical-verbs.md#STOW-VRB-002, corpus/verbs/verb-forms.md#STOW-VRB-006.

## 5. Safety checks: ALWAYS ACTIVE (system precedence)

- **Trigger:** the response contains a safety instruction, warning, caution, or hazard notice, whether or not a controlled-technical profile is active.
- **Region:** safety-prose.
- **Check:** STOW reviews the safety item for a risk-level label, a command-or-condition opening, and a stated consequence. These run at system precedence and outrank the profile, but they still yield guided review, not certification.
- **Reference:** see corpus/safety.md#STOW-SAF-001, corpus/safety.md#STOW-SAF-002, corpus/safety.md#STOW-SAF-003.

## Bottom line

Absent the shipped dictionary, terminology, directives, and full validation, STOW must not claim that any output fully conforms to the controlled-technical writing standard. Report structural and safety checks as *guided*, report dictionary-dependent checks as *unavailable*, and name both when describing the result.
