#!/usr/bin/env python3
"""Validate immutable container deployment inputs before credentials are used."""
from __future__ import annotations

import argparse
import re
import sys

IMAGE_REF = re.compile(r"^[a-z0-9.-]+(?::[0-9]+)?/[a-z0-9._/-]+@sha256:[0-9a-f]{64}$")
HOST_DNS = re.compile(r"^(?=.{1,253}$)(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)*)$")
IPV4 = re.compile(r"^(\d{1,3})(?:\.(\d{1,3})){3}$")
IPV6 = re.compile(r"^(?:[0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}$")
IDENTIFIER = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,62}$")


def _valid_host(host: str) -> bool:
    if not host or ".." in host or "/" in host or " " in host:
        return False
    if IPV4.fullmatch(host):
        return all(0 <= int(part) <= 255 for part in host.split("."))
    if ":" in host:
        return bool(IPV6.fullmatch(host)) and host.count("::") <= 1
    return bool(HOST_DNS.fullmatch(host))


def validate_deployment(
    *, environment: str, image: str, host: str, user: str, service: str,
    host_port: int, container_port: int, health_path: str,
    ssh_port: int = 22,
) -> list[str]:
    errors: list[str] = []
    if environment not in {"development", "staging", "production"}:
        errors.append("environment must be development, staging, or production")
    if not IMAGE_REF.fullmatch(image):
        errors.append("image must be a registry reference pinned to @sha256:<64 lowercase hex characters>")
    if not _valid_host(host):
        errors.append("host must be a DNS name, IPv4 address, or IPv6 address, without shell syntax")
    if not IDENTIFIER.fullmatch(user):
        errors.append("user must contain only letters, digits, dot, underscore, or hyphen")
    if not IDENTIFIER.fullmatch(service):
        errors.append("service must contain only letters, digits, dot, underscore, or hyphen")
    for name, port in (("host-port", host_port), ("container-port", container_port), ("ssh-port", ssh_port)):
        if not 1 <= port <= 65535:
            errors.append(f"{name} must be between 1 and 65535")
    if not re.fullmatch(r"/[A-Za-z0-9_./-]*", health_path) or ".." in health_path.split("/"):
        errors.append("health-path must be an absolute URL path without traversal or shell syntax")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--environment", required=True)
    parser.add_argument("--image", required=True)
    parser.add_argument("--host", required=True)
    parser.add_argument("--user", required=True)
    parser.add_argument("--service", required=True)
    parser.add_argument("--host-port", required=True, type=int)
    parser.add_argument("--container-port", required=True, type=int)
    parser.add_argument("--health-path", required=True)
    parser.add_argument("--ssh-port", type=int, default=22)
    args = parser.parse_args()
    errors = validate_deployment(
        environment=args.environment, image=args.image, host=args.host, user=args.user,
        service=args.service, host_port=args.host_port, container_port=args.container_port,
        health_path=args.health_path,
        ssh_port=args.ssh_port,
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Deployment inputs are valid; the image reference is immutable.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
