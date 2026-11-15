# RibhLab — AdSense readiness and short-URL migration

Verified: **15 November 2026**, `https://ribhlab.github.io/`.

## Completed and live-verified

- XML sitemap: **651 canonical entries**, fetched independently over public HTTPS. **0 URLs longer than 80 characters**, longest full URL **79 characters**.
- Public route migration: **258 unique legacy paths** mapped to canonical paths capped at **54 pathname characters**. Mappings are in `/assets/short-url-map.json`. Old paths stay available with an immediate HTML `meta refresh` and a canonical pointing to the new URL, rather than a fake HTTP 301. GitHub Pages does not support custom per-path server redirects in the static site.
- The canonical address, localized alternate links, structured metadata and internal article/search links are rewritten during builds. The sitemap contains the **new canonical paths only**. Do not delete legacy aliases; permanent redirects using an edge-enabled host would be preferable if a custom domain is later adopted.
- RibhLab was built in Arabic, English and French and navigation remained functional in Chromium responsive tests: **91 tests passed, 0 failed** on [GitHub Actions run 43661385087](https://github.com/ribhlab/ribhlab.github.io/actions/runs/43661385087).
- Search-quality gate: **65 of 95** trilingual editorial source records currently meet RibhLab's internal depth-and-attribution minimum; the other **30 remain directly accessible but use `noindex,follow`, do not load AdSense and are omitted from the article archive, category lists, related-story recommendations and site search until independently revised.
- Rewrote **four previously short/unsourced records** in all three languages using worked examples, transparent caveats, direct primary documentation and specific actionable guidance: `adsense-ready-original-site-2026-checklist`, `ai-prompts-at-work`, `online-income-real-business-models`, and `ai-finance-automation-with-human-controls` (synthetic reconciliation controls grounded in NIST and Microsoft security references). Their public links now pass the same evidence/depth gate.
- Independent OpenSEO audit of 50 discoverable pages found no critical issues, but identified long search titles and meta descriptions predominantly in recruitment reports; these snippets were shortened in `src/opportunity-pages.mjs` without changing factual H1 content. The 50-page crawl limit is a tool sampling limit, not a site error.
- The **120 recipe detail records × 3 languages** continue to have transparent notices explaining that their generic method directions are *not* individual kitchen tests. These details remain `noindex` and do not load AdSense while individual dish-specific instructions await genuine editorial review. Recipe browsing and ingredient measurements remain available.
- The removed skin-care content remains absent from the site and sitemap, with a future-publication block.
- AdSense ownership publisher meta, publisher-matched `/ads.txt`, official verification script on substantive eligible pages, privacy/editorial disclosures and author byline links remain configured. The script does not load on legal pages, noindexed articles, templated recipes or redirect aliases.
- Independent public source link tests, hreflang, canonical, XML validity, internal links, mobile layout and retired-health URL checks are enforced in the GitHub pipeline.

## Important limitations — not automatically solved by code

1. **Google AdSense rejection code:** The generic rejection email did not specify a violation. The only definitive case explanation remains in AdSense → Sites → `ribhlab.github.io` → Needs attention → View details. Nothing in this audit can guarantee approval.
2. **Search Console processing:** Google showed *Impossible de lire le sitemap* and sampled inspected URLs unknown to Google on **14 November 2026**. Independent HTTP 200 and valid XML cannot prove that Google's own account-side processor has succeeded. Check new processing results and indexing from Search Console; resubmit `sitemap.xml` only if the account still reports failure.
3. **Copyright and accuracy:** Automated checks prove neither global textual originality nor image authorship. Existing external images are credited/licensed where recorded, **not represented as original photos made by RibhLab**. Every material fact and license needs ongoing human verification. The 30 excluded articles must be substantively rewritten; do not pad words or invent references to bypass the editorial gate.
4. **Private contact:** Only a public GitHub issue workflow is configured for editorial corrections. A genuine private professional inbox would improve trust and privacy handling; do not invent or expose personal email addresses.
5. **Ad consent:** Before Google serves ads to users in the EEA, UK and Switzerland, implement the certified consent-management solution and settings required by the applicable Google publisher policies. The site source cannot configure all AdSense account-side settings without access.
6. **Domain:** `github.io` remains the actual origin; no unowned custom domain has been activated. Any future move must include verified DNS ownership, appropriate redirects and Search Console updates.

## Quality-control policy

There is **no general Google rule requiring 300 words or two citations per post**. Those are internal RibhLab triage thresholds to prioritize genuine editorial substance and verified evidence. An automated quality gate is not proof of content originality or approval.

## Primary documentation

- [Google AdSense readiness and original content](https://support.google.com/adsense/answer/7299563?hl=en)
- [Google Publisher Policies](https://support.google.com/adsense/answer/10502938?hl=en)
- [Google Search Central — site URL moves and redirects](https://developers.google.com/search/docs/crawling-indexing/site-move-with-url-changes)
- [Google Search Central — meta refresh alternatives](https://developers.google.com/search/docs/crawling-indexing/301-redirects)
- [AdSense site status and required review](https://support.google.com/adsense/answer/12170222)
