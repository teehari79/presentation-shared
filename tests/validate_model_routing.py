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
    "configs/models/model_profile_catalog_v1.yaml": "schemas/model-profile-catalog_v1.schema.json",
    "configs/models/catalog.yaml": "schemas/model-catalog-entry_v1.schema.json",
    "configs/models/routing.yaml": "schemas/routing-entry_v1.schema.json",
    "configs/models/fallbacks.yaml": "schemas/fallback-policy_v1.schema.json",
    "configs/models/scoring.yaml": "schemas/model-routing-scoring_v1.schema.json",
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
    fallbacks = load_yaml(ROOT / "configs/models/fallbacks_v1.yaml")
    policy = load_yaml(ROOT / "configs/models/policy_v1.yaml")
    profile_catalog = load_yaml(ROOT / "configs/models/model_profile_catalog_v1.yaml")

    provider_names = {provider["name"] for provider in providers["providers"]}
    model_refs = {f"{model['provider']}/{model['model_id']}" for model in catalog["models"]}
    slot_names = set(routing["task_slots"].keys())
    fallback_slot_names = set(fallbacks["slot_policies"].keys())
    policy_required_slots = set(policy["policy"]["required_task_slots"])
    policy_required_providers = set(policy["policy"]["required_provider_abstractions"])

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

    for slot_name in fallback_slot_names:
        if slot_name not in slot_names:
            raise ValueError(f"fallbacks slot_policies references unknown slot: {slot_name}")

    missing_fallback_slots = slot_names - fallback_slot_names
    if missing_fallback_slots:
        raise ValueError(
            f"fallbacks slot_policies missing routing slots: {sorted(missing_fallback_slots)}"
        )

    for slot_name, slot_policy in fallbacks["slot_policies"].items():
        for fallback_model in slot_policy["fallback_chain"]:
            if fallback_model not in model_refs:
                raise ValueError(
                    f"fallback chain for slot {slot_name} references unknown model: {fallback_model}"
                )

    for required_slot in policy_required_slots:
        if required_slot not in slot_names:
            raise ValueError(f"policy required_task_slots references unknown slot: {required_slot}")

    for required_provider in policy_required_providers:
        if required_provider not in provider_names:
            raise ValueError(
                f"policy required_provider_abstractions references unknown provider: {required_provider}"
            )

    profile_types = set(profile_catalog["profile_types"])
    profile_ids = set()
    for profile in profile_catalog["profiles"]:
        profile_ids.add(profile["profile_id"])
        if profile["profile_type"] not in profile_types:
            raise ValueError(
                f"profile catalog references unknown profile_type: {profile['profile_type']}"
            )
        if profile["provider"] != "local" and profile["provider"] not in provider_names:
            raise ValueError(f"profile catalog references unknown provider: {profile['provider']}")

    bundles_dir = ROOT / "configs/models/profile_bundles_v1"
    for bundle_path in sorted(bundles_dir.glob("*.yaml")):
        bundle = load_yaml(bundle_path)
        schema = load_json(ROOT / "schemas/model-profile-bundle_v1.schema.json")
        validate(bundle, schema, path=f"${bundle_path.name}")
        for task_name, profile_id in bundle["profiles"].items():
            if profile_id not in profile_ids:
                raise ValueError(
                    f"bundle {bundle_path.name} task {task_name} references unknown profile: {profile_id}"
                )


