extends SceneTree
## Verify that @tool editor preview builds the actual world and cars.
## Run only with TINY_TURBO_EDITOR_PREVIEW_TEST=1 and --headless --editor.
func _initialize() -> void:
	call_deferred("_validate")

func _validate() -> void:
	var pack: PackedScene = load("res://scenes/main.tscn")
	if pack == null:
		push_error("Preview scene could not load")
		quit(11)
		return
	var game: Node = pack.instantiate()
	root.add_child(game)
	await process_frame
	await process_frame
	await process_frame
	var preview: Node = game.get_node_or_null("EditorPreview")
	if preview == null:
		push_error("EditorPreview is not present")
		quit(12)
		return
	var world: Node = preview.get_node_or_null("LiveWorldPreview")
	if world == null:
		push_error("Editor tool did not create world in the viewport")
		quit(13)
		return
	var car_count: int = 0
	for n in preview.get_children():
		if "Preview" in n.name and n.name != "EditorPreview":
			car_count += 1
	if car_count < 4 or world.get_child_count() < 15:
		push_error("Preview missing geometry, cars="+str(car_count)+", scenery="+str(world.get_child_count()))
		quit(14)
		return
	print("TINY_TURBO_EDITOR_PREVIEW_PASS; cars=",car_count,"; world_nodes=",world.get_child_count())
	quit(0)
