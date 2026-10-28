import {buildCrossword,cleanCrosswordWord} from "./crossword-core.mjs";
const TEXT={
 ar:{across:"أفقي",down:"عمودي",new:"شبكة جديدة",check:"تحقق من الإجابات",hint:"أظهر حرفاً",clear:"مسح الشبكة",filled:"خانات صحيحة",done:"أحسنت! أكملت الكلمات المتقاطعة.",select:"اختر رقماً من القائمة أو خانة من الشبكة.",current:"الكلمة الحالية",wrong:"هناك أحرف غير صحيحة؛ يمكنك تصحيحها.",clue:"السؤال",next:"انتقل إلى الكلمة التالية",intro:"اقرأ الأسئلة الأفقية والعمودية، واكتب الحروف في شبكة واحدة: كل حرف عند التقاطع يخدم الكلمتين.",credits:"شبكات أصلية محررة خصيصاً لـRibhLab. لا تحتاج إلى حساب أو اتصال بالإنترنت."},
 en:{across:"Across",down:"Down",new:"New puzzle",check:"Check answers",hint:"Reveal one letter",clear:"Clear puzzle",filled:"Correct squares",done:"Well done! You completed the crossword.",select:"Choose a numbered clue or select a square.",current:"Current answer",wrong:"Some letters are incorrect. Correct them and try again.",clue:"Clue",next:"Next clue",intro:"Read the across and down clues. Type letters into one grid: each crossing square belongs to both words.",credits:"Original crosswords created for RibhLab; no account or internet connection required."},
 fr:{across:"Horizontal",down:"Vertical",new:"Nouvelle grille",check:"Vérifier les réponses",hint:"Révéler une lettre",clear:"Effacer la grille",filled:"Cases correctes",done:"Bravo ! La grille est terminée.",select:"Choisissez un indice ou une case.",current:"Réponse active",wrong:"Certaines lettres sont incorrectes, corrigez-les.",clue:"Définition",next:"Indice suivant",intro:"Lisez les définitions horizontales et verticales. Les lettres des cases croisées servent à deux mots.",credits:"Grilles originales créées pour RibhLab, sans inscription ni connexion."}
};
export function initCrossword(root){
 const lang=root.dataset.lang||'ar',t=TEXT[lang],grid=root.querySelector('#crossword-grid'),clues=root.querySelector('#crossword-clues'),status=root.querySelector('#crossword-status'),current=root.querySelector('#crossword-current'),counter=root.querySelector('#crossword-counter');
 let number=0,puzzle=null,values=[],active=null,solved=false;
 const cid=(r,c)=>r+','+c;
 const lookup=new Map();
 const cell=([r,c])=>grid.querySelector('[data-cell="'+cid(r,c)+'"]');
 function mark(){
  const completed=puzzle.entries.reduce((n,e)=>n+Number(e.cells.every(([r,c],i)=>values[r][c]===e.answer[i])),0);
  counter.textContent=completed+' / '+puzzle.entries.length+' · '+puzzle.intersectionCount+' '+(lang==='ar'?'تقاطعاً':lang==='en'?'crossings':'croisements');
  for(const input of grid.querySelectorAll('[data-cell]')){
   const [r,c]=input.dataset.cell.split(',').map(Number);
   const selected=active?.cells.some(([ar,ac])=>r===ar&&c===ac);
   input.classList.toggle('active',!!selected);
   input.classList.toggle('verified-good',input.dataset.verified==='good');
   input.classList.toggle('verified-bad',input.dataset.verified==='bad');
  }
  for(const button of clues.querySelectorAll('[data-entry]')){
   const e=puzzle.entries[Number(button.dataset.entry)],complete=e.cells.every(([r,c],i)=>values[r][c]===e.answer[i]);
   button.classList.toggle('active',e===active);button.classList.toggle('solved',complete);
  }
  if(active)current.textContent=active.number+' '+(active.axis==='across'?t.across:t.down)+' · '+active.clue;
 }
 function focusEntry(e,r,c){
  active=e;
  const [rr,cc]=Number.isInteger(r)&&Number.isInteger(c)?[r,c]:e.cells.find(([x,y])=>!values[x][y])||e.cells[0];
  mark();
  cell([rr,cc])?.focus();
 }
 function inputChanged(evt){
  if(solved)return;
  const input=evt.target,[r,c]=input.dataset.cell.split(',').map(Number);
  const normalized=cleanCrosswordWord(input.value,lang);
  const letter=Array.from(normalized).slice(-1)[0]||'';
  values[r][c]=letter;input.value=letter;input.removeAttribute('data-verified');
  if(!active?.cells.some(([rr,cc])=>rr===r&&cc===c)){
   const options=lookup.get(cid(r,c))||[];active=options[0]||null;
  }
  mark();
  if(letter&&active){
   const k=active.cells.findIndex(([rr,cc])=>rr===r&&cc===c);
   const next=active.cells.slice(k+1).find(([rr,cc])=>!values[rr][cc]);
   if(next)cell(next)?.focus();
  }
 }
 function keydown(evt){
  const input=evt.target,[r,c]=input.dataset.cell.split(',').map(Number);
  if(evt.key==='Backspace'&&!input.value&&active){
   const k=active.cells.findIndex(([rr,cc])=>rr===r&&cc===c);
   const prev=active.cells[k-1];
   if(prev){evt.preventDefault();values[prev[0]][prev[1]]='';cell(prev).value='';cell(prev).removeAttribute('data-verified');cell(prev).focus();mark();}
  }
  if(evt.key==='Enter'){evt.preventDefault();const k=puzzle.entries.indexOf(active);focusEntry(puzzle.entries[(k+1)%puzzle.entries.length]);}
  const arrow={'ArrowUp':[-1,0],'ArrowDown':[1,0],'ArrowLeft':[0,-1],'ArrowRight':[0,1]}[evt.key];
  if(arrow){evt.preventDefault();let nr=r+arrow[0],nc=c+arrow[1];while(nr>=0&&nr<puzzle.height&&nc>=0&&nc<puzzle.width){if(puzzle.cells[nr][nc]){cell([nr,nc])?.focus();break;}nr+=arrow[0];nc+=arrow[1];}}
 }
 function create(){
  puzzle=buildCrossword(lang,number++);values=puzzle.cells.map(row=>row.map(()=>''));solved=false;
  lookup.clear();puzzle.entries.forEach(e=>e.cells.forEach(x=>{const id=cid(...x);lookup.set(id,[...(lookup.get(id)||[]),e])}));
  grid.replaceChildren();grid.style.gridTemplateColumns='repeat('+puzzle.width+',minmax(0,1fr))';grid.setAttribute('aria-label','Crossword '+puzzle.width+' × '+puzzle.height);
  let numbers=new Map;for(const e of puzzle.entries)numbers.set(cid(...e.cells[0]),e.number);
  for(let r=0;r<puzzle.height;r++)for(let c=0;c<puzzle.width;c++){
   const w=grid.appendChild(document.createElement('div'));w.className='crossword-square'+(!puzzle.cells[r][c]?' blocked':'');
   if(!puzzle.cells[r][c])continue;
   const id=cid(r,c),n=numbers.get(id);
   if(n){const num=document.createElement('span');num.className='crossword-number';num.textContent=n;w.append(num);}
   const input=document.createElement('input');input.type='text';input.maxLength=2;input.inputMode='text';input.autocomplete='off';input.autocapitalize='characters';input.spellcheck=false;input.dir='auto';input.dataset.cell=id;input.setAttribute('aria-label',n?String(n):t.clue);
   input.addEventListener('input',inputChanged);input.addEventListener('keydown',keydown);
   input.addEventListener('focus',()=>{
    const candidates=lookup.get(id)||[],chosen=active&&candidates.includes(active)?active:candidates[0];
    active=chosen||null;mark();
   });
   input.addEventListener('click',()=>{
    const options=lookup.get(id)||[];if(options.length>1&&active===options[0]){active=options[1];mark();}
   });
   w.append(input);
  }
  clues.replaceChildren();
  for(const axis of ['across','down']){
   const section=document.createElement('section'),heading=document.createElement('h3');heading.textContent=axis==='across'?t.across:t.down;section.append(heading);
   const ul=document.createElement('ol');ul.className='crossword-clue-list';
   for(const [i,e] of puzzle.entries.entries())if(e.axis===axis){
    const li=document.createElement('li'),b=document.createElement('button');
    b.type='button';b.dataset.entry=i;b.textContent=e.number+'. '+e.clue+' ('+e.answer.length+')';b.addEventListener('click',()=>focusEntry(e));li.append(b);ul.append(li);
   }
   section.append(ul);clues.append(section);
  }
  active=puzzle.entries[0];mark();status.textContent=t.select;
 }
 root.querySelector('#crossword-new').addEventListener('click',create);
 root.querySelector('#crossword-check').addEventListener('click',()=>{
  let wrong=0,correct=0,total=0;
  for(const input of grid.querySelectorAll('[data-cell]')){
   const [r,c]=input.dataset.cell.split(',').map(Number);
   const expected=puzzle.cells[r][c],actual=values[r][c];total++;
   const okay=actual===expected;correct+=Number(okay);wrong+=Number(!!actual&&!okay);
   input.dataset.verified=actual?(okay?'good':'bad'):'';
  }
  solved=correct===total;mark();status.textContent=solved?t.done:wrong?t.wrong:t.select;
 });
 root.querySelector('#crossword-hint').addEventListener('click',()=>{
  if(!active||solved)return;
  const k=active.cells.findIndex(([r,c],i)=>values[r][c]!==active.answer[i]);
  if(k<0)return;
  const [r,c]=active.cells[k];values[r][c]=active.answer[k];
  const input=cell([r,c]);input.value=values[r][c];input.dataset.verified='good';input.focus();mark();
 });
 root.querySelector('#crossword-clear').addEventListener('click',()=>{values=puzzle.cells.map(row=>row.map(()=>''));solved=false;for(const x of grid.querySelectorAll('[data-cell]')){x.value='';x.removeAttribute('data-verified')}status.textContent=t.select;mark()});
 root.querySelector('#crossword-next').addEventListener('click',()=>{const n=puzzle.entries.indexOf(active);focusEntry(puzzle.entries[(n+1)%puzzle.entries.length]);});
 create();
}
if(typeof document!=='undefined'){const root=document.querySelector('[data-ribhlab-game="crossword"]');if(root)initCrossword(root);}
