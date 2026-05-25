---
name: terraform-plan-review
description: "Use when: terraform plan review, summarize tfplan, explain infrastructure changes for pull request, assess risk before apply in this repository."
---

# Terraform Plan Review

## Goal
Generate and review a Terraform plan, then explain expected infrastructure changes in plain language.

## Preconditions
- Repository is initialized (`terraform init` completed)
- Variables are available in `terraform.auto.tfvars`

## Steps
1. Run `terraform plan -out tfplan`.
2. Run `terraform show tfplan`.
3. Summarize:
- resources to add
- resources to change
- resources to destroy
- important attribute changes
4. Call out risk areas:
- destructive changes
- naming/location changes
- cost-relevant changes where obvious
5. Provide a short PR-ready summary text.

## Output format
- `Plan summary`: add/change/destroy counts
- `Change details`: important resource-level changes
- `Risk notes`: potential impact
- `PR text`: 3-6 lines, ready to paste

## Guardrails
- Do not run `terraform apply` automatically.
- If plan fails, report exact error and likely fix.
- Keep explanation concise and review-oriented.
