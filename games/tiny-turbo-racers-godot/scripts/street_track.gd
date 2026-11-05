@tool
extends "res://scripts/real_track.gd"
## RibhLab MIDNIGHT RUSH — original night street racing city.
## Full spline route is reused from GP v0.5; streets, skyline, lighting and
## city props are wholly new. This is NOT a reproduction of Need for Speed.
const PBR = preload("res://scripts/realism_materials.gd")
const NIGHT_BLUE := Color("#071529")
const CITY_STONE := Color("#14223a")
const WINDOW_TONES: Array[Color] = [
	Color("#5ecafa"), Color("#e8bd85"), Color("#ab78ff"), Color("#70f1ea")
]
var neon_brightness: float = 1.0

func _build_lighting() -> void:
	var world_env := WorldEnvironment.new()
	world_env.name = "MidnightSkyAndAtmosphere"
	var env := Environment.new()
	env.background_mode = Environment.BG_SKY
	var sky := Sky.new()
	var atmosphere := ProceduralSkyMaterial.new()
	atmosphere.sky_top_color = Color("#030717")
	atmosphere.sky_horizon_color = Color("#101a38")
	atmosphere.ground_bottom_color = Color("#10151e")
	atmosphere.ground_horizon_color = Color("#13233c")
	sky.sky_material = atmosphere
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color("#9db7dc")
	env.ambient_light_energy = 0.35
	env.reflected_light_source = Environment.REFLECTION_SOURCE_BG
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.glow_enabled = true
	env.fog_enabled = true
	env.fog_light_color = Color("#0d1a35")
	env.fog_density = .0018
	world_env.environment = env
	add_child(world_env)
	var moon := DirectionalLight3D.new()
	moon.name = "Moonlight"
	moon.rotation_degrees = Vector3(-46,-25,0)
	moon.light_color = Color("#9fc4ff")
	moon.light_energy = .75
	moon.shadow_enabled = true
	moon.directional_shadow_max_distance = 110.0
	add_child(moon)
	# 12 actual dynamic street lamps around the course: mobile lighting budget.
	for i in range(12):
		var angle: float = TAU*(float(i)+.32)/12.0
		var pole: Vector3 = road_position(angle,17.0)
		var lamp := OmniLight3D.new()
		lamp.name = "AreaStreetLight_%02d" % i
		lamp.position = pole+Vector3(0,9.2,0)
		lamp.light_color = Color("#ffcc90") if i%2==0 else Color("#79c8fa")
		lamp.light_energy = 1.18
		lamp.omni_range = 20.0
		lamp.shadow_enabled = false
		add_child(lamp)

func _build_ground() -> void:
	var base := make_box(self,Vector3(0,-1.65,0),Vector3(920,2.5,920),Color.WHITE)
	base.name = "GroundAndPBRGrass"
	base.material_override = PBR.terrain_grass()
	# City foundation slabs do not overlap asphalt track, which sits above y~.5
	var lot := make_box(self,Vector3(0,-.29,0),Vector3(710,.20,710),Color("#293442"),.93)
	lot.name = "DarkConcreteCityBlocks"
	var ground_body := StaticBody3D.new()
	ground_body.name = "JoltTerrainCollision"
	ground_body.position = Vector3(0,-.55,0)
	var shape_node := CollisionShape3D.new()
	var shape := BoxShape3D.new()
	shape.size = Vector3(920,.9,920)
	shape_node.shape = shape
	ground_body.add_child(shape_node)
	var friction := PhysicsMaterial.new()
	friction.friction = .87
	ground_body.physics_material_override = friction
	add_child(ground_body)
	# Harbor water and distant geography are restrained, not cartoon mountains.
	var harbor := make_box(self,Vector3(330,-.28,-145),Vector3(170,.09,360),
		Color("#163e55"),.18)
	harbor.name = "MidnightHarborWater"
	for i in range(20):
		var a: float = TAU*float(i)/20.0
		var r: float = 350.0+float(i%4)*13.0
		make_sphere(self,Vector3(cos(a)*r,10.0,sin(a)*r),
			Vector3(20+float(i%4)*5,10+float(i%3)*7,23),
			Color("#12233b"),.90)

