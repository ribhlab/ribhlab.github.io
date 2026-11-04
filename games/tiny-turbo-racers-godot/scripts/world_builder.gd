extends Node3D
## One full circular 3D toy-racing course built without downloaded models.
## Four scenic biomes sit around one playable circuit.
const RADIUS: float = 84.0
const HALF_WIDTH: float = 10.0
const SEGMENTS: int = 176
var cache: Dictionary = {}

func road_position(angle: float, offset: float = 0.0) -> Vector3:
	var r: float = RADIUS + offset
	return Vector3(cos(angle) * r, 0.0, sin(angle) * r)

func road_yaw(angle: float) -> float:
	# The cars face local -Z; along increasing track angle.
	return PI - angle

func build_world() -> void:
	_build_lighting()
	_build_ground()
	_build_racetrack()
	_build_roadside()
	_build_city()
	_build_beach()
	_build_candy()
	_build_dino()
	_build_ferris_wheel()
	_build_finish_gate()
	_build_clouds()

func material(color: Color, roughness: float = 0.46, glow: bool = false) -> StandardMaterial3D:
	var key: String = color.to_html(true) + "-" + str(roughness) + "-" + str(glow)
	if cache.has(key):
		return cache[key]
	var m := StandardMaterial3D.new()
	m.albedo_color = color
	m.roughness = roughness
	m.metallic = 0.0 if roughness > 0.48 else 0.08
	if glow:
		m.emission_enabled = true
		m.emission = color
		m.emission_energy_multiplier = 1.8
	cache[key] = m
	return m

func make_box(parent: Node3D, position: Vector3, size: Vector3, color: Color, roughness: float = 0.45, glow: bool = false) -> MeshInstance3D:
	var m := MeshInstance3D.new()
	var mesh := BoxMesh.new()
	mesh.size = size
	m.mesh = mesh
	m.material_override = material(color, roughness, glow)
	m.position = position
	parent.add_child(m)
	return m

func make_sphere(parent: Node3D, position: Vector3, scale3: Vector3, color: Color, roughness: float = 0.5, glow: bool = false) -> MeshInstance3D:
	var m := MeshInstance3D.new()
	var mesh := SphereMesh.new()
	mesh.radial_segments = 10
	mesh.rings = 6
	m.mesh = mesh
	m.material_override = material(color, roughness, glow)
	m.position = position
	m.scale = scale3
	parent.add_child(m)
	return m

func make_cylinder(parent: Node3D, position: Vector3, radius: float, height: float, color: Color, edges: int = 10) -> MeshInstance3D:
	var m := MeshInstance3D.new()
	var mesh := CylinderMesh.new()
	mesh.top_radius = radius
	mesh.bottom_radius = radius
	mesh.height = height
	mesh.radial_segments = edges
	m.mesh = mesh
	m.material_override = material(color)
	m.position = position
	parent.add_child(m)
	return m

func _build_lighting() -> void:
	var world_env := WorldEnvironment.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color("#71d5fa")
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color("#edfaff")
	env.ambient_light_energy = 0.86
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	world_env.environment = env
	add_child(world_env)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-48, -38, 0)
	sun.light_color = Color("#fff1ce")
	sun.light_energy = 1.65
	sun.shadow_enabled = false # Mobile battery-friendly
	add_child(sun)

func _build_ground() -> void:
	make_box(self, Vector3(0,-1.55,0), Vector3(400,2.5,400), Color("#78d36e"))
	make_cylinder(self, Vector3(0,-0.11,0), RADIUS - HALF_WIDTH - 0.55, 0.23, Color("#87dd78"), 60)
	# Hills and ocean beyond the outside of the circular course.
	make_box(self, Vector3(150,-.45,0), Vector3(90,.4,240), Color("#50d7ec"),.24)
	for i in range(22):
		var a: float = TAU * float(i) / 22.0
		var far: float = 145.0 + float(i % 4) * 12.0
		var p := road_position(a,far - RADIUS)
		make_sphere(self,Vector3(p.x, 3.0, p.z),Vector3(11.0 + float(i%3)*4.0, 6.0 + float(i%5),10.0),Color("#68c78c"))

