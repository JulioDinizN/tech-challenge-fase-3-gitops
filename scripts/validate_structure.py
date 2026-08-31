#!/usr/bin/env python3
"""Validate the GitOps scaffold without contacting a cluster."""

from __future__ import annotations

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
SERVICES = (
    "auth-service",
    "flag-service",
    "targeting-service",
    "evaluation-service",
    "analytics-service",
)
FORBIDDEN = (
    re.compile(r"(?i)password\s*:\s*[^_<{\s]"),
    re.compile(r"(?i)auth[_-]?token\s*:\s*[^_<{\s]"),
    re.compile(r"BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY"),
)


def main() -> int:
    errors: list[str] = []
    for service in SERVICES:
        path = ROOT / "apps" / service / "overlays" / "homolog" / "kustomization.yaml"
        if not path.is_file():
            errors.append(f"missing overlay: {path.relative_to(ROOT)}")
            continue
        text = path.read_text(encoding="utf-8")
        if f"- name: togglemaster/{service}" not in text:
            errors.append(f"missing image block for {service}")

    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        if path.suffix not in {".yaml", ".yml", ".json", ".md"}:
            continue
        text = path.read_text(encoding="utf-8")
        for pattern in FORBIDDEN:
            if pattern.search(text):
                errors.append(f"possible committed secret in {path.relative_to(ROOT)}")

    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1
    print("GitOps structure is valid and no obvious secret values were found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
