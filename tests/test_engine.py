#!/usr/bin/env python3
"""Python engine regression test for 分水 BUNSUI.

Rebuilds the level set from the definitions in tools/ and asserts every
solution wins and no initial board is pre-solved. Mirrors tests/run_tests.js
(the JS side); build.py guarantees both engines agree on the shipped data.

Run:  python tests/test_engine.py   (from repo root)
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

from build import build_levels, verify  # noqa: E402


def main():
    game, qa = build_levels()
    ok = verify(game, qa)
    print("\nPYTHON ENGINE: ALL OK" if ok else "\nPYTHON ENGINE: FAILURES")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