func _triangle(st: SurfaceTool, p1: Vector3, p2: Vector3, p3: Vector3, color: Color) -> void:
	st.set_color(color)
	st.add_vertex(p1)
	st.set_color(color)
	st.add_vertex(p2)
	st.set_color(color)
	st.add_vertex(p3)

func _band(st: SurfaceTool, inner: float, outer: float, a: float, b: float, y: float, color: Color) -> void:
	var p1 := Vector3(cos(a)*inner,y,sin(a)*inner)
	var p2 := Vector3(cos(a)*outer,y,sin(a)*outer)
	var p3 := Vector3(cos(b)*outer,y,sin(b)*outer)
	var p4 := Vector3(cos(b)*inner,y,sin(b)*inner)
	_triangle(st,p1,p2,p3,color)
	_triangle(st,p1,p3,p4,color)

func _build_racetrack() -> void:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var asphalt := Color("#627389")
	var yellow := Color("#ffeb9d")
	var white := Color("#fffaf0")
	for i in range(SEGMENTS):
		var a: float = TAU * float(i) / float(SEGMENTS)
		var b: float = TAU * float(i+1) / float(SEGMENTS)
		_band(st,RADIUS-HALF_WIDTH,RADIUS+HALF_WIDTH,a,b,.065,asphalt)
		var edge: Color = Color("#fb6871") if i%8<4 else white
		_band(st,RADIUS+HALF_WIDTH-0.4,RADIUS+HALF_WIDTH+0.55,a,b,.105,edge)
		_band(st,RADIUS-HALF_WIDTH-0.55,RADIUS-HALF_WIDTH+0.4,a,b,.105,edge)
		if i % 8 < 4:
			_band(st,RADIUS-0.25,RADIUS+0.25,a,b,.11,yellow)
		if i < 5:
			# Physically modeled starting grid tiles
			for tile in range(12):
				var r0: float = RADIUS-HALF_WIDTH + float(tile)*(HALF_WIDTH*2.0/12.0)
				var r1: float = r0+HALF_WIDTH*2.0/12.0
				if (tile+i)%2==0:
					_band(st,r0,r1,a,b,.15,white)
	st.generate_normals()
	var road_material := StandardMaterial3D.new()
	road_material.vertex_color_use_as_albedo = true
	road_material.roughness = 0.79
	road_material.cull_mode = BaseMaterial3D.CULL_DISABLED
	var mesh := st.commit()
	var instance := MeshInstance3D.new()
	instance.mesh = mesh
	instance.material_override = road_material
	add_child(instance)

func _build_roadside() -> void:
	for i in range(46):
		var a: float = TAU * float(i) / 46.0
		for side in [-1,1]:
			var offset: float = float(side) * (HALF_WIDTH+1.35)
			var p := road_position(a, offset)
			make_box(self, Vector3(p.x,.70,p.z),Vector3(.20,1.45,.2),Color("#fffbea"))
			make_sphere(self,Vector3(p.x,1.48,p.z),Vector3(.31,.31,.31),
				Color("#ffdf60") if i%2==0 else Color("#ff6baf"),.2,true)
	for i in range(28):
		var a: float = TAU * (float(i)+0.4)/28.0
		var p := road_position(a,HALF_WIDTH+7.8)
		var s: float = 0.82+float(i%4)*0.10
		_make_tree(p,s)

func _make_tree(p: Vector3, s: float = 1.0) -> void:
	make_cylinder(self,Vector3(p.x,1.95*s,p.z),.24*s,3.8*s,Color("#a97b4e"),7)
	make_sphere(self,Vector3(p.x,4.2*s,p.z),Vector3(1.58*s,2.25*s,1.38*s),Color("#48bc6b"))
	make_sphere(self,Vector3(p.x+0.90*s,4.4*s,p.z),Vector3(1.24*s,1.42*s,1.04*s),Color("#8be883"))
	make_sphere(self,Vector3(p.x-0.62*s,5.0*s,p.z),Vector3(1.03*s,1.20*s,.98*s),Color("#66d677"))

