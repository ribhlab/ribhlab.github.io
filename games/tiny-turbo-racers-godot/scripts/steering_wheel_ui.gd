extends Control
## Native 2D wheel HUD: self-drawn radial game controller with steering rotation.
## Touch input is owned by touch_controls.gd, so this visual has no blocking hitbox.
var steer_value: float = 0.0
var active: bool = false

func _ready() -> void:
	mouse_filter=Control.MOUSE_FILTER_IGNORE
	set_process(false)

func set_steering(value: float) -> void:
	var v:float=clampf(value,-1.0,1.0)
	if absf(v-steer_value)>.003:
		steer_value=v
		queue_redraw()

func _draw() -> void:
	var c:Vector2=size*.5
	var r:float=minf(size.x,size.y)*.47
	draw_circle(c,r+9,Color("#06111b",.75))
	draw_arc(c,r,0.0,TAU,90,Color("#6ee6fd",.55),9.0,true)
	draw_arc(c,r-9,0.0,TAU,90,Color("#111c2b",.96),20.0,true)
	draw_arc(c,r-15,0.0,TAU,90,Color("#a2ecff",.85),3.0,true)
	var rotation:float=steer_value*2.05
	for k in range(3):
		var angle:float=rotation+TAU*float(k)/3.0-PI*.5
		var spoke:Vector2=Vector2(cos(angle),sin(angle))
		draw_line(c+spoke*17.0,c+spoke*(r-15.0),Color("#b9d7e6"),15.0,true)
		draw_line(c+spoke*20.0,c+spoke*(r-15.0),Color("#4a839a"),4.0,true)
	draw_circle(c,23.0,Color("#182f47"))
	draw_arc(c,22.0,0.0,TAU,48,Color("#8ceaff"),4.0,true)
	draw_circle(c,9.0,Color("#eb6cae"))
	# Visible top marker rotates with physical hand movement.
	var top:Vector2=Vector2(sin(rotation),-cos(rotation))
	draw_line(c+top*(r-14),c+top*(r-1),Color("#f74d96"),11.0,true)
