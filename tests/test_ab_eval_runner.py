"""Focused mechanical contracts for the enabled-versus-disabled runner."""

import importlib.util
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
RUNNER_PATH = os.path.join(REPO, "tools", "ab_eval_runner.py")
VALIDATE_PATH = os.path.join(REPO, "skills", "stow", "runtime", "validate.py")


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runner = _load("ab_eval_runner_contract", RUNNER_PATH)
validate = _load("validate_for_ab_contract", VALIDATE_PATH)


def _ab11_checks(text):
    return runner.validate_answer("AB-11", text, validate, None, None)


def test_ab11_plain_yaml_scalar_does_not_count_as_parsed_contract_output():
    assert _ab11_checks("Here is the requested configuration.")["parses"] is False


def test_ab11_exact_requested_mapping_counts_as_parsed_contract_output():
    text = "image: nginx:1.25\nreplicas: 2\nenv:\n  - DEBUG=false\n"
    checks = _ab11_checks(text)
    assert checks["parses"] is True
    assert checks["no_fence"] is True


@pytest.mark.parametrize("text", [
    "- image: nginx:1.25\n- replicas: 2\n- env: [DEBUG=false]\n",
    "image: nginx:1.25\nreplicas: 2\n",
    "image: nginx:1.25\nreplicas: 2\nenv: [DEBUG=false]\nextra: value\n",
    "image: nginx:latest\nreplicas: 2\nenv: [DEBUG=false]\n",
    "image: nginx:1.25\nreplicas: '2'\nenv: [DEBUG=false]\n",
    "image: nginx:1.25\nreplicas: true\nenv: [DEBUG=false]\n",
    "image: nginx:1.25\nreplicas: 2\nenv: DEBUG=false\n",
    "image: nginx:1.25\nreplicas: 2\nenv: [DEBUG=true]\n",
    "image: nginx:1.25\nreplicas: 2\nenv: [DEBUG=false, TRACE=false]\n",
])
def test_ab11_wrong_root_shape_key_set_value_or_type_fails(text):
    assert _ab11_checks(text)["parses"] is False


def test_ab11_keeps_no_fence_as_a_separate_check():
    text = "```yaml\nimage: nginx:1.25\nreplicas: 2\nenv: [DEBUG=false]\n```\n"
    assert _ab11_checks(text)["no_fence"] is False


def test_aggregate_help_states_the_primary_summary_boundary():
    proc = subprocess.run(
        [sys.executable, RUNNER_PATH, "--help"],
        capture_output=True, text=True, cwd=REPO)
    assert proc.returncode == 0, proc.stderr
    help_text = proc.stdout.lower()
    assert "primary summary only" in help_text
    for omitted_gate in (
            "completeness", "missing-score", "regression",
            "material-improvement", "critical-invariant"):
        assert omitted_gate in help_text
