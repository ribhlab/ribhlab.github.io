extends SceneTree
## Visual QA: real framebuffer screenshot from the playable Godot 3D scene.
## The screenshot is NOT AI-generated or concept art.
func _initialize() -> void:
	call_deferred("_capture")

func _capture() -> void:
	var game_pack: PackedScene = load("res://scenes/main.tscn")
	if game_pack == null:
		push_error("Missing race scene")
		quit(1)
		return
	var game = game_pack.instantiate()
	root.add_child(game)
	game._start_race()
	game.state = "racing"
	game.progress = .046
	game.speed = 31.0
	game._apply_ui()
	game._place_car()
	game._animate_cars(.016)
	game._update_camera(1.0)
	# Wait for actual graphics GPU/CPU render, not just simulation ticks.
	for i in range(4):
		await RenderingServer.frame_post_draw
	var shot: Image = root.get_texture().get_image()
	if shot == null or shot.is_empty():
		push_error("No framebuffer from real Godot rendering")
		quit(2)
		return
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://build"))
	var path: String = ProjectSettings.globalize_path("res://build/real_circuit_frame.png")
	var result: int = shot.save_png(path)
	if result != OK:
		push_error("Could not save real 3D screenshot: "+str(result))
		quit(3)
		return
	print("REAL_CIRCUIT_SCREENSHOT_PASS ",path," ",shot.get_width(),"x",shot.get_height())
	quit(0)
