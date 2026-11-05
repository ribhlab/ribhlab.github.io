extends Node3D
## Tiny Turbo Racers 3D: self-contained, native Godot arcade racing vertical slice.
## Race a three-lap toy island circuit with chase camera, AI, stars and boost.
const WorldBuilder = preload("res://scripts/street_track.gd")
const CarVisual = preload("res://scripts/real_car.gd")
const ArcadeAudio = preload("res://scripts/arcade_audio.gd")
const VehicleDynamics = preload("res://scripts/vehicle_dynamics.gd")
const TrafficSystem = preload("res://scripts/traffic_system.gd")
const TouchControls = preload("res://scripts/touch_controls.gd")
const BrandCatalog = preload("res://scripts/brand_catalog.gd")
const MAX_LAPS: int = 3
const TRACK_RADIUS: float = 84.0
const CAR_COLORS: Array[Color] = [
	Color("#fa4155"), Color("#348bf3"), Color("#ffce42"),
	Color("#40d384"), Color("#ae73ff"), Color("#ff87bf")
]

var world
var traffic
var player
var camera: Camera3D
var audio
var rivals: Array = []
var pickups: Array = []
var state: String = "menu"
var progress: float = 0.0
var lane_offset: float = 0.0
var speed: float = 0.0
var handling = VehicleDynamics.new()
var last_skid_sound: float = 0.0
var boost_remaining: float = 0.0
var boost_cooldown: float = 0.0
var nitro_charge: float = 100.0
var drift_points: int = 0
var near_miss_count: int = 0
var held_drift: bool = false
var held_brake: bool = false
var touch = TouchControls.new()
var collision_feedback: float = 0.0
var countdown: float = 3.75
var race_seconds: float = 0.0
var player_stars: int = 0
var total_stars: int = 0
var selected_paint: int = 0
var selected_car: int = 0
var quality_level: int = 1
var quality_label: Label
var settings_overlay: Control
var garage_credit_label: Label
var credits_overlay: Control
var held_left: bool = false
var held_right: bool = false
var ui_root: Control
var top_hud: Control
var world_label: Label
var lap_label: Label
var position_label: Label
var stars_label: Label
var speed_label: Label
var boost_label: Label
var big_countdown: Label
var menu_overlay: Control
var pause_overlay: Control
var garage_overlay: Control
var finish_overlay: Control
var finish_title: Label
var finish_stats: Label
var garage_car_label: Label
var elapsed: float = 0.0
var collision_lock: float = 0.0
var last_lap: int = 1
var last_slip: float = 0.0

func _ready() -> void:
	_load_progress()
	_setup_world()
	_setup_rivals()
	_setup_traffic()
	_setup_pickups()
	_setup_audio()
	_setup_ui()
	_apply_quality()
	_place_car()
	_apply_ui()
	set_process(true)
	set_physics_process(true)

func _setup_world() -> void:
	world = WorldBuilder.new()
	world.name = "FourWorldsRaceCircuit"
	add_child(world)
	world.build_world()
	player = CarVisual.new()
	player.set_model_file(str(BrandCatalog.get_car(selected_car)["file"]))
	player.configure(CAR_COLORS[selected_paint], 0)
	player.name = "Speedy"
	add_child(player)
	camera = Camera3D.new()
	camera.name = "ChaseCamera"
	camera.current = true
	camera.fov = 61.0
	camera.near = .08
	camera.far = 400.0
	add_child(camera)
	camera.position = Vector3(0,7,-12)
	camera.look_at(Vector3.ZERO)

func _setup_rivals() -> void:
	for i in range(3):
		var car = CarVisual.new()
		car.set_model_file(str(BrandCatalog.get_car((selected_car+i+1)%BrandCatalog.CARS.size())["file"]))
		car.configure(CAR_COLORS[i+1],i+1)
		car.name = "Rival" + str(i+1)
		add_child(car)
		rivals.append({
			"node": car,
			"progress": .03*float(i+1),
			"speed": 28.5 + float(i)*2.45,
			"lane": [-5.1,0.0,5.15][i]
		})

func _setup_traffic() -> void:
	traffic = TrafficSystem.new()
	traffic.name = "MidnightCityTraffic"
	add_child(traffic)
	traffic.setup(world)

