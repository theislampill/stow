"""CI-integrity gate: the verification workflow must keep running every gate.

The doc-lint / count-leak property itself is already enforced by
``tests/test_count_leak.py``; this file does not duplicate it. What it enforces
is the layer above: that ``.github/workflows/verify.yml`` still *invokes* each
required gate by name.

Without this, any gate can be silently defanged by deleting one step from the
workflow. The suite would stay green -- the gate's own test file is untouched --
while the build stops checking the property. Here each required gate is pinned to
a step that must exist, so dropping a step fails the build loudly.

Two further defusing routes are closed as well:

* ``continue-on-error: true`` on a step turns a red gate into a warning.
* the leak gate must run in CI (default / weak) mode; ``--local`` needs a private
  pattern file that does not exist in CI, so a ``--local`` invocation there would
  hard-fail on the missing file rather than actually gating.

Run only this file: ``python -m pytest tests/test_doc_lint.py -q``.
"""

import os
import re

import pytest
from ruamel.yaml import YAML

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
WORKFLOW = os.path.join(REPO, ".github", "workflows", "verify.yml")


def load_workflow():
    yaml = YAML(typ="safe")
    with open(WORKFLOW, encoding="utf-8") as handle:
        return yaml.load(handle)


def steps():
    """Every step across every job, as a list of dicts."""
    data = load_workflow() or {}
    found = []
    for job in (data.get("jobs") or {}).values():
        found.extend((job or {}).get("steps") or [])
    return found


def run_commands():
    """The shell body of every step that has one."""
    return [str(s.get("run", "")) for s in steps() if s.get("run")]


# Each gate: a label, and the pattern its `run:` body must match.
# The pattern is matched against the raw shell body, so a step that invokes the
# gate inside a longer script still counts.
REQUIRED_GATES = (
    ("full pytest suite",        r"pytest\s+tests/(?:\s|$)"),
    ("rule-index generator",     r"tools/gen_rule_index\.py\s+--check"),
    ("always-on generator",      r"tools/gen_always_on\.py\s+--check"),
    ("conflict-doc generator",   r"tools/gen_rule_conflicts\.py\s+--check"),
    ("provenance leak gate",     r"tools/check_provenance_leak\.py"),
    ("count-leak / doc-lint",    r"tests/test_count_leak\.py"),
    ("install-smoke gate",       r"tests/test_install_smoke\.py"),
    ("CI-integrity gate",        r"tests/test_doc_lint\.py"),
)


# --------------------------------------------------------------------------- #
# The workflow exists and parses.
# --------------------------------------------------------------------------- #

def test_workflow_file_exists():
    assert os.path.isfile(WORKFLOW), "missing %s" % WORKFLOW


def test_workflow_parses_and_has_steps():
    assert steps(), "workflow declares no steps"


# --------------------------------------------------------------------------- #
# Every required gate is invoked.
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("label,pattern", REQUIRED_GATES,
                         ids=[g[0] for g in REQUIRED_GATES])
def test_ci_invokes_required_gate(label, pattern):
    bodies = run_commands()
    matched = [b for b in bodies if re.search(pattern, b)]
    assert matched, (
        "CI no longer runs the %s gate: no step matches %r. "
        "A gate was dropped from .github/workflows/verify.yml." % (label, pattern)
    )


def test_every_required_gate_step_is_named():
    """Each gate lives in a named step, so a failure reads as a property."""
    unnamed = [s for s in steps() if s.get("run") and not s.get("name")]
    assert unnamed == [], (
        "every step that runs a gate must carry a `name:` so CI failures are "
        "self-describing; unnamed: %r" % unnamed
    )


# --------------------------------------------------------------------------- #
# Gates must be real gates, not warnings.
# --------------------------------------------------------------------------- #

def test_no_step_is_continue_on_error():
    """`continue-on-error: true` downgrades a red gate to a warning."""
    soft = [s.get("name", "<unnamed>") for s in steps()
            if s.get("continue-on-error") is True]
    assert soft == [], "these steps cannot fail the build: %r" % soft


def test_install_smoke_is_a_real_gate():
    """The install-smoke step must not swallow its own exit status."""
    bodies = [b for b in run_commands() if "tests/test_install_smoke.py" in b]
    assert bodies, "install-smoke gate is not wired into CI"
    for body in bodies:
        assert "|| true" not in body, "install-smoke exit status is swallowed"
        assert "continue-on-error" not in body


# --------------------------------------------------------------------------- #
# The leak gate must run in CI mode.
# --------------------------------------------------------------------------- #

def test_leak_gate_runs_in_ci_mode_not_local():
    """`--local` needs a private pattern file absent from CI."""
    bodies = [b for b in run_commands() if "check_provenance_leak.py" in b]
    assert bodies, "leak gate is not wired into CI"
    for body in bodies:
        for line in body.splitlines():
            if "check_provenance_leak.py" in line:
                assert "--local" not in line, (
                    "the CI leak gate must run in default (weak) mode; --local "
                    "requires a private pattern file that does not exist in CI"
                )


# --------------------------------------------------------------------------- #
# Meta: the gate list itself must stay wired to reality.
# --------------------------------------------------------------------------- #

def test_referenced_test_files_exist():
    """A pinned gate that points at a deleted test would pass vacuously."""
    for name in ("test_count_leak.py", "test_install_smoke.py", "test_doc_lint.py"):
        assert os.path.isfile(os.path.join(HERE, name)), "missing tests/%s" % name


def test_referenced_tools_exist():
    for name in ("gen_rule_index.py", "gen_always_on.py", "check_provenance_leak.py"):
        assert os.path.isfile(os.path.join(REPO, "tools", name)), "missing tools/%s" % name
