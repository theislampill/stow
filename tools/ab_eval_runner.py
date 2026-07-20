#!/usr/bin/env python3
"""Runner for the enabled-versus-disabled evaluation (see tests/evals/ab/).

Executes (case, arm, rep) runs against the host CLI from a fresh scratch
directory per run, records the stream, extracts the final output and
telemetry, and applies the mechanical validators. Heavy outputs land under
--out (the governed run record), never in the repository.

Not a CI gate: this drives a live model and is run deliberately.

Modes:
  --run        execute runs for the selected cases/arms/reps
  --validate   apply mechanical validators to recorded answers
  --aggregate  compute the rubric.md spec from evaluator score files
"""

import argparse
import io
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile


def _claude_exe():
    for name in ("claude", "claude.cmd", "claude.exe"):
        path = shutil.which(name)
        if path:
            return path
    raise RuntimeError("claude CLI not found on PATH")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
AB_DIR = os.path.join(REPO, "tests", "evals", "ab")
RUNTIME = os.path.join(REPO, "skills", "stow", "runtime")

GENERAL = ["AB-%02d" % i for i in range(1, 17)]
CAPABILITY = ["AB-%02d" % i for i in range(17, 21)]

OVERCLAIM = ("fully conformant", "guarantees compliance", "certified conformance")
RFC_METHODS = ("GET", "HEAD", "POST", "PUT", "DELETE", "CONNECT", "OPTIONS",
               "TRACE", "PATCH")


def load_prompts():
    from ruamel.yaml import YAML
    with io.open(os.path.join(AB_DIR, "prompts.yaml"), encoding="utf-8") as fh:
        return YAML(typ="safe").load(fh)


def run_one(case_id, prompt, arm, rep, model, out_dir, plugin_dir):
    scratch = tempfile.mkdtemp(prefix="ab-%s-%s-%d-" % (case_id, arm, rep))
    cmd = [_claude_exe(), "--model", model, "-p", prompt,
           "--output-format", "stream-json", "--verbose"]
    if arm == "stow":
        cmd[1:1] = ["--plugin-dir", plugin_dir]
    base = os.path.join(out_dir, "%s.%s.r%d" % (case_id, arm, rep))
    with io.open(base + ".jsonl", "w", encoding="utf-8", newline="\n") as out, \
         io.open(base + ".err", "w", encoding="utf-8", newline="\n") as err:
        proc = subprocess.run(cmd, stdout=out, stderr=err, cwd=scratch,
                              text=True, timeout=600)
    return proc.returncode, base


