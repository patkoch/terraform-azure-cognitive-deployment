"""Run the repository preflight in its required order and write a sanitized report.

The report holds statuses, counts, resource addresses and attribute names only.
Raw plan output and plan JSON are neither stored nor printed.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = Path(".preflight") / "report.md"
GUID = re.compile(r"[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}")
ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
AUTH_HINT = re.compile(
    r"AzureCli|authorizer|az login|credential|AuthorizationFailed|AuthenticationFailed"
    r"|executable file not found|\b40[13]\b",
    re.I,
)
MAX_LINES = 40
MAX_DIFF_LINES = 1500
MAX_ATTRIBUTES = 15
EXIT_CODES = {"PASSED": 0, "FAILED": 1, "BLOCKED": 2}


@dataclass
class Step:
    name: str
    status: str  # passed | failed | blocked | skipped
    summary: str
    detail: str = ""


def sanitize(text, limit=MAX_LINES):
    lines = [GUID.sub("<guid>", ANSI.sub("", line)).rstrip() for line in text.splitlines()]
    if len(lines) > limit:
        lines = lines[:limit] + [f"... {len(lines) - limit} more lines omitted"]
    return "\n".join(lines)


def run(command, root, timeout=1800, stdout_only=False):
    try:
        done = subprocess.run(command, cwd=root, capture_output=True, text=True,
                              timeout=timeout, check=False)
    except FileNotFoundError:
        return None, f"{command[0]} is not installed"
    except subprocess.TimeoutExpired:
        return None, f"{command[0]} timed out"
    return done.returncode, done.stdout if stdout_only else done.stdout + done.stderr


def finish(name, code, output):
    """Static checks: diagnostics derive from repository files, so a short excerpt is kept."""
    if code is None:
        return Step(name, "blocked", output)
    if code == 0:
        return Step(name, "passed", "ok")
    return Step(name, "failed", f"exit code {code}", sanitize(output))


def finish_remote(name, code, output):
    """Azure-facing commands: raw output is withheld, only a classification is kept."""
    if code is None:
        return Step(name, "blocked", output)
    if code == 0:
        return Step(name, "passed", "ok")
    if AUTH_HINT.search(output):
        return Step(name, "blocked", "Azure authentication or CLI unavailable (raw output withheld)")
    return Step(name, "failed", f"exit code {code} (raw output withheld; rerun in a terminal)")


def step_policy(root):
    try:
        from check_terraform_policy import check
    except ImportError as error:
        return Step("policy", "blocked",
                    f"module {error.name} missing: pip install -r scripts/requirements-checks.txt")
    errors = check(root)
    if errors:
        return Step("policy", "failed", f"{len(errors)} violation(s)", "\n".join(errors))
    return Step("policy", "passed", "ok")


def step_secrets(root):
    code, output = run(["gitleaks", "dir", ".", "--redact", "--no-banner",
                        "--max-target-megabytes", "5"], root)
    return finish("secrets", code, output)


def step_tflint(root):
    code, output = run(["tflint", "--init"], root)
    if code != 0:
        return finish("tflint", code, output)
    code, output = run(["tflint", "--format=compact"], root)
    return finish("tflint", code, output)


def step_fmt(root, check_only):
    rewritten = []
    if not check_only:
        code, output = run(["terraform", "fmt", "-recursive"], root)
        if code != 0:
            return finish("fmt", code, output)
        rewritten = output.split()
    code, output = run(["terraform", "fmt", "-check", "-recursive"], root)
    step = finish("fmt", code, output)
    if step.status == "passed" and rewritten:
        step.summary = "rewrote " + ", ".join(rewritten)
    return step


def step_validate(root):
    code, output = run(["terraform", "validate", "-no-color"], root)
    return finish("validate", code, output)


def summarize_plan(plan):
    counts = {"create": 0, "update": 0, "delete": 0, "replace": 0}
    changes = []
    for resource in plan.get("resource_changes", []):
        change = resource.get("change", {})
        actions = change.get("actions", [])
        if actions in (["no-op"], ["read"]):
            continue
        kind = "replace" if set(actions) == {"create", "delete"} else "+".join(actions)
        counts[kind] = counts.get(kind, 0) + 1
        before = change.get("before") or {}
        after = change.get("after") or {}
        unknown = change.get("after_unknown") or {}
        names = sorted(
            key for key in set(before) | set(after) | set(unknown)
            if before.get(key) != after.get(key) or unknown.get(key) is True
        )
        changes.append({"address": resource.get("address", "?"), "action": kind,
                        "attributes": names if kind in ("update", "replace") else []})
    return {"counts": counts, "changes": changes}


def render_plan(summary, digest):
    counts = summary["counts"]
    lines = [
        f"Saved plan sha256: `{digest}`",
        f"Add {counts['create']}, change {counts['update']}, "
        f"replace {counts['replace']}, destroy {counts['delete']}.",
    ]
    if counts["replace"] or counts["delete"]:
        lines.append(f"**Risk:** {counts['replace']} replacement(s) and "
                     f"{counts['delete']} deletion(s) need review before any apply.")
    if summary["changes"]:
        lines += ["", "| Resource | Action | Changed attributes (names only) |", "| --- | --- | --- |"]
        for change in summary["changes"]:
            names = change["attributes"][:MAX_ATTRIBUTES]
            more = len(change["attributes"]) - len(names)
            shown = ", ".join(names) + (f", +{more} more" if more > 0 else "")
            lines.append(f"| `{change['address']}` | {change['action']} | {shown or '-'} |")
    return lines


def plan_steps(root):
    if not os.environ.get("TF_VAR_subscription_id"):
        return Step("plan", "blocked", "TF_VAR_subscription_id is not set"), []
    code, output = run(["terraform", "plan", "-input=false", "-no-color", "-out=tfplan"], root)
    step = finish_remote("plan", code, output)
    if step.status != "passed":
        return step, []
    code, shown = run(["terraform", "show", "-json", "tfplan"], root, stdout_only=True)
    try:
        summary = summarize_plan(json.loads(shown))
    except (TypeError, ValueError):
        code = None
    if code != 0:
        return Step("plan", "failed", "plan succeeded but could not be summarized"), []
    digest = hashlib.sha256((root / "tfplan").read_bytes()).hexdigest()
    counts = summary["counts"]
    step.summary = (f"add {counts['create']}, change {counts['update']}, "
                    f"replace {counts['replace']}, destroy {counts['delete']}")
    return step, render_plan(summary, digest)


def run_steps(root, check_only):
    steps = [step_policy(root), step_secrets(root), step_tflint(root), step_fmt(root, check_only)]
    code, output = run(["terraform", "init", "-input=false", "-no-color"], root)
    init = finish_remote("init", code, output)
    steps.append(init)
    steps.append(step_validate(root) if init.status == "passed"
                 else Step("validate", "blocked", "requires a successful terraform init"))
    required = [step for step in steps if step.name in ("tflint", "fmt", "validate")]
    if any(step.status == "failed" for step in steps):
        return steps + [Step("plan", "skipped", "an earlier check failed")], []
    if any(step.status != "passed" for step in required):
        return steps + [Step("plan", "blocked", "requires passing tflint, fmt and validate")], []
    plan, plan_lines = plan_steps(root)
    return steps + [plan], plan_lines


def overall(steps):
    statuses = {step.status for step in steps}
    if "failed" in statuses:
        return "FAILED"
    return "BLOCKED" if "blocked" in statuses else "PASSED"


def git(root, *args):
    code, output = run(["git", *args], root, stdout_only=True)
    return output if code == 0 else ""


def first_line(root, command):
    code, output = run(command, root, stdout_only=True)
    return output.splitlines()[0] if code == 0 and output else "not available"


def repository_state(root):
    head = git(root, "rev-parse", "HEAD").strip()
    status = git(root, "status", "--porcelain", "--untracked-files=all")
    diff = git(root, "diff", "HEAD", "--no-color")
    digest = hashlib.sha256(head.encode() + diff.encode())
    for line in sorted(status.splitlines()):
        path = root / line[3:]
        if line.startswith("?? ") and path.is_file() and path.stat().st_size < 1_000_000:
            digest.update(line[3:].encode() + path.read_bytes())
    return {
        "revision": head[:10] or "unknown",
        "branch": git(root, "rev-parse", "--abbrev-ref", "HEAD").strip() or "unknown",
        "changed": [line[3:] for line in status.splitlines()],
        "diff": sanitize(diff, MAX_DIFF_LINES),
        "fingerprint": digest.hexdigest(),
    }


def render_table(steps):
    rows = ["| Step | Status | Summary |", "| --- | --- | --- |"]
    rows += [f"| {s.name} | {s.status} | {s.summary.replace('|', '/')} |" for s in steps]
    return rows


def render_report(root, steps, plan_lines, state):
    subscription = os.environ.get("TF_VAR_subscription_id", "")
    tools = "; ".join([first_line(root, ["terraform", "version"]),
                       first_line(root, ["tflint", "--version"])])
    lines = [
        "# Preflight report",
        "",
        "Generated by `scripts/preflight.py`. Contains statuses, counts, resource addresses and "
        "attribute names, never plan values.",
        "",
        f"Overall: **{overall(steps)}**",
        f"Generated: {datetime.now(timezone.utc):%Y-%m-%d %H:%M:%S} UTC",
        f"Revision: {state['revision']} (branch {state['branch']}), "
        f"working tree {'dirty' if state['changed'] else 'clean'}",
        f"Worktree fingerprint: `{state['fingerprint']}`",
        f"Subscription: {'set (ends with ' + subscription[-4:] + ')' if subscription else 'not set'}",
        f"Tools: {tools}",
        "",
        "## Steps",
        "",
        *render_table(steps),
    ]
    for step in steps:
        if step.detail:
            lines += ["", f"### {step.name} details", "", "```text", step.detail, "```"]
    lines += ["", "## Plan", "", *(plan_lines or ["No plan was produced by this run."])]
    if not plan_lines and (root / "tfplan").exists():
        lines += ["", "Note: a `tfplan` file from an earlier run exists and is NOT covered by this report."]
    lines += ["", "## Changed files", "",
              *([f"- `{name}`" for name in state["changed"]] or ["None."]),
              "", "## Diff against HEAD (tracked files)", "", "```diff", state["diff"], "```", ""]
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run the repository preflight and write a report.")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--ci", action="store_true",
                        help="only check formatting; do not rewrite files")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    steps, plan_lines = run_steps(root, args.ci)
    report = root / REPORT_PATH
    report.parent.mkdir(exist_ok=True)
    report.write_text(render_report(root, steps, plan_lines, repository_state(root)))
    print("\n".join(render_table(steps)))
    print(f"\nOverall: {overall(steps)}\nReport: {report}")
    return EXIT_CODES[overall(steps)]


if __name__ == "__main__":
    raise SystemExit(main())
