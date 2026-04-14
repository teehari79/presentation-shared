# presentation-shared

Production-oriented shared backbone for the Presentation AI platform. This repository is the source of truth for:

- JSON schemas for workflow contracts
- Versioned YAML configs for routing, quality, limits, and safety
- RBAC/ABAC and content safety policies
- Design graph metadata for themes/layouts/object recipes
- Prompt templates and prompt metadata bindings
- Example payload fixtures used for validation and integration tests
- Red-team adversarial evaluation cases, rubrics, and taxonomy fixtures

## Versioning policy

- **All configs and policies are explicitly versioned** using suffixes like `_v1`.
- **Prompt metadata is versioned** and references immutable template file paths.
- **Schema changes should be backward compatible** unless an intentional breaking version is introduced.
- **No environment-specific values** (secrets, hostnames, deployment-specific IDs) belong in this repo.

## Repository consumption contract

### Orchestrator responsibilities

The orchestrator should:

1. Load active prompt versions from `configs/prompts/prompt_versions_v1.yaml`.
2. Select model profiles + task routes from `configs/models/` and `configs/routing/`.
3. Enforce product limits, thresholds, and circuit breakers from `configs/limits/`, `configs/quality/`, `configs/safety/`.
4. Enforce RBAC/ABAC policies before calling tools from `policies/auth/` and `policies/tool-access/`.
5. Validate payloads against JSON schemas in `schemas/` at each stage boundary.

### Renderer responsibilities

The renderer should:

1. Accept only validated `deck-spec` and `render-plan` payloads.
2. Resolve themes/layouts/object recipes from `design-graph/`.
3. Apply export policies from `policies/export/` before generating deliverables.
4. Emit QA/safety evidence records that can be validated by shared schemas.

## Key directories

- `schemas/`: Draft 2020-12 JSON schemas for workflow artifacts.
- `configs/`: Versioned YAML configuration sets.
- `policies/`: RBAC/ABAC, safety, and export policies.
- `design-graph/`: Themes, layouts, icon maps, object recipes, and sample slides.
- `prompts/`: Prompt template text files (system/user).
- `examples/`: Example JSON fixtures for schema validation.
- `redteam/`: Shared adversarial cases, scoring rubrics, schemas, and fixtures.
- `scripts/`: Validation scripts for schemas/configs/fixtures.
- `tests/`: Lightweight validation checks.

## Validation

Run lightweight validations:

```bash
./scripts/validate-schemas.sh
./scripts/validate-configs.sh
./scripts/validate-versions.sh
./scripts/validate-redteam.sh
```

These checks parse JSON schemas, validate YAML structure, validate fixture payloads against matching schemas, and verify changelog/version consistency.

CI runs the same checks in `.github/workflows/validation.yml` for every pull request and push to `main`.
