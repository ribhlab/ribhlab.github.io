/* RibhLab SMC Terminal | no secrets, no trading orders, all market data public. */
(function(){
'use strict';
const LW=window.LightweightCharts,Engine=window.SmcEngine;
const $=id=>document.getElementById(id);
const intervals={'5m':'1h','15m':'4h','1h':'4h','4h':'1d','1d':'1w'};
const coins=[
['BTCUSDT','Bitcoin','₿','#f2b443'],['ETHUSDT','Ethereum','Ξ','#8d9df5'],['SOLUSDT','Solana','◎','#8ae9ce'],
['BNBUSDT','BNB','⬡','#f4cb59'],['XRPUSDT','XRP','✕','#95a2b9'],['ADAUSDT','Cardano','₳','#7aa5ff'],
['DOGEUSDT','Dogecoin','Ð','#d9b356'],['AVAXUSDT','Avalanche','▲','#f27987'],['LINKUSDT','Chainlink','⬡','#5b8dee'],
['DOTUSDT','Polkadot','●','#e384bb'],['LTCUSDT','Litecoin','Ł','#9fa9b8'],['TRXUSDT','TRON','◈','#f26b72'],
['ATOMUSDT','Cosmos','⚛','#a8b2e6'],['NEARUSDT','NEAR','N','#8edccd'],['UNIUSDT','Uniswap','♧','#e690c3'],
['BCHUSDT','Bitcoin Cash','₿','#9ed96e'],['ETCUSDT','Ethereum Classic','◇','#5dc297'],['XLMUSDT','Stellar','✦','#8c9db4']
].map(([symbol,name,icon,color])=>({symbol,name,icon,color}));
let state={
symbol:'BTCUSDT',tf:'1h',data:[],analysis:null,htf:null,request:0,ws:null,controller:null,refreshTimer:null,
heartbeat:null,analysisTimer:null,reconnectTimer:null,autoSmc:true,drawMode:'cursor',drawStart:null,drawings:[],
tableTab:'events',favorites:new Set(),dark:true,activePrice:null,live:false
};
let chart,candles,vol,ema20,ema50,ema200,rsiChart,rsiSeries,markersApi,zoneCanvas,resizeObserver,toastTimer,shownGuide=false;
const preference=key=>{try{return localStorage.getItem('smct_'+key);}catch{return null;}};
const remember=(key,value)=>{try{localStorage.setItem('smct_'+key,value);}catch{}};
const num=(v,dec)=>Number.isFinite(v)?v.toLocaleString('en-US',{minimumFractionDigits:dec,maximumFractionDigits:dec}):'—';
const decimals=v=>v<.01?6:v<1?4:2;
const fmt=v=>num(v,decimals(Math.abs(v||1)));
const compact=v=>Number.isFinite(v)?Intl.NumberFormat('en-US',{notation:'compact',maximumFractionDigits:2}).format(v):'—';
const sign=v=>Number.isFinite(v)?(v>=0?'+':'')+num(v,2)+'%':'—';
const date=t=>new Date(t*1000).toLocaleString('en-GB',{timeZone:'UTC',day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit'});
const relative=(t)=>{const n=Math.round((Date.now()/1000-t)/60);return n<1?'just now':n<60?n+'m ago':n<1440?Math.floor(n/60)+'h ago':Math.floor(n/1440)+'d ago';};
const themeColors=()=>document.body.classList.contains('light')?{bg:'#f7f9fc',text:'#6b7b91',grid:'#e9eef4'}:{bg:'#0c1322',text:'#75849a',grid:'#172236'};
function toast(message,error=false){const el=$('toast');el.textContent=message;el.classList.toggle('error',error);el.classList.add('visible');clearTimeout(toastTimer);toastTimer=setTimeout(()=>el.classList.remove('visible'),5000);}
function connection(value,mode){$('connectionState').textContent=value;$('feedText').textContent=mode||value;$('liveDot').className='status-dot '+(value==='LIVE'?'online':value==='OFFLINE'?'offline':'');$('feedStatusDot').className='status-dot '+(value==='LIVE'?'online':value==='OFFLINE'?'offline':'');state.live=value==='LIVE';}
function loading(message,sub,error=false){const el=$('chartState');el.classList.remove('hidden');el.classList.toggle('error',error);el.querySelector('strong').textContent=message;el.querySelector('span').textContent=sub;}
function showChart(){ $('chartState').classList.add('hidden');}
function chartOptions(height,primary=false){
const c=themeColors();
return {autoSize:true,width:700,height,layout:{background:{type:'solid',color:c.bg},textColor:c.text,fontFamily:'IBM Plex Mono, monospace',fontSize:10,attributionLogo:true},
grid:{vertLines:{color:c.grid,style:1},horzLines:{color:c.grid,style:1}},
crosshair:{mode:LW.CrosshairMode.Normal,vertLine:{color:'#7592ae',style:2,labelBackgroundColor:'#243a54'},horzLine:{color:'#7592ae',style:2,labelBackgroundColor:'#243a54'}},
rightPriceScale:{borderColor:c.grid,scaleMargins:{top:.08,bottom:primary ? .18 : .06}},
timeScale:{borderColor:c.grid,timeVisible:true,secondsVisible:false,barSpacing:7,minBarSpacing:2,rightOffset:8},
handleScroll:true,handleScale:true,localization:{locale:'en-US'}};
}
function addLine(color,width=1){return chart.addSeries(LW.LineSeries,{color,lineWidth:width,priceLineVisible:false,lastValueVisible:false,crosshairMarkerVisible:false});}
function setupCharts(){
if(!LW||!LW.createChart||!LW.CandlestickSeries||!Engine)throw new Error('Chart or analysis library unavailable. Check your network and reload.');
chart=LW.createChart($('chartHost'),chartOptions(405,true));
candles=chart.addSeries(LW.CandlestickSeries,{upColor:'#36cba1',downColor:'#f2647e',borderUpColor:'#36cba1',borderDownColor:'#f2647e',wickUpColor:'#36cba1',wickDownColor:'#f2647e',priceLineVisible:false});
vol=chart.addSeries(LW.HistogramSeries,{priceScaleId:'volume',priceFormat:{type:'volume'},lastValueVisible:false,priceLineVisible:false});
chart.priceScale('volume').applyOptions({scaleMargins:{top:.82,bottom:0}});
ema20=addLine('#699cf6',2);ema50=addLine('#ecae53',1);ema200=addLine('#a28df0',1);
rsiChart=LW.createChart($('rsiHost'),{...chartOptions(92,false),rightPriceScale:{visible:true,borderVisible:false,scaleMargins:{top:.10,bottom:.10}},timeScale:{visible:false,borderVisible:false},grid:{vertLines:{visible:false},horzLines:{color:themeColors().grid}},crosshair:{vertLine:{visible:false},horzLine:{visible:false}},handleScroll:false,handleScale:false});
rsiSeries=rsiChart.addSeries(LW.LineSeries,{color:'#a998fc',lineWidth:2,priceLineVisible:false,lastValueVisible:false,crosshairMarkerVisible:false});
rsiSeries.createPriceLine({price:70,color:'rgba(245,114,140,.35)',lineStyle:LW.LineStyle.Dashed,lineWidth:1,axisLabelVisible:false});
rsiSeries.createPriceLine({price:30,color:'rgba(53,208,154,.35)',lineStyle:LW.LineStyle.Dashed,lineWidth:1,axisLabelVisible:false});
chart.timeScale().subscribeVisibleLogicalRangeChange(()=>{drawZones();try{const range=chart.timeScale().getVisibleRange();if(range&&state.data.length>14)rsiChart.timeScale().setVisibleRange(range);}catch{}});
chart.subscribeCrosshairMove(p=>{const c=p.seriesData?.get(candles);if(c&&Number.isFinite(c.close))setOhlc(c);else if(state.data.length)setOhlc(state.data.at(-1));});
chart.subscribeClick(onChartClick);
zoneCanvas=$('zoneOverlay');resizeObserver=new ResizeObserver(()=>drawZones());resizeObserver.observe($('chartHost'));
try{markersApi=LW.createSeriesMarkers?LW.createSeriesMarkers(candles,[]):null;}catch{markersApi=null;}
}
function updateTheme(){
document.body.classList.toggle('light',!state.dark);$('themeBtn').textContent=state.dark?'☀':'☾';
if(chart){
let t=themeColors();chart.applyOptions({layout:{background:{type:'solid',color:t.bg},textColor:t.text},grid:{vertLines:{color:t.grid},horzLines:{color:t.grid}},rightPriceScale:{borderColor:t.grid},timeScale:{borderColor:t.grid}});
rsiChart.applyOptions({layout:{background:{type:'solid',color:t.bg},textColor:t.text},grid:{horzLines:{color:t.grid}}});drawZones();
}
remember('theme',state.dark?'dark':'light');
}
function renderMarkets(){
const search=$('symbolSearch').value.trim().toLowerCase(),fav=state.favorites;
const markets=coins.filter(c=>c.symbol.toLowerCase().includes(search)||c.name.toLowerCase().includes(search)).sort((a,b)=>Number(fav.has(b.symbol))-Number(fav.has(a.symbol)));
$('marketCount').textContent=markets.length;
$('marketList').innerHTML=markets.map(c=>`<button class="market-row ${c.symbol===state.symbol?'active':''}" data-pair="${c.symbol}"><span class="coin-symbol" style="background:${c.color}">${c.icon}</span><span class="market-name"><b>${c.symbol.replace('USDT','/USDT')}</b><small>${c.name}</small></span><span data-star="${c.symbol}" class="star ${fav.has(c.symbol)?'favorite':''}" title="Toggle favorite">${fav.has(c.symbol)?'★':'☆'}</span></button>`).join('')||'<div class="empty-small">No matching pairs</div>';
}
function showInstrument(){
const c=coins.find(c=>c.symbol===state.symbol)||coins[0];
$('pairTitle').textContent=state.symbol.replace('USDT',' / USDT');$('pairSubtitle').textContent=c.name+' · Binance Spot';$('assetIcon').textContent=c.icon;$('assetIcon').style.background=c.color;
$('biasTimeframe').textContent=state.tf.toUpperCase();$('htfInterval').textContent='Higher TF: '+intervals[state.tf];
document.querySelectorAll('#timeframes button').forEach(b=>b.classList.toggle('active',b.dataset.tf===state.tf));
renderMarkets();
}
function setOhlc(c){
for(const [id,key] of [['oVal','open'],['hVal','high'],['lVal','low'],['cVal','close']])$(id).textContent=fmt(c[key]);
}
function updatePrice(v){if(!Number.isFinite(v))return;state.activePrice=v;$('lastPrice').textContent=fmt(v);$('updatedAt').textContent='Updated '+new Date().toLocaleTimeString('en-GB',{timeZone:'UTC',hour:'2-digit',minute:'2-digit',second:'2-digit'});}
function candleFromKline(k){return{time:Math.floor(Number(k[0])/1000),open:Number(k[1]),high:Number(k[2]),low:Number(k[3]),close:Number(k[4]),volume:Number(k[5])};}
function validate(rows){if(!Array.isArray(rows)||rows.length<60)throw new Error('Exchange returned insufficient candle data.');const data=rows.map(candleFromKline).filter(c=>Object.values(c).every(Number.isFinite));if(data.length<60)throw new Error('Exchange returned invalid OHLC prices.');return data.sort((a,b)=>a.time-b.time).filter((c,i,a)=>i===0||c.time!==a[i-1].time);}
async function fetchCandles(symbol,tf,limit=600,signal){
const q='?symbol='+encodeURIComponent(symbol)+'&interval='+encodeURIComponent(tf)+'&limit='+limit;
const urls=['https://data-api.binance.vision/api/v3/klines'+q,'https://api.binance.com/api/v3/klines'+q];
let error;
for(const url of urls){
try{const res=await fetch(url,{signal,cache:'no-store'});if(!res.ok)throw new Error('Exchange HTTP '+res.status);return validate(await res.json());}
catch(e){if(e.name==='AbortError')throw e;error=e;}
}
throw new Error('Unable to access public exchange candles. This network or region may block Binance. '+(error?.message||''));
}
async function fetchTicker(symbol,request){
const q='?symbol='+encodeURIComponent(symbol);
try{const res=await fetch('https://data-api.binance.vision/api/v3/ticker/24hr'+q,{cache:'no-store'});if(!res.ok)throw Error('ticker unavailable');const t=await res.json();if(request!==state.request)return;const ch=Number(t.priceChangePercent);
$('priceChange').textContent=sign(ch);$('priceChange').className='change-label '+(ch>=0?'up':'down');
$('high24').textContent=fmt(Number(t.highPrice));$('low24').textContent=fmt(Number(t.lowPrice));
$('volume24').textContent=compact(Number(t.quoteVolume))+' USDT';}catch{$('priceChange').textContent='24h n/a';}
}
function clearTimer(){clearInterval(state.refreshTimer);clearInterval(state.heartbeat);clearTimeout(state.reconnectTimer);clearTimeout(state.analysisTimer);try{state.ws?.close();}catch{}state.ws=null;}
async function loadMarket(fit=true){
const request=++state.request;state.controller?.abort();state.controller=new AbortController();clearTimer();connection('CONNECTING','Fetching historical candles...');
showInstrument();loading('Loading '+state.symbol.replace('USDT','/USDT'),'Retrieving historical OHLC data from Binance public market API.');
$('lastPrice').textContent='—';$('priceChange').textContent='—';$('high24').textContent='—';$('low24').textContent='—';$('volume24').textContent='—';state.data=[];state.analysis=null;state.htf=null;drawZones();
try{
const rows=await fetchCandles(state.symbol,state.tf,650,state.controller.signal);if(request!==state.request)return;
state.data=rows;setCandleData(true);setOhlc(rows.at(-1));updatePrice(rows.at(-1).close);showChart();connection('SYNCING','Historical data ready; opening live feed...');
analyze();fetchTicker(state.symbol,request);fetchHigherTimeframe(request);connectStream(request);
if(fit)chart.timeScale().fitContent();
try{history.replaceState(null,'',location.pathname+'?symbol='+state.symbol+'&tf='+state.tf);}catch{}
}catch(e){if(e.name==='AbortError'||request!==state.request)return;loading('Market data unavailable',e.message,true);connection('OFFLINE','Unable to fetch public exchange data');toast('Cannot load market data. Try another network or refresh.',true);}
}
function setCandleData(fit=false){
if(!state.data.length)return;
candles.setData(state.data.map(({time,open,high,low,close})=>({time,open,high,low,close})));
vol.setData($('toggleVolume').checked?state.data.map(d=>({time:d.time,value:d.volume,color:d.close>=d.open?'rgba(55,210,160,.19)':'rgba(240,94,125,.19)'})):[]);
refreshEMAs();
if(fit)chart.timeScale().fitContent();
}
function refreshEMAs(){
const show=$('toggleEMA').checked;
const data=state.data.slice(0,-1);
ema20.setData(show?Engine.ema(data,20):[]);ema50.setData(show?Engine.ema(data,50):[]);ema200.setData(show?Engine.ema(data,200):[]);
}
function refreshRsi(){
const show=$('toggleRSI').checked;$('rsiPanel').classList.toggle('hidden',!show);
rsiSeries.setData(show&&state.analysis?state.analysis.rsis.map(p=>({time:p.time,value:p.value})):[]);
if(show)try{const range=chart.timeScale().getVisibleRange();if(range)rsiChart.timeScale().setVisibleRange(range);}catch{}
}
function connectStream(request){
if(request!==state.request)return;
let connected=false;
try{
const url='wss://data-stream.binance.vision/ws/'+state.symbol.toLowerCase()+'@kline_'+state.tf;
const socket=new WebSocket(url);state.ws=socket;
socket.onopen=()=>{if(request!==state.request)return;connected=true;clearInterval(state.refreshTimer);state.refreshTimer=null;connection('LIVE','WebSocket — streaming market candles');};
socket.onmessage=e=>{
if(request!==state.request)return;
try{const packet=JSON.parse(e.data),k=packet.k;if(!k)return;
const incoming={time:Math.floor(k.t/1000),open:+k.o,high:+k.h,low:+k.l,close:+k.c,volume:+k.v};
if(!Number.isFinite(incoming.close))return;
const last=state.data.at(-1);
if(incoming.time===last?.time){state.data[state.data.length-1]=incoming;candles.update(incoming);if($('toggleVolume').checked)vol.update({time:incoming.time,value:incoming.volume,color:incoming.close>=incoming.open?'rgba(55,210,160,.19)':'rgba(240,94,125,.19)'});}
else if(incoming.time>last?.time){state.data.push(incoming);if(state.data.length>650)state.data.shift();candles.update(incoming);if($('toggleVolume').checked)vol.update({time:incoming.time,value:incoming.volume,color:incoming.close>=incoming.open?'rgba(55,210,160,.19)':'rgba(240,94,125,.19)'});refreshEMAs();analyze();}
updatePrice(incoming.close);setOhlc(incoming);
if(k.x){refreshEMAs();analyze();fetchTicker(state.symbol,request);}
}catch{}
};
socket.onerror=()=>{if(request===state.request&&!connected)connection('REST MODE','Live stream unavailable; polling every 60s');};
socket.onclose=()=>{if(request!==state.request)return;state.ws=null;connection('REST MODE','Live stream disconnected; polling every 60s');startPolling(request);state.reconnectTimer=setTimeout(()=>{if(request===state.request)connectStream(request);},45000);};
}catch{startPolling(request);}
clearInterval(state.heartbeat);state.heartbeat=setInterval(()=>{if(state.ws&&state.ws.readyState===1)return;startPolling(request);},20000);
}
function startPolling(request){
if(state.refreshTimer)return;
state.refreshTimer=setInterval(async()=>{
if(request!==state.request)return;
try{const rows=await fetchCandles(state.symbol,state.tf,100);if(request!==state.request)return;
for(const c of rows){const last=state.data.at(-1);if(c.time===last?.time)state.data[state.data.length-1]=c;else if(c.time>last?.time)state.data.push(c);}
if(state.data.length>650)state.data=state.data.slice(-650);
setCandleData();updatePrice(state.data.at(-1).close);setOhlc(state.data.at(-1));analyze();fetchTicker(state.symbol,request);
}catch{}
},60000);
}
async function fetchHigherTimeframe(request){
const tf=intervals[state.tf];$('htfValue').textContent='Checking…';
try{
const data=await fetchCandles(state.symbol,tf,350,state.controller?.signal);
if(request!==state.request)return;
const htf=Engine.calculate(data.slice(0,-1));state.htf=htf;$('htfValue').textContent=htf.direction==='bull'?'BULLISH':htf.direction==='bear'?'BEARISH':'RANGING';$('htfValue').className=htf.direction==='bull'?'text-green':htf.direction==='bear'?'text-red':'';
$('htfInterval').textContent=tf.toUpperCase()+' confirmed';renderBias();
}catch{if(request===state.request){$('htfValue').textContent='Unavailable';$('htfInterval').textContent=tf.toUpperCase()+' data unavailable';}}
}
function analyze(){
if(!state.data||state.data.length<65)return;
try{
const closed=state.data.slice(0,-1);
state.analysis=Engine.calculate(closed);
renderAnalysis();renderMarkers();drawZones();refreshRsi();
$('analysisDot').className='status-dot online';$('analysisLabel').textContent='Analyzed '+closed.length+' confirmed candles';
$('smcAsOf').textContent=date(closed.at(-1).time);
}catch(e){$('analysisLabel').textContent='Analysis error';toast('Analysis: '+e.message,true);}
}
function renderBias(){
const a=state.analysis;if(!a)return;
const dir=a.direction,card=document.querySelector('.bias-card');card.classList.toggle('bearish',dir==='bear');card.classList.toggle('neutral',dir==='neutral');
$('biasText').textContent=dir==='bull'?'BULLISH':dir==='bear'?'BEARISH':'RANGING';$('biasIcon').textContent=dir==='bull'?'↗':dir==='bear'?'↘':'◆';
const aligned=state.htf?.direction===dir&&dir!=='neutral';const score=Math.min(5,a.confluence+(aligned?1:0));$('biasMeterFill').style.width=(score/6*100)+'%';$('biasScore').textContent=score+'/6 filters';
$('biasReason').textContent=aligned?'Aligned with higher timeframe':a.latestEvent?'Latest '+a.latestEvent.type+' '+relative(a.latestEvent.time):'No confirmed recent structure break';
}
function renderAnalysis(){
const a=state.analysis;if(!a)return;renderBias();const e=a.latestEvent;
$('structureValue').textContent=e?e.type+' '+(e.direction==='bull'?'↑':'↓'):'—';$('structureValue').className=e?(e.direction==='bull'?'text-green':'text-red'):'';
$('structureAge').textContent=e?relative(e.time):'No confirmed break';
$('bullFvgCount').textContent=a.fvgs.filter(z=>z.direction==='bull').length;
$('bearFvgCount').textContent=a.fvgs.filter(z=>z.direction==='bear').length;
$('obCount').textContent=a.blocks.length;
$('sweepCount').textContent=a.sweeps.filter(s=>s.i>=a.dataCount-100).length;
const r=a.range;$('rangeLow').textContent=fmt(r.low);$('rangeHigh').textContent=fmt(r.high);
$('pdZone').textContent=r.position<.45?'DISCOUNT':r.position>.55?'PREMIUM':'EQUILIBRIUM';
$('pdPin').style.left=Math.max(1,Math.min(99,(1-r.position)*100))+'%';
$('techRsi').textContent=num(a.rsi,1)+' '+(a.rsi>=70?'· Overbought':a.rsi<=30?'· Oversold':'· Neutral');
$('techEma').textContent=a.ema20value>a.ema50value?'Bullish alignment':'Bearish alignment';
$('techEma').className=a.ema20value>a.ema50value?'text-green':'text-red';
$('techAtr').textContent=fmt(a.atr);
const sweep=a.sweeps.at(-1);$('techSweep').textContent=sweep?sweep.type+' · '+relative(sweep.time):'None detected';
$('rsiValue').textContent=num(a.rsi,1);$('stripRSI').textContent='RSI 14 '+num(a.rsi,1);
renderZonesList();renderBottom();
}
function renderZonesList(){
const a=state.analysis;if(!a)return;
const price=state.activePrice||a.last.close;
const items=[...a.activeZones].sort((x,y)=>Math.abs((x.high+x.low)/2-price)-Math.abs((y.high+y.low)/2-price)).slice(0,5);
$('zonesList').innerHTML=items.length?items.map(z=>{
const center=(z.low+z.high)/2;
return `<div class="zone-item"><span class="zone-indicator ${z.direction==='bear'?'bear':''}"></span><div class="zone-copy"><b>${z.direction==='bull'?'Bullish':'Bearish'} ${z.kind}</b><small>${relative(z.created)} · ${z.partial?'partially touched':'untouched'}</small></div><div class="zone-value">${fmt(z.low)} – ${fmt(z.high)}<small>${num((center-price)/price*100,2)}% from price</small></div></div>`;
}).join(''):'<div class="empty-small">No unmitigated zones detected in recent candles.</div>';
}
function renderMarkers(){
if(!markersApi)return;
const a=state.analysis;
if(!a||!state.autoSmc||!$('toggleMarkers').checked){markersApi.setMarkers([]);return;}
const markers=a.events.slice(-40).map(e=>({time:e.time,position:e.direction==='bull'?'belowBar':'aboveBar',color:e.direction==='bull'?'#35d3a0':'#f46c85',shape:e.direction==='bull'?'arrowUp':'arrowDown',text:e.type})).concat(a.sweeps.slice(-15).map(e=>({time:e.time,position:e.direction==='bull'?'belowBar':'aboveBar',color:'#f5b85e',shape:'circle',text:'SWEEP'})));
markers.sort((a,b)=>a.time-b.time);
markersApi.setMarkers(markers);
}
function drawZones(){
if(!zoneCanvas||!chart||!candles)return;
const rect=$('chartHost').getBoundingClientRect(),w=Math.floor(rect.width),h=Math.floor(rect.height),dpr=Math.min(window.devicePixelRatio||1,2);
if(!w||!h)return;zoneCanvas.width=Math.floor(w*dpr);zoneCanvas.height=Math.floor(h*dpr);const ctx=zoneCanvas.getContext('2d');ctx.scale(dpr,dpr);ctx.clearRect(0,0,w,h);
if(state.autoSmc&&$('toggleZones').checked&&state.analysis){
const zones=state.analysis.activeZones.slice(0,9);
const time=chart.timeScale();
for(const z of zones){
const x=time.timeToCoordinate(z.startTime),y1=candles.priceToCoordinate(z.high),y2=candles.priceToCoordinate(z.low);
if(x===null||y1===null||y2===null)continue;
const start=Math.max(0,x),end=w-58,top=Math.max(0,Math.min(y1,y2)),bottom=Math.min(h,Math.max(y1,y2));
if(end<=start||bottom<=top)continue;
ctx.fillStyle=z.direction==='bull'?'rgba(59,216,161,.095)':'rgba(250,104,126,.095)';ctx.fillRect(start,top,end-start,bottom-top);
ctx.strokeStyle=z.direction==='bull'?'rgba(59,216,161,.35)':'rgba(250,104,126,.35)';ctx.setLineDash([4,4]);ctx.strokeRect(start,top,end-start,bottom-top);ctx.setLineDash([]);
if(bottom-top>14){ctx.fillStyle=z.direction==='bull'?'#35c99b':'#f17b8c';ctx.font='9px IBM Plex Mono, monospace';ctx.fillText((z.kind==='FVG'?'FVG':'OB')+' '+(z.direction==='bull'?'▲':'▼'),start+6,top+11);}
}
}
}
function renderBottom(){
const a=state.analysis,root=$('bottomTable');if(!a){root.innerHTML='<div class="table-empty">Loading structure...</div>';return;}
$('eventsCount').textContent=a.events.length+a.sweeps.length;
if(state.tableTab==='events'){
const items=[...a.events,...a.sweeps].sort((x,y)=>y.time-x.time).slice(0,22);
root.innerHTML=items.length?'<table class="data-table"><thead><tr><th>TIME (UTC)</th><th>EVENT</th><th>BIAS</th><th>LEVEL</th><th>DETAIL</th></tr></thead><tbody>'+items.map(x=>`<tr><td>${date(x.time)}</td><td class="event-name ${x.direction==='bull'?'text-green':'text-red'}">${x.type}</td><td>${x.direction==='bull'?'BULLISH':'BEARISH'}</td><td>${fmt(x.price)}</td><td>${x.description}</td></tr>`).join('')+'</tbody></table>':'<div class="table-empty">No confirmed structure events found in this window.</div>';
}else{
const items=[...a.activeZones,...a.liquidity].sort((x,y)=>(y.i||0)-(x.i||0)).slice(0,23);
root.innerHTML=items.length?'<table class="data-table"><thead><tr><th>DETECTED</th><th>TYPE</th><th>SIDE</th><th>LOW</th><th>HIGH</th></tr></thead><tbody>'+items.map(x=>`<tr><td>${date(x.created||x.time)}</td><td>${x.kind}</td><td class="${x.direction==='bull'?'text-green':x.direction==='bear'?'text-red':''}">${x.direction.toUpperCase()}</td><td>${fmt(x.low??x.price)}</td><td>${fmt(x.high??x.price)}</td></tr>`).join('')+'</tbody></table>':'<div class="table-empty">No active levels detected.</div>';
}
}
function onChartClick(param){
if(state.drawMode==='cursor'||!param?.point)return;
const price=candles.coordinateToPrice(param.point.y),time=param.time||chart.timeScale().coordinateToTime(param.point.x);
if(!Number.isFinite(price)||!time)return;
if(state.drawMode==='horizontal'){
const line=candles.createPriceLine({price,color:'#62aeff',lineWidth:2,lineStyle:LW.LineStyle.Dashed,axisLabelVisible:true,title:'USER LEVEL'});state.drawings.push({kind:'price',line});toast('Horizontal level added at '+fmt(price));setDrawMode('cursor');return;
}
if(!state.drawStart){state.drawStart={time,price};$('drawHint').textContent='Select the second point on the chart';return;}
const start=state.drawStart;state.drawStart=null;
if(state.drawMode==='trend'){
if(start.time===time){toast('Choose two different candles.',true);return;}
const line=addLine('#64b7ff',2);const pts=[{time:start.time,value:start.price},{time,value:price}].sort((a,b)=>a.time>b.time?1:-1);line.setData(pts);state.drawings.push({kind:'series',line});toast('Trend line added.');
}else if(state.drawMode==='fib'){
const prices=[0,.236,.382,.5,.618,.786,1];const lines=[];
for(const level of prices){const p=start.price+(price-start.price)*level;lines.push(candles.createPriceLine({price:p,color:level===.618?'#f9bd66':'rgba(158,133,246,.65)',lineWidth:1,lineStyle:LW.LineStyle.Dashed,axisLabelVisible:true,title:'FIB '+(level*100).toFixed(1)+'%'}));}
state.drawings.push({kind:'fib',lines});toast('Fibonacci levels added.');
}
setDrawMode('cursor');
}
function setDrawMode(mode){
state.drawMode=mode;state.drawStart=null;
document.querySelectorAll('[data-draw]').forEach(b=>b.classList.toggle('active',b.dataset.draw===mode));
$('drawHint').classList.toggle('hidden',mode==='cursor');
if(mode!=='cursor')$('drawHint').textContent=mode==='horizontal'?'Click chart to add horizontal level':'Click the first point on the chart';
}
function clearDrawings(){
for(const d of state.drawings){try{if(d.kind==='price')candles.removePriceLine(d.line);else if(d.kind==='fib')d.lines.forEach(x=>candles.removePriceLine(x));else chart.removeSeries(d.line);}catch{}}
state.drawings=[];setDrawMode('cursor');toast('Drawings cleared.');
}
function downloadCsv(){
if(!state.data.length){toast('No candles to export yet',true);return;}
const header='timestamp_utc,open,high,low,close,volume';
const content=[header,...state.data.map(c=>[new Date(c.time*1000).toISOString(),c.open,c.high,c.low,c.close,c.volume].join(','))].join('\n');
const blob=new Blob([content],{type:'text/csv;charset=utf-8'}),url=URL.createObjectURL(blob),link=document.createElement('a');
link.href=url;link.download='RibhLab_'+state.symbol+'_'+state.tf+'_OHLCV.csv';document.body.appendChild(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),2000);toast('OHLCV CSV exported.');
}
function bind(){
$('marketList').addEventListener('click',e=>{
const star=e.target.closest('[data-star]');if(star){const s=star.dataset.star;if(state.favorites.has(s))state.favorites.delete(s);else state.favorites.add(s);remember('favorites',JSON.stringify([...state.favorites]));renderMarkets();return;}
const row=e.target.closest('[data-pair]');if(row&&row.dataset.pair!==state.symbol){state.symbol=row.dataset.pair;clearDrawings();loadMarket();}
});
$('symbolSearch').addEventListener('input',renderMarkets);
$('timeframes').addEventListener('click',e=>{const b=e.target.closest('[data-tf]');if(b&&b.dataset.tf!==state.tf){state.tf=b.dataset.tf;clearDrawings();loadMarket();}});
$('refreshBtn').addEventListener('click',()=>loadMarket(false));
$('fitBtn').addEventListener('click',()=>chart?.timeScale().fitContent());
$('csvBtn').addEventListener('click',downloadCsv);
$('themeBtn').addEventListener('click',()=>{state.dark=!state.dark;updateTheme();});
$('reAnalyzeBtn').addEventListener('click',()=>{analyze();fetchHigherTimeframe(state.request);toast('SMC analysis refreshed.');});
$('indicatorsBtn').addEventListener('click',e=>{e.stopPropagation();$('indicatorMenu').classList.toggle('open');});
document.addEventListener('click',e=>{if(!e.target.closest('.toolbar-menu'))$('indicatorMenu').classList.remove('open');});
$('toggleEMA').addEventListener('change',refreshEMAs);
$('toggleVolume').addEventListener('change',()=>{if(state.data.length)vol.setData($('toggleVolume').checked?state.data.map(d=>({time:d.time,value:d.volume,color:d.close>=d.open?'rgba(55,210,160,.19)':'rgba(240,94,125,.19)'})):[]);});
$('toggleRSI').addEventListener('change',refreshRsi);
$('toggleZones').addEventListener('change',drawZones);
$('toggleMarkers').addEventListener('change',renderMarkers);
$('autoSmcBtn').addEventListener('click',()=>{state.autoSmc=!state.autoSmc;$('autoSmcBtn').classList.toggle('active-tool',state.autoSmc);$('smcSwitchDot').style.opacity=state.autoSmc?'1':'.1';drawZones();renderMarkers();toast(state.autoSmc?'Auto SMC overlays on':'Auto SMC overlays hidden');});
document.querySelectorAll('[data-draw]').forEach(b=>b.addEventListener('click',()=>setDrawMode(b.dataset.draw)));
$('clearDrawingsBtn').addEventListener('click',clearDrawings);
document.querySelectorAll('[data-tab]').forEach(b=>b.addEventListener('click',()=>{state.tableTab=b.dataset.tab;document.querySelectorAll('[data-tab]').forEach(n=>n.classList.toggle('active',n===b));renderBottom();}));
const close=()=>{$('guideModal').classList.add('hidden');};
$('guideBtn').addEventListener('click',()=>{$('guideModal').classList.remove('hidden');});
$('closeGuideBtn').addEventListener('click',close);$('guideDoneBtn').addEventListener('click',close);
$('guideModal').addEventListener('click',e=>{if(e.target===$('guideModal'))close();});
document.addEventListener('keydown',e=>{if(e.key==='Escape'){close();setDrawMode('cursor');}});
}
function start(){
try{
const url=new URL(location.href),requested=url.searchParams.get('symbol'),tf=url.searchParams.get('tf');
if(coins.some(c=>c.symbol===requested))state.symbol=requested;
if(Object.hasOwn(intervals,tf))state.tf=tf;
try{state.favorites=new Set(JSON.parse(preference('favorites')||'[]'));}catch{}
state.dark=preference('theme')!=='light';
bind();renderMarkets();updateTheme();setupCharts();showInstrument();loadMarket();
}catch(e){loading('Unable to start the chart',e.message,true);connection('OFFLINE','Chart library missing');console.error(e);}
}
window.addEventListener('DOMContentLoaded',start);
})();