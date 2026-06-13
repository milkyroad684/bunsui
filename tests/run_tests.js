#!/usr/bin/env node
/* JS engine test runner for 分水 BUNSUI.
 * Loads the canonical src/engine.js, replays every verified solution from
 * tests/solutions.json against src/levels.json, and checks that:
 *   - every recorded solution wins,
 *   - no initial (scrambled) board is already solved.
 * Exit code is non-zero on any failure, so CI can gate on it.
 *
 * Run:  node tests/run_tests.js   (from repo root)
 */
const fs = require("fs");
const path = require("path");

const ROOT = path.dirname(__dirname);
const { newSim, stepSim } = require(path.join(ROOT, "src", "engine.js"));
const levels = JSON.parse(fs.readFileSync(path.join(ROOT, "src", "levels.json"), "utf-8"));
const qa = JSON.parse(fs.readFileSync(path.join(ROOT, "tests", "solutions.json"), "utf-8"));

function run(level, rots) {
  const sim = newSim(level, rots);
  let res = null;
  while (!sim.done) {
    const r = stepSim(sim);
    if (r.fail) res = r.fail.msg;
    if (r.win) res = "WIN";
  }
  return { res, tick: sim.tick };
}

let pass = 0, fail = 0;
levels.forEach((lv, i) => {
  qa[i].solutions.forEach((sol, j) => {
    const { res, tick } = run(lv, sol);
    const ok = res === "WIN";
    ok ? pass++ : fail++;
    console.log(`${ok ? "[OK ]" : "[FAIL]"} ${lv.name} sol${j}: ${res} (tick ${tick})`);
  });
  const { res } = run(lv, null);
  const ok = res !== "WIN";
  ok ? pass++ : fail++;
  if (!ok) console.log(`[FAIL] ${lv.name}: initial board already solved`);
});

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
