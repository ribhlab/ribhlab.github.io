# RivoMx — Kotlin Android AR Measurement

Experimental v0.1.0 — designed for Samsung Galaxy S22 Ultra, which supports ARCore Depth API.

## Implemented
- Live camera via ARCore + OpenGL ES 2.0 (ARCore owns the camera)
- ARCore Depth API automatic mode when supported; plane/feature fallback
- Distance: tap two points on tracked surfaces
- Length + width: tap two endpoints for length, then two for width
- Estimated rectangular area (assumes a rectangle)
- Units mm / cm / m / inches
- Tracking status and source of each 3D hit
- Local history and PDF export via Android document picker
- JUnit arithmetic tests
- No analytics, network permissions or uploads

## Open in Android Studio
1. Select branch named rivomx-android in ribhlab/ribhlab.github.io.
2. Download ZIP for that branch and extract, or clone only that branch.
3. Android Studio → Open → select the root containing settings.gradle.kts.
4. Install JDK 17 and Android SDK 36. Allow Gradle sync.
5. Run on Samsung Galaxy S22 Ultra and grant camera permission.
6. Install or update Google Play Services for AR if requested.
7. Move phone slowly around textured, well-lit surfaces and tap endpoints.

## Gradle
AGP 8.13.2, Kotlin 2.3.21, Compose, Gradle 8.13, ARCore 1.56.0.
Run ./gradlew testDebugUnitTest and ./gradlew assembleDebug.

## Limitations / known unfinished work
This is a source-code foundation, not a hardware-tested release. Android builds and live S22 Ultra measurements require device testing. ARCore's estimate is not unlimited precision. Results depend on surface, lighting, motion and tracking. The area formula assumes the measured sides form a rectangle. It cannot reliably measure any object from a single static photo. Auto object edge detection, OpenCV, ML Kit, calibration workflows, annotated photos and per-measurement PDFs are planned, not implemented yet.

## Privacy
History stored locally; PDF saved only to the destination selected in Android picker.

Copyright (c) RibhLab — all rights reserved until a licence is explicitly chosen.
