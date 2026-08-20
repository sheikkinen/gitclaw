"""FR-845 deterministic command and post-agent artifact contracts."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath

from tools import contain
from tools.request_contract import verify_request


FR_RE = re.compile(r"^feature-requests/FR-[A-Za-z0-9][A-Za-z0-9._-]*\.md$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
REPORT = Path("tmp/execution-report.json")
REQUIRED_FR_HEADINGS = (
    "## Summary",
    "## Value Statement",
    "## Problem",
    "## Ideal Result",
    "## Proposed Solution",
    "## Acceptance Criteria",
    "## Alternatives Considered",
)


class ExecutorContractError(ValueError):
    """The request or resulting artifacts cannot authorize side effects."""


@dataclass(frozen=True)
class Command:
    operation: str
    subject: str = ""
    target: str = ""
    pr: int | None = None
    feedback: str = ""


def _fail(message: str) -> None:
    raise ExecutorContractError(message)


def _fr_path(value: str) -> str:
    if not FR_RE.fullmatch(value) or ".." in PurePosixPath(value).parts:
        _fail("FR path must be feature-requests/FR-*.md")
    return value


def parse_command(title: str) -> Command:
    if not isinstance(title, str) or "\n" in title or "\x00" in title:
        _fail("command must be one line")
    match = re.fullmatch(r"Plan (.+) as a Feature Request", title)
    if match and match.group(1).strip() and ";" not in match.group(1):
        return Command("plan", subject=match.group(1).strip())
    match = re.fullmatch(r"Enforce (\S+)", title)
    if match:
        return Command("enforce", target=_fr_path(match.group(1)))
    match = re.fullmatch(r"Review ([1-9][0-9]*) against (\S+)", title)
    if match:
        return Command("review", target=_fr_path(match.group(2)), pr=int(match.group(1)))
    match = re.fullmatch(r"Revise PR ([1-9][0-9]*): (.+)", title)
    if match and match.group(2).strip():
        return Command("revise", pr=int(match.group(1)), feedback=match.group(2).strip())
    match = re.fullmatch(r"Revise (\S+): (.+)", title)
    if match and match.group(2).strip():
        return Command("revise", target=_fr_path(match.group(1)), feedback=match.group(2).strip())
    _fail("unsupported command; use Plan, Enforce, Review, or Revise exact form")


def classify_revision(paths: list[str]) -> str:
    if not paths:
        _fail("revision produced no artifacts")
    authority = [p for p in paths if p.startswith("feature-requests/")]
    implementation = [p for p in paths if not p.startswith("feature-requests/")]
    if authority and implementation:
        _fail("revision mixes authority and implementation artifacts")
    if authority:
        if any(not (FR_RE.fullmatch(p) or p.endswith(".judgement.md")) for p in authority):
            _fail("replan changed a non-FR authority path")
        return "replan"
    return "implementation"


def changed_paths() -> list[str]:
    result = subprocess.run(
        ["git", "status", "--porcelain"], capture_output=True, text=True, check=True
    )
    paths = []
    for line in result.stdout.splitlines():
        value = line[3:].strip('"')
        if " -> " in value:
            paths.extend(value.split(" -> ", 1))
        else:
            paths.append(value)
    expanded = []
    for value in paths:
        path = Path(value.rstrip("/"))
        if path.is_dir():
            expanded.extend(
                child.as_posix()
                for child in path.rglob("*")
                if child.is_file() and not child.is_symlink()
            )
        else:
            expanded.append(path.as_posix())
    return sorted(set(expanded))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _assert_head(expected: str) -> None:
    if not SHA_RE.fullmatch(expected):
        _fail("expected_head must be a full lowercase commit SHA")
    actual = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    if actual != expected:
        _fail("agent changed Git HEAD")


def _plan(paths: list[str], request_sha256: str) -> list[str]:
    frs = [p for p in paths if FR_RE.fullmatch(p) and not p.endswith(".judgement.md")]
    judgements = [p for p in paths if p.endswith(".judgement.md")]
    if len(frs) != 1 or len(judgements) != 1:
        _fail("plan must produce exactly one FR and one judgement")
    fr = Path(frs[0])
    expected_judgement = fr.with_suffix("").as_posix() + ".judgement.md"
    if judgements != [expected_judgement]:
        _fail("judgement must be the FR sibling")
    if contain.violations(paths, "plan", set(frs + judgements)):
        _fail("plan changed paths outside FR and judgement")
    text = fr.read_text()
    if any(heading not in text for heading in REQUIRED_FR_HEADINGS):
        _fail("FR is missing required headings")
    if request_sha256 not in text:
        _fail("FR does not record immutable request hash")
    judgement = Path(judgements[0])
    if not any(line.startswith("**Verdict:**") for line in judgement.read_text().splitlines()):
        _fail("judgement has no verdict line")
    return [fr.as_posix(), judgement.as_posix()]


def _enforce(paths: list[str], target: str) -> list[str]:
    forbidden = {target, target.removesuffix(".md") + ".judgement.md"}
    if forbidden.intersection(paths) or any(p.endswith("/request.json") for p in paths):
        _fail("enforcement changed immutable authority")
    if not paths:
        _fail("enforcement produced no implementation")
    if contain.violations(paths, "enforce"):
        _fail("enforcement changed authority or platform paths")
    governed = any(p.endswith("graph.yaml") or "/prompts/" in p for p in paths)
    if governed:
        report = Path("tmp/draft-authoring-report.md")
        if not report.is_file() or any(
            heading not in report.read_text()
            for heading in ("Artifacts", "Precedent", "Validation", "Repairs", "Blocked validation")
        ):
            _fail("graph work lacks valid authoring report")
    return paths


def _review(paths: list[str], pr: int | None, expected_pr_head: str) -> list[str]:
    if pr is None or not SHA_RE.fullmatch(expected_pr_head):
        _fail("review requires PR and full expected head")
    expected = f"reviews/pr-{pr}-{expected_pr_head}.md"
    if paths != [expected]:
        _fail("review must produce exactly one head-linked review artifact")
    if contain.violations(paths, "review", {expected}):
        _fail("review changed paths outside its report")
    first = Path(expected).read_text().splitlines()[0]
    if not first.startswith("**Merge verdict:**"):
        _fail("review artifact lacks line-one merge verdict")
    return paths


def verify(
    operation: Command,
    feature: str,
    request_sha256: str,
    expected_head: str,
    expected_pr_head: str = "",
) -> dict:
    _assert_head(expected_head)
    verify_request(Path.cwd(), feature, request_sha256)
    paths = [p for p in changed_paths() if not p.startswith("tmp/")]
    if operation.operation == "plan":
        staged = _plan(paths, request_sha256)
        revision = ""
    elif operation.operation == "enforce":
        staged = _enforce(paths, operation.target)
        revision = ""
    elif operation.operation == "review":
        staged = _review(paths, operation.pr, expected_pr_head)
        revision = ""
    else:
        revision = classify_revision(paths)
        staged = _plan(paths, request_sha256) if revision == "replan" else _enforce(paths, operation.target)
    report = {
        "version": 1,
        "operation": operation.operation,
        "pr": operation.pr,
        "revision": revision,
        "request_sha256": request_sha256,
        "input_head": expected_head,
        "pr_head": expected_pr_head,
        "paths": [{"path": p, "sha256": _sha256(Path(p))} for p in staged],
    }
    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n")
    return report


def main(argv: list[str]) -> int:
    try:
        if argv == ["classify"]:
            command = parse_command(os.environ.get("ISSUE_TITLE", ""))
            for key, value in asdict(command).items():
                if key in {"operation", "target", "pr"} and value not in ("", None):
                    print(f"{key}={value}")
            return 0
        if argv and argv[0] == "verify" and len(argv) == 5:
            command = parse_command(os.environ.get("ISSUE_TITLE", ""))
            verify(command, argv[1], argv[2], argv[3], argv[4])
            print(REPORT)
            return 0
        print("usage: executor_contract classify|verify ...", file=sys.stderr)
        return 2
    except ExecutorContractError as exc:
        print(f"executor_contract: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))