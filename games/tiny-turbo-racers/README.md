# 🏎️ Tiny Turbo Racers — Android Studio Edition

**Original children's racing game • RibhLab • v0.1 prototype (November 2026).**

Four smiling cartoon cars, four themed worlds, 3-lap races, 3 AI opponents, star pickups, turbo boost, cute garage, paint colors, stored scores, and simple kid-sized left/right touch controls.

![Playful racing game - gameplay designed to be cheerful and kid-friendly](https://placehold.co/1200x20/ffffff/ffffff.png)

## Where is the source?

The full Android Studio project lives in this folder:
`games/tiny-turbo-racers`.

The Android Activity loads the **offline HTML5 Canvas engine** from `app/src/main/assets`. No game engine download, ads, permissions, remote APIs, or paid assets needed. Racing visuals are **procedurally drawn 2.5D**, not the full 3D models shown in the earlier concept art; that concept is the visual target for future iterations.

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

A GitHub Actions workflow at `.github/workflows/tiny-turbo-racers.yml` builds `app-debug.apk` and uploads it as the `tiny-turbo-racers-debug-apk` artifact. Its wrapper-generation step can also populate the missing wrapper scripts/JAR in this branch when repository workflow write permissions are enabled.

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
app/build.gradle
build.gradle
settings.gradle
gradle.properties
gradle/wrapper/gradle-wrapper.properties
```

### Shipping notes

- This is a **playable first prototype**; polish, mobile performance testing and 3D assets remain future development.
- There is **no AdMob integrated yet**: child-directed Google Play apps must comply with Families policy and approved SDK rules before monetization. See `PRIVACY.md`.
- Change the app name/package only if needed, and create your own signing keystore.
- Full Google Play listing, content rating, privacy policy URL, app signing, screenshots and store review remain outstanding.
- The source code and drawings here are original and not a reskin of an existing proprietary racing game.
