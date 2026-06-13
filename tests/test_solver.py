#!/usr/bin/env python3
"""QA 安全網: ビルド済みの全レベルが総当たりソルバーで解けることを保証する。

`tools/solver.py` を全図に回し、1つでも解が見つからなければ非ゼロ終了する。
新しいレベルを追加したら、これを走らせれば「実は詰んでいる盤面」を出荷前に検出できる。

実行:  python tests/test_solver.py

依存は標準ライブラリのみ（外部パッケージ不要）。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TOOLS = os.path.join(ROOT, "tools")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

from solver import load_levels, solve  # noqa: E402


def main():
    game, _qa = load_levels()
    ok = True
    for g in game:
        lv = {"w": g["w"], "h": g["h"], "cells": g["cells"]}
        result = solve(lv)
        if result.solved:
            print(f"[OK ] {g['name']}: SOLVABLE "
                  f"({result.tap_count} taps, {result.metrics.nodes} nodes)")
        else:
            ok = False
            print(f"[XX ] {g['name']}: UNSOLVABLE "
                  f"({result.metrics.nodes} nodes searched)")

    print()
    if ok:
        print(f"SOLVER QA: ALL {len(game)} LEVELS SOLVABLE")
        sys.exit(0)
    else:
        print("SOLVER QA: FAILED — 解けないレベルがある")
        sys.exit(1)


if __name__ == "__main__":
    main()
