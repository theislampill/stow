"""R0001 SkillStore admission contract.

This suite binds the public skill metadata, licence topology, executable-helper
inventory, deterministic package, scoped submission identity, release-candidate
version, and hosted-CI controls.  The checks are repository-native so a future
edit cannot silently remove one layer while leaving another apparently green.

The material mutation table at the end proves that each admission oracle can
observe the failure it is meant to block.  It mutates disposable copies only.
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

import pytest
from ruamel.yaml import YAML

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
SKILL_DIR = REPO / "skills" / "stow"
SKILL_PATH = SKILL_DIR / "SKILL.md"
WORKFLOW = REPO / ".github" / "workflows" / "verify.yml"
EXPECTED_VERSION = "0.4.2"
EXPECTED_RUNTIME = {
    "dictionary_lookup.py",
    "lint_prose.py",
    "profiles.py",
    "query_rules.py",
    "validate.py",
    "validate_terms.py",
}
SCOPED_SOURCE = "https://github.com/theislampill/stow/tree/main/skills/stow"
RELEASE_SCOPED_SOURCE = "https://github.com/theislampill/stow/tree/v0.4.2/skills/stow"


# --------------------------------------------------------------------------- #
# Shared readers and loaders
# --------------------------------------------------------------------------- #

def _read(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")


def _bytes(root: Path, rel: str) -> bytes:
    return (root / rel).read_bytes()


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _frontmatter(root: Path) -> tuple[dict, str]:
    text = _read(root, "skills/stow/SKILL.md")
    match = re.match(r"\A---\n(.*?)\n---\n", text, re.DOTALL)
    assert match, "SKILL.md must start with one YAML frontmatter block"
    data = YAML(typ="safe").load(match.group(1))
    assert isinstance(data, dict), "SKILL.md frontmatter must parse to a mapping"
    return data, text


def _workflow(root: Path) -> tuple[dict, str]:
    text = _read(root, ".github/workflows/verify.yml")
    data = YAML(typ="safe").load(text)
    assert isinstance(data, dict), "verify.yml must parse to a mapping"
    return data, text


def _all_steps(workflow: dict) -> list[dict]:
    found: list[dict] = []
    for job in (workflow.get("jobs") or {}).values():
        found.extend((job or {}).get("steps") or [])
    return found


def _load_build(root: Path):
    return _load_module(
        "build_skill_admission_%s" % hashlib.sha1(str(root).encode()).hexdigest()[:12],
        root / "tools" / "build_skill.py",
    )


def _load_measure(root: Path):
    return _load_module(
        "measure_context_admission_%s" % hashlib.sha1(str(root).encode()).hexdigest()[:12],
        root / "tools" / "measure_context.py",
    )


# --------------------------------------------------------------------------- #
# Admission oracles
# --------------------------------------------------------------------------- #

def _check_frontmatter(root: Path) -> None:
    frontmatter, _text = _frontmatter(root)
    assert frontmatter.get("name") == "stow"

    description = frontmatter.get("description")
    assert isinstance(description, str) and description.strip()
    assert len(description) <= 1024
    assert "Use when" in description, "description needs explicit activation language"
    for cue in (
        "README", "runbook", "procedure", "audit", "handoff",
        "JSON", "JSONL", "YAML", "Markdown",
    ):
        assert cue in description, "description is missing activation cue %r" % cue
    assert "exact output contracts" in description
    assert frontmatter.get("license") == "LICENSE"
    licence_path = (root / "skills" / "stow" / frontmatter["license"]).resolve()
    skill_root = (root / "skills" / "stow").resolve()
    assert licence_path.parent == skill_root, "license must resolve inside the scoped skill"
    assert licence_path.is_file(), "frontmatter license path does not exist"

    compatibility = frontmatter.get("compatibility")
    assert isinstance(compatibility, str) and compatibility.strip()
    assert len(compatibility) <= 500
    for fact in (
        "Agent Skills-compatible hosts",
        "CPython 3.11",
        "ruamel.yaml>=0.19.1",
        "jsonschema>=4.26.0",
        "Installation alone runs no helper",
    ):
        assert fact in compatibility, "compatibility is missing evidenced fact %r" % fact
    assert not re.search(
        r"\b(?:all hosts|any host|universal(?:ly)?|Claude\.ai|Cursor|Windsurf)\b",
        compatibility,
        re.IGNORECASE,
    ), "compatibility contains an unsupported host or universal claim"

    metadata = frontmatter.get("metadata")
    assert isinstance(metadata, dict) and metadata
    assert metadata == {"author": "theislampill", "version": EXPECTED_VERSION}
    assert all(isinstance(key, str) and isinstance(value, str)
               for key, value in metadata.items())

    plugin = json.loads(_read(root, ".claude-plugin/plugin.json"))
    assert metadata["version"] == plugin["version"]


def _check_kernel_budget(root: Path) -> None:
    _frontmatter_data, text = _frontmatter(root)
    assert len(text.splitlines()) < 500
    measure = _load_measure(root)
    fallback = measure.estimate_tokens(text)
    assert fallback <= 1500, "fallback kernel estimate %d exceeds 1500" % fallback
    assert "## 7. Complete example" in text
    assert "Input:" in text and "Output:" in text


def _check_licences(root: Path) -> None:
    root_path = root / "LICENSE"
    scoped_path = root / "skills" / "stow" / "LICENSE"
    assert root_path.is_file(), "root LICENSE is missing"
    assert scoped_path.is_file(), "scoped skill LICENSE is missing"
    root_bytes = root_path.read_bytes()
    scoped_bytes = scoped_path.read_bytes()
    assert root_bytes == scoped_bytes, "root and scoped licence bytes differ"
    text = root_bytes.decode("utf-8")
    for clause in (
        "MIT License",
        "Copyright (c) 2026 theislampill",
        "Permission is hereby granted, free of charge",
        'THE SOFTWARE IS PROVIDED "AS IS"',
    ):
        assert clause in text, "MIT licence text is missing %r" % clause

    assert not (root / "THIRD_PARTY_NOTICES.md").exists()
    assert not (root / "skills" / "stow" / "THIRD_PARTY_NOTICES.md").exists()


def _call_name(node: ast.Call) -> str:
    parts: list[str] = []
    current = node.func
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
    return ".".join(reversed(parts))


def _open_mode(node: ast.Call) -> str | None:
    if not node.args and not node.keywords:
        return None
    mode_node = node.args[1] if len(node.args) > 1 else None
    for keyword in node.keywords:
        if keyword.arg == "mode":
            mode_node = keyword.value
    if isinstance(mode_node, ast.Constant) and isinstance(mode_node.value, str):
        return mode_node.value
    return None


def _runtime_effect_findings(root: Path) -> list[str]:
    forbidden_import_roots = {
        "aiohttp", "asyncio", "ftplib", "http", "multiprocessing", "requests",
        "socket", "smtplib", "subprocess", "telnetlib", "urllib",
    }
    forbidden_calls = {
        "os.system", "os.popen", "os.spawnl", "os.spawnle", "os.spawnlp",
        "os.spawnlpe", "os.spawnv", "os.spawnve", "os.spawnvp", "os.spawnvpe",
        "os.remove", "os.unlink", "os.rename", "os.replace", "os.mkdir",
        "os.makedirs", "os.rmdir", "os.removedirs",
    }
    write_methods = {
        "write_text", "write_bytes", "touch", "mkdir", "unlink", "rename",
        "rmdir",
    }
    findings: list[str] = []
    runtime = root / "skills" / "stow" / "runtime"
    for path in sorted(runtime.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".", 1)[0] in forbidden_import_roots:
                        findings.append("%s imports %s" % (path.name, alias.name))
            elif isinstance(node, ast.ImportFrom):
                root_name = (node.module or "").split(".", 1)[0]
                if root_name in forbidden_import_roots:
                    findings.append("%s imports from %s" % (path.name, node.module))
            elif isinstance(node, ast.Attribute):
                if (isinstance(node.value, ast.Name) and node.value.id == "os"
                        and node.attr == "environ"):
                    findings.append("%s reads os.environ" % path.name)
            elif isinstance(node, ast.Call):
                name = _call_name(node)
                if name in {"os.getenv", "getenv"}:
                    findings.append("%s reads environment variables" % path.name)
                if name in forbidden_calls or name.startswith("subprocess."):
                    findings.append("%s calls %s" % (path.name, name))
                if name.rsplit(".", 1)[-1] in write_methods:
                    findings.append("%s calls write-capable %s" % (path.name, name))
                if name.rsplit(".", 1)[-1] == "open":
                    mode = _open_mode(node)
                    if mode and any(marker in mode for marker in "wax+"):
                        findings.append("%s opens a file with mode %s" % (path.name, mode))
    return findings


def _check_runtime(root: Path) -> None:
    runtime = root / "skills" / "stow" / "runtime"
    actual = {path.name for path in runtime.glob("*.py")}
    assert actual == EXPECTED_RUNTIME, "runtime module population changed: %r" % actual
    build = _load_build(root)
    assert set(build.RUNTIME_ALLOW) == EXPECTED_RUNTIME
    assert _runtime_effect_findings(root) == []

    requirements = _read(root, "requirements-runtime.txt")
    assert "validate.py" in requirements
    for name in EXPECTED_RUNTIME - {"validate.py"}:
        assert name in requirements, "dependency note omits %s" % name
    assert "standard-library only" in requirements

    readme = _read(root, "README.md")
    normalized = " ".join(readme.replace("`", "").split()).casefold()
    for phrase in (
        "runtime/ is stow's named executable-helper directory",
        "agent skills format permits additional directories",
        "every packaged python file receives the same security treatment",
        "installation alone runs no helper",
        "no packaged helper opens a network connection, starts a subprocess, reads environment variables, or writes files",
    ):
        assert phrase in normalized, "README runtime disclosure misses %r" % phrase
    for name in EXPECTED_RUNTIME:
        assert "`runtime/%s`" % name in readme, "README inventory omits %s" % name
    for heading in ("Inputs", "Outputs", "Dependencies", "Effects", "Evidence ceiling"):
        assert heading in readme, "README runtime table omits %s" % heading


def _submission_section(root: Path) -> str:
    readme = _read(root, "README.md")
    match = re.search(
        r"<!-- SKILLSTORE-SUBMISSION:BEGIN -->(.*?)"
        r"<!-- SKILLSTORE-SUBMISSION:END -->",
        readme,
        re.DOTALL,
    )
    assert match, "README lacks the bounded SkillStore submission section"
    return match.group(1)


def _check_submission_docs(root: Path) -> None:
    section = _submission_section(root)
    assert SCOPED_SOURCE in section
    assert RELEASE_SCOPED_SOURCE in section
    assert "Do not submit the repository root" in section
    assert "Do not submit `dist/STOW.skill`" in section
    assert "generated release artefact" in section
    assert "has not yet been submitted" in section
    assert "not a universal safety certificate" in " ".join(section.split())


def _changelog_candidate_version(root: Path) -> str:
    changelog = _read(root, "CHANGELOG.md")
    match = re.search(r"^## \[((?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*))\] - Unreleased$",
                      changelog, re.MULTILINE)
    assert match, "CHANGELOG needs an unreleased candidate-version heading"
    return match.group(1)


def _check_version(root: Path) -> None:
    plugin = json.loads(_read(root, ".claude-plugin/plugin.json"))
    frontmatter, _text = _frontmatter(root)
    manifest = json.loads(_read(root, "dist/manifest.json"))
    assert plugin["version"] == EXPECTED_VERSION
    assert frontmatter["metadata"]["version"] == EXPECTED_VERSION
    assert manifest["version"] == EXPECTED_VERSION
    assert _changelog_candidate_version(root) == EXPECTED_VERSION
    readme = _read(root, "README.md")
    assert "Prepared release candidate: **v%s**" % EXPECTED_VERSION in readme
    assert "Current published release: **[v0.4.1]" in readme
    assert "v0.4.2 has not been released" in readme


def _lock_blocks(text: str) -> list[list[str]]:
    blocks: list[list[str]] = []
    current: list[str] = []
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw[:1].isspace():
            assert current, "lock continuation appears before a requirement"
            current.append(raw.strip())
            continue
        if current:
            blocks.append(current)
        current = [raw.strip()]
    if current:
        blocks.append(current)
    return blocks


def _check_ci(root: Path) -> None:
    workflow, raw = _workflow(root)
    assert workflow.get("permissions") == {"contents": "read"}
    assert "${{ secrets." not in raw
    assert "python -m pip install --upgrade pip" not in raw
    assert "ubuntu-latest" not in raw

    jobs = workflow.get("jobs") or {}
    assert jobs, "workflow has no jobs"
    verify = jobs.get("verify")
    assert isinstance(verify, dict), "workflow must keep the verify job"
    assert verify.get("runs-on") == "ubuntu-24.04"
    assert isinstance(verify.get("timeout-minutes"), int)
    assert 1 <= verify["timeout-minutes"] <= 60

    steps = _all_steps(workflow)
    assert steps
    for step in steps:
        assert step.get("continue-on-error") is not True, (
            "blocking step %r is softened" % step.get("name"))

    use_lines = re.findall(r"^\s*-?\s*uses:\s*([^@\s]+)@([^\s#]+)(?:\s+#\s*(.+))?$",
                           raw, re.MULTILINE)
    assert use_lines, "workflow has no external actions"
    for action, ref, comment in use_lines:
        if action.startswith("./"):
            continue
        assert re.fullmatch(r"[0-9a-f]{40}", ref), "%s is not SHA-pinned" % action
        assert comment and re.search(r"\bv\d", comment), (
            "%s pin needs a human-readable release comment" % action)

    checkout = next(step for step in steps
                    if str(step.get("uses", "")).startswith("actions/checkout@"))
    assert (checkout.get("with") or {}).get("persist-credentials") is False

    setup = next(step for step in steps
                 if str(step.get("uses", "")).startswith("actions/setup-python@"))
    assert str((setup.get("with") or {}).get("python-version")) == "3.11.15"

    install_steps = [step for step in steps if step.get("name") == "Install locked dependencies"]
    assert len(install_steps) == 1
    install_body = str(install_steps[0].get("run", ""))
    assert "python -m pip install --require-hashes" in install_body
    assert "-r requirements-ci.lock" in install_body
    assert "pip install ruamel.yaml" not in raw

    installer = next((step for step in steps
                      if step.get("name") == "Verify interpreter and installer identity"), None)
    assert installer is not None
    installer_body = str(installer.get("run", ""))
    for phrase in ("Python 3.11.15", "pip --version | awk", "26.2.1"):
        assert phrase in installer_body

    identity = next((step for step in steps
                     if step.get("name") == "Record verification identities"), None)
    assert identity is not None
    identity_body = str(identity.get("run", ""))
    for phrase in (
        "python --version", "python -m pip --version",
        "python -m pip freeze --all", "sha256sum requirements-ci.lock",
    ):
        assert phrase in identity_body

    admission = [step for step in steps if step.get("name") == "SkillStore admission gate"]
    assert len(admission) == 1
    body = str(admission[0].get("run", ""))
    assert re.search(r"python -m pytest\s+tests/test_skillstore_admission\.py\s+-q", body)
    env = admission[0].get("env") or {}
    assert str(env.get("STOW_REQUIRE_EXACT_TOKENS")) == "1"

    lock = _read(root, "requirements-ci.lock")
    for marker in (
        "Generated for CPython 3.11.15 on ubuntu-24.04",
        "Review procedure:",
        "pip-compile",
    ):
        assert marker in lock
    blocks = _lock_blocks(lock)
    assert blocks, "requirements-ci.lock has no requirements"
    for block in blocks:
        requirement = block[0].rstrip("\\").strip()
        assert re.match(r"^[A-Za-z0-9_.-]+==[^\s\\]+", requirement), (
            "CI requirement is not exactly pinned: %r" % block[0])
        joined = " ".join(block)
        assert "--hash=sha256:" in joined, "CI requirement lacks a SHA-256 hash"

    doc_lint = _read(root, "tests/test_doc_lint.py")
    assert "tests/test_skillstore_admission.py" in doc_lint
    assert "SkillStore admission gate" in doc_lint


def _check_package(root: Path) -> None:
    build = _load_build(root)
    with tempfile.TemporaryDirectory(prefix="stow-admission-build-") as temp:
        result = build.build(root=str(root), out_dir=temp)
        committed = _bytes(root, "dist/STOW.skill")
        rebuilt = Path(result["artifact_path"]).read_bytes()
        if committed != rebuilt:
            raise AssertionError(
                "committed package is stale: committed=%s rebuilt=%s"
                % (hashlib.sha256(committed).hexdigest(),
                   hashlib.sha256(rebuilt).hexdigest()))
        committed_sidecar = _bytes(root, "dist/STOW.skill.sha256")
        rebuilt_sidecar = Path(result["sha256_path"]).read_bytes()
        if committed_sidecar != rebuilt_sidecar:
            raise AssertionError("committed package sidecar is stale")
        committed_manifest = _bytes(root, "dist/manifest.json")
        rebuilt_manifest = Path(result["manifest_path"]).read_bytes()
        if committed_manifest != rebuilt_manifest:
            raise AssertionError("committed package manifest is stale")

    manifest = json.loads(_read(root, "dist/manifest.json"))
    assert manifest["artifact_sha256"] == hashlib.sha256(
        _bytes(root, "dist/STOW.skill")).hexdigest()
    assert manifest["entry_count"] == len(manifest["entries"])
    assert "stow/LICENSE" in manifest["entries"]
    assert not any("THIRD_PARTY_NOTICES" in entry for entry in manifest["entries"])

    with zipfile.ZipFile(root / "dist" / "STOW.skill") as archive:
        names = archive.namelist()
        assert {name.split("/", 1)[0] for name in names} == {"stow"}
        assert "stow/LICENSE" in names
        assert archive.read("stow/LICENSE") == _bytes(root, "skills/stow/LICENSE")
        runtime = {Path(name).name for name in names if name.startswith("stow/runtime/")}
        assert runtime == EXPECTED_RUNTIME


def _check_weak_provenance(root: Path) -> None:
    proc = subprocess.run(
        [sys.executable, str(root / "tools" / "check_provenance_leak.py"), "--tree"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "LEAK CHECK PASSED" in proc.stdout


def _check_all(root: Path) -> None:
    _check_frontmatter(root)
    _check_kernel_budget(root)
    _check_licences(root)
    _check_runtime(root)
    _check_submission_docs(root)
    _check_version(root)
    _check_ci(root)
    _check_package(root)
    _check_weak_provenance(root)


# --------------------------------------------------------------------------- #
# Candidate acceptance tests
# --------------------------------------------------------------------------- #

def test_frontmatter_and_activation_contract():
    _check_frontmatter(REPO)


def test_kernel_budget_and_complete_example():
    _check_kernel_budget(REPO)


def test_exact_kernel_budget_when_required():
    _frontmatter_data, text = _frontmatter(REPO)
    measure = _load_measure(REPO)
    encoder = measure.get_encoder()
    if encoder is None:
        if os.environ.get("STOW_REQUIRE_EXACT_TOKENS") == "1":
            pytest.fail("exact o200k_base token gate required but cache is unavailable")
        pytest.skip("exact tokenizer cache unavailable; fallback ceiling still enforced")
    exact = measure.count_tokens(text, encoder=encoder)
    assert exact <= 1500, "exact kernel count %d exceeds 1500" % exact


def test_mit_licence_topology_and_parity():
    _check_licences(REPO)


def test_runtime_inventory_effects_and_public_disclosure():
    _check_runtime(REPO)


def test_scoped_submission_identity_is_unambiguous():
    _check_submission_docs(REPO)


def test_release_candidate_version_coherence():
    _check_version(REPO)


def test_hosted_ci_is_immutable_and_hash_locked():
    _check_ci(REPO)


def test_deterministic_package_carries_the_scoped_licence():
    _check_package(REPO)


def test_weak_provenance_backstop_covers_the_candidate_tree():
    _check_weak_provenance(REPO)


# --------------------------------------------------------------------------- #
# Material mutation controls
# --------------------------------------------------------------------------- #

def _copy_candidate(destination: Path) -> Path:
    ignore = shutil.ignore_patterns(".git", ".pytest_cache", "__pycache__", "*.pyc")
    shutil.copytree(REPO, destination, ignore=ignore)
    return destination


def _rewrite_frontmatter(root: Path, mutate) -> None:
    data, text = _frontmatter(root)
    mutate(data)
    end = text.index("\n---\n", 4) + len("\n---\n")
    yaml = YAML()
    yaml.default_flow_style = False
    from io import StringIO
    sink = StringIO()
    yaml.dump(data, sink)
    replacement = "---\n" + sink.getvalue() + "---\n"
    (root / "skills" / "stow" / "SKILL.md").write_text(
        replacement + text[end:], encoding="utf-8", newline="\n")


def _remove_admission_step(root: Path) -> None:
    workflow, _raw = _workflow(root)
    steps = workflow["jobs"]["verify"]["steps"]
    workflow["jobs"]["verify"]["steps"] = [
        step for step in steps if step.get("name") != "SkillStore admission gate"
    ]
    yaml = YAML()
    with (root / ".github" / "workflows" / "verify.yml").open(
            "w", encoding="utf-8", newline="\n") as handle:
        yaml.dump(workflow, handle)


def _soften_admission_step(root: Path) -> None:
    workflow, _raw = _workflow(root)
    step = next(step for step in workflow["jobs"]["verify"]["steps"]
                if step.get("name") == "SkillStore admission gate")
    step["continue-on-error"] = True
    yaml = YAML()
    with (root / ".github" / "workflows" / "verify.yml").open(
            "w", encoding="utf-8", newline="\n") as handle:
        yaml.dump(workflow, handle)


def _mutable_action(root: Path) -> None:
    path = root / ".github" / "workflows" / "verify.yml"
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"actions/checkout@[0-9a-f]{40}", "actions/checkout@v4", text, count=1)
    path.write_text(text, encoding="utf-8", newline="\n")


def _submission_root_mutant(root: Path) -> None:
    path = root / "README.md"
    text = path.read_text(encoding="utf-8")
    text = text.replace(SCOPED_SOURCE, "https://github.com/theislampill/stow", 1)
    path.write_text(text, encoding="utf-8", newline="\n")


def _submission_dist_mutant(root: Path) -> None:
    path = root / "README.md"
    text = path.read_text(encoding="utf-8")
    text = text.replace(SCOPED_SOURCE, "dist/STOW.skill", 1)
    path.write_text(text, encoding="utf-8", newline="\n")


def _private_marker_mutant(root: Path) -> None:
    marker = "provenance" + "-private"
    (root / "docs" / "private-marker-mutant.txt").write_text(
        marker + "\n", encoding="utf-8")


MUTANTS = (
    ("M01-root-license-deleted", _check_licences,
     lambda root: (root / "LICENSE").unlink()),
    ("M02-scoped-license-deleted", _check_licences,
     lambda root: (root / "skills" / "stow" / "LICENSE").unlink()),
    ("M03-license-byte-drift", _check_licences,
     lambda root: (root / "skills" / "stow" / "LICENSE").write_bytes(
         (root / "skills" / "stow" / "LICENSE").read_bytes() + b"\n")),
    ("M04-frontmatter-license-missing", _check_frontmatter,
     lambda root: _rewrite_frontmatter(root, lambda data: data.__setitem__("license", "MISSING"))),
    ("M05-generic-description", _check_frontmatter,
     lambda root: _rewrite_frontmatter(root, lambda data: data.__setitem__(
         "description", "Apply STOW to responses and output contracts."))),
    ("M06-description-over-limit", _check_frontmatter,
     lambda root: _rewrite_frontmatter(root, lambda data: data.__setitem__(
         "description", "Use when " + ("x" * 1100)))),
    ("M07-unsupported-host-claim", _check_frontmatter,
     lambda root: _rewrite_frontmatter(root, lambda data: data.__setitem__(
         "compatibility", data["compatibility"] + " Works universally on all hosts."))),
    ("M08-non-string-metadata", _check_frontmatter,
     lambda root: _rewrite_frontmatter(root, lambda data: data["metadata"].__setitem__(
         "version", 402))),
    ("M09-version-mismatch", _check_version,
     lambda root: (root / ".claude-plugin" / "plugin.json").write_text(
         json.dumps({**json.loads(_read(root, ".claude-plugin/plugin.json")),
                     "version": "9.9.9"}, indent=2) + "\n", encoding="utf-8")),
    ("M11-kernel-over-budget", _check_kernel_budget,
     lambda root: (root / "skills" / "stow" / "SKILL.md").write_text(
         _read(root, "skills/stow/SKILL.md") + ("x" * 6000), encoding="utf-8")),
    ("M12-undocumented-runtime", _check_runtime,
     lambda root: (root / "skills" / "stow" / "runtime" / "seventh.py").write_text(
         "print('unexpected')\n", encoding="utf-8")),
    ("M13-network-runtime", _check_runtime,
     lambda root: (root / "skills" / "stow" / "runtime" / "profiles.py").write_text(
         _read(root, "skills/stow/runtime/profiles.py") + "\nimport socket\n", encoding="utf-8")),
    ("M14-runtime-write", _check_runtime,
     lambda root: (root / "skills" / "stow" / "runtime" / "profiles.py").write_text(
         _read(root, "skills/stow/runtime/profiles.py")
         + "\nfrom pathlib import Path\nPath('unexpected').write_text('x')\n",
         encoding="utf-8")),
    ("M15-stale-dist", _check_package,
     lambda root: (root / "skills" / "stow" / "SKILL.md").write_text(
         _read(root, "skills/stow/SKILL.md") + "\n", encoding="utf-8")),
    ("M16-mutable-action", _check_ci, _mutable_action),
    ("M17-unpinned-ci-dependency", _check_ci,
     lambda root: (root / "requirements-ci.lock").write_text(
         _read(root, "requirements-ci.lock") + "\nexample>=1\n", encoding="utf-8")),
    ("M18-hash-check-removed", _check_ci,
     lambda root: (root / "requirements-ci.lock").write_text(
         _read(root, "requirements-ci.lock").replace("--hash=sha256:", "--digest=sha256:"),
         encoding="utf-8")),
    ("M19-admission-step-removed", _check_ci, _remove_admission_step),
    ("M20-admission-step-softened", _check_ci, _soften_admission_step),
    ("M21-root-submission", _check_submission_docs, _submission_root_mutant),
    ("M22-dist-submission", _check_submission_docs, _submission_dist_mutant),
    ("M23-private-surface", _check_weak_provenance, _private_marker_mutant),
)


@pytest.mark.parametrize("_label,oracle,mutate", MUTANTS, ids=[item[0] for item in MUTANTS])
def test_material_mutant_is_rejected(tmp_path, _label, oracle, mutate):
    root = _copy_candidate(tmp_path / "candidate")
    oracle(root)  # candidate must pass the same oracle before mutation
    mutate(root)
    with pytest.raises(AssertionError):
        oracle(root)
