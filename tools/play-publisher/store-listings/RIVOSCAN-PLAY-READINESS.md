# RivoScan — Play Console readiness

Source reviewed: `univcours/ribhlab`, `feat/rivoscan-android-beta`.

## Prepared automatically
- Package identifier: `com.ribhlab.rivoscan`.
- Localized store listing: English (US), French (France), Arabic.
- Genuine 512 × 512 RivoScan icon copied from source. The publisher converts its indexed PNG to 32-bit RGBA when uploading, only if no icon is already uploaded.
- Listing deployment workflow: disabled by default and does not access Google until the initial AAB upload is saved and the release request is enabled.
- Existing app bundle versionCode must be read from Play Console: older project files mention 86 / 0.44.10 but the uploaded bundle may differ.

## Needs confirmation / cannot safely invent
- App privacy policy: the repository file `apps/rivoscan/public/privacy.html` is marked **Draft** and says the beta has no ads, but `apps/rivoscan/src/monetization.js` includes AdMob integration in test mode, rewarded ad gating, and ad-consent code. The final Android binary and third-party SDK data behaviors must be audited before declaring "no data collected" or "no ads." Do not publish the outdated draft policy.
- Data Safety / app data collection, sharing, encryption, deletion: complete using verified library SDK behavior and actual signed AAB. The API has a dataSafety write endpoint but does not justify guessing a declaration.
- App access (login required or not), target audience, content rating, category, advertising presence, government/financial declarations if relevant: must match tested binary.
- Screenshots: must be genuine captures of the actual running app. No fake UI screenshots have been supplied.
- Feature graphic: no verified art at the required store size has been supplied.
- Support email: do not publish a personal address without confirmation.
- Production access: dependent on developer account eligibility and Play Console onboarding requirements.
- First signed AAB upload: Play Console action by the owner, before API edits.
- First public release and policy review: Google-controlled approval, not guaranteed by API edit commit.

## Sequencing
1. Owner creates the RivoScan Play Console app and uploads/saves the first signed AAB.
2. Verify app exists and that `GOOGLE_PLAY_SERVICE_ACCOUNT_JSON` has access to it.
3. Finish privacy/Data Safety and first-time setup declarations in Play Console.
4. Confirm genuine screenshots and feature graphic.
5. Trigger the RivoScan listing-deploy request to upload localized text and icon without releasing a bundle.
6. Only after approval, handle internal testing, closed testing, and public release separately.
