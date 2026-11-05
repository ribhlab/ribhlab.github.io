extends Node3D
const RealismMaterials = preload("res://scripts/realism_materials.gd")
## Original procedural glossy cartoon racer, compatible with mobile OpenGL.
## Model faces local -Z; attach a rotating camera behind it.

var paint: Color = Color("#f83f53")
var character_id: int = 0
var wheels: Array[Node3D] = []
var flames: Array[MeshInstance3D] = []
var dust_emitters: Array[CPUParticles3D] = []
var glow_material: StandardMaterial3D
var body_material: StandardMaterial3D
var elapsed: float = 0.0

func configure(new_paint: Color, new_id: int = 0) -> void:
	paint = new_paint
	character_id = new_id

func _ready() -> void:
	_build()

func set_paint(color: Color) -> void:
	paint = color
	if body_material != null:
		body_material.albedo_color = color

func animate_car(delta: float, speed: float, steering: float, turbo: bool) -> void:
	elapsed += delta
	for i in range(wheels.size()):
		var wheel: Node3D = wheels[i]
		wheel.rotation.x -= delta * speed / 0.43
		# The front axle (local -Z) gently points toward the turn.
		wheel.rotation.y = lerpf(wheel.rotation.y, steering * 0.19 if i%2==0 else 0.0,
			clampf(delta*9.0,0,1))
	for dust in dust_emitters:
		dust.emitting = (speed>11.0 and absf(steering)>.62) or turbo
	for flame in flames:
		flame.visible = turbo
		if turbo:
			flame.scale.z = 0.75 + 0.26 * sin(elapsed * 29.0)
	rotation.z = lerpf(rotation.z, -steering * 0.055, minf(delta * 6.0, 1.0))
	if body_material != null:
		body_material.metallic = 0.18

func _mat(color: Color, roughness: float = 0.3, metallic: float = 0.08, emission: bool = false) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = color
	m.roughness = roughness
	m.metallic = metallic
	if emission:
		m.emission_enabled = true
		m.emission = color
		m.emission_energy_multiplier = 2.0
	return m

func _box(pos: Vector3, size: Vector3, material: Material) -> MeshInstance3D:
	var mesh := BoxMesh.new()
	mesh.size = size
	var mi := MeshInstance3D.new()
	mi.mesh = mesh
	mi.material_override = material
	mi.position = pos
	add_child(mi)
	return mi

func _sphere(pos: Vector3, scale3: Vector3, material: Material) -> MeshInstance3D:
	var mesh := SphereMesh.new()
	mesh.radial_segments = 12
	mesh.rings = 7
	var mi := MeshInstance3D.new()
	mi.mesh = mesh
	mi.material_override = material
	mi.position = pos
	mi.scale = scale3
	add_child(mi)
	return mi

