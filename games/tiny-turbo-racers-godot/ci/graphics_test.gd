extends SceneTree
## Check that Low/Medium/High are meaningful render-budget presets, not labels.
func _initialize() -> void:
	call_deferred("_test")

func _test() -> void:
	var game=load("res://scenes/main.tscn").instantiate()
	root.add_child(game)
	var environment=game.world.get_node_or_null("MidnightSkyAndAtmosphere") as WorldEnvironment
	var moon=game.world.get_node_or_null("Moonlight") as DirectionalLight3D
	var studs=game.world.get_node_or_null("InstancedRoadReflectors") as MultiMeshInstance3D
	if studs==null or studs.multimesh==null or studs.multimesh.instance_count!=256:
		push_error("Night street reflectors missing or not GPU-instanced")
		quit(55)
		return
	if environment==null or moon==null:
		push_error("Quality test missing night environment")
		quit(51)
		return
	game._select_quality(0)
	var low_hidden:int=0
	var towers:int=0
	for child in game.world.get_children():
		if child.name.begins_with("DowntownTower_"):
			towers+=1
			if not child.visible:
				low_hidden+=1
	if moon.shadow_enabled or environment.environment.glow_enabled or low_hidden<40:
		push_error("LOW quality doesn't reduce render detail. hidden="+str(low_hidden))
		quit(52)
		return
	# Reduced graphics must never make collidable traffic invisible.
	for car in game.traffic.vehicles:
		if not (car["node"] as Node3D).visible:
			push_error("Low graphics generated an invisible traffic collision hazard")
			quit(56)
			return
	game._select_quality(2)
	var high_visible:int=0
	for child in game.world.get_children():
		if child.name.begins_with("DowntownTower_") and child.visible:
			high_visible+=1
	if not moon.shadow_enabled or not environment.environment.glow_enabled or high_visible!=towers:
		push_error("HIGH did not restore detail or shadows")
		quit(53)
		return
	game._select_quality(1)
	if not game.quality_label.text.contains("MEDIUM"):
		push_error("Quality UI failed to update")
		quit(54)
		return
	print("TINY_TURBO_GRAPHICS_PRESET_PASS", " towers=",towers," low_hidden=",low_hidden)
	game.queue_free()
	quit(0)
