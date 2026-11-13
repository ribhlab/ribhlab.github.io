# RibhLab Focus Rescue
Native Android Camera2 app to test camera autofocus issues with bounded lens focus sweeps.

## What it does
- Live TextureView preview with selectable Camera2 lens.
- Manual near/infinity focus movement ONLY when supported by Camera2 MANUAL_SENSOR and positive LENS_INFO_MINIMUM_FOCUS_DISTANCE.
- Autofocus retrigger for autofocus-capable lenses.
- Throttled operation (850–2600 ms), explicit stop button, and automatic stop after 30 seconds.
- No network, storage, advertisements, or privileges beyond CAMERA.

## Important
Cannot alter electrical strength of a lens motor or repair a physically jammed autofocus assembly. Stop if unusual noise, heating or mechanical problems occur. This is an experimental diagnostic aid.

## APK
Actions -> RibhLab Focus Rescue APK -> latest successful run -> Artifacts -> RibhLab-Focus-Rescue-APK, unzip to get app-debug.apk.
Uses AGP 8.7.3, Gradle 8.9, Android 35, Java 17, minSdk 26.

## Sound diagnostics (v1.1)
- Synthetic beep per focus command (distinct from the actual lens sound). Disable it using the checkbox.
- User-initiated, eight-second microphone capture while testing focus; temporary in-memory buffer only.
- Replays microphone capture amplified 1x–12x. May amplify ambient sounds, and does not establish that the motor is actually moving.
- Requests RECORD_AUDIO only when capture is started. Audio is not saved or uploaded.
