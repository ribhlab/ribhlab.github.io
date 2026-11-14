# RibhLab — Google AdSense launch checklist

**AdSense publisher enabled in website configuration:** 30 October 2026

## Current factual status

- Public website: https://ribhlab.github.io/ (Arabic: /ar/, English: /en/, French: /fr/).
- Google Search Console property `https://ribhlab.github.io/` was directly confirmed as **siteOwner** by the authorized `rachid022note4@gmail.com` OpenSEO connection on 14 November 2026. At the time of the Google URL Inspection check, six tested pages were **URL is unknown to Google** and Search Analytics recorded **zero impressions and clicks** over the available Oct 27–Nov 11 time window. Submission of the sitemap does not prove it has been processed.
- As of 14 November 2026, the source contains **95 trilingual editorial article records**. An automated evidence-and-substance gate currently clears **61 records** for indexing, while **34 remain accessible but `noindex` and do not load the AdSense script** until their missing references, depth or translations are genuinely improved. This is a site-owned editorial gate, not a fixed Google article-length requirement.
- Public institutional employment section: https://ribhlab.github.io/ar/opportunities/competitions/. Selected and individually checked advertisements only; the government directory includes historical entries.
- Site policy pages: About, Editorial, Contact, Privacy, Terms and Disclaimer in all three languages.
- An editorial correction route is available at https://github.com/ribhlab/ribhlab.github.io/issues/new; this is a **public GitHub Issues channel**, not confidential email. No private contact address has been approved for public publication. A private editorial/privacy contact remains an uncompleted owner-facing trust improvement.
- **AdSense publisher ID is configured:** `ca-pub-7945572016731367` (owner supplied). An 11/12 November AdSense rejection email was generic and did not provide a specific policy-code reason. The actual **AdSense > Sites > Needs attention > Details** state remains unverified directly; do not infer that any one risk listed here was the rejection reason.
- The site appears in the owner's AdSense Sites list. **Approval is not established**; the owner must complete the site connection/review process, and Google makes the decision. A separate payment-account verification banner is visible.

## What is preconfigured

- A valid `ca-pub-XXXXXXXXXXXXXXXX` publisher ID, when supplied, generates the owner-verification meta tag on the root homepage and all generated pages.
- It also generates `/ads.txt` at the site root:
  `google.com, pub-XXXXXXXXXXXXXXXX, DIRECT, f08c47fec0942fa0`
- The owner-supplied AdSense verification script is now limited to substantial language homepages and editorial articles that pass source-and-content checks. It is **not** added to legal pages, tools, games, archives, recipe indexes, templated recipes or `noindex` articles. Publisher meta/`ads.txt` still establish ownership. **Loading the script sends requests to Google**, and after approval it may serve Auto Ads if enabled inside AdSense. Keep Auto Ads disabled until compliant consent choices are configured.
- Quality gates verify `ads.txt`, ownership metadata, script placement, multilingual privacy disclosures, absence of manual ad units, **zero AdSense loader on ineligible pages**, unique content metadata, and the actual public sitemap fetched with a Googlebot-style user-agent. Failure or warning of a check never itself establishes eligibility for AdSense.
- The privacy policy discloses Google-server requests as soon as the verification loader is enabled, and addresses cookies/identifiers when advertising begins.
- `robots.txt`, `sitemap.xml`, canonical and hreflang routes are generated and tested on every publish. A first-party Search Console screenshot on 14 November reported **Impossible de lire le sitemap** even though independent HTTPS tests returned `200` and valid XML. The exact Google-side reason remains unresolved. Subsequent monitoring must compare Google processing, not simply 'Sitemap envoyé'.

## Steps for the publisher (no passwords in GitHub or chat)

1. Create/log in to your own AdSense account at https://www.google.com/adsense/start/.
2. In **AdSense > Sites > + New site**, submit `ribhlab.github.io` exactly as the AdSense site UI permits. Google alone determines whether the address/domain is supported and eligible.
3. Retrieve your real publisher ID `ca-pub-XXXXXXXXXXXXXXXX` from AdSense account settings. Never use a placeholder and never put an AdSense account password, security code or payment card details in the repo.
4. **Already implemented:** the owner-confirmed ID is in `site.config.json`, with `adsenseVerificationScript=true` and `enableAdsense=true`. GitHub Pages publishing reads the publisher ID from this file (not a potentially stale `RIBHLAB_ADSENSE_PUBLISHER_ID` Actions variable). Do not create extra IDs. Optionally supply a real public editorial contact email via `RIBHLAB_CONTACT_EMAIL`.
5. Trigger **Actions > Publish RibhLab to GitHub Pages** on main (or save a reviewed change to main). Confirm that production succeeds and:
   - `https://ribhlab.github.io/ads.txt` shows the publisher account without mistakes
   - The page HTML includes `<meta name="google-adsense-account" content="ca-pub-...">`.
6. In AdSense > **Sites** > `ribhlab.github.io`, follow **Connectez votre site aux services AdSense**, confirm the script or ads.txt method, and use the available **Demander un examen / Request review** action. Do not claim success until Google marks the site **Prêt / Ready**. The user must complete buttons in their Google account.
7. Before displaying personalized ads to people in the EEA, UK or Switzerland, implement a Google-certified CMP using IAB TCF as required. Review local privacy rules and Google policies. Do not switch on ad delivery just to pass ownership checks.
8. **Important:** the verification loader already executes, so ensure **Auto Ads remain disabled inside AdSense** until required consent management (e.g., EEA/UK/Swiss Google-certified CMP) is in place; `enableAdsense=true` enables website-side ad readiness but does not grant approval or control Google-side Auto Ads configuration. No manual ad slots are inserted until reviewed and appropriately configured. After approval and consent, verify what Google is actually showing, adjust account settings and monitor Policy Centre and ads.txt.

## Revised AdSense quality intervention — 14 November 2026

- Removed the entire skin-care section and nine affected source articles, with a publishing guard against reintroduction.
- Retired **120 generated recipe details × three languages (360 pages)** from the indexable sitemap until their three locale-specific cooking methods are independently rewritten. Recipes remain browseable and useful as a reference, but the same templated actions cannot be described as 120 original independently edited tutorials.
- Retired **34 / 95 editorial records** from indexing and ad loading until they have at least two credible attributed HTTPS references, four meaningful localized sections and sufficient genuinely explanatory material in all three languages. The internal 300-word threshold is an editorial triage tool, **not a Google policy requirement**. Do not fabricate citations, add filler, or pretend translations were reviewed to clear it.
- Repaired nested `<main>` landmark elements in recipe and opportunity templates, corrected public contact/privacy/editorial statements and linked article author bylines to real published editorial standards.
- The remaining risks requiring verified real-world action are the precise AdSense Sites/Policy Centre rejection details, the Google-side sitemap processing state, private editorial contact and a Google-certified CMP/appropriate consent before regional ad delivery. External image rights and originality also need ongoing source review; unique licensing metadata alone does not establish original creation.

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

## 30 October 2026 activation request

- Website owner explicitly requested enabling Google AdSense on RibhLab.
- `site.config.json` now has `enableAdsense=true`; the GitHub Pages workflow no longer overrides it with `RIBHLAB_ENABLE_ADSENSE=false`.
- The configured publisher is `ca-pub-7945572016731367`, and the auto-generated `ads.txt` entry remains unchanged.
- This is **website-side activation only**: AdSense Site approval/Ready status, Auto Ads choice, consent management, and payout verification belong to Google settings and cannot be confirmed by GitHub builds.
- Do not assume ads are earning or displayed before approval; respect certified CMP requirements where applicable.