def extract(base):
    """Final text + telemetry from a stream capture."""
    model = None
    skill = False
    validator_call = False
    final = None
    with io.open(base + ".jsonl", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if event.get("type") == "system" and event.get("subtype") == "init":
                model = event.get("model")
            elif event.get("type") == "assistant":
                for block in (event.get("message") or {}).get("content") or []:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        name = block.get("name", "")
                        blob = json.dumps(block.get("input") or {})
                        if name == "Skill" or '"skill"' in blob:
                            skill = True
                        if "validate.py" in blob or "lint_prose.py" in blob:
                            validator_call = True
            elif event.get("type") == "result":
                final = event.get("result")
    if final is not None:
        with io.open(base + ".answer.txt", "w", encoding="utf-8", newline="\n") as fh:
            fh.write(final)
    return {"model": model, "skill_invoked": skill,
            "validator_invoked": validator_call, "has_final": final is not None}


def _load_runtime(name):
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        name + "_ab", os.path.join(RUNTIME, name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _fenced_yaml(text):
    match = re.search(r"```(?:yaml)?\n(.*?)```", text, re.S)
    return match.group(1) if match else None


def validate_answer(case_id, text, validate_mod, lint_mod, tables):
    """Mechanical verdicts for one answer. Returns dict of named checks."""
    checks = {}
    lowered = text.lower()
    checks["overclaim"] = not any(p in lowered for p in OVERCLAIM)
    stripped = text.strip()
    if case_id in ("AB-09", "AB-10", "AB-11", "AB-20"):
        checks["no_fence"] = not stripped.startswith("```")
    if case_id == "AB-07":
        checks["complete"] = all(re.search(r"\b%s\b" % m, text) for m in RFC_METHODS)
    if case_id == "AB-09":
        checks["parses"] = validate_mod.validate_json(stripped).ok
    elif case_id == "AB-10":
        checks["parses"] = validate_mod.validate_jsonl(stripped).ok
    elif case_id == "AB-11":
        checks["parses"] = validate_mod.validate_yaml(stripped).ok
    elif case_id == "AB-15":
        checks["identifiers"] = ("getUserData()" in text and "get_user_data()" in text)
    elif case_id == "AB-16":
        quote = "This groundbreaking solution leverages cutting-edge synergies — truly a game-changer."
        checks["quote_exact"] = quote in text
    elif case_id in ("AB-13", "AB-14"):
        first_step = re.search(r"^\s*1[.)]", text, re.M)
        first_hazard = re.search(r"WARNING|CAUTION|DANGER", text)
        checks["hazards_before_steps"] = bool(
            first_hazard and (not first_step or first_hazard.start() < first_step.start()))
    elif case_id in ("AB-17", "AB-18", "AB-19"):
        schema = {"AB-17": "handoff", "AB-18": "plan", "AB-19": "state"}[case_id]
        body = _fenced_yaml(text)
        checks["schema_valid"] = bool(body) and validate_mod.validate_schema(schema, body).ok
    elif case_id == "AB-20":
        checks["schema_valid"] = validate_mod.validate_schema("task-packet", stripped).ok
    if case_id not in ("AB-09", "AB-10", "AB-11", "AB-20"):
        findings = lint_mod.lint(text, profile="stow-default", tables=tables)
        checks["em_dash_count"] = sum(1 for a in findings if a.rule == "em-dash")
        checks["lint_advisories"] = len(findings)
        if case_id == "AB-13":
            guided = lint_mod.lint(text, profile="controlled-technical-guided",
                                   tables=tables)
            checks["guided_advisories"] = len(guided)
    return checks


def cmd_run(args):
    data = load_prompts()
    model = data["run_contract"]["model_pin"]
    cases = args.cases.split(",") if args.cases != "all" else list(data["cases"])
    os.makedirs(args.out, exist_ok=True)
    log = io.open(os.path.join(args.out, "runs.log.jsonl"), "a",
                  encoding="utf-8", newline="\n")
    for case_id in cases:
        prompt = data["cases"][case_id]
        for arm in args.arms.split(","):
            for rep in range(1, args.reps + 1):
                rc, base = run_one(case_id, prompt, arm, rep, model,
                                   args.out, REPO)
                info = extract(base)
                if not info["has_final"]:
                    rc2, base = run_one(case_id, prompt, arm, rep, model,
                                        args.out, REPO)
                    info = extract(base)
                    info["censored_retry"] = True
                row = dict(case=case_id, arm=arm, rep=rep, rc=rc, **info)
                log.write(json.dumps(row) + "\n")
                log.flush()
                print(json.dumps(row))
    log.close()
    return 0


def cmd_validate(args):
    validate_mod = _load_runtime("validate")
    lint_mod = _load_runtime("lint_prose")
    tables = lint_mod.load_banned_lists()
    out = io.open(os.path.join(args.out, "validators.jsonl"), "w",
                  encoding="utf-8", newline="\n")
    for name in sorted(os.listdir(args.out)):
        if not name.endswith(".answer.txt"):
            continue
        case_id, arm, rep = name.split(".")[0], name.split(".")[1], name.split(".")[2]
        text = io.open(os.path.join(args.out, name), encoding="utf-8").read()
        checks = validate_answer(case_id, text, validate_mod, lint_mod, tables)
        out.write(json.dumps(dict(case=case_id, arm=arm, rep=rep, **checks)) + "\n")
    out.close()
    print("validators.jsonl written")
    return 0


def cmd_aggregate(args):
    """Implements the rubric.md computation spec from evaluator score files
    (scores.jsonl rows: {case, rep, output: X|Y, dim, score, role}) plus the
    arm mapping (mapping.json: {case.rep: {X: arm, Y: arm}})."""
    with io.open(os.path.join(args.out, "mapping.json"), encoding="utf-8") as fh:
        mapping = json.load(fh)
    scores = {}
    with io.open(os.path.join(args.out, "scores.jsonl"), encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            key = (row["case"], str(row["rep"]))
            arm = mapping["%s.r%s" % key][row["output"]]
            scores.setdefault((row["case"], arm, str(row["rep"])),
                              {}).setdefault(row["dim"], []).append(row["score"])
    def median(vals):
        vals = sorted(vals)
        n = len(vals)
        return vals[n // 2] if n % 2 else (vals[n // 2 - 1] + vals[n // 2]) / 2.0
    run_scores = {}
    for (case, arm, rep), dims in scores.items():
        dim_vals = [sum(v) / len(v) for v in dims.values()]
        run_scores.setdefault((case, arm), []).append(sum(dim_vals) / len(dim_vals))
    result = {}
    for case in GENERAL:
        m_stow = median(run_scores.get((case, "stow"), [0]))
        m_base = median(run_scores.get((case, "base"), [0]))
        result[case] = {"stow": round(m_stow, 3), "base": round(m_base, 3),
                        "delta": round(m_stow - m_base, 3)}
    deltas = [v["delta"] for v in result.values()]
    wins = sum(1 for d in deltas if d > 0)
    losses = sum(1 for d in deltas if d < 0)
    summary = {"per_case": result, "median_delta": median(deltas),
               "mean_delta": sum(deltas) / len(deltas),
               "wins": wins, "losses": losses,
               "primary_gate": median(deltas) > 0 or (
                   median(deltas) == 0 and sum(deltas) > 0 and wins > losses)}
    with io.open(os.path.join(args.out, "aggregate.json"), "w",
                 encoding="utf-8", newline="\n") as fh:
        json.dump(summary, fh, indent=1)
    print(json.dumps({k: summary[k] for k in
                      ("median_delta", "mean_delta", "wins", "losses",
                       "primary_gate")}, indent=1))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--mode", choices=["run", "validate", "aggregate"],
                        required=True)
    parser.add_argument("--out", required=True,
                        help="output directory (the governed run record)")
    parser.add_argument("--cases", default="all")
    parser.add_argument("--arms", default="stow,base")
    parser.add_argument("--reps", type=int, default=3)
    args = parser.parse_args(argv)
    if args.mode == "run":
        return cmd_run(args)
    if args.mode == "validate":
        return cmd_validate(args)
    return cmd_aggregate(args)


if __name__ == "__main__":
    sys.exit(main())
