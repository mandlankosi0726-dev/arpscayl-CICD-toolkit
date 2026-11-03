#!/usr/bin/env python3
"""List or copy a toolkit template without silently overwriting files."""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = ROOT / "templates"


def available_templates(template_dir: Path | None = None) -> list[str]:
    template_dir = TEMPLATE_DIR if template_dir is None else template_dir
    return sorted(path.name for path in template_dir.iterdir() if path.is_dir()) if template_dir.exists() else []


def scaffold(template: str, output: Path, overwrite: bool = False) -> None:
    source = TEMPLATE_DIR / template
    if template not in available_templates() or not source.is_dir():
        raise ValueError(f"Unknown template '{template}'. Available: {', '.join(available_templates()) or '(none yet)'}")
    if output.exists() and any(output.iterdir()) and not overwrite:
        raise FileExistsError(f"Output directory is not empty: {output}; use --overwrite to replace matching files")
    output.mkdir(parents=True, exist_ok=True)
    for item in source.iterdir():
        destination = output / item.name
        if destination.exists() and not overwrite:
            raise FileExistsError(f"Refusing to overwrite {destination}; use --overwrite")
        if item.is_dir():
            shutil.copytree(item, destination, dirs_exist_ok=overwrite)
        else:
            shutil.copy2(item, destination)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="list available templates")
    parser.add_argument("--template", help="template name (python-api, node-api, dockerized-application, or infrastructure)")
    parser.add_argument("--output", type=Path, help="destination directory")
    parser.add_argument("--overwrite", action="store_true", help="allow replacing matching files")
    args = parser.parse_args()
    if args.list:
        names = available_templates()
        print("\n".join(names) if names else "No templates are available yet.")
        return 0
    if not args.template or not args.output:
        parser.error("--template and --output are required unless --list is used")
    try:
        scaffold(args.template, args.output, args.overwrite)
    except (OSError, ValueError) as exc:
        print(f"Scaffolding failed: {exc}", file=sys.stderr)
        return 1
    print(f"Created {args.template} project at {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
