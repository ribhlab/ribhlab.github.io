// Shared, side-effect-free Document Studio Pro calculations and draft validation.
// Runs in the browser and in the Node.js test suite; never sends data to a server.
export const DOCUMENT_KINDS=Object.freeze(['invoice','quote','cv','report','letter']);
export const DOCUMENT_THEMES=Object.freeze(['modern','classic','minimal']);
const round2=n=>Math.round((n+Number.EPSILON)*100)/100;
const number=(value,name,min,max)=>{
 const n=Number(value);
 if(!Number.isFinite(n)||n<min||n>max)throw new RangeError(name+' must be between '+min+' and '+max);
 return n;
};
export function computeTotals(items,taxPercent=0,discountPercent=0){
 if(!Array.isArray(items)||items.length<1||items.length>40)throw new RangeError('Add 1–40 invoice rows');
 const rows=items.map((item,index)=>{
  const qty=number(item.quantity,'Quantity row '+(index+1),0.000001,100000000);
  const unit=number(item.unitPrice,'Unit price row '+(index+1),0,100000000000);
  const description=String(item.description||'').trim().slice(0,500);
  return {description,quantity:qty,unitPrice:unit,lineTotal:round2(qty*unit)};
 });
 const taxRate=number(taxPercent,'Tax percent',0,100);
 const discountRate=number(discountPercent,'Discount percent',0,100);
 const subtotal=round2(rows.reduce((sum,row)=>sum+row.lineTotal,0));
 const discount=round2(subtotal*discountRate/100);
 const beforeTax=round2(subtotal-discount);
 const tax=round2(beforeTax*taxRate/100);
 const total=round2(beforeTax+tax);
 if(!Number.isFinite(total)||total>100000000000000)throw new RangeError('Document total exceeds supported value');
 return {rows,subtotal,discount,beforeTax,tax,total,taxRate,discountRate};
}
export function csvCell(value){
 let v=String(value??'');
 // Guard formula injection in spreadsheet applications, including leading whitespace.
 if(/^\s*[=+\-@]/u.test(v)||/^[\t\r\n]/u.test(v))v="'"+v;
 return '"'+v.replace(/"/g,'""')+'"';
}
export const csvLine=values=>values.map(csvCell).join(',');
const safeText=(value,max=200)=>String(value??'').slice(0,max);
export function normalizeDraft(input){
 if(!input||typeof input!=='object'||Array.isArray(input)||input.version!==1)throw new TypeError('Unsupported draft schema');
 const d=input.document;
 if(!d||typeof d!=='object'||Array.isArray(d))throw new TypeError('Document data missing');
 const kind=DOCUMENT_KINDS.includes(d.kind)?d.kind:'invoice';
 const theme=DOCUMENT_THEMES.includes(d.theme)?d.theme:'modern';
 const items=Array.isArray(d.items)?d.items.slice(0,40).map(item=>({
  description:safeText(item?.description,500),
  quantity:number(item?.quantity??1,'Quantity',0.000001,100000000),
  unitPrice:number(item?.unitPrice??0,'Unit price',0,100000000000)
 })):[{description:'',quantity:1,unitPrice:0}];
 if(!items.length)items.push({description:'',quantity:1,unitPrice:0});
 const result={
  kind,theme,
  issuer:safeText(d.issuer,180),
  recipient:safeText(d.recipient,180),
  details:safeText(d.details,12000),
  reference:safeText(d.reference,80),
  issueDate:safeText(d.issueDate,10),
  dueDate:safeText(d.dueDate,10),
  email:safeText(d.email,180),
  phone:safeText(d.phone,80),
  address:safeText(d.address,500),
  currency:['MAD','USD','EUR','GBP','CAD'].includes(d.currency)?d.currency:'MAD',
  taxPercent:number(d.taxPercent??0,'Tax percent',0,100),
  discountPercent:number(d.discountPercent??0,'Discount percent',0,100),
  items
 };
 if(result.issueDate&&!/^\d{4}-\d{2}-\d{2}$/.test(result.issueDate))throw new TypeError('Invalid issue date');
 if(result.dueDate&&!/^\d{4}-\d{2}-\d{2}$/.test(result.dueDate))throw new TypeError('Invalid due date');
 return result;
}
