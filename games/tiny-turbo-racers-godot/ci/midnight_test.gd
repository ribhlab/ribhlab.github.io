extends SceneTree
## v0.6: smoke test actual urban night level, 5 traffic cars, nitro, drift, PBR models.
func _initialize() -> void:
	call_deferred("_test")

func _test() -> void:
	var pack: PackedScene = load("res://scenes/main.tscn")
	if pack==null:
		push_error("Missing Midnight Rush main scene")
		quit(11)
		return
	var game=pack.instantiate()
	root.add_child(game)
	if game.world.get_node_or_null("MidnightSkyAndAtmosphere")==null:
		push_error("Night environment missing")
		quit(12)
		return
	if game.traffic == null or game.traffic.vehicles.size()!=5:
		push_error("Expected 5 real moving city traffic vehicles")
		quit(13)
		return
	var towers: int=0
	var facade: bool=false
	for child in game.world.get_children():
		if child.name.begins_with("DowntownTower_"):
			towers+=1
			for item in child.get_children():
				if item is MeshInstance3D and item.material_override is ShaderMaterial:
					facade=true
	if towers<100 or not facade:
		push_error("City too empty / emissive facades missing: "+str(towers)+", "+str(facade))
		quit(14)
		return
	game._start_race()
	game.held_accel=true
	# Countdown until the race controls are active.
	for i in range(170):
		game._physics_process(.033)
	if game.state != "racing":
		push_error("Race failed to start")
		quit(15)
		return
	var before: float=game.nitro_charge
	game._activate_boost()
	if game.boost_remaining <= 0 or game.nitro_charge>=before:
		push_error("Nitro did not consume a charge")
		quit(16)
		return
	game.held_right=true
	game.held_drift=true
	for i in range(210):
		game._physics_process(.033)
	if game.drift_points<=0:
		push_error("Drift scoring never activated")
		quit(17)
		return
	if game.traffic.vehicles[0]["angle"] <= .20:
		push_error("Night traffic failed to move")
		quit(18)
		return
	print("MIDNIGHT_RUSH_PLAYTEST_PASS; towers=",towers,
		"; traffic=",game.traffic.vehicles.size(),
		"; drift=",game.drift_points,"; nitro=",game.nitro_charge)
	game.queue_free()
	quit(0)
