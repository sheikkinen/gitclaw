"""Operation-aware write containment for the generic executor."""

from __future__ import annotations

import posixpath


PLATFORM_PREFIXES = (
    ".github/",
    "scripts/",
    "tools/",
    "prompts/",
    "policy/",
)
PLATFORM_FILES = {"gitclaw.yaml", "control-bundle.json", "control-bundle-trace.md"}


def normalized(path: str) -> str:
    value = path.rstrip("/")
    norm = posixpath.normpath(value)
    if not value or norm != value or value.startswith("/") or ".." in value.split("/"):
        raise ValueError(f"unsafe path: {path}")
    return norm


def violations(paths: list[str], operation: str, expected: set[str] | None = None) -> list[str]:
    bad = []
    expected = expected or set()
    for raw in paths:
        try:
            path = normalized(raw)
        except ValueError:
            bad.append(raw)
            continue
        if operation in {"plan", "review"}:
            if path not in expected:
                bad.append(raw)
            continue
        if path in PLATFORM_FILES or path.startswith(PLATFORM_PREFIXES):
            bad.append(raw)
        elif path.endswith("/request.json") or path.startswith("feature-requests/"):
            bad.append(raw)
    return bad
