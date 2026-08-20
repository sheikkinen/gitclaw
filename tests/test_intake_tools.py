"""Retained slug and cron candidate contracts."""

from tools import cron_run, slug


def test_slug_kebab():
    assert slug.make("Daily haiku about the weather in Oulu") == "daily-haiku-about-the-weather-in-oulu"


def test_slug_strips_injection_chars():
    assert slug.make("evil; rm -rf / && $(curl x)|`y`") == "evil-rm-rf-curl-x-y"


def test_slug_bounded_and_nonempty():
    assert len(slug.make("x " * 100)) <= 40
    assert slug.make("!!! ???") == "feature"


def test_run_feature_timeout_recorded(tmp_path, monkeypatch):
    monkeypatch.setattr(
        cron_run,
        "_run_bounded",
        lambda command, timeout=600: (None, b"", b"", "timeout after 600s"),
    )
    ok, reason = cron_run.run_feature(
        tmp_path / "features" / "slow" / "graph.yaml", "2026-08-20"
    )
    assert ok is False and "timeout" in reason


def test_extract_output_precedence_and_candidate_contract():
    state = {
        "feature": "feature output",
        "candidate": "candidate output",
        "legacy": {"legacy": "legacy output"},
    }
    assert cron_run.extract_output(state, "feature") == "feature output"
    assert cron_run.extract_output(state, "missing-feature") == "candidate output"
    assert cron_run.extract_output({"candidate": {"candidate": "nested"}}, "x") == "nested"


def test_extract_output_fails_closed_for_missing_ambiguous_or_metadata():
    assert cron_run.extract_output({"date": "x", "errors": ["boom"]}, "haiku") is None
    assert cron_run.extract_output({"a": {"a": "one"}, "b": {"b": "two"}}, "x") is None
    assert cron_run.extract_output({"candidate": {"wrong": "leak"}}, "x") is None
    assert cron_run.extract_output({"date": {"date": "leak"}}, "x") is None
    assert cron_run.extract_output({"unrelated": "must not publish"}, "x") is None


def test_cron_main_records_success_and_failure(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for name in ("good", "poison"):
        (tmp_path / "features" / name).mkdir(parents=True)
        (tmp_path / "features" / name / "graph.yaml").touch()
    monkeypatch.setattr(
        cron_run,
        "run_feature",
        lambda graph, date: (graph.parent.name == "good", "text"),
    )
    assert cron_run.main("2026-08-20") == 1
    output = (tmp_path / "outputs" / "2026-08-20-good.md").read_text()
    assert "github.com/sheikkinen/gitclaw" in output
    assert (tmp_path / "outputs" / "2026-08-20-poison.failed.json").exists()
