"""Slug + cron extraction + intake gate exit codes — RED specs."""

from tools import cron_run, ledger, slug


def test_slug_kebab():
    assert slug.make("Daily haiku about the weather in Oulu") == "daily-haiku-about-the-weather-in-oulu"


def test_slug_strips_injection_chars():
    assert slug.make("evil; rm -rf / && $(curl x)|`y`") == "evil-rm-rf-curl-x-y"


def test_slug_bounded_and_nonempty():
    assert len(slug.make("x " * 100)) <= 40
    assert slug.make("!!! ???") == "feature"


def test_slug_unique_no_collision(tmp_path):
    assert slug.unique("Daily haiku", 7, root=tmp_path) == "daily-haiku"


def test_slug_unique_collision_appends_issue(tmp_path):
    # two similar titles must not share features/<name>/
    (tmp_path / "daily-haiku").mkdir()
    assert slug.unique("Daily haiku", 7, root=tmp_path) == "daily-haiku-7"


def test_slug_unique_collision_stays_bounded(tmp_path):
    long_title = "x " * 100
    (tmp_path / slug.make(long_title)).mkdir()
    s = slug.unique(long_title, 12345, root=tmp_path)
    assert len(s) <= 40 and s.endswith("-12345")


def test_run_feature_timeout_recorded(tmp_path, monkeypatch):
    # a hung feature must be recorded as failed, not crash the loop
    import subprocess

    def hang(*a, **kw):
        raise subprocess.TimeoutExpired(cmd="yamlgraph", timeout=600)

    monkeypatch.setattr(cron_run.subprocess, "run", hang)
    ok, reason = cron_run.run_feature(tmp_path / "features" / "slow" / "graph.yaml", "2026-08-20")
    assert ok is False and "timeout" in reason


def test_extract_output_nested_dict():
    # inline-schema LLM nodes nest: state.haiku == {'haiku': text}
    state = {"date": "2026-08-20", "haiku": {"haiku": "text here"}}
    assert cron_run.extract_output(state, "haiku") == "text here"


def test_extract_output_plain_str():
    assert cron_run.extract_output({"horoscope": "sunny"}, "horoscope") == "sunny"


def test_extract_output_single_value_dict():
    state = {"aphorism": {"result": "less is more"}}
    assert cron_run.extract_output(state, "aphorism") == "less is more"


def test_extract_output_missing_returns_none():
    # failed LLM nodes exit 0 with no state key — must not pass silently
    assert cron_run.extract_output({"date": "x", "errors": ["boom"]}, "haiku") is None


def test_extract_output_fallback_single_output_key():
    # generated graphs pick their own state_key (issue #3: 'aphorism'
    # inside dir daily-aphorism-about-software-craft)
    state = {"date": "2026-08-20", "aphorism": {"aphorism": "build less"}}
    assert cron_run.extract_output(state, "daily-aphorism-about-software-craft") == "build less"


def test_extract_output_ambiguous_fails_closed():
    state = {"date": "x", "a": {"a": "one"}, "b": {"b": "two"}}
    assert cron_run.extract_output(state, "no-such-key") is None


def test_cron_main_exit_codes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for name in ("good", "poison"):
        (tmp_path / "features" / name).mkdir(parents=True)
        (tmp_path / "features" / name / "graph.yaml").touch()
    monkeypatch.setattr(
        cron_run,
        "run_feature",
        lambda g, d: (g.parent.name == "good", "text"),
    )
    assert cron_run.main("2026-08-20") == 1  # poison recorded, exit 1
    assert (tmp_path / "outputs" / "2026-08-20-good.md").exists()
    assert (tmp_path / "outputs" / "2026-08-20-poison.failed.json").exists()


def test_cron_output_carries_attribution(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "features" / "good").mkdir(parents=True)
    (tmp_path / "features" / "good" / "graph.yaml").touch()
    monkeypatch.setattr(cron_run, "run_feature", lambda g, d: (True, "text"))
    assert cron_run.main("2026-08-20") == 0
    out = (tmp_path / "outputs" / "2026-08-20-good.md").read_text()
    assert out.startswith("text\n")
    assert "github.com/sheikkinen/gitclaw" in out
    assert "github.com/sheikkinen/yamlgraph" in out


def test_intake_gate_exit_codes(tmp_path):
    path = tmp_path / "issues.jsonl"
    assert ledger.gate_code(path, 5) == 0  # fresh: run
    ledger.record(path, 5, "seen")
    ledger.record(path, 5, "planned")
    assert ledger.gate_code(path, 5) == 65  # interrupted: human recovery
    ledger.record(path, 5, "judged_rejected")
    assert ledger.gate_code(path, 5) == 78  # terminal: idempotent skip
