#!/usr/bin/env python3
"""Validate shared model-provider routing configs against JSON schemas."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCHEMA_MAP = {
    "configs/models/providers_v1.yaml": "schemas/providers-config_v1.schema.json",
    "configs/models/catalog_v1.yaml": "schemas/model-catalog_v1.schema.json",
    "configs/models/routing_v1.yaml": "schemas/model-routing_v1.schema.json",
    "configs/models/fallbacks_v1.yaml": "schemas/model-fallbacks_v1.schema.json",
    "configs/models/policy_v1.yaml": "schemas/model-policy_v1.schema.json",
}


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_yaml(path: Path):
    import subprocess

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

    if "enum" in schema and instance not in schema["enum"]:
        raise ValueError(f"{path}: value not in enum")

    if isinstance(instance, dict):
        props = schema.get("properties", {})
        required = schema.get("required", [])
        for key in required:
            if key not in instance:
                raise ValueError(f"{path}: missing required key {key}")

        min_properties = schema.get("minProperties")
        if min_properties is not None and len(instance) < min_properties:
            raise ValueError(f"{path}: expected at least {min_properties} properties")

        additional = schema.get("additionalProperties", True)
        extras = set(instance.keys()) - set(props.keys())
        if additional is False and extras:
            raise ValueError(f"{path}: extra keys not allowed: {sorted(extras)}")

        for key, value in instance.items():
            if key in props:
                validate(value, props[key], f"{path}.{key}")
            elif isinstance(additional, dict):
                validate(value, additional, f"{path}.{key}")

    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            raise ValueError(f"{path}: not enough items")
        item_schema = schema.get("items")
        if item_schema:
            for idx, item in enumerate(instance):
                validate(item, item_schema, f"{path}[{idx}]")

    if isinstance(instance, str) and "minLength" in schema and len(instance) < schema["minLength"]:
        raise ValueError(f"{path}: shorter than minLength")

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            raise ValueError(f"{path}: below minimum")
        if "maximum" in schema and instance > schema["maximum"]:
            raise ValueError(f"{path}: above maximum")


def validate_cross_config_consistency() -> None:
    providers = load_yaml(ROOT / "configs/models/providers_v1.yaml")
    catalog = load_yaml(ROOT / "configs/models/catalog_v1.yaml")
    routing = load_yaml(ROOT / "configs/models/routing_v1.yaml")

    provider_names = {provider["name"] for provider in providers["providers"]}
    model_refs = {f"{model['provider']}/{model['model_id']}" for model in catalog["models"]}
    slot_names = set(routing["task_slots"].keys())

    for model in catalog["models"]:
        if model["provider"] not in provider_names:
            raise ValueError(f"catalog references unknown provider: {model['provider']}")
        for fallback_candidate in model["fallback_candidates"]:
            if fallback_candidate not in model_refs:
                raise ValueError(f"catalog fallback references unknown model: {fallback_candidate}")

    for slot_name, slot_config in routing["task_slots"].items():
        for preferred_model in slot_config["preferred_models"]:
            if preferred_model not in model_refs:
                raise ValueError(f"routing slot {slot_name} references unknown model: {preferred_model}")

    for route, slot in routing["workflow_task_routes"].items():
        if slot not in slot_names:
            raise ValueError(f"route {route} references unknown slot: {slot}")


def main() -> int:
    for config_path, schema_path in SCHEMA_MAP.items():
        config = load_yaml(ROOT / config_path)
        schema = load_json(ROOT / schema_path)
        validate(config, schema)
        print(f"validated: {config_path} -> {schema_path}")

    validate_cross_config_consistency()
    print("validated: cross-config provider/model/slot references")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
