"""Frozen intake state machine (FR-827 R-5) — RED spec."""

import json

import pytest

from tools import ledger


def test_transitions_frozen():
    assert ledger.TRANSITIONS["seen"] == {"planned", "failed_recovery_required"}
    assert ledger.TRANSITIONS["planned"] == {
        "judged_approved",
        "judged_rejected",
        "failed_recovery_required",
    }
    assert ledger.TRANSITIONS["judged_approved"] == {
        "enforced",
        "failed_recovery_required",
    }
    assert ledger.TRANSITIONS["enforced"] == {
        "reviewed_approved",
        "reviewed_rejected",
        "failed_recovery_required",
    }
    assert ledger.TRANSITIONS["reviewed_rejected"] == {
        "enforced",
        "reviewed_rejected_final",
        "failed_recovery_required",
    }
    assert ledger.TRANSITIONS["reviewed_approved"] == {
        "pushed",
        "failed_recovery_required",
    }
    assert ledger.TRANSITIONS["pushed"] == {"closed", "failed_recovery_required"}


def test_terminal_states():
    for s in (
        "closed",
        "judged_rejected",
        "reviewed_rejected_final",
        "failed_recovery_required",
    ):
        assert ledger.is_terminal(s)
    assert not ledger.is_terminal("seen")
    assert not ledger.is_terminal("reviewed_rejected")


def test_record_and_current(tmp_path):
    path = tmp_path / "issues.jsonl"
    ledger.record(path, 7, "seen")
    ledger.record(path, 7, "planned")
    assert ledger.current(path, 7) == "planned"
    assert ledger.current(path, 99) is None
    lines = [json.loads(x) for x in path.read_text().splitlines()]
    assert lines[0]["issue"] == 7 and lines[0]["state"] == "seen"
    assert "ts" in lines[0]


def test_illegal_transition_raises(tmp_path):
    path = tmp_path / "issues.jsonl"
    ledger.record(path, 7, "seen")
    with pytest.raises(ledger.IllegalTransition):
        ledger.record(path, 7, "pushed")


def test_replay_terminal_is_idempotent(tmp_path):
    """Replayed issue event on a terminal state must not start a pipeline."""
    path = tmp_path / "issues.jsonl"
    for s in ("seen", "planned", "judged_approved", "enforced",
              "reviewed_approved", "pushed", "closed"):
        ledger.record(path, 7, s)
    assert ledger.should_run(path, 7) is False


def test_replay_nonterminal_resumes(tmp_path):
    path = tmp_path / "issues.jsonl"
    ledger.record(path, 7, "seen")
    ledger.record(path, 7, "planned")
    assert ledger.should_run(path, 7) is True


def test_fresh_issue_runs(tmp_path):
    assert ledger.should_run(tmp_path / "issues.jsonl", 1) is True


def test_one_remediation_lap_only(tmp_path):
    path = tmp_path / "issues.jsonl"
    for s in ("seen", "planned", "judged_approved", "enforced",
              "reviewed_rejected", "enforced", "reviewed_rejected"):
        ledger.record(path, 7, s)
    # second rejection: only legal continuation is final rejection or recovery
    with pytest.raises(ledger.IllegalTransition):
        ledger.record(path, 7, "enforced")
    ledger.record(path, 7, "reviewed_rejected_final")
    assert ledger.should_run(path, 7) is False


def test_failed_recovery_required_from_any_state(tmp_path):
    path = tmp_path / "issues.jsonl"
    ledger.record(path, 7, "seen")
    ledger.record(path, 7, "failed_recovery_required")
    assert ledger.should_run(path, 7) is False
