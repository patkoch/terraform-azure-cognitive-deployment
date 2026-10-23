import re
import shutil
import tempfile
import unittest
from pathlib import Path

import hcl2

from check_terraform_policy import check

DEPLOY_WORKFLOW = ".github/workflows/deploy-open-ai-service.yml"


class TerraformPolicyTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        repository = Path(__file__).resolve().parents[1]
        for source in list(repository.glob("*.tf")) + [repository / "terraform.auto.tfvars"]:
            shutil.copy(source, self.root / source.name)
        workflows = self.root / ".github" / "workflows"
        workflows.mkdir(parents=True)
        for source in (repository / ".github" / "workflows").glob("*.yml"):
            shutil.copy(source, workflows / source.name)
        with (self.root / "terraform.tf").open() as stream:
            terraform = hcl2.load(stream)["terraform"][0]
        self.azurerm_constraint = terraform["required_providers"][0]["azurerm"]["version"]

    def mutate(self, filename, before, after):
        path = self.root / filename
        contents = path.read_text()
        self.assertIn(before, contents)
        path.write_text(contents.replace(before, after, 1))

    def test_current_configuration_passes(self):
        self.assertEqual(check(self.root), [])

    def test_version_constraints_cannot_be_weakened(self):
        for constraint in ("> 6.2", ">= 6.2", "= 6.2", "6.2", "~6.2", "~> 6.2, >= 6.2"):
            with self.subTest(constraint=constraint):
                self.mutate("terraform.tf", self.azurerm_constraint, constraint)
                self.assertTrue(any("AzureRM" in error for error in check(self.root)))
                self.mutate("terraform.tf", constraint, self.azurerm_constraint)

    def test_pessimistic_constraints_allow_future_versions(self):
        for constraint in ("~> 6.2", "~> 6.2.1"):
            with self.subTest(constraint=constraint):
                self.mutate("terraform.tf", self.azurerm_constraint, constraint)
                self.assertEqual(check(self.root), [])
                self.mutate("terraform.tf", constraint, self.azurerm_constraint)

    def test_remote_backend_cannot_change(self):
        self.mutate("terraform.tf", 'backend "azurerm"', 'backend "local"')
        self.assertTrue(any("backend" in error for error in check(self.root)))

    def test_defaults_are_allowlisted(self):
        self.mutate("variables.tf", 'variable "subscription_id" {',
                    'variable "subscription_id" {\n default = null')
        self.assertTrue(any("default not allowed" in error for error in check(self.root)))

    def test_hardcoded_module_input_is_rejected(self):
        self.mutate("main.tf", "var.cognitive_account_local_auth_enabled", "true")
        self.assertTrue(any("must reference" in error for error in check(self.root)))

    def test_root_resource_is_rejected(self):
        (self.root / "extra.tf").write_text('resource "example" "test" {}')
        self.assertTrue(any("resources" in error for error in check(self.root)))

    def test_unapproved_module_ref_is_rejected(self):
        self.mutate("main.tf", "?ref=v2.0.0", "?ref=main")
        self.assertTrue(any("release source" in error for error in check(self.root)))

    def test_sensitive_input_is_rejected_without_disclosure(self):
        self.mutate("variables.tf", 'variable "subscription_id" {',
                    'variable "subscription_id" {\n sensitive = true')
        tfvars = self.root / "terraform.auto.tfvars"
        contents, replacements = re.subn(
            r'(?m)^subscription_id\s*=\s*"[^"]*"\s*$',
            'subscription_id = "do-not-disclose-this"',
            tfvars.read_text(),
            count=1,
        )
        self.assertEqual(replacements, 1)
        tfvars.write_text(contents)
        errors = check(self.root)
        self.assertTrue(any("sensitive input forbidden" in error for error in errors))
        self.assertNotIn("do-not-disclose-this", "\n".join(errors))

    def test_competing_tfvars_is_rejected(self):
        (self.root / "terraform.tfvars").write_text("")
        self.assertTrue(any("competing" in error for error in check(self.root)))

    def drop_environment(self, occurrence):
        path = self.root / DEPLOY_WORKFLOW
        text = path.read_text()
        matches = list(re.finditer(r"^ +environment: production *\n", text, re.M))
        self.assertGreaterEqual(len(matches), 2)
        match = matches[occurrence]
        path.write_text(text[:match.start()] + text[match.end():])

    def test_deploy_and_destroy_jobs_require_environment(self):
        for occurrence, job in ((0, "deploy"), (1, "destroy")):
            with self.subTest(job=job):
                self.setUp()
                self.drop_environment(occurrence)
                errors = check(self.root)
                self.assertTrue(any(f"job {job} runs terraform" in error for error in errors))

    def test_apply_workflow_requires_safe_concurrency(self):
        path = self.root / DEPLOY_WORKFLOW
        original = path.read_text()
        path.write_text(re.sub(r"^concurrency:\n(?:  .*\n)+", "", original, flags=re.M))
        self.assertTrue(any("need top-level concurrency" in error for error in check(self.root)))
        path.write_text(original.replace("cancel-in-progress: false", "cancel-in-progress: true"))
        self.assertTrue(any("must not cancel" in error for error in check(self.root)))


if __name__ == "__main__":
    unittest.main()