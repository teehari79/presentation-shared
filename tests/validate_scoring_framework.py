#!/usr/bin/env python3
"""Validate scoring framework config structure and guardrails."""

from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "quality" / "scoring_framework_v1.yaml"

REQUIRED_COMPONENTS = {
    "schema_validity",
    "support_grounding_quality",
    "first_pass_acceptance",
    "clarification_count",
    "regenerate_count",
    "explicit_user_rating",
    "latency_efficiency",
    "cost_efficiency",
}
REQUIRED_STAGES = {
    "understanding",
    "outline",
    "deck_spec",
    "formatting",
    "retrieval_reranking",
}


def load_yaml(path: Path):
    ruby = (
        "require 'yaml';require 'json';"
        f"data=YAML.load_file('{path.as_posix()}');"
        "puts JSON.generate(data)"
    )
    result = subprocess.run(["ruby", "-e", ruby], capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def assert_weights(name: str, weights: dict[str, float]) -> None:
    missing = REQUIRED_COMPONENTS - set(weights.keys())
    if missing:
        raise ValueError(f"profile '{name}' missing weights for: {sorted(missing)}")

    extras = set(weights.keys()) - REQUIRED_COMPONENTS
    if extras:
        raise ValueError(f"profile '{name}' has unknown weight keys: {sorted(extras)}")

    total = sum(float(v) for v in weights.values())
    if not math.isclose(total, 1.0, abs_tol=1e-6):
        raise ValueError(f"profile '{name}' weights must sum to 1.0, got {total}")

    for key, value in weights.items():
        if float(value) < 0:
            raise ValueError(f"profile '{name}' weight '{key}' must be >= 0")


def main() -> int:
    data = load_yaml(CONFIG)

    if data.get("version") != "v1":
        raise ValueError("scoring framework version must be v1")

    components = {item["key"] for item in data.get("components", [])}
    if components != REQUIRED_COMPONENTS:
        raise ValueError(
            "components must match required set exactly; "
            f"missing={sorted(REQUIRED_COMPONENTS - components)}, extra={sorted(components - REQUIRED_COMPONENTS)}"
        )

    profiles = data.get("profiles", {})
    if not profiles:
        raise ValueError("profiles must be defined")

    for name, profile in profiles.items():
        assert_weights(name, profile.get("weights", {}))

    stage_rules = data.get("stage_rules", {})
    missing_stages = REQUIRED_STAGES - set(stage_rules.keys())
    if missing_stages:
        raise ValueError(f"stage_rules missing required stages: {sorted(missing_stages)}")

    for stage, rule in stage_rules.items():
        profile = rule.get("profile")
        if profile not in profiles:
            raise ValueError(f"stage '{stage}' references unknown profile '{profile}'")

    overrides = data.get("workflow_overrides", {})
    for name, override in overrides.items():
        stage_profiles = override.get("stage_profiles", {})
        for stage in REQUIRED_STAGES:
            if stage not in stage_profiles:
                raise ValueError(f"override '{name}' missing stage '{stage}'")
            profile = stage_profiles[stage]
            if profile not in profiles:
                raise ValueError(f"override '{name}' stage '{stage}' references unknown profile '{profile}'")

    print(f"validated scoring framework: {CONFIG.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
