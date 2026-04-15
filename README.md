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


## Shared model-provider control plane

The `configs/models/` directory is the shared control plane for model-provider abstraction and routing.

- `providers_v1.yaml`: provider abstraction definitions (OpenAI, Vertex AI, Azure Foundry, Hugging Face, Groq).
- `catalog_v1.yaml`: versioned model catalog entries, task tags, capability metadata, environment allowlists, fallback candidates, and deprecation status.
- `routing_v1.yaml`: named task slots and workflow task-to-slot mapping so application logic does not hardcode model IDs.
- `fallbacks_v1.yaml`: ordered fallback chains, retry/timeout policy, fail-open vs fail-closed behavior, and structured-output revalidation flags.
- `policy_v1.yaml`: global guardrails that enforce environment-agnostic and versioned model-routing behavior.

Validation coverage for this control plane is provided by `tests/validate_model_routing.py`, which checks both schema conformance and cross-file reference integrity.

## Key directories

- `schemas/`: Draft 2020-12 JSON schemas for workflow artifacts.
- `configs/`: Versioned YAML configuration sets.
- `policies/`: RBAC/ABAC, safety, and export policies.
- `design-graph/`: Themes, layouts, icon maps, object recipes, and sample slides.
- `prompts/`: Prompt template text files (system/user).
- `examples/`: Example JSON fixtures for schema validation.
- `redteam/`: Shared adversarial cases, scoring rubrics, schemas, and fixtures.
- `docs/`: Practical red-team, operator, incident-response, and rollout playbooks.
- `scripts/`: Validation scripts for schemas/configs/fixtures.
- `tests/`: Lightweight validation checks.

## CI quality gates

The GitHub Actions workflow (`.github/workflows/validation.yml`) now enforces staged quality gates with machine-readable artifacts for every job:

- `unit-tests`: baseline unit validations.
- `integration-tests`: fixture + red-team contract integration checks.
- `shared-schema-config-validation`: schema/config parsing and shared red-team definition validation.
- `lint-type-checks`: Python compile checks + shell syntax checks.
- `build-verification`: archive/buildability and version consistency checks.
- `adversarial-smoke` (PR only): orchestrator smoke subset + renderer safety checks.
- `adversarial-full` (scheduled + `main`/`release/*`): broader orchestrator and renderer adversarial regressions.

Each gate uploads:

- JUnit XML report (`*.junit.xml`)
- JSON report (`*.report.json` plus red-team evaluation JSON)
- Markdown summary (`*.summary.md`)

Failure output is categorized to make triage clear:

- `schema`
- `policy`
- `adversarial regression`
- `authorization`
- `renderer safety`
- `normal unit test`

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


## Safety/operator playbooks

Practical runbooks are versioned under `docs/`:

- `docs/redteam_playbook_v1.md`
- `docs/orchestrator_safety_ops_playbook_v1.md`
- `docs/renderer_safety_ops_playbook_v1.md`
- `docs/incident_response_playbook_v1.md`
- `docs/safe_rollout_guidance_v1.md`
