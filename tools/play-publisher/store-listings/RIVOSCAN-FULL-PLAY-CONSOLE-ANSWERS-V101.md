# RivoScan — Complete Google Play declarations and release status

**Audit date:** 2026-11-07. **Application:** `com.ribhlab.rivoscan`.

## Important: actual submission status, not a promise

- **Confirmed through Google Play API:** `Data Safety` CSV payload accepted with HTTP 204 on 2026-11-07 18:29 UTC ([run](https://github.com/ribhlab/ribhlab.github.io/actions/runs/42401496716)); green Play Store icon committed; **Internal v74 completed**, **Closed v74 draft**, **Production v74 draft**.
- **App details (support email/site/default language):** managed separately by `rivoscan-complete-app-details.yml` and only considered complete if its actual API job succeeds.
- **NOT CONFIRMED IN GOOGLE PLAY CONSOLE:** IARC content rating, App access, Target Audience, Ads, Advertising ID, government/financial/health forms, app category, specific permissions, trader status. Screenshots from the user show some answers chosen, not confirmed submitted.
- **New source revision:** `univcours/ribhlab` branch `feat/rivoscan-android-beta` release `0.44.25` with **versionCode 101** and a corrected packaged privacy policy, approved original green icon, production-only AdMob IDs. This is NOT the uploaded signed AAB; GitHub AABs are unsigned until the ORIGINAL Play upload keystore is configured.

## Copy-ready App Content answers, grounded in v74 and current source

| Google Play Console setting / exact question | Recommended response | Scope / evidence |
|---|---|---|
| Application type | **App** | Document scanner and PDF toolkit |
| Store category | **Productivity** | Main app purpose |
| App display title | **RivoScan** | Source application ID and listing |
| Contact email | `rachid022note4@gmail.com` | Public RibhLab support channel |
| Contact website | https://ribhlab.github.io/rivoscan/ | Existing site |
| Privacy policy URL | https://ribhlab.github.io/rivoscan/privacy/ | Current externally hosted policy; v74 embedded policy was out of date |
| Ads / Does your app contain ads? | **Yes** | AdMob SDK included in v74 and v101 |
| Advertising ID / Does your app use advertising ID? | **Yes** | AD_ID manifest permission shown by user and AdMob SDK |
| Advertising ID purpose / Advertising or marketing | **Yes** | Ad serving, targeting and measurement |
| Advertising ID purpose / Analytics | **Yes if the installed SDK processes advertising ID for analytics** | Google Mobile Ads SDK declares analytics as a data-processing purpose; check integrated SDK |
| Advertising ID purpose / Fraud prevention | **Yes if the installed SDK processes advertising ID for fraud prevention** | Google Mobile Ads SDK declares fraud prevention |
| Advertising ID purpose / App functionality, developer communications, account management | **No** | No source evidence of those additional purposes |
| Advertising ID purpose / Personalization | **No**, unless this describes non-ad app content personalization with Advertising ID | Ad targeting is covered by advertising/marketing |
| App access / Is any part restricted? | **Yes** | v74 optional cloud AI requires a user-supplied OpenAI API key; some advanced v74 tools are gated behind demo rewarded ads |
| App access / reviewer instructions | **Basic scanning, PDF editing, OCR and file tools work without a RivoScan account. Optional 'AI Chat with Document' and 'Solver AI' require a user-provided OpenAI API key and per-request consent. v74 advanced tools require an optional rewarded test ad. Please review the unrestricted document tools without a login; for AI-only review use privately provided limited-use test credentials. No developer API key is bundled.** | Do NOT put a working API key into GitHub or a public listing. If Google requires full access, provide a controlled temporary credential privately inside the review form |
| Target audience | **18 and over** *(sole age group, if this reflects the owner's actual target market and marketing)* | Professional scanner/AdMob/optional API-funded AI; audience choice, NOT IARC rating |
| Restrict minor access | Leave **unchecked** unless a product/legal decision explicitly requires barring minors from Play | Optional setting distinct from intended audience |
| Designed for Families | **No**, if app is not designed for children | Professional utility |
| Government app | **No** | No government product or affiliation |
| Financial features | **App does not provide financial features** | Processing PDF invoices does not constitute banking/lending/crypto |
| Health features | **No health features** | Not a healthcare app |
| News app | **No** | Not a publisher |
| Data Safety | **Already submitted via API; see exact reviewed v74 CSV** | API HTTP 204 is not policy approval |
| Data Safety / Does app collect or share user data? | **Yes** | AdMob SDK and optional cloud AI |
| Data Safety / All user data encrypted in transit? | **No, conservatively for v74** | STUN may disclose IP/network metadata outside TLS; do not mark Yes without actual release network assessment |
| Data Safety / Account creation | **My app does not allow users to create an account** | OpenAI API key is external and optional, not in-app account |
| Data Safety / Users log in with outside accounts? | **No** | No RivoScan login/OAuth |
| Data Safety / Users may request deletion? | **No**, until an operational data deletion mechanism is verified | Local user deletion does not prove external SDK/provider deletion within requested period |

## Complete IARC content-rating questionnaire for All Other App Types

**Contact email:** `rachid022note4@gmail.com`; **Category:** `All Other App Types`.

| IARC question | Answer | Rationale |
|---|---|---|
| Downloaded App / Included age-relevant violent, sexual or offensive assets | **No** | No curated mature-themed content in scanned source |
| User Content Sharing / Native exchange of images, audio, messages or other content | **Yes** | WebRTC peer file transfer is in v74 source |
| Shared user-generated content primary source | **No** | App primarily creates/edits local PDFs |
| Permit public sharing of nudity | **No** | No public feed; private peer transfer only |
| Permit public sharing of graphic real-world violence | **No** | No public feed |
| Block users or user-generated content | **No** | No in-app user moderation/blocking system |
| Report users or user-generated content | **No** | No in-app social reporting system |
| Chat moderation | **No** | No peer chat platform |
| Interactions can be limited to invited friends | **Yes, subject to how Play interprets pair-by-code transfers** | Two parties must privately exchange WebRTC session offer/answer codes; no discovery directory |
| Online Content, including AI-generated answers | **Yes** | BYOK OpenAI Responses API |
| Violence | **No** | No curated violence |
| Sexuality | **No** | No curated sexual content |
| Language (offensive language) | **No** | Utility UI does not provide curated profanity |
| Controlled substances | **No** | No app content focused on drugs |
| Promotion/sale of age-restricted products | **No** | No gambling, tobacco, alcohol or weapons sales |
| User precise location shared with others | **No** | No GPS social broadcast feature |
| Purchase digital goods | **No** | v74 reward-video access is not paid Play Billing, v101 has no reward gate |
| Cash prizes / gift cards / play-to-earn / transferable crypto assets | **No** | No such rewards |
| General web browser or search engine | **No** | Fixed-purpose app and AI endpoint |
| Primarily news or educational product | **No** | Primary purpose is document scanning/editing, even with optional math solver |

IARC regional ages must be calculated by Google/IARC; do not invent them.

## Submission vs source: important limitations

- This document is complete **source-grounded guidance**, **NOT** proof that every Play Console UI form has been clicked/saved. The standard Android Publisher v3 API supports store metadata, release tracks, image assets and Data Safety CSV, but **does not expose a generic Play Console App Content questionnaire write** for this first-party store listing. The similarly named `appstoreappsreview` API is only for **third-party app stores** registered through the Third-party app store on Play program, **not** normal Google Play Console apps.
- Importing a Data Safety CSV or writing it by API replaces all previous answers, so do not re-run for future v101 AAB without comparing SDKs and native permissions.
- A signed AAB must be created with the existing Google Play **upload key**, not a newly invented keystore. GitHub Actions can sign it automatically once the four `RIVOSCAN_PLAY_*` repository secrets are added safely via `setup-rivoscan-play-signing.ps1 -ExistingKeystore <local path>`.
- Only the owner or an authenticated Play Console browser session can complete the IARC questionnaire, target ages, app access details and other UI-only policy forms. There is **no justification to claim those forms are submitted until Console confirms it**.
- Keep Production as a **draft**, and only release updated v101 publicly after signing, review, actual opted-in testers/production access when applicable.

## References

- https://developers.google.com/android-publisher/api-ref/rest/v3/applications/dataSafety
- https://developers.google.com/android-publisher/api-ref/rest/v3/edits.details
- https://developers.google.com/android-publisher/app-store-review (only third-party stores)
- https://support.google.com/googleplay/android-developer/answer/9859655
- https://support.google.com/googleplay/android-developer/answer/9867159
- https://developers.google.com/admob/android/privacy/play-data-disclosure
- https://support.google.com/googleplay/android-developer/answer/9842756
