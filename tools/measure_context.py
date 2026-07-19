#!/usr/bin/env python3
"""Measure the context cost of skill files, in tokens.

REPO-ONLY dev tool (not packaged into the shipped skill). It uses ``tiktoken``
with the ``o200k_base`` encoding to count tokens.

Single-file mode (default)
    Prints the file's token count, a ``chars/4`` proxy alongside it, the target
    band status (800-1200), and the hard-ceiling status (1500). Exits NONZERO
    when the file is over the 1500-token hard ceiling; otherwise exits 0.

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

Token counts are a proxy: they reflect one specific tokenizer. Other models
tokenize differently, so treat the numbers as guidance and leave headroom.
"""

import argparse
import os
import sys

import tiktoken
from ruamel.yaml import YAML

ENCODING_NAME = "o200k_base"
HARD_CEILING = 1500
BAND_LOW = 800
BAND_HIGH = 1200

_PROXY_CAVEAT = ("note: token counts use one tokenizer (%s); other models "
                 "tokenize differently, so leave headroom." % ENCODING_NAME)


def get_encoder():
    return tiktoken.get_encoding(ENCODING_NAME)


def count_tokens(text, encoder=None):
    encoder = encoder or get_encoder()
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


def measure_file(path, encoder=None):
    text = _read_text(path)
    tokens = count_tokens(text, encoder)
    chars = len(text)
    return tokens, chars


def _print_header():
    print("tokenizer: %s (tiktoken)" % ENCODING_NAME)


def run_single(path, encoder):
    tokens, chars = measure_file(path, encoder)
    over_ceiling = tokens > HARD_CEILING

    _print_header()
    print("file: %s" % path)
    print("tokens: %d" % tokens)
    print("chars/4 proxy: %d (chars=%d)" % (chars // 4, chars))
    print("target band %d-%d: %s" % (BAND_LOW, BAND_HIGH, band_status(tokens)))
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

    _print_header()
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
            print("  %-40s %6d tokens (chars/4=%d)" % (member, tokens, chars // 4))
        print("  %-40s %6d tokens (chars/4=%d)"
              % ("TOTAL", total_tokens, total_chars // 4))
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
