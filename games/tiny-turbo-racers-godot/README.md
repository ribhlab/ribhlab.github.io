# RibhLab Midnight Rush GT v0.9 — Free Steering and Live Minimap

**New gameplay improvement:** The car now has a real world-space 3D position and heading. The analog wheel changes the car's direction, while progressive arcade steering assistance helps follow curving circuits. A track-edge impact reduces speed. A minimap follows the actual x/z position of the player's car and AI competitors. Three route layouts, four race modes, original CC0 foliage, recorded engine RPM loops and the six existing separately licensed sports cars are retained.

**Development prototype only.** Famous manufacturer vehicle names, designs and trademarks are **not officially licensed** by this game. Artist CC BY 4.0 credit does not itself grant any car manufacturer's trademark or design rights. The project is not ready for public commercial Play Store distribution without appropriate review. Physically based PBR cars/terrain do not mean it is photorealistic. Device FPS numbers remain targets until tested on real hardware.

## Update an existing Windows checkout

Close Godot, open Windows PowerShell **inside any directory of the existing Git repo**, and paste:

```powershell
$ErrorActionPreference = "Stop"
$repo = (git rev-parse --show-toplevel).Trim()
Set-Location $repo
git stash push -u -m "Backup before real driving v0.9" -- games/tiny-turbo-racers-godot
git fetch origin
if (git branch --list tiny-turbo-racing-dev-v09) {
    git switch tiny-turbo-racing-dev-v09
} else {
    git switch --track origin/tiny-turbo-racing-dev-v09
}
git pull --ff-only origin tiny-turbo-racing-dev-v09
Set-Location (Join-Path $repo "games\tiny-turbo-racers-godot")
powershell -ExecutionPolicy Bypass -File .\SETUP_WINDOWS.ps1
```

Then open `scenes/main.tscn`, press **F5**, select a track and mode, and try the steering wheel with simultaneous GAS/BRAKE/DRIFT/NITRO touch zones. Use keyboard A/D/W/S and SHIFT/SPACE in the editor.

