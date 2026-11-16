const test = require('node:test');
const assert = require('node:assert/strict');
global.window = global;
require('../analysis.js');
const E = global.SmcEngine;

function candles(n=350){
  return Array.from({length:n},(_,i)=>{
    const base=100+(i*.06)+Math.sin(i/9)*5+Math.sin(i/30)*12;
    return {time:1700000000+i*3600,open:base-.2,close:base+.2,high:base+1.5,low:base-1.5,volume:120+i};
  });
}
test('EMA constant series stays constant and emits expected length',()=>{
  const data=Array.from({length:30},(_,i)=>({time:i,close:100}));
  const r=E.ema(data,20);assert.equal(r.length,11);assert.ok(r.every(x=>Math.abs(x.value-100)<1e-9));
});
test('RSI of flat closes is neutral at 50',()=>{
  const r=E.rsi(Array.from({length:35},(_,i)=>({time:i,close:100})),14);
  assert.equal(r.at(-1).value,50);
});
test('market structure calculation produces sane, finite values',()=>{
  const r=E.calculate(candles());
  assert.ok(['bull','bear','neutral'].includes(r.direction));
  assert.ok(r.rsi>=0&&r.rsi<=100);
  assert.ok(r.atr>0);
  assert.ok(r.range.high>r.range.low);
  assert.ok(r.ema200.length>0);
  assert.ok(r.pivots.highs.length>1);
  assert.ok(r.pivots.lows.length>1);
  assert.ok(r.confluence>=0&&r.confluence<=5);
});
test('confirm pivots only with right-side bars',()=>{
  const data=candles(40),before=E.confirmedPivots(data,3);
  const last=data.at(-1);
  const spike={...last,time:last.time+3600,high:last.high+200};
  const justSpiked=E.confirmedPivots([...data,spike],3);
  assert.ok(!justSpiked.highs.some(x=>x.time===spike.time));
  assert.ok(before.highs.every(x=>x.confirmedAt<x.i+4));
});
test('three candle upward FVG is detected and becomes invalid if filled',()=>{
  const bars=candles(80);
  bars[76]={time:bars[76].time,open:100,high:102,low:99,close:101,volume:1};
  bars[77]={time:bars[77].time,open:103,high:105,low:102.5,close:104,volume:1};
  bars[78]={time:bars[78].time,open:106,high:108,low:105,close:107,volume:1};
  bars[79]={time:bars[79].time,open:107,high:110,low:106,close:109,volume:1};
  assert.ok(E.gaps(bars,1).some(x=>x.direction==='bull'&&x.i===78));
  bars.push({time:bars[79].time+3600,open:107,high:107,low:101,close:102,volume:1});
  assert.ok(!E.gaps(bars,1).some(x=>x.direction==='bull'&&x.i===78));
});
