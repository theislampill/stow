# Cross-rule conflict resolutions

This document lists every declared conflict between STOW rules and the resolution
that governs when the two rules would otherwise pull in opposite directions. It is
generated from the `conflicts[]` arrays in `skills/stow/rules/registry.yaml`.

Conventions:

- Rules are referenced by id only. This document does not restate any rule's wording.
- Each conflict is a symmetric pair: both records declare it, so each pair is listed
  once here.
- Resolution text is reproduced verbatim from the registry.
- Pairs are grouped by the precedence principle that decides them.

Twelve records carry a non-empty `conflicts[]` array, which reduces to eight unique
rule pairs across three precedence principles.

---

## 1. Profile beats presentation

When a controlled-technical writing rule (`precedence: profile`) meets a
presentation-layer preference (`precedence: presentation`), the profile wins. The
presentation preference still applies, but only within the room the profile leaves.

### 1a. Sentence-length caps outrank the length-variation preference

**STOW-PRC-001 and STOW-PRO-007**

> Sentence-length caps govern inside a controlled-technical profile. Vary sentence length below the cap, never above it; the profile outranks the presentation-layer variance preference.

**STOW-DSC-003 and STOW-PRO-007**

> Sentence-length caps govern inside a controlled-technical profile. Vary sentence length below the cap, never above it; the profile outranks the presentation-layer variance preference.

### 1b. Consistent terminology outranks the wording-variation preference

**STOW-WRD-011 and STOW-PRO-007**

> Keep consistent terminology and wording for the same item or recurring step. Domain terminology and the controlled-technical profile outrank the presentation-layer variation preference.

**STOW-STY-004 and STOW-PRO-007**

> Keep consistent terminology and wording for the same item or recurring step. Domain terminology and the controlled-technical profile outrank the presentation-layer variation preference.

### 1c. Profile decides the banned-character substitution

**STOW-PCT-001 and STOW-PRO-001**

> Use neither character. Replace with a period, comma, colon, or two sentences; the active controlled-technical profile decides the substitute and outranks the presentation-layer preference.

---

## 2. Protected literals beat prose preferences

Presentation-layer lexical rules never touch protected regions. Keys, identifiers,
and quoted text stay exactly as written, because serialization validity and the
integrity of protected literals outrank any wording preference.

**STOW-WRD-014 and STOW-PRO-021**

> Protected regions are immutable. Do not rename keys or identifiers and do not edit quoted text; serialization validity and protected literals outrank presentation-layer lexical preferences, which skip protected regions.

**STOW-PCT-006 and STOW-PRO-021**

> Protected regions are immutable. Do not rename keys or identifiers and do not edit quoted text; serialization validity and protected literals outrank presentation-layer lexical preferences, which skip protected regions.

---

## 3. Factual accuracy beats the presentation preference

A preference to present a specific figure yields to the requirement that every number
be defensible. An unsupported number is omitted rather than shown.

**STOW-ACT-006 and STOW-PRO-002**

> Give an effort estimate only when a defensible range exists; otherwise omit it. Factual accuracy outranks the presentation-layer estimate preference, and an unsupported number must not be presented as fact.
