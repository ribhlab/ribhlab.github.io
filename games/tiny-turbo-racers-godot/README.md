# Tiny Turbo Racers — Godot 4.7.2 (3D vertical slice)

**A separate next-generation playable prototype.** The existing WebView Android Studio v0.2 game remains untouched at `../tiny-turbo-racers`.

## This prototype

- A fully modeled **circular 3D racetrack** with road, curbs, lane markers and safety barriers.
- Four brightly colored environmental zones around the course: **Toy City, Tropical Beach, Candy Park, Dino Valley**.
- An original glossy 3D cartoon racer with rotating wheels, eyes, headlights, roof, spoiler and turbo flames.
- Three independent AI cars, chase camera, lap counter, position ranking, pickups and star rewards.
- Responsive touch **steer left / steer right / TURBO** buttons; desktop arrow keys, A/D and space.
- Synthesized, original engine audio with pitch responding to speed, positional rival car engines, star/bounce/turbo/fanfare sounds.
- Start, pause, garage color selection and restart. A single polished circuit is intentionally built before more tracks.
- Completely offline, no tracking, no advertising or network access. No proprietary art or sound assets.

## Open in Godot (recommended)

Install **Godot 4.7.2 standard edition** (not .NET), then in the project manager use **Import** and pick this folder's `project.godot`. Press **F6/F5** (Run Project). The GitHub Actions validator tests the project in headless Godot.

### To export to Android

In Godot install the 4.7.2 export templates using Editor → Manage Export Templates, configure Android SDK and Java 17 under Editor Settings → Export → Android, then Project → Export → Android. See Godot's official Android export docs.

The provided `export_presets.cfg` defines an Android debug preset for building an APK. A CI workflow attempts a headless debug export when templates can be installed. That output can be installed directly on a phone.

**Android Studio:** A Godot project is not an Android Studio Gradle project. To use Android Studio for the Godot Android Java wrapper, open Godot → Project → Install Android Build Template; then open the generated `android/build` folder in Android Studio. For normal gameplay development, use **Godot editor**, not Android Studio. The old native Android Studio project stays usable in its separate folder.

### Git clone / PowerShell

```powershell
git fetch origin
git switch tiny-turbo-racers-godot-v1
git pull --ff-only origin tiny-turbo-racers-godot-v1
$root = (git rev-parse --show-toplevel).Trim()
Set-Location (Join-Path $root 'games\tiny-turbo-racers-godot')
# Open this project.godot in Godot 4.7.2
```

This vertical slice is a genuine Godot 3D game, but **not yet a production-quality render identical to concept artwork**. Optimize performance and conduct real Android device testing before release. Publishing for young children requires Google Play Families compliance and a verified privacy policy.
