# RivoScan Data Safety — evidence-based declaration review (7 Nov 2026)

**Application ID:** `com.ribhlab.rivoscan`  
**Observed on Google Play:** signed Internal Testing AAB `versionCode 74`, corresponding to source **0.43.4**.  
**Exact matching source revision:** [85fefd1d72c54bff2e624ac3b529c2fd1f796622](https://github.com/univcours/ribhlab/commit/85fefd1d72c54bff2e624ac3b529c2fd1f796622).  
**Source-to-binary caveat:** the versionCode and branch match, but the actual uploaded AAB binary has not been extracted or independently compared. Runtime configuration/SDK merge behavior may differ.

## Findings verified at version 74

- `apps/rivoscan/src/monetization.js`: includes `@capacitor-community/admob` and UMP consent flow; ad IDs are **Google demo units** in this old build, but SDK may transmit ad/diagnostic/device data nevertheless. Version 74 also provides **optional rewarded ads to access advanced tools**. This is obsolete compared with newer source versions.
- `apps/rivoscan/src/ai-provider.js`: optional POST to `https://api.openai.com/v1/responses` with user-provided secret, `store:false`, and selected document text, photo and prompt. The user's affirmative per-request confirmation is implemented in `src/document-ai.js`. No developer API key is included in this version. Do not assume `store:false` means all provider logs are immediately deleted.
- `apps/rivoscan/src/file-transfer.js`: private WebRTC datachannel with manually exchanged offer/answer and `stun:stun.l.google.com:19302`. File payload transfer is encrypted end-to-end, but STUN may disclose IP/network metadata over unencrypted UDP.
- Core local PDF/OCR operations are not remote uploads by default; OCR/ML Kit language/model downloads have their own network activity.
- **Material discrepancy:** `apps/rivoscan/public/privacy.html` bundled in **v74** falsely states that the app has no advertising or cloud AI. Do **not** publish v74 to Production without rebuilding with the updated policy, functionality and real signed AAB. The current hosted [privacy policy](https://ribhlab.github.io/rivoscan/privacy/) is newer, but cannot change already bundled v74 code.

## Official Google Play Data Safety CSV

Candidate file: `rivoscan-data-safety-candidate-2026-11-07.csv`.

The entire Google Play CSV format is retained, with responses based on the **actual v74 source** rather than v99. The base was a 783-line publicly documented export matching Google's official 2026 schema; all old third-party answer values were cleared.

### Data collection and security

| Google Play question | Prepared answer | Evidence |
|---|---|---|
| Collect or share any required user data? | **Yes** | Google Mobile Ads SDK + optional AI |
| Is all data encrypted in transit? | **No (conservative)** | WebRTC STUN communicates network metadata over standard unencrypted STUN/UDP despite encrypted WebRTC file data, AI HTTPS and AdMob TLS; no packet capture on uploaded AAB |
| Account creation method | **App does not allow account creation** | No RivoScan account signup; user-entered personal OpenAI API key is for external optional service |
| Can users log in with external accounts? | **No** | No RivoScan account or external OAuth sign-in |
| Users may request data deletion? | **No (not verified)** | Current app has no dedicated end-to-end verified developer-run deletion procedure; device-local files can be deleted in Android but this is not deletion from third parties |
| Independent security audit? | **No** | No completed MASA assessment established |

### Selected data types and handling

| Play data type | Collected? | Shared? | Required/Optional | Purposes |
|---|---|---|---|---|
| Approximate location | Yes (IP-derived) | Yes | Required/conservative | Advertising, analytics, fraud prevention |
| App interactions | Yes | Yes | Required/conservative | Advertising, analytics, fraud prevention |
| Diagnostics | Yes | Yes | Required/conservative | Advertising, analytics, fraud prevention |
| Device or other IDs | Yes | Yes | Required/conservative | Advertising, analytics, fraud prevention |
| Files and docs | Yes | No (user-initiated AI transfer exception) | Optional | App functionality |
| Photos | Yes | No (user-initiated AI transfer exception) | Optional | App functionality |
| Other user-generated content (AI questions) | Yes | No (user-initiated AI transfer exception) | Optional | App functionality |

No type is marked ephemeral, because ad profiling / provider abuse monitoring or retention can outlast a single real-time request. The sharing choice for user-initiated AI requests follows the Google Play exception for transfers the user explicitly initiates and reasonably expects. Even where sharing is exempt, **collection remains declared**. No contacts, precise GPS, payment information, call logs or health data are automatically declared without observed transfer.

Google's Google Mobile Ads SDK disclosure identifies **IP address**, **user product interactions**, **diagnostic information** and **device and account identifiers** as automatically collected and shared for advertising, analytics and fraud prevention. Google Play Data safety guidance distinguishes on-device processing and E2EE (not collected), user-initiated data sharing exceptions, ephemeral processing and mandatory SDK data.

Official sources:
- https://developers.google.com/admob/android/privacy/play-data-disclosure
- https://support.google.com/googleplay/android-developer/answer/10787469?hl=en
- https://developers.google.com/android-publisher/api-ref/rest/v3/applications/dataSafety

## Remaining release blockers

1. **Rebuild/sign and upload current RivoScan AAB** to replace old v74 before public release, with updated in-app privacy policy and non-demo production Ads identifiers.
2. Compare the **merged AndroidManifest, actual SDK versions and runtime traffic** of that final signed AAB with this CSV, and update the global Play declaration when SDK behaviors change.
3. Finish other Play Console App content questionnaires (IARC, target age, app access, government/financial/health) and collect actual closed-testing opt-ins.
4. Google Play's CSV import **overwrites all previous answers**. Do not mix with another app's export. The Data Safety API POST likewise replaces the entire safety declaration.

This file is evidence of a prepared declaration, not a claim of Google Play approval, account-specific verification or security testing.
