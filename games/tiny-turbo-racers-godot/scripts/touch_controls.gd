extends RefCounted
## Racing touch controller v0.8: analogue wheel + separate pedals, Nitro, drift.
## One finger ID remains assigned to its original control; dragging off the
## control never accidentally releases an unrelated held pedal.
var regions: Dictionary = {}
var pointers: Dictionary = {}
var wheel_value: float = 0.0
var wheel_id: int = -1

func configure(wheel: Rect2, gas: Rect2, brake: Rect2, drift: Rect2, nitro: Rect2) -> void:
	regions={"wheel":wheel,"gas":gas,"brake":brake,"drift":drift,"nitro":nitro}
	reset()

func reset() -> void:
	pointers.clear()
	wheel_id = -1
	wheel_value = 0.0

func _region(pos: Vector2) -> String:
	for key in ["wheel","gas","brake","drift","nitro"]:
		if (regions[key] as Rect2).has_point(pos):
			return key
	return ""

func _set_wheel(pos: Vector2) -> void:
	var r: Rect2=regions["wheel"]
	var middle: float=r.position.x+r.size.x*.5
	wheel_value=clampf((pos.x-middle)/(r.size.x*.43),-1.0,1.0)
	if absf(wheel_value)<.075:
		wheel_value=0.0

func handle(event: InputEvent) -> String:
	if event is InputEventScreenTouch:
		var t:=event as InputEventScreenTouch
		if t.pressed:
			var key:String=_region(t.position)
			pointers[t.index]=key
			if key=="wheel" and wheel_id<0:
				wheel_id=t.index
				_set_wheel(t.position)
			return key
		pointers.erase(t.index)
		if wheel_id==t.index:
			wheel_id=-1
			wheel_value=0.0
	elif event is InputEventScreenDrag:
		var d:=event as InputEventScreenDrag
		if wheel_id==d.index:
			_set_wheel(d.position)
	return ""

func held(action: String) -> bool:
	for key in pointers.values():
		if key==action:
			return true
	return false

func steer() -> float:
	return wheel_value

func pointer_count() -> int:
	return pointers.size()
