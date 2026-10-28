/* RibhLab legal chess, with local and peer-to-peer online multiplayer. */
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
const short={
 ar:{white:"الأبيض",black:"الأسود",move:"دوره",check:"كش",mate:"كش مات",stalemate:"تعادل بالتوقف",insufficient:"تعادل: قطع غير كافية",repetition:"تعادل بالتكرار",fifty:"تعادل بقاعدة 50 نقلة",seventyfive:"تعادل بقاعدة 75 نقلة",illegal:"نقلة غير مسموحة",wins:"فاز",claimed:"تم إعلان التعادل",tries:"المحاولة",hint:"تلميح",invalid:"أدخل كلمة من خمسة أحرف",won:"أحسنت! اكتشفت الكلمة.",lost:"انتهت المحاولات. الكلمة: ",promote:{q:"وزير",r:"قلعة",b:"فيل",n:"حصان"}},
 en:{white:"White",black:"Black",move:"to move",check:"Check",mate:"Checkmate",stalemate:"Stalemate",insufficient:"Draw: insufficient material",repetition:"Draw by repetition",fifty:"Draw by 50-move rule",seventyfive:"Draw by 75-move rule",illegal:"Illegal move",wins:"wins",claimed:"Draw claimed",tries:"Attempt",hint:"Clue",invalid:"Type exactly five letters",won:"Well done! You found the word.",lost:"No attempts left. The word was: ",promote:{q:"Queen",r:"Rook",b:"Bishop",n:"Knight"}},
 fr:{white:"Blancs",black:"Noirs",move:"jouent",check:"Échec",mate:"Échec et mat",stalemate:"Pat",insufficient:"Nulle : matériel insuffisant",repetition:"Nulle par répétition",fifty:"Nulle : règle des 50 coups",seventyfive:"Nulle : règle des 75 coups",illegal:"Coup illégal",wins:"gagnent",claimed:"Nulle réclamée",tries:"Essai",hint:"Indice",invalid:"Saisissez exactement cinq lettres",won:"Bravo ! Mot trouvé.",lost:"Plus d'essais. Le mot était : ",promote:{q:"Dame",r:"Tour",b:"Fou",n:"Cavalier"}}
};

