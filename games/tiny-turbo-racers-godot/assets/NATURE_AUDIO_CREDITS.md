# Third-party nature and recorded vehicle audio — RibhLab Midnight Rush v0.8

This file records the **actual sources and redistribution terms** for new game assets. The game is still a prototype; attribution for manufacturer-branded vehicles is documented separately in [BRANDED_MODEL_CREDITS.md](BRANDED_MODEL_CREDITS.md).

## Seven 3D tree mesh models — Kenney Nature Kit

- Source: https://kenney.nl/assets/nature-kit
- Mirrors/individual GLB distribution: https://github.com/Hidencod/tge-assets/tree/main/packs/nature-kit
- License published by Kenney: **CC0 1.0 Universal**, commercial redistribution allowed.
- Local files: `nature/tree-detailed.glb`, `tree-oak.glb`, `tree-pinetalla-detailed.glb`, `tree-pinetallb-detailed.glb`, `tree-palmdetailedtall.glb`, `tree-default.glb`, `tree-cone.glb`.
- Nature Kit models are stylized, non-photorealistic low/mid-poly real 3D meshes. They replace flat primitive green spheres but are not photographs or photogrammetry.
- Local route distribution: 32 trees around Harbor; 82 around Coast; 112 around Mountain at high quality; Low graphics shows fewer.

## Additional photo-textured and mesh-reduced tree — Poly Haven Pine Sapling Small

- Original author/site: Poly Haven — https://polyhaven.com/a/pine_sapling_small
- Public asset metadata: https://api.polyhaven.com/files/pine_sapling_small
- License: **CC0**, commercial use permitted.
- Source: 1k photographed leaf/bark texture sets and glTF geometry with dependencies.
- Local file: `nature/pine_sapling_ph_1k_lod.glb`.
- Transform: `gltf-transform simplify` with triangle target ratio 0.10 and error bound 0.02; converted to self-contained GLB, preserving the embedded photographic texture detail and materials for mobile.
- Approx. 6.5 MB optimized; sparsely instanced by the track rather than multiplied hundreds of times. LOD optimization can impact exact shape. On-device GPU memory and frame rate remain **unmeasured**.
- The API was used as an offline authoring-time download, **not queried or embedded in the Android game**.

## Six recorded car engine samples — OpenGameArt

- Creator: **domasx2**.
- Original page: https://opengameart.org/content/racing-car-engine-sound-loops
- License: **CC0**, originating in an actual public-domain car recording edited to loop with different pitch values.
- Verified source mirror: https://github.com/yashimosh/border-run/tree/main/public/sfx/engine
- Local files: `audio/engine/loop_0.wav`, `loop_1_0.wav`, `loop_2_0.wav`, `loop_3_0.wav`, `loop_4_0.wav`, `loop_5_0.wav`.
- Runtime: `arcade_audio.gd` uses six `AudioStreamPlayer` instances, pitched and crossfaded by approximate virtual RPM/speed; rival engine players are positioned using `AudioStreamPlayer3D`. Other UI beeps and skid effects remain synthesized, not recordings. This is not true microphone-recorded RPM from the six branded model vehicles.
- These assets were downloaded by `.github/workflows/tiny-turbo-v08-assets.yml`; the app needs no network to play the audio.

## Disclaimer

Model artists' author-granted CC BY licenses for the BMW, Mercedes, Porsche, Lamborghini, Ferrari and Audi **mesh files** are separate from manufacturer trademark/design/badge authorization. This project has not obtained automobile manufacturer sponsorship or official branding permission. Review and resolve trademark and design rights before publishing the game commercially on Google Play.
