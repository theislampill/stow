#!/usr/bin/env python3
"""Measure the context cost of skill files, in tokens.

REPO-ONLY dev tool (not packaged into the shipped skill).

Measurement method (recorded in every output):
    * ``o200k_base (tiktoken, local cache)`` -- exact counts, used when the
      encoding file is ALREADY in a local tiktoken cache directory.
    * ``estimate-chars-3.5`` -- a deterministic, conservative fallback
      (``ceil(chars / 3.5)``) used when the encoding is not cached. Measured on
      this repository's shipped files, the estimate over-counts by 8-38%, so a
      hard ceiling that passes in estimate mode also holds for real tokens.

This tool NEVER performs a network request. tiktoken downloads a missing
encoding on first use, so the tool first checks the local cache directories
itself and only invokes tiktoken when the encoding file is already present.
(Residual: a cache file that exists but fails tiktoken's own integrity check
would make tiktoken re-download; that corner is outside the offline contract.)

Single-file mode (default)
    Prints the file's token count, the target band status (800-1200), and the
    hard-ceiling status (1500). Exits NONZERO when the file is over the
    1500-token hard ceiling; otherwise exits 0. In estimate mode the ceiling is
    still enforced (the estimate is conservative); the band status is NOT
    evaluated, because a band has two sides and an over-count could misreport
    either of them.

Bundle mode (``--bundles <manifest>``)
    Reads a YAML manifest that groups files into named bundles, sums the token
    count of each bundle, and reports every total. This mode is SOFT: it
    reports but never fails (always exits 0).

Manifest shape::

    bundles:
      core:
        - SKILL.md
        - references/rule-index.md
      runtime:
        - runtime/validate.py

Bundle member paths are resolved relative to the manifest file's directory.

Token counts are a proxy: they reflect one specific tokenizer. Other models
tokenize differently, so treat the numbers as guidance and leave headroom.
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
BAND_LOW = 800
BAND_HIGH = 1200

# tiktoken caches each encoding under sha1(<its download URL>). Computing the
# key here lets this tool detect a warm cache WITHOUT importing the loader
# machinery that would download on a miss.
_ENCODING_BLOB_URL = (
    "https://openaipublic.blob.core.windows.net/encodings/o200k_base.tiktoken")

ESTIMATE_DIVISOR = 3.5
METHOD_TOKENIZER = "%s (tiktoken, local cache)" % ENCODING_NAME
METHOD_ESTIMATE = ("estimate-chars-3.5 (conservative fallback; tokenizer "
                   "cache unavailable, no download attempted)")

_PROXY_CAVEAT = ("note: token counts use one tokenizer (%s); other models "
                 "tokenize differently, so leave headroom." % ENCODING_NAME)

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
    """Deterministic conservative token estimate: ceil(chars / 3.5)."""
    return int(math.ceil(len(text) / ESTIMATE_DIVISOR))


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
    args = parser.parse_args(argv)

    encoder = get_encoder()

    if args.bundles:
        return run_bundles(args.path, encoder)
    return run_single(args.path, encoder)


if __name__ == "__main__":
    sys.exit(main())
