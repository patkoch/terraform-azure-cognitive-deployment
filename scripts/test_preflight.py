import tempfile
import unittest
from pathlib import Path
from unittest import mock

import preflight


def resource(address, actions, before=None, after=None, unknown=None):
    return {"address": address, "change": {"actions": actions, "before": before,
                                           "after": after, "after_unknown": unknown or {}}}


class PreflightTests(unittest.TestCase):
    def test_plan_summary_lists_actions_without_values(self):
        plan = {"resource_changes": [
            resource("module.a.x.this", ["update"],
                     {"tags": {"k": "SECRET-OLD"}, "name": "n"},
                     {"tags": {"k": "SECRET-NEW"}, "name": "n"}),
            resource("module.b.y.this", ["delete", "create"],
                     {"sku": "SECRET-S0"}, {"sku": "SECRET-S1"}, {"id": True}),
            resource("module.c.z.this", ["no-op"], {"a": 1}, {"a": 1}),
        ]}
        summary = preflight.summarize_plan(plan)
        self.assertEqual(summary["counts"],
                         {"create": 0, "update": 1, "delete": 0, "replace": 1})
        rendered = "\n".join(preflight.render_plan(summary, "abc123"))
        self.assertNotIn("SECRET", rendered)
        self.assertIn("tags", rendered)
        self.assertIn("1 replacement(s)", rendered)

    def test_sanitize_masks_guids_and_truncates(self):
        guid = "12345678-1234-1234-1234-123456789abc"
        text = "\n".join([f"line {guid}"] + ["x"] * 100)
        result = preflight.sanitize(text, limit=5)
        self.assertNotIn(guid, result)
        self.assertIn("<guid>", result)
        self.assertIn("more lines omitted", result)

    def test_overall_status_prefers_failures_over_blocks(self):
        passed = preflight.Step("a", "passed", "ok")
        blocked = preflight.Step("b", "blocked", "x")
        failed = preflight.Step("c", "failed", "x")
        self.assertEqual(preflight.overall([passed]), "PASSED")
        self.assertEqual(preflight.overall([passed, blocked]), "BLOCKED")
        self.assertEqual(preflight.overall([passed, blocked, failed]), "FAILED")

    def test_report_marks_stale_plan_file_and_hides_subscription(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "tfplan").write_bytes(b"old")
            state = {"revision": "abc", "branch": "main", "changed": [], "diff": "",
                     "fingerprint": "f"}
            steps = [preflight.Step("plan", "blocked", "requires passing tflint")]
            with mock.patch.dict(
                    "os.environ", {"TF_VAR_subscription_id": "00000000-0000-0000-0000-00000000abcd"}):
                report = preflight.render_report(root, steps, [], state)
        self.assertIn("NOT covered by this report", report)
        self.assertIn("ends with abcd", report)
        self.assertNotIn("00000000-0000-0000-0000-00000000abcd", report)


if __name__ == "__main__":
    unittest.main()
