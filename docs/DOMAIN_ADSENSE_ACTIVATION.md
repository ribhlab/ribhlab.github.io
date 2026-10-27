# RibhLab — Independent domain + Google AdSense activation playbook

*Prepared: 27 October 2026. Current production deliberately remains at https://univcours.github.io/ribhlab-site/ until **the owner purchases, verifies and configures a domain**. Nothing in this PR transfers domain ownership, buys a domain, or claims AdSense approval.*

## A. Domain decision

**First choice: `ribhlab.com`**, if an actual registrar checkout confirms registration is available at a reasonable renewal price. Alternatives to check: `ribhlab.net`, `ribhlabhub.com`, `ribhlabstudio.com`. None is represented as confirmed available or owned. The domain must be held in the owner's own registrar account.

Use a standard personally owned second-level domain. For normal AdSense signup, enter the registered domain, **not** `univcours.github.io/ribhlab-site/` (which contains a path) and not a free third-party subdomain. A custom `.com` helps with ownership and presentation but **does not guarantee AdSense acceptance**.

Before purchase: check spelling, current availability, annual renewal and tax, WHOIS privacy, access to DNS and DNSSEC, registrar reputation and trademarks. Don't buy lookalike brands. Registrars: [Namecheap](https://www.namecheap.com/domains/) and [Porkbun](https://porkbun.com/). These are examples, not ads or endorsements.

## B. Connect owned domain to GitHub Pages — ONLY after purchase

1. From the registrar, confirm actual ownership and control of the DNS zone. Keep the old GitHub Pages domain publishing until the new domain is provisioned.
2. Follow [GitHub's custom domain verification instructions](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/verifying-your-custom-domain-for-github-pages) to publish the TXT record that GitHub supplies under the registrar DNS zone. **Use GitHub's actual verification token**, not a fabricated example.
3. In `univcours/ribhlab-site` → **Settings → Pages → Custom domain**, enter the actual domain (e.g. `ribhlab.com`) and Save **before** changing DNS records, as GitHub recommends to avoid subdomain takeover.
4. If using **apex** `ribhlab.com` as canonical, create these A records for host `@` (remove conflicting apex A/AAAA/ALIAS records):
   
   ```
   @  A  185.199.108.153
   @  A  185.199.109.153
   @  A  185.199.110.153
   @  A  185.199.111.153
   ```
   
   Optional GitHub documented IPv6 AAAA records:
   
   ```
   @  AAAA  2606:50c0:8000::153
   @  AAAA  2606:50c0:8001::153
   @  AAAA  2606:50c0:8002::153
   @  AAAA  2606:50c0:8003::153
   ```
   
   To support `www` alongside it, create `www  CNAME  univcours.github.io`. **Do not use wildcard DNS**. If the registrar uses Cloudflare, initially set relevant DNS records to **DNS only** until GitHub's certificate provision is complete.
5. In repository **Settings → Secrets and variables → Actions → Variables**, set **`RIBHLAB_SITE_URL` to `https://ribhlab.com`** (use the ACTUAL purchased, configured domain if different). This is not a secret; it is the canonical public site URL.
6. Rerun the existing GitHub Pages deployment from Actions or push a normal content change to `main`. The existing build reads `RIBHLAB_SITE_URL`, and generates root-relative assets, canonical URLs, translated pages, `sitemap.xml`, `robots.txt`, search indexes and `ads.txt` for the new domain. Note: GitHub Actions publishing may ignore a `CNAME` file; the domain must be configured in **Settings → Pages**.
7. Wait for DNS propagation and GitHub SSL certificate; use **Enforce HTTPS** only once enabled. Confirm:
   - `https://ribhlab.com/ar/`, `/en/`, `/fr/`, `/tools/document-studio/`, `/markets/`.
   - Main navigation, article images, CSS, Google `robots.txt` and `sitemap.xml` return successfully with no repo-prefixed `/ribhlab-site/` paths.
   - `https://www.ribhlab.com/` redirects to canonical domain.
   - Search Console ownership is verified by DNS (Domain property); resubmit `https://ribhlab.com/sitemap.xml` and maintain redirects from prior URLs where possible.

**Do not switch `RIBHLAB_SITE_URL` before DNS and Pages ownership are ready**, or visitors/search engines may receive broken canonical URLs and links.

## C. AdSense: free preparation first, never promise approval

Google's rules require owning the HTML/source, original helpful content, policy compliance, crawlable pages, consistent site navigation, and final site review. Creating a standard custom domain **does not itself approve monetization**.

1. In your actual [Google AdSense account](https://www.google.com/adsense/), add the **apex registered domain** (e.g. `ribhlab.com`) to **Sites**.
2. In the same repository **Actions → Variables**, add `RIBHLAB_ADSENSE_PUBLISHER_ID` with your own actual `ca-pub-1234567890123456` account ID. Never use a sample ID. The site build automatically places the official ownership `<meta name="google-adsense-account" content="ca-pub-...">` inside every page's `<head>`, plus an `ads.txt` in the site root, while **ads remain disabled** by default.
3. Keep `RIBHLAB_ENABLE_ADSENSE=false` (or leave unset) throughout review. The root-domain build is ready to generate AdSense `ads.txt` and HTML verification, but no ad units run until explicitly enabled.
4. Confirm actual deployed `https://ribhlab.com/ads.txt` contains **your** `pub-` ID, and view the HTML source to confirm the meta verification tag; then submit AdSense site verification and click **Request review**.
5. In Search Console, verify the Domain property via a Google-supplied TXT DNS value. Validate indexability and investigate crawl, mobile layout, original content, sensitive content, missing contact/policy information, broken links and excessive external/affiliate content. AdSense's quality review is independent of GitHub CI.
6. **Only after the AdSense Sites status explicitly reads 'Ready'**, set the GitHub Actions variable `RIBHLAB_ENABLE_ADSENSE=true` and trigger redeployment. The ad loader is then emitted on pages; comply with Google's required consent management controls for relevant users and local laws. Keep the value `false` if status is not Ready.
7. Review traffic, ads.txt status, Policy Center alerts, and content quality regularly. Do not click your own ads or generate artificial traffic.

No AdSense Publisher ID, registrar login, proof of domain ownership, or approved AdSense status has been supplied to the assistant, so **no registrar transaction, DNS mutation or actual Google account linkage has been performed**. Never present the site as approved before Google's confirmation.

## D. Safety gate: rollback

If the new domain or certificate fails, leave or return `RIBHLAB_SITE_URL` to `https://univcours.github.io/ribhlab-site`, keep `RIBHLAB_ENABLE_ADSENSE=false`, restore GitHub Pages settings as needed and rerun the deploy workflow. The old static generator supports the original project prefix. Do not point unowned domain DNS to the repository.

## References

- [Google AdSense: enter a valid site URL](https://support.google.com/adsense/answer/2784438)
- [Google AdSense: connect a site and add meta tag](https://support.google.com/adsense/answer/7584263)
- [Google AdSense: readiness requirements](https://support.google.com/adsense/answer/12176698)
- [GitHub Pages: managing a custom domain](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site)
- [GitHub Pages: HTTPS DNS records](https://docs.github.com/en/pages/getting-started-with-github-pages/securing-your-github-pages-site-with-https)
