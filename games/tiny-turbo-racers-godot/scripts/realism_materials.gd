extends RefCounted
## Native Godot 4 PBR materials and procedural, seamless-ish surface maps.
## No imported models, third-party textures, licensing risks or network downloads.

const SIZE: int = 192

static func car_paint(color: Color) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = color
	m.metallic = 0.32
	m.roughness = 0.16
	m.clearcoat_enabled = true
	m.clearcoat = 0.83
	m.clearcoat_roughness = 0.09
	return m

static func polished_glass(color: Color = Color("#80cafa")) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = color
	m.metallic = 0.21
	m.roughness = .10
	m.clearcoat_enabled = true
	m.clearcoat = 0.72
	m.clearcoat_roughness = 0.06
	return m

static func rubber() -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = Color("#1e2431")
	m.roughness = 0.94
	m.metallic = 0.0
	return m

static func chrome(color: Color = Color("#d4e7ff")) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = color
	m.roughness = 0.16
	m.metallic = 0.82
	m.clearcoat_enabled = true
	m.clearcoat = 0.6
	return m

static func asphalt() -> StandardMaterial3D:
	var noise := FastNoiseLite.new()
	noise.seed = 87331
	noise.noise_type = FastNoiseLite.TYPE_SIMPLEX_SMOOTH
	noise.frequency = 0.10
	noise.fractal_type = FastNoiseLite.FRACTAL_FBM
	noise.fractal_octaves = 4
	var albedo := Image.create(SIZE,SIZE,false,Image.FORMAT_RGBA8)
	var normals := Image.create(SIZE,SIZE,false,Image.FORMAT_RGBA8)
	for y in range(SIZE):
		for x in range(SIZE):
			var xx := float(x)
			var yy := float(y)
			var h: float = noise.get_noise_2d(xx,yy)
			var coarse: float = noise.get_noise_2d(xx*0.25,yy*0.25)
			var gravel: float = 0.7*h + 0.3*coarse
			var shade: float = clampf(0.80 + gravel*.23,0.55,1.0)
			# Dark hairline fractures are represented without paid asphalt assets.
			var crack: float = absf(noise.get_noise_2d(xx*.55+96,yy*.41+300))
			if crack < .015 and coarse > .18:
				shade *= .62
			albedo.set_pixel(x,y,Color(shade*.97,shade*.98,shade,1))
			var dx: float = noise.get_noise_2d(xx+1.0,yy)-noise.get_noise_2d(xx-1.0,yy)
			var dy: float = noise.get_noise_2d(xx,yy+1.0)-noise.get_noise_2d(xx,yy-1.0)
			normals.set_pixel(x,y,Color(clampf(.5+dx*.48,0,1),clampf(.5+dy*.48,0,1),1.0,1.0))
	albedo.generate_mipmaps()
	normals.generate_mipmaps()
	var m := StandardMaterial3D.new()
	m.albedo_color = Color.WHITE
	m.albedo_texture = ImageTexture.create_from_image(albedo)
	m.normal_enabled = true
	m.normal_texture = ImageTexture.create_from_image(normals)
	m.normal_scale = 0.42
	m.vertex_color_use_as_albedo = true
	m.roughness = 0.92
	m.metallic = 0.025
	m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	return m
