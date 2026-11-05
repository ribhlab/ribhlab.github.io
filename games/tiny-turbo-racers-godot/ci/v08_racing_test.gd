extends SceneTree
## v0.8 e2e: import 7 actual 3D tree GLBs + CC0 recorded WAVs;
## verify three unique road splines, 4 race-mode goals, checkpoints and replay.
func _initialize() -> void:
	call_deferred("_verify")

func _die(message: String,code: int) -> void:
	push_error("TRACKS_AUDIO_RACING_QA_FAILED: "+message)
	quit(code)

func _simulate_to_finish(game: Node3D,limit: int=4900) -> bool:
	game.held_accel=true
	for step in range(limit):
		game._physics_process(.033)
		if game.state=="finished":
			return true
	return false

func _verify() -> void:
	var game=load("res://scenes/main.tscn").instantiate()
	root.add_child(game)
	var lengths: Array[float] = []
	for map_id in range(3):
		game.track_index=map_id
		game._rebuild_world_for_track()
		if game.world.circuit_variant!=map_id:
			_die("Different track was not loaded: "+str(map_id),61)
			return
		var meters:float=game.world.track_length
		if meters<700.0:
			_die("Track physically too short, meters="+str(meters),62)
			return
		for other in lengths:
			if absf(meters-other)<10.0:
				_die("Track layout has near-identical length: "+str(meters),63)
				return
		lengths.append(meters)
		var nature=game.world.get_node_or_null("ImportedRealTreeScenery")
		if nature==null or nature.tree_count<25 or nature.loaded_variants!=7:
			_die("Missing 7 licensed real 3D tree meshes on track "+str(map_id),64)
			return
		if not game.audio.using_recorded or game.audio.recorded_engines.size()!=6:
			_die("Six real recorded CC0 engine WAV samples not being played",65)
			return
		print("TRACK_REAL_TREES_AND_AUDIO_PASS ",map_id," length=",meters,
			" trees=",nature.tree_count," samples=",game.audio.recorded_engines.size())
	if not (lengths[0]!=lengths[1] and lengths[1]!=lengths[2]):
		_die("Distinct spline geometry missing",66)
		return

	# Sprint goes from start to its actual 83% route finish, not 3 laps.
	game.track_index=1
	game.race_mode=1
	game._start_race()
	if not is_equal_approx(game.race_target,.83*TAU) or game.checkpoints_total!=6:
		_die("Sprint route target/checkpoints are wrong",67)
		return
	if not _simulate_to_finish(game):
		_die("Sprint not finishable",68)
		return
	if game.checkpoints_passed!=game.checkpoints_total:
		_die("Sprint checkpoints not crossed",69)
		return
	print("SPRINT_MODE_PASS seconds=",game.race_seconds)

	# Time trial is solo racing with a saved personal best.
	game.race_mode=2
	game.track_index=2
	game._start_race()
	for r in game.rivals:
		if r["node"].visible:
			_die("Time Trial has visible opponent",70)
			return
	if not _simulate_to_finish(game):
		_die("Time trial not finishable",71)
		return
	if game.personal_best<=0.0:
		_die("Time trial didn't record best lap",72)
		return
	print("TIME_TRIAL_MODE_PASS best=",game.personal_best)

	# Drift is a separate 1-lap finish with score target and result screen.
	game.race_mode=3
	game._start_race()
	game.held_drift=true
	game.held_right=true
	if not _simulate_to_finish(game):
		_die("Drift challenge not finishable",73)
		return
	if game.drift_points<1 or game.finish_stats.text.is_empty():
		_die("Drift challenge didn't score or show results",74)
		return
	game._start_race()
	if game.checkpoints_passed!=0 or game.drift_points!=0:
		_die("Replay state didn't reset",75)
		return
	print("TINY_TURBO_V08_TRACKS_TREES_AUDIO_RACES_PASS length=",lengths)
	game.queue_free()
	quit(0)
