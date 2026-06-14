"""Color levels (18-20) — the 4th pillar: 色合成 (color synthesis).

Water carries a color (3 primaries as bits: R=1, Y=2, B=4). Merging on a
simultaneous arrival ORs the colors (赤+青=紫). Splitting preserves color.
Tanks may demand a specific color as well as an exact amount. Amount math
(divisibility / timing) is unchanged — color is an orthogonal new axis.

Reuses scramble()/stable_seed() from levels_6_15 so initial rotations are
deterministic and differ from the solution. See docs/design.md.
"""
from engine import P, SRC, TANK
from levels_6_15 import scramble, stable_seed

# Primary color bits.
R, Y, B = 1, 2, 4
O, G, Pp, BR = R | Y, Y | B, R | B, R | Y | B  # 橙, 緑, 紫, 茶

# ---------------------------------------------------------------- L18 two colors
L18 = {"w": 5, "h": 5, "name": "18. 二色の出会い",
       "goal": "新しい性質、色。水源ごとに色がある。赤と青を同じ部品へ同着させると"
               "混ざって紫になる。紫をぴったり6、タンクへ。",
       "cells": {
    "2,0": SRC(2, 3, col=R), "2,4": SRC(0, 3, col=B), "4,2": TANK(6, col=Pp),
    "2,1": P("I", 0), "2,3": P("I", 0), "2,2": P("T", 3), "3,2": P("I", 1),
    # decoys
    "1,1": P("L", 0), "3,0": P("L", 0), "1,3": P("L", 0), "0,2": P("T", 0)}}
S18 = {"2,1": 0, "2,3": 0, "2,2": 3, "3,2": 1}

# ---------------------------------------------------------------- L19 distribute
L19 = {"w": 8, "h": 5, "name": "19. 三色の分配",
       "goal": "黄を二手に割り、片方は赤と、片方は青と同着させる。"
               "橙（赤＋黄）と緑（黄＋青）を同時に量り出し、4ずつ両タンクへ。",
       "cells": {
    "0,2": SRC(1, 4, col=Y), "0,0": SRC(1, 2, col=R), "0,4": SRC(1, 2, col=B),
    "7,1": TANK(4, col=O), "7,3": TANK(4, col=G),
    "1,2": P("I", 1), "2,2": P("T", 1),
    "2,1": P("L", 1), "3,1": P("I", 1), "4,1": P("I", 1), "5,1": P("T", 2), "6,1": P("I", 1),
    "1,0": P("I", 1), "2,0": P("I", 1), "3,0": P("I", 1), "4,0": P("I", 1), "5,0": P("L", 2),
    "2,3": P("L", 0), "3,3": P("I", 1), "4,3": P("I", 1), "5,3": P("T", 0), "6,3": P("I", 1),
    "1,4": P("I", 1), "2,4": P("I", 1), "3,4": P("I", 1), "4,4": P("I", 1), "5,4": P("L", 3),
    # decoys
    "3,2": P("X", 0), "4,2": P("L", 0), "6,0": P("L", 0), "6,4": P("L", 0),
    "1,1": P("T", 0), "1,3": P("T", 0)}}
S19 = {"1,2": 1, "2,2": 1, "2,1": 1, "3,1": 1, "4,1": 1, "5,1": 2, "6,1": 1,
       "1,0": 1, "2,0": 1, "3,0": 1, "4,0": 1, "5,0": 2,
       "2,3": 0, "3,3": 1, "4,3": 1, "5,3": 0, "6,3": 1,
       "1,4": 1, "2,4": 1, "3,4": 1, "4,4": 1, "5,4": 3}

