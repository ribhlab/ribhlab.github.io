extends Node3D
## Tiny Turbo Racers 3D: self-contained, native Godot arcade racing vertical slice.
## Race a three-lap toy island circuit with chase camera, AI, stars and boost.
const WorldBuilder = preload("res://scripts/real_track.gd")
const CarVisual = preload("res://scripts/real_car.gd")
const ArcadeAudio = preload("res://scripts/arcade_audio.gd")
const VehicleDynamics = preload("res://scripts/vehicle_dynamics.gd")
const BrandCatalog = preload("res://scripts/brand_catalog.gd")
const MAX_LAPS: int = 3
const TRACK_RADIUS: float = 84.0
const CAR_COLORS: Array[Color] = [
	Color("#fa4155"), Color("#348bf3"), Color("#ffce42"),
	Color("#40d384"), Color("#ae73ff"), Color("#ff87bf")
]

var world
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
var countdown: float = 3.75
var race_seconds: float = 0.0
var player_stars: int = 0
var total_stars: int = 0
var selected_paint: int = 0
var selected_car: int = 0
var garage_credit_label: Label
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
var credits_overlay: Control
var finish_overlay: Control
var finish_title: Label
var finish_stats: Label
var garage_car_label: Label
var elapsed: float = 0.0
var collision_lock: float = 0.0
var last_lap: int = 1

func _ready() -> void:
	_load_progress()
	_setup_world()
	_setup_rivals()
	_setup_pickups()
	_setup_audio()
	_setup_ui()
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
		car.set_model_file(str(BrandCatalog.get_car((i+selected_car+1)%BrandCatalog.CARS.size())["file"]))
		car.configure(CAR_COLORS[i+1],i+1)
		car.name = "Rival" + str(i+1)
		add_child(car)
		rivals.append({
			"node": car,
			"progress": .03*float(i+1),
			"speed": 28.5 + float(i)*2.45,
			"lane": [-5.1,0.0,5.15][i]
		})

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

