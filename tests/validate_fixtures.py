#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCHEMA_MAP = {
    "session.sample.json": "session.schema.json",
    "source-document.sample.json": "source-document.schema.json",
    "extracted-understanding.sample.json": "extracted-understanding.schema.json",
    "outline.sample.json": "outline.schema.json",
    "deck-spec.sample.json": "deck-spec.schema.json",
    "render-plan.sample.json": "render-plan.schema.json",
    "safety-check-result.sample.json": "safety-check-result.schema.json",
    "llm-tool-cache-log-record.sample.json": "llm-tool-cache-log-record.schema.json",
    "feedback-thumbs-event.sample_v1.json": "feedback-thumbs-event_v1.schema.json",
    "user-text-feedback.sample_v1.json": "user-text-feedback_v1.schema.json",
    "artifact-acceptance-record.sample_v1.json": "artifact-acceptance-record_v1.schema.json",
    "clarification-loop-record.sample_v1.json": "clarification-loop-record_v1.schema.json",
    "regenerate-request-record.sample_v1.json": "regenerate-request-record_v1.schema.json",
    "model-comparison-score-record.sample_v1.json": "model-comparison-score-record_v1.schema.json",
}


def load_json(path: Path):
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


def validate(instance, schema, path="$"):
    schema_type = schema.get("type")
    if isinstance(schema_type, list):
        if not any(matches_type(instance, t) for t in schema_type):
            raise ValueError(f"{path}: expected one of types {schema_type}")
    elif isinstance(schema_type, str):
        if not matches_type(instance, schema_type):
            raise ValueError(f"{path}: expected type {schema_type}")

    if "const" in schema and instance != schema["const"]:
        raise ValueError(f"{path}: expected const value {schema['const']!r}")

    if "enum" in schema and instance not in schema["enum"]:
        raise ValueError(f"{path}: value not in enum")

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            raise ValueError(f"{path}: below minimum")
        if "maximum" in schema and instance > schema["maximum"]:
            raise ValueError(f"{path}: above maximum")

    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            raise ValueError(f"{path}: shorter than minLength")

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
    for fixture_name, schema_name in SCHEMA_MAP.items():
        fixture = load_json(ROOT / "examples" / fixture_name)
        schema = load_json(ROOT / "schemas" / schema_name)
        validate(fixture, schema)
        print(f"validated: {fixture_name} -> {schema_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