func _build_city() -> void:
	for i in range(14):
		var a: float = PI*0.12 + float(i)*PI*.72/14.0
		var p := road_position(a,HALF_WIDTH+12+float(i%2)*7.0)
		var h: float = 7.0 + float((i*11)%9)
		var color: Color = [Color("#ffb74c"),Color("#ff8dbb"),Color("#71b1ff"),Color("#c5ee68")][i%4]
		make_box(self,Vector3(p.x,h/2.0,p.z),Vector3(6.8,h,6.8),color)
		make_box(self,Vector3(p.x,h+.30,p.z),Vector3(7.3,.65,7.3),Color("#fff5d6"))
		for floor_idx in range(1,3):
			make_box(self,Vector3(p.x,h*float(floor_idx)/3.0,p.z-3.53),Vector3(4.2,.65,.11),Color("#f6fcff"),.15,true)
	# Little fairground towers create distinct skyline.
	for i in range(4):
		var p := Vector3(-49+float(i)*10.0,0,-46)
		make_cylinder(self,Vector3(p.x,4.1,p.z),1.2,8.2,Color("#c6d5f7"),8)
		make_box(self,Vector3(p.x,8.5,p.z),Vector3(4,1.5,4),Color("#f584c2"))
		make_sphere(self,Vector3(p.x,10.5,p.z),Vector3(2.0,2.6,2.0),Color("#ffdc55"))

func _build_beach() -> void:
	for i in range(12):
		var a: float = PI*.84+float(i)*PI*.50/12.0
		var p := road_position(a,HALF_WIDTH+12.0+float(i%2)*5.0)
		make_cylinder(self,Vector3(p.x,3.1,p.z),.33,6.3,Color("#b78b60"),7)
		make_sphere(self,Vector3(p.x,6.45,p.z),Vector3(3.4,.47,1.8),Color("#49b76d"))
		make_sphere(self,Vector3(p.x+1.45,6.3,p.z),Vector3(2.0,.42,2.9),Color("#56d983"))
		make_sphere(self,Vector3(p.x-1.3,6.40,p.z),Vector3(1.8,.50,2.8),Color("#41c978"))
	for i in range(4):
		var x: float = 102 + float(i)*8.0
		make_sphere(self,Vector3(x,.9,-15+float(i)*16),Vector3(2.4,.65,1.6),Color("#ffeac0"))
		make_box(self,Vector3(x,2.6,-15+float(i)*16),Vector3(.18,3.1,.18),Color("#fff"))
		make_sphere(self,Vector3(x,4.1,-15+float(i)*16),Vector3(2.5,.28,2.3),Color("#fa7a9d"))

func _build_candy() -> void:
	for i in range(14):
		var a: float = PI*1.48 + float(i)*PI*.43/14.0
		var p := road_position(a,HALF_WIDTH+11.0+float(i%3)*4.0)
		make_cylinder(self,Vector3(p.x,2.5,p.z),.20,5.0,Color("#f9f4fb"),8)
		var col: Color = [Color("#ff71ac"),Color("#b88bff"),Color("#fce15f")][i%3]
		make_sphere(self,Vector3(p.x,5.3,p.z),Vector3(1.45,1.52,.55),col,.2)
		make_sphere(self,Vector3(p.x+.38,5.63,p.z-.46),Vector3(.38,.36,.18),Color("#fff7df"),.3)
	for i in range(9):
		var a: float = PI*1.51 + float(i)*PI*.42/9.0
		var p := road_position(a,HALF_WIDTH+23.0)
		make_sphere(self,Vector3(p.x,2.45,p.z),Vector3(3.5,2.25,3.4),Color("#ffb6d6"))
		make_sphere(self,Vector3(p.x,4.15,p.z),Vector3(3.6,.55,3.5),Color("#fff3d9"))

