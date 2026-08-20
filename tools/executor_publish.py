"""Publish a verified executor report using Git/GitHub side effects."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path


class PublishError(ValueError):
    pass


def _run(*args: str, capture: bool = False) -> str:
    result = subprocess.run(args, check=True, text=True, capture_output=capture)
    return result.stdout.strip() if capture else ""


def publish(report_path: Path, repository: str, issue: int) -> dict:
    if not re.fullmatch(r"[^/\s]+/[^/\s]+", repository) or issue < 1:
        raise PublishError("invalid repository or issue")
    if not os.environ.get("GH_TOKEN"):
        raise PublishError("GH_TOKEN required only for publisher")
    report = json.loads(Path(report_path).read_text())
    paths = [entry["path"] for entry in report["paths"]]
    if not paths:
        raise PublishError("verified report contains no paths")
    for entry in report["paths"]:
        path = Path(entry["path"])
        if not path.is_file():
            raise PublishError(f"missing verified path: {path}")
        import hashlib

        if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            raise PublishError(f"verified path changed: {path}")

    operation = report["operation"]
    pr = report.get("pr")
    if operation == "revise" and pr:
        metadata = json.loads(
            _run(
                "gh",
                "pr",
                "view",
                str(pr),
                "-R",
                repository,
                "--json",
                "headRefName,headRepositoryOwner",
                capture=True,
            )
        )
        if metadata["headRepositoryOwner"]["login"] != repository.split("/", 1)[0]:
            raise PublishError("revision PR must use a branch in the target repository")
        branch = metadata["headRefName"]
    else:
        branch = f"gitclaw/issue-{issue}-{operation}"
    _run("git", "switch", "-C", branch)
    _run("git", "add", "--", *paths)
    _run("git", "commit", "-m", f"{operation}(gitclaw): issue #{issue}")
    _run("gh", "auth", "setup-git")
    _run("git", "push", "--force-with-lease", "-u", "origin", branch)
    commit = _run("git", "rev-parse", "HEAD", capture=True)

    pr_url = ""
    if operation in {"plan", "enforce", "revise"}:
        existing = _run(
            "gh",
            "pr",
            "list",
            "-R",
            repository,
            "--head",
            branch,
            "--json",
            "url",
            "--jq",
            ".[0].url // \"\"",
            capture=True,
        )
        pr_url = existing or _run(
            "gh",
            "pr",
            "create",
            "-R",
            repository,
            "--base",
            "main",
            "--head",
            branch,
            "--title",
            f"{operation}(gitclaw): issue #{issue}",
            "--body",
            f"Generated from #{issue}; human merge required.",
            capture=True,
        )
    body = f"gitclaw {operation} completed in `{commit}`."
    if pr_url:
        body += f" PR: {pr_url}"
    _run("gh", "issue", "comment", str(issue), "-R", repository, "--body", body)
    return {"branch": branch, "commit": commit, "pr": pr_url}


def main(argv: list[str]) -> int:
    try:
        if len(argv) != 3:
            raise PublishError("usage: executor_publish <report> <repository> <issue>")
        result = publish(Path(argv[0]), argv[1], int(argv[2]))
        print(json.dumps(result, sort_keys=True))
        return 0
    except (PublishError, OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"executor_publish: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))