"""Sanitize issue titles into feature slugs. Slugs flow into shell
commands and paths — strictly [a-z0-9-]."""

import re
import sys


def make(title: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    s = s[:40].rstrip("-")
    return s or "feature"


if __name__ == "__main__":
    print(make(sys.argv[1]))
