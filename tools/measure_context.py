#!/usr/bin/env python3
"""Measure the context cost of skill files, in tokens.

REPO-ONLY dev tool (not packaged into the shipped skill).

Measurement methods (recorded in every output):
    * ``o200k_base (tiktoken, local cache)`` -- exact counts, used when the
      encoding file is ALREADY in a local tiktoken cache directory.
    * ``estimate-chars-3.5`` -- a deterministic character estimator
      (``ceil(chars / 3.5)``) used when the encoding is not cached. It
      over-counted the historical calibration files, but it is not a universal
      upper bound for other files, tokenizers, or models.

This tool does not invoke tiktoken when the named cache file is absent.
tiktoken downloads a missing encoding on first use, so the precheck keeps the
ordinary cold-cache path offline.
(Residual: a cache file that exists but fails tiktoken's own integrity check
would make tiktoken re-download; that corner is outside the offline contract.)

Generic single-file mode (default)
    Preserves the historical generic-file behaviour: measure the complete file
    with the available method and fail when that measurement exceeds 1500.
    This mode remains useful for fixtures and non-SKILL.md files.

STOW skill-budget mode (``--skill-budget``)
    Applies the owner-amended R0001 contract to a frontmatter-bearing SKILL.md:

    * complete SKILL.md exact ``o200k_base`` <= 1500 is hard;
    * operative body fallback ``ceil(chars / 3.5)`` <= 1500 is hard;
    * complete SKILL.md fallback is recorded but nonblocking.

    ``--require-exact`` makes an unavailable exact tokenizer a failure. Without
    it, a cold-cache run enforces the body fallback, records the complete-file
    fallback, and marks the exact result NOT EVALUATED.

Bundle mode (``--bundles <manifest>``)
    Reads a YAML manifest that groups files into named bundles, sums the token
    count of each bundle, and reports every total. This mode is SOFT: it reports
    but never fails (always exits 0).

Manifest shape::

    bundles:
      core:
        - SKILL.md
        - references/rule-index.md
      runtime:
        - runtime/validate.py

Bundle member paths are resolved relative to the manifest file's directory.

These are static file measurements, not observations of live host reads,
latency, tool calls, or repair work. Token counts use one tokenizer; other
models can tokenize differently.
"""

import argparse
import hashlib
import math
import os
import sys
import tempfile

from ruamel.yaml import YAML

ENCODING_NAME = "o200k_base"
HARD_CEILING = 1500
FULL_SKILL_EXACT_CEILING = 1500
KERNEL_BODY_FALLBACK_CEILING = 1500
BAND_LOW = 800
BAND_HIGH = 1200

# tiktoken caches each encoding under sha1(<its download URL>). Computing the
# key here lets this tool detect a warm cache WITHOUT importing the loader
# machinery that would download on a miss.
_ENCODING_BLOB_URL = (
    "https://openaipublic.blob.core.windows.net/encodings/o200k_base.tiktoken")

ESTIMATE_DIVISOR = 3.5
METHOD_TOKENIZER = "%s (tiktoken, local cache)" % ENCODING_NAME
METHOD_ESTIMATE = ("estimate-chars-3.5 (calibrated fallback; tokenizer "
                   "cache unavailable, no download attempted)")

_PROXY_CAVEAT = ("note: static file proxy only; counts use one tokenizer (%s), "
                 "and the character estimate is not a universal upper bound."
                 % ENCODING_NAME)

_UNSET = object()


def _cache_dir():
    """The single cache directory tiktoken will use. tiktoken STOPS at the
    first configured variable (it never falls through to the default when a
    variable is set but the directory is empty), so this detection must stop
    there too or it would disagree with the loader it fronts."""
    for var in ("TIKTOKEN_CACHE_DIR", "DATA_GYM_CACHE_DIR"):
        value = os.environ.get(var, "")
        if value:
            return value
    return os.path.join(tempfile.gettempdir(), "data-gym-cache")


def find_cached_encoding():
    """Path of the locally cached encoding file, or None. Never touches the
    network."""
    key = hashlib.sha1(_ENCODING_BLOB_URL.encode("utf-8")).hexdigest()
    candidate = os.path.join(_cache_dir(), key)
    return candidate if os.path.isfile(candidate) else None


