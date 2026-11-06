# RivoScan — Play Console readiness

Source reviewed: `univcours/ribhlab`, `feat/rivoscan-android-beta`.

## Prepared automatically
- Package identifier: `com.ribhlab.rivoscan`.
- Localized store listing: English (US), French (France), Arabic.
- Genuine 512 × 512 RivoScan icon copied from source. The publisher converts its indexed PNG to 32-bit RGBA when uploading, only if no icon is already uploaded.
- Listing deployment workflow: disabled by default and does not access Google until the initial AAB upload is saved and the release request is enabled.
- Existing app bundle versionCode must be read from Play Console: older project files mention 86 / 0.44.10 but the uploaded bundle may differ.

## Needs confirmation / cannot safely invent
- Privacy policy: a RivoScan-specific public policy is hosted at `https://ribhlab.github.io/rivoscan/privacy/`. The Android source branch `feat/rivoscan-android-beta` now also contains updated `apps/rivoscan/public/privacy.html` and an in-app Settings link (merged commit `47dcd2cbea7ec7307ac34378bb86afe84e8ccca2`). **Existing AAB files do not automatically inherit this source change**; rebuild before publishing. The final signed binary and SDK data behavior still need verification before Data Safety submission.
- Data Safety / app data collection, sharing, encryption, deletion: complete using verified library SDK behavior and actual signed AAB. The API has a dataSafety write endpoint but does not justify guessing a declaration.
- App access (login required or not), target audience, content rating, category, advertising presence, government/financial declarations if relevant: must match tested binary.
- Screenshots: must be genuine captures of the actual running app. No fake UI screenshots have been supplied.
- Feature graphic: no verified art at the required store size has been supplied.
- Support contact shared with the published NovaGrid listing: `rachid022note4@gmail.com`; contact and RivoScan website were already committed through the Play Publishing API.
- Production access: dependent on developer account eligibility and Play Console onboarding requirements.
- First signed AAB upload and any replacement binary: must be completed in Play Console or through an authorized signing/upload workflow. The listing fields were already committed by API; they are not a replacement for an AAB.
- First public release and policy review: Google-controlled approval, not guaranteed by API edit commit.

## Sequencing
1. Owner creates the RivoScan Play Console app and uploads/saves the first signed AAB.
2. Verify app exists and that `GOOGLE_PLAY_SERVICE_ACCOUNT_JSON` has access to it.
3. Finish privacy/Data Safety and first-time setup declarations in Play Console.
4. Confirm genuine screenshots and feature graphic.
5. Store listing text (EN/FR/AR), genuine icon, developer email and website were committed via the official Play Publishing API on Nov 6, 2026. The one-time request was subsequently disabled. Privacy policy **URL** in the Play Console App content questionnaire remains a separate, unconfirmed manual declaration.
6. Only after approval, handle internal testing, closed testing, and public release separately.
