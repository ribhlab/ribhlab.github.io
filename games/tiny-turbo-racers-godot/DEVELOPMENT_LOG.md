# RibhLab Midnight Rush GT — DEVELOPMENT_LOG

## 2026-11-05 — v0.7 cumulative development iteration

**Starting point:** \`tiny-turbo-midnight-rush-v06\` SHA \`a1ae8c97d157636b1c5a93630063bd93da31f37f\`. The comparison with \`tiny-turbo-famous-brands-v06\` revealed divergent game branches. Neither original branch was overwritten.

**Real implemented changes:**
- Created isolated branch \`tiny-turbo-racing-dev-v07\`.
- Copied six already-licensed artist 3D GLB assets by existing Git object SHA, without lossy re-encoding; ported source metadata and garage model loader.
- Replaced the simplistic always-accelerating lateral simulation with torque fade, actual brake force, progressive steering, velocity-dependent traction, handbrake grip reduction, and skid state. \`ci/handling_test.gd\` verifies acceleration and braking.
- Added touchscreen finger-ID routing; simultaneous STEER + BRAKE + DRIFT + NITRO preserved, releasing one finger does not cancel the others. Added a visible BRAKE control.
- Smoothed chase camera with speed-aware framing / look-ahead and short collision shake; Nitro influences FOV.
- Kept Midnight city and its 5 moving traffic vehicles, near misses, drift points and earned nitro. Drift rewards now require measurable slide and nonzero speed/steer, not merely the drift key.
- Added garage with six independently loaded vehicles, saved selection and artist/source attribution.
- Added working Low/Medium/High settings (lighting, city/tower draw, fog and traffic detail), locally saved. **Performance gains are not yet measured on actual devices.**
- Android lifecycle: back gesture routed to pause / menu and background/focus loss pauses an active race.
- Added Godot CI regression for five simultaneous touch pointers, brake, nitro, drift, pause, replay and six actual imported GLBs.
- Android app metadata updated to version v0.7.

**Automated CI status:** See the successful Actions run link in the accompanying user report or subsequent log entry. Earlier initial v0.7 run passed gameplay and touch tests; it exposed an obsolete assertion requiring 100 meshes per imported car even though optimized BMW had 94. Adjusted QA threshold to 8 and retained the dedicated six-car import test.

**On-device validation:** NOT YET PERFORMED. No claim of measured FPS on Galaxy S22 Ultra or mid-tier Android. Dedicated hardware run still necessary.

**Open limitations:** Simulated arcade vehicle (not full rigid-body wheel suspension), no complete Sprint/Time Trial/Police Chase yet, no measured FPS, six car models used in **non-official developer preview** pending third-party brand/trademark rights review. Audio is synthesized rather than licensed recordings; visual wheel turning on GLB models needs artist-specific wheel-bone mapping.

**Next cycle:** benchmark on Android and work on wheel/spin visual, track feedback and checkpoints; do not add police chases until handling is stable.