func _build_racetrack() -> void:
	# Real-world-width 18m 4-lane urban boulevard with photographic asphalt,
	# white lane dividers, amber center, raised sidewalks and guardrails.
	var surface := SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	var stripes := SurfaceTool.new()
	stripes.begin(Mesh.PRIMITIVE_TRIANGLES)
	var sidewalks := SurfaceTool.new()
	sidewalks.begin(Mesh.PRIMITIVE_TRIANGLES)
	var railing := SurfaceTool.new()
	railing.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in range(TRACK_SAMPLES):
		var a: float=TAU*float(i)/float(TRACK_SAMPLES)
		var b: float=TAU*float(i+1)/float(TRACK_SAMPLES)
		var u0: float=accumulated[i]/4.8
		var u1: float=accumulated[i+1]/4.8
		_mesh_band(surface,a,b,-TRACK_HALF_WIDTH,TRACK_HALF_WIDTH,.10,
			Color("#c3c4c8"),u0,u1)
		for side in [-1,1]:
			var sd: float=float(side)
			_mesh_band(sidewalks,a,b,sd*9.3,sd*15.1,.25,
				Color("#59616d"),u0,u1)
			_mesh_band(stripes,a,b,sd*8.55,sd*8.68,.15,
				Color("#e8eff6"),u0,u1)
			if i%28<15:
				_mesh_band(stripes,a,b,sd*4.35-.085,sd*4.35+.085,.155,
					Color("#e6edf4"),u0,u1)
			# Guardrail / sidewalks with steel highlight.
			_mesh_band(railing,a,b,sd*15.65,sd*15.85,1.00,
				Color("#627b90"),u0,u1)
			_mesh_band(railing,a,b,sd*15.65,sd*15.85,.45,
				Color("#283e58"),u0,u1)
		_mesh_band(stripes,a,b,-.14,.14,.153,Color("#ffd078"),u0,u1)
		if i<7:
			for tile in range(12):
				if (tile+(i/2))%2==0:
					var start: float=-TRACK_HALF_WIDTH+float(tile)*TRACK_HALF_WIDTH*2.0/12.0
					_mesh_band(stripes,a,b,start,start+TRACK_HALF_WIDTH*2.0/12.0,
						.172,Color("#f4f6f7"),u0,u1)
	_commit_road(surface,PBR.asphalt(),"CC0_PolyHaven_Asphalt_Track")
	var marker:=StandardMaterial3D.new()
	marker.vertex_color_use_as_albedo=true
	marker.roughness=.65
	marker.cull_mode=BaseMaterial3D.CULL_DISABLED
	_commit_road(stripes,marker,"UrbanCenterAndLaneMarkings")
	_commit_road(sidewalks,marker,"RaisedCitySidewalks")
	_commit_road(railing,marker,"StreetSafetyGuardrails")
	# Extra short off-ramp keeps previously authored facility and Jolt tests valid.
	var spur := SurfaceTool.new()
	spur.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in range(13,65):
		var a: float=TAU*float(i)/float(TRACK_SAMPLES)
		var b: float=TAU*float(i+1)/float(TRACK_SAMPLES)
		_mesh_band(spur,a,b,18.0,23.5,.15,Color("#aab0b6"),float(i),float(i+1))
	_commit_road(spur,PBR.asphalt(),"SideStreetConnector")

func _build_roadside() -> void:
	# Street lamps on both sides with lit poles and overhead cables.
	for i in range(82):
		var a: float=TAU*(float(i)+.35)/82.0
		for side in [-1,1]:
			var sd: float=float(side)
			var p:Vector3=road_position(a,sd*17.2)
			var post:=make_box(self,p+Vector3(0,4.75,0),
				Vector3(.19,9.5,.20),Color("#657384"),.38)
			post.name="MidnightStreetlamp"
			make_box(self,p+Vector3(-sd*.70,9.35,0),
				Vector3(1.55,.13,.30),Color("#71849f"),.26)
			make_box(self,p+Vector3(-sd*1.25,9.20,0),
				Vector3(.90,.14,.60),
				Color("#fff0bd") if (i+int(side))%3 else Color("#9ee3ff"),.15,true)
			if i%7==0:
				# Road bollards that mark sidewalk corners.
				make_box(self,p+Vector3(0,.32,2.7),Vector3(.22,.66,.22),Color("#e9e9e6"))
				make_box(self,p+Vector3(0,.65,2.7),Vector3(.25,.13,.25),Color("#f2b56b"),.15,true)

func _building_palette(i:int) -> Color:
	var palette: Array[Color]=[
		Color("#23364b"),Color("#263041"),Color("#192d3a"),
		Color("#31384b"),Color("#23334a"),Color("#2c3442")]
	return palette[i%palette.size()]

