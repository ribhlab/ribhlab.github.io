# RivoNFC — AdMob verification diagnostic (2026-11-28)

**Scope:** RivoNFC only, Android package `com.ribhlab.rivonfc`. No Play binary, AdMob unit or other app was modified.

## Actual AdMob UI verified via authorized desktop session
- App: RivoNFC: NFC Tools (Android).
- AdMob app ID: `ca-app-pub-7945572016731367~3403190708`.
- Linked store: Google Play / `com.ribhlab.rivonfc`.
- App verification: **Not verified**.
- Approval status: **Requires review**.
- Ad serving: **Limited — Verify app to lift limit**.
- 3 active ad units.
- `Verify app` opened; exact feedback: **"We couldn't verify RivoNFC: NFC Tools (Android)"** / **"You may have set up an app-ads.txt file, but your details don't match the information in your AdMob account."**
- The suggested AdMob snippet exactly matched the site's public file: `google.com, pub-7945572016731367, DIRECT, f08c47fec0942fa0`.
- The actual `Check for updates` button was clicked once in AdMob in this session; the same mismatch feedback persisted. **No false claim of successful verification.**
- AdMob `app-ads.txt` overview showed 100% authorized queries; 5 other apps showed found and verified. RivoNFC was not present in the visible 5 rows; the overview itself warns apps may not appear if recently unverified or without requests. Do not infer AdMob has never crawled RivoNFC.

## Independent Google Play and web verification
- Read-only verified Google Play Android Publisher API app details `contactWebsite`: `https://ribhlab.github.io/rivonfc/` exactly.
- Read-only Play tracks: `production`, `completed`, code **12**; `internal`, `completed`, code **9**.
- Public Google Play HTML (not just Play API) includes:
  `<meta name="appstore:developer_url" content="https://ribhlab.github.io/rivonfc/">`.
- Site `https://ribhlab.github.io/rivonfc/` returns HTTP **200**.
- `https://ribhlab.github.io/app-ads.txt` returns HTTP **200**, `text/plain; charset=utf-8`, as inspected using the Googlebot User-Agent.
- Exact expected publisher line is present in the 59-byte root `app-ads.txt`; its publisher ID matches the displayed AdMob app ID.
- Automated read-only diagnostics: https://github.com/ribhlab/ribhlab.github.io/actions/runs/46155047410 (success).

## Unresolved external verification state
- Despite matching live AdMob publisher ID, Play store ID, developer website and app-ads.txt URL, AdMob's current app verification service continues to report a mismatch.
- The remaining cause is not directly observable from the available account UI. A stale AdMob crawler / propagation delay **may** explain it, but this is not independently proven.
- Google AdMob documentation instructs `Verify app -> Check for updates`, and notes Play website and crawler changes can take up to 24 hours for detection.
- Do **not** change the correct shared root file, app ID, production app, Google Play package, or unrelated apps merely to suppress the warning.
- If the same message persists after AdMob refreshes the crawler, raise an AdMob support request with the exact error, Play developer website, website HTTP200, root app-ads.txt, package ID and these diagnostics. Only Google can clear an incorrectly held verification/serving restriction.
- App readiness review happens after app-ads verification. Neither ad-served status nor estimated approval is guaranteed.

## 2026-11-28 — FIXED missing Play Console developer-profile website

- Inspected the actual, authenticated Google Play Console under **Manage account → Account details → Play developer profile → Developer page**. Its **Developer website** field was **empty** even though the per-app contact website and public Google Play store metadata linked correctly to `https://ribhlab.github.io/rivonfc/`.
- Filled the **shared developer profile website** with the already-owned canonical root `https://ribhlab.github.io/`, which serves the correctly formatted `/app-ads.txt`. No app's store metadata, release, AdMob unit, code, or other app was modified.
- An initial attempt to fill the field through remote keyboard input produced an invalid punctuation-only value and was rejected by Play (**Website URL is invalid**, nothing saved). Re-entered the URL with Unicode input, then clicked **Save changes**. Google Play explicitly confirmed **Your changes have been saved**.
- **Persistence independently verified**: refreshed Play Console and checked Developer website again; it still displays `https://ribhlab.github.io/` and Save changes is disabled (no pending edits).
- **AdMob recheck completed** after the fix: navigated to **RivoNFC → App settings → Verify app** and pressed **Check for updates**. The mismatch error was still present immediately; therefore app verification and removal of the serving limit are **not yet confirmed**. Official AdMob help permits up to **24 hours** for crawler/Play developer-website change detection. Review again after propagation; if still blocked, escalate with screenshots and these findings.
- **Apps to confirm (1)** in AdMob was checked: the only listed app was `com.ribhlab.rivosticker`, **not RivoNFC**. No action on RivoSticker was taken.
- This is an evidence-based correction of a genuine missing Play Developer page field; it is plausible, but not yet proven, that this was the only cause of the AdMob mismatch.
