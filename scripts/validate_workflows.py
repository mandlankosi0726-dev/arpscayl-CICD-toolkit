#!/usr/bin/env python3
"""Check workflow YAML syntax and enforce immutable third-party action refs."""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DIR = ROOT / ".github" / "workflows"
SHA_REF = re.compile(r"^[^/@]+/[^@]+@[0-9a-fA-F]{40}$")
WORKFLOW_REF = re.compile(
    r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/\.github/workflows/[A-Za-z0-9_.-]+\.ya?ml@(?:v\d+\.\d+\.\d+|[0-9a-fA-F]{40})$"
)
DOCKER_REF = re.compile(r"^docker://.+\@sha256:[0-9a-fA-F]{64}$")
UNTRUSTED_SHELL_EXPRESSION = re.compile(
    r"\$\{\{\s*(?:github\.event(?:\.|\b)|github\.head_ref\b|inputs\.)"
)


def trigger_event_names(trigger: Any) -> set[str]:
    if trigger is None:
        return set()
    if isinstance(trigger, str):
        return {trigger}
    if isinstance(trigger, list):
        names: set[str] = set()
        for item in trigger:
            names |= trigger_event_names(item)
        return names
    if isinstance(trigger, dict):
        return {str(key) for key in trigger}
    return set()


def untrusted_interpolation_locations(value: Any, prefix: str) -> list[str]:
    found: list[str] = []
    if isinstance(value, str):
        if UNTRUSTED_SHELL_EXPRESSION.search(value):
            found.append(prefix)
        return found
    if isinstance(value, dict):
        for key, item in value.items():
            found.extend(untrusted_interpolation_locations(item, f"{prefix}.{key}"))
        return found
    if isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(untrusted_interpolation_locations(item, f"{prefix}[{index}]"))
    return found


def validate_workflows(workflow_dir: Path | None = None) -> list[str]:
    errors: list[str] = []
    if workflow_dir is None:
        workflow_dirs = [WORKFLOW_DIR]
        for base in (ROOT / "templates", ROOT / "examples"):
            if base.exists():
                workflow_dirs.extend(base.rglob(".github/workflows"))
    else:
        workflow_dirs = [workflow_dir]
    files = sorted({path for directory in workflow_dirs for path in directory.rglob("*.yml")})
    files.extend(sorted({path for directory in workflow_dirs for path in directory.rglob("*.yaml")}))
    if not files:
        return [f"No workflow YAML files found in {workflow_dir}"]
    for path in files:
        try:
            workflow = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
        except (OSError, yaml.YAMLError) as exc:
            errors.append(f"{path.name}: invalid YAML: {exc}")
            continue
        if not isinstance(workflow, dict) or "jobs" not in workflow:
            errors.append(f"{path.name}: expected a workflow mapping with jobs")
            continue
        jobs = workflow["jobs"]
        if not isinstance(jobs, dict):
            errors.append(f"{path.name}: jobs must be a mapping")
            continue
        for scope_name, permissions in (("workflow", workflow.get("permissions")),):
            if permissions == "write-all":
                errors.append(f"{path.name}: {scope_name} permissions must not use write-all")
            elif permissions is not None and not isinstance(permissions, dict):
                errors.append(f"{path.name}: permissions must be a least-privilege mapping")
        has_pull_request_target = "pull_request_target" in trigger_event_names(workflow.get("on"))
        for job_name, job in jobs.items():
            if not isinstance(job, dict):
                errors.append(f"{path.name}: job {job_name} must be a mapping")
                continue
            job_permissions = job.get("permissions")
            if job_permissions == "write-all":
                errors.append(f"{path.name}: job {job_name} permissions must not use write-all")
            elif job_permissions is not None and not isinstance(job_permissions, dict):
                errors.append(f"{path.name}: job {job_name} permissions must be a least-privilege mapping")
            job_ref = job.get("uses")
            if job_ref:
                if job_ref.startswith("./"):
                    if not job_ref.startswith("./.github/workflows/"):
                        errors.append(
                            f"{path.name}: local reusable workflows must be under .github/workflows: {job_ref}"
                        )
                elif not WORKFLOW_REF.fullmatch(job_ref):
                    errors.append(
                        f"{path.name}: reusable workflow must use a semver release or full commit SHA: {job_ref}"
                    )
            steps = job.get("steps", [])
            if not isinstance(steps, list):
                errors.append(f"{path.name}: job {job_name} steps must be a sequence")
                continue
            for index, step in enumerate(steps):
                if not isinstance(step, dict):
                    errors.append(f"{path.name}: job {job_name} step {index + 1} must be a mapping")
                    continue
                step_label = f"job {job_name} step {index + 1}"
                ref = step.get("uses")
                if ref:
                    if ref.startswith("docker://"):
                        if not DOCKER_REF.fullmatch(ref):
                            errors.append(
                                f"{path.name}: {step_label} docker:// image must pin @sha256:<64 hex characters>: {ref}"
                            )
                    elif not ref.startswith("./") and not SHA_REF.fullmatch(ref):
                        errors.append(
                            f"{path.name}: {step_label} action must pin a full 40-character commit SHA: {ref}"
                        )
                for field in ("run", "with", "env"):
                    for location in untrusted_interpolation_locations(step.get(field), field):
                        errors.append(
                            f"{path.name}: {step_label} interpolates untrusted context in {location}; "
                            "pass it via env and reference the environment variable"
                        )
            if has_pull_request_target and any(
                isinstance(step, dict) and str(step.get("uses", "")).startswith("actions/checkout@")
                for step in steps
            ):
                errors.append(f"{path.name}: pull_request_target workflows must not check out pull request code")
    return errors


def main() -> int:
    errors = validate_workflows()
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Workflow YAML is valid; all third-party actions use immutable SHA references.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