func _build_dino() -> void:
	for i in range(7):
		var a: float = PI*1.98+float(i)*PI*.38/7.0
		var p := road_position(a,HALF_WIDTH+17.0)
		make_sphere(self,Vector3(p.x,2.6,p.z),Vector3(4.0,2.5,2.8),Color("#54c88b"))
		make_cylinder(self,Vector3(p.x+2.4,5.4,p.z),.58,4.8,Color("#54c88b"),9)
		make_sphere(self,Vector3(p.x+2.4,8.1,p.z),Vector3(1.15,1.14,.97),Color("#73e6a1"))
		make_sphere(self,Vector3(p.x+2.1,8.3,p.z-.78),Vector3(.13,.15,.08),Color("#fff8ef"))
		make_sphere(self,Vector3(p.x+2.1,8.3,p.z-.87),Vector3(.055,.07,.04),Color("#273c5f"))
		for k in range(3):
			make_sphere(self,Vector3(p.x-3.4+float(k)*1.1,3.4,p.z),Vector3(.8,.7,.8),Color("#b2f16b"))
	# distant low-poly volcano
	var cone := CylinderMesh.new()
	cone.top_radius = 3.0
	cone.bottom_radius = 17.0
	cone.height = 27.0
	cone.radial_segments = 9
	var mi := MeshInstance3D.new()
	mi.mesh = cone
	mi.material_override = material(Color("#8e957b"))
	mi.position = Vector3(142,12,-80)
	add_child(mi)
	make_cylinder(self,Vector3(142,27,-80),2.7,2.6,Color("#fc9860"))

func _build_ferris_wheel() -> void:
	var center := Vector3(-108,16,-35)
	var wheel_group := Node3D.new()
	wheel_group.position = center
	add_child(wheel_group)
	make_box(wheel_group,Vector3(-4,-8,0),Vector3(.5,17,.6),Color("#f8f7ee"))
	make_box(wheel_group,Vector3(4,-8,0),Vector3(.5,17,.6),Color("#f8f7ee"))
	make_sphere(wheel_group,Vector3.ZERO,Vector3(1.4,1.4,1.1),Color("#ffe364"),.18,true)
	for i in range(20):
		var a: float = TAU*float(i)/20.0
		var b: float = TAU*float(i+1)/20.0
		var p := Vector3(cos(a)*12.0,sin(a)*12.0,0)
		var q := Vector3(cos(b)*12.0,sin(b)*12.0,0)
		var bar := make_box(wheel_group,(p+q)*.5,Vector3(.45,p.distance_to(q),.40),Color("#ffb4d0"))
		bar.rotation.z = -a - PI/20.0
		var spoke := make_box(wheel_group,p*.5,Vector3(.21,12.0,.21),Color("#fcfaf5"))
		spoke.rotation.z = -a - PI/2.0
		if i%3==0:
			make_sphere(wheel_group,p,Vector3(1.55,.96,1.1),[Color("#ffe15c"),Color("#70dafe"),Color("#f887be")][i%3])
	make_cylinder(self,Vector3(-108,1.3,-35),5.0,.5,Color("#f9d0fa"),18)

func _build_finish_gate() -> void:
	var base := road_position(0)
	var gate := Node3D.new()
	gate.position = base
	gate.rotation.y = 0.0
	add_child(gate)
	for side in [-1,1]:
		make_box(gate,Vector3(float(side)*11.0,5.3,0),Vector3(1.10,10.6,1.0),Color("#fff9e9"))
		make_box(gate,Vector3(float(side)*11.0,9.1,0),Vector3(1.35,.85,1.2),Color("#ff72ae"))
	make_box(gate,Vector3(0,10.7,0),Vector3(23.0,1.8,1.2),Color("#fffdf0"))
	for j in range(22):
		make_box(gate,Vector3(-10.5+float(j),10.4,-.67),Vector3(.93,.75,.08),Color("#25355d") if j%2==0 else Color("#ffffff"))
	make_sphere(gate,Vector3(0,12.1,0),Vector3(1.55,1.6,.47),Color("#ffdd42"),.17,true)
	# Gate stays open for racers; signs are suspended overhead.

func _build_clouds() -> void:
	for i in range(14):
		var a: float = TAU*float(i)/14.0
		var p := road_position(a,28.0+float(i%3)*13.0)
		var h: float = 18.0+float(i%3)*6.0
		make_sphere(self,Vector3(p.x,h,p.z),Vector3(5.6,2.0,2.7),Color("#f7fcff"),.9)
		make_sphere(self,Vector3(p.x+2.4,h+1.1,p.z),Vector3(3.1,2.1,2.7),Color("#ffffff"),.9)
