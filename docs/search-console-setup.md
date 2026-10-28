# RibhLab — Google Search Console verification and sitemap

> This is a setup checklist for the owner. Do **not** put an email address, password, session cookie, or one-time code into the public repository.

## Canonical property

- Site: **https://ribhlab.github.io/**
- Search Console property type: **URL-prefix** (not a GitHub-wide `github.io` domain property)
- Languages: `/ar/`, `/en/` and `/fr/`
- Sitemap: **https://ribhlab.github.io/sitemap.xml**
- Robots: **https://ribhlab.github.io/robots.txt**

## Google Search Console setup

1. Open **https://search.google.com/search-console** while signed in as the Google account authorized to own RibhLab.
2. Choose **Add property → URL prefix** and paste `https://ribhlab.github.io/`. If this property already exists, open it instead; do not create a duplicate.
3. Check whether Google automatically verifies the property using its existing verification file: `https://ribhlab.github.io/googlee227daed117c5deb.html`. The GitHub repository already contains this file; its presence does not prove this specific Google account owns the property. **Do not replace or delete it.** If it belongs to a different owner, select **HTML tag** verification instead and copy the token from `content="..."`; the generator already supports `GOOGLE_SITE_VERIFICATION`, supplied by the GitHub Actions variable `RIBHLAB_GOOGLE_SITE_VERIFICATION`. No password or sign-in code should be shared. Confirm the tag is in the deployed homepage source before clicking Verify.
4. Once the tag is deployed and appears on the root and language homepages, click **Verify**. Keep the tag on the site for continued verification.
5. In **Sitemaps** submit `sitemap.xml`, then inspect its status and the Pages indexing report.
6. In **URL Inspection**, check `https://ribhlab.github.io/ar/`, `https://ribhlab.github.io/ar/recipes/`, `https://ribhlab.github.io/ar/opportunities/` and a recent original article. Use *Request indexing* selectively for newly created important pages, not automatically for every URL.
7. Under **Performance → Search results**, review queries, impressions, clicks, CTR and average position by page and country over time. Investigate pages with impressions but poor CTR: improve accurate titles and human-readable descriptions, not keyword stuffing.
8. Review rich results with Google's **Rich Results Test**; fix invalid properties before announcing Google enhancement eligibility.

## Repository SEO safeguards

- `src/build.mjs` produces the canonical URLs, hreflang alternates, robots directives and sitemap, plus breadcrumb structured data.
- The sitemap lists only indexable routes; unverified timestamps are omitted rather than fabricated. The `lastmod` for original editorial articles uses the actual article update date.
- `src/recipe-pages.mjs` provides dish-specific titles and Recipe structured data, original explanatory hub copy and internal links between relevant recipes.
- `src/check.mjs` checks the generated pages, links, meta tags and sitemap.

Submission is a **discovery signal**, not a guarantee of ranking, indexing, search traffic, or a particular position. Quality, competitive relevance and crawling decisions remain Google's responsibility.

References:
- https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap
- https://support.google.com/webmasters/answer/34592
- https://support.google.com/webmasters/answer/9008080
