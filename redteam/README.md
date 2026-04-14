# Red-team shared framework

This directory is the source of truth for adversarial evaluation assets used by Presentation AI orchestrator and renderer test suites.

## Structure

- `cases/`: Versioned adversarial case suites.
- `rubrics/`: Reusable scoring rubrics.
- `datasets/`: Shared attack category taxonomy datasets.
- `schemas/`: Versioned JSON schemas for red-team contracts.
- `fixtures/`: Expected-safe behavior fixtures and sample evaluation records.
- `reports/`: Documentation for generated evaluation reports.

## Consumption guidance

### Orchestrator

1. Load `redteam/cases/seed_enterprise_cases_v1.yaml` and select cases with `target_workflow_stage` in orchestrator-owned stages.
2. Validate case records against `redteam/schemas/adversarial-test-case_v1.schema.json`.
3. Execute each case payload against orchestrator boundary APIs and score with `redteam/rubrics/core_rubrics_v1.yaml`.
4. Persist results using `redteam/schemas/evaluation-result-record_v1.schema.json`.

### Renderer

1. Filter cases where category is `unsafe_renderer_payload` or stage is `renderer_preflight`/`rendering`.
2. Inject payloads into renderer preflight validation.
3. Assert sanitization/rejection behavior using expected outcome requirements.
4. Record outcome scores in evaluation result records for trending.

## Adding new cases

1. Add case entries to a versioned file in `redteam/cases/`.
2. Use a new ID (`RT-###`) and include all required fields.
3. Reference only generic, provider-agnostic attack patterns.
4. Run `./scripts/validate-redteam.sh` and commit updates.

## Versioning

- Keep version suffixes explicit (`_v1`, `_v2`, etc.) for datasets, rubrics, fixtures, and schemas.
- Introduce new major versions when backward compatibility breaks.
- Preserve old versions for reproducible regression testing.

## Validation

```bash
./scripts/validate-redteam.sh
```

The validator checks YAML/JSON parsing and schema conformance for cases, taxonomy, rubrics, fixtures, and sample evaluation records.
