#!/usr/bin/env python3
"""Run CI checks and emit JUnit, JSON, and Markdown reports."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CheckResult:
    name: str
    category: str
    command: str
    passed: bool
    duration_seconds: float
    output: str


def parse_check(raw: str) -> tuple[str, str, str]:
    parts = raw.split("::", 2)
    if len(parts) != 3:
        raise ValueError(f"Invalid --check format: {raw!r}. Expected name::category::command")
    return parts[0].strip(), parts[1].strip(), parts[2].strip()


def run_check(name: str, category: str, command: str) -> CheckResult:
    start = time.time()
    proc = subprocess.run(command, shell=True, text=True, capture_output=True)
    duration = time.time() - start
    combined = "\n".join(part for part in [proc.stdout, proc.stderr] if part).strip()
    return CheckResult(
        name=name,
        category=category,
        command=command,
        passed=proc.returncode == 0,
        duration_seconds=duration,
        output=combined,
    )


def write_junit(results: list[CheckResult], output_path: Path, suite_name: str) -> None:
    failures = sum(1 for r in results if not r.passed)
    suite = ET.Element(
        "testsuite",
        name=suite_name,
        tests=str(len(results)),
        failures=str(failures),
        errors="0",
        skipped="0",
        time=f"{sum(r.duration_seconds for r in results):.3f}",
    )

    for result in results:
        case = ET.SubElement(
            suite,
            "testcase",
            name=result.name,
            classname=f"ci.{result.category}",
            time=f"{result.duration_seconds:.3f}",
        )
        ET.SubElement(case, "properties")
        if not result.passed:
            failure = ET.SubElement(
                case,
                "failure",
                message=(
                    f"[{result.category}] {result.name} failed. "
                    f"Run `{result.command}` locally for details."
                ),
                type=result.category,
            )
            failure.text = result.output[:12000]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(suite).write(output_path, encoding="utf-8", xml_declaration=True)


def write_json(results: list[CheckResult], output_path: Path, gate: str) -> None:
    payload = {
        "gate": gate,
        "generated_at_epoch": int(time.time()),
        "summary": {
            "total": len(results),
            "passed": sum(1 for r in results if r.passed),
            "failed": sum(1 for r in results if not r.passed),
        },
        "checks": [
            {
                "name": r.name,
                "category": r.category,
                "command": r.command,
                "status": "passed" if r.passed else "failed",
                "duration_seconds": round(r.duration_seconds, 3),
                "message": r.output[:4000],
            }
            for r in results
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_markdown(results: list[CheckResult], output_path: Path, gate: str) -> None:
    lines = [f"# CI Gate Summary: {gate}", "", "| Status | Category | Check |", "|---|---|---|"]
    for r in results:
        icon = "✅" if r.passed else "❌"
        lines.append(f"| {icon} | `{r.category}` | `{r.name}` |")

    failed = [r for r in results if not r.passed]
    if failed:
        lines.extend(["", "## Failure Guidance", ""])
        for r in failed:
            lines.append(
                f"- **{r.name}** (`{r.category}`): failed. "
                f"Run `{r.command}` locally."
            )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate", required=True)
    parser.add_argument("--report-dir", default="artifacts")
    parser.add_argument("--check", action="append", required=True)
    args = parser.parse_args()

    parsed = [parse_check(item) for item in args.check]
    results = [run_check(name, category, command) for name, category, command in parsed]

    report_dir = Path(args.report_dir)
    safe_gate = args.gate.replace("/", "_")
    write_junit(results, report_dir / f"{safe_gate}.junit.xml", args.gate)
    write_json(results, report_dir / f"{safe_gate}.report.json", args.gate)
    write_markdown(results, report_dir / f"{safe_gate}.summary.md", args.gate)

    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"[{status}] [{r.category}] {r.name}")
        if not r.passed and r.output:
            print(r.output)

    return 0 if all(r.passed for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
