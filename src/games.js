/* RibhLab browser games. Local-only chess and five-letter word puzzle. */
const chessStartFen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
const glyph={K:"♔",Q:"♕",R:"♖",B:"♗",N:"♘",P:"♙",k:"♚",q:"♛",r:"♜",b:"♝",n:"♞",p:"\u265F\uFE0E",".":""};
const dirs={n:[-33,-31,-18,-14,14,18,31,33],b:[-17,-15,15,17],r:[-16,-1,1,16],k:[-17,-16,-15,-1,1,15,16,17]};
const on=i=>i>=0&&i<128&&!(i&0x88);
const side=p=>!p||p==="."?0:p===p.toUpperCase()?1:-1;
const sq=i=>"abcdefgh"[i&7]+(8-(i>>4));
const index=s=>(8-Number(s[1]))*16+"abcdefgh".indexOf(s[0]);
const key=m=>sq(m[0])+sq(m[1])+m[2];
function parseFen(fen){
 const f=fen.trim().split(/\s+/),rows=f[0].split("/"),b=Array(128).fill(".");
 if(rows.length!==8||!/^[wb]$/.test(f[1])||!/^(?:-|K?Q?k?q?)$/.test(f[2])||!/^(?:-|[a-h][36])$/.test(f[3]))throw Error("Invalid chess FEN");
 rows.forEach((row,r)=>{let col=0;for(const p of row){if(/^[1-8]$/.test(p))col+=Number(p);else{if(!/^[prnbqkPRNBQK]$/.test(p)||col>=8)throw Error("Invalid rank");b[r*16+col++]=p;}}if(col!==8)throw Error("Invalid rank width");});
 if(b.filter(p=>p==="K").length!==1||b.filter(p=>p==="k").length!==1)throw Error("Missing king");
 const c=(f[2].includes("K")?1:0)|(f[2].includes("Q")?2:0)|(f[2].includes("k")?4:0)|(f[2].includes("q")?8:0);
 return{b,t:f[1]==="w"?1:-1,c,ep:f[3]==="-"?-1:index(f[3]),half:Number(f[4]||0),full:Number(f[5]||1)};
}
function attacked(s,target,by){
 for(let f=0;f<128;f++){
  if(!on(f)||side(s.b[f])!==by)continue;
  const p=s.b[f].toLowerCase();
  if(p==="p"){if(target===f-16*by-1||target===f-16*by+1)return true;continue;}
  for(const d of(dirs[p]||dirs.k)){
   for(let t=f+d;on(t);t+=d){
    if(t===target)return true;
    if(s.b[t]!=="."||p==="n"||p==="k")break;
   }
  }
 }
 return false;
}
const checked=(s,color=s.t)=>attacked(s,s.b.indexOf(color===1?"K":"k"),-color);
function apply(s,m){
 const[f,t,promo,flag]=m,b=s.b.slice(),piece=b[f],captured=b[t];let c=s.c;
 b[f]=".";b[t]=promo?(s.t===1?promo.toUpperCase():promo):piece;
 if(flag==="ep")b[t+16*s.t]=".";
 if(flag==="castle"){const rf=t>f?f+3:f-4,rt=t>f?f+1:f-1;b[rt]=b[rf];b[rf]=".";}
 if(piece==="K")c&=~3;
 if(piece==="k")c&=~12;
 const rookBit={119:1,112:2,7:4,0:8};
 if(piece.toLowerCase()==="r")c&=~(rookBit[f]||0);
 if(captured.toLowerCase()==="r")c&=~(rookBit[t]||0);
 return{b,t:-s.t,c,ep:piece.toLowerCase()==="p"&&Math.abs(t-f)===32?(t+f)/2:-1,half:piece.toLowerCase()==="p"||captured!=="."||flag==="ep"?0:s.half+1,full:s.full+(s.t===-1?1:0)};
}
function pseudo(s){
 const out=[];
 for(let f=0;f<128;f++){
  if(!on(f)||side(s.b[f])!==s.t)continue;
  const p=s.b[f].toLowerCase();
  const add=(t,flag="")=>{
   if(s.b[t].toLowerCase()==="k")return;
   if(p==="p"&&((t>>4)===0||(t>>4)===7))for(const q of["q","r","b","n"])out.push([f,t,q,flag]);
   else out.push([f,t,"",flag]);
  };
  if(p==="p"){
   const t=f-16*s.t;
   if(on(t)&&s.b[t]==="."){add(t);const u=t-16*s.t;if((f>>4)===(s.t===1?6:1)&&s.b[u]===".")add(u);}
   for(const d of[-1,1]){const u=t+d;if(!on(u))continue;if(side(s.b[u])===-s.t)add(u);else if(u===s.ep&&s.b[u]==="."&&s.b[u+16*s.t]===(s.t===1?"p":"P"))add(u,"ep");}
  }else{
   for(const d of(dirs[p]||dirs.k)){
    for(let t=f+d;on(t);t+=d){if(side(s.b[t])===s.t)break;add(t);if(s.b[t]!=="."||p==="n"||p==="k")break;}
   }
   const home=s.t===1?116:4,rook=s.t===1?"R":"r",bits=s.t===1?[1,2]:[4,8];
   if(p==="k"&&f===home&&!checked(s)){
    if((s.c&bits[0])&&s.b[f+3]===rook&&s.b[f+1]==="."&&s.b[f+2]==="."&&!attacked(s,f+1,-s.t)&&!attacked(s,f+2,-s.t))add(f+2,"castle");
    if((s.c&bits[1])&&s.b[f-4]===rook&&s.b[f-1]==="."&&s.b[f-2]==="."&&s.b[f-3]==="."&&!attacked(s,f-1,-s.t)&&!attacked(s,f-2,-s.t))add(f-2,"castle");
   }
  }
 }
 return out;
}
const legal=s=>pseudo(s).filter(m=>!checked(apply(s,m),s.t));
function san(s,m){
 const[f,t,promo,flag]=m,p=s.b[f].toUpperCase(),capture=s.b[t]!=="."||flag==="ep";let v="";
 if(flag==="castle")v=t>f?"O-O":"O-O-O";
 else{
  if(p!=="P"){
   v=p;const other=legal(s).filter(x=>x[0]!==f&&x[1]===t&&s.b[x[0]]===s.b[f]);
   if(other.length)v+=!other.some(x=>(x[0]&7)===(f&7))?sq(f)[0]:!other.some(x=>(x[0]>>4)===(f>>4))?sq(f)[1]:sq(f);
  }else if(capture)v=sq(f)[0];
  v+=(capture?"x":"")+sq(t)+(promo?"="+promo.toUpperCase():"");
 }
 const next=apply(s,m);return v+(checked(next)?legal(next).length?"+":"#":"");
}
const moveLabel=(s,m)=>s.full+(s.t===1?". ":"... ")+san(s,m);
function positionKey(s){
 const epMove=s.ep>=0&&legal(s).some(m=>m[3]==="ep");
 return s.b.join("")+":"+s.t+":"+s.c+":"+(epMove?s.ep:-1);
}
function insufficient(s){
 const pcs=[];for(let i=0;i<128;i++)if(on(i)&&s.b[i]!=="."&&s.b[i].toLowerCase()!=="k")pcs.push([s.b[i].toLowerCase(),((i>>4)+(i&7))%2]);
 return pcs.length===0||(pcs.length===1&&["b","n"].includes(pcs[0][0]))||(pcs.every(p=>p[0]==="b")&&new Set(pcs.map(p=>p[1])).size===1);
}
function gameStatus(history){
 const s=history[history.length-1],moves=legal(s),check=checked(s),k=positionKey(s),repeats=history.filter(x=>positionKey(x)===k).length;
 if(!moves.length)return{done:true,kind:check?"checkmate":"stalemate",winner:check?-s.t:0,claim:"",check};
 if(insufficient(s))return{done:true,kind:"insufficient",winner:0,claim:"",check};
 if(s.half>=150||repeats>=5)return{done:true,kind:s.half>=150?"seventyfive":"repetition",winner:0,claim:"",check};
 return{done:false,kind:"",winner:0,claim:repeats>=3?"repetition":s.half>=100?"fifty":"",check};
}
const words={
 ar:[["مدرسة","مكان الدراسة"],["حديقة","مكان تنمو فيه النباتات"],["مكتبة","مكان الكتب"],["سفينة","تسافر فوق الماء"],["نافذة","تدخل منها أشعة الشمس"],["مدينة","أكبر من قرية"],["حقيبة","نحمل فيها أغراضنا"],["سيارة","وسيلة نقل على الطريق"],["زرافة","حيوان برقبة طويلة"],["طاولة","نضع عليها الأشياء"]],
 en:[["apple","A familiar fruit"],["grape","Small fruit in bunches"],["train","Rail transport"],["chess","Board game with kings"],["bread","Baked staple food"],["plant","Living thing that grows"],["water","Clear liquid to drink"],["light","Makes a room bright"],["beach","Sand beside the sea"],["music","Melody and rhythm"]],
 fr:[["livre","On le lit"],["porte","On la franchit pour entrer"],["table","Meuble pour les repas"],["plage","Bord de mer sableux"],["fleur","Elle peut pousser dans un jardin"],["monde","La planète et ses habitants"],["route","Les véhicules y circulent"],["pomme","Fruit croquant"],["sucre","Ingrédient au goût doux"],["chien","Animal domestique qui aboie"]]
};
const short={
 ar:{white:"الأبيض",black:"الأسود",move:"دوره",check:"كش",mate:"كش مات",stalemate:"تعادل بالتوقف",insufficient:"تعادل: قطع غير كافية",repetition:"تعادل بالتكرار",fifty:"تعادل بقاعدة 50 نقلة",seventyfive:"تعادل بقاعدة 75 نقلة",illegal:"نقلة غير مسموحة",wins:"فاز",claimed:"تم إعلان التعادل",tries:"المحاولة",hint:"تلميح",invalid:"أدخل كلمة من خمسة أحرف",won:"أحسنت! اكتشفت الكلمة.",lost:"انتهت المحاولات. الكلمة: ",promote:{q:"وزير",r:"قلعة",b:"فيل",n:"حصان"}},
 en:{white:"White",black:"Black",move:"to move",check:"Check",mate:"Checkmate",stalemate:"Stalemate",insufficient:"Draw: insufficient material",repetition:"Draw by repetition",fifty:"Draw by 50-move rule",seventyfive:"Draw by 75-move rule",illegal:"Illegal move",wins:"wins",claimed:"Draw claimed",tries:"Attempt",hint:"Clue",invalid:"Type exactly five letters",won:"Well done! You found the word.",lost:"No attempts left. The word was: ",promote:{q:"Queen",r:"Rook",b:"Bishop",n:"Knight"}},
 fr:{white:"Blancs",black:"Noirs",move:"jouent",check:"Échec",mate:"Échec et mat",stalemate:"Pat",insufficient:"Nulle : matériel insuffisant",repetition:"Nulle par répétition",fifty:"Nulle : règle des 50 coups",seventyfive:"Nulle : règle des 75 coups",illegal:"Coup illégal",wins:"gagnent",claimed:"Nulle réclamée",tries:"Essai",hint:"Indice",invalid:"Saisissez exactement cinq lettres",won:"Bravo ! Mot trouvé.",lost:"Plus d'essais. Le mot était : ",promote:{q:"Dame",r:"Tour",b:"Fou",n:"Cavalier"}}
};
function initChess(root){
 const lang=root.dataset.lang||"ar",t=short[lang],board=root.querySelector("#chess-board"),statusEl=root.querySelector("#chess-status"),list=root.querySelector("#chess-moves"),mode=root.querySelector("#chess-mode"),claim=root.querySelector("#chess-claim"),back=root.querySelector("#chess-back"),promoBox=root.querySelector("#chess-promotion"),promoOptions=root.querySelector("#chess-promotion-options"),claimText=root.querySelector("#chess-claim");
 let history=[parseFen(chessStartFen)],labels=[],selected=-1,pending=[],claimed=false,notification="",serial=0;
 const state=()=>history[history.length-1];
 const selection=()=>legal(state()).filter(m=>m[0]===selected);
 const botTurn=()=>mode.value==="computer"&&state().t===-1;
 function status(){
  const z=gameStatus(history);if(claimed)return t.claimed;
  if(z.done){if(z.kind==="checkmate")return t.mate+" — "+(z.winner===1?t.white:t.black)+" "+t.wins;return t[z.kind]||z.kind;}
  return (state().t===1?t.white:t.black)+" "+t.move+(z.check?" · "+t.check:"");
 }
 function redraw(){
  const s=state(),valid=legal(s),canPlay=!gameStatus(history).done&&!claimed&&!pending.length&&!botTurn(),targets=selection().map(m=>m[1]);
  board.replaceChildren();
  for(let r=0;r<8;r++)for(let c=0;c<8;c++){
   const i=r*16+c,p=s.b[i],button=document.createElement("button");
   button.type="button";button.className="chess-square "+(((r+c)%2)?"dark":"light");
   if(i===selected)button.classList.add("selected");
   if(targets.includes(i))button.classList.add("target");
   button.dataset.square=String(i);button.textContent=glyph[p];
   button.setAttribute("aria-label",sq(i)+" "+(p==="."?"empty":p));
   button.title=sq(i);button.disabled=!canPlay;
   if(c===0){const n=document.createElement("span");n.className="chess-rank";n.textContent=String(8-r);button.append(n);}
   if(r===7){const n=document.createElement("span");n.className="chess-file";n.textContent="abcdefgh"[c];button.append(n);}
   board.append(button);
  }
  statusEl.textContent=notification||status();
  list.replaceChildren();labels.forEach(x=>{const li=document.createElement("li");li.textContent=x;list.append(li);});list.scrollTop=list.scrollHeight;
  back.disabled=history.length===1;claim.hidden=!gameStatus(history).claim||claimed;claimText.textContent=gameStatus(history).claim==="fifty"?t.fifty:t.repetition;
  promoBox.hidden=!pending.length;
  promoOptions.replaceChildren();
  if(pending.length)for(const m of pending){const b=document.createElement("button");b.type="button";b.textContent=t.promote[m[2]];b.addEventListener("click",()=>play(m));promoOptions.append(b);}
 }
 function play(m){
  const s=state(),actual=legal(s).find(x=>key(x)===key(m));if(!actual)return;
  labels.push(moveLabel(s,actual));history.push(apply(s,actual));pending=[];selected=-1;notification="";redraw();
  if(botTurn()&&!gameStatus(history).done)queueBot();
 }
 function queueBot(){
  const id=++serial;window.setTimeout(()=>{
   if(id!==serial||!botTurn()||pending.length||gameStatus(history).done||claimed)return;
   const s=state(),moves=legal(s),values={p:1,n:3,b:3.1,r:5,q:9,k:0};
   if(!moves.length)return;let best=moves[0],bestScore=-Infinity;
   for(const m of moves){
    const next=apply(s,m),victim=m[3]==="ep"?"p":s.b[m[1]].toLowerCase(),pos=m[1],center=4-Math.abs((pos&7)-3.5)-Math.abs((pos>>4)-3.5);
    let score=(values[victim]||0)*14+center*.12;
    if(m[2])score+=(values[m[2]]||0)*10;
    if(m[3]==="castle")score+=2;
    if(checked(next))score+=1.5;
    if(!legal(next).length&&checked(next))score+=1000;
    if(legal(next).some(reply=>reply[1]===m[1]&&s.b[m[0]].toLowerCase()!=="k"))score-=(values[s.b[m[0]].toLowerCase()]||0)*8;
    score+=Math.random()*.4;
    if(score>bestScore){bestScore=score;best=m;}
   }
   play(best);
  },360);
 }
 board.addEventListener("click",e=>{
  const btn=e.target.closest("button[data-square]");if(!btn||btn.disabled)return;
  const s=state(),i=Number(btn.dataset.square);
  if(side(s.b[i])===s.t){selected=selected===i?-1:i;pending=[];notification="";redraw();return;}
  const choices=selection().filter(m=>m[1]===i);
  if(choices.length>1){pending=choices;notification="";redraw();}
  else if(choices.length===1)play(choices[0]);
  else{notification=t.illegal;redraw();}
 });
 function restart(){serial++;history=[parseFen(chessStartFen)];labels=[];selected=-1;pending=[];claimed=false;notification="";redraw();}
 root.querySelector("#chess-new").addEventListener("click",restart);
 mode.addEventListener("change",restart);
 back.addEventListener("click",()=>{
  serial++;if(history.length<=1)return;
  const howMany=mode.value==="computer"&&history.length>=3&&state().t===1?2:1;
  history.splice(-howMany);labels.splice(-howMany);selected=-1;pending=[];claimed=false;notification="";redraw();
  if(botTurn())queueBot();
 });
 root.querySelector("#chess-promotion-cancel").addEventListener("click",()=>{pending=[];redraw();});
 claim.addEventListener("click",()=>{if(gameStatus(history).claim){serial++;claimed=true;redraw();}});
 redraw();
}
function markGuess(guess,answer){
 const g=Array.from(guess),a=Array.from(answer),res=Array(5).fill("absent"),remain={};
 for(let i=0;i<5;i++)if(g[i]===a[i])res[i]="correct";else remain[a[i]]=(remain[a[i]]||0)+1;
 for(let i=0;i<5;i++)if(res[i]!=="correct"&&remain[g[i]]>0){res[i]="present";remain[g[i]]--;}
 return res;
}
function initWords(root){
 const lang=root.dataset.lang||"ar",t=short[lang],entries=words[lang],grid=root.querySelector("#word-grid"),input=root.querySelector("#word-input"),statusEl=root.querySelector("#word-status"),count=root.querySelector("#word-count"),clue=root.querySelector("#word-clue"),form=root.querySelector("#word-form");
 let answer="",hint="",attempts=[],done=false,last=-1;
 function next(){
  let i=Math.floor(Math.random()*entries.length);if(entries.length>1&&i===last)i=(i+1)%entries.length;last=i;[answer,hint]=entries[i];attempts=[];done=false;input.value="";input.disabled=false;form.querySelector("button").disabled=false;statusEl.textContent="";paint();input.focus();
 }
 function paint(){
  grid.replaceChildren();
  for(let r=0;r<6;r++){
   const entry=attempts[r],marks=entry?markGuess(entry,answer):[],letters=entry?Array.from(entry):[];
   const line=document.createElement("div");line.className="word-row";
   for(let c=0;c<5;c++){const cell=document.createElement("span");cell.className="tile "+(marks[c]||"");cell.textContent=letters[c]||"";cell.setAttribute("aria-label",(r+1)+":"+(c+1)+" "+(marks[c]||"empty"));line.append(cell);}grid.append(line);
  }
  count.textContent=t.tries+" "+(attempts.length+(!done?1:0))+" / 6";
  clue.textContent=t.hint+": "+hint;
 }
 function submit(e){
  e.preventDefault();if(done)return;
  let guess=input.value.trim().toLocaleLowerCase(lang).normalize("NFC");guess=guess.replace(/\s/g,"");
  if(lang==="ar"){guess=guess.replace(/[\u064B-\u065F\u0670]/g,"").replace(/[أإآ]/g,"ا");}
  if(Array.from(guess).length!==5||(lang==="ar"?!/^[\u0621-\u064A\u0671-\u06D3]{5}$/u.test(guess):!/^[a-z]{5}$/.test(guess))){statusEl.textContent=t.invalid;return;}
  attempts.push(guess);input.value="";
  if(guess===answer){done=true;statusEl.textContent=t.won;}
  else if(attempts.length>=6){done=true;statusEl.textContent=t.lost+answer;}
  else statusEl.textContent="";
  if(done){input.disabled=true;form.querySelector("button").disabled=true;}
  paint();
 }
 form.addEventListener("submit",submit);
 root.querySelector("#word-new").addEventListener("click",next);
 next();
}
if(typeof document!=="undefined"){
 const root=document.querySelector("[data-ribhlab-game]");
 if(root){if(root.dataset.ribhlabGame==="chess")initChess(root);else if(root.dataset.ribhlabGame==="words")initWords(root);}
}
export{parseFen,apply,legal,checked,san,gameStatus,moveLabel,index,markGuess,chessStartFen};
