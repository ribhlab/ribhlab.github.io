# RivoNFC 0.6.3 / code 10: rollout compliance checkpoint

**Current verified Play state (2026-11-27):**
- Application: `com.ribhlab.rivonfc`.
- Existing Production and Internal Testing: code 9, status `completed`.
- Newly signed code 10 AAB: **uploaded and committed to Play bundle library only** by [stage-only workflow](https://github.com/ribhlab/ribhlab.github.io/actions/runs/46057262175). Neither track has been changed.
- AAB SHA256: `771382d8e73cadcc9bb24535150f414c5dffcb2cf9b27dee53b83f79ddcbd7bb` (16,290,677 bytes).
- Original RivoScan upload certificate SHA-1: `E9:B3:E2:77:95:75:BA:08:A9:13:72:FC:38:85:EB:A0:1D:D3:E7:3E`.
- [Signed release](https://github.com/univcours/ribhlab/releases/tag/rivonfc-v0.6.3-rivoscan-signed).
- Last application-source revision is `abfa805014439e669a083e6bdfd93b6e43fe7dd3`; later changes are private handoff/CI workflow files only, as confirmed by GitHub compare.

**Required before activating code 10:**
1. In the *authenticated Play Console for RivoNFC* (`com.ribhlab.rivonfc`), open **Policy and programs → App content → Ads**, review, set **Contains ads = Yes**, and save.
2. In **App content → Data safety**, review and submit accurate data-collection/sharing disclosures that reflect **Google Mobile Ads SDK (Legacy) 25.5.0** and **UMP SDK 4.0.0**, not the old no-ads declaration. Google says its SDK automatically collects and shares IP address (approximate location), app interactions, diagnostics, and device/account IDs (including advertising ID when available) for advertising/analytics/fraud prevention. Choose actual purposes and required vs optional status based on the app and SDK processing; account for consent and export features. Refer to [Google's version-specific SDK disclosure](https://developers.google.com/admob/android/privacy/play-data-disclosure). Make no unsupported claims about local NFC data being sent externally.
3. Confirm store Privacy Policy points to [RivoNFC policy](https://ribhlab.github.io/rivonfc/privacy/), which describes 0.6.3 advertising behavior. Confirm correct audience/rating declarations remain valid.
4. Confirm the Play **developer website** is `https://ribhlab.github.io/rivonfc/` and `https://ribhlab.github.io/app-ads.txt` serves the verified publisher line `google.com, pub-7945572016731367, DIRECT, f08c47fec0942fa0`. Existing automated audit [passed](https://github.com/ribhlab/ribhlab.github.io/actions/runs/46055322784); AdMob may take ~24 hours or longer to recrawl. Verification must be checked separately in AdMob; file correctness is not verification confirmation.
5. Check Play Publishing overview for pending changes and review/approval requirements; do not overwrite other drafts.
6. **Only after steps 1-3 are actually saved and verified**, run [guarded RivoNFC 0.6.3 promotion workflow](https://github.com/ribhlab/ribhlab.github.io/actions/workflows/rivonfc-063-verified-promote.yml) with **both compliance confirmations true**. It promotes already uploaded code 10 to **Production**, commits, then **Internal Testing**, and preserves store artwork/country availability.
7. Verify both Play tracks and new version after the run. Verify actual public availability separately; API `completed` is not equivalent to worldwide availability.

**Tool limitation:** Desktop Commander on `ram` reported monthly usage exhausted on 2026-11-27. Do not retry or reconnect until service resets. Google Play Developer Publishing API does not provide an established, supported write method for these Play Console policy declarations. Do not claim either declaration was updated without proof. Preserve other app releases and signing secrets.
