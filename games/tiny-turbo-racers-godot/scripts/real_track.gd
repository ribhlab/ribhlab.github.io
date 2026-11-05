@tool
extends "res://scripts/world_builder.gd"
## RibhLab International Circuit: native curving racing circuit, not a circular toy loop.
## Uses arc-length-sampled closed Catmull-Rom spline with actual cornering geometry.
## Designed for realistic sports cars, braking zones, grandstands and pit lane.
const Materials = preload("res://scripts/realism_materials.gd")

const TRACK_SAMPLES: int = 1536
const TRACK_HALF_WIDTH: float = 9.1
const CONTROL: Array[Vector3] = [
	Vector3(-95,0,-100),
	Vector3(-39,0,-102),
	Vector3(42,0,-100),
	Vector3(110,0,-91),
	Vector3(158,0,-62),
	Vector3(201,0,-20),
	Vector3(216,0,35),
	Vector3(196,0,88),
	Vector3(145,0,116),
	Vector3(96,0,98),
	Vector3(53,0,85),
	Vector3(16,0,106),
	Vector3(-2,0,157),
	Vector3(-42,0,183),
	Vector3(-97,0,173),
	Vector3(-154,0,145),
	Vector3(-187,0,91),
	Vector3(-178,0,40),
	Vector3(-155,0,-13),
	Vector3(-170,0,-58),
	Vector3(-155,0,-91),
]
## Three actual layouts, each separately sampled into an arc-length spline.
## 0 Midnight Harbor, 1 Sunset Coast, 2 Pine Mountain.
var circuit_variant: int = 0
var alternate_control: Array[Vector3] = []
const COAST_ROAD: Array[Vector3] = [
	Vector3(-150,0,-85), Vector3(-55,0,-104), Vector3(38,0,-99),
	Vector3(129,0,-83), Vector3(207,0,-40), Vector3(239,0,19),
	Vector3(211,0,101), Vector3(150,0,154), Vector3(62,0,168),
	Vector3(-11,0,133), Vector3(-63,0,104), Vector3(-108,0,145),
	Vector3(-187,0,168), Vector3(-232,0,102), Vector3(-230,0,29),
	Vector3(-194,0,-37)
]
const MOUNTAIN_ROAD: Array[Vector3] = [
	Vector3(-130,0,-112), Vector3(-54,0,-113), Vector3(28,0,-102),
	Vector3(116,0,-127), Vector3(190,0,-119), Vector3(230,0,-72),
	Vector3(208,0,-12), Vector3(149,0,31), Vector3(75,0,15),
	Vector3(28,0,58), Vector3(66,0,114), Vector3(150,0,127),
	Vector3(172,0,187), Vector3(99,0,219), Vector3(23,0,191),
	Vector3(-38,0,153), Vector3(-110,0,197), Vector3(-187,0,166),
	Vector3(-237,0,101), Vector3(-195,0,37), Vector3(-146,0,-25)
]

func set_circuit(index: int) -> void:
	circuit_variant = clampi(index,0,2)
	match circuit_variant:
		1: alternate_control=COAST_ROAD.duplicate()
		2: alternate_control=MOUNTAIN_ROAD.duplicate()
		_: alternate_control=[]

func circuit_title() -> String:
	return ["MIDNIGHT HARBOR", "SUNSET COAST", "PINE MOUNTAIN"][circuit_variant]

var centerline: PackedVector3Array = PackedVector3Array()
var accumulated: PackedFloat32Array = PackedFloat32Array()
var track_length: float = 0.0

func _catmull(index: int, u: float) -> Vector3:
	var points: Array[Vector3] = alternate_control if alternate_control.size()>3 else CONTROL
	var n: int = points.size()
	var a: Vector3 = points[posmod(index-1,n)]
	var b: Vector3 = points[posmod(index,n)]
	var c: Vector3 = points[posmod(index+1,n)]
	var d: Vector3 = points[posmod(index+2,n)]
	var u2: float = u*u
	var u3: float = u2*u
	return .5*(2.0*b+(-a+c)*u+(2.0*a-5.0*b+4.0*c-d)*u2+
		(-a+3.0*b-3.0*c+d)*u3)