func _setup_pickups() -> void:
	for i in range(25):
		var a: float = .22+float(i)*TAU/25.0
		var offset: float = [-5.3,0.0,5.2][i%3]
		var root := Node3D.new()
		root.position = world.road_position(a,offset)+Vector3(0,2.0,0)
		root.name = "CollectibleStar" + str(i)
		add_child(root)
		var gold := _simple_material(Color("#ffdc49"),true)
		var light := _simple_material(Color("#fff8c5"),true)
		_add_star_box(root,Vector3.ZERO,Vector3(1.08,1.07,.40),gold)
		for spoke in range(5):
			var box := _add_star_box(root,Vector3(0,1.15,0),Vector3(.33,1.38,.35),light)
			box.rotation.z = float(spoke)*TAU/5.0
			box.position = Vector3(sin(float(spoke)*TAU/5.0),cos(float(spoke)*TAU/5.0),0)
		pickups.append({"node":root,"angle":a,"offset":offset,"collected":false})

func _add_star_box(parent: Node3D,p: Vector3,size: Vector3,mat: Material) -> MeshInstance3D:
	var mesh := BoxMesh.new()
	mesh.size = size
	var mi := MeshInstance3D.new()
	mi.mesh = mesh
	mi.material_override = mat
	mi.position = p
	parent.add_child(mi)
	return mi

func _simple_material(color: Color, glow: bool = false) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = color
	m.roughness = .23
	if glow:
		m.emission_enabled = true
		m.emission = color
		m.emission_energy_multiplier = 1.4
	return m

func _setup_audio() -> void:
	audio = ArcadeAudio.new()
	audio.name = "OriginalRaceSound"
	add_child(audio)
	for i in range(rivals.size()):
		audio.attach_rival(rivals[i]["node"],i)

func _style(bg: Color, stroke: Color = Color("#b35dfe"), radius: int = 17, border: int = 2) -> StyleBoxFlat:
	var sty := StyleBoxFlat.new()
	sty.bg_color = bg
	sty.border_color = stroke
	sty.set_border_width_all(border)
	sty.set_corner_radius_all(radius)
	sty.shadow_color = Color(0,.86,.98,.20)
	sty.shadow_size = 6
	return sty

func _label(parent: Control, text: String, rect: Rect2, font_size: int,
		color: Color = Color.WHITE, centered: bool = true) -> Label:
	var lb := Label.new()
	lb.text = text
	lb.position = rect.position
	lb.size = rect.size
	lb.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER if centered else HORIZONTAL_ALIGNMENT_LEFT
	lb.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	lb.add_theme_color_override("font_color",color)
	lb.add_theme_color_override("font_shadow_color",Color("#24568b"))
	lb.add_theme_constant_override("shadow_offset_x",2)
	lb.add_theme_constant_override("shadow_offset_y",3)
	lb.add_theme_font_size_override("font_size",font_size)
	parent.add_child(lb)
	return lb

func _button(parent: Control, text: String, rect: Rect2, bg: Color, pressed: Callable) -> Button:
	var bt := Button.new()
	bt.text = text
	bt.position = rect.position
	bt.size = rect.size
	bt.add_theme_stylebox_override("normal",_style(bg))
	bt.add_theme_stylebox_override("hover",_style(bg.lightened(.16)))
	bt.add_theme_stylebox_override("pressed",_style(bg.darkened(.16)))
	bt.add_theme_stylebox_override("focus",StyleBoxEmpty.new())
	bt.add_theme_color_override("font_color",Color("#ffffff"))
	bt.add_theme_color_override("font_hover_color",Color("#ffffff"))
	bt.add_theme_color_override("font_pressed_color",Color("#ffffff"))
	bt.add_theme_font_size_override("font_size",25)
	bt.pressed.connect(pressed)
	parent.add_child(bt)
	return bt

func _panel(parent: Control, r: Rect2, bg: Color, border: Color = Color.WHITE) -> Panel:
	var p := Panel.new()
	p.position = r.position
	p.size = r.size
	p.add_theme_stylebox_override("panel",_style(bg,border,28,6))
	parent.add_child(p)
	return p

func _overlay() -> Control:
	var c := Control.new()
	c.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	ui_root.add_child(c)
	return c

