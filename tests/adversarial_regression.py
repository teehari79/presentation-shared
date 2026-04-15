#!/usr/bin/env python3
"""Adversarial regression checks for orchestrator/renderer/shared CI gates."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ORCHESTRATOR_STAGES = {
    "ingestion",
    "understanding",
    "outline_generation",
    "deck_spec_generation",
    "export",
    "hitl_approval",
}
RENDERER_STAGES = {"renderer_preflight", "rendering"}

SMOKE_CASE_COUNT = 6


def load_yaml(path: Path):
    result = subprocess.run(
        [
            "ruby",
            "-ryaml",
            "-rjson",
            "-e",
            "puts JSON.generate(YAML.load_file(ARGV[0]))",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def fail(message: str) -> None:
    raise ValueError(message)


def verify_case_required_fields(case: dict, case_file: Path) -> None:
    required = [
        "id",
        "title",
        "category",
        "threat_description",
        "input_type",
        "target_workflow_stage",
        "attack_payload",
        "expected_safe_behavior",
        "severity",
        "recommended_mitigation_tags",
    ]
    missing = [key for key in required if key not in case or case[key] in (None, "", [])]
    if missing:
        fail(f"schema: {case_file} {case.get('id', '<missing-id>')} missing required fields: {missing}")


def load_cases() -> list[dict]:
    all_cases: list[dict] = []
    for case_file in sorted((ROOT / "redteam" / "cases").glob("*_v*.yaml")):
        doc = load_yaml(case_file)
        for case in doc.get("cases", []):
            verify_case_required_fields(case, case_file)
            all_cases.append(case)
    if not all_cases:
        fail("adversarial regression: no red-team cases found")

    ids = [case["id"] for case in all_cases]
    if len(ids) != len(set(ids)):
        fail("schema: duplicate red-team case ids detected")

    return sorted(all_cases, key=lambda c: c["id"])


def run_orchestrator(cases: list[dict], smoke: bool) -> tuple[list[dict], list[str]]:
    selected = [
        c
        for c in cases
        if c["target_workflow_stage"] in ORCHESTRATOR_STAGES and c["category"] != "unsafe_renderer_payload"
    ]
    if smoke:
        selected = selected[:SMOKE_CASE_COUNT]

    failures = []
    for case in selected:
        controls = set(case["expected_safe_behavior"].get("minimum_controls", []))
        accepted_controls = {
            "policy_filtering",
            "schema_validation",
            "tenant_isolation_check",
            "hitl_gate",
            "citation_verification",
            "rate_limit_or_budget_guard",
        }
        if not controls.intersection(accepted_controls):
            failures.append(
                f"policy: {case['id']} missing orchestrator guard control "
                f"(expected one of {sorted(accepted_controls)})"
            )
        if case["target_workflow_stage"] == "hitl_approval" and "hitl_gate" not in controls:
            failures.append(f"authorization: {case['id']} missing hitl_gate control")

    return selected, failures


def run_renderer(cases: list[dict]) -> tuple[list[dict], list[str]]:
    selected = [
        c
        for c in cases
        if c["category"] == "unsafe_renderer_payload" or c["target_workflow_stage"] in RENDERER_STAGES
    ]

    failures = []
    for case in selected:
        controls = set(case["expected_safe_behavior"].get("minimum_controls", []))
        if "renderer_sanitization" not in controls:
            failures.append(f"renderer safety: {case['id']} missing renderer_sanitization control")

    render_plan = json.loads((ROOT / "examples" / "render-plan.sample.json").read_text(encoding="utf-8"))
    required_top_level = {"theme_id", "strict_corporate_mode", "density_preference", "slides"}
    missing = sorted(required_top_level - set(render_plan.keys()))
    if missing:
        failures.append(f"renderer safety: deterministic render validation missing keys: {missing}")

    return selected, failures


def run_shared(cases: list[dict]) -> tuple[list[dict], list[str]]:
    failures: list[str] = []

    rubrics = list((ROOT / "redteam" / "rubrics").glob("*_v*.yaml"))
    if not rubrics:
        failures.append("policy: no red-team rubrics found")

    datasets = list((ROOT / "redteam" / "datasets").glob("*_v*.yaml"))
    if not datasets:
        failures.append("schema: no red-team datasets found")

    if len(cases) < 25:
        failures.append("adversarial regression: expected at least 25 versioned red-team cases")

    return cases, failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", choices=["orchestrator-smoke", "orchestrator-full", "renderer", "shared"], required=True)
    parser.add_argument("--json-out")
    args = parser.parse_args()

    cases = load_cases()
    if args.target == "orchestrator-smoke":
        selected, failures = run_orchestrator(cases, smoke=True)
    elif args.target == "orchestrator-full":
        selected, failures = run_orchestrator(cases, smoke=False)
    elif args.target == "renderer":
        selected, failures = run_renderer(cases)
    else:
        selected, failures = run_shared(cases)

    payload = {
        "target": args.target,
        "selected_case_count": len(selected),
        "selected_case_ids": [c["id"] for c in selected],
        "status": "passed" if not failures else "failed",
        "failures": failures,
    }

    if args.json_out:
        output = Path(args.json_out)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if failures:
        print(f"{args.target} failed with {len(failures)} issue(s):")
        for item in failures:
            print(f" - {item}")
        return 1

    print(f"{args.target} passed ({len(selected)} cases checked)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
