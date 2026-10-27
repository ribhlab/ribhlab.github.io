# RibhLab — safe custom-domain and AdSense activation guide (2026-10-27)

> **STOP: no domain has been purchased or connected by this commit.** Do not replace the current public URL or add a domain before the owner has registered it and proved ownership. Google AdSense acceptance is not guaranteed by a domain name, TLD or these technical changes. Ads are OFF by default. No scheduler is enabled.

## Recommended domain naming

**Preferred candidate:** \`ribhlab.com\` (short and identical to the site's brand). **Fallback candidates:** \`ribhlabhub.com\` and \`ribhlabonline.com\`. These are **proposed search terms only**; registrar availability is NOT verified and can change. Use a registrar's actual checkout availability and renewal price before making a purchase. Do not buy a lookalike or previously owned domain without checking brand conflicts, renewal pricing and its reputation.

A general \`.com\` is appropriate for a multilingual international magazine but **does not guarantee Google AdSense approval**. Choosing a temporary no-cost subdomain can complicate ownership and later migrations.

For a Moroccan checkout, the published OVHcloud Morocco standard \`.com\` price checked 27 October 2026 was 84.04 MAD excl. tax / 100.85 MAD incl. tax for the first year, and renewal 147 MAD excl. tax / 176.40 MAD incl. tax; verify current checkout for the exact name and any premium surcharge:
https://www.ovhcloud.com/fr-ma/domains/tld/com/

## Step 1 — Buy in your own name

Purchase **only after** the registrar confirms that the desired exact spelling is available, and ensure that your own account owns the registration. Keep registrar login, transfer/renewal rights and billing private. **No web hosting purchase is required**: the existing site is already deployed by GitHub Pages. Do not share login passwords or card information in GitHub issues or this repository.

## Step 2 — Set up GitHub Pages custom domain BEFORE DNS

1. Open https://github.com/univcours/ribhlab-site/settings/pages and set **Custom domain** to your genuinely registered exact domain, e.g. \`ribhlab.com\` (without https).
2. Save, and complete GitHub's **Verify domain** owner-proof flow. For GitHub Actions publishing, GitHub documentation says a \`CNAME\` file in the publishing artifact is **not** required and is ignored. Use GitHub Pages settings instead.
3. At your domain registrar's DNS zone, for an apex domain such as \`ribhlab.com\`, create four **A** records:

| DNS type | Host | Value |
|---|---|---|
| A | @ | 185.199.108.153 |
| A | @ | 185.199.109.153 |
| A | @ | 185.199.110.153 |
| A | @ | 185.199.111.153 |
| CNAME | www | univcours.github.io |

Use the exact host \`univcours.github.io\` with **no** \`/ribhlab-site\` path in the \`www\` CNAME. Remove conflicting records and avoid wildcard \`*\` records. Once GitHub's DNS and ownership checks pass, choose **Enforce HTTPS**. DNS can take up to 24 hours to propagate.

Official GitHub instructions:
https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site

## Step 3 — Switch the website build only AFTER HTTPS works

Open repo **Settings → Secrets and variables → Actions → Variables**:
https://github.com/univcours/ribhlab-site/settings/variables/actions

| Variable | Value | When |
|---|---|---|
| \`RIBHLAB_SITE_URL\` | \`https://ribhlab.com\` | Only after actual domain is owned, verified and points to GitHub Pages |
| \`RIBHLAB_CONTACT_EMAIL\` | A public editorial contact address | Before monetization review (do not post private emails in source code) |
| \`RIBHLAB_GOOGLE_SITE_VERIFICATION\` | **Exact** Google Search Console HTML-meta token | If using Search Console HTML tag verification rather than DNS TXT |
| \`RIBHLAB_ADSENSE_PUBLISHER_ID\` | Your own \`ca-pub-0000000000000000\` pattern ID | After creating your AdSense account; **never** copy the example ID |
| \`RIBHLAB_ENABLE_ADSENSE\` | \`false\` | KEEP OFF until AdSense site status is **Ready**; later owner can switch to \`true\` |

These configuration variables are read at GitHub Actions build time, not from visitors. Every push rebuilds the HTML using the new exact public origin. When the variable \`RIBHLAB_SITE_URL\` is not set, current GitHub Pages project site remains at \`https://univcours.github.io/ribhlab-site\`.

The build already adapts internal links, canonical metadata, hreflang, language routes \`/ar/\`, \`/en/\`, \`/fr/\`, \`robots.txt\`, \`sitemap.xml\`, and \`ads.txt\` for a root domain. A test workflow preflights this with a deliberately nonexistent \`.example\` hostname. Do not set test domain in production.

After setting the variables, run a regular deployment via push to \`main\` or GitHub Actions **workflow_dispatch**. The deployment workflow has no scheduled run.

## Step 4 — Google Search Console

1. Add **Domain property** for the domain at https://search.google.com/search-console and place Google's provided \`TXT\` DNS record at the registrar; this is usually the most comprehensive verification. Alternatively use the optional HTML meta token above (suitable for URL-prefix ownership verification).
2. Verify the property and submit **https://ribhlab.com/sitemap.xml** using the **actual** purchased domain.
3. Check canonical URLs, pages indexed, language versions and any redirect from old project site to the new domain. Do **not** claim a complete SEO migration merely because DNS or site deployment succeeded.

For an existing indexed site, follow Google's site-move guidance: https://developers.google.com/search/docs/crawling-indexing/site-move-with-url-changes .

## Step 5 — Connect & request Google AdSense review

1. In your own AdSense account go to **Sites → New site**, enter the actual domain and follow the verification instructions.
2. Add your real \`RIBHLAB_ADSENSE_PUBLISHER_ID\` in repository Action variables. The site build then outputs **two ownership-proof artifacts even while ads are OFF**:
    * \`<meta name="google-adsense-account" content="ca-pub-…">\` between \`<head>\` and \`</head>\`, on all generated pages;
    * \`https://YOUR-DOMAIN/ads.txt\` with Google's authorized digital seller record for your own publisher ID.
3. Verify ownership and use the AdSense dashboard to request **site review**. Keep \`RIBHLAB_ENABLE_ADSENSE=false\` until the AdSense site is formally marked **Ready**. AdSense review can take multiple weeks and can reject a site.
4. Review content originality and quality, source attribution, contact/about/privacy pages, crawlable navigation, compliance and any required consent-management setup (including relevant European visitor privacy requirements). Financial and crypto articles must not promise earnings or misrepresent prices. Third-party image credits and permissions must be sound.
5. Once approved and privacy/consent configuration is complete, set \`RIBHLAB_ENABLE_ADSENSE=true\` and deploy to insert the publisher's AdSense JavaScript.

Official AdSense instructions:
https://support.google.com/adsense/answer/12169212
https://support.google.com/adsense/answer/9724

## Tests and verification checkpoints

The CI quality workflow verifies the current \`github.io/ribhlab-site\` build, then rebuilds with \`https://ribhlab-preflight.example\` **without publishing that fake hostname**. It checks root-relative links, sitemap, robots, optional Search Console meta, AdSense ownership meta, \`ads.txt\` and ensures no ad-serving script is added when \`ENABLE_ADSENSE=false\`. This is a **technical readiness check**, not proof that any domain has been bought, that DNS/HTTPS are ready or that Google AdSense has approved the site.

## Safety and recovery

If custom-domain setup fails, clear \`RIBHLAB_SITE_URL\` and restore the GitHub Pages domain setting to the old origin, then redeploy. Keep DNS and GitHub's custom-domain settings coordinated to avoid dangling DNS records or domain takeover risks. Never paste registrar credentials, tokens, financial information or AdSense account screenshots publicly.
