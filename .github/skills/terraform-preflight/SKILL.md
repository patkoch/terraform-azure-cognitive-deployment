---
name: terraform-preflight
description: "Use when: terraform preflight check, terraform lint, terraform validate, terraform fmt check, before pull request in this repository. Runs safe local checks and returns actionable findings."
---

# Terraform Preflight

## Goal
Run a safe, repeatable quality gate for Terraform changes in this repository.

## Scope
- Terraform files at repository root
- Existing module references only
- No resource creation outside normal Terraform workflow

## Steps
1. Run `terraform fmt -check -recursive` and report formatting issues.
2. Run `terraform init -upgrade -backend=false`.
3. Run `terraform validate`.
4. Run `tflint`.
5. Return a concise report with:
- checks passed
- checks failed
- likely fixes
- recommendation whether `terraform plan -out tfplan` should be run next

## Output format
- `Summary`: short status line
- `Findings`: concrete, file-oriented issues
- `Next step`: one recommended command

## Guardrails
- Do not run `terraform apply` automatically.
- Do not modify backend settings.
- Keep provider version constraints compatible with repository rules.
