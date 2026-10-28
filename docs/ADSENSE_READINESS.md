# RibhLab — Google AdSense launch checklist

**Last editorial/technical audit:** 27 October 2026

## Current factual status

- Public website: https://ribhlab.github.io/ (Arabic: /ar/, English: /en/, French: /fr/).
- Search Console property `https://ribhlab.github.io/` was confirmed as owner by the site operator with an HTML verification file. This is not proof that articles are indexed.
- The site currently holds **43 original article records**, each authored in Arabic, English and French (129 localized article views), with 282 generated indexed-route pages at the latest verified deploy.
- Public institutional employment section: https://ribhlab.github.io/ar/opportunities/competitions/. Selected and individually checked advertisements only; the government directory includes historical entries.
- Site policy pages: About, Editorial, Contact, Privacy, Terms and Disclaimer in all three languages.
- An editorial correction route is available at https://github.com/ribhlab/ribhlab.github.io/issues/new; no personal contact email is configured and none is invented.
- **AdSense publisher ID is configured:** `ca-pub-7832982742727178` (provided by owner via AdSense code). The owner has added `ribhlab.github.io` in the AdSense dashboard, but its status was **Examen requis** (review required) and not **Prêt** (approved).
- The site appears in the owner's AdSense Sites list. **Approval is not established**; the owner must complete the site connection/review process, and Google makes the decision. A separate payment-account verification banner is visible.

## What is preconfigured

- A valid `ca-pub-XXXXXXXXXXXXXXXX` publisher ID, when supplied, generates the owner-verification meta tag on the root homepage and all generated pages.
- It also generates `/ads.txt` at the site root:
  `google.com, pub-XXXXXXXXXXXXXXXX, DIRECT, f08c47fec0942fa0`
- The owner supplied the official AdSense loader script. It now loads in `<head>` of the bare root homepage and generated language pages while `enableAdsense=false`, using `adsenseVerificationScript=true`. **Loading this code sends requests to Google**, and after site approval it may serve Auto Ads if enabled in the Google dashboard. Keep Auto Ads disabled until compliant consent choices are configured.
- Quality gates verify `ads.txt`, the HTML owner meta, source-matched AdSense loader, multilingual privacy disclosures, and absence of manually inserted ad units before approval.
- The privacy policy discloses Google-server requests as soon as the verification loader is enabled, and addresses cookies/identifiers when advertising begins.
- `robots.txt`, `sitemap.xml`, canonical and hreflang routes are generated and tested on every publish.

## Steps for the publisher (no passwords in GitHub or chat)

1. Create/log in to your own AdSense account at https://www.google.com/adsense/start/.
2. In **AdSense > Sites > + New site**, submit `ribhlab.github.io` exactly as the AdSense site UI permits. Google alone determines whether the address/domain is supported and eligible.
3. Retrieve your real publisher ID `ca-pub-XXXXXXXXXXXXXXXX` from AdSense account settings. Never use a placeholder and never put an AdSense account password, security code or payment card details in the repo.
4. **Already implemented:** the owner-supplied ID is in `site.config.json`, with `adsenseVerificationScript=true` and `enableAdsense=false`. Do not create extra IDs. Optionally supply a real public editorial contact email via `RIBHLAB_CONTACT_EMAIL`.
5. Trigger **Actions > Publish RibhLab to GitHub Pages** on main (or save a reviewed change to main). Confirm that production succeeds and:
   - `https://ribhlab.github.io/ads.txt` shows the publisher account without mistakes
   - The page HTML includes `<meta name="google-adsense-account" content="ca-pub-...">`.
6. In AdSense > **Sites** > `ribhlab.github.io`, follow **Connectez votre site aux services AdSense**, confirm the script or ads.txt method, and use the available **Demander un examen / Request review** action. Do not claim success until Google marks the site **Prêt / Ready**. The user must complete buttons in their Google account.
7. Before displaying personalized ads to people in the EEA, UK or Switzerland, implement a Google-certified CMP using IAB TCF as required. Review local privacy rules and Google policies. Do not switch on ad delivery just to pass ownership checks.
8. **Important:** the verification loader already executes, so ensure **Auto Ads remain disabled inside AdSense** until required consent management (e.g., EEA/UK/Swiss Google-certified CMP) is in place; `enableAdsense=false` only prevents intentionally adding manual ad units and does not override Google-side Auto Ads configuration. After approval and consent, verify what Google is actually showing, adjust account settings and monitor Policy Centre and ads.txt.

## Important editorial safeguards

- Keep each article original, accurate, dated, useful, independently sourced where needed, and non-misleading.
- Employment ads must use original government/employer URLs, show precise application deadlines and never promise recruitment or immigration.
- Fix errors rapidly using the public correction channel, show the real operator's identity when available, and do not publish fictional audience analytics or income claims.
- Preserve Google Search Console verification and monitor indexing and crawl coverage.
- The presence of content and technical tags alone **does not guarantee AdSense approval**.

## Google primary documentation

- https://support.google.com/adsense/answer/12169212 (adding/validating/reviewing a site)
- https://support.google.com/adsense/answer/9724 (AdSense eligibility and original content)
- https://support.google.com/adsense/answer/12131223 (site approval and ads.txt)
- https://support.google.com/adsense/answer/13554116 (consent platform requirements)
