/* 分水 BUNSUI — discrete flow engine (canonical).
 * Shared by the browser game (inlined at build time) and the Node test runner.
 * Mirror of tools/engine.py — keep both in sync; tests/run_tests.js checks parity.
 *
 * Dirs: 0=N 1=E 2=S 3=W.  Pieces rotate by rot*90deg.
 * One resolution per tick; merges only on simultaneous arrival (same tick, same cell).
 */
const DX=[0,1,0,-1],DY=[-1,0,1,0],BASE={I:[0,2],L:[0,1],T:[1,2,3],X:[0,1,2,3]};
function conns(c){return BASE[c.kind].map(d=>(d+c.rot)%4)}
function newSim(level,rots){
  const cells={};
  for(const k in level.cells){cells[k]=Object.assign({},level.cells[k]);
    if(cells[k].t==="tank")cells[k].fill=0;
    if(rots&&rots[k]!==undefined)cells[k].rot=rots[k];}
  const srcs=[];let lastEmit=0;
  for(const k in cells){const c=cells[k];
    if(c.t==="src"){const p=k.split(",");srcs.push({x:+p[0],y:+p[1],c});
      lastEmit=Math.max(lastEmit,((c.count||1)-1)*(c.period||1));}}
  function emit(t){const out=[];
    for(const s of srcs){const per=s.c.period||1,cnt=s.c.count||1;
      if(t%per===0&&t/per<cnt){const d=s.c.dir;
        out.push({x:s.x+DX[d],y:s.y+DY[d],frm:(d+2)%4,units:s.c.units});}}
    return out;}
  return{cells,emit,lastEmit,tick:0,packets:emit(0),done:false};
}
function stepSim(sim){
  sim.tick++;const wet=[];
  if(sim.tick>300){sim.done=true;return{fail:{msg:"タイムアウト：水が循環している？",x:-1,y:-1},wet}}
  const groups={};
  for(const p of sim.packets){const k=p.x+","+p.y;(groups[k]=groups[k]||[]).push(p);}
  const moves=[];
  for(const k in groups){
    const g=groups[k],parts=k.split(","),x=+parts[0],y=+parts[1];
    const total=g.reduce((s,p)=>s+p.units,0);const c=sim.cells[k];
    if(!c){sim.done=true;return{fail:{msg:"漏水：パイプのない場所へ水があふれた",x,y},wet}}
    if(c.t==="tank"){c.fill+=total;
      if(c.fill>c.need){sim.done=true;return{fail:{msg:"あふれた：タンクは要求量ぴったりで止める",x,y},wet}}
      continue;}
    if(c.t==="src"){sim.done=true;return{fail:{msg:"逆流：水が水源へ戻った",x,y},wet}}
    const cs=conns(c);
    for(const p of g)if(!cs.includes(p.frm)){
      sim.done=true;return{fail:{msg:"漏水：口の向きが水の来る向きと合っていない",x,y},wet}}
    const inc=new Set(g.map(p=>p.frm));const outs=cs.filter(d=>!inc.has(d));
    if(!outs.length){sim.done=true;return{fail:{msg:"行き止まり：出口がない",x,y},wet}}
    if(total%outs.length){sim.done=true;
      return{fail:{msg:"破裂："+total+"単位は"+outs.length+"方向に割り切れない",x,y},wet}}
    const per=total/outs.length;wet.push({k,dirs:[...inc,...outs]});
    for(const d of outs)moves.push({fx:x,fy:y,x:x+DX[d],y:y+DY[d],frm:(d+2)%4,units:per});
  }
  for(const a of moves)for(const b of moves)
    if(a!==b&&a.x===b.fx&&a.y===b.fy&&b.x===a.fx&&b.y===a.fy){
      sim.done=true;return{fail:{msg:"正面衝突：合流は同着のときだけ成立する",x:a.fx,y:a.fy},wet}}
  sim.packets=moves.map(m=>({x:m.x,y:m.y,frm:m.frm,units:m.units}));
  for(const p of sim.emit(sim.tick))sim.packets.push(p);
  if(!sim.packets.length&&sim.tick>=sim.lastEmit){
    sim.done=true;let ok=true;
    for(const k in sim.cells){const c=sim.cells[k];if(c.t==="tank"&&c.fill!==c.need)ok=false;}
    if(ok)return{win:true,wet};
    return{fail:{msg:"水量不足：すべてのタンクをぴったり満たそう",x:-1,y:-1},wet};
  }
  return{wet};
}

/* Node export (ignored by the browser, which inlines this file). */
if (typeof module !== "undefined" && module.exports) {
  module.exports = { DX, DY, BASE, conns, newSim, stepSim };
}
