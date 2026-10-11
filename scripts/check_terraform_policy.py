import argparse
import re
from pathlib import Path

import hcl2
import yaml


EXPECTED_BACKEND = {
    "resource_group_name": "azureworkshop-demo-rg",
    "storage_account_name": "azureworkshopdemostorage",
    "container_name": "tfstateopenai",
    "key": "terraform.tfstate",
}
EXPECTED_MODULES = ("resource_group", "cognitive_account", "cognitive_deployment")
PESSIMISTIC_CONSTRAINT = re.compile(r"~>\s+[0-9]+\.[0-9]+(?:\.[0-9]+)?")
REFERENCE = re.compile(
    r'^\$\{(?:var\.[a-zA-Z_][a-zA-Z_0-9]*|'
    r'module\.[a-zA-Z_][a-zA-Z_0-9]*\.[a-zA-Z_][a-zA-Z_0-9]*\["main"\])\}$'
)
SECRET_NAME = re.compile(r"password|secret|token|api_?key|private_?key|certificate", re.I)
MUTATING_COMMAND = re.compile(r"\bterraform\s+(?:-chdir=\S+\s+)?(?:apply|destroy)\b")


def check_workflows(root, errors):
    directory = root / ".github" / "workflows"
    if not directory.is_dir():
        return
    for path in sorted(directory.glob("*.y*ml")):
        name = f".github/workflows/{path.name}"
        try:
            workflow = yaml.safe_load(path.read_text()) or {}
        except yaml.YAMLError:
            errors.append(f"{name}: cannot parse YAML (details suppressed)")
            continue
        mutating_jobs = []
        for job_name, job in (workflow.get("jobs") or {}).items():
            steps = job.get("steps") or [] if isinstance(job, dict) else []
            if not any(isinstance(step, dict) and MUTATING_COMMAND.search(str(step.get("run", "")))
                       for step in steps):
                continue
            mutating_jobs.append(job_name)
            if not job.get("environment"):
                errors.append(
                    f"{name}: job {job_name} runs terraform apply/destroy without an environment"
                )
        if not mutating_jobs:
            continue
        concurrency = workflow.get("concurrency")
        if not concurrency:
            errors.append(f"{name}: workflows with apply/destroy jobs need top-level concurrency")
        elif isinstance(concurrency, dict) and concurrency.get("cancel-in-progress") is True:
            errors.append(f"{name}: concurrency must not cancel running apply/destroy jobs")


