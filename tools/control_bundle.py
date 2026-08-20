"""Verify the pinned FR-846 executable control bundle."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from pathlib import Path, PurePosixPath


TOP_KEYS = {"version", "source", "source_sha", "bundle_roots", "files"}
FILE_KEYS = {"source", "target", "sha256", "mode", "disposition"}
DISPOSITIONS = {"mirror", "adapt-local"}
EXPLICIT_TARGETS = {
    ".github/copilot-instructions.md",
    "scripts/author.sh",
    "scripts/author_preflight.py",
    "scripts/judge.sh",
    "scripts/review.sh",
}
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
MODE_RE = re.compile(r"^100(?:644|755)$")


class ControlBundleError(ValueError):
    """The bundle cannot be trusted as a closed pinned artifact."""


def _fail(message: str) -> None:
    raise ControlBundleError(message)


def _strict_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            _fail(f"duplicate key: {key}")
        result[key] = value
    return result


def _relative_path(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        _fail(f"{label} must be a non-empty string")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or str(path) != value:
        _fail(f"invalid {label}: {value}")
    return value


def _under_root(target: str, roots: list[str]) -> bool:
    return any(target == root or target.startswith(root + "/") for root in roots)


def _file_mode(path: Path) -> str:
    executable = bool(path.stat().st_mode & stat.S_IXUSR)
    return "100755" if executable else "100644"


def _load(path: Path) -> dict:
    try:
        return json.loads(path.read_text(), object_pairs_hook=_strict_object)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        _fail(f"manifest is not strict UTF-8 JSON: {exc}")


def verify(root: Path, manifest_path: Path) -> None:
    root = Path(root).resolve()
    manifest_path = Path(manifest_path)
    data = _load(manifest_path)
    if not isinstance(data, dict) or set(data) != TOP_KEYS:
        _fail("manifest has wrong top-level keys")
    if type(data["version"]) is not int or data["version"] != 1:
        _fail("version must be integer 1")
    if data["source"] != "https://github.com/sheikkinen/yamlgraph":
        _fail("unexpected source repository")
    if not isinstance(data["source_sha"], str) or not SHA_RE.fullmatch(
        data["source_sha"]
    ):
        _fail("source_sha must be 40 lowercase hex characters")

    roots = data["bundle_roots"]
    if (
        not isinstance(roots, list)
        or not roots
        or roots != sorted(set(roots))
        or any(_relative_path(item, "bundle root") != item for item in roots)
    ):
        _fail("bundle_roots must be a sorted unique non-empty path list")

    entries = data["files"]
    if not isinstance(entries, list) or not entries:
        _fail("files must be a non-empty list")
    targets = []
    sources = []
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != FILE_KEYS:
            _fail("file entry has wrong keys")
        source = _relative_path(entry["source"], "source")
        target = _relative_path(entry["target"], "target")
        if not _under_root(target, roots) and target not in EXPLICIT_TARGETS:
            _fail(f"target outside bundle closure: {target}")
        if not isinstance(entry["sha256"], str) or not DIGEST_RE.fullmatch(
            entry["sha256"]
        ):
            _fail(f"invalid sha256 for {target}")
        if not isinstance(entry["mode"], str) or not MODE_RE.fullmatch(entry["mode"]):
            _fail(f"invalid mode for {target}")
        if entry["disposition"] not in DISPOSITIONS:
            _fail(f"invalid disposition for {target}")
        sources.append(source)
        targets.append(target)

        path = root / target
        if path.is_symlink() or not path.is_file():
            _fail(f"missing or irregular target: {target}")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != entry["sha256"]:
            _fail(f"hash mismatch: {target}")
        if _file_mode(path) != entry["mode"]:
            _fail(f"mode mismatch: {target}")

    if targets != sorted(targets):
        _fail("file entries must be sorted by target")
    if len(targets) != len(set(targets)):
        _fail("duplicate target")
    if len(sources) != len(set(sources)):
        _fail("duplicate source")

    listed = set(targets)
    on_disk = set()
    for relative_root in roots:
        directory = root / relative_root
        if directory.is_symlink() or not directory.is_dir():
            _fail(f"missing or irregular bundle root: {relative_root}")
        for path in directory.rglob("*"):
            if path.is_symlink():
                _fail(f"symlink under bundle root: {path.relative_to(root)}")
            if path.is_file():
                on_disk.add(path.relative_to(root).as_posix())
    unlisted = sorted(on_disk - listed)
    if unlisted:
        _fail(f"unlisted file under bundle roots: {unlisted[0]}")


def main() -> int:
    root = Path(os.environ.get("GITCLAW_ROOT", Path.cwd()))
    manifest = root / "control-bundle.json"
    try:
        verify(root, manifest)
    except ControlBundleError as exc:
        print(f"control_bundle: {exc}")
        return 1
    print("control_bundle: verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())