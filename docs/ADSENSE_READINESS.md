# RibhLab — Google AdSense launch checklist

**Last editorial/technical audit:** 27 October 2026

## Current factual status

- Public website: https://ribhlab.github.io/ (Arabic: /ar/, English: /en/, French: /fr/).
- Search Console property `https://ribhlab.github.io/` was confirmed as owner by the site operator with an HTML verification file. This is not proof that articles are indexed.
- The site currently holds **43 original article records**, each authored in Arabic, English and French (129 localized article views), with 282 generated indexed-route pages at the latest verified deploy.
- Public institutional employment section: https://ribhlab.github.io/ar/opportunities/competitions/. Selected and individually checked advertisements only; the government directory includes historical entries.
- Site policy pages: About, Editorial, Contact, Privacy, Terms and Disclaimer in all three languages.
- An editorial correction route is available at https://github.com/ribhlab/ribhlab.github.io/issues/new; no personal contact email is configured and none is invented.
- **AdSense publisher ID is not yet configured; ads are OFF.**
- There is no evidence the site has been submitted to or approved by Google AdSense. Do not describe it as approved or guarantee eligibility.

## What is preconfigured

- A valid `ca-pub-XXXXXXXXXXXXXXXX` publisher ID, when supplied, generates the owner-verification meta tag on the root homepage and all generated pages.
- It also generates `/ads.txt` at the site root:
  `google.com, pub-XXXXXXXXXXXXXXXX, DIRECT, f08c47fec0942fa0`
- **The AdSense script does not run until explicitly enabled.** This intentionally separates ownership verification from ad delivery.
- Quality gates verify that `ads.txt`, the HTML owner meta, and policy disclosures agree with the configured publisher ID, and that no live ad script is included when not enabled.
- The privacy policy automatically gains a Google-advertising disclosure if and when ads are enabled.
- `robots.txt`, `sitemap.xml`, canonical and hreflang routes are generated and tested on every publish.

## Steps for the publisher (no passwords in GitHub or chat)

1. Create/log in to your own AdSense account at https://www.google.com/adsense/start/.
2. In **AdSense > Sites > + New site**, submit `ribhlab.github.io` exactly as the AdSense site UI permits. Google alone determines whether the address/domain is supported and eligible.
3. Retrieve your real publisher ID `ca-pub-XXXXXXXXXXXXXXXX` from AdSense account settings. Never use a placeholder and never put an AdSense account password, security code or payment card details in the repo.
4. In GitHub: **ribhlab/ribhlab.github.io > Settings > Secrets and variables > Actions > Variables**, set `RIBHLAB_ADSENSE_PUBLISHER_ID` to the real ID. Optionally set `RIBHLAB_CONTACT_EMAIL` to a public email belonging to your editorial team.
5. Trigger **Actions > Publish RibhLab to GitHub Pages** on main (or save a reviewed change to main). Confirm that production succeeds and:
   - `https://ribhlab.github.io/ads.txt` shows the publisher account without mistakes
   - The page HTML includes `<meta name="google-adsense-account" content="ca-pub-...">`.
6. In AdSense, validate the site and **request the official review**. Do not claim success until Google marks the site **Ready**.
7. Before displaying personalized ads to people in the EEA, UK or Switzerland, implement a Google-certified CMP using IAB TCF as required. Review local privacy rules and Google policies. Do not switch on ad delivery just to pass ownership checks.
8. After actual approval *and any necessary compliant consent controls are installed*, explicitly set `RIBHLAB_ENABLE_ADSENSE=true`, review placements and republish. Continue monitoring policy centre and ads.txt status.

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
