# RivoScan — IARC / Google Play Content Rating questionnaire

**App**: RivoScan • Android PDF Scanner & Editor  
**Package**: `com.ribhlab.rivoscan`  
**Prepared**: 2026-11-06  
**State**: ANSWERS PREPARED FROM SOURCE; NOT ENTERED OR SUBMITTED IN PLAY CONSOLE.  
**Source**: `univcours/ribhlab`, branch `feat/rivoscan-android-beta`; especially `apps/rivoscan/src/file-transfer.js`, `document-ai.js`, `ai-provider.js`, `monetization.js`, `main.js`, `package.json`.

## Entry fields

- **IARC contact email**: `rachid022note4@gmail.com` — the existing published RibhLab/NovaGrid developer support address. Check that this mailbox is monitored for rating-authority correspondence.
- **App category inside the IARC questionnaire**: **All Other App Types** (or the closest non-game app / utility category as displayed).
- **Store category** (different setting): **Productivity**.
- **Target audience setting** (different form): **18 and over** only, according to current RivoScan product targeting. This is NOT the eventual IARC content-rating value.

## Suggested content answers for the current RivoScan source

These answer *question meanings*, not a guessed exact screen order. The exact IARC wording and any conditional follow-ups must be checked in the live Console.

| IARC topic / question meaning | Answer | Basis and boundary |
|---|---|---|
| Violence, blood, gore or disturbing violent imagery **provided as app content** | **No** | RivoScan is a PDF/camera tool; no built-in violent media was found |
| Sexual acts, nudity or sexual themes **provided as app content** | **No** | Not a built-in content category |
| Profanity, crude humor or offensive language **provided by the app** | **No** | Utility interface; arbitrary user-loaded documents are not bundled editorial content |
| Drugs, alcohol, tobacco, controlled-substance references **provided by the app** | **No** | No such themed content by design |
| Gambling, gambling simulation or real-money betting | **No** | Document-scanning app, no gambling or betting features |
| Fear, horror or shocking imagery as curated content | **No** | No built-in horror content |
| Does the app natively allow users to **communicate/exchange their own content with other users?** | **YES** | `src/file-transfer.js` creates native WebRTC data channels and transfers user-selected files to another device. Google explicitly says native file/content exchange qualifies even without a public social network |
| Does the app publish files to a public feed or support public comments? | **No — based on reviewed source** | Device-to-device transfer is direct and optional, not a public feed |
| Does the app share/display a user's current precise location to other app users? | **No — based on reviewed source** | No app map or location-sharing feature. Note: WebRTC/STUN can expose network IP metadata; disclose this separately in privacy/data safety |
| Does the app offer **unrestricted internet browsing/search**, e.g. a browser or search engine? | **No** | Fixed-purpose model/download endpoints and selected AI provider are not a general browser |
| Does the app sell digital goods through in-app purchases / randomized paid items? | **No — for current source** | Premium tools use optional *rewarded advertising*, not a Play Billing purchase; no randomized purchases verified |
| Are there advertisements in the app? | **Yes — on the separate Play Console Ads declaration** | `src/monetization.js` integrates AdMob; development units can be demos but SDK and ad flow exist |
| Does the app provide **AI-generated/dynamic content from an online provider**? (if explicitly asked) | **Yes** | Optional document AI sends selected content to OpenAI on user approval and returns generated text; this is not a blanket “all online content is vetted” claim |
| Is there **user-generated content exchange**? (if asked separately from online interaction) | **Yes when referring to user-created files exchanged via WebRTC** | Don't answer “No” just because there is no social feed |
| Does the app offer open user-to-user **voice chat or public text chat**? | **No — based on reviewed source** | File transfer and external AI chat are not an in-app public or peer voice/text conversation |

## Critical conditional distinctions

1. **Online user interaction / content exchange = YES.** Google specifically treats sharing users' own files/photos or other material through the app's own mechanism as an interaction, while sharing exclusively via a separate app's OS share sheet would not count. RivoScan includes native WebRTC exchange, so this is affirmative.
2. **Built-in content** vs **arbitrary documents brought by users**: don't report every possible violent/sexual document as built-in content. Conversely, don't pretend that user-to-user file transfer cannot send unfiltered files.
3. **Optional AI generated responses** may contain material not curated into the shipped bundle. If Play shows any question about external unfiltered/dynamic content, answer based on this capability and its actual safeguards; do not automatically select No.
4. **18+ target audience** is a marketing/Play policy choice. The IARC regional content rating is **calculated by IARC**, not manually selected as 18+, PEGI 3, PEGI 7, etc. Never invent the resulting rating.
5. **Ads, privacy and Data Safety** are separately declared in Play Console. Don't use this content questionnaire as a replacement for verified privacy data disclosures.
6. The current Play release must be checked against the exact **signed AAB**. Re-run the questionnaire if features change.

## Submission workflow (requires Play Console UI)

Go to **Policy → App content → Content rating → Start questionnaire**. Enter the IARC contact email, select **All Other App Types**, fill topics above, review the calculated regional ratings, and click **Submit** if the actual displayed wording matches the reviewed evidence.

**Cannot be submitted using the Google Play Android Publisher API / GitHub publisher already connected.** Only the store's IARC questionnaire UI exposes the survey. This file is prepared evidence, not a submitted content rating.

## References

- Google Play Content rating instructions: https://support.google.com/googleplay/android-developer/answer/9859655
- Google Play clarification on native online content exchange: https://support.google.com/googleplay/android-developer/answer/7021383
- IARC questionnaire only available through participating storefronts: https://globalratings.com/faq/
- Interactive elements: https://globalratings.com/how-iarc-works/