def get_encoder():
    """A tiktoken encoder when the encoding is already cached, else None.

    Returning None selects the deterministic estimate; no code path here can
    trigger a download.
    """
    if find_cached_encoding() is None:
        return None
    import tiktoken
    return tiktoken.get_encoding(ENCODING_NAME)


def measurement_method(encoder):
    return METHOD_TOKENIZER if encoder is not None else METHOD_ESTIMATE


def estimate_tokens(text):
    """Deterministic character estimate: ceil(chars / 3.5)."""
    return int(math.ceil(len(text) / ESTIMATE_DIVISOR))


def skill_body_text(text):
    """Return every character after the closing YAML frontmatter delimiter.

    The body is returned without normalisation so character accounting follows
    the same exact text boundary protected by the repository's SHA-256 gate.
    """
    if not text.startswith("---\n"):
        raise ValueError("SKILL.md must start with YAML frontmatter")
    closing = text.find("\n---\n", 4)
    if closing < 0:
        raise ValueError("SKILL.md frontmatter has no closing delimiter")
    return text[closing + len("\n---\n"):]


def skill_budget_measurements(text, encoder=_UNSET):
    """Return the three measurements in the amended R0001 budget contract."""
    if encoder is _UNSET:
        encoder = get_encoder()
    body = skill_body_text(text)
    return {
        "full_exact_tokens": (
            None if encoder is None else count_tokens(text, encoder)
        ),
        "body_fallback_tokens": estimate_tokens(body),
        "full_fallback_tokens": estimate_tokens(text),
        "body_chars": len(body),
        "full_chars": len(text),
    }


def count_tokens(text, encoder=_UNSET):
    if encoder is _UNSET:
        encoder = get_encoder()
    if encoder is None:
        return estimate_tokens(text)
    return len(encoder.encode(text))


def _read_text(path):
    with open(path, "rb") as handle:
        return handle.read().decode("utf-8", errors="replace")


def band_status(tokens):
    if tokens < BAND_LOW:
        return "UNDER BAND"
    if tokens > BAND_HIGH:
        return "OVER BAND"
    return "WITHIN BAND"


def measure_file(path, encoder=_UNSET):
    text = _read_text(path)
    if encoder is _UNSET:
        encoder = get_encoder()
    tokens = count_tokens(text, encoder)
    chars = len(text)
    return tokens, chars


def _print_header(encoder):
    print("measurement: %s" % measurement_method(encoder))
    if encoder is not None:
        print("tokenizer: %s (tiktoken)" % ENCODING_NAME)


def run_single(path, encoder):
    tokens, chars = measure_file(path, encoder)
    over_ceiling = tokens > HARD_CEILING

    _print_header(encoder)
    print("file: %s" % path)
    print("tokens: %d" % tokens)
    print("chars: %d" % chars)
    if encoder is not None:
        print("target band %d-%d: %s"
              % (BAND_LOW, BAND_HIGH, band_status(tokens)))
    else:
        print("target band %d-%d: NOT EVALUATED (estimate mode; band checks "
              "need the exact tokenizer)" % (BAND_LOW, BAND_HIGH))
    print("hard ceiling %d: %s"
          % (HARD_CEILING, "EXCEEDED" if over_ceiling else "OK"))
    print(_PROXY_CAVEAT)

    if over_ceiling:
        print("FAIL: %s is over the %d-token hard ceiling (%d tokens)"
              % (path, HARD_CEILING, tokens), file=sys.stderr)
        return 1
    return 0


