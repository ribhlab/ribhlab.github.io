# RivoScan — Google Play Console onboarding (verified 7 Nov 2026)

**Status:** Working checklist prepared from the source and a verified Play API inventory. **NOT** proof that App content declarations have been submitted. Do not choose/submit a legal or Data Safety answer without checking the **actual uploaded signed AAB v74**, rather than assuming newest source v99 matches.

## Actual Google Play state

- App: `com.ribhlab.rivoscan`.
- Saved AAB: `versionCode 74`, Internal Testing `completed`.
- Closed testing (`alpha`): v74 `draft`.
- Production: v74 `draft`; **not public**.
- Google Play has returned: **"Only releases with status draft may be created on draft app."** The app onboarding needs completion before an active closed-test release.
- Original owner-approved green Play Store icon was **committed through Google Play API** on 7 Nov 2026 at 16:46 UTC; default `en-US` icon. Feature graphic already green. Console display may need a refresh or Google review.
- Newer branch `univcours/ribhlab`, `feat/rivoscan-android-beta`, contains v0.44.23 (`versionCode 99`), but that signed bundle was **not** uploaded through GitHub; do not claim v99 is already published or use its unverified functionality as evidence for v74.

## Basic app information — ready to enter

| Field | Value / action | Confidence |
|---|---|---|
| App or game | **App** | Source-confirmed |
| Store category | **Productivity** | Source-confirmed |
| Default locale | **English (United States)** | Already configured in publishing source |
| Name | **RivoScan** | Source-confirmed; listing synchronization may need review |
| Website | https://ribhlab.github.io/rivoscan/ | Public site source exists |
| Support email | rachid022note4@gmail.com | Existing project support address |
| Privacy-policy URL | https://ribhlab.github.io/rivoscan/privacy/ | Public policy source file exists. Enter in Console App content and verify the live URL from a browser. |
| Ads declaration | **Yes, contains ads** unless the exact v74 package is verified not to contain/show advertising | Current Android source includes AdMob SDK and consent; avoid a false **No** |
| Government apps | **No**, based on current document-processing features | Source-based |
| Financial features | **My app doesn't provide any financial features**, based on current document-processing features | Source-based; verify any payment/banking additions in v74 |
| Health apps | **No health features**, based on current document-processing features | Source-based; Google still requires the form |
| News apps | **No**, based on current source | Source-based |
| Store listing screenshots | Existing 4 genuine Android emulator screenshots | Already present in Play API inventory; do not substitute marketing mockups |

## App access — examine exact v74 before selecting

Core scan/edit/export features require **no RivoScan account** in the current source. Optional document AI can require the user's own OpenAI API key and approval. In Play Console **App access**, verify whether *all functionality* can genuinely be accessed without extra credentials on the signed v74 build. If a promised feature is restricted, use the restricted-access option with accurate review instructions, rather than claiming no restrictions. Do **not** put your own OpenAI key into public documentation.

## Target audience — product decision, not an automatic age rating

The current RivoScan product positioning is an adult document utility. The provisional recommendation is **18+ only**, *if* this reflects the actual market and advertising design. Do not automatically mark it unless the owner confirms that the app intentionally targets adults rather than teenagers/students. The IARC regional content rating is assigned by IARC separately; **do not manually choose PEGI/ESRB ratings**.

## Content rating — answer by question meaning after checking v74

- Application, not a game (choose `All Other App Types` or closest non-game category).
- No built-in violent, sexual, gambling, controlled-substance or horror-themed content identified in the current source.
- Current source has **optional device-to-device WebRTC user-selected file transfers**; if present in v74, user-to-user content exchange is **Yes**, even without a public chat/feed.
- Current source includes optional AI-generated document answers; if present in v74 and the questionnaire asks about online/AI generated content, answer accordingly.
- Use developer contact `rachid022note4@gmail.com` for IARC only if this mailbox is monitored.
- See `RIVOSCAN-IARC-CONTENT-RATING-ANSWERS.md` for the detailed conditional questionnaire.

## Data Safety — **NEEDS SIGNED v74 BINARY + SDK BEHAVIOR AUDIT BEFORE SUBMISSION**

Do **not** select “no data collected” or “no data shared” automatically. Source includes or references:
- Google AdMob / User Messaging Platform: potentially ad IDs, coarse location inferred from IP, app/device data, ad interactions, diagnostic data, consent preferences.
- Google ML Kit model downloads and OCR/translation components: model download network metadata, depending on actual SDK.
- Optional OpenAI API: selected text/images/prompts sent after user approval, *if this feature is in v74*.
- Optional WebRTC and Google STUN: IP/network metadata and user-selected device-to-device document transfer, *if in v74*.
- User-selected photos/document storage and sharing to recipients; core PDF/OCR intended to process locally.

Cross-check collection, sharing, optionality, purpose, security, encryption in transit, retention, deletion and every third-party SDK against signed AAB v74. Google Play Data safety can be uploaded through the official CSV API **once a validated official full template is available**. No fabricated or incomplete CSV should be submitted.

## Permissions / sensitive access

Check the actual signed v74 AndroidManifest and runtime permission prompts for CAMERA, file/gallery selectors, notifications, network access and any sensitive/broad storage permission. Do not claim “no sensitive permissions” based on source alone.

## Play Console navigation

1. Go to **Policy and programs → App content** (or the dashboard's `Set up your app` links).
2. Enter **Privacy policy**, **App access**, **Ads**, then **Target audience and content** (Google requires those preliminary declarations), **Content rating**, **Data safety**, and **Government / Financial / Health apps** declarations. Mark each *submitted* only when Play Console shows saved/completed.
3. Complete the **Store settings** (App + Productivity, contact fields); verify original green icon and feature graphic.
4. In **Closed testing → Testers**, add the owner's consented email `hamidtawfiq2@gmail.com` via the Console's private testers list and save (not public GitHub). Testers must opt in using the invitation link.
5. Review **Closed Testing** v74 draft, meet all app-onboarding rules, then activate it for the qualified testers. Google refused API `completed` while the app remained a draft.
6. **Production** v74 is only a nonpublic draft. Request production access/complete testing and review when eligible. Prefer a newly signed/QA-tested v99 or newer app for public release rather than making the older v74 publicly available.

## Submission limitations

The connected GitHub automation can modify Play Store listing graphics/text and prepare tracks via Google Play API, but **cannot click Google Play Console questionnaires** or upload an individual's tester email list. Use ChatGPT **Work** with Cloud Browser and an authenticated Play Console session to complete the Console UI, or enter the above accurate values in the Console directly. Do not assert declarations are complete until the Console confirms it.

Google policy docs:
- https://support.google.com/googleplay/android-developer/answer/9859455
- https://support.google.com/googleplay/android-developer/answer/9867159
- https://support.google.com/googleplay/android-developer/answer/10144311
- https://support.google.com/googleplay/android-developer/answer/14738291
- https://support.google.com/googleplay/android-developer/answer/13849271
- https://developers.google.com/android-publisher/api-ref/rest/v3/applications/dataSafety
