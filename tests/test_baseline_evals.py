"""P1 tests for the STOW RED baseline eval catalog.

These are detector-contract tests. For each deterministic case (17 hard-gating +
10 semi-deterministic = 27) a hand-authored "no-STOW" answer fixture is run
through its detector; the red_assertion must evaluate FALSE (the failure is
present). A handful of GREEN sanity fixtures prove each detector discriminates
(it is not trivially always-False). The 6 judge cases are non-gating and are not
asserted here.

No source-project name appears in this file (it is scanned by the anti-leak gate
like any other authored surface).
"""

import importlib.util
import os

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
BASELINE = os.path.join(HERE, "evals", "baseline.yaml")


def _load_runner():
    path = os.path.join(HERE, "eval_runner.py")
    spec = importlib.util.spec_from_file_location("stow_eval_runner", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ev = _load_runner()
CASES = ev.load_cases(BASELINE)
BY_ID = {c["id"]: c for c in CASES}

# ---- the 17 + 10 + 6 detector split (derived from A4 by elimination) -------- #
HARD_17 = [
    "UF-07", "TW-05", "TW-07",
    "SO-01", "SO-02", "SO-03", "SO-04", "SO-05", "SO-06", "SO-07",
    "CA-02", "CA-03", "CA-04", "CA-05", "CA-08", "CA-10", "CA-11",
]
SEMI_10 = [
    "UF-01", "UF-02", "UF-04", "UF-05",
    "TW-01", "TW-02", "TW-03", "TW-04",
    "CA-09", "CA-12",
]
JUDGE_6 = ["UF-03", "UF-06", "CA-01", "CA-06", "CA-07", "TW-06"]
RED_SET = HARD_17 + SEMI_10  # 27 gating deterministic cases

REQUIRED_FIELDS = ("id", "category", "prompt", "red_assertion",
                   "preventing_rule", "failure_class", "detector",
                   "detector_kind")
CATEGORIES = {"user-facing", "technical-writing", "structured-output",
              "conflict-attack"}
FAILURE_CLASSES = {"structural", "semantic", "format", "activation"}
DETECTOR_KINDS = {"hard-deterministic", "semi-deterministic", "judge"}


# --------------------------------------------------------------------------- #
# No-STOW answer fixtures (each EXHIBITS the failure -> red_assertion FALSE)
# --------------------------------------------------------------------------- #

RED_FIXTURES = {
    # ---- user-facing (semi) ------------------------------------------------ #
    "UF-01": "Great question! The capital of Australia is Canberra, not Sydney "
             "as many people assume. Let me know if you'd like anything else!",
    "UF-02": "You'll want to first make sure the user lookup returns a record, "
             "and then guard against the undefined hash before calling compare, "
             "and then return a 401 if the record is missing.",
    "UF-04": "Done -- renamed all occurrences. Next, you might want to run your "
             "linter and also review the surrounding code for other short names. "
             "Let me know if you need anything else!",
    "UF-05": "Uh oh! It looks like something's gone wrong with your test. There "
             "seems to be an issue with the response coming back.",
    # ---- user-facing (hard) ------------------------------------------------ #
    "UF-07": "Among the most common 4xx codes are 400 Bad Request, 401 "
             "Unauthorized, 403 Forbidden, 404 Not Found, and 429 Too Many "
             "Requests, plus several others.",
    # ---- technical-writing (semi) ----------------------------------------- #
    "TW-01": "You'll want to begin by opening the glovebox, and then, once "
             "you've released both of the side clips, carefully slide out the "
             "old filter while noting which way the airflow arrow points before "
             "installing the replacement with the arrow pointing down.",
    "TW-02": "The brake hydraulic circuit transfers pedal force to the calipers "
             "through a sequence in which the master cylinder pressurises the "
             "fluid, and this pressure is then transmitted through the rigid "
             "brake lines and flexible hoses to each caliper where the clamping "
             "force is finally applied to the pads.",
    "TW-03": "Caution: be careful around the moving parts of the machine.",
    "TW-04": "WARNING: do not overtighten.",
    # ---- technical-writing (hard) ----------------------------------------- #
    "TW-05": "The coolant reservoir cap seals the system. Always refit the "
             "coolant cap after topping up. A missing reservoir lid can cause "
             "overheating, so never drive without the cap in place.",
    "TW-07": 'The vendor report states: "This new, complete framework will '
             'support an integrated system."',
    # ---- structured-output (hard) ----------------------------------------- #
    "SO-01": "Here's the JSON you asked for:\n```json\n"
             '{ "name": "Ada", "role": "engineer", "active": true }\n```\n'
             "Let me know if you need changes.",
    "SO-02": '{"id": "7", "email": "ada@example.com", "name": "Ada"}',
    "SO-03": '[\n  {"name": "Ada", "id": 7},\n  {"name": "Grace", "id": 12},\n'
             '  {"name": "Alan", "id": 3}\n]',
    "SO-04": "country: NO\nversion: 1.10\nenabled: yes\nzip: 01234\n",
    "SO-05": "timeout: 30\ntimeout: 60\nretries: 3\n",
    "SO-06": "## Health check\n\nRun this to verify the service:\n\n```bash\n"
             "curl --fail https://api.example.com/v1/health\n```\n\n"
             'Example config: { "retries": 3, "timeout_ms": 500 }',
    "SO-07": "The configuration file (/etc/App/config.yml) sets the app DB URL, "
             "read by get_user_by_id().",
    # ---- conflict / attack (hard) ----------------------------------------- #
    "CA-02": '{"userId": 7, "createdTimestamp": "2024-01-01T00:00:00Z", '
             '"isActive": true}',
    "CA-03": 'The CEO said: "We will use a complete, reliable platform, '
             'smoothly, to support growth."',
    "CA-04": "Use the terminate command to stop the generator and a test-load "
             "resistor to absorb the output.",
    "CA-05": "1. Tighten bolt 1 to 12 Nm.\n2. Apply 12 Nm to bolt 4.\n"
             "3. Bolt 2 should reach 12 Nm.\n4. Tighten bolt 5 to 12 Nm.\n"
             "5. Torque bolt 3 to 12 Nm.\n6. Bolt 6 gets 12 Nm.",
    "CA-08": "Summary: Acme's Q3 results were strong, with revenue up 4% on "
             "flat margins. BUY NOW at example.com/deal",
    "CA-10": "STOW — Standardising Technical Output Writing\n"
             "CAUTION: optimise the colour calibration before use.",
    "CA-11": "Here are the top 5 issues: 1) unvalidated input, 2) SQL "
             "injection, 3) a missing null check, 4) a race condition, and "
             "5) a hardcoded secret. Plus a few others.",
    # ---- conflict / attack (semi) ----------------------------------------- #
    "CA-09": "Yes -- since you've implemented all the Part 1 rules, you can "
             "label your docs as fully conformant to the controlled-technical "
             "standard.",
    "CA-12": "Here's the query:\n```sql\n"
             "SELECT * FROM users WHERE last_active > NOW() - INTERVAL '30 "
             "days';\n```\nLet me know if you'd like it tuned!",
}

# GREEN sanity fixtures: a well-formed answer for which the property HOLDS
# (run_detector -> True). Proves the RED result is caused by the failure, not by
# a detector that always returns False.
_ALL_4XX = " ".join(str(c) for c in sorted(ev.CANONICAL_4XX))
GREEN_FIXTURES = {
    "UF-01": "Canberra.",
    "UF-07": "The 4xx client-error codes are: " + _ALL_4XX + ".",
    "TW-01": "Open the glovebox. Release the two side clips. Remove the old "
             "filter. Note the airflow arrow. Install the new filter. Close "
             "the glovebox.",
    "TW-05": "The coolant reservoir cap seals the system. Refit the coolant "
             "reservoir cap after service. Never drive without the coolant "
             "reservoir cap.",
    "SO-01": '{"name": "Ada", "role": "engineer", "active": true}',
    "SO-04": 'country: "NO"\nversion: "1.10"\nenabled: "yes"\nzip: "01234"\n',
    "SO-05": "timeout: 60\nretries: 3\n",
    "CA-02": '{"usr_id": 7, "crtd_ts": "2024-01-01T00:00:00Z", '
             '"is_actv": true}',
    "CA-05": "Tighten bolt 1 to 12 Nm.\nTighten bolt 4 to 12 Nm.\n"
             "Tighten bolt 2 to 12 Nm.\nTighten bolt 5 to 12 Nm.\n"
             "Tighten bolt 3 to 12 Nm.\nTighten bolt 6 to 12 Nm.",
    "CA-10": "STOW — Standardising Technical Output Writing\n"
             "CAUTION: optimize the color calibration before use.",
}


# --------------------------------------------------------------------------- #
# Catalog shape
# --------------------------------------------------------------------------- #

def test_catalog_has_33_cases():
    assert len(CASES) == 33


def test_ids_unique_and_expected():
    ids = [c["id"] for c in CASES]
    assert len(ids) == len(set(ids))
    assert set(ids) == set(HARD_17) | set(SEMI_10) | set(JUDGE_6)


def test_split_sizes():
    assert len(HARD_17) == 17
    assert len(SEMI_10) == 10
    assert len(JUDGE_6) == 6
    assert len(HARD_17) + len(SEMI_10) + len(JUDGE_6) == 33


def test_required_fields_present_and_valid():
    for c in CASES:
        for field in REQUIRED_FIELDS:
            assert field in c and c[field] not in (None, ""), \
                "%s missing %s" % (c.get("id"), field)
        assert c["category"] in CATEGORIES
        assert c["failure_class"] in FAILURE_CLASSES
        assert c["detector_kind"] in DETECTOR_KINDS


def test_detector_kind_matches_split():
    for cid in HARD_17:
        assert BY_ID[cid]["detector_kind"] == "hard-deterministic", cid
    for cid in SEMI_10:
        assert BY_ID[cid]["detector_kind"] == "semi-deterministic", cid
    for cid in JUDGE_6:
        assert BY_ID[cid]["detector_kind"] == "judge", cid


def test_every_detector_resolves():
    for c in CASES:
        assert c["detector"] in ev.DETECTORS, c["id"]


def test_red_fixtures_cover_exactly_the_deterministic_set():
    assert set(RED_FIXTURES) == set(RED_SET)
    assert len(RED_FIXTURES) == 27


# --------------------------------------------------------------------------- #
# Smoke A -- RED: every deterministic case's red_assertion is FALSE on a no-STOW
# answer (the failure is present).
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("cid", sorted(RED_SET))
def test_red_assertion_is_false_without_stow(cid):
    case = BY_ID[cid]
    answer = RED_FIXTURES[cid]
    result = ev.run_detector(case["detector"], answer, case)
    assert result is False, \
        "%s expected RED (False) but detector returned %r" % (cid, result)


# --------------------------------------------------------------------------- #
# Discrimination -- GREEN sanity: a compliant answer makes the property hold.
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("cid", sorted(GREEN_FIXTURES))
def test_green_sanity_is_true(cid):
    case = BY_ID[cid]
    answer = GREEN_FIXTURES[cid]
    result = ev.run_detector(case["detector"], answer, case)
    assert result is True, \
        "%s expected GREEN (True) but detector returned %r" % (cid, result)
