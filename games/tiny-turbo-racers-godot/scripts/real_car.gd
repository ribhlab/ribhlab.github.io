@tool
extends "res://scripts/car_visual.gd"
## RibhLab RealCars v0.5 — use the real CC0 Spectral GT RS 258-mesh GLB.
## Car geometry, glass, carbon, brakes, wing, headlamps and cockpit are authored
## in Blender and imported as PBR glTF. Fallback remains the older procedural car
## only when someone opens this project before the binary assets are installed.
const CAR_ASSET: String = "res://assets/vehicles/spectral_gt_rs_game_ready.glb"
const PBR = preload("res://scripts/realism_materials.gd")
var imported_vehicle: bool = false
var external_mesh_count: int = 0
var asset_path: String = CAR_ASSET

func set_model_file(path: String) -> void:
	if not path.is_empty():
		asset_path = path


func _ready() -> void:
	if not ResourceLoader.exists(asset_path):
		push_warning("High-fidelity CC0 sports car asset missing, using procedural fallback.")
		super._ready()
		return
	var packed: Resource = load(asset_path)
	if not packed is PackedScene:
		push_warning("High-fidelity GLB import not ready, using fallback")
		super._ready()
		return
	var holder := Node3D.new()
	holder.name = "Licensed_CC0_Spectral_GT_RS"
	add_child(holder)
	var model: Node3D = (packed as PackedScene).instantiate() as Node3D
	if model == null:
		super._ready()
		return
	holder.add_child(model)
	# Blender native front +X -> Godot game local forward -Z.
	holder.rotation.y = PI*.5
	# Clamp real-world car dimensions to ~4.65m length; preserve ALL fine PBR details.
	var bounds: AABB = _model_bounds(model)
	var long_axis: float = maxf(.01,maxf(bounds.size.x,bounds.size.z))
	# Imported Sketchfab models vary between X-forward and Z-forward coordinate conventions.
	# Match the largest body dimension; users can adjust orientation in the catalog later.
	holder.rotation.y = PI*.5 if bounds.size.x > bounds.size.z else 0.0
	var k: float = clampf(4.65/long_axis,.12,6.0)
	holder.scale = Vector3.ONE*k
	model.position = Vector3(
		-bounds.position.x-bounds.size.x*.5,
		-bounds.position.y-.08/k,
		-bounds.position.z-bounds.size.z*.5
	)
	body_material = PBR.car_paint(paint)
	_repaint_shells(model)
	if character_id == 0:
		_build_dust_fx()
	_build_turbo_exhaust()
	imported_vehicle = true

func _model_bounds(root: Node3D) -> AABB:
	var low := Vector3(INF,INF,INF)
	var high := Vector3(-INF,-INF,-INF)
	var stack: Array[Node] = [root]
	var inverse_root: Transform3D = root.global_transform.affine_inverse()
	while not stack.is_empty():
		var n: Node = stack.pop_back()
		if n is MeshInstance3D and (n as MeshInstance3D).mesh != null:
			var mi := n as MeshInstance3D
			var box: AABB = mi.mesh.get_aabb()
			var xform: Transform3D = inverse_root*mi.global_transform
			for i in range(8):
				var p: Vector3 = box.position + Vector3(
					box.size.x if (i&1)!=0 else 0.0,
					box.size.y if (i&2)!=0 else 0.0,
					box.size.z if (i&4)!=0 else 0.0)
				var point: Vector3 = xform*p
				low = low.min(point)
				high = high.max(point)
			external_mesh_count+=1
		for child in n.get_children():
			stack.push_back(child)
	if external_mesh_count==0:
		return AABB(Vector3(-2.0,0,-1),Vector3(4.0,1.6,2))
	return AABB(low,high-low)

func _repaint_shells(root: Node) -> void:
	var stack: Array[Node] = [root]
	while not stack.is_empty():
		var n: Node = stack.pop_back()
		if n is MeshInstance3D:
			var nm: String = n.name
			if nm.contains("BODY_Shell") or nm.contains("CABIN_Roof") or nm.contains("Hood_Center") or nm.contains("Door_Skin") or nm.contains("Fender_Lip") or nm.contains("Mirror_Shell"):
				(n as MeshInstance3D).material_override = body_material
		for child in n.get_children():
			stack.push_back(child)

func _build_turbo_exhaust() -> void:
	for s in [-1,1]:
		var cone := CylinderMesh.new()
		cone.top_radius=.10
		cone.bottom_radius=.29
		cone.height=.9
		cone.radial_segments=12
		var jet:=MeshInstance3D.new()
		jet.name="TurboBlueFlame"
		jet.mesh=cone
		var mat:=StandardMaterial3D.new()
		mat.albedo_color=Color("#43aaff")
		mat.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED
		mat.emission_enabled=true
		mat.emission=Color("#27caff")
		mat.emission_energy_multiplier=3.1
		jet.material_override=mat
		jet.rotation.x=PI*.5
		jet.position=Vector3(float(s)*.56,.42,2.27)
		jet.visible=false
		add_child(jet)
		flames.append(jet)

func animate_car(delta: float, speed: float, steering: float, turbo: bool) -> void:
	super.animate_car(delta,speed,steering,turbo)
	if imported_vehicle:
		# Suspension/camera bob stays restrained for a realistic sports-car feel.
		rotation.x=lerpf(rotation.x,clampf(speed/65.0,0,.4)*-.025,
			clampf(delta*3.8,0,1))
