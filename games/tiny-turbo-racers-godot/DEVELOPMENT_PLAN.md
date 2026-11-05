# DEVELOPMENT_PLAN — v0.8 Real Racing Controls, Tracks and Nature

**Branch:** \`tiny-turbo-racing-dev-v08\`. Based on validated \`tiny-turbo-racing-dev-v07\`; keep prior branches intact.

## Completed in this iteration
1. **Gamepad-style touch controls**: On-screen steering wheel with continuous analogue angle and independently held gas, brake, handbrake and nitro. Finger-ID routing supports multi-touch; keyboard W/A/S/D and SHIFT/SPACE remain for desktop. Disabled automatic acceleration in gameplay, throttle now controls torque.
2. **Three physically different tracks**: \`Midnight Harbor\` (original city night circuit), \`Sunset Coast\` (coastal spline and villas, sunset environment), \`Pine Mountain\` (technical spline with elevation, mountain lodges and more trees). Swapping routes reloads world/traffic/AI rather than changing a label.
3. **Four real competition objectives**: Circuit 3 laps + opponents, Sprint 83% of selected circuit, Time Trial 1 lap solo with persistent best time, Drift Challenge one lap with independent drift scoring. Each mode has correct end conditions and checkpoints.
4. **Mode and track selection UI** and updated telemetry.
5. **Actual scene-imported nature**: seven original Kenney CC0 3D tree meshes in vegetation zones; additional **photo-textured Poly Haven CC0 Pine Sapling Small** simplified to an Android LOD (6.5 MB), sparsely placed near road while keeping original optimized distant trees.
6. **Recorded sound**: six existing CC0 racing engine WAV loops crossfaded for virtual RPM, plus existing synthesized beeps / cues. Does not require network at runtime.
7. **Compatibility and performance**: supports Low/Medium/High city lighting, shadows and trees; vehicle traffic remains visible in Low (no invisible collision risk). Prior six CC BY artist car meshes and original night environment preserved.
8. **Automated regression**: legacy 3-lap run, Midnight Rush, physics/5-finger controls, source car imports, graphics presets, real foliage + audio + layouts + competition types and Android APK debug export.

## Next iterations (NOT implemented yet)
- Genuine VehicleBody3D independent wheel dynamics, textured wet roads and tunnels with lighting quality settings and LOD, AI line changes and overtaking; checkpoints with speed traps and lap timing display.
- Steering assist calibration with real Android touchscreen latency; controller haptics and native gamepad support; camera alternatives.
- Higher-detail photorealistic forests/rock layers optimized for mobile, far-field geometry instancing, camera-visible culling.
- Real race audio design (tyre, shifts, crash, music) with additional licensed recordings and full volume settings.
- Distinct time-trial leaderboards/local ghost, split times, track minimap, interactive garage upgrades.
- Measurements from **Galaxy S22 Ultra** and **a medium device**. 60 FPS / 30 FPS remain targets, not confirmed.
- Legal audit of famous automotive brand trademarks, genuine vehicle design and logo rights. Model artist CC BY is **not** manufacturer brand authorization. No official collaboration claimed.

## CI truth-in-reporting
GitHub Actions Godot headless tests validate logic; graphical CI screenshots are actual Godot frames but not phone screenshots. A successful debug APK export does not prove device FPS, Google Play compliance or brand rights.

---

# RibhLab Midnight Rush GT — DEVELOPMENT_PLAN

**Last updated:** 2026-11-05 | **Work branch:** \`tiny-turbo-racing-dev-v07\` | **Source branch:** \`tiny-turbo-midnight-rush-v06\`

## Principles
- Incremental, real Godot gameplay on Android; no fake high-fidelity screenshots.
- Preserve existing night-city geometry/traffic and separately developed six CC BY artist car meshes (copied from \`tiny-turbo-famous-brands-v06\`).
- Keep all game logic and files on this isolated branch until CI tests and target-device review pass. Never force-push or reset another developer's branch.
- Treat \`DEVELOPMENT_PLAN.md\` + \`DEVELOPMENT_LOG.md\` as durable checkpoints. For each cycle: check the HEAD SHA and latest CI, choose ONE important feature, implement, test, document, commit. Prefer no concurrent workflows updating gameplay files.
- All car brand assets are **non-official dev prototypes**. CC BY does not grant manufacturer trademark rights. The unbranded CC0 car remains available in prior source branch.
- Do not claim 60 FPS/30 FPS achieved without on-device profiling. GitHub Actions software rendering is not a Galaxy device.

## Baseline branch review (2026-11-05)
- \`tiny-turbo-famous-brands-v06\`: 6 commercial-use CC BY artist GLBs, garage switching; final GitHub Actions run **41945543087** successful.
- \`tiny-turbo-midnight-rush-v06\`: full neon city + urban street spline, 5 traffic AI, Nitro & Drift; GitHub Actions run **41944553038** successful.
- Branches diverged; v0.7 is based on Midnight City because this is a night-racing game and carries six distinct licensed car meshes into it.

## Iteration v0.7: first playable handling pass

| Area | Required outcome | Implementation |
|---|---|---|
| Longitudinal physics | Smooth automatic acceleration; service-brake force and engine resistance; nitro speed bonus | \`scripts/vehicle_dynamics.gd\` |
| Steering / Drift | Velocity-dependent steering response; controlled traction loss via handbrake; drift scoring based on speed and measured slip | \`vehicle_dynamics.gd\`, \`main.gd\` |
| Multi-touch | Independently track fingers for left/right/brake/drift/nitro and release independently | \`scripts/touch_controls.gd\`, gameplay HUD |
| Camera / Crash | Dynamic pursuit distance, look-ahead, boost FOV, short impact-feedback shake | \`main.gd\` |
| Car garage | Preserve six detailed source models, source credits and paint selection | \`scripts/brand_catalog.gd\`, \`real_car.gd\`, \`main.gd\` |
| Performance presets | Low/Medium/High materially control city draw, mobile lights, fog & shadows; persist in local config | \`main.gd\` |
| App lifecycle | Pause on focus loss / app background, handle Android back without uncontrolled quit | \`main.gd\`, \`project.godot\` |
| CI / packaging | Import, city and drift smoke test, 3-lap loop, touch, brake, six models, graphical scene and Android APK | \`.github/workflows/tiny-turbo-godot.yml\` |

## Planned subsequent cycles — not yet implemented / verified

1. **Handling pass 2:** steering assist on corners, progress-sensitive braking signs, visual wheel rotation and suspension animation; unit test handling on variable dt. Consider lower-detail LOD meshes for branded imports.
2. **Night city pass:** tunnel geometry with inside lighting, street signage, wet-road puddle PBR, tire smoke at wheel level, timed checkpoints. Hardware profiling on S22 Ultra and one midrange Android.
3. **Race content:** distinct Sprint and Time Trial routes, circuit race mode, AI passing, racing results and replay, fair reward balancing; exhaustive transition tests.
4. **Garage economy:** upgrades for accel/top speed/grip/nitro actually altering physics, with currency and saves; no dark patterns for a children's app.
5. **Controls + compatibility:** inspect real Android safe areas, gestures/back, refresh/resume, multi-touch on device, accessibility and controller support.
6. **Police chase and advanced VFX:** only once the preceding race mechanics and stability pass CI and mobile QA.
7. **Release readiness:** license/trademark permissions, Google Play Families compliance if directed at children, AAB signing, privacy policy, device benchmark logs.

## QA rule
- GitHub Actions \`--headless\` tests: **automated code / simulated gameplay, not a phone**.
- Xvfb screenshot: **actual Godot rendered frame on CI**, not representative of mobile FPS.
- APK export: **Android build**, does not establish install/run success on a specific handset.
- Galaxy S22 Ultra 60 FPS and mid-tier 30 FPS: **targets, unmeasured** until device logs are supplied.
