extends SceneTree
## CI: assert that the premium PBR/Jolt/CPU-particle features are active.
func _initialize() -> void:
	call_deferred("_test")

func _test() -> void:
	var configured: String = str(ProjectSettings.get_setting("physics/3d/physics_engine",""))
	if configured != "Jolt Physics":
		push_error("Expected built-in Jolt Physics but got: " + configured)
		quit(6)
		return
	var scene: PackedScene = load("res://scenes/main.tscn")
	if scene == null:
		push_error("Missing scene")
		quit(7)
		return
	var game = scene.instantiate()
	root.add_child(game)
	var road_found := false
	var grass_found := false
	var jolt_floor_found := false
	for child in game.world.get_children():
		if child is StaticBody3D and child.name=="JoltTerrainCollision":
			jolt_floor_found = true
		if child is MeshInstance3D:
			var m: Material = child.material_override
			if m is StandardMaterial3D:
				if m.normal_enabled:
					road_found = true
				if m.albedo_texture!=null and m.uv1_scale.x>=20.0:
					grass_found = true
	var paint: StandardMaterial3D = game.player.body_material
	var visual_ok: bool = paint != null and paint.clearcoat_enabled and paint.metallic>.2
	var dust_count: int = game.player.dust_emitters.size()
	var foliage_count: int = 0
	for child in game.world.get_children():
		if child is MultiMeshInstance3D:
			foliage_count += child.multimesh.instance_count
	if not (road_found and grass_found and jolt_floor_found and visual_ok and dust_count==2 and foliage_count>=500):
		push_error("Quality feature regression: asphalt="+str(road_found)+" grass="+str(grass_found)+
			" joltFloor="+str(jolt_floor_found)+" paint="+str(visual_ok)+
			" dust="+str(dust_count)+" vegetation="+str(foliage_count))
		quit(8)
		return
	# v0.5: distinguish real imported GLB from the legacy primitive fallback.
	var imported_car: bool = game.player.imported_vehicle
	var detailed_meshes: int = game.player.external_mesh_count
	var actual_road: Node = game.world.get_node_or_null("CC0_PolyHaven_Asphalt_Track")
	var circuit_meters: float = game.world.track_length
	var pbr_photo: bool = ResourceLoader.exists("res://assets/textures/asphalt_02_diff_1k.png")
	if not imported_car or detailed_meshes < 1 or actual_road == null or circuit_meters < 700.0 or not pbr_photo:
		push_error("Real GT model or realistic GP circuit not loaded: car="+str(imported_car)+
			" meshes="+str(detailed_meshes)+" road="+str(actual_road != null)+
			" track_meters="+str(circuit_meters)+" photo_pbr="+str(pbr_photo))
		quit(9)
		return
	print("REAL_GT_CIRCUIT_PASS imported meshes=",detailed_meshes," lap_meters=",circuit_meters)
	print("TINY_TURBO_REALISM_TEST_PASS, Jolt+PBR+grass+sky+tyreDust; instances=",foliage_count)
	game.queue_free()
	quit(0)
