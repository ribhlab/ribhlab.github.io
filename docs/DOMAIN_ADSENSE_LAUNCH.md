# RibhLab — custom domain and Google AdSense launch playbook
_27 October 2026 · Preparatory checklist; domain **not purchased, not verified, and not connected**._

## Recommended names (availability and exact renewal price NOT confirmed)
1. `ribhlab.com` — short, brand-matched, internationally understandable. **Preferred if currently available and not premium-priced.**
2. `ribhlabmedia.com` — clear fallback for a multilingual editorial website.
3. `ribhlabhub.com` — further fallback.

Do NOT assume any listed name is free or owned: check **live registrar availability and checkout pricing before paying**. Namecheap: https://www.namecheap.com/domains/domain-name-search/ ; OVHcloud Morocco: https://www.ovhcloud.com/fr-ma/domains/domain-name-checker/ . Compare **first-year and renewal pricing**, taxes, WHOIS privacy, DNS controls, account ownership and renewal policy. Register in the **site owner's own account**. These providers' public domain price banners are introductory generic offers, NOT verified prices or availability for the exact names.

### AdSense requirements that a .com suffix does NOT solve
Google checks unique, valuable original content, site ownership, site navigation, policy compliance and the site as a whole; **there is no AdSense-approved TLD**. The custom domain does not guarantee either indexing or AdSense approval. Apply only when the selected host is public and its content is ready. Official:
- https://support.google.com/adsense/answer/9724
- https://support.google.com/adsense/answer/12169212
- https://support.google.com/adsense/answer/2784438
- https://support.google.com/adsense/answer/12176698

## IMPORTANT: choose ONE primary hosting destination
Current GitHub archive (leave unchanged until the owner has verified a live domain):
https://univcours.github.io/ribhlab-site/

Separate Blogger project: https://ribhlab.blogspot.com/ . Publishing and ownership verification must be done explicitly. RibhLab blog drafts are not automatically approved/published by changing a DNS record. Do NOT point the same bare domain to Blogger and GitHub Pages simultaneously; pick one canonical host.

### Option A — recommended if Blogger is the future public editorial + AdSense site
1. First buy the domain; do **not** make GitHub custom-domain changes or redirect the existing GitHub site.
2. In Blogger select RibhLab → **Settings → Publishing → Custom domain** → type `www.YOUR-OWN-DOMAIN.com`. Blogger will provide two CNAMEs: `www → ghs.google.com` and a second **per-account verification CNAME** with a unique token. Only use the values that Blogger displays for the actual signed-in blog.
3. At the registrar add the two CNAMEs. For apex forwarding from `YOUR-OWN-DOMAIN.com` to `www`, add these Google A records at `@`: `216.239.32.21`, `216.239.34.21`, `216.239.36.21`, `216.239.38.21`. Enable Blogger **Redirect domain**, **HTTPS availability** and **HTTPS redirect** after propagation. Make sure a conflicting A/CNAME record is not present. If a CAA record is used, it must permit Let's Encrypt per Blogger guidance.
4. Verify the purchased domain in **Google Search Console** via the exact DNS TXT verification Google provides. Submit the live Blogger sitemap after original posts are published and URLs respond 200.
5. From Blogger → **Earnings**, follow Google's AdSense onboarding (not the standalone static-site flow). Have policy pages, original publicly accessible posts, working navigation, privacy policy and source attribution. Do **not** claim that RibhLab is approved or activate ads until Google says Ready.
6. Keep GitHub Pages operational as an existing archive. Decide on 301 redirects, canonical duplication policy and article-by-article URL mapping **only after** Blogger publication and verification.

Official Blogger domain instructions: https://support.google.com/blogger/answer/1233387
Blogger / AdSense: https://support.google.com/adsense/answer/1269077

### Option B — use custom domain on existing GitHub Pages site (only if you choose GitHub as the main host)
1. Buy and verify a domain in your own account. Under GitHub repository `univcours/ribhlab-site` → Settings → Pages → Custom domain, enter the actual verified domain. GitHub Actions deployment (the current publication source) does **not** need a CNAME file in the repository.
2. For an **apex** root `YOUR-OWN-DOMAIN.com`, at the domain DNS registrar configure four A records: `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153` on `@`. Add `www` CNAME pointing to `univcours.github.io` — **not** `univcours.github.io/ribhlab-site`. Optional AAAA IPs are documented at GitHub.
3. Wait for GitHub Pages' green DNS check and enable **Enforce HTTPS**. Verify that the apex and `www` resolve correctly and the site's assets load under `https://YOUR-OWN-DOMAIN.com/ar/`.
4. ONLY AFTER verification, set GitHub Repository → Settings → Secrets and variables → Actions → **Variables**:
   - `RIBHLAB_SITE_URL = https://YOUR-OWN-DOMAIN.com`
   - Optional `GOOGLE_SITE_VERIFICATION = TOKEN_FROM_YOUR_SEARCH_CONSOLE` (the value of the HTML meta token, not an invented code).
   - Optional `ADSENSE_PUBLISHER_ID = ca-pub-XXXXXXXXXXXXXXXX` (only your **real** AdSense account's assigned ID).
5. On next push or manual workflow dispatch, the existing publishing workflow builds all Arabic, French and English routes, canonical URLs, OG URLs, robots.txt and sitemap for the **root domain**, not the old `/ribhlab-site/` subpath. No repository variable is currently set as part of this PR; by default the existing `github.io` URL remains unchanged.
6. Confirm `https://YOUR-OWN-DOMAIN.com/sitemap.xml`, `robots.txt`, `/ar/`, `/fr/`, `/en/`, then submit sitemap to Search Console.
7. For independent AdSense: AdSense → Sites → New site → type the root domain **without /ar/** → copy the owner-verification code or use your real publisher ID and request review. The build may insert the verified AdSense identification script **without enabling ads**. Actual ad placements remain turned off until approval; the codebase's `ENABLE_ADSENSE` default is `false`. With a validated publisher ID, `ads.txt` is generated by the build.
8. Never set `RIBHLAB_SITE_URL` before actual domain ownership/DNS. This changes HTML paths and canonical URLs; premature activation would break the current URL.

GitHub DNS/domain official: https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site
AdSense site verification: https://support.google.com/adsense/answer/12169212
AdSense `ads.txt`: https://support.google.com/adsense/answer/12171612

## Status/requirements checklist
- [x] Current GitHub Pages URL preserved until verified replacement exists.
- [x] Optional GitHub Actions custom-root URL and Google verification variables supported by source; checkout/ads off by default.
- [x] Static-site sitemap and multilingual canonical URLs are generated using the configured root URL.
- [ ] Domain actually registered in owner's registrar account (ownership **not proven**).
- [ ] Selected hosting destination confirmed (Blogger vs GitHub Pages).
- [ ] DNS added and validated; HTTPS ready.
- [ ] Google Search Console DNS or meta ownership verified.
- [ ] AdSense account/actual publisher ID supplied (none is presently configured).
- [ ] Content/policy readiness review and AdSense site review approved.
