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


## 27 November 2026 — new findings and corrected latest-code11 publisher

**App identifier: ONLY `com.ribhlab.rivonfc`.** No changes to RivoScan, NovaGrid, TradingFiew, or any other application.

- The original code11 0.6.4 upload remains in Google's bundle library. A fresh API check verified Production **Published code9** and Internal **Published code9**. Six publisher regression tests PASS; the exact code11 bundle is no longer accidentally classified as newer (fixed >10 comparison), and commits set `ERROR_IF_IN_REVIEW` to avoid canceling a pending review: https://github.com/ribhlab/ribhlab.github.io/actions/runs/46075998928.
- Live app-ads.txt `https://ribhlab.github.io/app-ads.txt`, dedicated `https://ribhlab.github.io/rivonfc/privacy/` and site `https://ribhlab.github.io/rivonfc/` all returned HTTP 200; the privacy policy discloses AdMob, identifiers, and UMP. These checks **cannot** prove Play Console declarations are saved.
- Captured **four genuine new 1080×1920 code11 screenshots from the certified original-key-signed release APK** on Android 35: Scan, Write, Tools, History. They were tested against live accessibility hierarchies, a visible bounded "ADVERTISEMENT" dock, no scroll on Scan, signed code11 metadata, and distinct SHA256 checksums. No simulated NFC reads and no live AdMob requests in screenshot QA: https://github.com/ribhlab/ribhlab.github.io/actions/runs/46076130056. Artifact `RivoNFC-064-Code11-OriginalSigned-Genuine-StoreMedia`.
- Existing en-US/fr-FR/ar Play long descriptions all **lack ads disclosures** and en-US screenshot set contains four **older code9** photos. The new `tools/play-publisher/rivonfc_064_production_real_media.py` and `.github/workflows/rivonfc-064-production-real-signed-media.yml` make an atomic, release-aligned update: Production code11, four original signed screenshots in en-US, and accurate ads information appended to existing en-US/fr-FR/ar descriptions. The icon and feature graphic are preserved; Internal Testing remains untouched.
- A safe **dry-run** applied the proposed changes inside a disposable Google Play Edit (nothing was committed) and received an exact **HTTP 400** from Google: `This release includes the com.google.android.gms.permission.AD_ID permission but your declaration on Play Console says your app doesn't use advertising ID. You must update your advertising ID declaration.` Evidence: https://github.com/ribhlab/ribhlab.github.io/actions/runs/46076457738.
- **Mandatory third declaration** (in addition to Contains ads = Yes, and correctly completed Data safety): Go to the RivoNFC Google Play Console **Advertising ID** app-content declaration and mark **YES** because Google Mobile Ads SDK 25.5.0 uses it. Save the answer. Do not falsely claim the Console declaration is fixed from changes to the Android manifest, GitHub, or app-ads.txt. This is an actual Google API blocker verified by Google's own validation, not a guessed setting.
- Only after the authorized account independently confirms the three accurate Console declarations, invoke the new **RivoNFC 0.6.4 - code11 original-signed Production and genuine store screenshots** workflow and tick the three factual confirmations. Never tick these without checking Play Console. This publishes the **already uploaded** original-signed code11; no code12 rebuild is needed merely because the publisher was corrected.
- The former `rivonfc-064-verified-promote.yml` was restricted to **Internal Testing only**, after the real Production code11 release exists. Its obsolete Production path is blocked to prevent reusing old-code9 Play screenshots and skipping the new Advertising ID confirmation.
- Google Play `RELEASE_LIFECYCLE_STATE_IN_REVIEW` is **not** yet confirmed for code11; code9 remains the published version. Do not claim code11 has been approved until the release API confirms it.

### Required Play Console verification (RivoNFC app ONLY)

1. **Policy and programs → App content → Ads**: `Contains ads = Yes`, because banner, interstitial and optional rewarded ads are included in code11.
2. **Policy and programs → App content → Advertising ID**: `Uses advertising ID = Yes` for `com.google.android.gms.permission.AD_ID`; required by the exact Google Play HTTP 400 rejection.
3. **Policy and programs → App content → Data safety**: Submit truthful declarations for Google Mobile Ads SDK 25.5.0 and UMP 4.0.0 based on SDK-specific data disclosures and actual app use (device or other IDs, IP-derived approximate location, app/ad interactions and diagnostics where collected/shared; purposes may include advertising, analytics and fraud prevention). Do **not** invent selections without inspecting the Console's full form and data practices.
4. Confirm privacy policy link `https://ribhlab.github.io/rivonfc/privacy/` and full target audience declarations. Keep the existing app ID, 0.6.4 code11 bundle, signing key, store launcher icon and canonical listing.