const onlineText={
 ar:{idle:'يمكنك إنشاء غرفة أو الانضمام إلى غرفة صديقك.',loading:'جارٍ فتح الاتصال بالشطرنج الأونلاين…',hosting:'الغرفة جاهزة. شارك الرابط وانتظر اللاعب الأسود.',joining:'جارٍ الاتصال بغرفة صديقك…',ready:'متصل: الأبيض صاحب الغرفة والأسود الضيف. العب عندما يحين دورك.',waiting:'في انتظار تأكيد النقلة…',closed:'انقطع اتصال المنافس. أعد الانضمام أو أنشئ غرفة جديدة.',error:'تعذر الاتصال عبر هذه الشبكة. جرّب شبكة أخرى أو اللعب المحلي.',invalid:'رمز الغرفة غير صحيح. استعمل الرمز المكوّن من 12 حرفاً أو رقماً.',full:'هذه الغرفة مشغولة بلاعب آخر.',copied:'تم نسخ رابط الدعوة.',copyFailed:'انسخ الرابط يدوياً من شريط العنوان.',guest:'الضيف يتحكم في الأسود فقط.',host:'صاحب الغرفة يتحكم في الأبيض فقط.',noReset:'الضيف لا يستطيع إعادة المباراة؛ اطلب من صاحب الغرفة ذلك.'},
 en:{idle:'Create a private room or join a friend.',loading:'Opening the online chess connection…',hosting:'Room ready. Share the link and wait for the Black player.',joining:'Connecting to your friend’s room…',ready:'Connected: the host plays White, the guest Black. Wait for your turn.',waiting:'Waiting for move confirmation…',closed:'Opponent disconnected. Rejoin or create a new room.',error:'Peer connection unavailable on this network. Try another network or local play.',invalid:'Invalid room code. Use the 12-character code.',full:'This room already has a guest.',copied:'Invite link copied.',copyFailed:'Copy the room link manually from the address bar.',guest:'Guests control Black only.',host:'Hosts control White only.',noReset:'Only the host can restart the online game.'},
 fr:{idle:'Créez une salle privée ou rejoignez un ami.',loading:'Ouverture de la connexion en ligne…',hosting:'Salle prête. Partagez le lien et attendez le joueur noir.',joining:'Connexion à la salle de votre ami…',ready:'Connecté : l’hôte joue les Blancs, l’invité les Noirs.',waiting:'En attente de confirmation du coup…',closed:'L’adversaire s’est déconnecté. Rejoignez ou recréez une salle.',error:'Connexion pair à pair impossible sur ce réseau. Essayez un autre réseau.',invalid:'Code de salle incorrect : 12 caractères requis.',full:'Cette salle a déjà un invité.',copied:'Lien d’invitation copié.',copyFailed:'Copiez le lien dans la barre d’adresse.',guest:'L’invité joue uniquement les Noirs.',host:'L’hôte joue uniquement les Blancs.',noReset:'Seul l’hôte peut recommencer.'}
};
let peerScriptPromise=null;
function loadPeerJS(){
 if(typeof window==='undefined')return Promise.reject(Error('Browser required'));
 if(window.Peer)return Promise.resolve(window.Peer);
 if(peerScriptPromise)return peerScriptPromise;
 peerScriptPromise=new Promise((resolve,reject)=>{
  const src='https://cdn.jsdelivr.net/npm/peerjs@1.5.5/dist/peerjs.min.js';
  const script=document.createElement('script');script.src=src;script.async=true;script.crossOrigin='anonymous';
  const timeout=setTimeout(()=>{script.remove();reject(Error('PeerJS loading timed out'));},12000);
  script.onload=()=>{clearTimeout(timeout);if(window.Peer)resolve(window.Peer);else reject(Error('PeerJS unavailable'))};
  script.onerror=()=>{clearTimeout(timeout);reject(Error('PeerJS library blocked'))};
  document.head.append(script);
 }).catch(e=>{peerScriptPromise=null;throw e});
 return peerScriptPromise;
}
const onlineRoomId=code=>'ribhlab-chess-v1-'+code.toLowerCase();
function validRoom(code){return /^[A-Z0-9]{12}$/.test(code);}
function randomRoomCode(){
 const bytes=new Uint8Array(12);window.crypto.getRandomValues(bytes);
 const abc='ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
 return Array.from(bytes,x=>abc[x%abc.length]).join('');
}
function initChess(root){
 const lang=root.dataset.lang||"ar",t=short[lang],board=root.querySelector("#chess-board"),statusEl=root.querySelector("#chess-status"),list=root.querySelector("#chess-moves"),mode=root.querySelector("#chess-mode"),claim=root.querySelector("#chess-claim"),back=root.querySelector("#chess-back"),promoBox=root.querySelector("#chess-promotion"),promoOptions=root.querySelector("#chess-promotion-options"),claimText=root.querySelector("#chess-claim");
 let history=[parseFen(chessStartFen)],labels=[],uciHistory=[],selected=-1,pending=[],claimed=false,notification="",serial=0;
 const onlinePanel=root.querySelector('#chess-online'),onlineStatus=root.querySelector('#chess-online-status'),roomInput=root.querySelector('#chess-room'),createButton=root.querySelector('#chess-create'),joinButton=root.querySelector('#chess-join'),copyButton=root.querySelector('#chess-copy'),leaveButton=root.querySelector('#chess-leave'),newButton=root.querySelector('#chess-new');
 const otext=onlineText[lang],net={peer:null,conn:null,room:'',role:'',connected:false,awaiting:false,serial:0};
 function netNotice(message){if(onlineStatus)onlineStatus.textContent=message;}
 function stopOnline(message=''){
  net.serial++;net.conn?.close();net.peer?.destroy();
  net.peer=null;net.conn=null;net.connected=false;net.awaiting=false;net.room='';net.role='';
  if(copyButton)copyButton.hidden=true;if(leaveButton)leaveButton.hidden=true;
  if(message)netNotice(message);
 }
 function send(data){if(net.conn?.open){try{net.conn.send(data);return true}catch{}}return false;}
 function publishState(){if(net.role==='host'&&net.connected)send({type:'state',moves:uciHistory.slice(),claimed});}
 function acceptState(data){
  if(!Array.isArray(data.moves)||data.moves.length>500||data.moves.some(x=>typeof x!=='string'||!/^[a-h][1-8][a-h][1-8][qrbn]?$/.test(x)))return;
  let h=[parseFen(chessStartFen)],labelsNext=[],uciNext=[];
  for(const uci of data.moves){
   const start=h[h.length-1],move=legal(start).find(m=>key(m)===uci);
   if(!move)return;labelsNext.push(moveLabel(start,move));h.push(apply(start,move));uciNext.push(uci);
  }
  serial++;history=h;labels=labelsNext;uciHistory=uciNext;selected=-1;pending=[];claimed=data.claimed===true&&!!gameStatus(history).claim;net.awaiting=false;notification='';redraw();
 }
 function connectLine(conn,role,id){
  const session=net.serial;net.conn=conn;net.role=role;
  conn.on('open',()=>{
   if(session!==net.serial)return;
   net.connected=true;net.awaiting=false;netNotice(otext.ready);
   if(role==='host')publishState();redraw();
  });
  conn.on('data',data=>{
   if(session!==net.serial||!data||typeof data!=='object')return;
   if(role==='guest'){
    if(data.type==='state')acceptState(data);
    else if(data.type==='full')netNotice(otext.full);
    return;
   }
   if(data.type==='move'){
    if(state().t!==-1||!Number.isInteger(data.ply)||data.ply!==uciHistory.length){publishState();return;}
    const found=typeof data.uci==='string'?legal(state()).find(m=>key(m)===data.uci):null;
    if(found)play(found,true);else publishState();
   }else if(data.type==='claim'&&gameStatus(history).claim){claimed=true;publishState();redraw();}
   else if(data.type==='sync')publishState();
  });
  conn.on('close',()=>{
   if(session!==net.serial)return;
   net.connected=false;net.awaiting=false;net.conn=null;
   netNotice(otext.closed);redraw();
  });
  conn.on('error',()=>{if(session===net.serial){netNotice(otext.error);redraw();}});
 }
 async function openOnline(role,room){
  stopOnline();if(!validRoom(room)){netNotice(otext.invalid);return;}
  net.room=room;net.role=role;netNotice(otext.loading);
  const session=net.serial;
  try{
   const Peer=await loadPeerJS();if(session!==net.serial||mode.value!=='online')return;
   const peer=role==='host'?new Peer(onlineRoomId(room),{host:'0.peerjs.com',port:443,secure:true,debug:0}):new Peer({host:'0.peerjs.com',port:443,secure:true,debug:0});
   net.peer=peer;
   peer.on('error',()=>{if(session===net.serial){netNotice(otext.error);redraw();}});
   peer.on('disconnected',()=>{if(session===net.serial&&!net.connected)netNotice(otext.closed);});
   peer.on('open',()=>{
    if(session!==net.serial)return;
    if(role==='host'){
     netNotice(otext.hosting);
     const url=new URL(window.location.href);url.searchParams.set('room',room);window.history.replaceState(null,'',url.pathname+url.search);
     copyButton.hidden=false;leaveButton.hidden=false;redraw();
    }else{
     netNotice(otext.joining);const conn=peer.connect(onlineRoomId(room),{reliable:true,serialization:'json'});
     connectLine(conn,'guest',session);leaveButton.hidden=false;
    }
   });
   if(role==='host')peer.on('connection',conn=>{
    if(session!==net.serial){conn.close();return;}
    if(net.connected||net.conn){conn.on('open',()=>{conn.send({type:'full'});conn.close();});return;}
    connectLine(conn,'host',session);
   });
   if(role==='host'){resetGame(false);}
  }catch{if(session===net.serial){stopOnline(otext.error);redraw();}}
 }
 function resetGame(broadcast=true){
  serial++;history=[parseFen(chessStartFen)];labels=[];uciHistory=[];selected=-1;pending=[];claimed=false;notification='';net.awaiting=false;redraw();
  if(broadcast)publishState();
 }

 const state=()=>history[history.length-1];
 const selection=()=>legal(state()).filter(m=>m[0]===selected);
 const botTurn=()=>mode.value==="computer"&&state().t===-1;
 const peerTurn=()=>mode.value==='online'&&(!net.connected||net.awaiting||state().t!==(net.role==='host'?1:-1));
 function status(){
  const z=gameStatus(history);if(claimed)return t.claimed;
  if(z.done){if(z.kind==="checkmate")return t.mate+" — "+(z.winner===1?t.white:t.black)+" "+t.wins;return t[z.kind]||z.kind;}
  return (state().t===1?t.white:t.black)+" "+t.move+(z.check?" · "+t.check:"");
 }
 function redraw(){
  const s=state(),valid=legal(s),canPlay=!gameStatus(history).done&&!claimed&&!pending.length&&!botTurn()&&!peerTurn(),targets=selection().map(m=>m[1]);
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
  back.disabled=history.length===1||mode.value==='online';
  newButton.disabled=mode.value==='online'&&net.role==='guest';
  claim.hidden=!gameStatus(history).claim||claimed||(mode.value==='online'&&!net.connected);claimText.textContent=gameStatus(history).claim==="fifty"?t.fifty:t.repetition;
  promoBox.hidden=!pending.length;
  promoOptions.replaceChildren();
  if(pending.length)for(const m of pending){const b=document.createElement("button");b.type="button";b.textContent=t.promote[m[2]];b.addEventListener("click",()=>play(m));promoOptions.append(b);}
 }
 function play(m,remote=false){
  const s=state(),actual=legal(s).find(x=>key(x)===key(m));if(!actual)return;
  if(mode.value==='online'&&!remote){
   if(!net.connected||s.t!==(net.role==='host'?1:-1)||net.awaiting)return;
   if(net.role==='guest'){
    net.awaiting=true;selected=-1;pending=[];notification=otext.waiting;
    if(!send({type:'move',ply:uciHistory.length,uci:key(actual)})){net.awaiting=false;notification=otext.closed;}
    redraw();return;
   }
  }
  labels.push(moveLabel(s,actual));uciHistory.push(key(actual));history.push(apply(s,actual));pending=[];selected=-1;notification="";redraw();
  if(mode.value==='online'&&net.role==='host')publishState();
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
 newButton.addEventListener('click',()=>{if(mode.value==='online'&&net.role==='guest'){netNotice(otext.noReset);return;}resetGame();});
 mode.addEventListener('change',()=>{
  stopOnline(otext.idle);onlinePanel.hidden=mode.value!=='online';
  resetGame(false);
 });
 createButton.addEventListener('click',()=>{if(mode.value==='online')openOnline('host',randomRoomCode());});
 joinButton.addEventListener('click',()=>{
  const code=roomInput.value.trim().toUpperCase().replace(/^.*[?&]room=/,'').split('&')[0];
  if(!validRoom(code)){netNotice(otext.invalid);return;}openOnline('guest',code);
 });
 copyButton.addEventListener('click',async()=>{
  const url=new URL(window.location.href);url.searchParams.set('room',net.room);
  try{await navigator.clipboard.writeText(url.href);netNotice(otext.copied);}catch{roomInput.value=url.href;roomInput.select();netNotice(otext.copyFailed);}
 });
 leaveButton.addEventListener('click',()=>{
  stopOnline(otext.closed);resetGame(false);
  const url=new URL(window.location.href);url.searchParams.delete('room');window.history.replaceState(null,'',url.pathname+url.search);
 });
 const invitedRoom=new URL(window.location.href).searchParams.get('room');
 if(invitedRoom&&validRoom(invitedRoom.toUpperCase())){mode.value='online';onlinePanel.hidden=false;roomInput.value=invitedRoom.toUpperCase();netNotice(otext.idle);}
 else netNotice(otext.idle);
 back.addEventListener("click",()=>{
  serial++;if(history.length<=1)return;
  const howMany=mode.value==="computer"&&history.length>=3&&state().t===1?2:1;
  history.splice(-howMany);labels.splice(-howMany);uciHistory.splice(-howMany);selected=-1;pending=[];claimed=false;notification="";redraw();
  if(botTurn())queueBot();
 });
 root.querySelector("#chess-promotion-cancel").addEventListener("click",()=>{pending=[];redraw();});
 claim.addEventListener('click',()=>{
  if(!gameStatus(history).claim)return;
  if(mode.value==='online'&&net.role==='guest'){send({type:'claim'});return;}
  serial++;claimed=true;redraw();publishState();
 });
 redraw();
}
if(typeof document!=="undefined"){
 const root=document.querySelector("[data-ribhlab-game]");
 if(root){if(root.dataset.ribhlabGame==="chess")initChess(root);}
}
export{parseFen,apply,legal,checked,san,gameStatus,moveLabel,index,chessStartFen};
