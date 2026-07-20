"""Three-way agreement gates for the validated reference load graph.

``skills/stow/rules/routing.yaml`` is a VALIDATION artifact: it mirrors the
kernel activation map (SKILL.md section 5), the profile data
(rules/profiles.json), and the raw-artifact router row emitted by
``tools/gen_always_on.py``. The kernel is never generated from routing.yaml and
no runtime path reads it, so these gates are what keep it honest.

Gates:
  (a) Every section-5 route line's reference paths appear in exactly one
      routing.yaml route, and every routing.yaml reference path appears in a
      section-5 line. Divergence in either direction fails.
  (b) Every profile id named in routing.yaml exists in profiles.json, and every
      available profile that carries auto_contexts appears in at least one route.
  (c) The raw-artifact router row in the gen_always_on.py ROUTER agrees with the
      raw route entry: a raw mode lists no references.
  (d) Every reference file under references/ is named by at least one route, or
      is listed in routing.yaml's ``unrouted:`` section with a reason.

This module is source-name-free: it names none of the external projects the
rules were derived from.
"""

import importlib.util
import os
import re

from ruamel.yaml import YAML

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SKILL_DIR = os.path.join(REPO, "skills", "stow")

SKILL_PATH = os.path.join(SKILL_DIR, "SKILL.md")
REFS_DIR = os.path.join(SKILL_DIR, "references")
ROUTING_PATH = os.path.join(SKILL_DIR, "rules", "routing.yaml")
PROFILES_PATH = os.path.join(SKILL_DIR, "rules", "profiles.json")

# A route path token: a references/<file>.md target, or the registry that the
# rule-audit line loads alongside its index. rules/profiles.json is deliberately
# excluded: it appears in a section-5 line only as a pointer to where a profile
# is defined (its binding is carried by the route ``profile`` field), not as a
# reference the route loads.
ROUTE_PATH_RE = re.compile(r"references/[A-Za-z0-9_.-]+\.md|rules/registry\.yaml")

# --------------------------------------------------------------------------- #
# Loaders
# --------------------------------------------------------------------------- #


def _read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def _load_yaml(path):
    yaml = YAML(typ="safe")
    with open(path, encoding="utf-8") as handle:
        return yaml.load(handle)


def _load_json(path):
    import json
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _load_module(name, relpath):
    spec = importlib.util.spec_from_file_location(name, os.path.join(REPO, relpath))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SKILL_TEXT = _read(SKILL_PATH)
ROUTING = _load_yaml(ROUTING_PATH)
PROFILES = _load_json(PROFILES_PATH)
ROUTES = ROUTING["routes"]
UNROUTED = ROUTING.get("unrouted") or []


def _activation_map_lines():
    """Section-5 bullet lines carrying a predicate -> target mapping.

    Same mechanical extraction used by test_references.py: find the activation
    map heading, then take the ``- ... -> ...`` bullets until the next heading.
    """
    lines = SKILL_TEXT.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.startswith("## ") and "activation map" in line.lower():
            start = i
            break
    assert start is not None, "SKILL.md has no activation-map section"
    entries = []
    for line in lines[start + 1:]:
        if line.startswith("## "):
            break
        if "->" in line and line.lstrip().startswith("-"):
            entries.append(line)
    assert entries, "activation-map section has no predicate -> target bullets"
    return entries


ACTIVATION_LINES = _activation_map_lines()


# --------------------------------------------------------------------------- #
# Sanity
# --------------------------------------------------------------------------- #

def test_routing_loads_and_has_routes():
    assert ROUTES, "routing.yaml declares no routes"
    assert ROUTING.get("schema_version") == 1
    for route in ROUTES:
        for key in ("mode", "predicate", "references", "profile", "corpus", "validator"):
            assert key in route, "route %r missing key %s" % (route.get("mode"), key)
    modes = [r["mode"] for r in ROUTES]
    assert len(modes) == len(set(modes)), "duplicate route mode: %r" % modes
    # The two synthetic routes required by the spec are present.
    assert "kernel-alone" in modes, "kernel-alone fallback route missing"
    assert "raw-artifact-exclusion" in modes, "raw-artifact exclusion route missing"


# --------------------------------------------------------------------------- #
# Gate (a) -- section-5 reference paths and routing references agree both ways
# --------------------------------------------------------------------------- #

def _skill_route_paths():
    """Every reference path named across the section-5 bullets."""
    paths = []
    for line in ACTIVATION_LINES:
        paths.extend(ROUTE_PATH_RE.findall(line))
    return paths


def _routing_reference_paths():
    """(path, mode) for every reference path across all routes."""
    pairs = []
    for route in ROUTES:
        for ref in route["references"] or []:
            pairs.append((ref, route["mode"]))
    return pairs


