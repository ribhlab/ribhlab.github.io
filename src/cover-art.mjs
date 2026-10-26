// Original, offline SVG artwork for every article. No third-party images, logos or remote assets.
const PALETTES={
 freelance:['#081e32','#153e51','#44e4bc','#a1fff0'],
 'online-business':['#112033','#263d64','#ffba6e','#ffe2b0'],
 'ai-automation':['#101c3d','#29345e','#a78bfa','#d9cfff'],
 'mobile-apps':['#09233f','#175e75','#33d9e8','#b2fff7'],
 'games-security':['#171b41','#473b79','#ff8db7','#f9d3e3'],
 'trading-risk':['#0b2236','#16465a','#5be6bb','#b5ffeb'],
 'crypto-web3':['#111a3d','#2c3969','#8cb1ff','#d5e2ff'],
 'gold-macro':['#251c32','#51405b','#f3c96e','#fff0b7']
};
const LABELS={freelance:'FREELANCE','online-business':'DIGITAL BUSINESS','ai-automation':'AI & AUTOMATION','mobile-apps':'MOBILE APPS','games-security':'GAME DEVELOPMENT','trading-risk':'TRADING EDUCATION','crypto-web3':'CRYPTO RESEARCH','gold-macro':'GOLD & MACRO'};
const escXml=x=>String(x).replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const hash=x=>[...x].reduce((a,c)=>((a*33)^c.charCodeAt(0))>>>0,5381);
const rng=seed=>()=>{seed=(1664525*seed+1013904223)>>>0;return seed/4294967296;};
const rr=(x,y,w,h,fill,r=16,other='')=>'<rect x="'+x+'" y="'+y+'" width="'+w+'" height="'+h+'" rx="'+r+'" fill="'+fill+'" '+other+'/>';
const line=(x1,y1,x2,y2,color,stroke=3,other='')=>'<line x1="'+x1+'" y1="'+y1+'" x2="'+x2+'" y2="'+y2+'" stroke="'+color+'" stroke-width="'+stroke+'" stroke-linecap="round" '+other+'/>';
const circle=(x,y,r,color,more='')=>'<circle cx="'+x+'" cy="'+y+'" r="'+r+'" fill="'+color+'" '+more+'/>';
const poly=(points,color,stroke=5)=>'<polyline points="'+points+'" fill="none" stroke="'+color+'" stroke-width="'+stroke+'" stroke-linecap="round" stroke-linejoin="round"/>';
function symbol(section,v,primary,light){
 const a=primary,b=light,m='#b4d2ec';
 if(section==='freelance')return rr(420,210,380,225,'#1d3650',24,'stroke="'+a+'" stroke-width="4"')+
  rr(440,230,340,30,'#35576b',9)+rr(455,278,145,125,'#254c5d',14)+rr(620,278,140,24,a,8)+
  rr(620,317,115,12,'#719ba7',6)+rr(620,340,135,12,'#719ba7',6)+
  line(480,367,570,367,a,10)+circle(482,323,22,b)+circle(537,323,22,a)+
  '<path d="M465 462h290l35 22H430z" fill="#6b91a5" opacity=".68"/>';
 if(section==='online-business')return rr(450,213,305,265,'#24445e',22,'stroke="'+a+'" stroke-width="4"')+
  '<path d="M468 273h271l-23 67H491z" fill="'+a+'"/>'+
  rr(484,341,237,106,'#1a3653',10)+rr(506,358,90,70,'#6a9aa0',7)+
  '<path d="M526 388l21-22 27 34" fill="none" stroke="'+b+'" stroke-width="6"/>'+
  rr(619,361,85,14,b,7)+rr(619,390,70,11,'#8aa0b4',6)+
  circle(489,276,15,b)+circle(544,276,15,b)+circle(601,276,15,b)+circle(661,276,15,b)+circle(716,276,15,b);
 if(section==='ai-automation')return rr(484,235,224,205,'#263660',28,'stroke="'+a+'" stroke-width="6"')+
  rr(518,268,156,140,'#15234e',18)+
  circle(556,325,13,a)+circle(633,325,13,a)+circle(595,369,13,b)+
  poly('556,325 595,369 633,325',a,5)+
  Array.from({length:5},(_,i)=>line(495+i*46,198,495+i*46,234,b,5)).join('')+
  Array.from({length:5},(_,i)=>line(495+i*46,443,495+i*46,480,b,5)).join('')+
  Array.from({length:4},(_,i)=>line(443,251+i*49,481,251+i*49,b,5)).join('')+
  Array.from({length:4},(_,i)=>line(708,251+i*49,752,251+i*49,b,5)).join('');
 if(section==='mobile-apps')return rr(495,182,205,317,'#101f3b',32,'stroke="'+a+'" stroke-width="6"')+
  rr(511,206,173,266,'#20476b',20)+rr(567,211,63,10,'#0e243c',5)+
  Array.from({length:9},(_,i)=>rr(528+(i%3)*54,258+Math.floor(i/3)*61,37,38,i%3===0?a:i%3===1?'#88a8ef':b,9)).join('')+
  rr(572,482,51,6,'#c8e2ef',4);
 if(section==='games-security')return '<path d="M460 305c-28-36-60 0-67 49l-18 93c-7 31 27 47 49 26l64-59h236l64 59c23 21 56 5 49-26l-18-93c-9-48-41-85-69-49-50-20-240-20-290 0z" fill="#344266" stroke="'+a+'" stroke-width="6"/>'+
  rr(477,349,90,20,a,6)+rr(512,314,20,90,a,6)+
  circle(706,346,19,b)+circle(751,388,19,a)+circle(710,415,13,'#8ba7d8')+
  rr(585,337,43,16,'#8193be',7)+rr(647,337,42,16,'#8193be',7);
 if(section==='trading-risk'){
  const candles=Array.from({length:12},(_,i)=>{const x=440+i*29;const y=280+Math.round(Math.sin((i+v)/2.2)*48)+Math.round((11-i)*3);const h=40+Math.round(Math.abs(Math.sin(i+v))*48);const up=(i+v)%3!==0;return line(x,y-17,x,y+h+13,b,3)+rr(x-10,y,20,h,up?a:'#ef9b9e',3);}).join('');
  return rr(414,224,392,255,'#142f4a',17,'stroke="'+a+'" stroke-width="3"')+
   Array.from({length:4},(_,i)=>line(438,274+i*56,782,274+i*56,'#668499',2,'opacity=".28"')).join('')+candles+
   '<path d="M468 439l72-47 56 15 55-77 67 16 42-73" fill="none" stroke="'+b+'" stroke-width="5" stroke-linejoin="round" opacity=".8"/>';
 }
 if(section==='crypto-web3')return circle(595,350,120,'#243d6c','stroke="'+a+'" stroke-width="7"')+
  '<path d="M595 268l80 45v78l-80 44-80-44v-78z" fill="#304976" stroke="'+b+'" stroke-width="4"/>'+
  poly('595,268 595,435 515,391 675,313 515,313 675,391',a,3)+
  circle(595,268,13,a)+circle(595,435,13,a)+circle(515,313,13,b)+circle(675,313,13,b)+
  circle(515,391,13,b)+circle(675,391,13,b);
 return rr(438,385,150,82,'#99794e',13,'stroke="'+b+'" stroke-width="5"')+
  rr(522,323,150,88,'#c79a55',13,'stroke="'+b+'" stroke-width="5"')+
  rr(603,389,150,77,'#e3b66d',13,'stroke="'+b+'" stroke-width="5"')+
  poly('465,309 518,270 553,281 601,224 646,254 689,211 741,230',b,8)+
  Array.from({length:7},(_,i)=>circle(465+[0,53,88,136,181,224,276][i], [309,270,281,224,254,211,230][i],7,a)).join('');
}
export function renderArticleCover(article,section){
 const seed=hash(article.slug),rand=rng(seed),v=seed%7;
 const [bg,mid,accent,light]=PALETTES[section]||PALETTES['online-business'];
 const orbit=Array.from({length:12},(_,i)=>{const x=Math.round(95+rand()*1000),y=Math.round(70+rand()*530),r=Math.round(5+rand()*24);return circle(x,y,r,light,'opacity="'+(0.035+rand()*.095).toFixed(2)+'"');}).join('');
 const bars=Array.from({length:7},(_,i)=>rr(848+i*30,422-Math.round(rand()*90),15,55+Math.round(rand()*90),i%2?light:accent,5,'opacity=".56"')).join('');
 const angle=-11+(seed%23);
 const chip=rr(125,410,188,74,'#183852',17,'stroke="'+accent+'" stroke-width="2" opacity=".9"')+
  circle(157,448,18,accent)+line(187,434,283,434,light,8)+line(187,456,251,456,'#94b2c7',6);
 const bubbles=rr(852,182,230,105,'#213d5a',18,'stroke="'+accent+'" stroke-width="2"')+
  rr(878,205,114,12,light,6,'opacity=".65"')+
  rr(878,234,162,13,accent,6)+rr(878,257,87,10,'#afc9de',5,'opacity=".56"');
 return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 675" width="1200" height="675" role="img" aria-label="'+escXml('Original RibhLab editorial illustration: '+(LABELS[section]||'DIGITAL SKILLS'))+'">'+
 '<defs><linearGradient id="bg" x1="0" x2="1" y1="1" y2="0"><stop offset="0%" stop-color="'+bg+'"/><stop offset="100%" stop-color="'+mid+'"/></linearGradient>'+
 '<radialGradient id="halo"><stop offset="0" stop-color="'+accent+'" stop-opacity=".29"/><stop offset="1" stop-color="'+accent+'" stop-opacity="0"/></radialGradient>'+
 '<linearGradient id="panel" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#274867"/><stop offset="1" stop-color="#10243d"/></linearGradient>'+
 '<filter id="shadow"><feDropShadow dx="0" dy="18" stdDeviation="19" flood-opacity=".27"/></filter>'+
 '<pattern id="grid" width="42" height="42" patternUnits="userSpaceOnUse"><path d="M42 0H0V42" fill="none" stroke="#b8d0dd" stroke-opacity=".06"/></pattern></defs>'+
 rr(0,0,1200,675,'url(#bg)',0)+rr(0,0,1200,675,'url(#grid)',0)+
 circle(633,325,320,'url(#halo)')+orbit+
 '<path d="M0 558Q365 492 650 585T1200 528" fill="none" stroke="'+accent+'" stroke-width="2" opacity=".24"/>'+
 rr(321,121,553,429,'url(#panel)',30,'filter="url(#shadow)" stroke="'+accent+'" stroke-opacity=".56" stroke-width="3"')+
 rr(344,144,507,36,'#18354b',12)+circle(366,162,6,accent)+circle(387,162,6,light)+circle(408,162,6,'#93acc8')+
 symbol(section,v,accent,light)+
 '<g transform="rotate('+angle+',233,449)">'+chip+'</g>'+bubbles+
 bars+
 '<text x="84" y="92" fill="'+light+'" font-family="Arial,Helvetica,sans-serif" font-size="23" font-weight="700" letter-spacing="6">RIBHLAB</text>'+
 '<text x="84" y="125" fill="#b8d3e0" font-family="Arial,Helvetica,sans-serif" font-size="13" letter-spacing="3">'+escXml(LABELS[section]||'ORIGINAL GUIDE')+'</text>'+
 rr(84,151,145,5,accent,2)+
 '<text x="91" y="616" fill="#adcad5" font-family="Arial,Helvetica,sans-serif" font-size="14" letter-spacing="2">ORIGINAL EDITORIAL ART</text>'+
 '<text x="1112" y="616" text-anchor="end" fill="'+light+'" font-family="Arial,Helvetica,sans-serif" font-size="18" font-weight="700">R.</text>'+
 '</svg>';
}
