extends RefCounted
## v0.7 multi-touch racing input. Individual Android finger IDs are tracked.
## This prevents simultaneous STEER + BRAKE + DRIFT + NITRO from cancelling
## one another when more than one touchscreen is pressed.
var regions: Dictionary = {}
var pointers: Dictionary = {}

func configure(left: Rect2, right: Rect2, brake: Rect2, drift: Rect2, nitro: Rect2) -> void:
	regions = {"left":left,"right":right,"brake":brake,"drift":drift,"nitro":nitro}
	pointers.clear()

func reset() -> void:
	pointers.clear()

func _region(pos: Vector2) -> String:
	for key in ["left","right","brake","drift","nitro"]:
		if regions.has(key) and (regions[key] as Rect2).has_point(pos):
			return key
	return ""

func handle(event: InputEvent) -> String:
	# Return the newly pressed action (for one-shot NITRO) or empty String.
	if event is InputEventScreenTouch:
		var touch := event as InputEventScreenTouch
		if touch.pressed:
			var action: String = _region(touch.position)
			pointers[touch.index] = action
			return action
		pointers.erase(touch.index)
	elif event is InputEventScreenDrag:
		var drag := event as InputEventScreenDrag
		if pointers.has(drag.index):
			pointers[drag.index] = _region(drag.position)
	return ""

func held(key: String) -> bool:
	for action in pointers.values():
		if action == key:
			return true
	return false

func steer() -> float:
	return float(int(held("right"))-int(held("left")))

func pointer_count() -> int:
	return pointers.size()