def test_every_skill_path_is_in_exactly_one_route():
    routing_pairs = _routing_reference_paths()
    for path in _skill_route_paths():
        owners = [mode for ref, mode in routing_pairs if ref == path]
        assert len(owners) == 1, (
            "section-5 path %r appears in %d routes (%r), expected exactly one"
            % (path, len(owners), owners))


def test_every_route_path_is_a_skill_path():
    skill_paths = set(_skill_route_paths())
    for ref, mode in _routing_reference_paths():
        assert ref in skill_paths, (
            "route %r loads %r which no section-5 bullet names" % (mode, ref))


def test_path_sets_match_exactly():
    skill_paths = set(_skill_route_paths())
    route_paths = set(ref for ref, _mode in _routing_reference_paths())
    assert skill_paths == route_paths, (
        "section-5 paths and route paths diverge: only-in-skill=%r only-in-routes=%r"
        % (sorted(skill_paths - route_paths), sorted(route_paths - skill_paths)))


# --------------------------------------------------------------------------- #
# Gate (b) -- profile ids resolve; available auto_context profiles are routed
# --------------------------------------------------------------------------- #

def _profiles_by_id():
    return {p["id"]: p for p in PROFILES["profiles"]}


def test_route_profiles_exist_in_profiles_json():
    known = set(_profiles_by_id())
    for route in ROUTES:
        pid = route["profile"]
        if pid is None:
            continue
        assert pid in known, (
            "route %r names profile %r absent from profiles.json"
            % (route["mode"], pid))


def test_available_auto_context_profiles_are_routed():
    routed = {r["profile"] for r in ROUTES if r["profile"] is not None}
    for prof in PROFILES["profiles"]:
        if prof.get("status") != "available":
            continue
        if not prof.get("auto_contexts"):
            continue
        assert prof["id"] in routed, (
            "available profile %r carries auto_contexts but no route binds it"
            % prof["id"])


# --------------------------------------------------------------------------- #
# Gate (c) -- raw router row agrees; raw modes load no references
# --------------------------------------------------------------------------- #

def test_raw_route_agrees_with_always_on_router():
    gen = _load_module("gen_always_on_for_routing", os.path.join("tools", "gen_always_on.py"))
    router = gen.ROUTER
    assert "raw artifact:" in router, (
        "gen_always_on.py ROUTER has no raw-artifact row to agree with")
    raw_routes = [r for r in ROUTES if "raw" in r["mode"]]
    assert raw_routes, "routing.yaml has no raw route to match the router row"
    for route in raw_routes:
        assert (route["references"] or []) == [], (
            "raw route %r must load no references (a raw artifact loads none of "
            "the always-on checks); found %r" % (route["mode"], route["references"]))


# --------------------------------------------------------------------------- #
# Gate (d) -- every reference is routed or carries an unrouted reason
# --------------------------------------------------------------------------- #

def _all_reference_files():
    return sorted(f for f in os.listdir(REFS_DIR) if f.endswith(".md"))


def _routed_reference_basenames():
    routed = set()
    for ref, _mode in _routing_reference_paths():
        if ref.startswith("references/"):
            routed.add(ref.split("/", 1)[1])
    return routed


def _unrouted_reasons():
    reasons = {}
    for entry in UNROUTED:
        ref = entry["reference"]
        base = ref.split("/", 1)[1] if ref.startswith("references/") else ref
        reasons[base] = (entry.get("reason") or "").strip()
    return reasons


def test_every_reference_is_routed_or_reasoned():
    routed = _routed_reference_basenames()
    reasons = _unrouted_reasons()
    for name in _all_reference_files():
        if name in routed:
            continue
        assert name in reasons and reasons[name], (
            "reference %s is neither routed nor listed in unrouted: with a reason"
            % name)


def test_index_and_always_on_are_routed_not_unrouted():
    routed = _routed_reference_basenames()
    reasons = _unrouted_reasons()
    for name in ("rule-index.md", "always-on.md"):
        assert name in routed, "%s must be routed" % name
        assert name not in reasons, "%s must not appear in unrouted:" % name


def test_unrouted_entries_are_real_files_and_not_double_listed():
    routed = _routed_reference_basenames()
    existing = set(_all_reference_files())
    for name in _unrouted_reasons():
        assert name in existing, "unrouted names a missing reference: %s" % name
        assert name not in routed, (
            "reference %s is both routed and listed unrouted:" % name)


def test_no_em_dash_in_routing():
    assert "—" not in _read(ROUTING_PATH), "routing.yaml contains an em dash"