func _style(bg: Color, stroke: Color = Color("#f7faff"), radius: int = 23, border: int = 4) -> StyleBoxFlat:
	var sty := StyleBoxFlat.new()
	sty.bg_color = bg
	sty.border_color = stroke
	sty.set_border_width_all(border)
	sty.set_corner_radius_all(radius)
	sty.shadow_color = Color(0,.20,.48,.25)
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
	_panel(ui_root,Rect2(13,10,570,68),Color("#247fd9e9"))
	top_hud = Control.new()
	top_hud.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	ui_root.add_child(top_hud)
	lap_label = _label(top_hud,"LAP 1 / 3",Rect2(25,16,160,52),24)
	position_label = _label(top_hud,"4th",Rect2(202,16,120,52),27,Color("#ffe36e"))
	stars_label = _label(top_hud,"STARS 0",Rect2(340,16,220,52),23,Color("#fff0a7"))
	_panel(top_hud,Rect2(976,10,290,68),Color("#1b6dccdf"))
	speed_label = _label(top_hud,"0 km/h",Rect2(981,14,274,55),30,Color("#fff2a2"))
	_label(top_hud,"RIBHLAB GT CUP",Rect2(565,14,317,56),22)
	_button(top_hud,"II",Rect2(897,16,75,55),Color("#2789e2"),func(): _pause_race())
	_panel(ui_root,Rect2(439,677,400,28),Color("#167cbeae"))
	boost_label = _label(ui_root,"TURBO READY",Rect2(454,675,370,31),18,Color("#ffffff"))
	
	var left := _button(ui_root,"◀",Rect2(28,573,122,117),Color("#247ce6"),func(): pass)
	var right := _button(ui_root,"▶",Rect2(171,573,122,117),Color("#247ce6"),func(): pass)
	left.button_down.connect(func(): held_left = true)
	left.button_up.connect(func(): held_left = false)
	right.button_down.connect(func(): held_right = true)
	right.button_up.connect(func(): held_right = false)
	var turbo := _button(ui_root,"⚡ TURBO",Rect2(1033,574,210,113),Color("#f9a924"),func(): _activate_boost())
	turbo.add_theme_font_size_override("font_size",27)
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
	_panel(menu_overlay,Rect2(354,83,574,565),Color("#2f83e9f1"),Color("#dffaff"))
	_label(menu_overlay,"TINY TURBO",Rect2(377,113,529,83),57,Color("#fff6c6"))
	_label(menu_overlay,"RACERS 3D",Rect2(377,188,529,80),56,Color("#ffe05e"))
	_label(menu_overlay,"Real sports cars • RibhLab Grand Prix Circuit",Rect2(390,288,500,44),22)
	_button(menu_overlay,"🏁 START RACE",Rect2(465,360,351,78),Color("#36cf54"),func(): _start_race())
	_button(menu_overlay,"🚗 GARAGE",Rect2(465,462,351,72),Color("#20a8e5"),func(): _open_garage())
	_label(menu_overlay,"ARROWS or A/D • SPACE = TURBO",Rect2(400,563,477,40),19,Color("#dfffff"))

	garage_overlay = _overlay()
	_panel(garage_overlay,Rect2(313,108,650,505),Color("#1e80cde9"))
	_label(garage_overlay,"REAL CAR GARAGE",Rect2(359,134,566,64),43,Color("#ffe36c"))
	garage_car_label = _label(garage_overlay,"SELECT A 3D SPORTS CAR",Rect2(350,209,580,51),29)
	garage_credit_label = _label(garage_overlay,"3D art licensed CC BY • manufacturers not affiliated",Rect2(347,257,590,30),15)
	for i in range(BrandCatalog.CARS.size()):
		var brand_index: int = i
		var car_info: Dictionary = BrandCatalog.get_car(i)
		var x: float = 348.0+float(i%3)*210.0
		var y: float = 302.0+float(i/3)*70.0
		var entry: Button = _button(garage_overlay,str(car_info["name"]),Rect2(x,y,195,59),
			CAR_COLORS[i],func(): _select_brand(brand_index))
		entry.add_theme_font_size_override("font_size",16)
		entry.disabled = not BrandCatalog.available(i)
	_label(garage_overlay,"Each car keeps its source-model paint and details.",Rect2(347,480,590,35),19)
	_label(garage_overlay,"Independent prototype • not officially endorsed.",Rect2(347,515,590,30),17,Color("#fff2ad"))
	_button(garage_overlay,"▶ RACE!",Rect2(501,554,288,52),Color("#42ce54"),func(): _start_race())
	_button(garage_overlay,"BACK",Rect2(333,121,110,52),Color("#348ae3"),func(): _go_menu())
	_button(garage_overlay,"CREDITS",Rect2(824,123,122,48),Color("#317ce0"),func(): _open_credits())

	credits_overlay = _overlay()
	_panel(credits_overlay,Rect2(175,63,929,612),Color("#1a477feF"))
	_label(credits_overlay,"MODEL ARTISTS & LICENSING",Rect2(241,90,810,75),40,Color("#fff2ac"))
	var text_area := RichTextLabel.new()
	text_area.position = Vector2(231,177)
	text_area.size = Vector2(817,407)
	text_area.add_theme_color_override("default_color",Color.WHITE)
	text_area.add_theme_font_size_override("normal_font_size",19)
	text_area.scroll_active = true
	text_area.bbcode_enabled = false
	var artist_text: String = "DEVELOPMENT SHOWCASE ONLY — NOT AN OFFICIAL AUTOMAKER GAME\n\n"
	for i in range(BrandCatalog.CARS.size()):
		var info: Dictionary = BrandCatalog.get_car(i)
		artist_text += "%s — 3D art: %s — CC BY 4.0\n%s\n\n" % [str(info["name"]),str(info["artist"]),str(info["source"])]
	artist_text += "Model licenses: https://creativecommons.org/licenses/by/4.0/\n"
	artist_text += "The mesh copyright license is NOT a manufacturer logo/trademark license.\n"
	artist_text += "Before commercial release, review manufacturer rights and store policy."
	text_area.text = artist_text
	credits_overlay.add_child(text_area)
	_button(credits_overlay,"BACK TO GARAGE",Rect2(467,598,346,60),Color("#1e9ade"),
		func(): _return_garage())


	pause_overlay = _overlay()
	_panel(pause_overlay,Rect2(396,155,490,401),Color("#217bc6f4"))
	_label(pause_overlay,"PIT STOP!",Rect2(424,190,427,79),55,Color("#ffe878"))
	_button(pause_overlay,"▶ RESUME",Rect2(494,312,295,72),Color("#38c95b"),func(): _resume_race())
	_button(pause_overlay,"⌂ MAIN MENU",Rect2(494,416,295,71),Color("#2691e5"),func(): _go_menu())

	finish_overlay = _overlay()
	_panel(finish_overlay,Rect2(368,112,545,501),Color("#2474d5f6"))
	finish_title = _label(finish_overlay,"SUPER STAR RACER!",Rect2(390,150,500,90),44,Color("#ffe66a"))
	finish_stats = _label(finish_overlay,"",Rect2(401,269,490,113),29)
	_button(finish_overlay,"▶ RACE AGAIN",Rect2(453,417,371,74),Color("#37ce59"),func(): _start_race())
	_button(finish_overlay,"⌂ HOME",Rect2(483,512,314,63),Color("#2ca4e8"),func(): _go_menu())
	world_label = _label(ui_root,"RIBHLAB INTERNATIONAL RACEWAY",Rect2(425,82,430,45),18)
	world_label.visible = false

func _apply_ui() -> void:
	menu_overlay.visible = state == "menu"
	garage_overlay.visible = state == "garage"
	credits_overlay.visible = state == "credits"
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
	audio.stop_engines()
	_apply_ui()

func _open_credits() -> void:
	state = "credits"
	audio.cue("click")
	_apply_ui()

