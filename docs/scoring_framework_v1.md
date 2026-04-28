# Scoring Framework v1

This document defines the shared, provider-agnostic scoring framework used to measure model quality and user-perceived outcomes across presentation workflows.

## Goals

- Normalize cross-surface feedback into shared contracts reusable by UI and orchestrator layers.
- Keep scoring configurable in versioned YAML (no hardcoded component weights in code).
- Support stage-specific quality gates and profile overrides for different workflow modes.

## Shared feedback/acceptance schemas

The following versioned schemas are introduced:

- `schemas/feedback-thumbs-event_v1.schema.json`
- `schemas/user-text-feedback_v1.schema.json`
- `schemas/artifact-acceptance-record_v1.schema.json`
- `schemas/clarification-loop-record_v1.schema.json`
- `schemas/regenerate-request-record_v1.schema.json`
- `schemas/model-comparison-score-record_v1.schema.json`

Example fixtures are provided in `examples/*.sample_v1.json` with matching names.

## Scoring configuration

`configs/quality/scoring_framework_v1.yaml` defines:

- Component registry with polarity semantics (`positive`/`negative`).
- Weight profiles (`baseline`, `quality_strict`, `efficiency_first`).
- Stage rules for:
  - `understanding`
  - `outline`
  - `deck_spec`
  - `formatting`
  - `retrieval_reranking`
- Workflow overrides (`draft_mode`, `release_mode`) to tune stage profiles by workflow mode.

### Core weighted components

- `schema_validity`
- `support_grounding_quality`
- `first_pass_acceptance`
- `clarification_count`
- `regenerate_count`
- `explicit_user_rating`
- `latency_efficiency`
- `cost_efficiency`

## Validation

- `tests/validate_fixtures.py` validates new feedback and scoring fixtures against their schemas.
- `tests/validate_scoring_framework.py` validates scoring framework integrity:
  - required components/stages exist
  - profile weights are complete and sum to 1.0
  - stage and override profile references are valid

Run:

```bash
python3 tests/validate_fixtures.py
python3 tests/validate_scoring_framework.py
```