func _prepare_spline() -> void:
	var point_count: int = alternate_control.size() if alternate_control.size()>3 else CONTROL.size()
	centerline.clear()
	accumulated.clear()
	track_length = 0.0
	for i in range(TRACK_SAMPLES+1):
		var t: float = float(i) / float(TRACK_SAMPLES) * float(point_count)
		var idx: int = mini(int(floor(t)),point_count-1)
		var local: float = t-float(idx)
		var v: Vector3 = _catmull(idx,local)
		# Mild smooth elevation changes, including one raised outer turn.
		v.y = .32 + (7.3 if circuit_variant==2 else 1.4 if circuit_variant==1 else 1.45) * pow(maxf(sin(t*TAU/float(point_count)+.20),0.0),4.0)
		if i>0:
			track_length += centerline[i-1].distance_to(v)
		centerline.push_back(v)
		accumulated.push_back(track_length)

func _center_at_distance(distance: float) -> Vector3:
	var target: float = fposmod(distance,track_length)
	var low: int = 0
	var high: int = accumulated.size()-1
	while high-low>1:
		var mid: int = (low+high)/2
		if accumulated[mid] < target:
			low=mid
		else:
			high=mid
	var span: float = maxf(.000001,accumulated[high]-accumulated[low])
	return centerline[low].lerp(centerline[high],(target-accumulated[low])/span)

func _center_at_angle(angle: float) -> Vector3:
	return _center_at_distance(fposmod(angle,TAU)/TAU*track_length)

func road_tangent(angle: float) -> Vector3:
	var step: float = 2.1
	var at: float = fposmod(angle,TAU)/TAU*track_length
	var v: Vector3 = _center_at_distance(at+step)-_center_at_distance(at-step)
	v.y=0
	return v.normalized()

func road_position(angle: float, offset: float = 0.0) -> Vector3:
	var center: Vector3 = _center_at_angle(angle)
	var tangent: Vector3 = road_tangent(angle)
	var sideways := Vector3(tangent.z,0,-tangent.x)
	return center+sideways*offset

func road_yaw(angle: float) -> float:
	var t: Vector3 = road_tangent(angle)
	return atan2(-t.x,-t.z)

func road_meters_per_radian() -> float:
	return track_length / TAU

func build_world() -> void:
	_prepare_spline()
	super.build_world()
	_build_real_track_facilities()

func _build_ground() -> void:
	var floor_mesh := make_box(self,Vector3(0,-1.62,0),Vector3(900,2.4,900),Color.WHITE)
	floor_mesh.material_override = Materials.terrain_grass()
	var ground_body := StaticBody3D.new()
	ground_body.name = "JoltTerrainCollision"
	ground_body.position = Vector3(0,-.68,0)
	var collider := CollisionShape3D.new()
	var shape := BoxShape3D.new()
	shape.size = Vector3(900,1.4,900)
	collider.shape=shape
	ground_body.add_child(collider)
	var pm := PhysicsMaterial.new()
	pm.friction = .88
	ground_body.physics_material_override=pm
	add_child(ground_body)
	# Vegetation beyond track is batched; hills use modest silhouettes.
	for i in range(30):
		var a: float = TAU*float(i)/30.0
		var r: float = 270+float(i%3)*22
		make_sphere(self,Vector3(cos(a)*r,10.0,sin(a)*r),Vector3(32,17+float(i%4)*3,28),Color("#6cae83"),.89)
	# Industrial-looking lake beside the southern stretch.
	make_box(self,Vector3(240,-.36,-130),Vector3(112,.15,230),Color("#439fc1"),.20)

func _add_triangle(st: SurfaceTool,a: Vector3,b: Vector3,c: Vector3,
		uva: Vector2,uvb: Vector2,uvc: Vector2,tint: Color) -> void:
	st.set_color(tint)
	st.set_uv(uva)
	st.add_vertex(a)
	st.set_color(tint)
	st.set_uv(uvb)
	st.add_vertex(b)
	st.set_color(tint)
	st.set_uv(uvc)
	st.add_vertex(c)

func _mesh_band(st: SurfaceTool,angle0:float,angle1:float,off0:float,off1:float,
		y:float,c:Color,u0:float,u1:float) -> void:
	var a: Vector3=road_position(angle0,off0)+Vector3(0,y,0)
	var b: Vector3=road_position(angle0,off1)+Vector3(0,y,0)
	var d: Vector3=road_position(angle1,off0)+Vector3(0,y,0)
	var e: Vector3=road_position(angle1,off1)+Vector3(0,y,0)
	_add_triangle(st,a,b,e,Vector2(u0,0),Vector2(u0,4),Vector2(u1,4),c)
	_add_triangle(st,a,e,d,Vector2(u0,0),Vector2(u1,4),Vector2(u1,0),c)