func _setup_ui() -> void:
	var layer := CanvasLayer.new()
	layer.name = "GameUI"
	add_child(layer)
	ui_root = Control.new()
	ui_root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	layer.add_child(ui_root)
	_panel(ui_root,Rect2(13,10,570,68),Color("#0c1630e9"),Color("#54c5eb"))
	top_hud = Control.new()
	top_hud.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	ui_root.add_child(top_hud)
	lap_label = _label(top_hud,"LAP 1 / 3",Rect2(25,16,160,52),24)
	position_label = _label(top_hud,"4th",Rect2(202,16,120,52),27,Color("#ffe36e"))
	stars_label = _label(top_hud,"STARS 0",Rect2(340,16,220,52),23,Color("#fff0a7"))
	_panel(top_hud,Rect2(976,10,290,68),Color("#0d1936df"),Color("#b665e4"))
	speed_label = _label(top_hud,"0 km/h",Rect2(981,14,274,55),30,Color("#fff2a2"))
	_label(top_hud,"MIDNIGHT RUSH",Rect2(555,14,331,56),22,Color("#81eeff"))
	_button(top_hud,"II",Rect2(897,16,75,55),Color("#3d3d76"),func(): _pause_race())
	_panel(ui_root,Rect2(370,133,540,35),Color("#0e1d3dcf"),Color("#46cbf9"))
	boost_label = _label(ui_root,"NITRO 100% | DRIFT 0",Rect2(381,134,517,32),18,Color("#a3f2ff"))
	
	var left := _button(ui_root,"◀",Rect2(28,573,122,117),Color("#136487"),func(): pass)
	var right := _button(ui_root,"▶",Rect2(171,573,122,117),Color("#136487"),func(): pass)
	left.button_down.connect(func(): held_left = true)
	left.button_up.connect(func(): held_left = false)
	right.button_down.connect(func(): held_right = true)
	right.button_up.connect(func(): held_right = false)
	var brake_btn := _button(ui_root,"BRAKE",Rect2(698,586,154,101),
		Color("#344d69"),func(): pass)
	brake_btn.button_down.connect(func(): held_brake=true)
	brake_btn.button_up.connect(func(): held_brake=false)
	brake_btn.set_meta("race_only",true)
	var drift_btn := _button(ui_root,"DRIFT",Rect2(868,586,150,101),
		Color("#8b3e96"),func(): pass)
	drift_btn.button_down.connect(func(): held_drift=true)
	drift_btn.button_up.connect(func(): held_drift=false)
	drift_btn.set_meta("race_only",true)
	var turbo := _button(ui_root,"NITRO",Rect2(1033,574,210,113),
		Color("#ef4d85"),func(): _activate_boost())
	turbo.add_theme_font_size_override("font_size",27)
	touch.configure(left.get_global_rect(),right.get_global_rect(),
		brake_btn.get_global_rect(),drift_btn.get_global_rect(),turbo.get_global_rect())
	# Race-only controls remain reachable while other overlays block touch.
	top_hud.visible = false
	left.visible = false
	right.visible = false
	turbo.visible = false
	left.set_meta("race_only",true)
	right.set_meta("race_only",true)
	turbo.set_meta("race_only",true)

	big_countdown = _label(ui_root,"3",Rect2(480,230,320,230),116,Color("#ffed6f"))
	big_countdown.visible = false

	menu_overlay = _overlay()
	_panel(menu_overlay,Rect2(354,83,574,565),Color("#0a1125ed"),Color("#6ac3f6"))
	_label(menu_overlay,"MIDNIGHT",Rect2(377,118,529,83),62,Color("#e8f9ff"))
	_label(menu_overlay,"RUSH GT",Rect2(377,193,529,83),68,Color("#fd69b2"))
	_label(menu_overlay,"A street racing experience by RibhLab",Rect2(385,296,510,42),22,Color("#a3d8ff"))
	_button(menu_overlay,"START NIGHT RACE",Rect2(465,359,351,80),Color("#e44588"),func(): _start_race())
	_button(menu_overlay,"TUNE YOUR CAR",Rect2(465,463,351,72),Color("#15698d"),func(): _open_garage())
	_button(menu_overlay,"⚙ SETTINGS",Rect2(465,548,351,52),Color("#284d76"),func(): _open_settings())
	_label(menu_overlay,"A/D STEER | S BRAKE | SHIFT DRIFT | SPACE NITRO",
		Rect2(367,605,543,31),15,Color("#b6dfff"))

	garage_overlay = _overlay()
	_panel(garage_overlay,Rect2(313,108,650,505),Color("#0e1931eb"),Color("#6ccbe9"))
	_label(garage_overlay,"REAL 3D GT GARAGE",Rect2(359,134,566,69),42,Color("#ff84bd"))
	garage_car_label = _label(garage_overlay,"BMW M4 CSL",Rect2(346,209,588,49),27)
	garage_credit_label = _label(garage_overlay,"Models by independent 3D artists • CC BY",Rect2(353,253,573,33),16)
	for i in range(BrandCatalog.CARS.size()):
		var selected_index: int = i
		var info: Dictionary = BrandCatalog.get_car(i)
		var gx: float = 335.0+float(i%3)*208.0
		var gy: float = 298.0+float(i/3)*65.0
		var choice: Button = _button(garage_overlay,str(info["name"]),
			Rect2(gx,gy,198,56),CAR_COLORS[i],func(): _select_brand(selected_index))
		choice.add_theme_font_size_override("font_size",16)
		choice.disabled = not BrandCatalog.available(i)
	_label(garage_overlay,"EXPERIMENTAL PAINT",Rect2(354,431,566,32),17,Color("#cae6ff"))
	for i in range(CAR_COLORS.size()):
		var color_index: int = i
		_button(garage_overlay,"●",Rect2(392+float(i)*82.0,470,72,42),CAR_COLORS[i],
			func(): _select_paint(color_index))
	_button(garage_overlay,"RACE!",Rect2(514,540,256,63),Color("#e94087"),func(): _start_race())
	_button(garage_overlay,"BACK",Rect2(326,119,100,50),Color("#348ae3"),func(): _go_menu())
	_button(garage_overlay,"CREDITS",Rect2(817,119,136,50),Color("#35649e"),func(): _open_credits())

	credits_overlay = _overlay()
	_panel(credits_overlay,Rect2(164,62,946,612),Color("#121f3af3"),Color("#52cbe1"))
	_label(credits_overlay,"MODEL ARTISTS & LICENSING",Rect2(220,85,841,73),39,Color("#fff2ac"))
	var text_area := RichTextLabel.new()
	text_area.position=Vector2(219,161)
	text_area.size=Vector2(841,434)
	text_area.add_theme_font_size_override("normal_font_size",18)
	text_area.add_theme_color_override("default_color",Color.WHITE)
	var artist_text: String = "DEVELOPMENT PROTOTYPE ONLY. NOT AN OFFICIAL AUTOMAKER GAME.\n\n"
	for i in range(BrandCatalog.CARS.size()):
		var info: Dictionary=BrandCatalog.get_car(i)
		artist_text += "%s — 3D art: %s — CC BY 4.0\n%s\n\n" % [
			str(info["name"]),str(info["artist"]),str(info["source"])]
	artist_text += "Mesh licenses: https://creativecommons.org/licenses/by/4.0/\n"
	artist_text += "Manufacturer trademarks and logos are NOT licensed by this project."
	text_area.text = artist_text
	credits_overlay.add_child(text_area)
	_button(credits_overlay,"BACK TO GARAGE",Rect2(445,602,384,58),
		Color("#267baa"),func(): _return_garage())

	settings_overlay = _overlay()
	_panel(settings_overlay,Rect2(365,135,550,447),Color("#0c1832f2"),Color("#54d5ef"))
	_label(settings_overlay,"GRAPHICS SETTINGS",Rect2(392,163,493,75),39,Color("#8ee9ff"))
	quality_label = _label(settings_overlay,"QUALITY: MEDIUM",Rect2(407,253,465,48),25,Color("#fff1b7"))
	for i in range(3):
		var selected_quality: int = i
		_button(settings_overlay,["LOW","MEDIUM","HIGH"][i],
			Rect2(394.0+float(i)*170.0,333,158,70),
			[Color("#34638a"),Color("#297c95"),Color("#bf4e9a")][i],
			func(): _select_quality(selected_quality))
	_label(settings_overlay,"Low reduces lights, shadows and distant city detail.",
		Rect2(399,420,487,48),17,Color("#c9e7f7"))
	_button(settings_overlay,"BACK",Rect2(503,497,280,59),
		Color("#2c83b6"),func(): _go_menu())

	pause_overlay = _overlay()
	_panel(pause_overlay,Rect2(396,155,490,401),Color("#0c1633f4"),Color("#75d5f2"))
	_label(pause_overlay,"RACE PAUSED",Rect2(424,190,427,79),45,Color("#ffe878"))
	_button(pause_overlay,"▶ RESUME",Rect2(494,312,295,72),Color("#38c95b"),func(): _resume_race())
	_button(pause_overlay,"⌂ MAIN MENU",Rect2(494,416,295,71),Color("#2691e5"),func(): _go_menu())

	finish_overlay = _overlay()
	_panel(finish_overlay,Rect2(368,112,545,501),Color("#0b1834f6"),Color("#fe6db3"))
	finish_title = _label(finish_overlay,"SUPER STAR RACER!",Rect2(390,150,500,90),44,Color("#ffe66a"))
	finish_stats = _label(finish_overlay,"",Rect2(401,269,490,113),29)
	_button(finish_overlay,"▶ RACE AGAIN",Rect2(453,417,371,74),Color("#37ce59"),func(): _start_race())
	_button(finish_overlay,"⌂ HOME",Rect2(483,512,314,63),Color("#2ca4e8"),func(): _go_menu())
	world_label = _label(ui_root,"MIDNIGHT HARBOR • CITY SPRINT",Rect2(425,82,430,45),18,Color("#d4d9ff"))
	world_label.visible = false

