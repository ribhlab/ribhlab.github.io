# Tiny Turbo Racers — Godot 4.7.2 / Realism v0.4

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
