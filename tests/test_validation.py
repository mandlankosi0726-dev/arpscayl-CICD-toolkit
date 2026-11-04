from __future__ import annotations

import tempfile
import unittest
import json
from pathlib import Path

import yaml

from scripts.validate_config import validate_config
from scripts.validate_workflows import validate_workflows
from scripts import scaffold_project
from scripts.validate_docker import validate_dockerfile
from scripts.deployment_preflight import validate_deployment

ROOT = Path(__file__).resolve().parents[1]


class ConfigValidationTests(unittest.TestCase):
    def test_default_configuration_is_valid(self) -> None:
        self.assertEqual(validate_config(ROOT / "configs" / "defaults.yml"), [])

    def test_invalid_fields_are_reported(self) -> None:
        content = (
            (ROOT / "configs" / "defaults.yml")
            .read_text(encoding="utf-8")
            .replace("retention_days: 14", "retention_days: 0")
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.yml"
            path.write_text(content, encoding="utf-8")
            errors = validate_config(path)
        self.assertTrue(any("retention_days" in error for error in errors))

    def test_malformed_yaml_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.yml"
            path.write_text("a: [", encoding="utf-8")
            self.assertIn("Unable to read YAML", validate_config(path)[0])

    def test_template_configurations_are_valid(self) -> None:
        for template in ("python-api", "node-api", "dockerized-application", "infrastructure"):
            with self.subTest(template=template):
                path = ROOT / "templates" / template / "project-ci.yml"
                self.assertEqual(validate_config(path), [])

    def test_new_project_types_are_validated_against_their_toolchain(self) -> None:
        config = (ROOT / "configs" / "defaults.yml").read_text(encoding="utf-8")
        cases = (
            ("bun-frontend", "bun", "bun", "bun.lock"),
            ("ansible-playbook", "ansible", "none", "requirements.yml"),
            ("security-toolkit", "python", "pip", "pyproject.toml"),
            ("backup-toolkit", "python", "pip", "pyproject.toml"),
        )
        for project_type, language, manager, lockfile in cases:
            with (
                self.subTest(project_type=project_type),
                tempfile.TemporaryDirectory() as directory,
            ):
                data = yaml.safe_load(config)
                data["project"]["type"] = project_type
                data["runtime"]["language"] = language
                data["dependencies"]["manager"] = manager
                data["dependencies"]["lockfile"] = lockfile
                if manager not in {"pip", "poetry", "uv", "npm", "pnpm", "yarn"}:
                    data["security"]["dependency_scan"] = False
                path = Path(directory) / "project-ci.yml"
                path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
                self.assertEqual(validate_config(path), [])


class WorkflowValidationTests(unittest.TestCase):
    def test_toolkit_workflows_are_valid(self) -> None:
        self.assertEqual(validate_workflows(), [])

    def test_rejects_mutable_action_reference(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.yml"
            path.write_text(
                "name: test\non: push\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n",
                encoding="utf-8",
            )
            errors = validate_workflows(Path(directory))
        self.assertTrue(any("full 40-character commit SHA" in error for error in errors))

    def test_rejects_broad_permissions_and_untrusted_shell_interpolation(self) -> None:
        workflow = """name: unsafe
on:
  pull_request:
permissions: write-all
jobs:
  test:
    runs-on: ubuntu-latest
    permissions: write-all
    steps:
      - run: echo '${{ github.event.pull_request.title }}'
"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "unsafe.yml"
            path.write_text(workflow, encoding="utf-8")
            errors = validate_workflows(Path(directory))
        self.assertTrue(any("write-all" in error for error in errors))
        self.assertTrue(any("untrusted context directly into shell" in error for error in errors))

    def test_rejects_pull_request_target_checkout(self) -> None:
        workflow = """name: unsafe
on:
  pull_request_target:
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@1111111111111111111111111111111111111111
"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "unsafe.yml"
            path.write_text(workflow, encoding="utf-8")
            errors = validate_workflows(Path(directory))
        self.assertTrue(any("must not check out pull request code" in error for error in errors))

    def test_all_template_workflows_are_valid(self) -> None:
        self.assertEqual(validate_workflows(), [])


class ScaffoldTests(unittest.TestCase):
    def test_list_includes_supported_templates(self) -> None:
        self.assertEqual(
            scaffold_project.available_templates(),
            ["dockerized-application", "infrastructure", "node-api", "python-api"],
        )

    def test_refuses_to_overwrite_existing_files(self) -> None:
        original = scaffold_project.TEMPLATE_DIR
        with tempfile.TemporaryDirectory() as directory:
            template_root = Path(directory) / "templates"
            template = template_root / "sample"
            template.mkdir(parents=True)
            (template / "file.txt").write_text("template", encoding="utf-8")
            output = Path(directory) / "output"
            output.mkdir()
            (output / "file.txt").write_text("user data", encoding="utf-8")
            scaffold_project.TEMPLATE_DIR = template_root
            try:
                with self.assertRaises(FileExistsError):
                    scaffold_project.scaffold("sample", output)
            finally:
                scaffold_project.TEMPLATE_DIR = original
            self.assertEqual((output / "file.txt").read_text(encoding="utf-8"), "user data")

    def test_scaffolds_infrastructure_template(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "new-infra"
            scaffold_project.scaffold("infrastructure", output)
            self.assertIn("terraform_data", (output / "main.tf").read_text(encoding="utf-8"))
            self.assertEqual(validate_config(output / "project-ci.yml"), [])


class ExampleTests(unittest.TestCase):
    def test_node_manifest_and_lockfile_match(self) -> None:
        for base in (ROOT / "templates" / "node-api", ROOT / "examples" / "node-application"):
            manifest = json.loads((base / "package.json").read_text(encoding="utf-8"))
            lock = json.loads((base / "package-lock.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["name"], lock["name"])
            self.assertEqual(manifest["version"], lock["version"])
            self.assertEqual(manifest["scripts"].keys(), {"lint", "test", "build"})

    def test_examples_are_copies_of_their_templates(self) -> None:
        for template, example in (
            ("python-api", "python-api"),
            ("node-api", "node-application"),
            ("dockerized-application", "docker-application"),
            ("infrastructure", "infrastructure"),
        ):
            template_files = {
                p.relative_to(ROOT / "templates" / template)
                for p in (ROOT / "templates" / template).rglob("*")
                if p.is_file() and "__pycache__" not in p.parts
            }
            example_files = {
                p.relative_to(ROOT / "examples" / example)
                for p in (ROOT / "examples" / example).rglob("*")
                if p.is_file() and "__pycache__" not in p.parts
            }
            self.assertEqual(template_files, example_files)


class DockerValidationTests(unittest.TestCase):
    def validate_text(
        self,
        contents: str,
        require_non_root: bool = True,
        require_digest: bool = False,
    ) -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "Dockerfile"
            path.write_text(contents, encoding="utf-8")
            return validate_dockerfile(path, require_non_root, require_digest)

    def test_accepts_pinned_base_tag_and_non_root_user(self) -> None:
        self.assertEqual(self.validate_text("FROM python:3.12-slim\nUSER 10001:10001\n"), [])

    def test_rejects_latest_base_and_root_user(self) -> None:
        errors = self.validate_text("FROM python:latest\nUSER root\n")
        self.assertTrue(any("explicit tag or digest" in error for error in errors))
        self.assertTrue(any("must not run as root" in error for error in errors))

    def test_requires_non_root_user_when_configured(self) -> None:
        errors = self.validate_text("FROM python:3.12-slim\n")
        self.assertTrue(any("declare a non-root USER" in error for error in errors))

    def test_can_require_digest_pinned_base_images(self) -> None:
        errors = self.validate_text(
            "FROM python:3.12-slim\nUSER 10001:10001\n", require_digest=True
        )
        self.assertTrue(any("must be pinned to @sha256" in error for error in errors))

    def test_handles_multistage_build_and_platform_flag(self) -> None:
        dockerfile = "FROM --platform=linux/amd64 python:3.12-slim AS build\nRUN true\nFROM scratch\nUSER 10001\n"
        self.assertEqual(self.validate_text(dockerfile), [])


class DeploymentPreflightTests(unittest.TestCase):
    def test_accepts_immutable_image_and_safe_deployment_inputs(self) -> None:
        errors = validate_deployment(
            environment="staging",
            image="ghcr.io/acme/service@sha256:" + "a" * 64,
            host="deploy.example.com",
            user="deployer",
            service="api-service",
            host_port=8080,
            container_port=8000,
            health_path="/health",
        )
        self.assertEqual(errors, [])

    def test_rejects_mutable_image_and_shell_injection_inputs(self) -> None:
        errors = validate_deployment(
            environment="production; touch /tmp/pwned",
            image="ghcr.io/acme/service:latest",
            host="deploy.example.com;id",
            user="deployer;id",
            service="api;id",
            host_port=70000,
            container_port=0,
            health_path="/health;id",
        )
        self.assertGreaterEqual(len(errors), 7)


if __name__ == "__main__":
    unittest.main()
