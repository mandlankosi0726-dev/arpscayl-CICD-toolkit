#!/usr/bin/env python3
"""Perform small deterministic Dockerfile checks before an image build."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

DIGEST = re.compile(r"@sha256:[0-9a-fA-F]{64}(?:$|[ \t])")


def _logical_instructions(lines: list[str]) -> list[tuple[str, str, int]]:
    instructions: list[tuple[str, str, int]] = []
    buffer: list[str] = []
    start: int | None = None
    for number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if start is None:
            start = number
        continued = stripped.endswith("\\")
        piece = stripped[:-1].rstrip() if continued else stripped
        buffer.append(piece)
        if continued:
            continue
        combined = " ".join(item for item in buffer if item)
        buffer = []
        origin = start
        start = None
        match = re.match(r"([A-Za-z]+)\s+(.*)", combined)
        if match:
            instructions.append((match.group(1).upper(), match.group(2).strip(), origin))
    return instructions


def validate_dockerfile(
    path: Path,
    require_non_root: bool = True,
    require_digest: bool = True,
) -> list[str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return [f"Unable to read Dockerfile: {exc}"]

    instructions = _logical_instructions(lines)
    errors: list[str] = []
    from_instructions = [(argument, line) for name, argument, line in instructions if name == "FROM"]
    if not from_instructions:
        errors.append("Dockerfile must include at least one FROM instruction")
    for argument, line in from_instructions:
        tokens = argument.split()
        image = next((token for token in tokens if not token.startswith("--") and token.upper() != "AS"), "")
        if image == "scratch":
            continue
        if require_digest:
            if not DIGEST.search(image):
                errors.append(f"line {line}: base image '{image}' must be pinned to @sha256:<64 hex characters>")
        elif image.endswith(":latest") or (":" not in image and "@sha256:" not in image):
            errors.append(f"line {line}: base image '{image}' must use an explicit tag or digest")

    final_stage: list[tuple[str, str, int]] = []
    for instruction in instructions:
        if instruction[0] == "FROM":
            final_stage = []
        final_stage.append(instruction)
    user_instructions = [(argument, line) for name, argument, line in final_stage if name == "USER"]
    if user_instructions:
        user, line = user_instructions[-1]
        if user.lower() in {"root", "0", "0:0"} or user.lower().startswith("root:"):
            errors.append(f"line {line}: final image must not run as root")
    elif require_non_root:
        errors.append("final build stage must declare a non-root USER")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dockerfile", type=Path)
    parser.add_argument("--allow-root", action="store_true", help="allow a final stage without a non-root USER")
    parser.add_argument(
        "--allow-mutable-tag",
        action="store_true",
        help="allow a tagged base image that is not pinned by digest",
    )
    args = parser.parse_args()
    errors = validate_dockerfile(
        args.dockerfile,
        require_non_root=not args.allow_root,
        require_digest=not args.allow_mutable_tag,
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"Dockerfile checks passed: {args.dockerfile}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
