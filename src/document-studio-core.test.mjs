import test from 'node:test';
import assert from 'node:assert/strict';
import {computeTotals,normalizeDraft,csvCell,csvLine,DOCUMENT_KINDS} from './document-studio-core.mjs';

test('Pro invoice calculates multiple lines, discounts and tax deterministically',()=>{
 const v=computeTotals([{description:'First',quantity:2,unitPrice:12.5},{description:'Second',quantity:3,unitPrice:10}],20,10);
 assert.equal(v.rows.length,2);
 assert.equal(v.subtotal,55);
 assert.equal(v.discount,5.5);
 assert.equal(v.beforeTax,49.5);
 assert.equal(v.tax,9.9);
 assert.equal(v.total,59.4);
});
test('Money rounds each line to cents and supports an optional zero-tax quote',()=>{
 const v=computeTotals([{description:'Small',quantity:3,unitPrice:0.1}],0,0);
 assert.equal(v.subtotal,0.3);
 assert.equal(v.tax,0);
 assert.equal(v.total,0.3);
});
test('Limits prevent accidental negative charges, negative items and unsupported tax',()=>{
 assert.throws(()=>computeTotals([{description:'Bad',quantity:-1,unitPrice:20}],0,0),RangeError);
 assert.throws(()=>computeTotals([{description:'Bad',quantity:1,unitPrice:-20}],0,0),RangeError);
 assert.throws(()=>computeTotals([{description:'Bad',quantity:1,unitPrice:20}],101,0),RangeError);
 assert.throws(()=>computeTotals([],20,0),RangeError);
 assert.throws(()=>computeTotals(Array.from({length:41},()=>({quantity:1,unitPrice:1})),0,0),RangeError);
});
test('CSV protects spreadsheet applications from formula execution',()=>{
 assert.equal(csvCell('=cmd'),'"\'=cmd"');
 assert.equal(csvCell('  +SUM(A1:A2)'),'"\'  +SUM(A1:A2)"');
 assert.equal(csvCell('@malicious'),'"\'@malicious"');
 assert.equal(csvCell('A "quote", thanks'),'"A ""quote"", thanks"');
 assert.equal(csvLine(['a','b']),'"a","b"');
});
test('Import of saved project supports all 5 document kinds, validated themes and currencies',()=>{
 for(const kind of DOCUMENT_KINDS){
  const d=normalizeDraft({version:1,document:{kind,theme:'modern',issuer:'Acme',recipient:'Customer',reference:'DOC-01',currency:'MAD',taxPercent:20,discountPercent:5,items:[{description:'Consulting',quantity:2,unitPrice:100}]}});
  assert.equal(d.kind,kind);
  assert.equal(d.reference,'DOC-01');
  assert.equal(d.items.length,1);
  assert.equal(d.currency,'MAD');
  assert.equal(d.taxPercent,20);
 }
});
test('Import strips unknown fields, constrains lengths and rejects malformed projects',()=>{
 const doc=normalizeDraft({version:1,document:{kind:'report',issuer:'x'.repeat(900),__proto__:null,items:[{quantity:1,unitPrice:0}],untrusted:'ignore'}});
 assert.equal(doc.issuer.length,180);
 assert.equal(Object.hasOwn(doc,'untrusted'),false);
 assert.throws(()=>normalizeDraft({version:2,document:{}}),TypeError);
 assert.throws(()=>normalizeDraft({version:1,document:{taxPercent:-10}}),RangeError);
 assert.throws(()=>normalizeDraft({version:1,document:{issueDate:'yesterday'}}),TypeError);
});