func _apply_ui() -> void:
	menu_overlay.visible = state == "menu"
	garage_overlay.visible = state == "garage"
	credits_overlay.visible = state == "credits"
	settings_overlay.visible = state == "settings"
	pause_overlay.visible = state == "paused"
	finish_overlay.visible = state == "finished"
	var active: bool = state == "racing" or state == "countdown"
	top_hud.visible = active
	big_countdown.visible = state == "countdown"
	world_label.visible = active
	for child in ui_root.get_children():
		if child.has_meta("race_only"):
			child.visible = active
	boost_label.visible = active

func _go_menu() -> void:
	state = "menu"
	held_left = false
	held_right = false
	held_drift = false
	held_brake = false
	touch.reset()
	audio.stop_engines()
	_apply_ui()

func _open_settings() -> void:
	state = "settings"
	quality_label.text = "QUALITY: "+["LOW","MEDIUM","HIGH"][quality_level]
	audio.cue("click")
	_apply_ui()

func _select_quality(index: int) -> void:
	quality_level=clampi(index,0,2)
	_apply_quality()
	quality_label.text="QUALITY: "+["LOW","MEDIUM","HIGH"][quality_level]
	audio.cue("click")
	_save_progress()

func _apply_quality() -> void:
	# This controls draw calls/light count, not just text or tint.
	var world_env := world.get_node_or_null("MidnightSkyAndAtmosphere") as WorldEnvironment
	if world_env != null and world_env.environment != null:
		world_env.environment.glow_enabled = quality_level>=1
		world_env.environment.fog_enabled = quality_level>=1
	for node in world.get_children():
		if node is OmniLight3D:
			var light_id: String=str(node.name)
			node.visible = quality_level==2 or (quality_level==1 and (not light_id.ends_with("00") or light_id.ends_with("04"))) or light_id.ends_with("00")
		elif node is DirectionalLight3D:
			(node as DirectionalLight3D).shadow_enabled = quality_level>=1
		elif node is MultiMeshInstance3D:
			if node.name.begins_with("InstancedStreetTrees_"):
				node.visible = quality_level>=1
		elif node.name.begins_with("DowntownTower_"):
			if quality_level==0:
				var parts: PackedStringArray = str(node.name).split("_")
				var num: int=int(parts[parts.size()-1])
				node.visible = (num%3==0)
			else:
				node.visible = true
	# Traffic must remain visible at every quality level: hiding active cars
	# while leaving collision checks enabled causes unfair invisible crashes.
	for car in traffic.vehicles:
		var vehicle: Node3D=car["node"]
		vehicle.visible = true

