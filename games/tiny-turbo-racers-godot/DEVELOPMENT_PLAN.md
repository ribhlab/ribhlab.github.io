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
