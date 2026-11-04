#!/usr/bin/env python3
"""Validate a project-ci.yml file against the toolkit JSON Schema."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "pipeline-config.schema.json"

TYPE_LANGUAGE = {
    "python-api": "python",
    "node-application": "node",
    "bun-frontend": "bun",
    "dockerized-application": "docker",
    "infrastructure": "terraform",
    "ansible-playbook": "ansible",
    "security-toolkit": "python",
    "backup-toolkit": "python",
}
TYPE_MANAGERS = {
    "python-api": {"pip", "poetry", "uv"},
    "node-application": {"npm", "pnpm", "yarn"},
    "bun-frontend": {"bun"},
    "dockerized-application": {"none", "pip", "poetry", "uv", "npm", "pnpm", "yarn"},
    "infrastructure": {"none"},
    "ansible-playbook": {"none"},
    "security-toolkit": {"pip", "poetry", "uv"},
    "backup-toolkit": {"pip", "poetry", "uv"},
}
DEPENDENCY_SCAN_MANAGERS = {"pip", "poetry", "uv", "npm", "pnpm", "yarn"}


class _TimestampAsStringLoader(yaml.SafeLoader):
    """Keep YAML timestamps as ISO strings so JSON Schema date fields validate."""


def _timestamp_as_string(loader: yaml.SafeLoader, node: yaml.Node) -> str:
    value = loader.construct_scalar(node)
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return str(value)
    if parsed.tzinfo is not None:
        parsed = parsed.replace(tzinfo=None)
    if parsed.time() == datetime.min.time():
        return parsed.date().isoformat()
    return parsed.isoformat()


_TimestampAsStringLoader.add_constructor("tag:yaml.org,2002:timestamp", _timestamp_as_string)


def load_config_yaml(text: str) -> Any:
    return yaml.load(text, Loader=_TimestampAsStringLoader)


def _json_pointer(path: list[Any]) -> str:
    if not path:
        return "$"
    parts = ["$"]
    for item in path:
        parts.append(f".{item}" if isinstance(item, str) else f"[{item}]")
    return "".join(parts)


def _schema_errors(config: Any, schema: dict[str, Any]) -> list[str]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors: list[str] = []
    for error in sorted(validator.iter_errors(config), key=lambda item: list(item.path)):
        errors.append(f"{_json_pointer(list(error.path))}: {error.message}")
    return errors


def _semantic_errors(config: Any) -> list[str]:
    if not isinstance(config, dict):
        return []
    errors: list[str] = []
    project = config.get("project") if isinstance(config.get("project"), dict) else {}
    runtime = config.get("runtime") if isinstance(config.get("runtime"), dict) else {}
    dependencies = (
        config.get("dependencies") if isinstance(config.get("dependencies"), dict) else {}
    )
    security = config.get("security") if isinstance(config.get("security"), dict) else {}
    deployment = config.get("deployment") if isinstance(config.get("deployment"), dict) else {}
    project_type = project.get("type")
    language = runtime.get("language")
    manager = dependencies.get("manager")
    expected_language = TYPE_LANGUAGE.get(str(project_type))
    if expected_language and language and language != expected_language:
        errors.append(
            f"$.runtime.language: must be {expected_language} when project.type is {project_type}"
        )
    allowed_managers = TYPE_MANAGERS.get(str(project_type))
    if allowed_managers and manager and manager not in allowed_managers:
        errors.append(
            f"$.dependencies.manager: must be one of {', '.join(sorted(allowed_managers))} "
            f"when project.type is {project_type}"
        )
    if security.get("dependency_scan") and manager not in DEPENDENCY_SCAN_MANAGERS:
        errors.append(
            "$.security.dependency_scan: enable only when dependencies.manager is a package manager"
        )
    environments = deployment.get("environments")
    if (
        isinstance(environments, list)
        and "production" in environments
        and deployment.get("production_requires_approval") is False
    ):
        errors.append(
            "$.deployment.production_requires_approval: must be true when production is listed"
        )
    today = date.today()
    checks = security.get("disabled_checks")
    if isinstance(checks, list):
        for index, item in enumerate(checks):
            if not isinstance(item, dict):
                continue
            review_by = item.get("review_by")
            if not isinstance(review_by, str):
                continue
            try:
                expiry = date.fromisoformat(review_by)
            except ValueError:
                continue
            if expiry < today:
                errors.append(
                    f"$.security.disabled_checks[{index}].review_by: exception expired on {review_by}"
                )
    return errors


def validate_config(config_path: Path, schema_path: Path = SCHEMA_PATH) -> list[str]:
    try:
        config = load_config_yaml(config_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        return [f"Unable to read YAML: {exc}"]
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"Unable to read schema: {exc}"]
    try:
        errors = _schema_errors(config, schema)
    except ValidationError as exc:
        return [str(exc)]
    errors.extend(_semantic_errors(config))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path, help="YAML project configuration")
    args = parser.parse_args()
    errors = validate_config(args.config)
    if errors:
        print(f"Configuration invalid: {args.config}", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"Configuration valid: {args.config}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
