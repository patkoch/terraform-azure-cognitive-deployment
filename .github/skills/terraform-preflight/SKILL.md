---
name: terraform-preflight
description: "Use when: checking root Terraform or workflow changes before a PR. Runs TFLint, fmt, validate, then plan and reports policy and secret-scan results."
---

# Terraform Preflight

Read [shared rules](../../copilot-instructions.md). Work from this repository's
root, never from the separate module repository.

## Run

Run `python3 scripts/preflight.py` from the repository root after the last edit.
It executes the order below and writes the sanitized report `.preflight/report.md`
(gitignored), which the Reviewer reads. If `python-hcl2` or `PyYAML` is missing,
use the `.venv-checks` interpreter described in the README. `--ci` checks
formatting without rewriting files. Exit code: 0 passed, 1 failed, 2 blocked.

Prerequisites are Terraform, TFLint, Gitleaks, the policy dependencies, Azure
authentication, `TF_VAR_subscription_id`, and remote backend access. The script
reports a missing prerequisite as blocked, never as passed. Do not silently
install or upgrade tools, and never print secrets.

## Order

1. Policy check (`scripts/check_terraform_policy.py`: versions, backend, modules,
   defaults, workflows) and Gitleaks secret scan.
2. `tflint --init`, then `tflint --format=compact`.
3. `terraform fmt -recursive` locally (CI: check only), then `terraform fmt -check -recursive`.
4. `terraform init -input=false` against the remote backend (never `-upgrade`),
   then `terraform validate -no-color`.
5. Only if TFLint, fmt, and validate passed:
   `terraform plan -input=false -no-color -out=tfplan`. Keep state locking enabled.
   Never use local state, `-target`, `-refresh=false`, or backend bypasses.
6. Review the plan with [terraform-plan-review](../terraform-plan-review/SKILL.md).

On failure, repair only in-scope issues and rerun everything. Missing tools,
credentials, network, or backend access block dependent steps. Independent
static steps still run but do not make a full preflight.
Never apply, destroy, mutate state, or run `init -upgrade`.

## Report

The terminal prints a status table. `.preflight/report.md` adds the revision,
a worktree fingerprint, the saved plan's sha256, plan counts with resource
addresses and changed attribute names (never values), changed files, and the
diff against HEAD. Raw plan, plan JSON, and state are never written or pasted.
State passed, failed, or blocked per step and a concrete next action.