func _open_garage() -> void:
	state = "garage"
	var info: Dictionary = BrandCatalog.get_car(selected_car)
	garage_car_label.text = str(info["name"])
	garage_credit_label.text = "3D art by "+str(info["artist"])+" • CC BY • unofficial"
	audio.cue("click")
	_apply_ui()

func _open_credits() -> void:
	state = "credits"
	audio.cue("click")
	_apply_ui()

func _return_garage() -> void:
	_open_garage()

func _select_brand(index: int) -> void:
	if not BrandCatalog.available(index):
		return
	selected_car = clampi(index,0,BrandCatalog.CARS.size()-1)
	var info: Dictionary=BrandCatalog.get_car(selected_car)
	if is_instance_valid(player):
		remove_child(player)
		player.queue_free()
	player=CarVisual.new()
	player.set_model_file(str(info["file"]))
	player.configure(CAR_COLORS[selected_paint],0)
	player.name="GTPlayer"
	add_child(player)
	_place_car()
	garage_car_label.text=str(info["name"])
	garage_credit_label.text="3D art by "+str(info["artist"])+" • CC BY • unofficial"
	audio.cue("click")
	_save_progress()

func _select_paint(index: int) -> void:
	selected_paint = clampi(index,0,CAR_COLORS.size()-1)
	player.set_paint(CAR_COLORS[selected_paint])
	garage_car_label.text = str(BrandCatalog.get_car(selected_car)["name"])
	audio.cue("click")
	_save_progress()

