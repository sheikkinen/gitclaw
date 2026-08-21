"""Retained issue-title slug contracts."""

from tools import slug


def test_slug_kebab():
    assert slug.make("Daily haiku about the weather in Oulu") == "daily-haiku-about-the-weather-in-oulu"


def test_slug_strips_injection_chars():
    assert slug.make("evil; rm -rf / && $(curl x)|`y`") == "evil-rm-rf-curl-x-y"


def test_slug_bounded_and_nonempty():
    assert len(slug.make("x " * 100)) <= 40
    assert slug.make("!!! ???") == "feature"
