---
name: update-shared-schema-safely
description: Use this when modifying shared schemas, contracts, or structured artifact shapes in the shared repo and coordinating the corresponding orchestrator changes. Use for schema evolution, contract changes, and backward compatibility review.
---

# Goal

Change a shared schema without breaking the orchestrator, tests, or downstream consumers.

# Scope

This skill covers:
- `presentation-shared/schemas/`
- orchestrator Pydantic/domain models
- validation logic
- test fixtures
- compatibility and migration review

# Process

1. Locate the schema to be changed.
2. Identify all known consumers:
   - API layer
   - orchestration layer
   - persistence layer
   - validation layer
   - renderer or downstream consumers if referenced
3. Classify the change:
   - additive
   - optional field change
   - required field change
   - field rename
   - field removal
   - semantic behavior change
4. Update the shared schema first.
5. Update matching models and validators in the orchestrator.
6. Update examples and fixtures.
7. Update tests.
8. Review backward compatibility risks.

# Required output

Provide:
- the schema diff summary
- consumer impact summary
- backward compatibility assessment
- files changed
- tests added/updated
- rollout cautions

# Rules

- Prefer additive and backward-compatible changes when possible.
- Never silently change schema meaning without documenting it.
- If a breaking change is required, call it out explicitly.