func _start_race() -> void:
	audio.stop_engines()
	audio.cue("click")
	state = "countdown"
	progress = 0.0
	speed = 0.0
	handling.reset()
	lane_offset = 0.0
	race_seconds = 0.0
	countdown = 3.8
	boost_remaining = 0.0
	boost_cooldown = 0.0
	nitro_charge = 100.0
	drift_points = 0
	near_miss_count = 0
	held_drift = false
	held_brake = false
	collision_feedback = 0.0
	touch.reset()
	traffic.reset()
	player_stars = 0
	collision_lock = 0.0
	last_lap = 1
	for i in range(rivals.size()):
		rivals[i]["progress"] = .03*float(i+1)
	for item in pickups:
		item["collected"] = false
		item["node"].visible = true
	_place_car()
	_apply_ui()

func _pause_race() -> void:
	if state != "racing":
		return
	state = "paused"
	held_brake = false
	held_drift = false
	touch.reset()
	audio.stop_engines()
	audio.cue("click")
	_apply_ui()

func _resume_race() -> void:
	if state != "paused":
		return
	state = "racing"
	audio.start_engines()
	_apply_ui()

func _activate_boost() -> void:
	if state != "racing" or boost_cooldown > 0.0 or nitro_charge < 35.0:
		return
	nitro_charge -= 35.0
	boost_remaining = 3.0
	boost_cooldown = 3.6
	audio.cue("boost")

func _input(event: InputEvent) -> void:
	if not (event is InputEventScreenTouch or event is InputEventScreenDrag):
		return
	if state != "countdown" and state != "racing":
		return
	var action: String = touch.handle(event)
	if action == "nitro" and state == "racing":
		_activate_boost()
	# Keep each finger's original touch sequence separate from Godot UI Buttons.
	# Mouse callbacks remain enabled for desktop / editor testing.
	get_viewport().set_input_as_handled()

func _notification(what: int) -> void:
	# Godot WM_GO_BACK_REQUEST=1007; app pause=2015; focus out=2018.
	if what == 1007:
		if state == "racing":
			_pause_race()
		elif state in ["paused","garage","finished","settings","credits"]:
			_go_menu()
	elif what == 2015 or what == 2018:
		if state == "racing":
			_pause_race()

func _steer_input() -> float:
	var left_pressed: bool = held_left or touch.held("left") or Input.is_key_pressed(KEY_LEFT) or Input.is_key_pressed(KEY_A)
	var right_pressed: bool = held_right or touch.held("right") or Input.is_key_pressed(KEY_RIGHT) or Input.is_key_pressed(KEY_D)
	return float(int(right_pressed)-int(left_pressed))

func _brake_input() -> bool:
	return held_brake or touch.held("brake") or Input.is_key_pressed(KEY_DOWN) or Input.is_key_pressed(KEY_S)

func _drift_input() -> bool:
	return held_drift or touch.held("drift") or Input.is_key_pressed(KEY_SHIFT)

func _unhandled_key_input(event: InputEvent) -> void:
	if not event is InputEventKey or not event.pressed or event.echo:
		return
	match event.keycode:
		KEY_SPACE:
			_activate_boost()
		KEY_SHIFT:
			held_drift=true
		KEY_ESCAPE:
			if state == "racing":
				_pause_race()
			elif state == "paused":
				_resume_race()
			else:
				_go_menu()
		KEY_ENTER:
			if state == "menu" or state == "finished":
				_start_race()
		KEY_M:
			audio.toggle_sound()

