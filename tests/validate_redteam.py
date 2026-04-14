#!/usr/bin/env python3
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "redteam" / "schemas"


def load_data(path: Path):
    if path.suffix in {".yaml", ".yml"}:
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

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def matches_type(value, schema_type):
    if schema_type == "object":
        return isinstance(value, dict)
    if schema_type == "array":
        return isinstance(value, list)
    if schema_type == "string":
        return isinstance(value, str)
    if schema_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if schema_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if schema_type == "boolean":
        return isinstance(value, bool)
    if schema_type == "null":
        return value is None
    return True


def resolve_ref(ref: str):
    return load_data(SCHEMA_DIR / ref)


def validate(instance, schema, path="$"):
    if "$ref" in schema:
        schema = resolve_ref(schema["$ref"])

    schema_type = schema.get("type")
    if isinstance(schema_type, list):
        if not any(matches_type(instance, t) for t in schema_type):
            raise ValueError(f"{path}: expected one of types {schema_type}")
    elif isinstance(schema_type, str):
        if not matches_type(instance, schema_type):
            raise ValueError(f"{path}: expected type {schema_type}")

    if "enum" in schema and instance not in schema["enum"]:
        raise ValueError(f"{path}: value not in enum")

    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            raise ValueError(f"{path}: shorter than minLength")
        if "pattern" in schema and not re.match(schema["pattern"], instance):
            raise ValueError(f"{path}: does not match pattern")

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            raise ValueError(f"{path}: below minimum")
        if "maximum" in schema and instance > schema["maximum"]:
            raise ValueError(f"{path}: above maximum")

    if isinstance(instance, dict):
        props = schema.get("properties", {})
        required = schema.get("required", [])
        for key in required:
            if key not in instance:
                raise ValueError(f"{path}: missing required key {key}")

        if schema.get("additionalProperties") is False:
            extras = set(instance.keys()) - set(props.keys())
            if extras:
                raise ValueError(f"{path}: extra keys not allowed: {sorted(extras)}")

        for key, value in instance.items():
            if key in props:
                validate(value, props[key], f"{path}.{key}")

    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            raise ValueError(f"{path}: not enough items")
        item_schema = schema.get("items")
        if item_schema:
            for idx, item in enumerate(instance):
                validate(item, item_schema, f"{path}[{idx}]")


def main() -> int:
    taxonomy = load_data(ROOT / "redteam" / "datasets" / "attack_taxonomy_v1.yaml")
    taxonomy_schema = load_data(SCHEMA_DIR / "attack-category-taxonomy_v1.schema.json")
    validate(taxonomy, taxonomy_schema)
    print("validated: attack_taxonomy_v1.yaml")

    rubrics = load_data(ROOT / "redteam" / "rubrics" / "core_rubrics_v1.yaml")
    rubric_schema = load_data(SCHEMA_DIR / "scoring-rubric_v1.schema.json")
    validate(rubrics, rubric_schema)
    print("validated: core_rubrics_v1.yaml")

    cases_doc = load_data(ROOT / "redteam" / "cases" / "seed_enterprise_cases_v1.yaml")
    case_schema = load_data(SCHEMA_DIR / "adversarial-test-case_v1.schema.json")
    for case in cases_doc["cases"]:
        validate(case, case_schema)
    if len(cases_doc["cases"]) < 25:
        raise ValueError("redteam seed suite must contain at least 25 cases")
    print(f"validated: seed_enterprise_cases_v1.yaml ({len(cases_doc['cases'])} cases)")

    expected_behaviors = load_data(ROOT / "redteam" / "fixtures" / "expected_safe_behaviors_v1.yaml")
    expected_outcome_schema = load_data(SCHEMA_DIR / "expected-outcome_v1.schema.json")
    for _, outcome in expected_behaviors["default_expected_outcomes"].items():
        validate(outcome, expected_outcome_schema)
    print("validated: expected_safe_behaviors_v1.yaml")

    eval_record = load_data(ROOT / "redteam" / "fixtures" / "evaluation_result_record.sample_v1.json")
    eval_schema = load_data(SCHEMA_DIR / "evaluation-result-record_v1.schema.json")
    validate(eval_record, eval_schema)
    print("validated: evaluation_result_record.sample_v1.json")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
