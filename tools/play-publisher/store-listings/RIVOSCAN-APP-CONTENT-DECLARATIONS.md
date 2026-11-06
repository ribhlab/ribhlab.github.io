# Google Play App Content — RivoScan (`com.ribhlab.rivoscan`)

Status: **implementation evidence reviewed; declarations not submitted from Console**.
Only shared developer identity/contact is reused from NovaGrid. Do **not** copy NovaGrid's Data Safety and IARC answers blindly; the apps have different capabilities.

| Play Console item | Prepared value / recommendation | Evidence / blocker |
|---|---|---|
| App or game | **App** | Android scanner & PDF editor, not a game |
| Category | **Productivity** | Document scanning, OCR and PDF management |
| Default locale | **English (United States)** | Localized listing exists in EN/FR/AR |
| App website | https://ribhlab.github.io/rivoscan/ | RibhLab website app landing page |
| Developer email | rachid022note4@gmail.com | Shared public NovaGrid developer support contact |
| Privacy policy | https://ribhlab.github.io/rivoscan/privacy/ | RivoScan-specific policy; must be entered under App content in Console |
| Ads | **Yes / Contains ads (preliminary based on source)** | `src/monetization.js` includes Google AdMob SDK and ad displays, but with test IDs. Recheck final signed AAB and turn off test IDs before public monetization |
| Data Safety | **Not submitted — must audit final signed AAB and SDKs** | AdMob, Google ML Kit, Tesseract language pack fetch, user-triggered OpenAI API, WebRTC STUN. Cannot declare “no data collected” from source alone |
| App access | **Core scanner does not require an account**, optional AI requires user's own API key and separate consent | Confirm whether reviewer must receive access instructions for any gated premium/AI tools |
| Target audience | **Ages 18 and over** — proposed sole age group; **not yet submitted in Play Console** | Professional document scanner with optional cloud AI and AdMob. Product is currently intended/marketed to adults, not children. Re-evaluate if the actual release or marketing is designed to target teenagers or children. |
| Content rating | **Prepare productivity/document utility answers, not NovaGrid game answers** | IARC responses must match actual features and access to user content |
| News | **No**, based on current project | Document tool, not news publisher |
| Government | **No**, based on current project | Not a government service |
| Financial features | **No**, based on current project | Document processing is not a financial service; confirm whether future features introduce financial functionality |
| Health features | **No**, based on current project | Document scanning is not a healthcare app |
| Sensitive permissions | **Needs final manifest verification** | Camera/storage selection, nearby data transfers, optional features; don't guess based on source-only branches |
| Screenshots | **Not available as verified store-ready captures** | Need genuine on-device captures of current release |
| AAB | **First signed bundle must be uploaded/saved in Play Console** | Latest GitHub AAB artifact was named UNSIGNED; not release-ready |
| Public release | **Not authorized by this checklist** | Google review, account-specific testing and developer declaration requirements remain |

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
