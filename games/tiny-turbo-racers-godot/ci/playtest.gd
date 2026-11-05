extends SceneTree
## CI gameplay smoke test: simulate menu, countdown, turbo, 3 laps, result screen.
func _initialize() -> void:
	call_deferred("_test")

func _test() -> void:
	var scene: PackedScene = load("res://scenes/main.tscn")
	if scene == null:
		push_error("Missing main scene")
		quit(2)
		return
	var game = scene.instantiate()
	root.add_child(game)
	if game.state != "menu":
		push_error("Menu state not initialized")
		quit(3)
		return
	game._start_race()
	game.held_accel=true
	var used_turbo: bool = false
	for step in range(7200):
		game._physics_process(0.033)
		if game.state == "racing" and not used_turbo:
			game._activate_boost()
			used_turbo = true
		if game.state == "finished":
			break
	if game.state != "finished":
		push_error("Three-lap simulation never reached finish (state="+game.state+")")
		quit(4)
		return
	if game.total_stars < 1 or not used_turbo:
		push_error("Stars reward or boost failed")
		quit(5)
		return
	print("TINY_TURBO_GODOT_PLAYTEST_PASS; stars=",game.total_stars,
		"; elapsed=",game.race_seconds)
	game.queue_free()
	quit(0)