func _commit_road(st: SurfaceTool,m: Material,name: String) -> void:
	st.generate_normals()
	var inst:=MeshInstance3D.new()
	inst.mesh=st.commit()
	inst.material_override=m
	inst.name=name
	add_child(inst)

func _build_racetrack() -> void:
	var surface:=SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	var paint:=SurfaceTool.new()
	paint.begin(Mesh.PRIMITIVE_TRIANGLES)
	var barriers:=SurfaceTool.new()
	barriers.begin(Mesh.PRIMITIVE_TRIANGLES)
	var white:Color=Color("#fff9e8")
	var road_tint:Color=Color("#c5c5c5")
	for i in range(TRACK_SAMPLES):
		var a:float=TAU*float(i)/float(TRACK_SAMPLES)
		var b:float=TAU*float(i+1)/float(TRACK_SAMPLES)
		var u0:float=accumulated[i]/4.6
		var u1:float=accumulated[i+1]/4.6
		_mesh_band(surface,a,b,-TRACK_HALF_WIDTH,TRACK_HALF_WIDTH,0.10,road_tint,u0,u1)
		var red_white:Color=Color("#f54a54") if (i/9)%2==0 else white
		_mesh_band(paint,a,b,-TRACK_HALF_WIDTH-.7,-TRACK_HALF_WIDTH+.35,.16,red_white,u0,u1)
		_mesh_band(paint,a,b,TRACK_HALF_WIDTH-.35,TRACK_HALF_WIDTH+.7,.16,red_white,u0,u1)
		# Painted solid white boundary markers, offset from the red/white kerb.
		_mesh_band(paint,a,b,-TRACK_HALF_WIDTH+0.55,-TRACK_HALF_WIDTH+0.70,.17,white,u0,u1)
		_mesh_band(paint,a,b,TRACK_HALF_WIDTH-0.70,TRACK_HALF_WIDTH-0.55,.17,white,u0,u1)
		if i%18<9:
			_mesh_band(paint,a,b,-0.11,0.11,.18,Color("#ffde88"),u0,u1)
		# Wide striped starting grid for motorsport authenticity.
		if i<10:
			for k in range(10):
				if (k+i/2)%2==0:
					var aa:float=-TRACK_HALF_WIDTH+float(k)*(TRACK_HALF_WIDTH*2/10)
					_mesh_band(paint,a,b,aa,aa+TRACK_HALF_WIDTH*2/10,.21,white,u0,u1)
		# Twin metal Armco strips following every bend, merged into one mesh.
		for side in [-1,1]:
			var s:float=float(side)
			for hh in [.73,1.20]:
				_mesh_band(barriers,a,b,s*12.8,s*12.97,hh,
					Color("#b0b9c8") if i%12<9 else Color("#e3e7ef"),u0,u1)
	_commit_road(surface,Materials.asphalt(),"CC0_PolyHaven_Asphalt_Track")
	var m:=StandardMaterial3D.new()
	m.vertex_color_use_as_albedo=true
	m.roughness=.7
	m.cull_mode=BaseMaterial3D.CULL_DISABLED
	_commit_road(paint,m,"RaceKerbsAndPaintedMarkings")
	_commit_road(barriers,m,"ArmcoSafetyBarriers")
	# Visible pit lane with merge strip and white boundary.
	var pit:=SurfaceTool.new()
	pit.begin(Mesh.PRIMITIVE_TRIANGLES)
	var pitlines:=SurfaceTool.new()
	pitlines.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in range(3,95):
		var a:float=TAU*float(i)/float(TRACK_SAMPLES)
		var b:float=TAU*float(i+1)/float(TRACK_SAMPLES)
		_mesh_band(pit,a,b,16.6,23.5,.10,Color("#9eabb3"),float(i)/4.0,float(i+1)/4.0)
		_mesh_band(pitlines,a,b,16.35,16.58,.18,white,float(i),float(i+1))
	_commit_road(pit,Materials.asphalt(),"ActualPitLane")
	_commit_road(pitlines,m,"PitLaneWhiteLine")

