# Renderer Safety Ops Playbook v1

Use this guide in the renderer repository for unsafe payload handling and validation triage.

## 1) Unsafe render input model

Treat input as unsafe by default when any of the following are present:

- untrusted HTML/markdown/script-like fragments
- external links/assets not in allowlist
- oversized or malformed structural fields
- style or object directives that attempt sandbox escape
- payload fields that do not match deck-spec/render-plan contracts

## 2) Sanitization and rejection rules

Apply this order consistently:

1. **Schema validation first**: reject structurally invalid payloads.
2. **Policy validation second**: reject disallowed constructs even if schema-valid.
3. **Sanitize only known-safe transforms**: strip/normalize where deterministic.
4. **Hard reject on ambiguous risk**: do not attempt best-effort rendering for high-risk payloads.

Practical rule: sanitize presentation formatting; reject execution-like or exfiltration-like content.

## 3) Troubleshoot validation failures

When renderer validation fails:

1. Record failing case ID and payload hash.
2. Identify failure class:
   - schema parse/shape failure
   - policy violation
   - sanitizer transform mismatch
3. Compare expected-outcome rule from red-team case.
4. Re-run case in isolation with debug logging enabled.
5. Confirm final decision (sanitize vs reject) matches policy intent.

If output is accepted after sanitizer but should be rejected, escalate as high severity.

## 4) Regression test additions

For each new renderer safety rule, add:

- one payload expected to be sanitized
- one payload expected to be rejected
- expected evidence fields recorded for auditability
