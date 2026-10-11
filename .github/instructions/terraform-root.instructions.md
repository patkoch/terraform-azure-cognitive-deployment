---
description: "Use when: changing root Terraform, provider constraints, backend, module inputs, variables, or Terraform workflows."
applyTo: "*.tf,*.tfvars,.github/workflows/*.yml"
---

# Root Terraform Rules

- AzureRM in `terraform.tf` must use a single pessimistic `~>` constraint.
  Preserve the current version number and precision during ordinary tasks.
  Never replace `~>` with `>`, `>=`, `=`, or an unconstrained version.
  Change the version only on an explicit AzureRM upgrade request from the user,
  not during refactoring, lint fixes, preflight, or automated dependency cleanup.
  If the request does not specify a target, ask before choosing or editing it;
  never select "latest" automatically. Read the version from `terraform.tf`.
  A precision change (major.minor to major.minor.patch) also requires explicit
  agreement because it changes the allowed upgrade range.
  Load [terraform-azurerm-upgrade](../skills/terraform-azurerm-upgrade/SKILL.md)
  for an authorized upgrade. Preserve
  `required_version = "~> 1.16.4"`; Terraform CLI upgrades are separate tasks.
- Preserve the existing remote `backend "azurerm"`, including resource group
  `azureworkshop-demo-rg`, storage account `azureworkshopdemostorage`, container
  `tfstateopenai`, and key `terraform.tfstate`. Never switch to local state,
  bypass the backend for a plan, or migrate state without a separate task.
- Root Terraform must not contain `resource` blocks. `main.tf` is module
  composition only. Existing `moved` blocks are allowed and must be preserved.
- Consume modules only from `patkoch/terraform-modules` using release tags.
  Preserve current tags unless explicitly asked to update them. Branches,
  commit SHAs, local paths, and arbitrary module repositories are forbidden.
- Configurable module inputs use `var.*` or module outputs, never literals.
  Literal module `source` strings, stable `main` instance keys, and references
  using `["main"]` are required structural exceptions, not deployment values.
- Declare root variables in `variables.tf` with types and descriptions.
  No defaults, including `null`, except exactly `resource_group_tags` with
  `{ ManagedBy = "Terraform" }`. Other tag variables are not on the allowlist.
- Put non-sensitive deployment values only in root `terraform.auto.tfvars`.
  Do not introduce competing tfvars files or deployment-value locals.
- Preserve meaningful input validation; add validation when appropriate.
- Never use `terraform init -upgrade` for routine validation. It is permitted
  only within an explicitly authorized dependency-upgrade task. Preserve the
  provider lockfile in ordinary tasks and inspect its diff during upgrades.
- Follow preflight order: TFLint, formatting, validation, then plan. Missing
  prerequisites mean blocked, never passed. Rerun checks after corrective edits.
- Workflow jobs that run `terraform apply` or `terraform destroy` must use a
  protected `environment` (deploy and destroy both use `production`), and such a
  workflow keeps top-level `concurrency` with `cancel-in-progress: false`.
  `scripts/check_terraform_policy.py` enforces both.