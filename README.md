# Presentation Shared

Shared contracts, policies, configs, prompts, and design metadata for the Presentation AI platform.

## Contents
- `schemas/` for JSON schemas
- `policies/` for auth, safety, export, and tool-access rules
- `configs/` for model, prompt, routing, limits, chunking, quality, and feature settings
- `prompts/` for prompt templates and prompt metadata
- `design-graph/` for themes, layouts, sample slides, object recipes, and icon mappings
- `examples/` for sample payloads and fixtures

## Consumers
This repo is used by:
- `presentation-orchestrator`
- `presentation-ui-renderer`

## Rules
- keep configs versioned
- keep schemas stable
- keep policies explicit and reviewable
- do not store environment-specific values or real secrets here

## Common commands
Validate schemas/configs:
```bash
bash scripts/validate-configs.sh