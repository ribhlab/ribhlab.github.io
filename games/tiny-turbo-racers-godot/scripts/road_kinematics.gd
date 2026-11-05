extends RefCounted
## v0.9 actual free car pose on the 3D road (not locked to road_position()).
## Assisted arcade bicycle steering with physical road-edge boundary contact,
## signed lateral displacement, nearest-track projection and no lap teleporting.
##
## Geometry comes from WorldBuilder.centerline / accumulated and is world-space.
## Curves + road bounds are real. The collision boundary is an arcade wall,
## NOT a full wheel-based VehicleBody3D simulator.
const SEARCH_RADIUS: int = 48
const EDGE_CONTACT: float = 11.1
const WHEEL_BASE: float = 2.7

var position: Vector3 = Vector3.ZERO
var heading: float = 0.0
var distance: float = 0.0
var sample_index: int = 0
var lateral_offset: float = 0.0
var touched_wall: bool = false
var offroad: bool = false
var turn_rate: float = 0.0
var initialized: bool = false

func reset(track: Node3D, angle: float = 0.0, lane: float = 0.0) -> void:
	var route_angle: float = fposmod(angle,TAU)
	position = track.road_position(route_angle,lane) + Vector3(0,.10,0)
	heading = track.road_yaw(route_angle)
	distance = maxf(0.0,angle/TAU*track.track_length)
	sample_index = posmod(int(round(route_angle/TAU*float(track.centerline.size()-1))),track.centerline.size()-1)
	lateral_offset = lane
	touched_wall = false
	offroad = false
	turn_rate = 0.0
	initialized = true

func _nearest(track: Node3D, query: Vector3) -> Dictionary:
	var count: int=track.centerline.size()-1
	if count<=0:
		return {"index":0,"meters":0.0,"center":Vector3.ZERO,"side":Vector3.RIGHT,"offset":0.0}
	var closest: int=sample_index
	var lowest: float=INF
	for k in range(-SEARCH_RADIUS,SEARCH_RADIUS+1):
		var idx: int=posmod(sample_index+k,count)
		var p: Vector3=track.centerline[idx]
		var dx: float=p.x-query.x
		var dz: float=p.z-query.z
		var square:float=dx*dx+dz*dz
		if square<lowest:
			lowest=square
			closest=idx
	var center: Vector3=track.centerline[closest]
	var before: Vector3=track.centerline[posmod(closest-1,count)]
	var after: Vector3=track.centerline[posmod(closest+1,count)]
	var tangent: Vector3=after-before
	tangent.y=0.0
	tangent=tangent.normalized()
	# Real_track positive lane is LEFT of travel.
	var left: Vector3=Vector3(tangent.z,0.0,-tangent.x)
	var offset:float=(query-center).dot(left)
	return {"index":closest,"meters":float(track.accumulated[closest]),
		"center":center,"side":left,"offset":offset,"tangent":tangent}

func advance(track: Node3D, delta: float, speed: float, steer_input: float,
		wheel_angle: float, slide_velocity: float, drifting: bool = false) -> Dictionary:
	if not initialized:
		reset(track)
	var dt: float=clampf(delta,0.0,.05)
	var velocity:float=clampf(speed,0.0,75.0)
	var meters_per_rad:float=track.road_meters_per_radian()
	var yaw_prior:float=heading
	# 13-35 meters ahead for smooth mobile steering assist. With strong manual
	# input the assistance backs off; steering ALWAYS changes actual direction.
	var lookahead:float=12.0+velocity*.36
	var aim_angle:float=(distance+lookahead)/meters_per_rad
	var aim:Vector3=track.road_position(aim_angle,0.0)
	var diff:Vector3=aim-position
	diff.y=0
	var desired_yaw:float=atan2(-diff.x,-diff.z) if diff.length_squared()>.02 else heading
	var yaw_error:float=wrapf(desired_yaw-heading,-PI,PI)
	var assist_power:float=clampf(1.0-absf(steer_input)*.83,.17,1.0)
	if drifting:
		assist_power*=.38
	var assist_rate:float=clampf(yaw_error*3.4,-1.85,1.85)*assist_power
	var manual_rate:float=-tan(clampf(wheel_angle,-.53,.53))*velocity/WHEEL_BASE*.12
	if drifting:
		manual_rate*=1.45
	turn_rate=clampf(manual_rate+assist_rate,-2.05,2.05)
	heading=wrapf(heading+turn_rate*dt,-PI,PI)
	var forward: Vector3=Vector3(-sin(heading),0.0,-cos(heading))
	var right: Vector3=Vector3(cos(heading),0.0,-sin(heading))
	# Tire slip can move the body sideways while yawing, rather than faking
	# a lateral lane offset divorced from the car's actual world transform.
	position += forward*velocity*dt + right*slide_velocity*dt*(.08 if not drifting else .17)

	var path:Dictionary=_nearest(track,position)
	var new_index: int=int(path["index"])
	var measured:float=float(path["meters"])
	var prior_measured:float=fposmod(distance,track.track_length)
	var step:float=measured-prior_measured
	if step>track.track_length*.5:
		step-=track.track_length
	elif step < -track.track_length*.5:
		step+=track.track_length
	# Only forward travel can earn checkpoint/lap progress. No shortcut
	# teleport from nearest-sample jumps and no reverse-drive cheating.
	var allowed:float=maxf(1.5,velocity*dt*1.65)
	if velocity<.5:
		step=0.0
	else:
		step=clampf(step,-allowed,allowed)
	distance=maxf(0.0,distance+step)
	sample_index=new_index
	lateral_offset=float(path["offset"])
	offroad=absf(lateral_offset)>9.25
	touched_wall=false
	if absf(lateral_offset)>EDGE_CONTACT:
		touched_wall=true
		lateral_offset=signf(lateral_offset)*EDGE_CONTACT
		position=(path["center"] as Vector3)+(path["side"] as Vector3)*lateral_offset
		# Move heading toward upcoming road after contact so steering can recover.
		var target_yaw:float=track.road_yaw(distance/meters_per_rad)
		heading=lerp_angle(heading,target_yaw,clampf(dt*2.8,0,1))
	position.y=float((path["center"] as Vector3).y)+.10
	return {"angle":distance/meters_per_rad,"offset":lateral_offset,
		"position":position,"heading":heading,"offroad":offroad,
		"wall":touched_wall,"yaw_delta":wrapf(heading-yaw_prior,-PI,PI),
		"turn_rate":turn_rate}
