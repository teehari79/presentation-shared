# Incident Response Playbook v1 (Safety)

Use this runbook for production safety incidents.

## Global response flow (all incident types)

1. **Declare incident** with severity and start timestamp.
2. **Stabilize** by applying immediate guardrails (kill-switch, strict mode, or model/prompt rollback).
3. **Scope impact** by tenant, timeframe, and workflow stage.
4. **Preserve evidence** (request IDs, payload snapshots, policy decisions, model/prompt versions).
5. **Mitigate** with reversible changes first.
6. **Verify containment** using targeted adversarial replay.
7. **Communicate** status updates on defined cadence.
8. **Close with actions** (tests, policy updates, rollout gate changes).

---

## A) Prompt injection discovered in production

Immediate actions:

1. Enable stricter prompt-injection policy mode.
2. Disable vulnerable tools/workflow stages if needed.
3. Replay the discovered payload across smoke cases.

Diagnosis:

- determine ingress path (user prompt, retrieved doc, tool output)
- identify missing or bypassed guardrail stage
- map affected prompt/model version pair

Containment complete when:

- injection payload is blocked or neutralized in replay
- no privileged tool calls occur from injected instructions

## B) Suspected tenant leakage

Immediate actions:

1. Freeze cross-tenant retrieval/tool paths.
2. Rotate or revoke affected credentials/tokens.
3. Force strict tenant-bound filters at query boundary.

Diagnosis:

- inspect authorization decisions (RBAC/ABAC)
- inspect retrieval filters and cache partition keys
- quantify exposed records and tenants impacted

Containment complete when:

- leakage path reproduced and closed
- regression test added for the exact leak pattern

## C) Hallucinated unsupported deck content

Immediate actions:

1. Add temporary output constraint to block unsupported claims.
2. Route high-risk generations through stricter review path.

Diagnosis:

- verify source attribution/grounding path
- determine whether failure is prompt guidance, retrieval quality, or policy thresholding

Containment complete when:

- unsupported content scenario fails safe in adversarial replay
- rubric score returns to pass for affected category

## D) Approval bypass defect

Immediate actions:

1. Re-enable hard approval gate (fail-closed).
2. Suspend auto-publish/export for affected workflow.

Diagnosis:

- identify where state transition allowed bypass
- verify signature/token/state-machine checks

Containment complete when:

- approval transitions are provably gated end-to-end
- bypass attempt is blocked in regression tests

## E) Unsafe renderer payload acceptance

Immediate actions:

1. Enable strict renderer preflight mode.
2. Block rendering for suspicious payload class.

Diagnosis:

- compare sanitizer output to rejection policy
- inspect schema and policy evaluation ordering

Containment complete when:

- payload is rejected (or safely sanitized per policy)
- renderer adversarial regression passes for affected class
