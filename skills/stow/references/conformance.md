# Conformance guidance (no overclaim)

This reference governs how STOW may describe its own output against the underlying controlled-technical writing standard. It is application guidance, not a restatement of any rule. For the normative text of a cited rule, open its `corpus_ref`.

STOW gives **guided** alignment, never certification. The strict, fully conformant profile is **locked and unavailable in v0.1**: the controlled dictionary, the approved terminology set, the official directives, and the full validation suite do not ship. Because those inputs are absent, STOW must never state that its output fully conforms to the controlled-technical writing standard on the basis of the rule set alone. The correct phrasing is that output is *guided by the controlled-technical rules*, with the unavailable checks named.

Each group below lists: the observable **Trigger**, the output **Region** it applies to, how STOW **Checks** it (or why the check is unavailable), and a `corpus_ref` **Reference** for the full rule text.

## 1. Conformance-claim guard

- **Trigger:** the assistant is about to label, certify, or otherwise describe output as meeting the controlled-technical writing standard, or a user asks whether output conforms.
- **Region:** assistant statements about output status, not the prose itself.
- **Check:** STOW asserts only guided alignment. It emits no conformance certificate. Any claim of full or strict conformance is downgraded to *guided, partial*, because the strict profile is locked in v0.1. STOW names which checks ran and which are unavailable instead of making a blanket claim.
- **Reference:** the profile-gated rule set as a whole; representative see corpus/words/stow-wrd-001.md.

## 2. Dictionary-dependent checks: reported UNAVAILABLE

- **Trigger:** prose under an active controlled-technical profile whose evaluation would require looking a word up in the controlled dictionary, confirming its approved sense, part of speech, or inflection, testing technical-noun or technical-verb category membership, checking approved connectors, company or industry terminology, phrasal-verb admissibility, or false-friend status.
- **Region:** all-prose, including procedural and descriptive prose; excludes code, structured data, quoted text, and identifiers.
- **Check:** unavailable in v0.1. Without the shipped dictionary, approved terminology, and directives, STOW cannot confirm these rules are satisfied. It marks each as *not checked: dictionary unavailable* and never counts them toward a conformance claim.
- **Reference:** see corpus/words/stow-wrd-001.md, corpus/words/stow-wrd-005.md, corpus/verbs/stow-vrb-001.md, corpus/sentences/stow-sen-004.md, corpus/style/stow-sty-002.md, corpus/style/stow-sty-003.md, corpus/general/stow-gen-005.md.

## 3. Structural and mechanical checks: AVAILABLE (guided)

- **Trigger:** surface features STOW can read directly: words per sentence, sentences per paragraph, length of a multi-word noun, presence of a semicolon, presence of a contraction or an omitted word, and the token-counting mechanics those measures rely on.
- **Region:** procedural, descriptive, and all-prose regions; excludes code, structured data, quoted text, and identifiers.
- **Check:** STOW measures these deterministically over the rendered prose and flags any item outside the bound the rule sets. Results support a guided assessment only. Passing them does not establish conformance, because the dictionary-dependent rules in Group 2 stay unverified.
- **Reference:** see corpus/procedures/stow-prc-001.md, corpus/procedures/stow-prc-005.md, corpus/descriptions/stow-dsc-003.md, corpus/descriptions/stow-dsc-006.md, corpus/multiword-nouns/stow-mwn-001.md, corpus/punctuation/stow-pct-001.md, corpus/punctuation/stow-pct-004.md, corpus/punctuation/stow-pct-006.md, corpus/sentences/stow-sen-002.md.

## 4. Grammar and construction checks: PARTIAL (best-effort, guided)

- **Trigger:** procedural or descriptive prose where clause shape can be read from the text: whether an instruction opens in the imperative, whether a sentence carries more than one instruction, whether a leading condition is separated by a comma, which verb tense and voice appear, and whether an action is expressed as a nominalization.
- **Region:** procedural and descriptive prose.
- **Check:** STOW inspects sentence structure and flags likely deviations. These are judgment calls, not certified parses, so STOW reports them as guidance rather than pass or fail.
- **Reference:** see corpus/procedures/stow-prc-002.md, corpus/procedures/stow-prc-003.md, corpus/procedures/stow-prc-004.md, corpus/verbs/stow-vrb-002.md, corpus/verbs/stow-vrb-006.md.

## 5. Safety checks: ALWAYS ACTIVE (system precedence)

- **Trigger:** the response contains a safety instruction, warning, caution, or hazard notice, whether or not a controlled-technical profile is active.
- **Region:** safety-prose.
- **Check:** STOW reviews the safety item for a risk-level label, a command-or-condition opening, and a stated consequence. These run at system precedence and outrank the profile, but they still yield guided review, not certification.
- **Reference:** see corpus/safety/stow-saf-001.md, corpus/safety/stow-saf-002.md, corpus/safety/stow-saf-003.md.

## Bottom line

Absent the shipped dictionary, terminology, directives, and full validation, STOW must not claim that any output fully conforms to the controlled-technical writing standard. Report structural and safety checks as *guided*, report dictionary-dependent checks as *unavailable*, and name both when describing the result.