def check(root):
    errors = []
    documents = {}
    for path in sorted(root.glob("*.tf")):
        try:
            with path.open() as stream:
                documents[path.name] = hcl2.load(stream)
        except Exception:
            errors.append(f"{path.name}: cannot parse HCL (details suppressed)")
    try:
        with (root / "terraform.auto.tfvars").open() as stream:
            values = hcl2.load(stream)
    except Exception:
        values = {}
        errors.append("terraform.auto.tfvars: cannot parse HCL (details suppressed)")

    for required in ("terraform.tf", "variables.tf", "main.tf"):
        if required not in documents:
            errors.append(f"{required}: required configuration missing")
    for filename, document in documents.items():
        if "resource" in document or "locals" in document:
            errors.append(f"{filename}: root resources and deployment locals are forbidden")
        if filename != "variables.tf" and "variable" in document:
            errors.append(f"{filename}: declare root variables only in variables.tf")
        if filename != "terraform.tf" and "terraform" in document:
            errors.append(f"{filename}: declare versions/backend only in terraform.tf")
        if filename != "main.tf" and "module" in document:
            errors.append(f"{filename}: declare module composition only in main.tf")

    terraform_blocks = documents.get("terraform.tf", {}).get("terraform", [])
    if len(terraform_blocks) != 1:
        errors.append("terraform.tf: exactly one terraform block is required")
    else:
        terraform = terraform_blocks[0]
        providers = terraform.get("required_providers", [])
        azurerm = providers[0].get("azurerm", {}) if len(providers) == 1 else {}
        if not isinstance(azurerm, dict) or azurerm.get("source") != "hashicorp/azurerm":
            errors.append("terraform.tf: preserve the AzureRM provider source")
        else:
            constraint = azurerm.get("version")
            if not isinstance(constraint, str) or not PESSIMISTIC_CONSTRAINT.fullmatch(constraint):
                errors.append("terraform.tf: AzureRM must use a single ~> version constraint")
        if terraform.get("required_version") != "~> 1.16.4":
            errors.append("terraform.tf: preserve exact Terraform ~> 1.16.4 constraint")
        if terraform.get("backend") != [{"azurerm": EXPECTED_BACKEND}]:
            errors.append("terraform.tf: preserve the configured Azure remote backend exactly")

    variables = {}
    for block in documents.get("variables.tf", {}).get("variable", []):
        for name, definition in block.items():
            if name in variables:
                errors.append(f"variables.tf: duplicate variable {name}")
            variables[name] = definition
            if "type" not in definition or not definition.get("description"):
                errors.append(f"variables.tf: {name} needs type and description")
            if "default" in definition and (
                name != "resource_group_tags"
                or definition["default"] != {"ManagedBy": "Terraform"}
            ):
                errors.append(f"variables.tf: default not allowed for {name}")

    for name in values:
        definition = variables.get(name)
        if definition is None:
            errors.append("terraform.auto.tfvars: undeclared input found (name suppressed)")
        elif definition.get("sensitive") or SECRET_NAME.search(name):
            errors.append("terraform.auto.tfvars: sensitive input forbidden (name suppressed)")
    for name, definition in variables.items():
        if name != "subscription_id" and not definition.get("sensitive"):
            if name not in values and "default" not in definition:
                errors.append(f"terraform.auto.tfvars: required non-sensitive input {name} missing")
    for path in root.iterdir():
        if (path.name.endswith((".tfvars", ".tfvars.json"))
                and path.name != "terraform.auto.tfvars"):
            errors.append("root: competing tfvars file forbidden")

    def inspect_inputs(value, location):
        if isinstance(value, dict):
            for key, child in value.items():
                inspect_inputs(child, f"{location}.{key}")
        elif not isinstance(value, str) or not REFERENCE.fullmatch(value):
            errors.append(f"main.tf: {location} must reference a variable or module output")

    main = documents.get("main.tf", {})
    if set(main) - {"module", "moved"}:
        errors.append("main.tf: only module and moved blocks are allowed")
    modules = {}
    for block in main.get("module", []):
        for name, definition in block.items():
            if name in modules:
                errors.append(f"main.tf: duplicate module {name}")
            modules[name] = definition
            expected_source = (
                "git::https://github.com/patkoch/terraform-modules//azurerm/"
                f"{name.replace('_', '-')}?ref=v2.0.0"
            )
            if definition.get("source") != expected_source:
                errors.append(f"main.tf: preserve approved release source for {name}")
            if set(definition) - {"source", "instances", "depends_on"}:
                errors.append(f"main.tf: unexpected module arguments for {name}")
            instances = definition.get("instances", {})
            if not isinstance(instances, dict) or set(instances) != {"main"}:
                errors.append(f"main.tf: preserve stable main instance for {name}")
            else:
                inspect_inputs(instances["main"], name)
            dependencies = definition.get("depends_on", [])
            if not isinstance(dependencies, list) or any(
                not isinstance(dependency, str)
                or not re.fullmatch(r"\$\{module\.[a-zA-Z_][a-zA-Z_0-9]*\}", dependency)
                for dependency in dependencies
            ):
                errors.append(f"main.tf: invalid dependency references for {name}")
    if set(modules) != set(EXPECTED_MODULES):
        errors.append("main.tf: preserve the approved module composition")
    check_workflows(root, errors)
    return errors


def main():
    parser = argparse.ArgumentParser(description="Check root Terraform invariants without Azure access")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors = check(args.root)
    for error in errors:
        print(error)
    if not errors:
        print("Terraform policy checks passed (secret scanning is a separate check).")
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())