def validate_model_routing_control_plane() -> None:
    providers = load_yaml(ROOT / "configs/models/providers_v1.yaml")
    catalog = load_yaml(ROOT / "configs/models/catalog.yaml")
    routing = load_yaml(ROOT / "configs/models/routing.yaml")
    fallbacks = load_yaml(ROOT / "configs/models/fallbacks.yaml")
    scoring = load_yaml(ROOT / "configs/models/scoring.yaml")

    provider_names = {provider["name"] for provider in providers["providers"]}
    allowed_external_providers = {"cohere_managed"}
    model_keys = {entry["key"] for entry in catalog["models"]}
    model_by_key = {entry["key"]: entry for entry in catalog["models"]}
    compatible_roles = {
        "reasoning_primary": {"reasoning_primary", "reasoning_fast"},
        "reasoning_fast": {"reasoning_primary", "reasoning_fast"},
    }

    def slot_role_match(slot_name: str, model_key: str) -> bool:
        roles = set(model_by_key[model_key]["roles"])
        allowed = compatible_roles.get(slot_name, {slot_name})
        return bool(roles & allowed)

    for entry in catalog["models"]:
        validate(entry, load_json(ROOT / "schemas/model-catalog-entry_v1.schema.json"), path="$.models[]")
        if entry["provider"] not in provider_names and entry["provider"] not in allowed_external_providers:
            raise ValueError(f"catalog provider is not recognized: {entry['provider']}")

    for slot_name, slot_entry in routing["task_slots"].items():
        validate(slot_entry, load_json(ROOT / "schemas/routing-entry_v1.schema.json"), path=f"$.task_slots.{slot_name}")
        for model_key in slot_entry["model_keys"]:
            if model_key not in model_keys:
                raise ValueError(f"task slot {slot_name} references unknown model key: {model_key}")
            if not slot_role_match(slot_name, model_key):
                raise ValueError(
                    f"task slot {slot_name} references model {model_key} without matching role"
                )

    for task_name, slot_name in routing["workflow_task_routes"].items():
        if slot_name not in routing["task_slots"]:
            raise ValueError(f"workflow route {task_name} references unknown slot: {slot_name}")

    required_slots = {
        "reasoning_primary",
        "reasoning_fast",
        "classification_small",
        "formatting_small",
        "embedding_primary",
        "reranker_primary",
    }
    missing_slots = required_slots - set(routing["task_slots"].keys())
    if missing_slots:
        raise ValueError(f"routing is missing required task slots: {sorted(missing_slots)}")

    for slot_name, slot_policy in fallbacks["slot_policies"].items():
        validate(slot_policy, load_json(ROOT / "schemas/fallback-policy_v1.schema.json"), path=f"$.slot_policies.{slot_name}")
        if slot_name not in routing["task_slots"]:
            raise ValueError(f"fallback slot policy references unknown slot: {slot_name}")
        for model_key in slot_policy["ordered_model_chain"]:
            if model_key not in model_keys:
                raise ValueError(f"fallback slot {slot_name} references unknown model key: {model_key}")
            if not slot_role_match(slot_name, model_key):
                raise ValueError(
                    f"fallback slot {slot_name} references model {model_key} without matching role"
                )

    missing_fallbacks = set(routing["task_slots"].keys()) - set(fallbacks["slot_policies"].keys())
    if missing_fallbacks:
        raise ValueError(f"fallback policies missing slots: {sorted(missing_fallbacks)}")

    for profile_name, profile in routing["profile_bundles"].items():
        missing_bundle_slots = required_slots - set(profile.keys())
        if missing_bundle_slots:
            raise ValueError(
                f"profile bundle {profile_name} missing required slots: {sorted(missing_bundle_slots)}"
            )
        for slot_name, bundle_model_keys in profile.items():
            if slot_name not in routing["task_slots"]:
                raise ValueError(f"profile bundle {profile_name} references unknown slot: {slot_name}")
            for model_key in bundle_model_keys:
                if model_key not in model_keys:
                    raise ValueError(
                        f"profile bundle {profile_name} slot {slot_name} references unknown model: {model_key}"
                    )
                if not slot_role_match(slot_name, model_key):
                    raise ValueError(
                        f"profile bundle {profile_name} slot {slot_name} references model {model_key} without matching role"
                    )

    validate(scoring, load_json(ROOT / "schemas/model-routing-scoring_v1.schema.json"), path="$.scoring")
    weight_sum = sum(scoring["weights"].values())
    if abs(weight_sum - 1.0) > 1e-9:
        raise ValueError(f"scoring weights must sum to 1.0 (got {weight_sum})")


def main() -> int:
    for config_path, schema_path in SCHEMA_MAP.items():
        config = load_yaml(ROOT / config_path)
        schema = load_json(ROOT / schema_path)
        if config_path.endswith("catalog.yaml"):
            for idx, item in enumerate(config["models"]):
                validate(item, schema, path=f"$.models[{idx}]")
        elif config_path.endswith("routing.yaml"):
            for slot_name, slot in config["task_slots"].items():
                validate(slot, schema, path=f"$.task_slots.{slot_name}")
        elif config_path.endswith("fallbacks.yaml"):
            for slot_name, slot_policy in config["slot_policies"].items():
                validate(slot_policy, schema, path=f"$.slot_policies.{slot_name}")
        else:
            validate(config, schema)
        print(f"validated: {config_path} -> {schema_path}")

    validate_cross_config_consistency()
    print("validated: cross-config provider/model/slot references")

    validate_model_routing_control_plane()
    print("validated: model routing control-plane catalog/routing/fallback/profile/scoring checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