def run_skill_budget(path, encoder=_UNSET, require_exact=False):
    """Apply the amended full-exact/body-fallback SKILL.md contract."""
    text = _read_text(path)
    if encoder is _UNSET:
        encoder = get_encoder()
    try:
        measurements = skill_budget_measurements(text, encoder)
    except ValueError as exc:
        print("FAIL: %s" % exc, file=sys.stderr)
        return 1

    exact = measurements["full_exact_tokens"]
    body_fallback = measurements["body_fallback_tokens"]
    full_fallback = measurements["full_fallback_tokens"]
    body_over = body_fallback > KERNEL_BODY_FALLBACK_CEILING
    exact_over = exact is not None and exact > FULL_SKILL_EXACT_CEILING
    exact_missing = require_exact and exact is None

    _print_header(encoder)
    print("budget contract: complete-file exact + operative-body fallback")
    print("file: %s" % path)
    if exact is None:
        print("full skill exact o200k_base: NOT EVALUATED "
              "(tokenizer cache unavailable)")
        print("full skill exact hard ceiling %d: NOT EVALUATED"
              % FULL_SKILL_EXACT_CEILING)
    else:
        print("full skill exact o200k_base: %d" % exact)
        print("full skill exact hard ceiling %d: %s"
              % (FULL_SKILL_EXACT_CEILING,
                 "EXCEEDED" if exact_over else "OK"))
    print("kernel body fallback: %d" % body_fallback)
    print("kernel body fallback hard ceiling %d: %s"
          % (KERNEL_BODY_FALLBACK_CEILING,
             "EXCEEDED" if body_over else "OK"))
    print("full skill fallback (recorded, nonblocking): %d" % full_fallback)
    print("full skill chars: %d" % measurements["full_chars"])
    print("kernel body chars: %d" % measurements["body_chars"])
    print(_PROXY_CAVEAT)

    failed = False
    if exact_missing:
        print("FAIL: exact o200k_base measurement required but tokenizer "
              "cache is unavailable", file=sys.stderr)
        failed = True
    if exact_over:
        print("FAIL: complete SKILL.md exceeds the %d exact-token ceiling "
              "(%d tokens)" % (FULL_SKILL_EXACT_CEILING, exact),
              file=sys.stderr)
        failed = True
    if body_over:
        print("FAIL: operative kernel body exceeds the %d fallback ceiling "
              "(%d tokens)" % (KERNEL_BODY_FALLBACK_CEILING, body_fallback),
              file=sys.stderr)
        failed = True
    return 1 if failed else 0


def _load_manifest(path):
    yaml = YAML(typ="safe")
    with open(path, encoding="utf-8") as handle:
        return yaml.load(handle)


def run_bundles(manifest_path, encoder):
    data = _load_manifest(manifest_path) or {}
    bundles = data.get("bundles") or {}
    base = os.path.dirname(os.path.abspath(manifest_path))

    _print_header(encoder)
    print("manifest: %s (bundle mode is soft; never fails)" % manifest_path)

    if not bundles:
        print("no bundles found in manifest")
        print(_PROXY_CAVEAT)
        return 0

    for name in bundles:
        members = bundles[name] or []
        total_tokens = 0
        total_chars = 0
        print("bundle %s:" % name)
        for member in members:
            member_path = os.path.join(base, str(member))
            if not os.path.isfile(member_path):
                print("  %-40s MISSING" % member)
                continue
            tokens, chars = measure_file(member_path, encoder)
            total_tokens += tokens
            total_chars += chars
            print("  %-40s %6d tokens (chars=%d)" % (member, tokens, chars))
        print("  %-40s %6d tokens (chars=%d)"
              % ("TOTAL", total_tokens, total_chars))
    print(_PROXY_CAVEAT)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("path", help="a file to measure, or a bundle manifest with --bundles")
    parser.add_argument("--bundles", action="store_true",
                        help="treat PATH as a YAML bundle manifest (soft; never fails)")
    parser.add_argument("--skill-budget", action="store_true",
                        help="apply the complete-exact/body-fallback SKILL.md contract")
    parser.add_argument("--require-exact", action="store_true",
                        help="with --skill-budget, fail if o200k_base is unavailable")
    args = parser.parse_args(argv)

    if args.bundles and args.skill_budget:
        parser.error("--bundles and --skill-budget are mutually exclusive")
    if args.require_exact and not args.skill_budget:
        parser.error("--require-exact requires --skill-budget")

    encoder = get_encoder()

    if args.bundles:
        return run_bundles(args.path, encoder)
    if args.skill_budget:
        return run_skill_budget(args.path, encoder, args.require_exact)
    return run_single(args.path, encoder)


if __name__ == "__main__":
    sys.exit(main())
