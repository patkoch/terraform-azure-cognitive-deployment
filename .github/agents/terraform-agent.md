# Terraform Agent — Personalized Development Agent

This document explains how to set up and use a simple, personalized "agent" for developing and testing Terraform changes in this repository. The goal is faster feedback on changes, reproducible local workflows, and safe use in GitHub Actions.
The guidance below targets professional Terraform development practices.

## Purpose
- Automatically format, validate, and generate plans for pull requests
- Provide local helper commands for repeatable testing
- CI workflows for plan/apply using secure secrets

## Prerequisites
- Terraform (recommended: >= 1.13)
- Azure CLI (`az`) for local authentication
- `jq` (optional, for parsing `terraform show -json`)

## Local setup
1. Clone the repository and change into the project directory.
2. Install Terraform and verify:
   - `terraform --version`
3. Sign in to Azure if needed:
   - Interactive: `az login`
   - Service Principal (for automated agents):
     ```powershell
     az ad sp create-for-rbac --name "tf-agent-<your-name>" --role Contributor --scopes /subscriptions/<SUBSCRIPTION_ID>
     ```
     The command returns `appId`, `password`, and `tenant` — store these values securely as repository secrets.

## Recommended environment variables
- `ARM_SUBSCRIPTION_ID`
- `ARM_CLIENT_ID` (appId)
- `ARM_CLIENT_SECRET` (password)
- `ARM_TENANT_ID`

Set these locally for testing or rely on `az login` for interactive development.

## Local agent — example flow
Run the following locally to get quick feedback:

- Format: `terraform fmt -recursive`
- Init: `terraform init`
- Validate: `terraform validate`
- Plan: `terraform plan -out=tfplan` or `terraform plan -var-file="terraform.auto.tfvars" -out=tfplan`
- Optional: `terraform show -json tfplan | jq .` to programmatically inspect the plan output

You can bundle these commands into a small shell/PowerShell script (e.g. `scripts/agent-plan.ps1`) and adjust to your needs.

## Lint & security (recommended checks)
Add automated checks to keep code quality and security high. Run these locally and in CI:

- Formatting: `terraform fmt -recursive`
- Static analysis / linting: `tflint --init && tflint`
- Security scanning: `tfsec .` or `checkov -d .`
- Policy/unit checks: `conftest test` (Rego policies) or `opa eval` for policy-as-code
- Documentation: `terraform-docs markdown . | sed -n '1,80p'`
- Cost estimates: `infracost breakdown --path .` (optional)

Install these tools via your package manager or `brew`, `choco`, or `scoop` on Windows. Use `tfenv` to manage Terraform versions across environments.

## GitHub Actions — example (Plan on PR)
Create a workflow that runs `terraform fmt`, `terraform validate`, and `terraform plan` automatically on pull requests. Use secure secrets (`AZURE_CREDENTIALS` or the `ARM_*` variables above).

Key points:
- Store secrets in the repository settings — never in plaintext in the repo.
- Create Service Principal credentials with the minimum required permissions.
- Require additional checks (e.g. review/approval) before running `terraform apply`.

Minimal example (place in `.github/workflows/terraform-plan.yml`):

```yaml
name: Terraform Plan (PR)
on:
   pull_request:
      paths:
         - '**/*.tf'
         - '**/*.tfvars'

jobs:
   plan:
      runs-on: ubuntu-latest
      steps:
         - uses: actions/checkout@v4
         - name: Setup Terraform
            uses: hashicorp/setup-terraform@v2
            with:
               terraform_version: '1.3.7'
         - name: Terraform fmt (check)
            run: terraform fmt -check -recursive
         - name: Terraform init
            run: terraform init -input=false
         - name: Terraform validate
            run: terraform validate
         - name: Terraform plan
            run: terraform plan -out=tfplan -input=false
         - name: Upload plan artifact
            uses: actions/upload-artifact@v4
            with:
               name: tfplan
               path: tfplan
```

Key points:
- Store secrets in the repository settings — never in plaintext in the repo.
- Create Service Principal credentials with the minimum required permissions.
- Require additional checks (for example, approval) before running `terraform apply`.

## Customizing the agent
- Default tfvars: use `terraform.auto.tfvars` for development values.
- Modules/backends: adjust backend configuration for remote state when collaborating.
- Notifications: integrate Slack/Teams webhooks or `scripts/send_requests.py` to post plan results.

## Remote state & locking (Azure)
Use an Azure Storage Account with a blob container to store Terraform state and enable locking. Example `backend` block:

```hcl
terraform {
   backend "azurerm" {
      resource_group_name  = "rg-terraform-state"
      storage_account_name = "tfstateacct"
      container_name       = "tfstate"
      key                  = "env/terraform.tfstate"
   }
}
```

Create the storage account and container with soft-delete/versioning and follow Azure RBAC practices so only the CI/service principal can access the state.

## Security notes
- Never commit secrets to Git.
- Limit Service Principal permissions to the minimum required.

## Pinning providers
Pin provider versions in your configuration using a `required_providers` block to ensure reproducible runs. Example:

```hcl
terraform {
   required_providers {
      azurerm = {
         source  = "hashicorp/azurerm"
         version = ">= 3.0, < 4.0"
      }
   }
}
```

## Testing modules and automation
- For simple checks, use `terraform validate` and `terraform plan` with CI. For integration tests, consider Terratest (Go) or kitchen-terraform.
- Consider automation platforms: Atlantis, Terraform Cloud/Enterprise, or GitHub Actions with strict approval gates.
- Policy enforcement: use Sentinel (Terraform Cloud), OPA/Conftest, or Azure Policy for governance.

---
If you like, I can also:
- create a small `scripts/agent-plan.ps1` script,
- add an example GitHub Actions workflow, or
- automate the secrets/SP creation steps.

Tell me which of the three options you want.