func _build_city() -> void:
	# About a hundred original high-rise buildings, no downloaded copyrighted city model.
	# Realistic windows are pooled into a handful of MultiMesh batches.
	var lit_windows: Array[Array] = [[],[],[],[]]
	for i in range(112):
		var a:float=TAU*(float(i)+.32)/112.0
		var side:float=1.0 if i%2==0 else -1.0
		var dist:float=32.0+float((i*17)%4)*13.0
		var pos:Vector3=road_position(a,side*dist)
		# Avoid repetition using seeded deterministic height/width.
		var h:float=18.0+float((i*19)%13)*4.1
		var w:float=10.0+float((i*7)%4)*3.0
		var d:float=12.0+float((i*5)%4)*4.0
		var building:=Node3D.new()
		building.name="DowntownTower_%03d" % i
		building.position=pos
		building.rotation.y=road_yaw(a)
		add_child(building)
		make_box(building,Vector3(0,h*.5,0),Vector3(w,h,d),_building_palette(i),.61)
		make_box(building,Vector3(0,h+.42,0),Vector3(w+.5,.85,d+.5),
			Color("#111d2e"),.38)
		# Hotel glow and glass curtain walls.
		make_box(building,Vector3(-side*(w*.49),h*.51,0),
			Vector3(.12,h*.70,d*.77),Color("#174660"),.18)
		var rows:int=mini(14,int(h/3.25))
		var cols:int=mini(6,int(d/3.8))
		for row in range(rows):
			for column in range(cols):
				if (row*7+column*11+i*3)%5==0:
					continue
				var tone:int=(i+row+column)%4
				var z:float=-d*.39+float(column)*d*.78/maxf(1,cols-1)
				var y:float=3.1+float(row)*3.0
				var window_x:float=-side*(w*.5+.035)
				var tr: Transform3D=building.transform*Transform3D(
					Basis().scaled(Vector3(.16,1.45,1.95)),
					Vector3(window_x,y,z))
				lit_windows[tone].append(tr)
		if i%8==0:
			# Rooftop antenna and neon sign blocks.
			make_box(building,Vector3(0,h+2.8,0),Vector3(.12,5.0,.12),
				Color("#a5b6ca"),.18)
			make_sphere(building,Vector3(0,h+5.3,0),Vector3(.30,.30,.30),
				Color("#f85c79"),.2,true)
		if i%11==0:
			_add_neon_sign(building,Vector3(0,4.5,-d*.50),w*.75,i)
	_flush_windows(lit_windows)
	# Atmospheric glass towers in the central skyline visible behind the street.
	for k in range(30):
		var ang:float=TAU*float(k)/30.0
		var rad:float=38.0+float(k%4)*7.0
		var tall:float=42.0+float((k*13)%17)*3.2
		var p:=Vector3(cos(ang)*rad,tall*.5,sin(ang)*rad)
		make_box(self,p,Vector3(11+float(k%3)*3,tall,14.0),
			_building_palette(k+3),.3)

func _flush_windows(groups: Array[Array]) -> void:
	for k in range(groups.size()):
		var items: Array=groups[k]
		if items.is_empty():
			continue
		var mesh:=BoxMesh.new()
		mesh.size=Vector3.ONE
		var mat:=StandardMaterial3D.new()
		mat.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED
		mat.albedo_color=WINDOW_TONES[k]
		mat.emission_enabled=true
		mat.emission=WINDOW_TONES[k]
		mat.emission_energy_multiplier=.85
		mesh.material=mat
		var mm:=MultiMesh.new()
		mm.transform_format=MultiMesh.TRANSFORM_3D
		mm.mesh=mesh
		mm.instance_count=items.size()
		for j in range(items.size()):
			mm.set_instance_transform(j,items[j])
		var inst:=MultiMeshInstance3D.new()
		inst.name="InstancedCityWindows_"+str(k)
		inst.multimesh=mm
		add_child(inst)

func _add_neon_sign(parent:Node3D,at:Vector3,span:float,i:int) -> void:
	var sign_col: Color=WINDOW_TONES[i%4]
	make_box(parent,at,Vector3(span,1.80,.28),Color("#0e1830"),.16)
	make_box(parent,at+Vector3(0,0,-.20),
		Vector3(span*.80,.18,.09),sign_col,.13,true)
	make_box(parent,at+Vector3(0,.50,-.20),
		Vector3(span*.47,.22,.09),Color("#f0f5ff"),.13,true)
	make_box(parent,at+Vector3(0,-.50,-.20),
		Vector3(span*.67,.14,.09),sign_col,.13,true)

func _build_beach() -> void:
	# Industrial waterfront by the south-east street segment.
	var docks:=Node3D.new()
	docks.name="HarborContainersAndCranes"
	docks.position=Vector3(255,0,-102)
	add_child(docks)
	for i in range(26):
		var x:float=float(i%7)*8.0-25
		var z:float=float(i/7)*9.0-22
		var y:float=1.5+float((i*3)%3)*2.9
		make_box(docks,Vector3(x,y,z),Vector3(7.4,3,8.3),
			[Color("#a5504a"),Color("#315b83"),Color("#b27c48"),Color("#d4d4cb")][i%4],.7)
	for k in range(3):
		var x:float=float(k)*18-12
		make_box(docks,Vector3(x,18,-31),Vector3(.85,36,.85),Color("#e4bb7d"),.4)
		make_box(docks,Vector3(x+7,35,-31),Vector3(15,.5,.8),Color("#e4bb7d"),.4)
		make_box(docks,Vector3(x+13,28,-31),Vector3(.20,14,.20),Color("#d8dde0"))

