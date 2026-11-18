# TradingFiew Play Console App Content — source-verified draft
Checked: 2026-11-18
Package: `com.ribhlab.tradingfiew` / v1.0.2 (`versionCode 3`)
Public policy: https://tradingfiew.github.io/privacy.html
Publisher: RibhLab
Status: **REFERENCE ONLY — NOT filed in Google Play Console**.

The public privacy policy is actually deployed. The Google Play Publishing API does not provide the normal Play Console App Content declaration forms; a signed-in account session is required to save and submit these fields. This document prepares only source-evidenced answers; it is **not** an automatic legal certification.

## 1. Privacy policy
- **Answer**: `https://tradingfiew.github.io/privacy.html`.
- **Evidence**: public multilingual HTML policy describes publisher, local data, third parties, notifications, external links, ad status, storage/deletion and contact.
- **Play Console state**: not yet verified entered/saved in the designated **App content → Privacy policy** field.

## 2. App access
- **Supported answer**: **No, all functionality used for charting is accessible without a login or other restrictions**.
- **Evidence**: the website/TWA offers public financial charts, workspace/settings locally in the browser; no TradingFiew account, paid tier or password gate. External GitHub sign-in is only for an optional public supporter acknowledgment request and is not needed to review or use the app.
- **Watch**: do not falsely promise access to third-party pages without those parties' accounts; explain the optional external GitHub Issues feature if the form asks.

## 3. Ads
- **Current built app**: **No advertising currently serves**. `adsense.js` has `siteReady:false`, `cmpReady:false`, and `mobileVignetteOnlyConfirmed:false`. Android Gradle includes Android Browser Helper and androidx.browser, **no native AdMob SDK**. Mobile in-page placements are hidden.
- **Supported current-state answer**: `No` **only if the website ad activation flags remain disabled when this release is distributed**.
- **Future**: user requested mobile only interstitial/Vignette. Do not enable without approved AdSense site, actual account-side Vignette-only configuration, consent, a revised privacy policy, and revised Play Ads/Data Safety declaration.

## 4. Advertising ID
- **Manifest review**: no explicit `com.google.android.gms.permission.AD_ID`, only INTERNET and optional POST_NOTIFICATIONS, and no AdMob dependency.
- **Answer**: **No advertising ID used by first-party app code** based on reviewed source. Before signing the final Console declaration, inspect the final merged APK manifest and third-party browser dependencies.

## 5. Target audience
- **Evidence**: charts, price alerts and technical analysis about financial markets; not directed at children and no child-oriented features in the reviewed source.
- **Recommended age**: **18 and above only**, consistent with finance/trading market research.
- **Requires developer declaration**: age-band selection is a statement about actual intended marketing and audience, not something a source tree alone can legally certify; Google may show optional minor-access restrictions.

## 6. Financial features
- **Observed**: technical charts, educational SMC indicators, price alerts and calendars; crypto Spot *price data*, and a voluntary external crypto donation address. No in-app brokerage, buy/sell execution, credit, personal lending, banking, financial account management, crypto custody, or personalized investment advice.
- **Before answering**: examine the current Console financial product categories. If `Other` is available, describe honestly as `Educational market-data charts, technical indicators and local price alerts; no investment execution, account or wallet custody, and no personalized advice`. Do not select crypto wallet/exchange merely because a public donation address exists. Do not claim regulated license status or select `Financial advice` without a documented business need.

## 7. Data Safety
**Do not submit "No user data collected" solely because settings are stored locally.**
- **On-device storage**: local workspace identifier, user preferences, drawings, alerts and scheduled reminders.
- **Network requests**: GitHub Pages, Binance Spot, biquote, TradingView (calendar opened by user), Google Fonts and jsDelivr; providers may receive IP, user agent, request URLs, timestamps and technical diagnostics. Google Play's Data Safety guidance includes data handled by third-party providers/WebView-style content.
- **Permissions**: INTERNET, POST_NOTIFICATIONS.
- **Unknown without outside provider review**: third-party data retention, any logging linked to a user/device, whether third parties are processors or independent controllers, and whether specific API requests include persistent identifiers.
- **Action**: review provider privacy docs and Play's data taxonomy before marking each field: collected, shared, optional/required, purpose, encryption in transit, and deletion. Do not falsely claim "none" or "data is not shared".

## 8. Content rating
- **Confirmed elements**: educational finance and technical market data, no broker transactions; user can visit external public GitHub Issues pages; optional cryptocurrency donation address; externally embedded economic calendar.
- **Action**: complete the actual IARC questionnaire truthfully. Ratings are assigned by review authorities; do not select or invent a rating without seeing all questions.

## 9. Other declarations and first publication
- Health app: no health features found in reviewed source.
- Government app: not operated by a government according to project presentation.
- App permissions: INTERNET + optional POST_NOTIFICATIONS are declared. Verify merged manifest before final.
- Content category: FINANCE in planned listing, already approved as metadata only where observable.
- Website: https://tradingfiew.github.io/
- Store metadata: English, French, Arabic titles/descriptions and genuine media uploaded.
- App AAB: versionCode 3 in Google Play. Internal track = `completed`, Production track = `draft`; neither status alone establishes public visibility.
- Critical blocker: prior user's Android phone startup crashed. Latest emulator CI failed before a verified launcher completion (ADB/emulator tooling errors), so **native startup QA still needs a confirmed pass**.
- App status: Google Play API rejected completed Production in Draft app: `Only releases with status draft may be created on draft app.`
- Account review / closed testing / tester requirements remain subject to current Google Play Console dashboard, not inferred from repository.

## Play Console sequence
1. **Policy and programs → App content → Privacy policy** — enter public URL above and save.
2. **App access** — confirm no login is needed for core functionality.
3. **Ads** — reflect current deployed state (disabled); update if monetization changes.
4. **Target audience** — confirm actual intended 18+ audience.
5. **Financial features** — choose descriptions matching the live educational market-data app, not wallet/exchange or advice.
6. **Data safety** — complete a provider-by-provider data flow assessment before checking attestations.
7. **Content rating** — answer IARC based on actual features.
8. Verify remaining account, country availability, testing eligibility, startup QA and review requirements.
9. Submit Production only when the required declarations and tests have actually been completed and Google Play accepts the action. Verify publication in Console, not just a CI log.

## Evidence references
- https://github.com/tradingfiew/tradingfiew.github.io/blob/main/privacy.html
- https://github.com/tradingfiew/tradingfiew.github.io/blob/main/adsense.js
- https://github.com/tradingfiew/tradingfiew.github.io/blob/main/workspace.js
- https://github.com/tradingfiew/tradingfiew.github.io/blob/main/alerts.js
- https://github.com/tradingfiew/tradingfiew.github.io/blob/main/android/app/src/main/AndroidManifest.xml
- https://support.google.com/googleplay/android-developer/answer/9859455
- https://support.google.com/googleplay/android-developer/answer/10787469
