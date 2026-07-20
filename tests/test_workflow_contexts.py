"""GitHub expression-context placement gate for workflow files.

GitHub rejects a workflow BEFORE any job runs when an expression names a
context that is unavailable where it appears. The concrete class this gate
covers: the ``runner`` context is not available under ``jobs.<job_id>.env``
(GitHub parses the job-level env before a runner is assigned), while the same
``${{ runner.temp }}`` expression is valid in step-level ``with:``, ``env:``,
and ``run:`` positions. Ordinary YAML parsing cannot catch this -- the file is
valid YAML either way -- which is exactly how an invalid workflow shipped once:
the local suite parsed it happily and GitHub refused it with

    Unrecognized named-value: 'runner'. ... within expression: runner.temp

This gate is NOT a general workflow validator (actionlint is the semantic
gate); it pins the one context-placement class that already bit, with RED and
GREEN fixtures, and scans every real workflow file. No network access.
"""

import io
import os

import pytest
from ruamel.yaml import YAML

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
WORKFLOWS_DIR = os.path.join(REPO, ".github", "workflows")

FORBIDDEN_MARKER = "${{ runner."


def _load_yaml(text):
    return YAML(typ="safe").load(io.StringIO(text))


def job_level_runner_refs(doc):
    """Return [(job_id, env_key, value)] for every jobs.<job>.env value that
    references the runner context. These are exactly the placements GitHub
    rejects at workflow parse."""
    findings = []
    for job_id, job in ((doc or {}).get("jobs") or {}).items():
        env = (job or {}).get("env") or {}
        if not isinstance(env, dict):
            continue
        for key, value in env.items():
            if isinstance(value, str) and FORBIDDEN_MARKER in value:
                findings.append((job_id, key, value))
    return findings


def workflow_files():
    if not os.path.isdir(WORKFLOWS_DIR):
        return []
    return sorted(
        os.path.join(WORKFLOWS_DIR, name)
        for name in os.listdir(WORKFLOWS_DIR)
        if name.endswith((".yml", ".yaml"))
    )


# --------------------------------------------------------------------------- #
# Fixtures: the detector itself must be RED on the broken shape and GREEN on
# the repaired shape, or the live-file scan below proves nothing.
# --------------------------------------------------------------------------- #

# The shape GitHub rejected (job-level env referencing the runner context).
INVALID_FIXTURE = """
name: broken
on: push
jobs:
  verify:
    runs-on: ubuntu-latest
    env:
      TIKTOKEN_CACHE_DIR: ${{ runner.temp }}/tiktoken-cache
    steps:
      - name: Noop
        run: "true"
"""

# The repaired design: the runner context appears only at step level (a cache
# action's `with:`, a step `env:`, a `run:` body writing GITHUB_ENV).
VALID_FIXTURE = """
name: repaired
on: push
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - name: Configure tokenizer cache directory
        shell: bash
        run: echo "TIKTOKEN_CACHE_DIR=$RUNNER_TEMP/tiktoken-cache" >> "$GITHUB_ENV"
      - name: Restore the tokenizer cache
        uses: actions/cache@v4
        with:
          path: ${{ runner.temp }}/tiktoken-cache
          key: cache-key
      - name: Step-level env is a valid runner-context position
        env:
          SCRATCH: ${{ runner.temp }}/scratch
        run: echo "$SCRATCH"
"""


def test_detector_flags_the_invalid_fixture():
    findings = job_level_runner_refs(_load_yaml(INVALID_FIXTURE))
    assert findings == [
        ("verify", "TIKTOKEN_CACHE_DIR", "${{ runner.temp }}/tiktoken-cache")
    ]


def test_detector_passes_the_valid_fixture():
    assert job_level_runner_refs(_load_yaml(VALID_FIXTURE)) == []


# --------------------------------------------------------------------------- #
# Live scan: every real workflow file.
# --------------------------------------------------------------------------- #

def test_there_are_workflow_files_to_scan():
    assert workflow_files(), "no workflow files found under .github/workflows/"


@pytest.mark.parametrize("path", workflow_files(),
                         ids=[os.path.basename(p) for p in workflow_files()])
def test_no_job_level_env_references_the_runner_context(path):
    with open(path, encoding="utf-8") as fh:
        doc = _load_yaml(fh.read())
    findings = job_level_runner_refs(doc)
    assert findings == [], (
        "%s uses the runner context in jobs.<job>.env, which GitHub rejects "
        "at workflow parse (move it to a step: write GITHUB_ENV from a run "
        "step, or use a step-level with:/env: position): %r"
        % (os.path.basename(path), findings))