func _physics_process(delta: float) -> void:
	elapsed += delta
	if state == "countdown":
		countdown -= delta
		if countdown >= 0.0:
			var n: int = int(ceil(countdown))
			big_countdown.text = str(n)
			if n != last_lap:
				last_lap = n
				audio.cue("count")
		else:
			big_countdown.text = "GO!"
			if countdown < -0.4:
				state = "racing"
				audio.cue("go")
				audio.start_engines()
				last_lap = 1
				_apply_ui()
	if state == "racing":
		_drive(delta)
	if state == "racing" or state == "countdown" or state == "garage" or state == "menu":
		_animate_cars(delta)
		_animate_pickups(delta)
	_update_camera(delta)
	if state == "racing":
		_update_hud()

func _drive(delta: float) -> void:
	race_seconds += delta
	boost_cooldown = maxf(0.0,boost_cooldown-delta)
	boost_remaining = maxf(0.0,boost_remaining-delta)
	collision_lock = maxf(0.0,collision_lock-delta)
	var boost: bool = boost_remaining > 0.0
	var steer: float = _steer_input()
	var braking: bool = _brake_input()
	var drifting: bool = _drift_input()
	var physics: Dictionary = handling.simulate(delta,steer,boost,
		absf(lane_offset)>7.1,braking,drifting)
	speed = float(physics["speed"])
	lane_offset = clampf(lane_offset+float(physics["lateral_velocity"])*delta,-7.5,7.5)
	last_slip = float(physics["slip"])
	if drifting and absf(steer)>.14 and speed>14.0 and last_slip>.30:
		drift_points += maxi(1,int(speed*delta*(1.0+last_slip*2.8)))
		nitro_charge = minf(100.0,nitro_charge+delta*3.2)
	else:
		nitro_charge = minf(100.0,nitro_charge+delta*.45)
	if handling.drift_intensity>.45 and race_seconds-last_skid_sound>2.1:
		audio.cue("skid")
		last_skid_sound = race_seconds
	progress += speed*delta/world.road_meters_per_radian()
	var new_lap: int = mini(MAX_LAPS,int(progress/TAU)+1)
	if new_lap > last_lap:
		last_lap = new_lap
		audio.cue("lap")
	_check_pickups()
	_check_collisions()
	var traffic_event: Dictionary = traffic.tick(delta,progress,lane_offset,speed)
	if bool(traffic_event["collision"]) and collision_lock<=0.0:
		speed *= .53
		handling.velocity=speed
		collision_feedback = 1.0
		collision_lock=1.15
		audio.cue("skid")
	var misses: int=int(traffic_event["near_misses"])
	if misses>0:
		near_miss_count += misses
		nitro_charge = minf(100.0,nitro_charge+float(misses)*8.0)
	audio.set_motor_speed(speed/72.0,boost)
	if braking and speed>5.0 and last_slip>.25:
		collision_feedback=maxf(collision_feedback,.10)
	if progress>=float(MAX_LAPS)*TAU:
		_finish_race()

func _animate_cars(delta: float) -> void:
	_place_car()
	var steering: float = _steer_input()
	player.animate_car(delta,speed,steering*(1.32 if _drift_input() else 1.0),boost_remaining>0.0)
	for i in range(rivals.size()):
		var car_data: Dictionary = rivals[i]
		if state == "racing":
			car_data["progress"] += (float(car_data["speed"])+sin(elapsed*.7+float(i)*3.0)*3.0)*delta / world.road_meters_per_radian()
		var a: float = float(car_data["progress"])
		var offset: float = float(car_data["lane"])
		var car_node = car_data["node"]
		car_node.position = world.road_position(a,offset) + Vector3(0,.10,0)
		car_node.rotation.y = world.road_yaw(a)
		car_node.animate_car(delta,float(car_data["speed"]),sin(elapsed+float(i))*.3,false)

func _place_car() -> void:
	player.position = world.road_position(progress,lane_offset) + Vector3(0,.10,0)
	player.rotation.y = world.road_yaw(progress)

