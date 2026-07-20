"""Runtime dependency failure behavior for the shipped validator.

skills/stow/runtime/validate.py is the only shipped runtime module that imports
third-party packages (ruamel.yaml, jsonschema). When either is absent the CLI
must fail with one concise install instruction and a stable exit code, not an
opaque ImportError traceback. Uninstalling a package inside the test run is
fragile, so this exercises the error-path helpers directly.
"""

import importlib.util
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
VALIDATE = os.path.join(REPO, "skills", "stow", "runtime", "validate.py")
REQUIREMENTS = os.path.join(REPO, "requirements-runtime.txt")


def _load():
    spec = importlib.util.spec_from_file_location("validate_under_test", VALIDATE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validate = _load()


def test_requirements_file_names_both_packages():
    assert os.path.isfile(REQUIREMENTS), "requirements-runtime.txt is missing"
    with open(REQUIREMENTS, encoding="utf-8") as fh:
        text = fh.read().lower()
    assert "ruamel.yaml" in text
    assert "jsonschema" in text


def test_missing_dependency_message_is_actionable():
    msg = validate.missing_dependency_message(ImportError("no module named jsonschema"))
    assert "pip install" in msg
    assert "requirements-runtime.txt" in msg
    # The concrete package names are also spelled out for the manual path.
    assert "ruamel.yaml" in msg and "jsonschema" in msg


def test_direct_install_is_primary_over_requirements_file():
    """A package-only user (no repository checkout) is given the direct install
    first; the requirements-runtime.txt file is the checkout alternative and is
    mentioned after it."""
    msg = validate.missing_dependency_message(ImportError("no module named ruamel"))
    assert "pip install ruamel.yaml jsonschema" in msg
    assert msg.index("pip install ruamel.yaml jsonschema") < msg.index(
        "requirements-runtime.txt")


def test_dependency_exit_returns_stable_code_3():
    sink = io.StringIO()
    code = validate.dependency_exit(ImportError("simulated"), stream=sink)
    assert code == 3
    assert validate.MISSING_DEPENDENCY_EXIT == 3
    # The instruction is written to the provided stream, not swallowed.
    assert "pip install" in sink.getvalue()


def test_dependency_exit_used_by_main_when_import_failed(monkeypatch):
    """If the guarded import failed at load time, main() short-circuits to the
    dependency exit before argument parsing, so a missing package never reaches
    a raw traceback."""
    monkeypatch.setattr(validate, "_IMPORT_ERROR", ImportError("simulated absent dep"))
    assert validate.main(["--format", "json", "nonexistent.json"]) == 3
