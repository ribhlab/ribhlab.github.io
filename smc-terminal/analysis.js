/* RibhLab SMC Terminal — transparent, deterministic, educational analysis.
 * Confirmed pivots require right-hand candles, so they do not repaint after confirmation.
 * SMC concepts are interpretive heuristics, not evidence of actual institutional orders.
 */
(function(global){
  'use strict';
  const round=(v,n=2)=>Number.isFinite(v)?Number(v.toFixed(n)):null;
  const finite=v=>typeof v==='number'&&Number.isFinite(v);
  function ema(data,period){
    const out=[],k=2/(period+1);let sum=0,prev=null;
    for(let i=0;i<data.length;i++){
      sum+=data[i].close;
      if(i===period-1){prev=sum/period;out.push({time:data[i].time,value:prev});}
      else if(i>=period){prev=data[i].close*k+prev*(1-k);out.push({time:data[i].time,value:prev});}
    }
    return out;
  }
  function rsi(data,period=14){
    const out=[];if(data.length<=period)return out;
    let gains=0,losses=0;
    for(let i=1;i<=period;i++){const delta=data[i].close-data[i-1].close;gains+=Math.max(0,delta);losses+=Math.max(0,-delta);}
    let ag=gains/period,al=losses/period;
    const calc=()=>al===0?(ag===0?50:100):100-100/(1+ag/al);
    out.push({time:data[period].time,value:calc()});
    for(let i=period+1;i<data.length;i++){
      const d=data[i].close-data[i-1].close;
      ag=(ag*(period-1)+Math.max(d,0))/period;
      al=(al*(period-1)+Math.max(-d,0))/period;
      out.push({time:data[i].time,value:calc()});
    }
    return out;
  }
  function atr(data,period=14){
    const out=[];if(!data.length)return out;
    let sum=0,avg=0;
    for(let i=0;i<data.length;i++){
      const prev=i?data[i-1].close:data[i].close;
      const tr=Math.max(data[i].high-data[i].low,Math.abs(data[i].high-prev),Math.abs(data[i].low-prev));
      if(i<period)sum+=tr;
      if(i===period-1){avg=sum/period;out.push({time:data[i].time,value:avg});}
      else if(i>=period){avg=(avg*(period-1)+tr)/period;out.push({time:data[i].time,value:avg});}
    }
    return out;
  }
  function confirmedPivots(data,radius=3){
    const highs=[],lows=[];
    for(let i=radius;i<data.length-radius;i++){
      let high=true,low=true;
      for(let n=1;n<=radius;n++){
        if(data[i].high<=data[i-n].high||data[i].high<data[i+n].high)high=false;
        if(data[i].low>=data[i-n].low||data[i].low>data[i+n].low)low=false;
      }
      if(high)highs.push({i,time:data[i].time,price:data[i].high,confirmedAt:i+radius});
      if(low)lows.push({i,time:data[i].time,price:data[i].low,confirmedAt:i+radius});
    }
    return {highs,lows};
  }
  function structure(data,pivots){
    const events=[],sweeps=[];
    const radius=3;
    const highAt=new Map(pivots.highs.map(p=>[p.confirmedAt,p]));
    const lowAt=new Map(pivots.lows.map(p=>[p.confirmedAt,p]));
    let activeHigh=null,activeLow=null,lastDir=null;
    const broken=new Set(),swept=new Set();
    for(let i=radius+2;i<data.length;i++){
      if(highAt.has(i))activeHigh=highAt.get(i);
      if(lowAt.has(i))activeLow=lowAt.get(i);
      const c=data[i],prev=data[i-1],t=c.time;
      if(activeHigh&&activeHigh.i<i){
        if(c.close>activeHigh.price&&prev.close<=activeHigh.price&&!broken.has('h'+activeHigh.i)){
          const type=lastDir==='bear'?'CHoCH':'BOS';lastDir='bull';broken.add('h'+activeHigh.i);
          events.push({time:t,i,type,direction:'bull',price:activeHigh.price,trigger:c.close,swingIndex:activeHigh.i,description:'Close above confirmed swing high'});
        }else if(c.high>activeHigh.price&&c.close<activeHigh.price&&prev.close<=activeHigh.price&&!swept.has('h'+activeHigh.i)){
          swept.add('h'+activeHigh.i);sweeps.push({time:t,i,direction:'bear',type:'High sweep',price:activeHigh.price,description:'Wick above high, close back below'});
        }
      }
      if(activeLow&&activeLow.i<i){
        if(c.close<activeLow.price&&prev.close>=activeLow.price&&!broken.has('l'+activeLow.i)){
          const type=lastDir==='bull'?'CHoCH':'BOS';lastDir='bear';broken.add('l'+activeLow.i);
          events.push({time:t,i,type,direction:'bear',price:activeLow.price,trigger:c.close,swingIndex:activeLow.i,description:'Close below confirmed swing low'});
        }else if(c.low<activeLow.price&&c.close>activeLow.price&&prev.close>=activeLow.price&&!swept.has('l'+activeLow.i)){
          swept.add('l'+activeLow.i);sweeps.push({time:t,i,direction:'bull',type:'Low sweep',price:activeLow.price,description:'Wick below low, close back above'});
        }
      }
    }
    return {events:events.slice(-100),sweeps:sweeps.slice(-100),direction:lastDir||'neutral'};
  }
  function gaps(data,atrNow){
    const result=[];const minimum=Math.max(1e-10,atrNow*.07);
    const start=Math.max(2,data.length-195);
    for(let i=start;i<data.length;i++){
      const first=data[i-2],third=data[i];
      let direction,low,high;
      if(third.low>first.high+minimum){direction='bull';low=first.high;high=third.low;}
      else if(third.high<first.low-minimum){direction='bear';low=third.high;high=first.low;}
      else continue;
      let active=true,partial=false;
      for(let k=i+1;k<data.length;k++){
        if(direction==='bull'){
          if(data[k].low<=low){active=false;break;}
          if(data[k].low<high)partial=true;
        }else{
          if(data[k].high>=high){active=false;break;}
          if(data[k].high>low)partial=true;
        }
      }
      if(active)result.push({kind:'FVG',direction,low,high,startTime:first.time,created:third.time,i,partial});
    }
    return result.slice(-30);
  }
  function blocks(data,events){
    const result=[];
    for(const event of events.slice(-30)){
      let origin=-1;
      for(let j=event.i-1;j>=Math.max(0,event.i-16);j--){
        const c=data[j];
        if(event.direction==='bull'&&c.close<c.open){origin=j;break;}
        if(event.direction==='bear'&&c.close>c.open){origin=j;break;}
      }
      if(origin<0)continue;
      const c=data[origin],block={kind:'Order block',direction:event.direction,low:c.low,high:c.high,startTime:c.time,created:event.time,i:event.i};
      let invalid=false,partial=false;
      for(let k=event.i+1;k<data.length;k++){
        if(event.direction==='bull'){if(data[k].close<c.low){invalid=true;break;}if(data[k].low<=c.high)partial=true;}
        else{if(data[k].close>c.high){invalid=true;break;}if(data[k].high>=c.low)partial=true;}
      }
      if(!invalid&&event.i>=data.length-160){block.partial=partial;result.push(block);}
    }
    return result.slice(-8);
  }
  function equalLiquidity(pivots,tolerance){
    const out=[];
    for(const [arr,direction] of [[pivots.highs,'high'],[pivots.lows,'low']]){
      const recent=arr.slice(-20);
      for(let i=1;i<recent.length;i++){
        const a=recent[i-1],b=recent[i];
        if(b.i-a.i>=4&&Math.abs(a.price-b.price)<=tolerance)
          out.push({kind:direction==='high'?'Equal highs':'Equal lows',direction,price:(a.price+b.price)/2,time:b.time,i:b.i});
      }
    }
    return out.slice(-8).sort((a,b)=>b.i-a.i);
  }
  function calculate(data,{radius=3}={}){
    if(!Array.isArray(data)||data.length<60)throw new Error('At least 60 completed OHLC candles are required');
    const pivots=confirmedPivots(data,radius),s=structure(data,pivots),ema20=ema(data,20),ema50=ema(data,50),ema200=ema(data,200),rsis=rsi(data),atrs=atr(data);
    const last=data[data.length-1],atrNow=atrs.at(-1)?.value||(last.high-last.low);
    const fvgs=gaps(data,atrNow),obs=blocks(data,s.events),liquidity=equalLiquidity(pivots,atrNow*.16);
    const low=Math.min(...data.slice(-110).map(c=>c.low));
    const high=Math.max(...data.slice(-110).map(c=>c.high));
    const position=high===low ? 0.5 : (last.close-low)/(high-low);
    const direction=s.direction,latestEvent=s.events.at(-1)||null;
    const m20=ema20.at(-1)?.value,m50=ema50.at(-1)?.value;
    const rv=rsis.at(-1)?.value;
    let confluence=0;
    if(direction==='bull'||direction==='bear'){
      confluence+=1;
      if(finite(m20)&&finite(m50)&&(direction==='bull'?m20>m50:m20<m50))confluence++;
      if(finite(rv)&&(direction==='bull'?rv>=50:rv<=50))confluence++;
      if(fvgs.some(z=>z.direction===direction))confluence++;
      if(obs.some(z=>z.direction===direction))confluence++;
    }
    return {
      dataCount:data.length,last,ema20,ema50,ema200,rsis,atrs,
      pivots,events:s.events,sweeps:s.sweeps,fvgs,blocks:obs,liquidity,
      direction,latestEvent,atr:atrNow,rsi:rv,ema20value:m20,ema50value:m50,
      range:{low,high,mid:(low+high)/2,position},
      confluence,confluenceMax:5,
      activeZones:[...fvgs,...obs].sort((a,b)=>b.i-a.i).slice(0,12)
    };
  }
  global.SmcEngine={calculate,ema,rsi,atr,confirmedPivots,structure,gaps,blocks,version:'1.0.0'};
})(window);