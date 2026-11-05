extends SceneTree
## v0.7 regression: acceleration, real brake, steering traction, drift, nitro,
## three/four independent touchscreen pointers, pause and replay.
const Dynamics = preload("res://scripts/vehicle_dynamics.gd")
const Touch = preload("res://scripts/touch_controls.gd")
const GameScene = preload("res://scenes/main.tscn")
func _initialize() -> void:
	call_deferred("_run_tests")

func _fail(message: String, code: int) -> void:
	push_error("HANDLING_QA_FAIL: "+message)
	quit(code)

func _run_tests() -> void:
	var dynamics = Dynamics.new()
	for i in range(240):
		dynamics.simulate(1.0/60.0,0.0,false)
	var cruising: float = dynamics.velocity
	if cruising < 15.0 or cruising > 40.0:
		_fail("Bad driving acceleration; 4s speed="+str(cruising),32)
		return
	for i in range(170):
		dynamics.simulate(1.0/60.0,0.0,false,false,true)
	if dynamics.velocity > cruising*.45:
		_fail("Brake failed: before="+str(cruising)+" after="+str(dynamics.velocity),33)
		return
	dynamics.reset()
	for i in range(220):
		dynamics.simulate(1.0/60.0,0.0,false)
	var normal_slip: float = 0.0
	for i in range(25):
		var s: Dictionary=dynamics.simulate(1.0/60.0,1.0,false)
		normal_slip=maxf(normal_slip,float(s["slip"]))
	var plain_drift: float = dynamics.drift_intensity
	dynamics.reset()
	for i in range(220):
		dynamics.simulate(1.0/60.0,0.0,false)
	var slide:float=0.0
	for i in range(25):
		var s:Dictionary=dynamics.simulate(1.0/60.0,1.0,false,false,false,true)
		slide=maxf(slide,float(s["slip"]))
	if slide<.35 or slide<=plain_drift:
		_fail("Handbrake grip did not induce extra slide: handbrake="+str(slide)+" normal="+str(plain_drift),34)
		return
	var d= Dynamics.new()
	for i in range(160):
		d.simulate(1.0/60.0,0.0,true)
	var boosted:float=d.velocity
	if boosted<=cruising*.8:
		_fail("Nitro not accelerating strongly: "+str(boosted),35)
		return

	var touch=Touch.new()
	touch.configure(Rect2(0,0,90,90),Rect2(100,0,90,90),
		Rect2(200,0,90,90),Rect2(300,0,90,90),Rect2(400,0,90,90))
	for id in range(5):
		var e:=InputEventScreenTouch.new()
		e.index=id
		e.pressed=true
		e.position=Vector2(float(id)*100.0+20,20)
		touch.handle(e)
	if touch.pointer_count()!=5 or not (touch.held("left") and touch.held("right")
			and touch.held("brake") and touch.held("drift") and touch.held("nitro")):
		_fail("Five simultaneous touch zones not independent",36)
		return
	var up:=InputEventScreenTouch.new()
	up.index=2
	up.position=Vector2(220,20)
	up.pressed=false
	touch.handle(up)
	if touch.held("brake") or not (touch.held("drift") and touch.held("nitro")):
		_fail("Releasing one finger erroneously cleared other presses",37)
		return

	var game = GameScene.instantiate()
	root.add_child(game)
	if game.state!="menu":
		_fail("Menu not initialized",38)
		return
	game._open_garage()
	game._select_brand(3)
	if game.state!="garage" or game.selected_car!=3:
		_fail("Branded garage selection not retained",39)
		return
	game._start_race()
	for i in range(175):
		game._physics_process(.033)
	if game.state!="racing":
		_fail("Countdown did not transition to racing",40)
		return
	for i in range(110):
		game._physics_process(.033)
	var before:float=game.speed
	game.held_brake=true
	for i in range(60):
		game._physics_process(.033)
	if game.speed>=before or not game._brake_input():
		_fail("Integrated brake did not reduce racing speed",41)
		return
	game.held_brake=false
	game._notification(2015)
	if game.state!="paused":
		_fail("Android background did not pause live race",42)
		return
	game._resume_race()
	if game.state!="racing":
		_fail("Could not resume",43)
		return
	game._finish_race()
	if game.state!="finished":
		_fail("Finish overlay missing",44)
		return
	game._start_race()
	if game.state!="countdown" or game.drift_points!=0:
		_fail("Replay did not reset score and state",45)
		return
	print("TINY_TURBO_HANDLING_TOUCH_REPLAY_PASS", " accel=",cruising,
		" boost=",boosted," slide=",slide," pointers=5")
	game.queue_free()
	quit(0)
