extends Node
## Entire sound library synthesized at launch; no copyrighted sound samples.
## The local player engine is stereo, rivals use AudioStreamPlayer3D positional audio.

const RATE: int = 22050
var enabled: bool = true
var engine: AudioStreamPlayer
var sfx: Array[AudioStreamPlayer] = []
var tones: Dictionary = {}
var engine_wave: AudioStreamWAV
var sfx_index: int = 0
var rival_sounds: Array[AudioStreamPlayer3D] = []

func _ready() -> void:
	engine_wave = _wave("engine", 0.50, 75.0, true)
	engine = AudioStreamPlayer.new()
	engine.name = "PlayerMotor"
	engine.stream = engine_wave
	engine.volume_db = -18.0
	add_child(engine)
	for i in range(5):
		var p := AudioStreamPlayer.new()
		p.name = "SoundEffect" + str(i)
		add_child(p)
		sfx.append(p)
	tones["count"] = _wave("count", .16, 520.0)
	tones["go"] = _wave("go", .46, 880.0)
	tones["coin"] = _wave("coin", .30, 960.0)
	tones["boost"] = _wave("boost", .58, 185.0)
	tones["lap"] = _wave("lap", .48, 700.0)
	tones["win"] = _wave("win", 1.30, 420.0)
	tones["click"] = _wave("click", .13, 660.0)
	tones["skid"] = _wave("skid", .28, 160.0)

func attach_rival(car_node: Node3D, id: int) -> void:
	var p := AudioStreamPlayer3D.new()
	p.name = "RivalMotor" + str(id)
	p.stream = engine_wave
	p.volume_db = -25.0
	p.unit_size = 8.0
	p.max_distance = 70.0
	p.pitch_scale = 0.85 + float(id) * .12
	car_node.add_child(p)
	rival_sounds.append(p)

func start_engines() -> void:
	if not enabled:
		return
	if engine != null and not engine.playing:
		engine.play()
	for p in rival_sounds:
		if not p.playing:
			p.play()

func stop_engines() -> void:
	if engine != null:
		engine.stop()
	for p in rival_sounds:
		p.stop()

func set_motor_speed(speed_ratio: float, turbo: bool) -> void:
	if engine == null:
		return
	var ratio: float = clampf(speed_ratio,0.0,1.0)
	engine.pitch_scale = 0.71 + ratio * .82 + (0.24 if turbo else 0.0)
	engine.volume_db = -19.0 + ratio * 5.0 + (2.0 if turbo else 0.0)

func toggle_sound() -> bool:
	enabled = not enabled
	if not enabled:
		stop_engines()
	else:
		start_engines()
	return enabled

func cue(key: String) -> void:
	if not enabled or not tones.has(key):
		return
	var p: AudioStreamPlayer = sfx[sfx_index]
	sfx_index = (sfx_index+1) % sfx.size()
	p.stream = tones[key]
	p.volume_db = -10.0 if key != "skid" else -19.0
	p.pitch_scale = 1.0
	p.play()

func _wave(kind: String, length: float, frequency: float, looping: bool = false) -> AudioStreamWAV:
	var count: int = int(length * float(RATE))
	var bytes := PackedByteArray()
	bytes.resize(count * 2)
	for i in range(count):
		var t: float = float(i)/float(RATE)
		var x: float = t/length
		var envelope: float = 1.0 if looping else pow(1.0-x,1.4)
		var sample: float = 0.0
		match kind:
			"engine":
				sample = .47*sin(TAU*frequency*t)+.24*sin(TAU*frequency*2.0*t)+.12*sin(TAU*frequency*3.0*t)
				sample += .08*sin(TAU*frequency*5.0*t)
			"count":
				sample = .55*sin(TAU*frequency*t)+.14*sin(TAU*frequency*2.0*t)
			"go":
				sample = .47*sin(TAU*(frequency*t+310.0*t*t))+.20*sin(TAU*(frequency*1.5*t))
			"coin":
				sample = .43*sin(TAU*(frequency*t+380.0*t*t))+.19*sin(TAU*(frequency*1.49*t))
			"boost":
				sample = .36*sin(TAU*(frequency*t+760.0*t*t))+.17*sin(TAU*(frequency*3.1*t))
			"lap":
				sample = .52*sin(TAU*(frequency*(1.0+floorf(x*3.0)*.25)*t))
			"win":
				var note: int = mini(int(x*7.0),6)
				var semitones: Array[int] = [0,4,7,12,7,12,16]
				var hz: float = frequency*pow(2.0,float(semitones[note])/12.0)
				sample = .47*sin(TAU*hz*t)+.09*sin(TAU*hz*2.0*t)
			"skid":
				sample = .33*sin(TAU*(frequency*t+230.0*t*t))+.15*sin(TAU*(frequency*5.3*t))
			_:
				sample = .45*sin(TAU*frequency*t)
		var value: int = int(clampf(sample*envelope,-0.96,.96)*32760.0)
		bytes.encode_s16(i*2,value)
	var wav := AudioStreamWAV.new()
	wav.format = AudioStreamWAV.FORMAT_16_BITS
	wav.mix_rate = RATE
	wav.stereo = false
	wav.data = bytes
	if looping:
		wav.loop_mode = AudioStreamWAV.LOOP_FORWARD
		wav.loop_begin = 0
		wav.loop_end = count
	return wav
