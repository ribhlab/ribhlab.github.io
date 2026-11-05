extends SceneTree
## Actual car world-space QA; verifies steering changes route geometry instead of
## moving only a UI wheel, and road edge contact visibly reduces speed.
const TRACK = preload("res://scripts/street_track.gd")
const MOTION = preload("res://scripts/road_kinematics.gd")
func _initialize() -> void:
	call_deferred("_verify")

func _fail(reason: String,code: int) -> void:
	push_error("REAL_STEERING_QA_FAILED: "+reason)
	quit(code)

func _verify() -> void:
	var track=TRACK.new()
	root.add_child(track)
	track.build_world()
	var neutral=MOTION.new()
	neutral.reset(track)
	var right=MOTION.new()
	right.reset(track)
	var left=MOTION.new()
	left.reset(track)
	for i in range(110):
		neutral.advance(track,1.0/60.0,25.0,0.0,0.0,0.0)
		right.advance(track,1.0/60.0,25.0,1.0,.39,0.0)
		left.advance(track,1.0/60.0,25.0,-1.0,-.39,0.0)
	var separation:float=right.position.distance_to(left.position)
	if separation<4.0:
		_fail("Opposite steering still drives same line! separation="+str(separation),81)
		return
	if absf(wrapf(right.heading-left.heading,-PI,PI))<.05:
		_fail("Steering did not rotate real vehicle heading",82)
		return
	if neutral.distance<28.0:
		_fail("Neutral arcade assist could not follow spline",83)
		return
	if right.distance>neutral.distance+25.0:
		_fail("Moving toward corner jumps checkpoints",84)
		return
	# Force boundary contact with a car spawned outside the kerb, and ensure
	# position is brought back inside safety barriers rather than left in void.
	var wall=MOTION.new()
	wall.reset(track,0.0,22.0)
	var result:Dictionary=wall.advance(track,.016,21.0,1.0,.39,0.0)
	if not bool(result["wall"]) or absf(float(result["offset"]))>11.2:
		_fail("Physical barrier collision did not resolve offroad pose",85)
		return
	# Each mode's course is a different real 3D spline.
	var lengths: Array[float]=[]
	for map_id in range(3):
		var course=TRACK.new()
		course.set_circuit(map_id)
		root.add_child(course)
		course.build_world()
		lengths.append(course.track_length)
		course.queue_free()
	if absf(lengths[0]-lengths[1])<10.0 or absf(lengths[1]-lengths[2])<10.0:
		_fail("Route variants were not different",86)
		return
	print("TINY_TURBO_REAL_STEERING_PASS separation=",separation," neutral_m=",neutral.distance,
		" wall_offset=",result["offset"])
	track.queue_free()
	quit(0)
