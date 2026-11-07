# RivoScan — owner-supplied Google Play image package

Source: uploaded `RivoScan_Google_Play_Complete(1).zip`, reviewed on 7 November 2026.

## Approved asset mapping

| Original ZIP file | Staged destination | Intended use |
|---|---|---|
| `assets/app_icon_512x512.png` | `store-listings/assets/rivoscan-icon.png` and `public/rivoscan/icon.png` | **Original green** app icon, 512×512 RGBA PNG |
| `assets/feature_graphic_1024x500.png` | `store-listings/assets/rivoscan-owner-feature-1024x500.jpg` and `public/rivoscan/feature.jpg` | Feature graphic converted from RGBA to nontransparent RGB JPEG, 1024×500 |
| `assets/01_hero_smart_scanning.png` through `05_built_for_everyday_use.png` | `public/rivoscan/marketing/*.jpg` | Marketing images on the app landing page; JPEG conversion preserving aspect ratio |

**Important screenshot accuracy:** the five owner-supplied marketing images show rendered phone mockups. They are not verified captures from the RivoScan Android build. Google expects screenshots showing the real app experience; therefore these five are published only in a clearly labeled promotional gallery and do **not** replace the four genuine 1080×1920 Android emulator screenshots already staged in the Play publisher. See official guidance: https://support.google.com/googleplay/android-developer/answer/9866151

## Publishing behavior

- Exact package: `com.ribhlab.rivoscan`.
- User-provided English store title: **RivoScan**.
- User-provided English short description: **Smart document scanning with edge detection, OCR, PDF export, and sharing.**
- Six other translated store descriptions stay in place (French, Arabic, Spanish, German, Portuguese, Italian).
- Owner green icon is locked to SHA-256 `67cd03f1d7e91e50ed398cc03c0a77482721e23053831df13984dbe3dffd9ce3`.
- Converted owner feature JPEG is locked to SHA-256 `53c4af468ee27d6fba11dabc6b2ca9cee46b0ea331bfe410283b32786491e51c`.
- A **read-only** Google Play release check is scheduled twice per hour. It cannot view an ongoing upload or unsaved AAB. It recognizes only a saved version in a visible Google Play track release.
- Once a saved release is seen, the workflow applies the listing text, green icon and feature graphic **once** using a Play API edit, then marks synchronization complete. It never uploads an AAB, changes tracks, enrolls testers or publishes production.
- This flow intentionally does not create a Google Play edit while an AAB upload is still being prepared in Play Console, which could invalidate unsaved changes.
- App Content declarations (Data Safety, advertising, age rating, content rating, privacy-policy URL and permissions) remain subject to truthful owner review within Play Console. Do not infer approval from a workflow success.

All asset files were sourced from the user-uploaded ZIP. No credentials or personal tester emails are included.
