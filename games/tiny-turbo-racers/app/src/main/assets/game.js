
"use strict";
// Tiny Turbo Racers - original HTML5 Canvas game by RibhLab (2026).
// Runs completely offline in Android WebView. No tracking, ads or network access.
const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];
const worlds = [
  {name:"Toy City",emoji:"🏙️",sky:"#61ccff",ground:"#8add77",road:"#595f78",accent:"#ffad36",art:"🏙️",desc:"Rainbow toy-town"},
  {name:"Beach Track",emoji:"🏝️",sky:"#70dcff",ground:"#ffdf84",road:"#65778a",accent:"#18bcdc",art:"🏖️",desc:"Palm trees & waves"},
  {name:"Candy Park",emoji:"🍭",sky:"#ffa2e5",ground:"#b5e58a",road:"#936b9d",accent:"#ff55b8",art:"🍩",desc:"A sweet adventure"},
  {name:"Dino Valley",emoji:"🦕",sky:"#69dbf1",ground:"#8ad45a",road:"#647b79",accent:"#f8a737",art:"🦕",desc:"Friendly dinosaurs"}
];
const cars = [
  {name:"Speedy",icon:"⚡",color:"#f73542",emoji:"🏎️",desc:"Ready to zoom!"},
  {name:"Buddy",icon:"⭐",color:"#2d8ff4",emoji:"🚙",desc:"A true teammate!"},
  {name:"Bubbles",icon:"🌸",color:"#ffd33f",emoji:"🚕",desc:"Always smiling!"},
  {name:"Ranger",icon:"🏔️",color:"#41c47b",emoji:"🚜",desc:"Loves adventures!"}
];
const paints = ["#f73542","#2d8ff4","#ffd33f","#41c47b","#a75df8","#ff7cc6"];
function stored(k,fallback){try{return JSON.parse(localStorage.getItem(k))??fallback}catch(e){return fallback}}
function save(k,v){try{localStorage.setItem(k,JSON.stringify(v))}catch(e){}}
let chosenWorld=stored("tiny_world",0),chosenCar=stored("tiny_car",0);
let carPaint=stored("tiny_paints",cars.map(c=>c.color)),wallet=stored("tiny_wallet",0);
if(!Array.isArray(carPaint)||carPaint.length!==4)carPaint=cars.map(c=>c.color);
chosenWorld=Math.max(0,Math.min(3,Number(chosenWorld)||0));
chosenCar=Math.max(0,Math.min(3,Number(chosenCar)||0));
let current="home",race=null,heldLeft=false,heldRight=false,soundEnabled=true,audio=null;
let toastTimer=0;
function coins(){ $("#balance").textContent=wallet }
function toast(message){const el=$("#toast");el.textContent=message;el.classList.add("show");clearTimeout(toastTimer);toastTimer=setTimeout(()=>el.classList.remove("show"),2200)}
function beep(freq=660,duration=.085,type="sine"){
 if(!soundEnabled)return;
 try{audio=audio||new(window.AudioContext||window.webkitAudioContext)();const o=audio.createOscillator(),g=audio.createGain();
 o.type=type;o.frequency.value=freq;g.gain.setValueAtTime(.055,audio.currentTime);g.gain.exponentialRampToValueAtTime(.001,audio.currentTime+duration);
 o.connect(g);g.connect(audio.destination);o.start();o.stop(audio.currentTime+duration)}catch(e){}
}
function show(id){
 if(id==="race")document.body.classList.add("in-race");else document.body.classList.remove("in-race");
 $$(".screen").forEach(e=>e.classList.toggle("active",e.id===id));current=id;heldLeft=heldRight=false;
 if(id==="garage")renderGarageUi();
 if(id==="worlds")renderWorlds();
 if(id!=="race" && race)race.paused=true;
 coins();beep(600,.05);
}
function renderWorlds(){
 const grid=$("#worldGrid");grid.innerHTML="";
 worlds.forEach((w,i)=>{
 const b=document.createElement("button");b.className="world-card"+(chosenWorld===i?" chosen":"");
 b.style.setProperty("--sky",w.sky);b.style.setProperty("--ground",w.ground);
 b.innerHTML='<span class="world-art">'+w.art+'</span><h3>'+w.emoji+" "+w.name+'</h3><span class="world-check">'+(chosenWorld===i?"✓":"☆")+"</span>";
 b.onclick=()=>{chosenWorld=i;save("tiny_world",i);renderWorlds();beep(850,.09)};
 grid.appendChild(b);
 });
}
function renderGarageUi(){
 $("#carTitle").textContent=cars[chosenCar].icon+" "+cars[chosenCar].name;
 const grid=$("#carGrid");grid.innerHTML="";
 cars.forEach((car,i)=>{
 const btn=document.createElement("button");btn.className="car-choice"+(chosenCar===i?" chosen":"");
 btn.innerHTML='<span class="car-emoji">'+car.emoji+"</span>"+car.icon+" "+car.name;
 btn.onclick=()=>{chosenCar=i;save("tiny_car",i);renderGarageUi();beep(620+i*100,.12)};grid.appendChild(btn);
 });
 const p=$("#paintColors");p.innerHTML="";
 paints.forEach(color=>{
 const b=document.createElement("button");b.className="paint-dot"+(color===carPaint[chosenCar]?" chosen":"");b.style.background=color;
 b.setAttribute("aria-label","Paint car "+color);
 b.onclick=()=>{carPaint[chosenCar]=color;save("tiny_paints",carPaint);renderGarageUi();beep(890,.05)};p.appendChild(b);
 });
}
$$("[data-screen]").forEach(b=>b.addEventListener("click",()=>show(b.dataset.screen)));
$("#homeHow").onclick=()=>toast("❮ ❯ to steer • ⚡ for TURBO • collect ⭐");
$("#soundBtn").onclick=()=>{soundEnabled=!soundEnabled;$("#soundBtn").textContent=soundEnabled?"🔊":"🔇";if(soundEnabled)beep(880)};
$("#raceFromWorlds").onclick=startRace;
$("#againBtn").onclick=startRace;
$("#pauseBtn").onclick=()=>{if(!race)return;race.paused=true;$("#pausePanel").classList.remove("hidden");beep(420)};
$("#resumeBtn").onclick=()=>{if(!race)return;race.paused=false;$("#pausePanel").classList.add("hidden");beep(600)};
$("#quitRace").onclick=()=>{race=null;$("#pausePanel").classList.add("hidden");show("home")};
function holdButton(selector,side){
 const el=$(selector);
 el.addEventListener("pointerdown",e=>{e.preventDefault();el.setPointerCapture(e.pointerId);if(side==="left")heldLeft=true;else heldRight=true});
 const release=e=>{e.preventDefault();if(side==="left")heldLeft=false;else heldRight=false};
 el.addEventListener("pointerup",release);el.addEventListener("pointercancel",release);el.addEventListener("lostpointercapture",release);
}
holdButton("#leftBtn","left");holdButton("#rightBtn","right");
$("#boostBtn").onclick=()=>{
 if(!race||race.paused||race.countdown>0||race.cooldown>0)return;
 race.boost=3.3;race.cooldown=10;beep(1050,.22,"sawtooth");$("#boostBtn").classList.add("cooldown");
};
document.addEventListener("keydown",e=>{
 if(["ArrowLeft","ArrowRight"," ","Escape"].includes(e.key))e.preventDefault();
 if(e.key==="ArrowLeft")heldLeft=true;if(e.key==="ArrowRight")heldRight=true;
 if(e.key===" "&&current==="race")$("#boostBtn").click();
 if(e.key==="Escape"||e.key==="Backspace")window.kidsBack();
});
document.addEventListener("keyup",e=>{if(e.key==="ArrowLeft")heldLeft=false;if(e.key==="ArrowRight")heldRight=false});
window.kidsBack=()=>{if(current==="race"&&race&&!race.paused)$("#pauseBtn").click();else if(current==="race"&&race&&race.paused)$("#resumeBtn").click();else show("home")};
function startRace(){
 race={t:0,progress:0,lane:0,stars:0,boost:0,cooldown:0,paused:false,countdown:3.4,
 nextStar:0,missed:0,car:chosenCar,world:chosenWorld,shake:0,lastPlace:4};
 $("#pausePanel").classList.add("hidden");$("#countdown").classList.remove("hidden");$("#boostBtn").classList.remove("cooldown");
 $("#hudStars").textContent="⭐ 0";$("#hudPlace").textContent="🏆 4 / 4";$("#hudLap").textContent="🏁 LAP 1 / 3";
 show("race");
}
const clamp=(v,a,b)=>Math.min(b,Math.max(a,v));
const ease=(a,b,t)=>a+(b-a)*t;
function updateRace(dt){
 if(!race||race.paused)return;
 race.t+=dt;
 if(race.countdown>0){
   const old=Math.ceil(race.countdown);race.countdown-=dt;
   const newCount=Math.ceil(race.countdown);
   $("#countdown").textContent=newCount>0?String(newCount):"GO!";
   if(old!==newCount)beep(newCount>0?440+newCount*100:880,.13);
   if(race.countdown<-.7){race.countdown=0;$("#countdown").classList.add("hidden")}
   else if(race.countdown<=0)race.countdown=-.71;
   return;
 }
 let turn=(heldRight?1:0)-(heldLeft?1:0);
 race.lane=clamp(race.lane+turn*dt*1.3,-.96,.96);
 if(race.boost>0)race.boost=Math.max(0,race.boost-dt);
 race.cooldown=Math.max(0,race.cooldown-dt);
 const speed=(race.boost>0?35:23)*(Math.abs(race.lane)>.85?.88:1);
 race.progress+=dt*speed;
 const pickupAt=80+race.nextStar*112;
 if(race.progress>=pickupAt){
   const target=Math.sin(race.nextStar*2.6)*.65;
   if(Math.abs(race.lane-target)<.52){race.stars++;beep(800+race.stars*65,.08);race.shake=.11}
   else race.missed++;
   race.nextStar++;$("#hudStars").textContent="⭐ "+race.stars;
 }
 const rivals=[race.progress+Math.sin(race.t*.7+1)*45+38,race.progress+Math.cos(race.t*.53+2)*64+4,race.progress+Math.sin(race.t*.38+4)*73-14];
 const place=1+rivals.filter(v=>v>race.progress).length;race.lastPlace=place;
 $("#hudPlace").textContent="🏆 "+place+" / 4";
 const lap=Math.min(3,Math.floor(race.progress/400)+1);
 $("#hudLap").textContent="🏁 LAP "+lap+" / 3";
 $("#boostBtn").classList.toggle("cooldown",race.cooldown>0);
 if(race.progress>=1200)finish();
}
function finish(){
 if(!race)return;const score=race.stars+Math.max(2,(5-race.lastPlace)*4);
 wallet+=score;save("tiny_wallet",wallet);
 $("#earnedStars").textContent=score;
 const tags=["🥇 1st place!","🥈 2nd place!","🥉 3rd place!","🌟 4th place!"];
 $("#resultPlace").textContent=tags[clamp(race.lastPlace-1,0,3)];
 $("#resultHeading").textContent=race.lastPlace===1?"🏆 Super star champion!":"🎉 Wonderful racing!";
 $("#resultSubheading").textContent="You finished all 3 laps in "+Math.floor(race.t)+" seconds!";
 beepsSuccess();race=null;show("results");
}
function beepsSuccess(){beep(740,.16);setTimeout(()=>beep(900,.17),110);setTimeout(()=>beep(1080,.2),230)}
function rr(ctx,x,y,w,h,r){r=Math.min(r,w/2,h/2);ctx.beginPath();ctx.moveTo(x+r,y);ctx.arcTo(x+w,y,x+w,y+h,r);ctx.arcTo(x+w,y+h,x,y+h,r);ctx.arcTo(x,y+h,x,y,r);ctx.arcTo(x,y,x+w,y,r);ctx.closePath()}
function fillRounded(ctx,x,y,w,h,r,color){ctx.fillStyle=color;rr(ctx,x,y,w,h,r);ctx.fill()}
function grad(ctx,x,y,w,h,c1,c2){const g=ctx.createLinearGradient(x,y,x,y+h);g.addColorStop(0,c1);g.addColorStop(1,c2);return g}
function circle(ctx,x,y,r,color){ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);ctx.fillStyle=color;ctx.fill()}
function ellipse(ctx,x,y,rx,ry,color){ctx.beginPath();ctx.ellipse(x,y,rx,ry,0,0,Math.PI*2);ctx.fillStyle=color;ctx.fill()}
function star(ctx,x,y,size,color="#ffe533",stroke="#ff9800"){ctx.save();ctx.translate(x,y);ctx.beginPath();for(let i=0;i<10;i++){const a=-Math.PI/2+i*Math.PI/5;const r=i%2?size*.48:size;const px=Math.cos(a)*r,py=Math.sin(a)*r;i?ctx.lineTo(px,py):ctx.moveTo(px,py)}ctx.closePath();ctx.fillStyle=color;ctx.fill();ctx.lineWidth=size*.13;ctx.strokeStyle=stroke;ctx.stroke();ctx.restore()}
function cloud(ctx,x,y,s=1){ctx.save();ctx.translate(x,y);ctx.scale(s,s);ellipse(ctx,0,13,76,26,"#e9fdff");circle(ctx,-36,-2,31,"#fff");circle(ctx,5,-19,44,"#fff");circle(ctx,47,0,32,"#fff");ellipse(ctx,0,16,77,22,"#fff");ctx.restore()}
function road(ctx,W,H,world,t=0,curve=0){
 const y0=H*.40;const col=world.road;
 ctx.fillStyle=world.ground;ctx.fillRect(0,y0,W,H-y0);
 // diagonal roadside stripes and perspective track
 for(let i=0;i<40;i++){
  const z0=i/40,z1=(i+1)/40,p0=z0*z0,p1=z1*z1;
  const yy0=y0+(H-y0)*p0,yy1=y0+(H-y0)*p1;
  const c0=W/2+curve*(1-p0)*120,c1=W/2+curve*(1-p1)*120;
  const w0=85+W*.43*p0,w1=85+W*.43*p1;
  ctx.beginPath();ctx.moveTo(c0-w0,yy0);ctx.lineTo(c0+w0,yy0);ctx.lineTo(c1+w1,yy1);ctx.lineTo(c1-w1,yy1);ctx.closePath();
  ctx.fillStyle=col;ctx.fill();
  // curb segments along sides
  const flip=(i+Math.floor(t/23))%4<2;
  ctx.strokeStyle=flip?"#ff5e61":"#fff";ctx.lineWidth=4+25*p1;ctx.beginPath();ctx.moveTo(c0-w0,yy0);ctx.lineTo(c1-w1,yy1);ctx.moveTo(c0+w0,yy0);ctx.lineTo(c1+w1,yy1);ctx.stroke();
  if((i+Math.floor(t/23))%6<3){ctx.strokeStyle="#fffceb";ctx.lineWidth=2+7*p1;for(let k=-1;k<=1;k+=2){ctx.beginPath();ctx.moveTo(c0+k*w0*.33,yy0);ctx.lineTo(c1+k*w1*.33,yy1);ctx.stroke()}}
 }
}
function scenery(ctx,W,H,world,t){
 const y=H*.40;const id=worlds.indexOf(world);
 // clouds & glowing sun
 circle(ctx,W*.82,H*.14,52,"#fff8b0");circle(ctx,W*.82,H*.14,39,"#ffe364");
 for(let i=0;i<4;i++)cloud(ctx,(W*(i*.31+.08)-t*1.8)%(W+250)-100,48+(i%2)*45,.5+(i%2)*.22);
 // hills
 for(let i=0;i<8;i++){ellipse(ctx,i*W/7-50,y+28,160,80,i%2?"#78d96a":"#92e68a")}
 if(id===0){ // toy city
   for(let i=0;i<13;i++){const h=60+(i*47)%93,x=i*100-30;fillRounded(ctx,x,y-h,67,h,6,["#ffb13f","#f878bc","#438ef5","#f5e352"][i%4]);fillRounded(ctx,x+16,y-h+19,16,16,3,"#fff4b0");fillRounded(ctx,x+43,y-h+19,14,16,3,"#fff4b0");}
 }else if(id===1){ // beach
   ctx.fillStyle="#30c6e7";ctx.fillRect(0,y-11,W,39);ctx.fillStyle="#ffe0a1";ctx.fillRect(0,y+20,W,27);
   for(let i=0;i<7;i++){const x=i*170+20;ctx.strokeStyle="#7b522e";ctx.lineWidth=9;ctx.beginPath();ctx.moveTo(x,y+22);ctx.lineTo(x+15,y-53);ctx.stroke();circle(ctx,x+18,y-65,24,"#37b86b");ellipse(ctx,x+35,y-64,32,12,"#40ce72");}
 }else if(id===2){ // candy
   for(let i=0;i<11;i++){const x=i*120+20;ctx.fillStyle=i%2?"#f4a8ed":"#fbd69a";ctx.beginPath();ctx.arc(x,y-8,45,Math.PI,Math.PI*2);ctx.lineTo(x+45,y+32);ctx.lineTo(x-45,y+32);ctx.fill();circle(ctx,x,y-63,19,["#ff448c","#e455f2","#53dbff"][i%3]);ctx.fillStyle="#fff";ctx.fillRect(x-3,y-44,6,53)}
 }else{
   for(let i=0;i<12;i++){const x=i*108;ellipse(ctx,x,y-17,33,45,i%2?"#3eae59":"#5ec46b");ellipse(ctx,x-25,y+8,46,24,"#379c54")}
   ctx.fillStyle="#aa9b73";ctx.beginPath();ctx.moveTo(W*.72,y-50);ctx.lineTo(W*.81,y-185);ctx.lineTo(W*.93,y-50);ctx.fill();
 }
 // pennants, lights, balloons
 for(let i=0;i<7;i++){const x=i*180+40,bob=Math.sin(t*.02+i)*4;circle(ctx,x,y+13+bob,6,"#fff");circle(ctx,x+15,y+4+bob,6,i%2?"#ff99b9":"#ffe75c")}
}
function car(ctx,x,y,s,col,tilt=0,character=0){
 ctx.save();ctx.translate(x,y);ctx.rotate(tilt);ctx.scale(s,s);
 ellipse(ctx,0,53,104,18,"#1d356b42");
 // tires
 fillRounded(ctx,-102,-4,37,79,14,"#26344d");fillRounded(ctx,65,-4,37,79,14,"#26344d");
 fillRounded(ctx,-95,14,25,36,10,"#61697c");fillRounded(ctx,70,14,25,36,10,"#61697c");
 // spoiler and body
 fillRounded(ctx,-85,-66,170,18,8,"#e6eaff");fillRounded(ctx,-84,-61,168,17,7,col);
 ctx.fillStyle=grad(ctx,-90,-45,180,112,"#ffffff",col);
 rr(ctx,-91,-45,182,110,40);ctx.fill();
 ctx.strokeStyle="#ffffffbb";ctx.lineWidth=5;ctx.stroke();
 // cabin shape
 ctx.fillStyle="#3a85cc";rr(ctx,-67,-78,134,81,38);ctx.fill();
 ctx.fillStyle=grad(ctx,-65,-72,132,70,"#cefcff","#7bc5ff");rr(ctx,-62,-71,124,63,34);ctx.fill();
 // eyes
 for(const e of [-26,26]){ellipse(ctx,e,-42,18,23,"#fff");ellipse(ctx,e+5,-37,9,15,"#163d83");circle(ctx,e+9,-44,4,"#fff")}
 // thick cartoon eyebrows
 ctx.strokeStyle="#1a326a";ctx.lineWidth=6;ctx.lineCap="round";for(const e of [-26,26]){ctx.beginPath();ctx.moveTo(e-12,-63);ctx.quadraticCurveTo(e,-72,e+12,-64);ctx.stroke()}
 // headlights
 ellipse(ctx,-70,22,19,15,"#fff5ab");ellipse(ctx,70,22,19,15,"#fff5ab");
 // bumper mouth
 ctx.fillStyle="#87263f";ctx.beginPath();ctx.ellipse(0,35,29,18,0,0,Math.PI);ctx.fill();
 ellipse(ctx,0,46,16,7,"#ff86a5");
 // cartoon sticker by car
 star(ctx,-51,13,character===0?16:11,"#fffacd","#ffbd32");
 if(character===2){circle(ctx,66,-76,13,"#ff70b4");circle(ctx,77,-85,11,"#ff8ac8")}
 if(character===3){fillRounded(ctx,-65,-86,44,14,7,"#ef9d38");circle(ctx,-48,-80,14,"#d5ffff")}
 if(character===1){circle(ctx,0,13,14,"#fff");star(ctx,0,13,10,"#83d7ff","#83d7ff")}
 ctx.restore();
}
function drawHero(){
 const c=$("#heroCanvas").getContext("2d"),W=1200,H=480;
 c.clearRect(0,0,W,H);c.fillStyle=grad(c,0,0,W,H,"#5ad4ff","#efffff");c.fillRect(0,0,W,H);
 scenery(c,W,H,worlds[0],performance.now()/80);
 road(c,W,H,worlds[0],performance.now()/80,-.25);
 // track arches
 c.lineWidth=17;c.strokeStyle="#fff";c.beginPath();c.arc(865,265,170,Math.PI,0);c.stroke();
 c.strokeStyle="#ff97d5";c.lineWidth=12;c.beginPath();c.arc(865,265,169,Math.PI,0);c.stroke();
 star(c,865,100,33);car(c,795,328,.87,"#2d8ff4",-.12,1);car(c,1086,340,.78,"#41c47b",.13,3);
 car(c,965,364,1.2,"#f73542",-.05,0);car(c,708,405,.65,"#ffd33f",-.09,2);
 for(let i=0;i<14;i++){const x=560+i*52+(Math.sin(i*3.1)*12),y=245+i%3*74;star(c,x,y,6+(i%3)*3,["#fff","#ffda4b","#ff9ed9"][i%3],"#fff")}
}
function drawGarage(){
 const c=$("#garageCanvas").getContext("2d"),W=750,H=430;c.clearRect(0,0,W,H);
 const g=grad(c,0,0,W,H,"#8ce6ff","#ffe6a1");c.fillStyle=g;c.fillRect(0,0,W,H);
 for(let i=0;i<9;i++)star(c,45+i*79,70+(i%4)*56,8+(i%3)*4);
 ellipse(c,375,362,254,35,"#0c84bb5c");ellipse(c,375,342,235,37,"#dfffff");ellipse(c,375,345,218,20,"#3aa4e9");
 car(c,375,257,1.9,carPaint[chosenCar],Math.sin(performance.now()/850)*.04,chosenCar);
}
function drawRace(){
 if(!race)return;const c=$("#raceCanvas").getContext("2d"),W=1200,H=640,w=worlds[race.world],p=race.progress,t=race.t;
 c.clearRect(0,0,W,H);c.fillStyle=grad(c,0,0,W,H,w.sky,"#f1ffff");c.fillRect(0,0,W,H);
 scenery(c,W,H,w,p*.9);road(c,W,H,w,p,Math.sin(p/200)*.55);
 // edge trees, flags, stars
 for(let i=0;i<8;i++){
  const phase=(i/8+p/140)%1,k=phase*phase,y=H*.40+k*H*.65,xx=600+(280+440*k);
  if(i%2){circle(c,xx,y-50*k,7+25*k,"#56bd69");fillRounded(c,xx-3-6*k,y-10,7+10*k,40*k,3,"#ae7853");}
  else{c.font=(20+k*25)+"px sans-serif";c.textAlign="center";c.fillText("🏁",xx,y)}
 }
 // pickups moving in oncoming perspective
 for(let j=0;j<5;j++){
   const index=race.nextStar+j,target=80+index*112,dist=target-p;
   if(dist>0 && dist<240){
    const depth=1-dist/240,z=depth*depth;
    const lane=Math.sin(index*2.6)*.65;
    const center=W/2+Math.sin(p/200)*.55*(1-z)*120;
    const x=center+lane*(84+W*.39*z),y=H*.40+z*H*.55;
    star(c,x,y,11+19*z,"#ffe648","#ff9d18");
   }
 }
 // opponents placed in lanes, float slightly
 const lanes=[-.6,.05,.65],colors=["#2d8ff4","#ffd33f","#41c47b"];
 for(let i=0;i<3;i++){
    const bob=Math.sin(t*.9+i*2.6);
    const yy=328+(i%2)*66+bob*15;
    const xx=600+lanes[i]*(100+(yy/640)*230)+Math.sin(p/180)*45;
    car(c,xx,yy,.55+yy/1600,colors[i],Math.sin(t+i)*.05,i+1);
 }
 // player behind, bounces and sparkles when turbo
 const x=600+race.lane*330;
 ellipse(c,x,558,134,28,"#091d4c44");
 car(c,x,504,1.3,carPaint[race.car],(heldRight?1:heldLeft?-1:0)*.07,race.car);
 if(race.boost>0){for(let i=0;i<9;i++)star(c,x+(i-4)*31,625+(i%2)*18,4+(i%3)*4,"#ffffa0","#ffa324")}
 const pbar=clamp(p/1200,0,1);
 fillRounded(c,390,18,418,16,8,"#ffffff");fillRounded(c,394,22,410*pbar,8,4,"#35d775");
 if(race.shake>0)race.shake=Math.max(0,race.shake-.016);
}
let last=0;
function loop(ts){
 const dt=clamp((ts-last)/1000||.016,0,.06);last=ts;
 if(current==="home")drawHero();else if(current==="garage")drawGarage();
 else if(current==="race"){updateRace(dt);drawRace()}
 requestAnimationFrame(loop);
}
coins();renderWorlds();renderGarageUi();requestAnimationFrame(loop);