func _build_roadside() -> void:
	# Rounded tire stacks every 90 meters, visible up close during overtakes.
	for i in range(105):
		var a:float=TAU*float(i)/105
		for side in [-1,1]:
			var p:Vector3=road_position(a,float(side)*13.2)
			var post:=make_box(self,p+Vector3(0,.8,0),Vector3(.16,1.65,.16),Color("#d4dae1"))
			post.name="SafetyFenceSupport"
			if i%4==0:
				make_sphere(self,p+Vector3(0,2.25,0),Vector3(.25,.25,.25),Color("#ffeaa2"),.3,true)
	# Braking-zone distance markers (no fake international race sponsors).
	for i in [8,18,39,54,73,90]:
		var a:float=TAU*float(i)/105
		var node:=Node3D.new()
		node.position=road_position(a,15.4)
		node.rotation.y=road_yaw(a)
		add_child(node)
		make_box(node,Vector3(0,1.6,0),Vector3(2.4,2.2,.28),Color("#f7fcff"))
		make_box(node,Vector3(0,1.6,-.2),Vector3(1.75,.18,.08),Color("#e94d52"))
		for k in range(3):
			make_box(node,Vector3(-.65+float(k)*.65,.85,-.2),Vector3(.35,.22,.08),Color("#162d53"))

func _build_city() -> void:
	# Replace toy buildings with a real paddock, pit garages and control tower.
	var pad:=Node3D.new()
	pad.name="PitBuildingAndRacePaddock"
	pad.position=road_position(.185,33.0)
	pad.rotation.y=road_yaw(.185)
	add_child(pad)
	make_box(pad,Vector3(0,5.3,0),Vector3(16.0,10.3,120.0),Color("#dfe5e9"),.55)
	make_box(pad,Vector3(-6.3,4.0,-.4),Vector3(.5,5.2,118.0),Color("#313d50"),.30)
	make_box(pad,Vector3(0,10.8,0),Vector3(18.5,.7,123.0),Color("#273d56"),.3)
	for j in range(10):
		var z:float=-51.0+float(j)*11.2
		make_box(pad,Vector3(-8.36,3.1,z),Vector3(.30,5.5,8.8),Color("#40546c"),.28)
		make_box(pad,Vector3(-8.61,5.42,z),Vector3(.08,.24,8.4),Color("#eac56d"),.2,true)
		make_box(pad,Vector3(-8.5,1.0,z-2.1),Vector3(.09,.23,1.5),Color("#ea5c66"))
		make_box(pad,Vector3(-8.5,1.0,z+2.1),Vector3(.09,.23,1.5),Color("#5dbfef"))
		make_box(pad,Vector3(0,8.85,z),Vector3(12.0,.25,8.9),Color("#92bdde"),.15)
	make_box(pad,Vector3(0,19.1,-32),Vector3(12,15,21),Color("#bed2d9"),.3)
	for j in range(5):
		make_box(pad,Vector3(-6.12,14.1+float(j)*2.3,-32),Vector3(.15,1.14,18),Color("#3f769b"),.18)
	make_box(pad,Vector3(0,27,-32),Vector3(13.5,.6,22.0),Color("#cbd7d9"))

func _build_beach() -> void:
	# In place of a candy beach: real track-side scenic lake and pit access.
	for i in range(15):
		var a:float=.9+float(i)*.025
		var p:Vector3=road_position(a,25.0+float(i%3)*4.0)
		make_sphere(self,p+Vector3(0,1.0,0),Vector3(3,1.2,2.2),Color("#8c9d8b"),.88)
		if i%2==0:
			_make_tree(p+Vector3(2.0,0,4.2),.8)

func _build_candy() -> void:
	# Motorsport grandstands in three spectator sectors.
	for k in range(4):
		_make_grandstand(TAU*(.24+float(k)*.17),26.0 if k%2==0 else -28.0)

func _make_grandstand(angle:float,offset:float) -> void:
	var stand:=Node3D.new()
	stand.name="Grandstand"
	stand.position=road_position(angle,offset)
	stand.rotation.y=road_yaw(angle)
	add_child(stand)
	make_box(stand,Vector3(0,1.4,0),Vector3(17.0,2.8,39.0),Color("#5a6a72"),.9)
	for row in range(7):
		var height:float=2.8+float(row)*.69
		var x:float=7.0-float(row)*1.0
		make_box(stand,Vector3(x,height,0),Vector3(1.5,.42,37.0),Color("#b2bec9"),.8)
		for strip in range(12):
			var z:float=-16.0+float(strip)*2.7
			make_box(stand,Vector3(x,height+.42,z),Vector3(1.1,.5,2.20),
				[Color("#e74c51"),Color("#3868a6"),Color("#f2d561")][(row+strip)%3],.74)
	for z in [-16.0,16.0]:
		make_box(stand,Vector3(0,7.9,z),Vector3(.28,12,.28),Color("#d9dee2"),.45)
	make_box(stand,Vector3(0,13.9,0),Vector3(20,.65,42),Color("#26374c"),.48)
	make_box(stand,Vector3(0,13.65,-21.1),Vector3(20,.20,.15),Color("#ff4e56"),.24,true)

