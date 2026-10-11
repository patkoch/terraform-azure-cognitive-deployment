---
name: terraform-azurerm-upgrade
description: "Use only when: the user explicitly requests an AzureRM provider version upgrade. Not for routine Terraform edits, refactoring, lint fixes, or preflight."
---

# Explicit AzureRM Upgrade

Read [shared rules](../../copilot-instructions.md). An explicit user request
is required before changing AzureRM's version constraint or resolved lockfile
version. Do not treat CI failures, tool notices, or newer releases as authorization.

## Procedure

1. Read the current constraint from `terraform.tf` and resolved provider version
   from the lockfile if present. Do not assume a fixed starting version.
2. If the user says only "please upgrade AzureRM", ask for the desired target
   before editing. You may present researched options but never choose "latest"
   automatically. Confirm constraint precision if changing its component count.
3. Explain the distinction between the constraint and installed version: `~> X.Y`
   permits releases below the next major, while `~> X.Y.Z` permits releases below
   the next minor. Initialization may resolve a newer version within that range.
   Agree on both the constraint and intended lockfile resolution before proceeding.
4. Check official release notes/migration guidance, Terraform compatibility, and
   the provider constraints in the currently tagged modules. If compatibility
   requires module changes, stop and request a separate module task. Never edit
   the module repository or update module tags as an incidental upgrade.
5. Change only the authorized AzureRM constraint, related compatibility fixes,
   lockfile, and affected documentation. Keep `~>`; preserve Terraform CLI
   constraints, backend, module tags, and unrelated deployment inputs.
6. `terraform init -upgrade -input=false` is allowed only for this explicit
   upgrade, not routine validation. It can update other dependencies too; inspect
   the resulting diff and report unexpected changes before proceeding.
7. Load [terraform-doc-sync](../terraform-doc-sync/SKILL.md), then execute
   [terraform-preflight](../terraform-preflight/SKILL.md) in its required order.
   Report unavailable credentials/tools as blocked; never bypass the backend.
8. Summarize old/new constraint and lockfile versions, compatibility evidence,
   check results, and plan risks. Hand off to the read-only reviewer.

Never apply, destroy, migrate state, or make unsolicited follow-up upgrades.