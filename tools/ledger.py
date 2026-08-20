"""Intake ledger: append-only JSONL state machine (FR-827 R-5).

CLI:
  python -m tools.ledger record <issue> <state> [key=value ...]
  python -m tools.ledger current <issue>
  python -m tools.ledger should-run <issue>   # exit 0 run, 78 skip
"""

import json
import sys
import time
from pathlib import Path

LEDGER = Path("state/issues.jsonl")

TRANSITIONS = {
    "seen": {"planned", "failed_recovery_required"},
    "planned": {"judged_approved", "judged_rejected", "failed_recovery_required"},
    "judged_approved": {"enforced", "failed_recovery_required"},
    "enforced": {"reviewed_approved", "reviewed_rejected", "failed_recovery_required"},
    "reviewed_rejected": {"enforced", "reviewed_rejected_final", "failed_recovery_required"},
    "reviewed_approved": {"pushed", "failed_recovery_required"},
    "pushed": {"closed", "failed_recovery_required"},
}

TERMINAL = {"closed", "judged_rejected", "reviewed_rejected_final", "failed_recovery_required"}

STATES = set(TRANSITIONS) | TERMINAL


class IllegalTransition(Exception):
    pass


def is_terminal(state: str) -> bool:
    return state in TERMINAL


def _entries(path: Path, issue: int) -> list[dict]:
    if not Path(path).exists():
        return []
    out = []
    for line in Path(path).read_text().splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        if entry["issue"] == issue:
            out.append(entry)
    return out


def current(path: Path, issue: int) -> str | None:
    entries = _entries(path, issue)
    return entries[-1]["state"] if entries else None


def record(path: Path, issue: int, state: str, **extra) -> None:
    if state not in STATES:
        raise IllegalTransition(f"unknown state: {state}")
    prev = current(path, issue)
    if prev is None:
        if state != "seen":
            raise IllegalTransition(f"first state must be 'seen', got '{state}'")
    else:
        if prev in TERMINAL:
            raise IllegalTransition(f"'{prev}' is terminal")
        allowed = TRANSITIONS[prev]
        if state not in allowed:
            raise IllegalTransition(f"'{prev}' -> '{state}' not allowed")
        # one remediation lap: a second reviewed_rejected forbids re-enforce
        if state == "enforced" and prev == "reviewed_rejected":
            rejections = [e for e in _entries(path, issue) if e["state"] == "reviewed_rejected"]
            if len(rejections) >= 2:
                raise IllegalTransition("remediation lap already used")
    entry = {"issue": issue, "state": state, "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **extra}
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a") as f:
        f.write(json.dumps(entry) + "\n")


def should_run(path: Path, issue: int) -> bool:
    state = current(path, issue)
    return state is None or not is_terminal(state)


def gate_code(path: Path, issue: int) -> int:
    """Intake gate: 0 fresh, 78 terminal (idempotent skip), 65 interrupted."""
    state = current(path, issue)
    if state is None:
        return 0
    if is_terminal(state):
        return 78
    return 65


def main(argv: list[str]) -> int:
    cmd, issue = argv[0], int(argv[1])
    if cmd == "record":
        extra = dict(kv.split("=", 1) for kv in argv[3:])
        record(LEDGER, issue, argv[2], **extra)
        return 0
    if cmd == "current":
        print(current(LEDGER, issue) or "")
        return 0
    if cmd == "should-run":
        return gate_code(LEDGER, issue)
    raise SystemExit(f"unknown command: {cmd}")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
