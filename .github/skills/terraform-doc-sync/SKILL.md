---
name: terraform-doc-sync
description: "Use when: synchronizing README after Terraform input, model, workflow, agent, skill, or deployment procedure changes."
---

# Terraform Documentation Sync

Read [documentation rules](../../instructions/documentation.instructions.md).

1. Compare affected README sections with the changed configuration/workflow.
2. Check input examples, model/version/region, prerequisites, remote state,
   authentication, module references, and TFLint/fmt/validate/plan ordering.
3. Verify agent/skill links and explain roles separately from procedures.
4. The developer updates affected sections in the same change set. The read-only
   reviewer reports discrepancies instead. Do not edit historical screenshots.
5. Verify local links resolve and examples contain no secrets or competing tfvars.

Report updated sections, or why no README update was needed. Do not make unrelated
rewrites or claim that commands ran merely because they appear in examples.