func _return_garage() -> void:
	state = "garage"
	audio.cue("click")
	_apply_ui()

func _open_garage() -> void:
	state = "garage"
	garage_car_label.text = str(BrandCatalog.get_car(selected_car)["name"])
	garage_credit_label.text = "3D: "+str(BrandCatalog.get_car(selected_car)["artist"])+" • CC BY • not official"
	audio.cue("click")
	_apply_ui()


func _select_brand(index: int) -> void:
	if not BrandCatalog.available(index):
		return
	selected_car = clampi(index,0,BrandCatalog.CARS.size()-1)
	var info: Dictionary = BrandCatalog.get_car(selected_car)
	if is_instance_valid(player):
		remove_child(player)
		player.queue_free()
	player = CarVisual.new()
	player.set_model_file(str(info["file"]))
	player.configure(CAR_COLORS[selected_paint],0)
	player.name = "SelectedLicensedModel"
	add_child(player)
	_place_car()
	garage_car_label.text = str(info["name"])
	garage_credit_label.text = "3D: "+str(info["artist"])+" • CC BY 4.0 • not official"
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
	if state != "racing" or boost_cooldown > 0.0:
		return
	boost_remaining = 2.8
	boost_cooldown = 8.0
	audio.cue("boost")

func _unhandled_key_input(event: InputEvent) -> void:
	if not event is InputEventKey or not event.pressed or event.echo:
		return
	match event.keycode:
		KEY_SPACE:
			_activate_boost()
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
	var steer: float = 0.0
	if held_left or Input.is_key_pressed(KEY_LEFT) or Input.is_key_pressed(KEY_A):
		steer -= 1.0
	if held_right or Input.is_key_pressed(KEY_RIGHT) or Input.is_key_pressed(KEY_D):
		steer += 1.0
	var physics: Dictionary = handling.simulate(delta, steer, boost, absf(lane_offset)>7.1)
	speed = float(physics["speed"])
	lane_offset = clampf(lane_offset+float(physics["lateral_velocity"])*delta,-7.5,7.5)
	if float(physics["slip"])>.45 and race_seconds-last_skid_sound>2.1:
		audio.cue("skid")
		last_skid_sound = race_seconds
	progress += speed*delta/world.road_meters_per_radian()
	var new_lap: int = mini(MAX_LAPS,int(progress/TAU)+1)
	if new_lap > last_lap:
		last_lap = new_lap
		audio.cue("lap")
	_check_pickups()
	_check_collisions()
	audio.set_motor_speed(speed/59.0,boost)
	if progress>=float(MAX_LAPS)*TAU:
		_finish_race()

func _animate_cars(delta: float) -> void:
	_place_car()
	var steering: float = 0.0
	if held_left or Input.is_key_pressed(KEY_LEFT) or Input.is_key_pressed(KEY_A):
		steering -= 1.0
	if held_right or Input.is_key_pressed(KEY_RIGHT) or Input.is_key_pressed(KEY_D):
		steering += 1.0
	player.animate_car(delta,speed,steering,boost_remaining>0.0)
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
	var eye: Vector3 = player.global_position - tangent*9.5 + Vector3(0,4.7,0)
	var look: Vector3 = player.global_position + tangent*13.0 + Vector3(0,1.30,0)
	if state == "menu" or state == "garage":
		var spin: float = elapsed*.27
		eye = player.global_position + Vector3(cos(spin)*10.0,5.1,sin(spin)*10.0)
		look = player.global_position + Vector3(0,1.10,0)
	camera.global_position = camera.global_position.lerp(eye,clampf(delta*3.8,0.0,1.0))
	camera.look_at(look,Vector3.UP)
	var target_fov: float = 76.0 if boost_remaining>0.0 and state=="racing" else 61.0
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
	boost_label.text = "⚡ TURBO " + ("READY!" if boost_cooldown<=0.0 else str(ceili(boost_cooldown))+"s")

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
	finish_title.text = "🏆 CHAMPION!" if rank==1 else "⭐ GREAT RACING!"
	finish_stats.text = ["1st","2nd","3rd","4th"][rank-1] + " PLACE  •  3 LAPS\n" + str(player_stars) + " STARS + "+str(bonus)+" BONUS\nTOTAL: "+str(total_stars)+" STARS"
	_apply_ui()

func _load_progress() -> void:
	var cfg := ConfigFile.new()
	if cfg.load("user://tiny-turbo-save.cfg")==OK:
		total_stars = int(cfg.get_value("player","stars",0))
		selected_paint = clampi(int(cfg.get_value("player","paint",0)),0,CAR_COLORS.size()-1)
		selected_car = clampi(int(cfg.get_value("player","brand",0)),0,BrandCatalog.CARS.size()-1)

func _save_progress() -> void:
	var cfg := ConfigFile.new()
	cfg.set_value("player","stars",total_stars)
	cfg.set_value("player","paint",selected_paint)
	cfg.set_value("player","brand",selected_car)
	cfg.save("user://tiny-turbo-save.cfg")
