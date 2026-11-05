# Third-party assets and commercial license verification — Tiny Turbo Racers GT v0.5

All downloaded assets in this upgrade were obtained from sources that publish an **explicit CC0 1.0** public-domain dedication and may be included in a commercial Android game. No Ferrari, Lamborghini, Porsche, F1, Gran Turismo or other manufacturer/team branding is licensed or included.

## Real 3D sports-car asset

- File: `assets/vehicles/spectral_gt_rs_game_ready.glb`
- Original title: **Spectral GT RS**, an original performance-car design, not a branded production car
- Author: **Jaron K. Bragg** (JaronKBragg7337)
- Repository: https://github.com/JaronKBragg7337/spectral-gt-rs
- Model: https://github.com/JaronKBragg7337/spectral-gt-rs/blob/main/spectral_gt_rs_game_ready.glb
- License: **Creative Commons Zero v1.0 Universal (CC0-1.0)**: https://github.com/JaronKBragg7337/spectral-gt-rs/blob/main/LICENSE
- GLB format: 4,688,844 bytes, **258 actual imported meshes**, 23 materials, separate glass/body/cockpit/wheels and brakes.
- Orientation in source: front +X; `real_car.gd` rotates the imported vehicle to the game -Z forward direction.
- The scene is imported by Godot 4's glTF importer and can be inspected in the Godot editor.

## Photographed PBR road asphalt

- Files:
  - `assets/textures/asphalt_02_diff_1k.png`
  - `assets/textures/asphalt_02_nor_gl_1k.png`
  - `assets/textures/asphalt_02_rough_1k.png`
- Asset: **Asphalt 02** by **Rob Tuytel**, via Poly Haven.
- Source: https://polyhaven.com/a/asphalt_02
- Direct original download host: `dl.polyhaven.org`
- License: **CC0** (per Poly Haven product listing).
- These are genuine photographic/albedo, tangent-space OpenGL normal and roughness maps. They are used by `realism_materials.gd` for the full circuit and pit lane.

### Implementation notes

The real circuit geometry, original RibhLab race infrastructure, physics controller and UI scripts are authored for this project. The track is an **original GP-style circuit**, not an exact reproduction of a real-world FIA-licensed racetrack, so no real-world track trademarks or claims of official affiliation apply.

For performance, the original 258-mesh model is far more detailed than the toy-car prototype. The v0.5 prototype deliberately keeps just 4 active cars, disables expensive environment reflections for distant props, and uses Godot's mobile renderer. Test frame-rate, memory and thermal throttling on the actual target Android hardware. If needed, prepare LOD1/LOD2 meshes from the provided CC0 source to reduce draw calls.

CC0 removes the need for mandatory attribution, but author/source acknowledgement is voluntarily retained here.
