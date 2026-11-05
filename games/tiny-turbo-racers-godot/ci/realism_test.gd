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
	print("TINY_TURBO_REALISM_TEST_PASS, Jolt+PBR+grass+sky+tyreDust; instances=",foliage_count)
	game.queue_free()
	quit(0)
