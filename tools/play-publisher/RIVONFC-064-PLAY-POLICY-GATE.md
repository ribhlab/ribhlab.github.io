# RivoNFC 0.6.4 / versionCode 11 — verified delivery and release gate

Checked on 2026-11-27. App **ONLY**: `com.ribhlab.rivonfc`.

## Verified source, build, signing and Google Play bundle
- Code version `0.6.4`, versionCode `11`, original app-source commit `c1a6c156d7b394267ebc01b7da1b2e28e2e26f47`.
- Source build, unit tests, lint, APK/AAB: PASS: https://github.com/univcours/RivoSticker/actions/runs/46064225553
- Private encrypted handoff and original RivoScan upload-key signing: PASS: https://github.com/univcours/ribhlab/actions/runs/46064368904
- Signed release: https://github.com/univcours/ribhlab/releases/tag/rivonfc-v0.6.4-rivoscan-signed
- Signed AAB SHA256: `70c7f7c9095659ad1d1ab16ef00790c839c71ec4839bb50d80dd9aba4261bfae` (16,301,282 bytes).
- Original RivoScan upload certificate SHA1: `E9:B3:E2:77:95:75:BA:08:A9:13:72:FC:38:85:EB:A0:1D:D3:E7:3E`.
- Google Play Developer API returned `RIVONFC_064_STAGE_COMMITTED`, signed code **11** in the bundle library, with `productionUnchanged=true` and `internalUnchanged=true`: https://github.com/ribhlab/ribhlab.github.io/actions/runs/46064942873
- Existing **Production and Internal** remained code **9**, 0.6.2, in this independent transaction. Code 10 was an obsolete non-active staged bundle.
- Do not run the former code-10 promotion. The 0.6.3 promotion workflow was disabled.

## Critical mandatory Play Console policy gate — not independently confirmed
1. In authenticated Play Console for **RivoNFC only**, go to **Policy and programs → App content → Ads**. Verify **Contains ads = Yes** has actually been saved.
2. Open **App content → Data safety**. Verify that answers have been submitted for Google Mobile Ads SDK 25.5.0 and UMP 4.0.0 (IP-derived approximate location, app interactions, advertising ID and other IDs, diagnostic info, advertising measurement and anti-fraud), and that the answers correctly reflect this exact app and SDK behavior. Never falsely assert 'No data collected'; inspect the official SDK disclosure.
3. Confirm the public policy URL `https://ribhlab.github.io/rivonfc/privacy/` has the 0.6.4 advertisement and privacy disclosure, and that the Console uses it. Verify audience rating, advertising ID declaration and review notices.
4. Verify the developer website `https://ribhlab.github.io/rivonfc/` and `https://ribhlab.github.io/app-ads.txt`. Presence of app-ads.txt is not proof that AdMob has crawled it or is serving paid ads.
5. Only after items 1–3 are independently verified, run **[guarded 0.6.4 promotion](https://github.com/ribhlab/ribhlab.github.io/actions/workflows/rivonfc-064-verified-promote.yml)** with both Ads and Data safety confirmations genuinely true. This promotes **already signed code 11** to Production first then Internal and checks the old tracks and artwork to avoid collateral edits.
6. Verify the Play receipts, current Production and Internal tracks, and actual public distribution. A completed API commit is not automatic proof that Google has approved or worldwide published a new build.

## App experience
- Responsive no-vertical-scroll Scan landing page; full NFC details appear in a separate scrollable dialog.
- Anchored adaptive banner stays in a stable clipped container above bottom navigation. Empty ad inventory is not a fake ad: placeholder shows until Google serves real creative.
- UMP consent gate, debug-only Google official test units, live AdMob IDs only on production builds.
- Interstitial shows only on safe transitions into Tools/History, with >=120 seconds since session start, 3 eligible navigation changes and >=240 seconds since the **last confirmed displayed** interstitial. NFC operations block interstitials.
- Runtime emulator QA: https://github.com/univcours/RivoSticker/actions/runs/46065123693 (check its final conclusion).

**Not claimed:** Play policy declarations completed, code 11 Production activation, non-test AdMob ad fill, live on-device NFC verification. Never bypass policy or publish a stale code-10 bundle.
