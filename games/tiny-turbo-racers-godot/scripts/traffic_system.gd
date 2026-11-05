extends Node3D
## Mid-distance city traffic for the Midnight Rush closed-course race.
## Four affordable LOD vehicles; detailed CC0 258-mesh GT cars remain players/rivals.
## They move along the same 3D road spline, with near-miss and collision callbacks.
const TRAFFIC_COUNT: int = 5
var route
var vehicles: Array[Dictionary] = []
var elapsed: float = 0.0
var collision_lock: float = 0.0
var near_miss_lock: Dictionary = {}

func setup(track: Node3D) -> void:
	route = track
	for i in range(TRAFFIC_COUNT):
		var root := Node3D.new()
		root.name = "StreetTraffic_%02d" % i
		add_child(root)
		var paint: Color = [
			Color("#c7d1db"),Color("#f2c858"),Color("#596b90"),
			Color("#e5e9e5"),Color("#cf5259")][i]
		_make_lod_car(root,paint,i)
		vehicles.append({
			"node":root,"angle":.20+float(i)*.68,
			"lane": [-6.20,-2.1,2.1,6.20,2.1][i],
			"speed":13.8+float(i%3)*2.7,
			"counted":false
		})
	reset()

func reset() -> void:
	elapsed = 0.0
	collision_lock=0.0
	near_miss_lock.clear()
	for i in range(vehicles.size()):
		vehicles[i]["angle"] = .20+float(i)*.68
		vehicles[i]["counted"] = false
		_place(i)

func _mat(color: Color,glow: bool = false) -> StandardMaterial3D:
	var mat:=StandardMaterial3D.new()
	mat.albedo_color=color
	mat.metallic=.25
	mat.roughness=.28
	if glow:
		mat.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED
		mat.emission_enabled=true
		mat.emission=color
		mat.emission_energy_multiplier=1.3
	return mat

func _part(car: Node3D,pos:Vector3,sz:Vector3,mat: Material) -> void:
	var part:=MeshInstance3D.new()
	var mesh:=BoxMesh.new()
	mesh.size=sz
	part.mesh=mesh
	part.material_override=mat
	part.position=pos
	car.add_child(part)

func _make_lod_car(car: Node3D,color:Color,index:int) -> void:
	# One smooth body and roof silhouette, distinct sedan/van/service profiles.
	var body:=_mat(color)
	var glass:=_mat(Color("#153a5e"))
	var dark:=_mat(Color("#18212b"))
	var lamps:=_mat(Color("#ff496c"),true)
	var headlamp:=_mat(Color("#fff2d1"),true)
	var chrome:=_mat(Color("#8e9da9"))
	var van:bool=index%3==0
	_part(car,Vector3(0,.75,0),Vector3(1.84,.80,3.78 if van else 3.45),body)
	_part(car,Vector3(0,1.37,.20),Vector3(1.58,.80,2.35 if van else 2.0),glass)
	_part(car,Vector3(0,1.75,.20),Vector3(1.66,.11,2.2 if van else 1.86),body)
	for side in [-1,1]:
		for end in [-1,1]:
			_part(car,Vector3(float(side)*.99,.36,float(end)*1.12),
				Vector3(.25,.68,.67),dark)
		_part(car,Vector3(float(side)*.74,.73,1.74),Vector3(.23,.16,.08),lamps)
		_part(car,Vector3(float(side)*.74,.78,-1.74),Vector3(.23,.14,.08),headlamp)
	_part(car,Vector3(0,.57,1.78),Vector3(1.60,.15,.08),chrome)

func _place(index:int) -> void:
	var v:Dictionary=vehicles[index]
	var at:float=float(v["angle"])
	var node:Node3D=v["node"]
	node.position=route.road_position(at,float(v["lane"]))+Vector3(0,.07,0)
	node.rotation.y=route.road_yaw(at)

func tick(delta: float,player_angle:float,player_lane:float,player_speed:float) -> Dictionary:
	elapsed+=delta
	collision_lock=maxf(0.0,collision_lock-delta)
	var touched:bool=false
	var near_misses:int=0
	for i in range(vehicles.size()):
		var v:Dictionary=vehicles[i]
		v["angle"] = float(v["angle"])+float(v["speed"])*delta/route.road_meters_per_radian()
		_place(i)
		var delta_angle:float=absf(wrapf(player_angle-float(v["angle"]),-PI,PI))
		var separation:float=delta_angle*route.road_meters_per_radian()
		var lateral:float=absf(player_lane-float(v["lane"]))
		if player_speed>15.0 and separation<3.8 and lateral<2.2 and collision_lock<=0:
			touched=true
			collision_lock=1.5
		elif player_speed>17.0 and separation<5.3 and lateral>2.1 and lateral<4.5:
			if not near_miss_lock.has(i):
				near_miss_lock[i]=true
				near_misses+=1
		elif separation>20.0:
			near_miss_lock.erase(i)
	return {"collision":touched,"near_misses":near_misses}
