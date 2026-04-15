# Orchestrator Adversarial Ops Playbook v1

Use this guide in the orchestrator repository when running and triaging adversarial regressions.

## 1) Run adversarial tests locally

1. Sync latest shared assets used by orchestrator.
2. Run orchestrator adversarial suite in smoke mode first.
3. Run full suite before merging high-risk safety changes.

Recommended local sequence (adapt command names to orchestrator repo scripts):

```bash
# fast confidence check
python3 tests/adversarial_regression.py --target orchestrator-smoke

# broader pre-merge check
python3 tests/adversarial_regression.py --target orchestrator-full
```

## 2) Interpret failures quickly

For each failing case capture:

- case ID and category
- workflow stage where failure surfaced
- expected outcome vs actual outcome
- rubric score delta

Triage matrix:

- **Policy mismatch**: guardrail decision incorrect -> inspect policy config and thresholds.
- **Hooking defect**: correct policy exists but never executed -> inspect stage hook registration.
- **Prompt behavior drift**: model output shape changed but policy still runs -> inspect prompt/model version pairing.
- **Schema/contract mismatch**: payload rejected/accepted incorrectly -> inspect schema and boundary adapter.

## 3) Safety hooks vs workflow stages

Safety hooks should run at minimum at:

1. input ingestion
2. retrieval/context assembly
3. draft generation
4. tool invocation boundaries
5. output post-processing

Operational expectations:

- Earlier stages block known-bad inputs.
- Mid stages prevent lateral escalation (tool abuse, data overreach).
- Final stage performs defense-in-depth checks before external output.

If a case fails late but should have failed early, file as stage-ordering defect.

## 4) Add new policy checks

1. Define check intent in one sentence (what unsafe action is prevented).
2. Add versioned policy/config in shared repo (`policies/` or `configs/safety/`).
3. Wire check into the intended workflow stage hook.
4. Add at least one positive and one negative adversarial case.
5. Confirm failure category is reported clearly (`policy`, `authorization`, `adversarial regression`, etc.).

Minimum acceptance before merge:

- new policy check can be toggled deterministically
- adversarial case fails before fix and passes after fix
- no regressions in smoke suite