func _update_camera(delta: float) -> void:
	var a: float = progress
	var tangent: Vector3 = world.road_tangent(a)
	var sideways: Vector3 = Vector3(tangent.z,0.0,-tangent.x)
	var eye: Vector3 = player.global_position - tangent*(9.2+speed*.020) + sideways*handling.steer_angle*.60 + Vector3(0,4.45,0)
	var look: Vector3 = player.global_position + tangent*(13.3+speed*.035) - sideways*handling.steer_angle*1.35 + Vector3(0,1.35,0)
	# Controlled speed shake and drift look-ahead; never obscure road.
	collision_feedback = move_toward(collision_feedback,0.0,delta*2.6)
	eye += sideways*sin(elapsed*36.0)*.21*collision_feedback
	eye += Vector3.UP*cos(elapsed*43.0)*.17*collision_feedback
	if state == "menu" or state == "garage":
		var spin: float = elapsed*.27
		eye = player.global_position + Vector3(cos(spin)*10.0,5.1,sin(spin)*10.0)
		look = player.global_position + Vector3(0,1.10,0)
	camera.global_position = camera.global_position.lerp(eye,clampf(delta*3.8,0.0,1.0))
	camera.look_at(look,Vector3.UP)
	var target_fov: float = 77.0 if boost_remaining>0.0 and state=="racing" else 61.0 + clampf(speed/65.0,0.0,1.0)*6.5
	camera.fov = lerpf(camera.fov,target_fov,clampf(delta*3.0,0.0,1.0))

func _animate_pickups(delta: float) -> void:
	for item in pickups:
		if item["collected"]:
			continue
		var n: Node3D = item["node"]
		n.rotate_y(delta*1.7)
		n.position.y = 2.0 + .32*sin(elapsed*3.5+float(item["angle"])*4.0)

func _check_pickups() -> void:
	var current_angle: float = fposmod(progress,TAU)
	for item in pickups:
		if item["collected"]:
			continue
		var difference: float = absf(wrapf(current_angle-float(item["angle"]),-PI,PI))
		if difference < .055 and absf(lane_offset-float(item["offset"])) < 2.5:
			item["collected"] = true
			item["node"].visible = false
			player_stars += 1
			audio.cue("coin")

func _check_collisions() -> void:
	if collision_lock > 0.0:
		return
	for rival in rivals:
		var delta_angle: float = absf(wrapf(progress-float(rival["progress"]),-PI,PI))
		if delta_angle < .036 and absf(lane_offset-float(rival["lane"])) < 2.0:
			speed *= .65
			handling.velocity = speed
			lane_offset = clampf(lane_offset+(2.0 if lane_offset >= 0.0 else -2.0),-7.5,7.5)
			collision_lock = 1.3
			collision_feedback = 1.0
			audio.cue("skid")
			return

func _race_position() -> int:
	var position: int = 1
	for rival in rivals:
		if float(rival["progress"]) > progress:
			position += 1
	return position

func _update_hud() -> void:
	var lap: int = mini(MAX_LAPS,int(progress/TAU)+1)
	lap_label.text = "LAP " + str(lap) + " / " + str(MAX_LAPS)
	position_label.text = ["1st","2nd","3rd","4th"][_race_position()-1]
	stars_label.text = "★ STARS " + str(player_stars)
	speed_label.text = str(int(speed*3.6))+" km/h"
	boost_label.text = ("NITRO "+str(int(nitro_charge))+"%  |  DRIFT "+str(drift_points)
		+ "  |  NEAR MISS "+str(near_miss_count)+ ("  |  BRAKING" if _brake_input() else ""))

func _finish_race() -> void:
	if state != "racing":
		return
	state = "finished"
	audio.stop_engines()
	audio.cue("win")
	var rank: int = _race_position()
	var bonus: int = maxi(2,5-rank)*4
	total_stars += player_stars + bonus
	_save_progress()
	finish_title.text = "MIDNIGHT CHAMPION" if rank==1 else "FINISH LINE"
	finish_stats.text = (["1st","2nd","3rd","4th"][rank-1]+" PLACE  /  3 LAPS"
		+ "\nDRIFT "+str(drift_points)+"  •  NEAR MISSES "+str(near_miss_count)
		+ "\nSTREET CREDITS "+str(player_stars+bonus))
	_apply_ui()

func _load_progress() -> void:
	var cfg := ConfigFile.new()
	if cfg.load("user://tiny-turbo-save.cfg")==OK:
		total_stars = int(cfg.get_value("player","stars",0))
		selected_paint = clampi(int(cfg.get_value("player","paint",0)),0,CAR_COLORS.size()-1)
		selected_car = clampi(int(cfg.get_value("player","brand",0)),0,BrandCatalog.CARS.size()-1)
		quality_level = clampi(int(cfg.get_value("player","quality",1)),0,2)

func _save_progress() -> void:
	var cfg := ConfigFile.new()
	cfg.set_value("player","stars",total_stars)
	cfg.set_value("player","paint",selected_paint)
	cfg.set_value("player","brand",selected_car)
	cfg.set_value("player","quality",quality_level)
	cfg.save("user://tiny-turbo-save.cfg")
