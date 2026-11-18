# TradingFiew — first Google Play publication readiness

Last technical review: 18 November 2026. App: `com.ribhlab.tradingfiew`.

## Confirmed through the Google Play Developer API
- Signed **AAB v1.0.2 / versionCode 3** uploaded successfully.
- **Internal Testing** release created with `status=draft`, not distributed to testers.
- **Production** track remains an older empty draft (not published).
- Store listings: **en-US**, **fr-FR**, **ar** — titles, short descriptions and full descriptions committed.
- Original logo icon **512×512**, original branded **1024×500** feature graphic, and **three genuine mobile screenshots** uploaded. Screenshots were captured from the live TradingFiew TWA web interface using real loaded market data. None were synthesized or mocked.
- Support website: https://tradingfiew.github.io/
- Existing registered contact email preserved by API without replacement.

## Verified from source code, but still requiring Console declarations
- **Privacy policy**: https://tradingfiew.github.io/privacy.html ; it now explains the Android TWA, local workspace, third-party market data, notifications and inactive mobile advertising. The separate Play Console **privacy-policy URL** declaration is *not* accessible through the Edits API; do not falsely claim it was entered there.
- **App access**: public web terminal does not require login or a demo account. An App Access declaration still needs to be submitted in Play Console.
- **Android permissions**: INTERNET and optional POST_NOTIFICATIONS. No native camera, microphone, contacts, location, calls, SMS or Android advertising-ID permission declared in the source Android manifest.
- **Ads**: the Android project has no native AdMob SDK. Website AdSense is disabled at this time (pending site approval/consent); mobile inline ads are suppressed. If future vignette ads are activated, update the Play Ads and Data Safety disclosures *before* activation. Do not answer the Ads declaration from a planned future monetization state.
- **Finance content**: educational market charts and indicators, no broker order execution, no custodied wallets. A cryptocurrency donation link is provided. The Play financial-features declaration must be reviewed against the actual functionality and jurisdictions; do not assert regulatory exemptions that have not been documented.
- **Network/data**: browser requests contact GitHub Pages, Binance, biquote, TradingView and possibly other resource hosts. Third parties may receive IP addresses, user-agent information and request details. Local drawings/preferences are saved locally; notification rules may request optional permission. A verified Data Safety CSV requires a full provider/SDK data-retention and sharing assessment, so do not blindly declare "no data collected."
- **Target audience**: no child-focused content or child-specific features found. Exact age bands must be selected by the developer in Play Console, including any needed finance/ad restrictions.
- **Content rating**: complete the IARC questionnaire inside Play Console, with true answers about financial research, any crypto donation links and external websites. Do not fabricate a rating.

## Remaining owner/account-side steps
1. Open **Play Console → TradingFiew → Policy and programs → App content**. Complete **App Access**, **Ads**, **Target Audience**, **Financial Features (when shown)**, **Content Rating**, **Data Safety**, and **Privacy Policy URL** after checking their actual questions. Google may request identity or developer verification.
2. Set country/region availability and verify developer details, pricing, and any app-level policy forms in Play Console.
3. Resolve the actual Android startup crash. 1.0.2 has signed APK/AAB, compile and static regression tests; the user's earlier phone crash makes production inappropriate before a fresh physical-device or emulator startup success.
4. Once all Console forms are genuinely complete and a clean smoke test is recorded, convert Internal Testing from **draft** to **completed** and examine Play pre-launch report. Do not imply an internal draft is public distribution.
5. Follow any Closed Testing/Production eligibility imposed on this developer account (for example the applicable number of testers and testing duration). Do not simulate or shorten a required test.
6. Request Production only after those requirements pass. Verify the final state through Play Console **and** Google Play API before reporting a public listing URL.

## References
- Source: https://github.com/tradingfiew/tradingfiew.github.io/
- Signed APK/AAB (original RivoScan upload key): https://github.com/univcours/ribhlab/releases/tag/tradingfiew-android-v1.0.2-rivo-key
- Publisher scripts and exact audit: https://github.com/ribhlab/ribhlab.github.io/tree/main/tools/play-publisher
- Google policy requirements: https://support.google.com/googleplay/android-developer/answer/9859455
