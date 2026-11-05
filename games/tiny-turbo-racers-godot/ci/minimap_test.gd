extends SceneTree
## HUD regression: minimap draws actual course splines and moves its player marker
## from the manually steered car's world position, not a fake static image.
func _initialize() -> void:
	call_deferred("_verify")

func _verify() -> void:
	var game=load("res://scenes/main.tscn").instantiate()
	root.add_child(game)
	# Previous CI tests may have saved route 2 to shared user://, so force a
	# deterministic original map before comparing two different courses.
	game.track_index=0
	game._rebuild_world_for_track()
	if game.minimap==null or game.minimap.line.size()!=129:
		push_error("Minimap must contain sampled real track geometry")
		quit(91)
		return
	var previous_line:PackedVector2Array=game.minimap.line.duplicate()
	game.track_index=2
	game._rebuild_world_for_track()
	if game.minimap.track!=game.world or game.minimap.line.size()!=129:
		push_error("Minimap did not reload after track selection")
		quit(92)
		return
	var shape_difference:float=0.0
	for i in range(0,previous_line.size(),8):
		shape_difference+=previous_line[i].distance_to(game.minimap.line[i])
	if shape_difference<120.0:
		push_error("Minimap did not redraw the actual different road spline")
		quit(93)
		return
	game.race_mode=0
	game._start_race()
	game.held_accel=true
	var initial:Vector3=game.car_motion.position
	for tick in range(250):
		game._physics_process(.033)
	if game.car_motion.position.distance_to(initial)<10.0:
		push_error("Car didn't move on real road")
		quit(94)
		return
	if game.minimap.player_world.distance_to(game.car_motion.position)>.15:
		push_error("HUD marker is not tracking real car world position")
		quit(95)
		return
	if game.minimap.rival_world.size()!=3:
		push_error("Three opponent positions should be rendered in race minimap")
		quit(96)
		return
	print("TINY_TURBO_MINIMAP_WORLD_POSITION_PASS / course_length=",game.world.track_length)
	game.queue_free()
	quit(0)
