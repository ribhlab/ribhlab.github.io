# 🏎️ Tiny Turbo Racers — Android Studio Edition

**Original children's racing game • RibhLab • v0.2 3D + Sound (November 2026).**

Four smiling cartoon cars, four themed worlds, 3-lap races, 3 AI opponents, star pickups, turbo boost, cute garage, paint colors, stored scores, and simple kid-sized left/right touch controls.

## Where is the source?

The full Android Studio project lives in this folder:
`games/tiny-turbo-racers`.

The Android Activity loads an **offline WebGL 3D racing engine** with procedural 3D car meshes, 3D wheels, perspective driving camera, animated roadside scenery, and four distinct racing landscapes. A 2D Canvas fallback remains for devices without WebGL. The 3D graphics use original code without downloading any 3D libraries, textures, sounds, or paid assets.

Audio uses **Web Audio** synthesis (no downloaded or copyrighted audio files): engine RPM/wind, race start/countdown, turbo, skid, star pickup, lap and victory fanfare with a quiet original race tune. Sound can be muted from the app's main menu. This is a **stylized low-poly 3D implementation**, not yet the same high-detail, sculpted production 3D quality as the concept artwork.

### Windows + Android Studio

```powershell
git clone -b tiny-turbo-racers-v01 --single-branch https://github.com/ribhlab/ribhlab.github.io.git
cd ribhlab.github.io\games\tiny-turbo-racers
& "C:\Program Files\Android\Android Studio\bin\studio64.exe" .
```

If Android Studio is installed elsewhere, open it via Start Menu > **File > Open**, then select `ribhlab.github.io\games\tiny-turbo-racers`.

- Install Android SDK 36 and JDK 17 or later when prompted.
- Gradle: **8.13**, Android Gradle Plugin **8.13.2**, target **API 36**.
- Select an Android phone/emulator and click **Run app** (green ▶).
- Android Studio > Build > Build APK(s) for a debug installer.
- Android Studio > Build > Generate Signed App Bundle / APK for Play Store; use **AAB**, release signing and Play App Signing.

A GitHub Actions workflow at `.github/workflows/tiny-turbo-racers.yml` validates JS, builds `app-debug.apk` and uploads it as the `tiny-turbo-racers-debug-apk` artifact, alongside browser preview assets. Its wrapper-generation step can also populate the missing wrapper scripts/JAR in this branch when repository workflow write permissions are enabled.

### Gameplay

1. Tap **Let's Race**, pick one of **Toy City**, **Beach Track**, **Candy Park**, **Dino Valley**.
2. Tap **Start Race**, steer with **❮ ❯**, use **⚡ TURBO** after its cooldown.
3. Collect ⭐ by driving toward them; complete three laps against three rival toy cars.
4. Win stars, choose a different car or change car colors in **My Cars**.
5. Tap **Ⅱ** to pause. Everything runs offline.

### Source layout

```text
app/
  src/main/AndroidManifest.xml
  src/main/java/com/ribhlab/tinyturboracers/MainActivity.java
  src/main/res/drawable/ic_launcher.xml
  src/main/assets/index.html
  src/main/assets/style.css
  src/main/assets/game.js
  src/main/assets/race3d.js   # Native offline WebGL 3D scene
  src/main/assets/sound.js    # Original generated race audio
  src/main/assets/race-preview.html # QA scene
app/build.gradle
build.gradle
settings.gradle
gradle.properties
gradle/wrapper/gradle-wrapper.properties
```

### Shipping notes

- This is a **playable v0.2 build** with real WebGL 3D meshes and synthesised racing sounds; still requires real-device testing, stronger car art/animation, optimizations and accessibility QA before store launch.
- There is **no AdMob integrated yet**: child-directed Google Play apps must comply with Families policy and approved SDK rules before monetization. See `PRIVACY.md`.
- Change the app name/package only if needed, and create your own signing keystore.
- Full Google Play listing, content rating, privacy policy URL, app signing, screenshots and store review remain outstanding.
- The source code and drawings here are original and not a reskin of an existing proprietary racing game.