func _build_candy() -> void:
	# Four pedestrian underpasses / flyovers framing street racing district.
	for i in range(4):
		var a:float=TAU*(.22+float(i)*.235)
		var p:Vector3=road_position(a)
		var crossing:=Node3D.new()
		crossing.name="DowntownCrossing"
		crossing.position=p
		crossing.rotation.y=road_yaw(a)
		add_child(crossing)
		make_box(crossing,Vector3(-19,4.7,0),Vector3(2.3,9.4,3.0),Color("#404e60"))
		make_box(crossing,Vector3(19,4.7,0),Vector3(2.3,9.4,3.0),Color("#404e60"))
		make_box(crossing,Vector3(0,9.35,0),Vector3(41,1.2,7.6),Color("#303c4f"))
		make_box(crossing,Vector3(0,8.65,0),Vector3(26,.16,2.9),
			Color("#6ad0e7") if i%2==0 else Color("#fc548d"),.16,true)

func _build_dino() -> void:
	# Urban parks are small lighting accents; trees don't obstruct the circuit.
	for i in range(25):
		var a:float=TAU*(float(i)+.65)/25
		var offset:float=-25.0 if i%2 else 26.0
		_make_tree(road_position(a,offset),.60+float(i%3)*.15)

func _build_ferris_wheel() -> void:
	pass

func _build_finish_gate() -> void:
	var gate:=Node3D.new()
	gate.name="MidnightRushStreetStart"
	gate.position=road_position(0)
	gate.rotation.y=road_yaw(0)
	add_child(gate)
	for s in [-1,1]:
		make_box(gate,Vector3(float(s)*12.8,6.5,0),
			Vector3(.65,13.0,.75),Color("#555f75"))
	make_box(gate,Vector3(0,12.8,0),Vector3(27,1.8,1.7),Color("#162039"),.24)
	make_box(gate,Vector3(0,12.82,-.94),Vector3(21.8,.22,.11),
		Color("#ec5fa5"),.1,true)
	for i in range(5):
		var lit:Color=Color("#ef3154") if i%2 else Color("#23d9f4")
		make_sphere(gate,Vector3(-5.8+float(i)*2.9,11.43,-1.1),
			Vector3(.44,.44,.2),lit,.13,true)

func _build_real_track_facilities() -> void:
	# Police-free closed street racing festival: night city, not pursuit mode yet.
	# Road banners and parking lots, no private sponsor logos.
	for i in range(8):
		var angle:float=TAU*(.10+float(i)*.11)
		var booth:=Node3D.new()
		booth.name="StreetRaceMarshal"
		booth.position=road_position(angle,20.1)
		booth.rotation.y=road_yaw(angle)
		add_child(booth)
		make_box(booth,Vector3(0,1.75,0),Vector3(4.3,3.5,5.8),
			Color("#202f40"),.47)
		make_box(booth,Vector3(0,3.45,0),Vector3(4.6,.28,6.0),
			Color("#db528d"),.18,true)
		make_box(booth,Vector3(0,2.1,-3.0),Vector3(3.2,.63,.12),
			Color("#63d6e5"),.1,true)

func _build_clouds() -> void:
	# Stars are dots in the sky dome (no bright cartoon clouds at night).
	pass

func _build_instanced_vegetation() -> void:
	# Prior 540 batches were required by quality QA; convert to street plantings.
	for j in range(2):
		var hedge:=SphereMesh.new()
		hedge.radial_segments=5
		hedge.rings=3
		hedge.material=material(Color("#25544d") if j==0 else Color("#426656"),.95)
		var mm:=MultiMesh.new()
		mm.transform_format=MultiMesh.TRANSFORM_3D
		mm.mesh=hedge
		mm.instance_count=270
		var rand:=RandomNumberGenerator.new()
		rand.seed=41088+j*31
		for n in range(mm.instance_count):
			var a:float=rand.randf_range(0,TAU)
			var d:float=22.0+rand.randf_range(0,4.0)
			var p:Vector3=road_position(a,d if j==0 else -d)
			var scale:float=rand.randf_range(.4,.78)
			mm.set_instance_transform(n,Transform3D(
				Basis().scaled(Vector3(scale,.45*scale,scale)),p+Vector3(0,.15,0)))
		var inst:=MultiMeshInstance3D.new()
		inst.multimesh=mm
		inst.name="InstancedStreetTrees_"+str(j)
		add_child(inst)
