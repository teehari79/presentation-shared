# AGENTS.md

## Repo purpose
This repository contains shared schemas, configs, policies, prompts, and design graph metadata.

## Rules
- Version configs and prompts explicitly.
- Keep schemas stable and backward compatible unless intentionally changed.
- Do not add environment-specific values here.
- Validate YAML and schema examples when making changes.
- Version red-team datasets/rubrics/cases explicitly and keep them provider-agnostic.


## Shared model routing control plane
- The `configs/models/` directory is the authoritative, versioned model-provider abstraction and routing control plane.
- Keep provider/model identifiers configurable in YAML; avoid hardcoding them in downstream business logic.
- Ensure routing, fallback, and policy files stay environment-agnostic and free of secrets/endpoints.
- When updating model control-plane configs, update schemas and `tests/validate_model_routing.py` together.
