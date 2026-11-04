from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from scripts.validate_workflows import validate_workflows

ROOT = Path(__file__).resolve().parents[1]
VALIDATION_WORKFLOWS = (
    "ci-bun.yml",
    "ci-python.yml",
    "ci-docker.yml",
    "ci-terraform.yml",
    "ci-ansible.yml",
    "ci-security.yml",
    "ci-backup.yml",
)


def load_workflow(path: Path) -> dict:
    return yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)


class WorkflowContractTests(unittest.TestCase):
    def test_all_workflows_pass_static_validation(self) -> None:
        self.assertEqual(validate_workflows(), [])

    def test_validation_workflows_are_read_only_and_secret_free(self) -> None:
        for name in VALIDATION_WORKFLOWS:
            with self.subTest(workflow=name):
                workflow = load_workflow(ROOT / ".github" / "workflows" / name)
                self.assertEqual(workflow["permissions"], {"contents": "read"})
                self.assertIn("workflow_call", workflow["on"])
                self.assertNotIn("secrets", workflow["on"]["workflow_call"])
                for job in workflow["jobs"].values():
                    self.assertNotIn("environment", job)

    def test_python_ci_exposes_common_backend_checks(self) -> None:
        workflow = load_workflow(ROOT / ".github" / "workflows" / "ci-python.yml")
        inputs = workflow["on"]["workflow_call"]["inputs"]
        for name in ("run-compileall", "run-pip-check", "run-pip-audit", "run-typecheck"):
            self.assertIn(name, inputs)
        run_steps = "\n".join(
            step.get("run", "") for job in workflow["jobs"].values() for step in job["steps"]
        )
        for command in ("compileall", "pip check", "pip_audit", "pytest", "ruff check"):
            self.assertIn(command, run_steps)

    def test_terraform_and_ansible_checks_do_not_apply_or_connect(self) -> None:
        terraform = load_workflow(ROOT / ".github" / "workflows" / "ci-terraform.yml")
        self.assertEqual(
            terraform["on"]["workflow_call"]["inputs"]["terraform-version"]["default"], "1.10.5"
        )
        terraform_runs = "\n".join(
            step.get("run", "") for job in terraform["jobs"].values() for step in job["steps"]
        )
        self.assertIn("terraform init -backend=false", terraform_runs)
        self.assertNotIn("terraform plan", terraform_runs)
        self.assertNotIn("terraform apply", terraform_runs)

        ansible = load_workflow(ROOT / ".github" / "workflows" / "ci-ansible.yml")
        ansible_runs = "\n".join(
            step.get("run", "") for job in ansible["jobs"].values() for step in job["steps"]
        )
        self.assertIn("inventories/development/hosts.yml", ansible_runs)
        self.assertIn("--syntax-check", ansible_runs)
        self.assertNotIn("--become", ansible_runs)

    def test_template_and_consumer_examples_have_explicit_permissions(self) -> None:
        workflow_dirs = [ROOT / ".github" / "workflows"]
        for base in (ROOT / "templates", ROOT / "examples"):
            workflow_dirs.extend(base.rglob(".github/workflows"))
        paths = {p for directory in workflow_dirs for p in directory.rglob("*.yml")}
        paths.update(p for directory in workflow_dirs for p in directory.rglob("*.yaml"))
        for path in paths:
            with self.subTest(workflow=path.relative_to(ROOT)):
                self.assertIsInstance(load_workflow(path).get("permissions"), dict)

    def test_consumer_examples_are_read_only_pr_and_main_callers(self) -> None:
        examples = sorted((ROOT / "examples" / "consumers").glob("*/.github/workflows/ci.yml"))
        self.assertEqual(len(examples), 7)
        for path in examples:
            with self.subTest(workflow=path.relative_to(ROOT)):
                workflow = load_workflow(path)
                self.assertEqual(workflow["permissions"], {"contents": "read"})
                self.assertIn("pull_request", workflow["on"])
                self.assertIn("main", workflow["on"]["push"]["branches"])
                for job in workflow["jobs"].values():
                    self.assertTrue(job["uses"].startswith("your-org/arpscayl-CICD-toolkit/"))
                    self.assertNotIn("secrets", job)
                    self.assertNotIn("environment", job)

    def test_publish_write_permission_is_isolated_from_build_and_pr(self) -> None:
        workflow = load_workflow(ROOT / ".github" / "workflows" / "docker-build-publish.yml")
        jobs = workflow["jobs"]
        self.assertEqual(workflow["permissions"], {"contents": "read"})
        self.assertNotIn("packages", jobs["build-verify"].get("permissions", {}))
        self.assertEqual(jobs["publish"]["permissions"]["packages"], "write")
        self.assertIn("github.event_name == 'push'", jobs["publish"]["if"])
        self.assertIn("refs/heads/main", jobs["publish"]["if"])

    def test_deployment_is_reusable_and_requires_an_environment(self) -> None:
        workflow = load_workflow(ROOT / ".github" / "workflows" / "deploy-container.yml")
        self.assertIn("workflow_call", workflow["on"])
        self.assertNotIn("pull_request", workflow["on"])
        self.assertIn("environment", workflow["jobs"]["deploy"])

    def test_workflow_validator_rejects_missing_permissions(self) -> None:
        workflow = "name: test\non: push\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - run: true\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing-permissions.yml"
            path.write_text(workflow, encoding="utf-8")
            errors = validate_workflows(Path(directory))
        self.assertTrue(any("permissions must be declared explicitly" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
