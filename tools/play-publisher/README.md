# RibhLab Google Play Publisher

An Android Google Play publisher for multiple apps. GitHub Actions takes an existing, signed Android App Bundle (.aab) from a GitHub Release in this repository, uploads it through the official Google Play Developer API, and creates a release on a chosen track.

**Safe defaults: internal testing + draft.** Draft releases are not sent to users. Production + completed requires explicitly typing PUBLISH and should additionally use required reviewers in a protected GitHub Environment.

## 1. Configure Google Play connection (once)

1. Create/select a project in [Google Cloud Console](https://console.cloud.google.com/).
2. Enable [Google Play Android Developer API](https://console.cloud.google.com/apis/library/androidpublisher.googleapis.com).
3. Under Google Cloud > IAM & Admin > [Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts), create a service account. Do not grant it global Owner/Admin roles.
4. In [Google Play Console](https://play.google.com/console/) > **Users and permissions**, invite the service account's email address and grant only required app-level permissions to view the app and manage the selected testing/production releases.
5. Create a JSON key for that service account. In GitHub > repository **Settings > Secrets and variables > Actions**, add a repository secret named **GOOGLE_PLAY_SERVICE_ACCOUNT_JSON** containing the complete JSON. Do not send a key in chat, attach it to a GitHub Issue, or commit it into this public repository. Workload Identity Federation is a stronger long-term option but is not implemented here.
6. In GitHub repository **Settings > Environments**, create **play-production**, set **required reviewers** and restrict who can deploy. Also create **play-testing** if different approval/secrets are desired. An unprotected environment does not enforce approval on its own.

**Before API usage:** Every Android app must already exist in the Play Console and its first APK/AAB must be uploaded manually via the Console. The API cannot create the new app or accept the required legal/developer declarations.

## 2. Upload signed AAB and run the publisher

1. Build a production-signed Android App Bundle with an incremented versionCode.
2. Create a GitHub Release in this repository with a tag like novagrid-v12; attach the .aab file (e.g. novagrid-v12.aab).
3. Go to **GitHub > Actions > Google Play Publisher — manual, draft by default > Run workflow**.
4. Set package_name to the exact existing Android applicationId; release_tag to the GitHub Release tag; bundle_asset to the AAB filename. Choose the track and release_status.
5. Select **draft** to prepare a release without distributing it. Select **completed** only to distribute to eligible testers or (for production) actual users, subject to Google review.
6. For production + completed, set production_confirmation to PUBLISH and have an authorized reviewer approve the protected environment. Check the Actions run and then verify the status in Play Console. An API commit does not guarantee store approval or immediate availability.

**Important:** This publishing repository is PUBLIC. Assets attached to GitHub Releases here are downloadable by the public. For private AAB binaries, put this workflow in a **private** GitHub repository instead of attaching private assets to public releases.

## 3. Limitations and safety

- Does not build or sign bundles; Android release build configuration is per app.
- Does not create new Play Console app entries, perform first uploads, configure app content disclosures, data safety, privacy policy, screenshots, pricing, or policy declarations.
- Does not schedule unattended production deployments.
- Serializes API updates by package name to reduce simultaneous edits.
- The service account needs Play Console permissions for the target app; a Google Cloud project alone is insufficient.
- Google Play review, country availability, tester requirements, and production access rules still apply.

## 4. Local dry run

Run:

    python tools/play-publisher/publish.py --aab /path/to/signed.aab --package com.example.app --track internal --status draft --dry-run

Tests (no credentials needed):

    python -m unittest discover tools/play-publisher -p 'test_*.py' -v

To actually upload locally, install tools/play-publisher/requirements.txt, securely provide the GOOGLE_PLAY_SERVICE_ACCOUNT_JSON environment variable, and remove --dry-run. Prefer the Actions workflow to avoid handling keys on a personal machine.

Official documentation: [Google Play API setup](https://developers.google.com/android-publisher/getting_started), [Edits workflow](https://developers.google.com/android-publisher/edits), [Draft releases](https://developers.google.com/android-publisher/tracks).
