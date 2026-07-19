#!/usr/bin/env python3
"""Deterministic package builder for the STOW skill.

Packs everything under ``skills/stow/**`` into ``dist/STOW.skill`` -- a ZIP
archive whose single top-level directory ``stow/`` holds the remapped tree
(``skills/stow/SKILL.md`` -> ``stow/SKILL.md``, ``skills/stow/references/`` ->
``stow/references/``, and likewise for ``corpus/``, ``rules/``, ``runtime/``).
The ``tools/`` directory sits outside ``skills/stow/`` and is therefore never
seen by the walk, so it is excluded by construction.

The build is byte-for-byte reproducible. Two runs on the same content produce an
identical archive (and therefore an identical SHA-256) because every source of
non-determinism is pinned:

* ``ZIP_STORED`` -- no compression, so no compressor-version drift.
* ``create_system = 3`` (Unix) on every entry, regardless of the build host OS.
* ``external_attr = 0o644 << 16`` -- one fixed permission bit pattern.
* ``date_time = (1980, 1, 1, 0, 0, 0)`` -- the ZIP epoch, so no wall-clock time.
* ``flag_bits = 0`` and empty ``extra`` -- no data descriptor, no extra fields.
* ``allowZip64 = False`` -- no ZIP64 records (all members are tiny).
* no archive comment.
* entries emitted in sorted archive-name order.
* every text file's bytes normalised to LF before it is written.

Alongside the archive the builder writes ``dist/STOW.skill.sha256`` (a
``sha256sum``-style line) and ``dist/manifest.json`` (the archived entry list
plus the product version from the plugin manifest; no build-environment
strings, so the manifest is reproducible across hosts).

The ``runtime/`` subtree ships an ALLOWLIST -- exactly ``validate.py``,
``lint_prose.py``, and ``profiles.py``. Byte-compiled caches (``__pycache__``, ``*.pyc``) and other
incidental files never enter the archive.
"""

import argparse
import hashlib
import io
import json
import os
import sys
import zipfile

# --------------------------------------------------------------------------- #
# Layout and pinned metadata
# --------------------------------------------------------------------------- #

SOURCE_PARTS = ("skills", "stow")   # the packaged subtree, under the repo root
TOP = "stow"                         # the single top-level directory in the zip
ARTIFACT_NAME = "STOW.skill"

# Only these runtime modules are packaged; everything else under runtime/ is
# dropped (the shipped runtime surface is a fixed, auditable allowlist).
RUNTIME_ALLOW = frozenset({"validate.py", "lint_prose.py", "profiles.py"})

# Deterministic ZIP entry metadata.
ZIP_DATE_TIME = (1980, 1, 1, 0, 0, 0)   # the DOS/ZIP epoch -- no wall-clock time
EXTERNAL_ATTR = 0o644 << 16              # rw-r--r-- in the high 16 bits
CREATE_SYSTEM = 3                        # Unix, independent of the build host
ENTRY_VERSION = 20                       # fixed create/extract version (2.0)

# Files and directories that never enter the archive.
EXCLUDE_DIR_NAMES = frozenset({"__pycache__"})
EXCLUDE_SUFFIXES = (".pyc", ".pyo")
EXCLUDE_BASENAMES = frozenset({".DS_Store", "Thumbs.db"})


# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #

