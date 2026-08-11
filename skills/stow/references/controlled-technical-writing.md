# Controlled-technical writing profile: application reference

This reference is compressed application guidance for the controlled-technical
writing profile: **when and where** each rule fires, **which output region** it
governs, **how STOW checks it**, and a link to the corpus file that holds the
full normative text. It does not restate the rules themselves: read the linked
corpus file for the wording that governs.

**Guided, not conformant.** This profile is *guided*. STOW applies the checks
below as best-effort shaping of prose. Passing them is not a claim of full
conformance to any controlled-language standard, and it does not certify the
output against the external standard the rules trace to. Treat a clean pass as
*shaped toward the controlled-technical rules*, not *verified compliant*.

**Activation gate (shared by every rule here).** These are profile-precedence
rules. They apply only when a controlled-technical writing profile is active and
the response contains prose. They govern prose only and skip the protected
regions: code, structured data, quoted text, and identifiers. Unless a row says
otherwise, the region is *all prose*; the two exceptions are called out
explicitly.

**How to read each entry.** Every row names the *observable trigger* (the output
feature that invokes the check), the *region*, *how STOW checks it* (the
enforcement kind plus the named validator, with any numeric limit), and the
*corpus_ref* for the governing text. The controlled-technical rules are grouped
below as WRD (words), MWN (multi-word nouns), VRB (verbs, voice, tense), SEN
(sentences, lists, articles), STY (writing-practice consistency), and GEN
(general recommendations).

## WRD: words

| Rule | Observable trigger | Region | How STOW checks | Full text |
| --- | --- | --- | --- | --- |
| WRD-001 | A content word appears, including a proposed technical noun or technical verb | all prose | semantic review · admit a technical term only under a defined category and external terminology authority; prefer an approved dictionary verb when one exists; the dictionary lookup is not bundled | see corpus/words/selection.md#STOW-WRD-001 |
| WRD-002 | An approved word is used in a part of speech or inflected form, including a past participle used as an adjective | all prose | contextual review · use only the dictionary-specified part of speech and listed forms; the named parser is planned, not callable | see corpus/words/selection.md#STOW-WRD-002 |
| WRD-003 | An approved word carries a particular sense | all prose | semantic-review · `approved-sense-only` | see corpus/words/selection.md#STOW-WRD-003 |
| WRD-007 | A technical-noun token is functioning as a verb | all prose | parser · `no-technical-noun-as-verb` | see corpus/words/selection.md#STOW-WRD-007 |
| WRD-008 | A technical noun is selected where a company, industry, or field term exists | all prose | heuristic · `company-term-preferred` | see corpus/words/usage.md#STOW-WRD-008 |
| WRD-010 | A candidate technical noun looks regional, slang, or jargon | all prose | semantic-review · `no-slang-or-jargon-noun` | see corpus/words/usage.md#STOW-WRD-010 |
| WRD-011 | A referent, logical relation, or recurring work context is named more than once | all prose | contextual review · keep one technical noun per referent, preserve key words and key phrases that organize the logic, and reuse the same wording for the same recurring context | see corpus/words/usage.md#STOW-WRD-011 |
| WRD-014 | A word has a spelling variant (skips quoted text) | all prose | deterministic · `american-english-spelling` | see corpus/words/usage.md#STOW-WRD-014 |

WRD-011 and WRD-014 carry recorded conflict resolutions (with the presentation
layer and with protected regions respectively); the corpus file states the
resolution.

## MWN: multi-word nouns

| Rule | Observable trigger | Region | How STOW checks | Full text |
| --- | --- | --- | --- | --- |
| MWN-001 | A coined or approved noun phrase contains stacked nouns or modifiers | all prose | contextual review · keep it to three words and keep coined terms short and easy; if an approved term is longer, write it in full first and then use a declared short form, approved abbreviation, or clear hyphenation | see corpus/multiword-nouns.md#STOW-MWN-001 |

## VRB: verbs, voice, and tense

| Rule | Observable trigger | Region | How STOW checks | Full text |
| --- | --- | --- | --- | --- |
| VRB-002 | A verb carries tense or aspect marking | all prose | contextual guidance · allow only infinitive, imperative, simple present, simple past, simple future, and a listed past participle used as an adjective; the named parser is planned, not callable | see corpus/verbs/technical-verbs.md#STOW-VRB-002 |
| VRB-005 | An `-ing` word appears | all prose | parser · `ing-only-as-technical-noun` | see corpus/verbs/technical-verbs.md#STOW-VRB-005 |
| VRB-006 | A clause is in the passive voice | all prose | parser · `active-voice-required-unless-agentless-descriptive` | see corpus/verbs/verb-forms.md#STOW-VRB-006 |
| VRB-007 | An action is expressed as a noun, or a technical verb is used in a non-verb role | all prose | contextual review · express the action with the verb; a listed past participle can act as an adjective | see corpus/verbs/verb-forms.md#STOW-VRB-007 |

## SEN: sentences, lists, and articles

| Rule | Observable trigger | Region | How STOW checks | Full text |
| --- | --- | --- | --- | --- |
| SEN-002 | A contraction or a dropped word appears | all prose | deterministic · `no-contractions-no-word-omission` | see corpus/sentences.md#STOW-SEN-002 |
| SEN-003 | A sentence packs complex or enumerated content | all prose | heuristic · `vertical-list-formatting` | see corpus/sentences.md#STOW-SEN-003 |
| SEN-004 | Adjacent sentences share a related topic | all prose | heuristic · `approved-connectors-only` | see corpus/sentences.md#STOW-SEN-004 |
| SEN-005 | A noun or multi-word noun appears without an article or demonstrative | all prose | parser · `article-and-demonstrative-usage` | see corpus/sentences.md#STOW-SEN-005 |

## STY: writing-practice consistency

| Rule | Observable trigger | Region | How STOW checks | Full text |
| --- | --- | --- | --- | --- |
| STY-001 | A sentence where a word-for-word swap does not hold | all prose | semantic-review · `rewrite-construction-preserve-meaning` | see corpus/style/economy.md#STOW-STY-001 |
| STY-003 | A verb-plus-particle pairing appears | all prose | parser · `no-phrasal-verbs` | see corpus/style/economy.md#STOW-STY-003 |

## GEN: general recommendations

| Rule | Observable trigger | Region | How STOW checks | Full text |
| --- | --- | --- | --- | --- |
| GEN-002 | The preposition `with` appears | all prose | heuristic · `with-ambiguity-check` | see corpus/general-practice.md#STOW-GEN-002 |
| GEN-003 | A pronoun appears | all prose | parser · `approved-and-unambiguous-pronoun` | see corpus/general-practice.md#STOW-GEN-003 |
| GEN-005 | A word resembling a cross-language cognate appears | all prose | semantic-review · `false-friend-check` | see corpus/general-practice.md#STOW-GEN-005 |
| GEN-006 | A Latin-derived abbreviation appears | all prose | deterministic · `no-latin-abbreviations` | see corpus/general-practice.md#STOW-GEN-006 |
| GEN-007 | Gendered or non-inclusive wording appears | all prose | deterministic · `gender-neutral-language` | see corpus/general-practice.md#STOW-GEN-007 |
