extends RefCounted
## RibhLab Midnight Rush v0.7 — assisted longitudinal and lateral car dynamics.
## Designed for 60 Hz fixed physics: throttle (automatic), service brake,
## progressive steering, friction-limited grip and actual handbrake slip.
## This IS NOT an independently simulated wheel-suspension RigidBody3D.
var velocity: float = 0.0
var slip_velocity: float = 0.0
var steer_angle: float = 0.0
var body_roll: float = 0.0
var engine_load: float = 0.0
var wheel_spin: float = 0.0
var drift_intensity: float = 0.0
var brake_intensity: float = 0.0
var skid_time: float = 0.0

const MASS: float = 1030.0
const DRAG_COEFF: float = .50
const ROLLING_RESISTANCE: float = 135.0
const MOTOR_FORCE: float = 12400.0
const BOOST_FORCE: float = 18100.0
const BRAKE_FORCE: float = 20500.0
const EDGE_DRAG: float = 5600.0
const WHEEL_RADIUS: float = .43

func reset() -> void:
	velocity = 0.0
	slip_velocity = 0.0
	steer_angle = 0.0
	body_roll = 0.0
	engine_load = 0.0
	wheel_spin = 0.0
	drift_intensity = 0.0
	brake_intensity = 0.0
	skid_time = 0.0

func simulate(delta: float, steering_input: float, boosting: bool,
		outside_edge: bool = false, braking: bool = false,
		handbrake: bool = false, upgrades: Dictionary = {}, throttle: float = 1.0) -> Dictionary:
	var dt: float = clampf(delta,0.0,.05)
	var steering: float = clampf(steering_input,-1.0,1.0)
	var speed_level: int = clampi(int(upgrades.get("speed",0)),0,5)
	var accel_level: int = clampi(int(upgrades.get("accel",0)),0,5)
	var grip_level: int = clampi(int(upgrades.get("grip",0)),0,5)
	var max_speed: float = (63.0 if boosting else 39.0)*(1.0+.055*float(speed_level))
	var motor_force: float = (BOOST_FORCE if boosting else MOTOR_FORCE)*(1.0+.105*float(accel_level))*clampf(throttle,0.0,1.0)
	# Braking is a real force; there is no instantaneous artificial speed multiplier.
	brake_intensity = move_toward(brake_intensity,1.0 if braking else 0.0,7.5*dt)
	var torque_falloff: float = clampf((max_speed-velocity)/13.5,0.0,1.0)
	var air_drag: float = DRAG_COEFF*velocity*velocity
	var drag: float = air_drag+ROLLING_RESISTANCE + (EDGE_DRAG if outside_edge else 0.0)
	var brake_force: float = BRAKE_FORCE*brake_intensity
	if handbrake:
		brake_force += BRAKE_FORCE*.20
	# Electronic speed limiter: prevents unlimited boost and physics explosions.
	if velocity>max_speed:
		brake_force += BRAKE_FORCE*clampf((velocity-max_speed)/8.0,0.0,1.0)
	var acceleration: float = (motor_force*torque_falloff-drag-brake_force)/MASS
	velocity = clampf(velocity+acceleration*dt,0.0,75.0)
	if braking and velocity<.5:
		velocity = 0.0

	# Progressive steering at speed; less twitchy at high speed.
	var response: float = lerpf(3.1,2.15,clampf(velocity/70.0,0.0,1.0))
	var steer_limit: float = lerpf(.46,.29,clampf(velocity/65.0,0.0,1.0))
	steer_angle = move_toward(steer_angle,steering*steer_limit,response*dt)

	# Corner lateral speed is controlled by traction. Handbrake temporarily
	# cuts grip so a drift develops, then the tyre catches gradually on release.
	var base_lateral: float = steer_angle*(7.0+velocity*.22)
	var target_lateral: float = base_lateral*(1.72 if handbrake else 1.0)
	var grip: float = (7.8 + float(grip_level)*.90)*(0.30 if handbrake else 1.0)
	if boosting:
		grip *= .87
	var before: float = slip_velocity
	slip_velocity = move_toward(slip_velocity,target_lateral,grip*dt)
	var slip_delta: float = absf(target_lateral-slip_velocity)
	var tire_yaw: float = absf(steer_angle)*clampf(velocity/35.0,0.0,1.0)
	var slide: float = slip_delta/(7.5 if handbrake else 9.5)
	drift_intensity = clampf(slide+(.25 if handbrake and absf(steering)>.12 and velocity>14.0 else 0.0),0.0,1.0)
	if handbrake and absf(steering)>.15 and velocity>14.0:
		skid_time += dt
	else:
		skid_time = maxf(0.0,skid_time-dt*3.0)
	body_roll = lerpf(body_roll,
		-steer_angle*.22-drift_intensity*signf(steer_angle)*.065,
		clampf(dt*4.0,0.0,1.0))
	engine_load = lerpf(engine_load,torque_falloff,clampf(dt*4.5,0.0,1.0))
	wheel_spin = fposmod(wheel_spin+velocity*dt/WHEEL_RADIUS,TAU)
	return {
		"speed":velocity,
		"acceleration":acceleration,
		"lateral_velocity":slip_velocity,
		"roll":body_roll,
		"slip":drift_intensity,
		"pitch":.8+velocity/80.0+(.16 if boosting else 0.0),
		"brake":brake_intensity,
		"grip":grip,
		"yaw":tire_yaw,
		"skid_time":skid_time,
		"lateral_change":slip_velocity-before
	}
