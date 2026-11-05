@tool
extends Node3D
## EDITOR-ONLY preview of the EXACT procedural world and car constructors.
## Important: never save generated meshes into main.tscn: they are rebuilt at runtime.
## This script is inert in exported Android games.
const WorldBuilder = preload("res://scripts/real_track.gd")
const CarVisual = preload("res://scripts/real_car.gd")

var preview_loaded: bool = false

func _ready() -> void:
	if not Engine.is_editor_hint():
		visible = false
		return
	# Godot's headless import/build tools do not need the full editor visualization.
	if DisplayServer.get_name() == "headless" and not OS.has_environment("TINY_TURBO_EDITOR_PREVIEW_TEST"):
		return
	call_deferred("_build_editor_preview")

func _build_editor_preview() -> void:
	if not is_inside_tree() or not Engine.is_editor_hint():
		return
	if preview_loaded or has_node("LiveWorldPreview"):
		return
	preview_loaded = true
	# Create the actual world with all four biomes, road and PBR materials.
	var world = WorldBuilder.new()
	world.name = "LiveWorldPreview"
	add_child(world)
	world.build_world()
	# The original 3D car builder is shared with the playable game.
	var colors: Array[Color] = [
		Color("#fa4155"), Color("#348bf3"),
		Color("#ffce42"), Color("#40d384")
	]
	for i in range(colors.size()):
		var toy = CarVisual.new()
		toy.name = ["SpeedyPreview","BuddyPreview","SunnyPreview","RangerPreview"][i]
		toy.configure(colors[i],i)
		add_child(toy)
		var angle: float = 0.08+float(i)*0.034
		var lane: float = [-1.5,-5.4,3.6,6.4][i]
		toy.position = world.road_position(angle,lane) + Vector3(0,.10,0)
		toy.rotation.y = world.road_yaw(angle)
	# Camera node is in the saved scene tree: select it, enable Preview.
	var camera := get_node_or_null("ShowcaseCamera") as Camera3D
	if camera != null:
		var first: Vector3 = world.road_position(0)
		var tangent: Vector3 = world.road_tangent(0)
		camera.position = first - tangent*32.0 + Vector3(0,14,0)
		camera.look_at(first + tangent*22.0 + Vector3(0,1.4,0),Vector3.UP)
	# Focus the scene-editor viewport on the start line, rather than origin
	# (which is inside the empty central lawn of the circular racetrack).
	call_deferred("_focus_editor_camera")

func _focus_editor_camera() -> void:
	if not Engine.is_editor_hint() or DisplayServer.get_name() == "headless":
		return
	if EditorInterface.get_edited_scene_root() != get_parent():
		return
	var viewport := EditorInterface.get_editor_viewport_3d(0)
	if viewport == null:
		return
	var editor_cam := viewport.get_camera_3d()
	if editor_cam == null:
		return
	var world = get_node_or_null("LiveWorldPreview")
	if world == null:
		return
	var start: Vector3 = world.road_position(0)
	var tangent: Vector3 = world.road_tangent(0)
	editor_cam.global_position = start - tangent*32.0 + Vector3(0,14,0)
	editor_cam.look_at(start+tangent*22.0 + Vector3(0,1.4,0),Vector3.UP)