# ---------------------------------------------------------------- L20 graduation
L20 = {"w": 8, "h": 7, "name": "20. 三原色の大合奏",
       "goal": "赤・黄・青の三流を一点で同時に合流させ、茶（三色すべて）の9をつくる。"
               "その9を十字で3・3・3に割り、三つのタンクへ。割る・揃える・混ぜるの総合。",
       "cells": {
    "4,0": SRC(2, 3, col=R), "1,3": SRC(1, 3, col=Y), "4,6": SRC(0, 3, col=B),
    "6,2": TANK(3, col=BR), "7,3": TANK(3, col=BR), "6,4": TANK(3, col=BR),
    "4,1": P("I", 0), "4,2": P("I", 0), "2,3": P("I", 1), "3,3": P("I", 1),
    "4,5": P("I", 0), "4,4": P("I", 0), "4,3": P("X", 0), "5,3": P("I", 1), "6,3": P("X", 0),
    # decoys
    "2,2": P("L", 0), "6,1": P("L", 0), "6,5": P("L", 0), "2,4": P("L", 0),
    "5,2": P("T", 0), "5,4": P("T", 0), "1,1": P("I", 0)}}
S20 = {"4,1": 0, "4,2": 0, "2,3": 1, "3,3": 1, "4,5": 0, "4,4": 0,
       "4,3": 0, "5,3": 1, "6,3": 0}

# ---------------------------------------------------------------- L21 the ring
# A closed loop with 6 special T-junctions, alternating source / tank.
# Each source splits its 4 both ways round the ring (2+2); every arc is 3 steps
# long, so the two streams meeting at each tank arrive on the same tick and merge
# into a secondary colour:  R+Y=橙, Y+B=緑, B+R=紫.  New idea: loop topology —
# water travels round a ring, not down a tree.  Symmetry guarantees the timing.
L21 = {"w": 8, "h": 7, "name": "21. 色の環・三対の同着",
       "goal": "環（輪になった配管）。三つの水源が4を両方向へ2・2に分け、輪を回る。"
               "隣り合う流れが各タンクで同着し、橙・緑・紫を同時に作り分ける。"
               "分ける・揃える・混ぜるのすべてを一枚に。",
       "cells": {
    # sources (R top, Y right, B bottom) and the three secondary tanks
    "2,0": SRC(2, 4, col=R), "7,3": SRC(3, 4, col=Y), "2,6": SRC(0, 4, col=B),
    "5,0": TANK(4, col=O), "5,6": TANK(4, col=G), "0,3": TANK(4, col=Pp),
    # the 18-cell ring, clockwise from the top-left corner
    "1,1": P("L", 1), "2,1": P("T", 2), "3,1": P("I", 1), "4,1": P("I", 1),
    "5,1": P("T", 2), "6,1": P("L", 2), "6,2": P("I", 0), "6,3": P("T", 3),
    "6,4": P("I", 0), "6,5": P("L", 3), "5,5": P("T", 0), "4,5": P("I", 1),
    "3,5": P("I", 1), "2,5": P("T", 0), "1,5": P("L", 0), "1,4": P("I", 0),
    "1,3": P("T", 1), "1,2": P("I", 0),
    # decoys (isolated interior pieces — never see water)
    "3,3": P("X", 0), "4,3": P("T", 0), "3,2": P("L", 0)}}
S21 = {"1,1": 1, "2,1": 2, "3,1": 1, "4,1": 1, "5,1": 2, "6,1": 2,
       "6,2": 0, "6,3": 3, "6,4": 0, "6,5": 3, "5,5": 0, "4,5": 1,
       "3,5": 1, "2,5": 0, "1,5": 0, "1,4": 0, "1,3": 1, "1,2": 0}

NEW_COLOR = [("L18", L18, S18), ("L19", L19, S19), ("L20", L20, S20),
             ("L21", L21, S21)]


def scramble_color():
    """Apply the deterministic scramble to every color level in place."""
    for tag, lv, sol in NEW_COLOR:
        scramble(lv, sol, seed=stable_seed(tag))


if __name__ == "__main__":
    from engine import check, check_initial_not_solved
    scramble_color()
    ok = True
    for tag, lv, sol in NEW_COLOR:
        ok &= check(tag + " " + lv["name"], lv, sol)
        ok &= check_initial_not_solved(tag, lv)
    print("ALL OK" if ok else "SOME FAILED")
