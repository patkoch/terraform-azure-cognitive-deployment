---
name: terraform-plan-review
description: "Use when: reviewing an existing Terraform plan, explaining changes for a PR, or assessing replacement, deletion, network, identity, and cost risks. Does not generate plans."
---

# Terraform Plan Review

Review the plan section of `.preflight/report.md`, written by
[terraform-preflight](../terraform-preflight/SKILL.md), or other supplied sanitized
evidence. Do not run `terraform plan` again. Read
[shared rules](../../copilot-instructions.md).

## Preconditions

- The report identifies revision, fingerprint, subscription (masked), and the
  status of preceding checks. Old plans do not validate newer edits; state the
  report's timestamp and whether any later edit is known.
- The reviewer reads only the report. If it is missing or has no plan section,
  report plan review as blocked; do not read `tfplan`, raw JSON, or state files.
- The report lists resource addresses, actions, and changed attribute names, not
  values. An execution-enabled developer may inspect `terraform show -no-color tfplan`
  locally for values but must not publish raw output, because even redacted text
  can contain sensitive values. Never use `show -json` in chat.

## Review

1. Summarize add/change/replace/destroy counts and explicitly identify replacements.
2. Check naming/location changes, public access, authentication, identity,
   model/version, capacity, state moves, and cost-relevant changes.
3. Distinguish configuration evidence from live model availability, quotas,
   and estimated costs. Do not invent availability claims or prices.
4. Flag unexpected destruction/replacement for investigation before any human
   deployment decision. Never apply or mutate state.

## Output

Provenance and counts, highest-risk changes, assumptions/missing evidence, then
a short PR-ready summary with sanitized values. If a plan is unavailable, say
so; static inspection is not a substitute for an actual plan.
