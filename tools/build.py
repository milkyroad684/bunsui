#!/usr/bin/env python3
"""Build step for 分水 BUNSUI.

1. Imports all 15 level definitions and their verified solutions.
2. Verifies every solution wins, and that no initial board is already solved.
3. Writes src/levels.json (game data) and tests/solutions.json (QA data).
4. Injects levels.json into src/template.html -> dist/bunsui.html (single file).

Run from the repo root:  python tools/build.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from engine import check, check_initial_not_solved  # noqa: E402
from levels_1_5 import L1, S1, L2, S2, L3, S3, L4, S4, L5, S5a, S5b  # noqa: E402
from levels_6_15 import NEW, scramble, stable_seed  # noqa: E402
from levels_color import NEW_COLOR  # noqa: E402

META_1_5 = [
    ("1. はじめの配管",
     "水源（緑）の4単位を、パイプを回転させてタンクまで導こう。要求は4ぴったり。",
     L1, [S1]),
    ("2. 二手に分ける",
     "4単位をT字管で分流して、2つのタンクに2ずつ届けよう。T字管は入ってきた水を残りの口へ均等に分ける。",
     L2, [S2]),
    ("3. 合流と分流",
     "4と2を合流させてから3ずつに分流。合流が成立するのは、両方の水が同じティックにT字管へ着いたときだけ。",
     L3, [S3]),
    ("4. 時間差の罠",
     "6と2を同着で合わせて8に。その8を4と4に、片方をさらに2と2へ。タンクは4・2・2。最短経路が正解とは限らない。",
     L4, [S4]),
    ("5. 三と五",
     "水源は6と2、タンクは3と5。8はどう割っても3と5にならない。どのT字管に「割る」役と「合わせる」役を与えるかは君が決める。正解はひとつではない。",
     L5, [S5a, S5b]),
]


def build_levels():
    """Return (game_levels, qa_solutions) lists, fully scrambled & ordered."""
    game, qa = [], []
    for name, goal, lv, sols in META_1_5:
        game.append({"name": name, "goal": goal, "w": lv["w"], "h": lv["h"],
                     "cells": lv["cells"]})
        qa.append({"name": name, "solutions": sols})
    for tag, lv, sol in NEW + NEW_COLOR:
        scramble(lv, sol, seed=stable_seed(tag))
        game.append({"name": lv["name"], "goal": lv["goal"], "w": lv["w"],
                     "h": lv["h"], "cells": lv["cells"]})
        qa.append({"name": lv["name"], "solutions": [sol]})
    return game, qa


def verify(game, qa):
    ok = True
    for g, q in zip(game, qa):
        lv = {"w": g["w"], "h": g["h"], "cells": g["cells"]}
        for i, sol in enumerate(q["solutions"]):
            ok &= check(f"{g['name']} sol{i}", lv, sol)
        ok &= check_initial_not_solved(g["name"], lv)
    return ok


def main():
    game, qa = build_levels()
    if not verify(game, qa):
        print("BUILD ABORTED: verification failed")
        sys.exit(1)

    levels_path = os.path.join(ROOT, "src", "levels.json")
    sols_path = os.path.join(ROOT, "tests", "solutions.json")
    with open(levels_path, "w", encoding="utf-8") as f:
        json.dump(game, f, ensure_ascii=False, indent=1)
    with open(sols_path, "w", encoding="utf-8") as f:
        json.dump(qa, f, ensure_ascii=False, indent=1)

    tpl_path = os.path.join(ROOT, "src", "template.html")
    with open(tpl_path, encoding="utf-8") as f:
        tpl = f.read()
    engine_path = os.path.join(ROOT, "src", "engine.js")
    with open(engine_path, encoding="utf-8") as f:
        engine_js = f.read()
    # Drop the Node-only export tail when inlining into the browser bundle.
    marker = "/* Node export"
    if marker in engine_js:
        engine_js = engine_js[:engine_js.index(marker)].rstrip() + "\n"

    inline = json.dumps(game, ensure_ascii=False, separators=(",", ":"))
    for ph in ("__ENGINE__", "__LEVELS__"):
        if ph not in tpl:
            print(f"BUILD ABORTED: {ph} placeholder not found in template.html")
            sys.exit(1)
    html = tpl.replace("__ENGINE__", engine_js).replace("__LEVELS__", inline)

    dist_dir = os.path.join(ROOT, "dist")
    os.makedirs(dist_dir, exist_ok=True)
    out_path = os.path.join(dist_dir, "bunsui.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"OK: wrote {levels_path}")
    print(f"OK: wrote {sols_path}")
    print(f"OK: wrote {out_path} ({len(html.encode())} bytes)")


if __name__ == "__main__":
    main()
