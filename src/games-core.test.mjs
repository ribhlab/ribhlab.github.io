import test from "node:test";
import assert from "node:assert/strict";
import {parseFen,apply,legal,checked,gameStatus,index,chessStartFen} from "./games.js";

import {buildCrossword,cleanCrosswordWord} from './crossword-core.mjs';
function go(s,uci){
 const moves=legal(s),m=moves.find(x=>("abcdefgh"[x[0]&7]+(8-(x[0]>>4))+"abcdefgh"[x[1]&7]+(8-(x[1]>>4))+x[2])===uci);
 assert.ok(m,"Expected legal move "+uci);
 return apply(s,m);
}
test("correct chess setup, all kings and opening move legality",()=>{
 const s=parseFen(chessStartFen);
 assert.equal(s.b[index("d1")],"Q");assert.equal(s.b[index("d8")],"q");
 assert.equal(s.b[index("e1")],"K");assert.equal(s.b[index("e8")],"k");
 assert.equal(legal(s).length,20);
 assert.equal(s.b[index("h1")],"R");
 assert.equal(go(s,"e2e4").b[index("e4")],"P");
});
test("castling is legal only after clearing path and king remains safe",()=>{
 let s=parseFen(chessStartFen);
 for(const m of ["e2e4","e7e5","g1f3","b8c6","f1c4","g8f6"])s=go(s,m);
 assert.ok(legal(s).some(m=>m[3]==="castle"&&m[1]===index("g1")));
 s=go(s,"e1g1");assert.equal(s.b[index("g1")],"K");assert.equal(s.b[index("f1")],"R");
 assert.equal(s.c&3,0);
});
test("en passant removes the captured pawn",()=>{
 let s=parseFen(chessStartFen);for(const m of ["e2e4","a7a6","e4e5","d7d5"])s=go(s,m);
 assert.ok(legal(s).some(m=>m[3]==="ep"&&m[1]===index("d6")));
 s=go(s,"e5d6");assert.equal(s.b[index("d6")],"P");assert.equal(s.b[index("d5")],".");
});
test("all four promotions are available",()=>{
 const s=parseFen("8/P7/8/8/8/8/7p/K6k w - - 0 1");
 const promotions=legal(s).filter(m=>m[0]===index("a7")&&m[1]===index("a8"));
 assert.deepEqual(promotions.map(m=>m[2]).sort(),["b","n","q","r"]);
 assert.equal(go(s,"a7a8n").b[index("a8")],"N");
});
test("fool's mate produces a black checkmate",()=>{
 let s=parseFen(chessStartFen),h=[s];
 for(const m of ["f2f3","e7e5","g2g4","d8h4"]){s=go(s,m);h.push(s);}
 assert.equal(checked(s),true);
 const result=gameStatus(h);assert.equal(result.done,true);assert.equal(result.kind,"checkmate");assert.equal(result.winner,-1);
});

test("nine complete, authentic crossword grids in Arabic, French and English",()=>{
 for(const lang of ["ar","en","fr"])for(let index=0;index<3;index++){
  const g=buildCrossword(lang,index),starts=new Map(),cells=new Map;
  assert.ok(g.entries.length>=7,lang+index+" should have multiple answers");
  assert.ok(g.intersectionCount>=g.entries.length-1,lang+index+" must have genuine intersections");
  assert.ok(g.width<=19&&g.height<=19);
  for(const e of g.entries){
   assert.ok(["across","down"].includes(e.axis));
   assert.equal(e.cells.length,Array.from(e.answer).length);
   const start=e.cells[0].join(",");
   if(starts.has(start))assert.equal(starts.get(start),e.number);
   starts.set(start,e.number);
   assert.ok(e.clue.length>=5);
   for(let i=0;i<e.cells.length;i++){
    const [row,col]=e.cells[i],letter=e.answer[i];
    assert.equal(g.cells[row][col],letter);
    const key=row+","+col;
    if(!cells.has(key))cells.set(key,[]);
    cells.get(key).push(e.axis);
    assert.ok(cells.get(key).length<=2,"At most one across and one down word per cell");
   }
  }
  assert.ok([...cells.values()].some(v=>v.includes("across")&&v.includes("down")),"Words must share at least one actual square");
  assert.equal(new Set(g.entries.map(x=>x.answer)).size,g.entries.length);
 }
});
test("crosswords normalize Latin accents but preserve Arabic letters",()=>{
 assert.equal(cleanCrosswordWord("Rivière","fr"),"RIVIERE");
 assert.equal(cleanCrosswordWord("مَدرسة","ar"),"مدرسة");
 assert.equal(cleanCrosswordWord("chess","en"),"CHESS");
});
