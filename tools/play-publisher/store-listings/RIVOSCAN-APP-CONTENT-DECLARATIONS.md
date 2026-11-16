# Google Play App Content — RivoScan (`com.ribhlab.rivoscan`)

**Current verified Play API audit: 16 November 2026** — [GitHub audit 43782275213](https://github.com/ribhlab/ribhlab.github.io/actions/runs/43782275213).
Production **RivoScan 0.45.40 / versionCode 144 is completed**; signed original-key AAB was accepted by Google Play ([successful publish run 43781620385](https://github.com/ribhlab/ribhlab.github.io/actions/runs/43781620385)). The seven listing locales (English, Arabic, French, Spanish, German, Italian, Portuguese) each have valid title, short description and full description. Default language en-US, support email and support website are set. en-US store assets contain **1 icon, 1 Feature Graphic, 8 phone, 8 seven-inch tablet and 8 ten-inch tablet screenshots**. API detected **zero missing editable fields**. Contact phone is null (optional; owner has not provided a verified telephone number). Do not overwrite these already-complete fields just because a historic checklist says they were incomplete.

**Important:** Standard Android Publisher API cannot report the saved/accepted status of Play Console App Content questionnaires (privacy policy URL, IARC rating, target audience, app access, ads declaration, government/health/financial forms, app category or developer verification). Any statement about those being submitted or needing attention requires **Play Console → Policy and programs → App content → Needs attention / Actioned**, and **Store settings**. The API accepted an older Data Safety CSV on **7 Nov 2026** (HTTP 204, run 42401496716) based on old versionCode 74; this is **not** proof that declaration is up-to-date with v144. Only correct it after auditing final v144 SDKs and data handling. Do not guess or silently overwrite legal statements. Screenshots and all store branding are to be kept unchanged.

The table below is retained as a source-based checklist, but older "not uploaded" entries have been corrected against the live audit.
Only shared developer identity/contact is reused from NovaGrid. Do **not** copy NovaGrid's Data Safety and IARC answers blindly; the apps have different capabilities.

| Play Console item | Prepared value / recommendation | Evidence / blocker |
|---|---|---|
| App or game | **App** | Android scanner & PDF editor, not a game |
| Category | **Productivity** | Document scanning, OCR and PDF management |
| Default locale | **English (United States)** | Localized listing exists in EN/FR/AR |
| App website | https://ribhlab.github.io/rivoscan/ | Confirmed saved in Play API app details (2026-11-16); page source exists in GitHub Pages repo |
| Developer email | rachid022note4@gmail.com | Confirmed saved in Play API app details; contact phone is optional and currently absent |
| Privacy policy | https://ribhlab.github.io/rivoscan/privacy/ | Public RivoScan-specific HTML policy exists in site source; actual Play Console App content URL field status **not readable by Publishing API**, so check Console |
| Ads | **Yes / Contains ads** is the source-grounded answer; Console saved status **unverified** | Original-key v144 release build configured for live AdMob Banner and Interstitial placements; disclosure must match Play Console App content |
| Data Safety | **Earlier v74 declaration accepted by Play API (2026-11-07); review against current signed v144 required** | AdMob, Google ML Kit, OCR/model downloads, optional cloud AI and WebRTC networking. Cannot invent an updated answer or assume API acceptance equals Google policy approval |
| App access | **Core scanner does not require an account**, optional AI requires user's own API key and separate consent | Confirm whether reviewer must receive access instructions for any gated premium/AI tools |
| Target audience | **Ages 18 and over** — proposed sole age group; **not yet submitted in Play Console** | Professional document scanner with optional cloud AI and AdMob. Product is currently intended/marketed to adults, not children. Re-evaluate if the actual release or marketing is designed to target teenagers or children. |
| Content rating | **Prepared in [`RIVOSCAN-IARC-CONTENT-RATING-ANSWERS.md`](./RIVOSCAN-IARC-CONTENT-RATING-ANSWERS.md); not submitted in Play Console** | Core utility content: no bundled mature themes; **YES native user-to-user file exchange** via WebRTC; optional AI outputs must be considered |
| News | **No**, based on current project | Document tool, not news publisher |
| Government | **No**, based on current project | Not a government service |
| Financial features | **No**, based on current project | Document processing is not a financial service; confirm whether future features introduce financial functionality |
| Health features | **No**, based on current project | Document scanning is not a healthcare app |
| Sensitive permissions | **Needs final manifest verification** | Camera/storage selection, nearby data transfers, optional features; don't guess based on source-only branches |
| Screenshots | **Present in Play API (8 phone + 8 7-inch + 8 10-inch)** | Live audit 2026-11-16. Browser-rendered genuine app UI; do not claim native physical-device screenshots. Feature Graphic and icon also each present |
| AAB | **Signed v0.45.40 / code144 accepted and assigned to Production** | Original upload certificate checked; test alpha and Production API commits succeeded at 00:40 UTC, 16 Nov 2026 |
| Public release | **Production API edit committed with status completed (v144)** | Google review/visibility and owner App Content checklist require Console verification |

## Target audience — selected recommendation (6 November 2026)

**Play Console → Policy → App content → Target audience and content → Start → Target age:**
select **18 and over** *only*. Do **not** select 5 and under / 6–8 / 9–12 / 13–15 / 16–17, because the current RivoScan release is designed and presented as a professional document utility rather than a children’s app. This is a product audience selection, not the IARC content rating.

**Restrict minor access:** Google's option is separate from choosing the 18+ audience; do not enable an additional account-age restriction automatically. Decide separately if the product must block all minors. Google can review whether stated audience matches actual UI, store assets, marketing and app behavior. If teenage/student usage is explicitly targeted in the future, update the declared groups and privacy/ad compliance rather than retaining an inaccurate 18+ declaration.

**Submission state:** prepared in this file only. The Google Play Developer API currently used for store listings does not submit this App content form. A Play Console user must select the group and press **Save**. Do not mark the declaration as submitted until Play Console confirms it.

Sources: https://support.google.com/googleplay/android-developer/answer/9867159 and https://support.google.com/googleplay/android-developer/answer/18265346.

## What can be done via Google Play Developer API

- Localized listing titles, short/long descriptions and genuine icon (edits).
- Public app details such as default language and support website/email (edits).
- Data Safety CSV can be written using `applications.dataSafety` **only after** the official, complete Google Play CSV declaration is audited. API write is not a license to invent answers.

## Console-only declarations

The App content page has questionnaires/declarations for ads, content rating, target audience, app access, privacy policy URL, sensitive permissions, and other applicable programs. The Publishing API cannot generically fill all Console questionnaires. Complete those screens using this evidence after checking the signed release's manifest and SDK behavior.

## Discrepancies preventing automatic Data Safety declaration

The original RivoScan `apps/rivoscan/public/privacy.html` states “no ads, ... cloud AI” for an early beta. Newer `src/monetization.js` includes AdMob and `src/document-ai.js` sends user-selected content to an external AI provider after consent. An accurate release needs the RivoScan-specific policy, updated app disclosure and matching signed-binary tests.
