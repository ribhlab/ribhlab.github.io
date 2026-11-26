# RivoCaption 0.4.3 — Google Play foreground-service permission declaration

## Verified 26 November 2026

Google Play Android Publisher rejected the AAB v17 commit with HTTP 403:

> You must let us know whether your app uses any Foreground Service permissions.

This is **not** an AAB signing failure. The original RivoScan upload-key-signed RivoCaption 0.4.3 (code 17) is available at:

https://github.com/univcours/ribhlab/releases/tag/rivocaption-v0.4.3-original-rivoscan-aab

A publisher workflow in `ribhlab/ribhlab.github.io` already downloads that exact verified AAB.
Production currently has versionCode 8.

## Required console-only account declaration

In Google Play Console, select **RivoCaption** (`com.rivocaption.editor`), then:

**Policy and programs → App content → Foreground service permissions → Manage / Start.**

Review the following source-grounded uses and declare the specific types listed in the actual manifest. Do **not** declare other types such as microphone or media playback unless genuinely present in the actual uploaded manifest.

### FOREGROUND_SERVICE_DATA_SYNC

- **Appropriate purpose/category:** Network transfer / Upload or download (specifically model download).
- **English explanation:** "RivoCaption lets the user explicitly download an offline Whisper speech-recognition model. The transfer can be large and may continue after the user switches apps. Android WorkManager shows a foreground notification with percentage progress and a Cancel action. The model stays in app-private storage and is used for on-device transcription. The download never starts without a user request."
- **French explanation:** "L'utilisateur choisit explicitement de télécharger un modèle de reconnaissance vocale Whisper pour le traitement hors ligne. Le téléchargement peut être volumineux et continuer lorsque l'application passe en arrière-plan. Une notification affiche la progression et propose Annuler. Le modèle est stocké dans l'espace privé de l'application."
- **Video evidence:** Actual recording showing the user's consent, model download starting, and the genuine Android foreground download progress notification with Cancel. **A real hosted video URL must be supplied in Play Console; do not invent one.**

### FOREGROUND_SERVICE_MEDIA_PROCESSING

- **Appropriate purpose/category:** Media processing / media conversion or transcoding, subject to Google Play's current form options and actual ASR behavior.
- **English explanation:** "After a user selects a video and requests offline transcription, RivoCaption extracts and processes its audio and performs potentially lengthy on-device speech recognition. On Android 15 and above the isolated Whisper worker runs as a mediaProcessing foreground service, displaying an ongoing progress notification and a Cancel option. The process stops after completion or cancellation, and the media is not automatically uploaded to a remote service in local mode."
- **French explanation:** "Après avoir sélectionné une vidéo et lancé la transcription hors ligne, l'application extrait et traite la piste audio puis exécute la reconnaissance vocale sur l'appareil. À partir d'Android 15, ce traitement utilise un service au premier plan de type mediaProcessing, avec notification de progression et possibilité d'annuler. Le traitement s'arrête à la fin ou sur annulation."
- **Video evidence:** Actual recording showing video selection, starting Whisper offline transcription, and the ongoing foreground progress notification / Cancel. **Not a fabricated simulation.**

### UI and permission consistency notes

Actual AndroidManifest.xml requests:
- `android.permission.FOREGROUND_SERVICE`
- `android.permission.FOREGROUND_SERVICE_DATA_SYNC`
- `android.permission.FOREGROUND_SERVICE_MEDIA_PROCESSING`

The manifest declares `SystemForegroundService` as `dataSync`, and isolated `WhisperRecognitionService` as `dataSync|mediaProcessing`. Android 10–14 transcribing falls back to dataSync; Android 15+ uses mediaProcessing.

The Play Console declaration and supporting demonstration links must reflect **actual** user-initiated behaviors. Google reviews them for policy compliance. No fake video or false declaration should be submitted.

## Publisher after the declaration

After the form is saved/submitted, run **RivoCaption 0.4.3 verified Google Play production publisher** from:

https://github.com/ribhlab/ribhlab.github.io/actions/workflows/rivocaption-043-publish-signed-aab.yml

The existing workflow checks the key and Play tracks, uploads AAB v17 and verifies the production track. The workflow will fail honestly if another policy item is required; don't bypass review.

Then run the genuine-screen image workflow only after source screenshot capture succeeds and the new production version is committed:

https://github.com/ribhlab/ribhlab.github.io/actions/workflows/rivocaption-043-production-and-real-media.yml

**Caution:** The combined workflow currently downloads an older release tag that included both signed APK and signed AAB. Since the newer signer generated an AAB-only release, revise and validate its input assets before dispatching it. Never upload synthetic app screenshots or claim the production track is updated without Play API verification.

Sources:
- https://support.google.com/googleplay/android-developer/answer/13392821
- https://developer.android.com/about/versions/14/changes/fgs-types-required

## Validation notes

- Build verified 35 Android unit tests; app code 17, version 0.4.3.
- Signing verified original RivoScan upload-key certificate; signed AAB published on GitHub.
- Play API confirmed access and source track production code 8 before attempt.
- Publishing HTTP 403 foreground-service declaration missing, so **not published**.
- Five genuine updated store screenshots have not been captured and uploaded yet.