def repo_root():
    """The repository root (the parent of this ``tools/`` directory)."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def source_root(root):
    return os.path.join(root, *SOURCE_PARTS)


# --------------------------------------------------------------------------- #
# Content normalisation
# --------------------------------------------------------------------------- #

def _is_binary(raw):
    return b"\x00" in raw


def normalize_lf(raw):
    """Normalise CRLF and lone-CR line endings to LF for text content.

    Operates on raw bytes so UTF-8 sequences are preserved untouched. Binary
    content (any file containing a NUL byte) is passed through verbatim.
    """
    if _is_binary(raw):
        return raw
    return raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


# --------------------------------------------------------------------------- #
# Source enumeration
# --------------------------------------------------------------------------- #

def collect_entries(root):
    """Return a sorted list of ``(abs_path, arcname)`` pairs to package.

    ``arcname`` is the archive path with ``skills/stow/`` remapped to
    ``stow/`` and forward slashes throughout.
    """
    src = source_root(root)
    entries = []
    for dirpath, dirnames, filenames in os.walk(src):
        # Prune excluded directories in place so os.walk never descends them.
        dirnames[:] = sorted(d for d in dirnames if d not in EXCLUDE_DIR_NAMES)

        rel_dir = os.path.relpath(dirpath, src)
        rel_dir = "" if rel_dir == "." else rel_dir.replace(os.sep, "/")

        for filename in filenames:
            if filename in EXCLUDE_BASENAMES:
                continue
            if filename.endswith(EXCLUDE_SUFFIXES):
                continue

            rel = filename if not rel_dir else rel_dir + "/" + filename

            # Runtime allowlist: only the sanctioned modules ship.
            top_segment = rel.split("/", 1)[0]
            if top_segment == "runtime" and filename not in RUNTIME_ALLOW:
                continue

            abs_path = os.path.join(dirpath, filename)
            arcname = TOP + "/" + rel
            entries.append((abs_path, arcname))

    entries.sort(key=lambda pair: pair[1])
    return entries


# --------------------------------------------------------------------------- #
# Archive construction
# --------------------------------------------------------------------------- #

def _zipinfo(arcname):
    info = zipfile.ZipInfo(arcname, date_time=ZIP_DATE_TIME)
    info.compress_type = zipfile.ZIP_STORED
    info.create_system = CREATE_SYSTEM
    info.create_version = ENTRY_VERSION
    info.extract_version = ENTRY_VERSION
    info.external_attr = EXTERNAL_ATTR
    info.internal_attr = 0
    info.flag_bits = 0
    info.extra = b""
    info.comment = b""
    return info


def build_archive_bytes(root):
    """Build the deterministic archive in memory and return its bytes."""
    entries = collect_entries(root)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED,
                         allowZip64=False) as archive:
        archive.comment = b""
        for abs_path, arcname in entries:
            with open(abs_path, "rb") as handle:
                data = normalize_lf(handle.read())
            archive.writestr(_zipinfo(arcname), data)
    return buffer.getvalue(), [arc for _abs, arc in entries]


# --------------------------------------------------------------------------- #
# Output writing
# --------------------------------------------------------------------------- #

def _product_version(root):
    """The product version, read from the plugin manifest -- the single
    committed version constant."""
    path = os.path.join(root, ".claude-plugin", "plugin.json")
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)["version"]


def _manifest(entries, digest, root):
    # The hash key is named ``artifact_sha256`` (not a bare ``sha256``) so it
    # matches the ``manifest.json:*_sha256`` content-hash position exemption in
    # the anti-leak gate: this digest is the STOW artifact's own hash, not a
    # leaked source-file hash.
    #
    # No build-environment block: environment strings differ across hosts and
    # would make the manifest non-reproducible (and disclose the build host).
    # The archive bytes are already environment-independent; the manifest must
    # be too, so the committed-artifact freshness gate can compare it.
    return {
        "artifact": ARTIFACT_NAME,
        "artifact_sha256": digest,
        "version": _product_version(root),
        "entry_count": len(entries),
        "entries": entries,
    }


def build(root=None, out_dir=None):
    """Build the artifact and write all three outputs into ``out_dir``.

    Returns a dict with the archive bytes, the SHA-256 hex digest, the archived
    entry list, and the three output paths.
    """
    root = root or repo_root()
    out_dir = out_dir or os.path.join(root, "dist")
    os.makedirs(out_dir, exist_ok=True)

    archive_bytes, entries = build_archive_bytes(root)
    digest = hashlib.sha256(archive_bytes).hexdigest()

    artifact_path = os.path.join(out_dir, ARTIFACT_NAME)
    sha_path = artifact_path + ".sha256"
    manifest_path = os.path.join(out_dir, "manifest.json")

    with open(artifact_path, "wb") as handle:
        handle.write(archive_bytes)

    with open(sha_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("%s  %s\n" % (digest, ARTIFACT_NAME))

    with open(manifest_path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(_manifest(entries, digest, root), handle,
                  indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")

    return {
        "archive_bytes": archive_bytes,
        "sha256": digest,
        "entries": entries,
        "artifact_path": artifact_path,
        "sha256_path": sha_path,
        "manifest_path": manifest_path,
    }


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Build the deterministic STOW skill package.")
    parser.add_argument("--out", default=None,
                        help="output directory (default: <repo>/dist)")
    args = parser.parse_args(argv)

    result = build(out_dir=args.out)
    print("artifact: %s" % result["artifact_path"])
    print("sha256:   %s" % result["sha256"])
    print("entries:  %d" % len(result["entries"]))
    print("manifest: %s" % result["manifest_path"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