**Build evidence:** [GitHub Actions racing APK workflow](https://github.com/ribhlab/ribhlab.github.io/actions/workflows/tiny-turbo-godot.yml). Download the artifact from the latest **successful** run for branch `tiny-turbo-racing-dev-v09`, checking the commit SHA.

---

# RibhLab Midnight Rush GT v0.8 — Nature, Racing Modes, Manual Wheel and Recorded Engines

This is the **actual playable Godot Android racing project**, not image mockups. The v0.8 branch inherits the v0.7 driving and night racing project.

**What's new:** seven authentic 3D Kenney tree models (CC0) and one mobile-decimated photo-textured Pine Sapling Small from Poly Haven (CC0); three actual spline road layouts (Midnight Harbor, Sunset Coast and Pine Mountain); four playable game modes (Circuit, Sprint, Time Trial solo with local personal best, Drift Challenge); a **live analog steering wheel** + GAS/BRAKE/HANDBRAKE/NITRO controls with independent finger input; and **six original recorded CC0 engine WAV loops** crossfaded with virtual RPM. The photo tree is used sparingly to protect Android frame rates. All textures/samples are packed offline.

**How to play:** Start the game (F5), choose **CHOOSE RACE** → your preferred road and race objective → **RACE NOW**. On desktop: W/UP accelerates, A/D or arrow keys steer, S/DOWN brakes, SHIFT drifts, SPACE uses Nitro. On Android use the steering wheel at bottom left and the separate pedals on the right; multiple fingers can be held simultaneously. Drive through checkpoints to the finish; Sprint is a point-to-point portion, Time Trial is solo, Drift rewards sideways slides. Open **TUNE YOUR CAR** to select the six existing independently imported artist models.

### Windows PowerShell update (run from any location inside the existing cloned repository)

First close Godot to prevent local \`project.godot\` and \`main.tscn\` edits from blocking Git pull:

\`\`\`powershell
$ErrorActionPreference = "Stop"
$repo = (git rev-parse --show-toplevel).Trim()
Set-Location $repo
git stash push -u -m "Backup before TinyTurbo v0.8" -- games/tiny-turbo-racers-godot
git fetch origin
if (git branch --list tiny-turbo-racing-dev-v08) {
    git switch tiny-turbo-racing-dev-v08
} else {
    git switch --track origin/tiny-turbo-racing-dev-v08
}
git pull --ff-only origin tiny-turbo-racing-dev-v08
if ($LASTEXITCODE -ne 0) { throw "Git update failed" }
Set-Location (Join-Path $repo "games\tiny-turbo-racers-godot")
powershell -ExecutionPolicy Bypass -File .\SETUP_WINDOWS.ps1
\`\`\`

**Dev documentation:** [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md), [DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md), [NATURE_AUDIO_CREDITS.md](assets/NATURE_AUDIO_CREDITS.md). The v0.8 GitHub Actions workflow checks assets, real sound mode, independent road layouts, race transitions and Android export.

**Limitations:** Trees mix optimized low-poly real meshes with a sparse photo-textured species, not a dense photoreal AAA forest. The racing model remains physics-inspired, assisted spline steering rather than independent wheel/body dynamics. Actual Android FPS on Galaxy S22 Ultra or mid-range devices has NOT been benchmarked. Six CC BY car meshes are from artists; automobile branding/trademark rights must be resolved before distributing as a commercial branded title.

---

# RibhLab Midnight Rush GT v0.6 — Original street racing game

This is the **night street-racing branch** of the Godot 4.7.2 prototype. It aims for the *genre* of premium arcade street racers (night racing, custom cars, Nitro, drift, traffic), **not a copy of Need for Speed**. There are no Need for Speed logos, music, game files or licensed real-world car manufacturer marks in this project.

## Playable in v0.6

- Actual native **3D neon harbor metropolis**: 112 deterministic roadside towers, 30 skyline buildings, 4 overpasses, illuminated windows and neon billboards, 164 lampposts, 12 actual lamps, port containers, pedestrians-free closed racing route.
- **Spectral GT RS** sports car, 258-mesh imported Blender glTF, CC0. Player and three rivals have full-size detailed PBR body and brake/glass parts. Runtime 5 traffic vehicles are lighter simplified LOD 3D meshes to protect Android performance.
- Curving 3D street circuit, asphalt photographic PBR, four traffic lanes, sidewalks, guardrails, checkpoints and a starting light gantry.
- Driving controls: **A/D or left/right = steering**, **Space = Nitro**, **Shift = Drift**. Touch buttons added for left/right, DRIFT and NITRO. Position, lap, speed, near misses and drift points in neon HUD.
- Nitro charges slowly by driving and faster through deliberate drifting or safe near misses. Traffic contact slows you down; finished races reward your accumulated credits.
- Original procedural/synthesized audio already used in v0.5. Offline only, no ads, traffic logs, API calls or tracking.
- **Godot test** `ci/midnight_test.gd` checks actual city meshes, 5 traffic vehicles, moving traffic, drift points and rechargeable Nitro.

## What this is not yet

A vertical slice, **not yet an AAA photorealistic open-world game**. The current course is one closed track, not a full navigable city map. The street traffic cars are lightweight LOD meshes; cars have stylized arcade drivetrain, not individual 4-wheel suspension or licensed manufacturer sounds. Pursuit AI, destructible environments, cinematic menus, upgrade economy, online multiplayer, mobile performance tuning and store preparation still need development.

## Download / build

- [Source branch on GitHub](https://github.com/ribhlab/ribhlab.github.io/tree/tiny-turbo-midnight-rush-v06/games/tiny-turbo-racers-godot)
- [Android CI workflow](https://github.com/ribhlab/ribhlab.github.io/actions/workflows/tiny-turbo-godot.yml) — open the newest successful run and download `tiny-turbo-godot3d-debug-apk`.
- Open `scenes/main.tscn` in **Godot 4.7.2**, select `EditorPreview > ShowcaseCamera`, activate the camera preview, press F5 to play.

### PowerShell — update from any folder inside the existing repository

```powershell
$ErrorActionPreference = "Stop"
$repo = (git rev-parse --show-toplevel).Trim()
Set-Location $repo

# Back up locally modified Godot files before branch switch
git stash push -u -m "Backup before Midnight Rush v0.6" -- games/tiny-turbo-racers-godot

git fetch origin
if (git branch --list tiny-turbo-midnight-rush-v06) {
    git switch tiny-turbo-midnight-rush-v06
} else {
    git switch --track origin/tiny-turbo-midnight-rush-v06
}
git pull --ff-only origin tiny-turbo-midnight-rush-v06

Set-Location (Join-Path $repo "games\tiny-turbo-racers-godot")
powershell -ExecutionPolicy Bypass -File .\SETUP_WINDOWS.ps1
```

Do **not** run `git stash pop` immediately or it may restore old version settings over these files. A real phone test is required for performance, clipping, touchscreen behavior and thermals before publishing.

### Licenses

Third-party 3D sports car and photographed road textures are **CC0**. See [assets/ASSET_LICENSES.md](assets/ASSET_LICENSES.md). Godot Engine is MIT. The neon-city code and game logic in this branch are original. The game is not associated with Electronic Arts or Criterion Games.

---

# Tiny Turbo Racers — Real GT Racing v0.5 (Godot 4.7.2)

This branch replaces the toy-ring race and primitive-looking cars with a **licensed detailed external sports-car model** and a **realistic original motorsport circuit**.

## What is truly new in v0.5?

- **Imported sports car, not cubes:** `assets/vehicles/spectral_gt_rs_game_ready.glb`, a 4.69 MB sports car designed in Blender and exported as GLB; **258 independent mesh objects**, 23 base materials, wheels, brakes, glass, clearcoat body panels and cockpit. Four instances are used for the player and AI opponents; body panels receive selectable racing colors. CC0 source: https://github.com/JaronKBragg7337/spectral-gt-rs
- **Actual racing course layout:** `scripts/real_track.gd` creates a closed arc-length-sampled Catmull-Rom GP circuit with a proper main straight, elevation variations, S bends and a hairpin sequence. No longer a plain 84-meter-radius circle.
- **Motorsport architecture:** full pit lane, garages, control tower, four grandstands, welded metal safety barriers, red/white corner kerbs, racing lines, brake-distance boards, gantry and start lights, trackside marshals.
- **Photographic road PBR:** authentic CC0 Poly Haven Asphalt 02 1K diffuse, normal, roughness maps by Rob Tuytel. The road genuinely uses photo textures, not hand-painted fake gravel. https://polyhaven.com/a/asphalt_02
- **Mobile-first native Godot:** built-in Jolt physics, physically inspired lateral grip and drive torque, native Vulkan Mobile renderer, clearcoat metals, long camera chase and original offline audio.

### Asset provenance

See [ASSET_LICENSES.md](assets/ASSET_LICENSES.md). All externally sourced 3D model and texture files have verified CC0 licensing permitting commercial use. No proprietary real-brand logos or licensed motor-racing track layouts are included.

### Quality verification

The GitHub Actions workflow validates scene/script import, a complete 3-lap simulation, car mesh import, photo PBR track, Jolt colliders, editor preview, and debug Android APK export. Optional graphical QA produces a real screenshot from Godot under software rendering on CI when available.

### Exact PowerShell command after each update (from your existing Git checkout)

```powershell
$ErrorActionPreference = "Stop"
$repo = (git rev-parse --show-toplevel).Trim()
Set-Location $repo

# Safely preserve locally edited project files before changing branches
git stash push -u -m "TinyTurbo backup before real GT v0.5" -- games/tiny-turbo-racers-godot

git fetch origin
if (git branch --list tiny-turbo-real-racing-v05) {
    git switch tiny-turbo-real-racing-v05
} else {
    git switch --track origin/tiny-turbo-real-racing-v05
}
git pull --ff-only origin tiny-turbo-real-racing-v05
$project = Join-Path $repo "games\tiny-turbo-racers-godot"
Set-Location $project
powershell -ExecutionPolicy Bypass -File .\SETUP_WINDOWS.ps1
```

The game is authored in Godot, not the old WebView Android Studio project. Open **scenes/main.tscn**, select **EditorPreview → ShowcaseCamera**, then enable Camera Preview. Press **F5** to play.

**Limitations:** This is an actual licensed detailed sports-car model and a proper motorsport circuit with photographic road textures, but it is **not** an official FIA circuit, exact licensed Ferrari/Lamborghini model or photorealistic AAA engine. AI vehicles reuse the same base model with paint variations; tire/contact physics is still assisted arcade driving rather than independent-wheel rigid-body simulation. Test on your actual Android phone for FPS/heat. For Google Play, complete Families compliance and release signing.

---


**A separate next-generation playable prototype, upgraded to native Jolt physics + PBR rendering.** The existing WebView Android Studio v0.2 game remains untouched at `../tiny-turbo-racers`.

## v0.4 premium technology stack (already integrated)

| Godot built-in system | Real implementation | Mobile rationale |
| --- | --- | --- |
| **Jolt Physics 3D** | Selected physics backend and StaticBody3D floor/contact material | Built into Godot 4.7, no outdated GDExtension |
| **Godot Vulkan Mobile renderer** | Enabled in `project.godot`; custom sun, real shadow caster, glow, procedural sky and depth fog | Better lighting and PBR support than Compatibility on capable devices |
| **StandardMaterial3D PBR** | Car clearcoat paint, chrome rims, rough rubber, reflective glass, procedural asphalt normal map | Physically based shading rather than flat cartoon coloring |
| **Native CPUParticles3D** | Skid dust and turbo haze behind the player car | Mobile-compatible VFX without downloading sample packs |
| **Native MultiMeshInstance3D** | 580 instanced patches of vegetation around the circuit | Batches foliage and avoids hundreds of separate draw calls |
| **VehicleDynamics** | Original GDScript motor force, quadratic drag, lateral grip, progressive steering and skid response | Physics-inspired, accessible control; *not* a fully simulated rigid-body car yet |

The prototype creates assets at runtime without any externally licensed 3D meshes, textures, audio recordings, or network calls. It remains family friendly and offline. These upgrades target higher visual fidelity but do **not** make the build photorealistic or equivalent to a professional high-poly trailer. A capable Vulkan Android GPU is recommended; optimize and test on actual devices.

## This prototype

- A fully modeled **circular 3D racetrack** with road, curbs, lane markers and safety barriers.
- Four brightly colored environmental zones around the course: **Toy City, Tropical Beach, Candy Park, Dino Valley**.
- An original glossy 3D cartoon racer with rotating wheels, eyes, headlights, roof, spoiler and turbo flames.
- Three independent AI cars, chase camera, lap counter, position ranking, pickups and star rewards.
- Responsive touch **steer left / steer right / TURBO** buttons; desktop arrow keys, A/D and space.
- Synthesized, original engine audio with pitch responding to speed, positional rival car engines, star/bounce/turbo/fanfare sounds.
- Start, pause, garage color selection and restart. A single polished circuit is intentionally built before more tracks.
- Completely offline, no tracking, no advertising or network access. No proprietary art or sound assets.

## See the 3D scene inside Godot's editor

Previous versions showed only the empty Node3D and axes when `main.tscn` was open, because all track and car geometry was created by `main.gd::_ready()` at runtime.

**Fixed:** `scenes/main.tscn` now includes a saved `EditorPreview` node with an `@tool` script. In the graphical Godot editor it generates the **same world builder and the same four procedural 3D car designs** without starting the race or downloading assets.

1. Update the project branch and reopen `scenes/main.tscn` (close/reopen the scene if it was already open when source files were updated).
2. Open the **3D** tab. You should see the track, scenery, and four toy cars in the scene viewport.
3. For a guaranteed angle, expand `EditorPreview`, select `ShowcaseCamera`, and activate the camera's **Preview** toggle in the 3D viewport.
4. Alternatively, select `FocusTrackStart` under `EditorPreview`, then press `F` to focus the track.
5. Press `F5` to launch the **playable** game. The editor preview is disabled in the Android build, so it does not duplicate meshes at runtime.

The preview meshes are **temporary editor-only generated nodes** and intentionally do not appear individually in the Scene tree dock or get saved into `main.tscn` (this avoids serializing hundreds of meshes and duplicating them at runtime). Do not manually save generated preview meshes into the playable scene.

## Open in Godot (recommended)

Install **Godot 4.7.2 standard edition** (not .NET), then in the project manager use **Import** and pick this folder's `project.godot`. Press **F6/F5** (Run Project). The GitHub Actions validator tests the project in headless Godot.

### To export to Android

In Godot install the 4.7.2 export templates using Editor → Manage Export Templates, configure Android SDK and Java 17 under Editor Settings → Export → Android, then Project → Export → Android. See Godot's official Android export docs.

The provided `export_presets.cfg` defines an Android debug preset for building an APK. GitHub Actions validates script parsing, scene startup, simulated 3-lap gameplay, Jolt/PBR/dust QA, and produces a **debug APK** using official Godot Android export templates. Its artifact can be installed directly on an Android phone.

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

This vertical slice uses actual 3D PBR rendering and a physics-inspired racing model, but **is not yet a full rigid-body driving simulator or a production-quality render identical to concept artwork**. Optimize performance and conduct real Android device testing before release. Publishing for young children requires Google Play Families compliance and a verified privacy policy.

## Update an existing Windows checkout (from any nested folder)

Open PowerShell inside the existing `ribhlab.github.io` Git checkout and run:

```powershell
$ErrorActionPreference = 'Stop'
$repo = (git rev-parse --show-toplevel).Trim()
Set-Location $repo
git fetch origin
git switch tiny-turbo-racers-godot-v1
git pull --ff-only origin tiny-turbo-racers-godot-v1
Set-Location (Join-Path $repo 'games\tiny-turbo-racers-godot')
powershell -ExecutionPolicy Bypass -File .\SETUP_WINDOWS.ps1
```

The Godot editor's F5 runs the 3D game. Download the APK from the newest passing [GitHub Actions workflow](https://github.com/ribhlab/ribhlab.github.io/actions/workflows/tiny-turbo-godot.yml).

## Official technical references

- [Godot: Using Jolt Physics](https://docs.godotengine.org/en/stable/tutorials/physics/using_jolt_physics.html)
- [Godot: Rendering backends and limitations](https://docs.godotengine.org/en/stable/tutorials/rendering/renderers.html)
- [Godot: CPUParticles3D](https://docs.godotengine.org/en/stable/classes/class_cpuparticles3d.html)

Godot is MIT licensed. All new GDScript, meshes, textures and synthesized sounds for this version are original to this project. If photorealistic third-party PBR packs, licensed vehicle model sets or recorded engine samples are introduced later, preserve their author/license attribution and shipping rights.
