// RibhLab editorial provenance audit. Run: node scripts/audit-editorial-provenance.mjs
// This checks metadata integrity only. It cannot prove copyright ownership,
// originality, exact visual matching, or whether a remote license is still valid.
import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();
const read = p => JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
const sections = read('content/sections.json').sections;
const photos = read('content/licensed-photos.json').articlePhotos;
const audit = read('content/recipes/photo-audit.json');
const slugs = sections.flatMap(s => s.publishedSlugs || []);
const count = values => values.reduce((m,v)=>(m.set(v,(m.get(v)||0)+1),m),new Map());
const duplicates = values => [...count(values)].filter(([,n])=>n>1).map(([v,n])=>({value:v,count:n}));
const errors = [], warnings = [];
const known = new Set(slugs);
const ids = [], urls = [];
for (const slug of slugs) {
  const p = photos[slug];
  if (!p) { errors.push('Article missing image metadata: '+slug); continue; }
  if (!p.photoId || !p.source || !p.photographer || !p.license || !p.alt) {
    errors.push('Incomplete photo provenance: '+slug);
  }
  if (p.photoId) ids.push(p.photoId);
  if (p.source) urls.push(p.source);
  if (!p.license?.includes('Unsplash') && !/CC0|CC BY|Public Domain/i.test(p.license||'')) {
    warnings.push('Manually check commercial license: '+slug);
  }
  if (!p.originalAssetProof && !p.originalCreationEvidence) {
    warnings.push('Third-party/uncertified originality (do not claim owned photo): '+slug);
  }
}
for (const slug of Object.keys(photos)) if (!known.has(slug)) warnings.push('Orphan photo metadata: '+slug);
for (const item of duplicates(slugs)) errors.push('Duplicate article slug: '+item.value);
for (const item of duplicates(ids)) errors.push('Duplicate photo ID: '+item.value);
for (const item of duplicates(urls)) errors.push('Duplicate source URL: '+item.value);
if (audit.totalRecipes !== audit.photoBackedRecipes + audit.temporaryIllustrations)
  errors.push('Recipe photo totals do not reconcile');
if (audit.temporaryIllustrations) warnings.push(audit.temporaryIllustrations+' recipe cards still use temporary illustrations');

// Editorial text integrity: detects exact reused paragraphs, missing references,
// and incomplete translations. This is not a web plagiarism detector.
const articlesDir = path.join(root, 'content/articles');
const articleFiles = fs.readdirSync(articlesDir).filter(f => f.endsWith('.json'));
const seenParagraphs = new Map();
const normalize = s => String(s || '').toLowerCase().replace(/\\s+/g, ' ').trim();
for (const file of articleFiles) {
  const article = read('content/articles/' + file);
  if (!article.slug || !known.has(article.slug)) warnings.push('Unlisted article file: ' + file);
  if (!Array.isArray(article.sources) || !article.sources.length)
    warnings.push('No references: ' + file);
  for (const src of article.sources || []) {
    if (!String(src.url || '').startsWith('https://')) errors.push('Invalid source URL: ' + file);
  }
  for (const locale of ['ar', 'en', 'fr']) {
    const tr = article.translations?.[locale];
    if (!tr?.title || !tr?.lead || !Array.isArray(tr.sections) || !tr.sections.length) {
      errors.push('Incomplete ' + locale + ' translation: ' + file);
      continue;
    }
    const paragraphs = tr.sections.flatMap(sec => sec.paragraphs || []);
    const words = normalize([tr.lead, ...paragraphs].join(' ')).split(' ').filter(Boolean).length;
    if (words < 120) warnings.push('Short article (' + locale + ', ' + words + ' words): ' + file);
    for (const para of paragraphs) {
      const key = locale + ':' + normalize(para);
      if (key.length < 100) continue;
      const prev = seenParagraphs.get(key);
      if (prev && prev !== article.slug)
        warnings.push('Repeated paragraph (' + locale + '): ' + prev + ' / ' + article.slug);
      else seenParagraphs.set(key, article.slug);
    }
  }
}

const result = {
  checkedAt: new Date().toISOString(),
  scope: 'Source metadata; not a plagiarism scan, image visual inspection, or live website test',
  articleCount: slugs.length, sections: sections.length,
  assignedArticlePhotos: slugs.filter(s=>!!photos[s]).length,
  photoIdsUnique: new Set(ids).size, photoSourceUrlsUnique: new Set(urls).size,
  recipeCount: audit.totalRecipes, recipePhotos: audit.photoBackedRecipes,
  recipeTemporaryIllustrations: audit.temporaryIllustrations,
  errors, warnings,
  approvalReady: false,
  note: 'Never claim AdSense approval readiness or original photography from this audit alone.'
};
console.log(JSON.stringify(result,null,2));
if (errors.length) process.exitCode = 1;
