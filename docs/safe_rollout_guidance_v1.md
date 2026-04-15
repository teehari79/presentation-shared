# Safe Rollout Guidance v1 (Model/Prompt Changes)

Use this checklist before enabling new model profiles or prompt versions.

## 1) Must-pass gates before enablement

Do not enable in production unless all are true:

- shared schema/config validation passes
- orchestrator adversarial smoke passes
- renderer safety adversarial suite passes
- no unresolved high-severity failures in current release window
- rollback plan is documented and tested

## 2) Smoke tests to run

Run at minimum:

1. high-severity prompt-injection case
2. tenant-isolation adversarial case
3. approval-gate enforcement case
4. unsafe renderer payload rejection case
5. baseline happy-path deck generation case

Smoke objective: verify both safety rejection behavior and non-regression on normal flow.

## 3) Rollback considerations

Before rollout, prepare:

- previous model profile and prompt version pointers
- one-command rollback procedure for runtime config
- data needed to compare pre/post safety metrics
- owner and on-call acknowledgment for rollback execution

Rollback triggers (examples):

- any new high-severity adversarial failure
- repeated partial rubric outcomes in critical categories
- evidence of policy-hook non-execution in production telemetry

## 4) Operator release sequence

1. deploy disabled behind feature flag
2. run smoke suite in pre-prod
3. enable for limited traffic slice
4. monitor incident indicators and adversarial canary results
5. expand gradually only if no new safety regressions
