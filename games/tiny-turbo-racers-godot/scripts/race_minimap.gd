extends Control
## v0.9 interactive race HUD minimap.
## Draws the true spline centreline of each circuit and real world positions
## of the manually controlled car and AI drivers. No pre-rendered fake track.
var track: Node3D
var line: PackedVector2Array=PackedVector2Array()
var limits: Rect2=Rect2()
var player_world: Vector3=Vector3.ZERO
var rival_world: Array[Vector3]=[]
var color: Color=Color("#60e5fa")

func _ready() -> void:
	mouse_filter=Control.MOUSE_FILTER_IGNORE

func configure_world(world: Node3D) -> void:
	track=world
	line.clear()
	rival_world.clear()
	var low:=Vector2(INF,INF)
	var high:=Vector2(-INF,-INF)
	for i in range(129):
		var p: Vector3=world.road_position(TAU*float(i)/128.0)
		var projected:=Vector2(p.x,p.z)
		low=low.min(projected)
		high=high.max(projected)
		line.push_back(projected)
	limits=Rect2(low,high-low)
	color=[Color("#4fe3ff"),Color("#ffbf6c"),Color("#b6f390")][world.circuit_variant]
	queue_redraw()

func _map(p: Vector2) -> Vector2:
	var margin: float=14.0
	var usable:Vector2=size-Vector2.ONE*margin*2.0
	var denom:Vector2=Vector2(maxf(1.0,limits.size.x),maxf(1.0,limits.size.y))
	var scale:float=minf(usable.x/denom.x,usable.y/denom.y)
	var center:=limits.position+limits.size*.5
	var local:Vector2=(p-center)*scale
	# Map top is world -Z; preserve physical orientation.
	return size*.5+local

func set_positions(player_position: Vector3, rivals: Array[Vector3]) -> void:
	player_world=player_position
	rival_world=rivals
	queue_redraw()

func _draw() -> void:
	if line.size()<3:
		return
	draw_rect(Rect2(Vector2.ZERO,size),Color("#071629",.78),true)
	draw_rect(Rect2(Vector2.ZERO,size),Color("#4aa2cd",.65),false,2.0)
	var points:=PackedVector2Array()
	for p in line:
		points.push_back(_map(p))
	draw_polyline(points,Color("#172b4d"),10.0,true)
	draw_polyline(points,color,3.2,true)
	var start:Vector2=_map(line[0])
	draw_circle(start,3.8,Color.WHITE)
	for p in rival_world:
		var dot:Vector2=_map(Vector2(p.x,p.z))
		draw_circle(dot,4.6,Color("#ff6c82"))
		draw_circle(dot,2.1,Color.WHITE)
	var current:Vector2=_map(Vector2(player_world.x,player_world.z))
	draw_circle(current,8.0,Color("#05121e"))
	draw_circle(current,5.5,Color("#5afb77"))
	draw_circle(current,2.0,Color.WHITE)
