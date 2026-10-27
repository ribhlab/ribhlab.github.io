import {DOCUMENT_KINDS,computeTotals,normalizeDraft,csvLine} from './document-studio-core.mjs';

const root=document.getElementById('document-studio');
if(root){
 const language=['ar','en','fr'].includes(document.documentElement.lang)?document.documentElement.lang:'en';
 const copy={
  ar:{invoice:'فاتورة مسودة',quote:'عرض ثمن',cv:'السيرة الذاتية',report:'تقرير مهني',letter:'رسالة مهنية',issuer:'الصادر عن',to:'إلى',reference:'المرجع',date:'التاريخ',due:'الاستحقاق / الصلاحية',email:'البريد',phone:'الهاتف',address:'العنوان',item:'الخدمة / السلعة',qty:'الكمية',price:'سعر الوحدة',amount:'المبلغ',subtotal:'المجموع الفرعي',discount:'خصم',tax:'ضريبة',total:'المجموع النهائي',details:'التفاصيل',role:'المنصب / التخصص',signature:'الاسم والتوقيع',preview:'تم تحديث المعاينة',invalid:'تحقق من بنود الفاتورة والنسب المدخلة',invoiceOnly:'تصدير CSV متاح للفواتير وعروض الأثمان فقط',saved:'تم حفظ المسودة على هذا الجهاز فقط',loaded:'تم استرجاع المسودة المحلية',cleared:'تم حذف الحفظ المحلي',noSave:'لا توجد مسودة محفوظة',loadFailed:'تعذر قراءة المسودة: ',imported:'تم استيراد المسودة بنجاح',tooLarge:'ملف JSON كبير جداً (الحد 1MB)',downloaded:'تم إعداد التحميل',print:'تفتح نافذة الطباعة؛ اختر حفظ PDF',promptReady:'البرومبت جاهز للنسخ؛ راجع الخصوصية قبل مشاركته مع خدمة أخرى',copied:'تم النسخ',copyFailed:'حدد البرومبت وانسخه يدوياً',maxRows:'الحد الأقصى 40 بنداً',minRows:'يلزم وجود بند واحد على الأقل',place:'أدخل بيانات الوثيقة لاستعراضها',promptInstruction:'حسّن المسودة التالية لغوياً وهيكلياً، دون اختراع حقائق أو أرقام. استعمل العناوين والعملة كما هي، وميز المعلومات غير المتحققة. تجنب استنتاج الامتثال الضريبي أو القانوني، واطلب مراجعة بشرية.'},
  en:{invoice:'Draft invoice',quote:'Price quotation',cv:'Curriculum vitae',report:'Professional report',letter:'Business letter',issuer:'Issued by',to:'To',reference:'Reference',date:'Date',due:'Due / valid until',email:'Email',phone:'Phone',address:'Address',item:'Item or service',qty:'Quantity',price:'Unit price',amount:'Amount',subtotal:'Subtotal',discount:'Discount',tax:'Tax',total:'Total',details:'Details',role:'Position / specialty',signature:'Name and signature',preview:'Preview updated',invalid:'Review quantities, prices, discounts and tax rates',invoiceOnly:'CSV is available for invoices and quotes only',saved:'Draft saved on this device only',loaded:'Saved browser draft restored',cleared:'Local saved draft removed',noSave:'No saved draft on this browser',loadFailed:'Unable to read draft: ',imported:'Draft imported successfully',tooLarge:'JSON file too large (1 MB limit)',downloaded:'Download prepared',print:'Print dialog opens; select Save as PDF',promptReady:'Prompt ready; review privacy before sharing with an external provider',copied:'Copied',copyFailed:'Select and copy the prompt manually',maxRows:'Maximum 40 line items',minRows:'At least one line item is required',place:'Fill in your details to preview the document',promptInstruction:'Edit the following draft for clarity and professional tone, without inventing facts, amounts or sources. Keep document references and currency unchanged. Flag any uncertain claim. Do not imply tax or legal compliance and request human review.'},
  fr:{invoice:'Facture brouillon',quote:'Devis',cv:'Curriculum vitae',report:'Rapport professionnel',letter:'Lettre professionnelle',issuer:'Émetteur',to:'Destinataire',reference:'Référence',date:'Date',due:'Échéance / validité',email:'E-mail',phone:'Téléphone',address:'Adresse',item:'Désignation',qty:'Quantité',price:'Prix unitaire',amount:'Montant',subtotal:'Sous-total',discount:'Remise',tax:'Taxe',total:'Total',details:'Détails',role:'Poste / spécialité',signature:'Nom et signature',preview:'Aperçu actualisé',invalid:'Vérifiez quantités, prix, remise et taxe',invoiceOnly:'Le CSV est réservé aux factures et devis',saved:'Brouillon enregistré sur cet appareil uniquement',loaded:'Brouillon du navigateur restauré',cleared:'Sauvegarde locale supprimée',noSave:'Aucun brouillon sauvegardé',loadFailed:'Impossible de lire le brouillon : ',imported:'Brouillon importé',tooLarge:'Fichier JSON trop volumineux (limite 1 Mo)',downloaded:'Téléchargement préparé',print:'La fenêtre d’impression permet Enregistrer en PDF',promptReady:'Prompt prêt ; vérifiez la confidentialité avant un partage externe',copied:'Copié',copyFailed:'Sélectionnez et copiez manuellement',maxRows:'Maximum 40 lignes',minRows:'Au moins une ligne est nécessaire',place:'Complétez les champs pour voir le document',promptInstruction:'Améliorez la clarté et le style professionnel du brouillon ci-dessous sans inventer de faits, de montants ni de sources. Conservez les références et la devise. Signalez les informations incertaines. Ne supposez aucune conformité fiscale ou juridique et demandez une relecture humaine.'}
 }[language];
 const localKey='ribhlab:document-studio-pro:v1';
 const find=id=>document.getElementById(id);
 const status=find('studio-status');
 const preview=find('studio-preview');
 const rowBox=find('studio-items');
 const financial=find('studio-financial-fields');
 const notes=document.querySelector('.studio-financial-field');
 const fields={
  kind:'studio-type',theme:'studio-theme',issuer:'studio-name',recipient:'studio-client',details:'studio-text',
  reference:'studio-ref',issueDate:'studio-issue-date',dueDate:'studio-due-date',email:'studio-email',
  phone:'studio-phone',address:'studio-address',currency:'studio-currency',
  taxPercent:'studio-tax',discountPercent:'studio-discount'
 };
 const value=id=>find(id)?.value??'';
 const setStatus=(message,isError=false)=>{status.textContent=message;status.dataset.error=isError?'true':'false';};
 const element=(tag,text,className)=>{
  const e=document.createElement(tag);
  if(text!==undefined&&text!==null)e.textContent=String(text);
  if(className)e.className=className;
  return e;
 };
 const addLine=(item={description:'',quantity:1,unitPrice:0})=>{
  if(rowBox.children.length>=40){setStatus(copy.maxRows,true);return;}
  const row=element('div',null,'studio-line');
  for(const [kind,text,type,val] of [
   ['description',rowBox.dataset.labelDescription,'text',item.description],
   ['quantity',rowBox.dataset.labelQuantity,'number',item.quantity],
   ['unitPrice',rowBox.dataset.labelPrice,'number',item.unitPrice]
  ]){
   const label=element('label',text,'studio-line-label');
   const input=element('input');
   input.dataset.field=kind;
   input.type=type;
   input.value=val===undefined?'':String(val);
   if(type==='number'){input.min=kind==='quantity'?'0.000001':'0';input.step='any';input.inputMode='decimal';}
   else input.maxLength=500;
   label.appendChild(input);
   row.appendChild(label);
  }
  const remove=element('button',rowBox.dataset.labelRemove,'btn btn-neutral studio-remove-row');
  remove.type='button';
  remove.setAttribute('aria-label',rowBox.dataset.labelRemove);
  remove.addEventListener('click',()=>{
   if(rowBox.children.length<=1){setStatus(copy.minRows,true);return;}
   row.remove();render();
  });
  row.appendChild(remove);
  rowBox.appendChild(row);
 };
 const readItems=()=>Array.from(rowBox.children).map(row=>{
  const get=field=>row.querySelector('[data-field="'+field+'"]')?.value??'';
  return {description:get('description'),quantity:get('quantity'),unitPrice:get('unitPrice')};
 });
 const read=()=>({
  ...Object.fromEntries(Object.entries(fields).map(([key,id])=>[key,value(id)])),
  items:readItems()
 });
 const money=(amount,currency)=>new Intl.NumberFormat(language==='ar'?'ar-MA':language==='fr'?'fr-FR':'en-GB',{minimumFractionDigits:2,maximumFractionDigits:2}).format(amount)+' '+currency;
 const append=(parent,tag,text,className)=>{const e=element(tag,text,className);parent.appendChild(e);return e;};
 const labeled=(parent,label,text)=>{
  const p=append(parent,'p',null,'studio-label-value');
  const bold=append(p,'strong',label+': ');
  p.appendChild(document.createTextNode(text||'—'));
  return bold;
 };
 const render=()=>{
  const draft=read(),kind=draft.kind,invoice=kind==='invoice'||kind==='quote';
  financial.hidden=!invoice;
  if(notes)notes.hidden=!invoice;
  const qtyButtons=Array.from(rowBox.querySelectorAll('.studio-remove-row'));
  qtyButtons.forEach(btn=>btn.disabled=rowBox.children.length===1);
  preview.replaceChildren();
  preview.className='studio-document theme-'+(draft.theme||'modern');
  preview.dir=language==='ar'?'rtl':'ltr';
  let totals;
  if(invoice){
   try{totals=computeTotals(draft.items,draft.taxPercent,draft.discountPercent);}
   catch(error){setStatus(copy.invalid+': '+error.message,true);return false;}
  }
  const header=append(preview,'div',null,'studio-doc-header');
  append(header,'span','RIBHLAB · DOCUMENT STUDIO PRO','studio-doc-overline');
  append(header,'h2',copy[kind]||copy.invoice);
  if(draft.reference.trim())append(header,'p',copy.reference+': '+draft.reference.trim(),'studio-document-ref');
  if(draft.issueDate)append(header,'p',copy.date+': '+draft.issueDate);
  if(invoice&&draft.dueDate)append(header,'p',copy.due+': '+draft.dueDate);
  const contact=append(preview,'div',null,'studio-doc-contact');
  labeled(contact,copy.issuer,draft.issuer);
  if(draft.email.trim())labeled(contact,copy.email,draft.email);
  if(draft.phone.trim())labeled(contact,copy.phone,draft.phone);
  if(draft.address.trim())labeled(contact,copy.address,draft.address);
  if(kind==='cv'){
   if(draft.recipient.trim())labeled(preview,copy.role,draft.recipient);
  }else labeled(preview,copy.to,draft.recipient);
  if(invoice){
   if(draft.details.trim())append(preview,'p',draft.details.trim(),'studio-document-body');
   const table=append(preview,'table',null,'studio-doc-table');
   const thead=append(table,'thead'),headrow=append(thead,'tr');
   [copy.item,copy.qty,copy.price,copy.amount].forEach(text=>append(headrow,'th',text));
   const tbody=append(table,'tbody');
   for(const item of totals.rows){
    const tr=append(tbody,'tr');
    for(const text of [item.description||'—',String(item.quantity),money(item.unitPrice,draft.currency),money(item.lineTotal,draft.currency)]){
     append(tr,'td',text);
    }
   }
   const summary=append(preview,'div',null,'studio-doc-summary');
   labeled(summary,copy.subtotal,money(totals.subtotal,draft.currency));
   if(totals.discountRate)labeled(summary,copy.discount+' ('+totals.discountRate+'%)','− '+money(totals.discount,draft.currency));
   labeled(summary,copy.tax+' ('+totals.taxRate+'%)',money(totals.tax,draft.currency));
   labeled(summary,copy.total,money(totals.total,draft.currency));
  }else{
   append(preview,'h3',kind==='cv'?copy.details:kind==='letter'?copy.letter:copy.details);
   append(preview,'p',draft.details.trim()||copy.place,'studio-document-body');
   if(kind==='letter')append(preview,'p',draft.issuer.trim()||'—','studio-letter-signature');
  }
  setStatus(copy.preview);
  return true;
 };
 const fill=(d)=>{
  for(const [key,id] of Object.entries(fields))find(id).value=d[key]??'';
  rowBox.replaceChildren();
  d.items.forEach(addLine);
  render();
 };
 const safeDraft=()=>normalizeDraft({version:1,document:read()});
 const slug=()=>{
  const s=value('studio-ref').trim().replace(/[^a-z0-9_-]+/gi,'-').replace(/^-+|-+$/g,'').slice(0,48);
  return 'ribhlab-'+(s||value('studio-type'));
 };
 const download=(filename,text,type)=>{
  const blob=new Blob([text],{type});
  const url=URL.createObjectURL(blob),link=document.createElement('a');
  link.href=url;link.download=filename;
  document.body.appendChild(link);link.click();link.remove();
  setTimeout(()=>URL.revokeObjectURL(url),1500);
  setStatus(copy.downloaded);
 };
 const exportHtml=()=>{
  if(!render())return;
  const stylesheet='@page{size:A4;margin:15mm}*{box-sizing:border-box}body{margin:0;font-family:Arial,Helvetica,sans-serif;color:#192a3b}article{max-width:210mm;margin:0 auto;padding:14mm;line-height:1.6}h2{font-size:26px;margin:0 0 8px}h3{margin:18px 0 8px}.studio-doc-header{border-bottom:2px solid #176d76;margin-bottom:16px;padding-bottom:14px}.studio-doc-overline{font-size:10px;text-transform:uppercase;letter-spacing:2px;color:#176d76}.studio-doc-contact{margin-bottom:22px}.studio-label-value{margin:4px 0}.studio-document-body{white-space:pre-wrap;overflow-wrap:anywhere}table{border-collapse:collapse;width:100%;margin:16px 0;font-size:13px}th,td{border-bottom:1px solid #ccd6df;padding:9px 5px;text-align:start;vertical-align:top}th{background:#eef5f6}.studio-doc-summary{margin-inline-start:auto;max-width:340px}.studio-doc-summary p:last-child{border-top:2px solid #176d76;padding-top:9px;font-size:19px;font-weight:700}.theme-classic .studio-doc-header{border-color:#253147}.theme-minimal .studio-doc-header{border-color:#888}';
  const content='<!doctype html><html lang="'+language+'" dir="'+(language==='ar'?'rtl':'ltr')+'"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Document Studio Pro - '+slug()+'</title><style>'+stylesheet+'</style></head><body>'+preview.outerHTML.replace('<div ','<article ').replace(/<\/div>$/,'</article>')+'</body></html>';
  download(slug()+'.html',content,'text/html;charset=utf-8');
 };
 const exportCsv=()=>{
  const d=read();
  if(d.kind!=='invoice'&&d.kind!=='quote'){setStatus(copy.invoiceOnly,true);return;}
  let total;
  try{total=computeTotals(d.items,d.taxPercent,d.discountPercent);}
  catch(error){setStatus(copy.invalid+': '+error.message,true);return;}
  const rows=[
   [copy.reference,d.reference],
   [copy.issuer,d.issuer],
   [copy.to,d.recipient],
   [copy.date,d.issueDate],
   [copy.due,d.dueDate],
   [],
   [copy.item,copy.qty,copy.price,copy.amount],
   ...total.rows.map(item=>[item.description,item.quantity,item.unitPrice,item.lineTotal]),
   [],
   [copy.subtotal,total.subtotal],
   [copy.discount,total.discount],
   [copy.tax,total.tax],
   [copy.total,total.total],
   ['Currency',d.currency]
  ];
  download(slug()+'.csv','\uFEFF'+rows.map(csvLine).join('\r\n'),'text/csv;charset=utf-8');
 };
 const prompt=()=>{
  const draft=read();
  const label=copy[draft.kind]||draft.kind;
  const body=[copy.promptInstruction,'',label,copy.issuer+': '+draft.issuer,copy.to+': '+draft.recipient,copy.reference+': '+draft.reference,copy.date+': '+draft.issueDate,copy.details+':',draft.details];
  if(draft.kind==='invoice'||draft.kind==='quote'){
   body.push('',copy.item+':');
   draft.items.forEach((row,i)=>body.push((i+1)+'. '+row.description+' | '+row.quantity+' × '+row.unitPrice+' '+draft.currency));
   body.push(copy.tax+': '+draft.taxPercent+'%',copy.discount+': '+draft.discountPercent+'%');
  }
  find('studio-ai-prompt-output').value=body.join('\n');
  setStatus(copy.promptReady);
 };
 const print=()=>{if(render()){setStatus(copy.print);window.print();}};
 find('studio-add-item').addEventListener('click',()=>{addLine();render();});
 find('studio-render').addEventListener('click',render);
 find('studio-print').addEventListener('click',print);
 find('studio-html').addEventListener('click',exportHtml);
 find('studio-csv').addEventListener('click',exportCsv);
 find('studio-json-download').addEventListener('click',()=>{
  try{const d=safeDraft();download(slug()+'.json',JSON.stringify({version:1,document:d},null,2),'application/json;charset=utf-8');}
  catch(error){setStatus(copy.invalid+': '+error.message,true);}
 });
 find('studio-save').addEventListener('click',()=>{
  try{const draft=safeDraft();localStorage.setItem(localKey,JSON.stringify({version:1,document:draft}));setStatus(copy.saved);}
  catch(error){setStatus(copy.loadFailed+error.message,true);}
 });
 find('studio-load').addEventListener('click',()=>{
  try{const raw=localStorage.getItem(localKey);if(!raw){setStatus(copy.noSave,true);return;}fill(normalizeDraft(JSON.parse(raw)));setStatus(copy.loaded);}
  catch(error){setStatus(copy.loadFailed+error.message,true);}
 });
 find('studio-clear').addEventListener('click',()=>{
  try{localStorage.removeItem(localKey);setStatus(copy.cleared);}
  catch(error){setStatus(copy.loadFailed+error.message,true);}
 });
 find('studio-import').addEventListener('change',async e=>{
  const file=e.target.files?.[0];
  if(!file)return;
  try{
   if(file.size>1048576)throw new Error(copy.tooLarge);
   const d=normalizeDraft(JSON.parse(await file.text()));
   fill(d);setStatus(copy.imported);
  }catch(error){setStatus(copy.loadFailed+error.message,true);}
  finally{e.target.value='';}
 });
 find('studio-prompt').addEventListener('click',prompt);
 find('studio-copy-prompt').addEventListener('click',async()=>{
  const box=find('studio-ai-prompt-output');
  if(!box.value)prompt();
  try{await navigator.clipboard.writeText(box.value);setStatus(copy.copied);}
  catch{box.focus();box.select();setStatus(copy.copyFailed,true);}
 });
 root.addEventListener('input',e=>{
  if(e.target?.closest?.('#studio-items')||e.target?.matches?.('input,textarea,select'))render();
 });
 root.addEventListener('change',e=>{
  if(e.target?.matches?.('select'))render();
 });
 addLine();
 const issue=find('studio-issue-date');
 if(!issue.value){
  const now=new Date(),local=new Date(now.getTime()-now.getTimezoneOffset()*60000);
  issue.value=local.toISOString().slice(0,10);
 }
 render();
}
