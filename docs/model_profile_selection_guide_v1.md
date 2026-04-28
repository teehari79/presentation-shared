# Model Profile Selection Guide v1

This guide explains how to select small-task model profiles and precomposed bundles in `configs/models/model_profile_catalog_v1.yaml` and `configs/models/profile_bundles_v1/`.

## Profile families

- **small_classification**: low-cost intent/sentiment/language tagging and routing prechecks.
- **small_formatting**: lightweight rewrite/normalization tasks before premium generation.
- **local_quantized_instruction**: locally runnable instruction models for development, offline debugging, and experimentation.
- **embedding**: retrieval and semantic indexing.
- **reranker**: relevance reranking for search, grounding, and citation selection.

## Metadata fields and how to use them

- `expected_task_fit`: primary tasks where the profile is expected to perform well.
- `cpu_suitability`: rough CPU-only suitability (`high`, `medium`, `low`).
- `local_dev_suitability`: suitability for local development and iterative testing.
- `latency_class`: expected latency tier from `very_fast` to `slow`.
- `cost_class`: expected spend tier (`economy`, `standard`, `premium`).
- `structured_output_fit`: expected fit for strict schema/JSON workflows.
- `experimentation_only`: mark profiles not yet intended as production defaults.

## Bundle recommendations

- **cheap-fast**: best for high-throughput, cost-sensitive preprocessing and retrieval.
- **quality-first**: use when output quality and reranking precision matter more than latency.
- **hf-heavy**: use when minimizing provider variance with a Hugging Face–centric stack.
- **local-dev**: use for laptop-friendly or offline development and prompt iteration.
- **balanced-enterprise**: use for mixed workloads needing stable quality and controlled spend.

## Operational guidance

- Prefer non-experimental profiles (`experimentation_only: false`) for production-critical flows.
- Use bundle defaults as starting points, then override per task slot as needed.
- Keep provider and model IDs configurable and avoid endpoint-specific assumptions.
