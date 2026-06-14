#!/usr/bin/env python3
"""Brute-force solver for BUNSUI discrete-flow levels.

The solver searches every rotation choice that can be reached by water flow.
It branches when a packet group reaches an unassigned pipe, keeps choices that
obey the engine rules, and returns the lowest tap-count winning assignment.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from engine import DX, DY, conns


Packet = Dict[str, int]
Move = Dict[str, int]
Rotations = Dict[str, int]
Fill = Dict[str, int]


@dataclass
class Metrics:
    nodes: int = 0
    pipe_branches: int = 0
    rotation_candidates: int = 0
    wins: int = 0
    failures: int = 0
    pruned: int = 0
    max_depth: int = 0
    seen_states: int = 0

    @property
    def average_branching_factor(self) -> float:
        if self.pipe_branches == 0:
            return 0.0
        return self.rotation_candidates / self.pipe_branches


@dataclass
class SolveResult:
    solved: bool
    rotations: Rotations = field(default_factory=dict)
    tap_sequence: List[str] = field(default_factory=list)
    tap_count: int = 0
    tick: Optional[int] = None
    metrics: Metrics = field(default_factory=Metrics)


class FlowSolver:
    def __init__(self, level, max_ticks=300):
        self.level = level
        self.max_ticks = max_ticks
        self.cells = level["cells"]
        self.pipe_keys = sorted(k for k, c in self.cells.items() if c["t"] == "pipe")
        self.initial_rots = {k: self.cells[k]["rot"] for k in self.pipe_keys}
        self.srcs = []
        for k, c in self.cells.items():
            if c["t"] == "src":
                x, y = map(int, k.split(","))
                self.srcs.append((x, y, c))
        self.last_emit = max(
            (c.get("count", 1) - 1) * c.get("period", 1) for _, _, c in self.srcs
        )
        self.best: Optional[SolveResult] = None
        self.metrics = Metrics()
        self.seen = {}

    def solve(self) -> SolveResult:
        packets = self._emit(0)
        fills = {k: (0, 0) for k, c in self.cells.items() if c["t"] == "tank"}
        self._search(
            tick=0, packets=packets, fills=fills, rots={}, order=[], cost=0, depth=0
        )
        self.metrics.seen_states = len(self.seen)
        if self.best:
            self.best.metrics = self.metrics
            return self.best
        return SolveResult(False, metrics=self.metrics)

    def _emit(self, tick: int) -> List[Packet]:
        out = []
        for x, y, c in self.srcs:
            period, count = c.get("period", 1), c.get("count", 1)
            if tick % period == 0 and tick // period < count:
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

    def _tap_delta(self, key: str, rot: int) -> int:
        return (rot - self.initial_rots[key]) % 4

    def _current_cost(self, rots: Rotations) -> int:
        return sum(self._tap_delta(k, r) for k, r in rots.items())

    def _tap_sequence(self, rots: Rotations, order: List[str]) -> List[str]:
        seq = []
        ordered = order + [k for k in sorted(rots) if k not in set(order)]
        for k in ordered:
            seq.extend([k] * self._tap_delta(k, rots[k]))
        return seq

    def _state_key(
        self, tick: int, packets: List[Packet], fills: Fill, rots: Rotations
    ):
        packet_key = tuple(
            sorted(
                (p["x"], p["y"], p["frm"], p["units"], p.get("col", 0)) for p in packets
            )
        )
        fill_key = tuple(sorted(fills.items()))
        rot_key = tuple(sorted(rots.items()))
        return tick, packet_key, fill_key, rot_key

    def _search(
        self,
        tick: int,
        packets: List[Packet],
        fills: Fill,
        rots: Rotations,
        order: List[str],
        cost: int,
        depth: int,
    ):
        self.metrics.nodes += 1
        self.metrics.max_depth = max(self.metrics.max_depth, depth)
        if self.best and cost >= self.best.tap_count:
            self.metrics.pruned += 1
            return
        key = self._state_key(tick, packets, fills, rots)
        old = self.seen.get(key)
        if old is not None and old <= cost:
            self.metrics.pruned += 1
            return
        self.seen[key] = cost

        tick += 1
        if tick > self.max_ticks:
            self.metrics.failures += 1
            return

        groups = {}
        for p in packets:
            groups.setdefault((p["x"], p["y"]), []).append(p)
        group_items = list(groups.items())
        self._resolve_groups(tick, group_items, 0, fills, rots, order, [], cost, depth)

    def _resolve_groups(
        self,
        tick: int,
        group_items,
        index: int,
        fills: Fill,
        rots: Rotations,
        order: List[str],
        moves: List[Move],
        cost: int,
        depth: int,
    ):
        if index == len(group_items):
            if self._has_collision(moves):
                self.metrics.failures += 1
                return
            next_packets = [
                {
                    "x": m["x"],
                    "y": m["y"],
                    "frm": m["frm"],
                    "units": m["units"],
                    "col": m["col"],
                }
                for m in moves
            ]
            next_packets.extend(self._emit(tick))
            if not next_packets and tick >= self.last_emit:
                if self._is_win(fills):
                    self._record_win(tick, rots, order, cost)
                else:
                    self.metrics.failures += 1
                return
            self._search(tick, next_packets, fills, rots, order, cost, depth + 1)
            return

        (x, y), group = group_items[index]
        c = self.cells.get(f"{x},{y}")
        total = sum(p["units"] for p in group)
        gcol = 0
        for p in group:
            gcol |= p.get("col", 0)
        if c is None or c["t"] == "src":
            self.metrics.failures += 1
            return
        if c["t"] == "tank":
            cell_key = f"{x},{y}"
            amt, col = fills[cell_key]
            if c.get("col") and (gcol & ~c["col"]):
                self.metrics.failures += 1
                return
            if amt + total > c["need"]:
                self.metrics.failures += 1
                return
            new_fills = dict(fills)
            new_fills[cell_key] = (amt + total, col | gcol)
            self._resolve_groups(
                tick, group_items, index + 1, new_fills, rots, order, moves, cost, depth
            )
            return

        cell_key = f"{x},{y}"
        if cell_key in rots:
            candidates = [rots[cell_key]]
        else:
            candidates = list(range(4))
            self.metrics.pipe_branches += 1
            self.metrics.rotation_candidates += len(candidates)

        for rot in candidates:
            produced = self._pipe_moves(x, y, c["kind"], rot, group, total, gcol)
            if produced is None:
                continue
            if cell_key in rots:
                self._resolve_groups(
                    tick,
                    group_items,
                    index + 1,
                    fills,
                    rots,
                    order,
                    moves + produced,
                    cost,
                    depth,
                )
            else:
                new_rots = dict(rots)
                new_rots[cell_key] = rot
                new_cost = cost + self._tap_delta(cell_key, rot)
                new_order = order + [cell_key]
                self._resolve_groups(
                    tick,
                    group_items,
                    index + 1,
                    fills,
                    new_rots,
                    new_order,
                    moves + produced,
                    new_cost,
                    depth,
                )

    def _pipe_moves(
        self,
        x: int,
        y: int,
        kind: str,
        rot: int,
        group: List[Packet],
        total: int,
        gcol: int = 0,
    ) -> Optional[List[Move]]:
        cs = conns(kind, rot)
        for p in group:
            if p["frm"] not in cs:
                return None
        incoming = {p["frm"] for p in group}
        outs = [d for d in cs if d not in incoming]
        if not outs or total % len(outs):
            return None
        units = total // len(outs)
        return [
            {
                "fx": x,
                "fy": y,
                "x": x + DX[d],
                "y": y + DY[d],
                "frm": (d + 2) % 4,
                "units": units,
                "col": gcol,
            }
            for d in outs
        ]

    def _has_collision(self, moves: List[Move]) -> bool:
        for i, a in enumerate(moves):
            for b in moves[i + 1 :]:
                if (
                    a["x"] == b["fx"]
                    and a["y"] == b["fy"]
                    and b["x"] == a["fx"]
                    and b["y"] == a["fy"]
                ):
                    return True
        return False

    def _is_win(self, fills: Fill) -> bool:
        for k, c in self.cells.items():
            if c["t"] != "tank":
                continue
            amt, col = fills[k]
            if amt != c["need"]:
                return False
            if c.get("col") and col != c["col"]:
                return False
        return True

    def _record_win(self, tick: int, rots: Rotations, order: List[str], cost: int):
        self.metrics.wins += 1
        if self.best and cost >= self.best.tap_count:
            return
        taps = self._tap_sequence(rots, order)
        self.best = SolveResult(True, dict(rots), taps, cost, tick, self.metrics)


def solve(level, max_ticks=300) -> SolveResult:
    return FlowSolver(level, max_ticks=max_ticks).solve()


def load_levels():
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    from build import build_levels

    return build_levels()


def compare_known(level_index: int, found: Rotations, qa) -> Tuple[bool, str]:
    known_solutions = qa[level_index]["solutions"]
    for known in known_solutions:
        if found == known:
            return True, "exact match with tests/solutions.json"
    best = max(
        (sum(1 for k, v in known.items() if found.get(k) == v), len(known))
        for known in known_solutions
    )
    return True, (
        "alternate winning solution; "
        f"{best[0]}/{best[1]} recorded rotations match tests/solutions.json"
    )


def result_payload(label: str, result: SolveResult, level_index=None, qa=None):
    payload = {
        "level": label,
        "solved": result.solved,
        "tap_count": result.tap_count,
        "solution_length": result.tap_count,
        "tick": result.tick,
        "rotations": result.rotations,
        "tap_sequence": result.tap_sequence,
        "metrics": {
            "nodes": result.metrics.nodes,
            "search_space_size": result.metrics.nodes,
            "pipe_branches": result.metrics.pipe_branches,
            "rotation_candidates": result.metrics.rotation_candidates,
            "average_branching_factor": result.metrics.average_branching_factor,
            "wins": result.metrics.wins,
            "failures": result.metrics.failures,
            "pruned": result.metrics.pruned,
            "max_depth": result.metrics.max_depth,
            "seen_states": result.metrics.seen_states,
        },
    }
    if result.solved and level_index is not None and qa is not None:
        ok, message = compare_known(level_index, result.rotations, qa)
        payload["known_solution_comparison"] = {"compatible": ok, "message": message}
    return payload


def parse_args():
    parser = argparse.ArgumentParser(
        description="Solve BUNSUI levels by exhaustive flow DFS."
    )
    parser.add_argument("--level", type=int, help="1-based level number to solve")
    parser.add_argument("--all", action="store_true", help="solve every built level")
    parser.add_argument("--max-ticks", type=int, default=300)
    parser.add_argument(
        "--json", action="store_true", help="print machine-readable JSON"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if not args.all and not args.level:
        args.level = 15
    game, qa = load_levels()
    indices = range(len(game)) if args.all else [args.level - 1]
    outputs = []
    for i in indices:
        if i < 0 or i >= len(game):
            raise SystemExit(f"bad level number: {i + 1}")
        lv = {"w": game[i]["w"], "h": game[i]["h"], "cells": game[i]["cells"]}
        result = solve(lv, max_ticks=args.max_ticks)
        outputs.append(result_payload(game[i]["name"], result, i, qa))
    if args.json:
        print(
            json.dumps(
                outputs if args.all else outputs[0], ensure_ascii=False, indent=2
            )
        )
        return
    for out in outputs:
        m = out["metrics"]
        print(f"{out['level']}: {'SOLVED' if out['solved'] else 'UNSOLVABLE'}")
        print(f"  solution length: {out['solution_length']} taps, tick={out['tick']}")
        print(
            f"  search space: {m['search_space_size']} nodes, "
            f"branching={m['average_branching_factor']:.2f}, "
            f"wins={m['wins']}, failures={m['failures']}, pruned={m['pruned']}"
        )
        if "known_solution_comparison" in out:
            cmp = out["known_solution_comparison"]
            print(f"  known comparison: {cmp['message']}")
        print(
            f"  rotations: {json.dumps(out['rotations'], ensure_ascii=False, sort_keys=True)}"
        )
        print(f"  taps: {' '.join(out['tap_sequence'])}")


if __name__ == "__main__":
    main()
