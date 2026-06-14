"""Bunsui (分水) puzzle engine — Python mirror of the JS game engine.

Semantics (must stay identical to the JS implementation):
- Dirs: 0=N, 1=E, 2=S, 3=W. DX/DY per dir.
- Pieces: I=[N,S], L=[N,E], T=[E,S,W], X=[N,E,S,W]; conns = base rotated by rot*90deg.
- Packets live "at" a cell with an incoming side `frm`; one resolution per tick.
- Resolution per occupied cell (all packets in a cell are grouped):
    * no cell           -> FAIL leak
    * tank              -> absorb; fill>need -> FAIL overflow
    * src               -> FAIL backflow
    * pipe: every frm must be in conns else FAIL leak;
            outs = conns - incoming sides; outs empty -> FAIL deadend;
            total % len(outs) != 0 -> FAIL burst; else split evenly.
- After computing all moves, any pair swapping cells head-on -> FAIL collision.
- Pulsed sources: emit `units` at global ticks 0, period, 2*period ... (count times).
  New pulse packets are added AFTER the move resolution of that tick.
- Win: no packets, all pulses emitted, every tank fill == need.
"""

DX = [0, 1, 0, -1]
DY = [-1, 0, 1, 0]
BASE = {"I": [0, 2], "L": [0, 1], "T": [1, 2, 3], "X": [0, 1, 2, 3]}


def conns(kind, rot):
    return [(d + rot) % 4 for d in BASE[kind]]


def simulate(level, rots=None, max_ticks=300, trace=False):
    cells = {k: dict(v) for k, v in level["cells"].items()}
    if rots:
        for k, r in rots.items():
            assert k in cells and cells[k]["t"] == "pipe", f"bad rot key {k}"
            cells[k]["rot"] = r
    srcs = []
    for k, c in cells.items():
        if c["t"] == "src":
            x, y = map(int, k.split(","))
            srcs.append((x, y, c))
        if c["t"] == "tank":
            c["fill"] = 0
            c["fillcol"] = 0
    last_emit = max((c.get("count", 1) - 1) * c.get("period", 1) for _, _, c in srcs)

    def emit(t):
        out = []
        for x, y, c in srcs:
            per, cnt = c.get("period", 1), c.get("count", 1)
            if t % per == 0 and t // per < cnt:
                d = c["dir"]
                out.append(
                    {
                        "x": x + DX[d],
                        "y": y + DY[d],
                        "frm": (d + 2) % 4,
                        "units": c["units"],
                        "col": c.get("col", 0),
                    }
                )
        return out

    packets = emit(0)
    tick = 0
    log = []
    while True:
        tick += 1
        if tick > max_ticks:
            return {"result": "timeout", "tick": tick, "log": log}
        groups = {}
        for p in packets:
            groups.setdefault((p["x"], p["y"]), []).append(p)
        moves = []
        for (x, y), g in groups.items():
            total = sum(p["units"] for p in g)
            gcol = 0
            for p in g:
                gcol |= p.get("col", 0)
            c = cells.get(f"{x},{y}")
            if c is None:
                return {"result": f"leak at ({x},{y})", "tick": tick, "log": log}
            if c["t"] == "tank":
                if c.get("col") and (gcol & ~c["col"]):
                    return {
                        "result": f"colorclash at ({x},{y})",
                        "tick": tick,
                        "log": log,
                    }
                c["fill"] += total
                c["fillcol"] = c.get("fillcol", 0) | gcol
                if c["fill"] > c["need"]:
                    return {
                        "result": f"overflow at ({x},{y}) fill={c['fill']}>{c['need']}",
                        "tick": tick,
                        "log": log,
                    }
                continue
            if c["t"] == "src":
                return {"result": f"backflow at ({x},{y})", "tick": tick, "log": log}
            cs = conns(c["kind"], c["rot"])
            for p in g:
                if p["frm"] not in cs:
                    return {
                        "result": f"leak(port) at ({x},{y}) frm={p['frm']}",
                        "tick": tick,
                        "log": log,
                    }
            inc = {p["frm"] for p in g}
            outs = [d for d in cs if d not in inc]
            if not outs:
                return {"result": f"deadend at ({x},{y})", "tick": tick, "log": log}
            if total % len(outs):
                return {
                    "result": f"burst at ({x},{y}) {total}%{len(outs)}",
                    "tick": tick,
                    "log": log,
                }
            per = total // len(outs)
            for d in outs:
                moves.append(
                    {
                        "fx": x,
                        "fy": y,
                        "x": x + DX[d],
                        "y": y + DY[d],
                        "frm": (d + 2) % 4,
                        "units": per,
                        "col": gcol,
                    }
                )
        for a in moves:
            for b in moves:
                if (
                    a is not b
                    and a["x"] == b["fx"]
                    and a["y"] == b["fy"]
                    and b["x"] == a["fx"]
                    and b["y"] == a["fy"]
                ):
                    return {
                        "result": f"collision ({a['fx']},{a['fy']})<->({b['fx']},{b['fy']})",
                        "tick": tick,
                        "log": log,
                    }
        packets = [
            {
                "x": m["x"],
                "y": m["y"],
                "frm": m["frm"],
                "units": m["units"],
                "col": m["col"],
            }
            for m in moves
        ]
        packets += emit(tick)
        if trace:
            log.append((tick, [(p["x"], p["y"], p["units"]) for p in packets]))
        if not packets and tick >= last_emit:
            ok = True
            color_bad = False
            for k, c in cells.items():
                if c["t"] != "tank":
                    continue
                if c["fill"] != c["need"]:
                    ok = False
                elif c.get("col") and c.get("fillcol", 0) != c["col"]:
                    ok = False
                    color_bad = True
            if ok:
                return {"result": "WIN", "tick": tick, "log": log}
            return {
                "result": "colorfail" if color_bad else "underfill",
                "tick": tick,
                "log": log,
            }


def P(kind, rot):
    return {"t": "pipe", "kind": kind, "rot": rot}


def SRC(d, units, count=1, period=1, col=0):
    s = {"t": "src", "dir": d, "units": units}
    if count > 1:
        s["count"] = count
        s["period"] = period
    if col:
        s["col"] = col
    return s


def TANK(need, col=0):
    t = {"t": "tank", "need": need}
    if col:
        t["col"] = col
    return t


def check(name, level, solution, expect="WIN"):
    r = simulate(level, solution)
    status = "OK " if r["result"] == expect else "FAIL"
    print(f"[{status}] {name}: {r['result']} (tick {r['tick']})")
    return r["result"] == expect


def check_initial_not_solved(name, level):
    """The scrambled initial rotation must not already be a winning state."""
    r = simulate(level, None)
    ok = r["result"] != "WIN"
    print(f"[{'OK ' if ok else 'FAIL'}] {name} initial-not-solved: {r['result']}")
    return ok