func _build_dino() -> void:
	# Wooded hills replace children-oriented dinosaur props in this racing circuit.
	for i in range(42):
		var a:float=TAU*float(i)/42.0
		var p:Vector3=road_position(a,36.0+float(i%4)*4.5)
		_make_tree(p,.7+float(i%3)*.14)

func _build_ferris_wheel() -> void:
	# Realistic race-circuit facilities rather than a fairground wheel.
	pass

func _build_clouds() -> void:
	# Built-in procedural HDR-like sky is configured in the world environment.
	pass

func _build_finish_gate() -> void:
	var gate:=Node3D.new()
	gate.name="RibhLabStartFinishGantry"
	gate.position=road_position(0.0)
	gate.rotation.y=road_yaw(0.0)
	add_child(gate)
	for side in [-1,1]:
		make_box(gate,Vector3(float(side)*11.8,6.4,0),Vector3(.8,12.8,.8),Color("#eef2f5"))
		make_box(gate,Vector3(float(side)*11.8,8.0,-.54),Vector3(.8,.9,.1),Color("#f34e56"))
	make_box(gate,Vector3(0,12.8,0),Vector3(25.3,2.0,2.5),Color("#273347"),.3)
	for i in range(24):
		make_box(gate,Vector3(-11.5+float(i),12.8,-1.31),Vector3(.97,.95,.1),
			Color("#f7f9fa") if i%2==0 else Color("#192d42"))
	make_box(gate,Vector3(0,14.2,0),Vector3(26.0,.4,2.9),Color("#aebac7"))
	# Starting lights
	for j in range(5):
		make_sphere(gate,Vector3(-5.6+float(j)*2.8,11.30,-1.32),Vector3(.57,.52,.25),Color("#f34b54"),.24,true)

func _build_real_track_facilities() -> void:
	# Marshal stations and race timing booths near corner exits.
	for i in range(6):
		var a:float=TAU*(.08+float(i)*.155)
		var booth:=Node3D.new()
		booth.position=road_position(a,-19.3)
		booth.rotation.y=road_yaw(a)
		add_child(booth)
		make_box(booth,Vector3(0,2.1,0),Vector3(4.8,3.5,5.2),Color("#dee2e6"),.5)
		make_box(booth,Vector3(0,4.0,0),Vector3(5.5,.35,5.8),Color("#ea5059"),.26)
		make_box(booth,Vector3(-2.5,2.6,0),Vector3(.08,.9,3.4),Color("#4999c2"),.16)
		# CCTV mast
		make_box(booth,Vector3(2.8,5.2,1.2),Vector3(.16,8,.16),Color("#bdc7d2"))
		make_box(booth,Vector3(2.3,9.25,1.2),Vector3(1.2,.36,.45),Color("#293b50"))

func _build_instanced_vegetation() -> void:
	# Approximately 520 patches of grass as 2 MultiMeshes, not 520 draw calls.
	for j in range(2):
		var foliage:=SphereMesh.new()
		foliage.radial_segments=5
		foliage.rings=3
		foliage.material=material(Color("#519960") if j==0 else Color("#81bd6b"),.96)
		var mm:=MultiMesh.new()
		mm.transform_format=MultiMesh.TRANSFORM_3D
		mm.mesh=foliage
		mm.instance_count=270
		var rng:=RandomNumberGenerator.new()
		rng.seed=111930+j*319
		for i in range(mm.instance_count):
			var a:float=rng.randf_range(0,TAU)
			var r:float=rng.randf_range(35.0,72.0)
			var p:Vector3=road_position(a,TRACK_HALF_WIDTH+r)
			var k:float=rng.randf_range(.4,1.3)
			mm.set_instance_transform(i,Transform3D(Basis().scaled(Vector3(k,.45*k,k)),Vector3(p.x,.10,p.z)))
		var inst:=MultiMeshInstance3D.new()
		inst.multimesh=mm
		inst.name="BatchedCircuitGrass"
		add_child(inst)
