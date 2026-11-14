// RibhLab AdSense/search editorial quality gate.
// An internal safeguard, NOT a Google-required word count or a claim of
// copyright verification. Editors must independently confirm evidence,
// citations, photographs and originality before clearing the gate.
export const SUPPORTED_LOCALES=['ar','en','fr'];
export const MIN_EXPLANATORY_WORDS=300;
const normalize=s=>String(s||'').normalize('NFKC').toLocaleLowerCase().replace(/\s+/gu,' ').trim();

export function articleEditorialIssues(article){
 const issues=[];
 const sources=Array.isArray(article?.sources)?article.sources:[];
 const credible=sources.filter(s=>s&&typeof s.label==='string'&&s.label.trim().length>=3&&/^https:\/\/[^/]+\/.+/i.test(s.url||''));
 const distinctSources=new Set(credible.map(s=>s.url.trim().split('#')[0]));
 if(distinctSources.size<2)issues.push('fewer than two traceable HTTPS references');
 for(const lang of SUPPORTED_LOCALES){
  const translated=article?.translations?.[lang];
  const sections=translated?.sections;
  if(!translated?.title||!translated?.lead||!Array.isArray(sections)||sections.length<4){
   issues.push(lang+': incomplete article structure');
   continue;
  }
  const paragraphs=sections.flatMap(s=>Array.isArray(s.paragraphs)?s.paragraphs:[]);
  if(sections.some(s=>!s.heading||!Array.isArray(s.paragraphs)||!s.paragraphs.length)){
   issues.push(lang+': empty editorial section');
  }
  if(paragraphs.some(p=>typeof p!=='string'||p.trim().length<30)){
   issues.push(lang+': placeholder-like paragraph');
  }
  const words=normalize([translated.lead,...paragraphs].join(' ')).split(' ').filter(Boolean).length;
  if(words<MIN_EXPLANATORY_WORDS)issues.push(lang+': thin explanation ('+words+' words)');
  const heads=sections.map(s=>normalize(s.heading));
  if(new Set(heads).size!==heads.length)issues.push(lang+': repeated section headings');
 }
 return issues;
}
export const articleIndexReady=article=>articleEditorialIssues(article).length===0;
