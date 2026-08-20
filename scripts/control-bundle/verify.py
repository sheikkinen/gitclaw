#!/usr/bin/env python3
"""CLI entrypoint for the FR-846 control-bundle verifier."""

from tools.control_bundle import main


if __name__ == "__main__":
    raise SystemExit(main())