func _build() -> void:
	body_material = RealismMaterials.car_paint(paint)
	var dark := _mat(Color("#172d53"), 0.72)
	var tire := RealismMaterials.rubber()
	var rim := RealismMaterials.chrome()
	var window := RealismMaterials.polished_glass()
	var white := _mat(Color("#fff8ec"), 0.24)
	var blue := _mat(Color("#183f81"), 0.32)
	var pink := _mat(Color("#fc7fac"), 0.3)
	var stripe := _mat(Color("#fff9de"), 0.13)
	var golden := _mat(Color("#ffe05e"), 0.23, 0.08, true)

	# A rounded multi-body silhouette gives more depth than a single cube.
	_box(Vector3(0, 0.75, 0), Vector3(2.12, 0.78, 3.15), body_material)
	_sphere(Vector3(0, 0.94, -0.92), Vector3(1.05, 0.40, 0.91), body_material)
	_sphere(Vector3(0, 0.87, 1.05), Vector3(1.08, 0.35, 0.75), body_material)
	_box(Vector3(0, 1.40, 0.16), Vector3(1.62, 0.75, 1.68), window)
	_box(Vector3(0, 1.81, 0.21), Vector3(1.72, 0.20, 1.78), body_material)
	_box(Vector3(0, 1.53, -0.73), Vector3(1.38, 0.52, 0.07), _mat(Color("#a7ecff"), 0.07, 0.04))
	_box(Vector3(0, 1.55, 0.99), Vector3(1.38, 0.50, 0.07), window)
	_box(Vector3(0, 1.02, -1.59), Vector3(1.89, 0.14, 0.09), stripe)
	_box(Vector3(-0.22, 1.17, -1.10), Vector3(0.16, 0.07, 0.83), stripe)
	_box(Vector3(0.22, 1.17, -1.10), Vector3(0.16, 0.07, 0.83), stripe)
	_box(Vector3(0, 1.35, 1.57), Vector3(2.10, 0.15, 0.36), body_material)
	_box(Vector3(-0.75, 1.22, 1.53), Vector3(0.17, 0.26, 0.21), dark)
	_box(Vector3(0.75, 1.22, 1.53), Vector3(0.17, 0.26, 0.21), dark)

	# 3D facial expressions, unique to this original toy-car.
	for x in [-0.41, 0.41]:
		_sphere(Vector3(x, 1.50, -0.82), Vector3(0.23, 0.29, 0.08), white)
		_sphere(Vector3(x + 0.06, 1.48, -0.906), Vector3(0.11, 0.16, 0.035), blue)
		_sphere(Vector3(x + 0.09, 1.54, -0.944), Vector3(0.042, 0.065, 0.018), white)
		_sphere(Vector3(x, 0.88, -1.55), Vector3(0.22, 0.13, 0.10), golden)
	_sphere(Vector3(0, 0.78, -1.64), Vector3(0.39, 0.105, 0.03), dark)
	_sphere(Vector3(0, 0.725, -1.675), Vector3(0.20, 0.048, 0.035), pink)

	# Real wheel meshes, with transparent metal-style hub.
	for side in [-1, 1]:
		for end in [-1, 1]:
			var pivot := Node3D.new()
			pivot.position = Vector3(float(side) * 1.10, 0.40, float(end) * 1.06)
			add_child(pivot)
			wheels.append(pivot)
			var wm := CylinderMesh.new()
			wm.top_radius = 0.43
			wm.bottom_radius = 0.43
			wm.height = 0.29
			wm.radial_segments = 12
			var wheel_mesh := MeshInstance3D.new()
			wheel_mesh.mesh = wm
			wheel_mesh.material_override = tire
			wheel_mesh.rotation.z = PI / 2.0
			pivot.add_child(wheel_mesh)
			var hub := MeshInstance3D.new()
			var hm := CylinderMesh.new()
			hm.top_radius = 0.24
			hm.bottom_radius = 0.24
			hm.height = 0.31
			hm.radial_segments = 10
			hub.mesh = hm
			hub.material_override = rim
			hub.rotation.z = PI / 2.0
			pivot.add_child(hub)
			# Five angular alloy wheel spokes, visible as the wheels rotate.
			for k in range(5):
				var spoke := MeshInstance3D.new()
				var bar := BoxMesh.new()
				bar.size = Vector3(.10,.41,.035)
				spoke.mesh = bar
				spoke.material_override = rim
				spoke.rotation.x = TAU*float(k)/5.0
				spoke.position.x = float(side)*.19
				pivot.add_child(spoke)
	
	# Mirror caps, chrome door handles, brake light clusters and diffusers.
	for side in [-1,1]:
		var x: float = float(side)
		_sphere(Vector3(x*1.04,1.48,-.44),Vector3(.27,.16,.22),body_material)
		_box(Vector3(x*1.08,.99,.25),Vector3(.03,.07,.40),rim)
		_box(Vector3(x*.79,.85,1.635),Vector3(.40,.16,.07),_mat(Color("#ff405e"),.22,0.0,true))
		_box(Vector3(x*.70,.55,-1.62),Vector3(.26,.09,.07),rim)
	# Scalloped ventilated bumper and lower side trim.
	_box(Vector3(0,.55,-1.66),Vector3(1.48,.20,.08),dark)
	for i in range(5):
		_box(Vector3((float(i)-2.0)*.25,.56,-1.72),Vector3(.10,.17,.04),rim)
	_box(Vector3(0,.41,1.64),Vector3(1.40,.18,.11),dark)
	# A single white highlight on the windshield makes clearcoat readable.
	_box(Vector3(-.54,1.69,-.777),Vector3(.10,.24,.02),_mat(Color("#d9fcff"),.10))
	
	# Turbo exhaust jets glow blue while the boost control is held.
	for x in [-0.53, 0.53]:
		_box(Vector3(x, 0.66, 1.64), Vector3(0.27, 0.19, 0.17), dark)
		var fm := CylinderMesh.new()
		fm.top_radius = 0.055
		fm.bottom_radius = 0.21
		fm.height = 0.86
		fm.radial_segments = 9
		var inst := MeshInstance3D.new()
		inst.mesh = fm
		inst.material_override = _mat(Color("#44dfff"), 0.2, 0.05, true)
		inst.rotation.x = PI / 2.0
		inst.position = Vector3(x, 0.63, 2.05)
		inst.visible = false
		add_child(inst)
		flames.append(inst)
	
	if character_id == 0:
		_build_dust_fx()
	if character_id == 2:
		_sphere(Vector3(0.66, 2.03, 0.40), Vector3(0.28, 0.20, 0.32), pink)
		_sphere(Vector3(0.86, 2.09, 0.42), Vector3(0.16, 0.19, 0.18), pink)
	if character_id == 3:
		_box(Vector3(0, 1.94, 0.18), Vector3(0.81, 0.11, 0.29), golden)

func _build_dust_fx() -> void:
	# Godot's native CPUParticles3D: gentle tyre smoke / road dust.
	# CPU particles also work on devices where GPU particle support is limited.
	var smoke_mat := _mat(Color("#d6e6f1"),.95)
	smoke_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	smoke_mat.albedo_color.a = .45
	for side in [-1,1]:
		var emitter := CPUParticles3D.new()
		emitter.name = "SkidDust" + str(side)
		emitter.position = Vector3(float(side)*1.08,.30,1.19)
		emitter.amount = 20
		emitter.lifetime = .65
		emitter.lifetime_randomness = .40
		emitter.emitting = false
		emitter.local_coords = false
		emitter.direction = Vector3(0,1,1)
		emitter.spread = 45.0
		emitter.gravity = Vector3(0,.36,0)
		emitter.initial_velocity_min = .6
		emitter.initial_velocity_max = 2.2
		emitter.scale_amount_min = .42
		emitter.scale_amount_max = 1.30
		var blob := SphereMesh.new()
		blob.radius = .20
		blob.height = .40
		blob.radial_segments = 6
		blob.rings = 3
		blob.material = smoke_mat
		emitter.mesh = blob
		add_child(emitter)
		dust_emitters.append(emitter)
