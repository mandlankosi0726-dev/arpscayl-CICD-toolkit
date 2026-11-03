#!/usr/bin/env python3
"""Resolve reusable-workflow inputs from project-ci.yml, honoring documented exceptions."""
from __future__ import annotations

import argparse
import os
import sys
from datetime import date
from pathlib import Path
from typing import Any

try:
    from scripts.validate_config import load_config_yaml, validate_config
except ImportError:
    from validate_config import load_config_yaml, validate_config

CHECK_OUTPUTS = {
    "secret_scan": "run_secret_scan",
    "dependency_scan": "run_dependency_scan",
    "sast": "run_sast",
}


def _as_bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _github_bool(value: bool) -> str:
    return "true" if value else "false"


def active_disabled_checks(config: dict[str, Any]) -> set[str]:
    disabled: set[str] = set()
    today = date.today()
    for item in config.get("security", {}).get("disabled_checks", []) or []:
        if not isinstance(item, dict):
            continue
        review_by = item.get("review_by")
        name = item.get("check")
        if not isinstance(name, str) or not isinstance(review_by, str):
            continue
        try:
            expiry = date.fromisoformat(review_by)
        except ValueError:
            continue
        if expiry >= today:
            disabled.add(name)
    return disabled


def security_language(config: dict[str, Any]) -> str:
    language = str(config.get("runtime", {}).get("language", ""))
    if language in {"python", "node"}:
        return language
    manager = str(config.get("dependencies", {}).get("manager", ""))
    if manager in {"pip", "poetry", "uv"}:
        return "python"
    if manager in {"npm", "pnpm", "yarn"}:
        return "node"
    return language


def resolve_pipeline(config: dict[str, Any] | None, inputs: dict[str, str]) -> dict[str, str]:
    resolved = {
        "python_version": inputs.get("python_version", "3.12"),
        "node_version": inputs.get("node_version", "22"),
        "terraform_version": inputs.get("terraform_version", "1.14.6"),
        "requirements_file": inputs.get("requirements_file", "requirements.txt"),
        "dockerfile": inputs.get("dockerfile", "Dockerfile"),
        "image_name": inputs.get("image_name", ""),
        "coverage_minimum": inputs.get("coverage_minimum", "0"),
        "run_typecheck": _github_bool(_as_bool(inputs.get("run_typecheck", "false"))),
        "language": inputs.get("language", "python"),
        "run_secret_scan": _github_bool(_as_bool(inputs.get("run_secret_scan", "true"))),
        "run_dependency_scan": _github_bool(_as_bool(inputs.get("run_dependency_scan", "true"))),
        "run_sast": _github_bool(_as_bool(inputs.get("run_sast", "false"))),
        "require_non_root": _github_bool(_as_bool(inputs.get("require_non_root", "true"))),
        "scan_severity": inputs.get("scan_severity", "HIGH,CRITICAL"),
    }
    if not config:
        return resolved
    runtime = config.get("runtime", {})
    quality = config.get("quality", {})
    security = config.get("security", {})
    docker = config.get("docker", {})
    dependencies = config.get("dependencies", {})
    language = str(runtime.get("language", resolved["language"]))
    version = str(runtime.get("version", ""))
    if language == "python" and version:
        resolved["python_version"] = version
    if language == "node" and version:
        resolved["node_version"] = version
    if language == "terraform" and version:
        resolved["terraform_version"] = version
    if dependencies.get("lockfile") and language == "python":
        resolved["requirements_file"] = str(dependencies["lockfile"])
    if quality.get("typecheck") is not None:
        resolved["run_typecheck"] = _github_bool(bool(quality["typecheck"]))
    coverage = quality.get("coverage_minimum")
    if coverage is None:
        resolved["coverage_minimum"] = "0"
    elif coverage != "":
        resolved["coverage_minimum"] = str(int(coverage))
    resolved["language"] = security_language(config) or resolved["language"]
    resolved["run_secret_scan"] = _github_bool(bool(security.get("secret_scan", True)))
    resolved["run_dependency_scan"] = _github_bool(bool(security.get("dependency_scan", True)))
    resolved["run_sast"] = _github_bool(bool(security.get("sast", False)))
    for check, output_name in CHECK_OUTPUTS.items():
        if check in active_disabled_checks(config):
            resolved[output_name] = "false"
    if docker.get("dockerfile"):
        resolved["dockerfile"] = str(docker["dockerfile"])
    if docker.get("image_name"):
        resolved["image_name"] = str(docker["image_name"])
    return resolved


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--github-output", type=Path, default=None)
    args = parser.parse_args()
    config: dict[str, Any] | None = None
    if args.config is not None:
        errors = validate_config(args.config)
        if errors:
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
        loaded = load_config_yaml(args.config.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            print("ERROR: configuration must be a mapping", file=sys.stderr)
            return 1
        config = loaded
    inputs = {
        "python_version": os.environ.get("INPUT_PYTHON_VERSION", "3.12"),
        "node_version": os.environ.get("INPUT_NODE_VERSION", "22"),
        "terraform_version": os.environ.get("INPUT_TERRAFORM_VERSION", "1.14.6"),
        "requirements_file": os.environ.get("INPUT_REQUIREMENTS_FILE", "requirements.txt"),
        "dockerfile": os.environ.get("INPUT_DOCKERFILE", "Dockerfile"),
        "image_name": os.environ.get("INPUT_IMAGE_NAME", ""),
        "coverage_minimum": os.environ.get("INPUT_COVERAGE_MINIMUM", "0"),
        "run_typecheck": os.environ.get("INPUT_RUN_TYPECHECK", "false"),
        "language": os.environ.get("INPUT_LANGUAGE", "python"),
        "run_secret_scan": os.environ.get("INPUT_RUN_SECRET_SCAN", "true"),
        "run_dependency_scan": os.environ.get("INPUT_RUN_DEPENDENCY_SCAN", "true"),
        "run_sast": os.environ.get("INPUT_RUN_SAST", "false"),
        "require_non_root": os.environ.get("INPUT_REQUIRE_NON_ROOT", "true"),
        "scan_severity": os.environ.get("INPUT_SCAN_SEVERITY", "HIGH,CRITICAL"),
    }
    resolved = resolve_pipeline(config, inputs)
    destination = args.github_output or Path(os.environ.get("GITHUB_OUTPUT", "/dev/stdout"))
    with destination.open("a", encoding="utf-8") as handle:
        for key, value in resolved.items():
            handle.write(f"{key}={value}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
