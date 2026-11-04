extends RefCounted
## Physically inspired arcade drivetrain: engine torque, quadratic air drag,
## longitudinal grip, progressive steering, lateral slip and suspension response.
## This runs alongside Godot's built-in Jolt 3D physics backend.
## It is intentionally kid-friendly and is NOT a full raycast/rigid-body car simulator.

var velocity: float = 0.0
var slip_velocity: float = 0.0
var steer_angle: float = 0.0
var body_roll: float = 0.0
var engine_load: float = 0.0
var wheel_spin: float = 0.0
var drift_intensity: float = 0.0

const MASS: float = 990.0
const DRAG_COEFF: float = 0.51
const ROLLING_RESISTANCE: float = 145.0
const MOTOR_FORCE: float = 10750.0
const BOOST_FORCE: float = 15500.0
const BRAKE_FORCE: float = 10500.0
const TIRE_GRIP: float = 7.8
const WHEEL_RADIUS: float = 0.43

func reset() -> void:
	velocity = 0.0
	slip_velocity = 0.0
	steer_angle = 0.0
	body_roll = 0.0
	engine_load = 0.0
	wheel_spin = 0.0
	drift_intensity = 0.0

func simulate(delta: float, steering_input: float, boosting: bool, outside_edge: bool = false) -> Dictionary:
	var steering: float = clampf(steering_input, -1.0, 1.0)
	var max_velocity: float = 59.0 if boosting else 38.0
	var air_drag: float = DRAG_COEFF * velocity * velocity
	var motor: float = BOOST_FORCE if boosting else MOTOR_FORCE
	# Ease engine torque as the car reaches its configured top speed.
	var torque_factor: float = clampf((max_velocity - velocity) / 12.0, 0.0, 1.0)
	var force: float = motor * torque_factor - air_drag - ROLLING_RESISTANCE
	if velocity > max_velocity:
		force -= BRAKE_FORCE * clampf((velocity-max_velocity)/8.0, 0.0, 1.0)
	if outside_edge:
		force -= BRAKE_FORCE * 0.35
	velocity = clampf(velocity + (force / MASS) * delta, 0.0, 65.0)
	var response: float = 2.9 - clampf(velocity / 120.0, 0.0, 0.45)
	steer_angle = move_toward(steer_angle, steering * 0.43, response * delta)
	var lateral_target: float = steer_angle * (7.6 + velocity * 0.15)
	var effective_grip: float = TIRE_GRIP * (0.75 if boosting else 1.0)
	slip_velocity = move_toward(slip_velocity, lateral_target, effective_grip * delta)
	drift_intensity = clampf(absf(lateral_target-slip_velocity)/5.0, 0.0, 1.0)
	body_roll = lerpf(body_roll, -steer_angle*0.19 - drift_intensity*signf(steer_angle)*0.055,
		clampf(delta*5.0, 0.0, 1.0))
	engine_load = lerpf(engine_load, torque_factor, clampf(delta*4.0, 0.0, 1.0))
	wheel_spin = fposmod(wheel_spin + velocity * delta / WHEEL_RADIUS, TAU)
	return {
		"speed": velocity,
		"lateral_velocity": slip_velocity,
		"roll": body_roll,
		"slip": drift_intensity,
		"pitch": 0.8 + velocity / 80.0 + (0.18 if boosting else 0.0)
	}
