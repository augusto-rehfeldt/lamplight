@tool
extends CharacterBody2D

signal arrived
signal footstep
var can_move := false
var phase := 0.0
var facing := Vector2.DOWN
var path := PackedVector2Array()
var foot_clock := 0.0
var sprites: Texture2D = preload("res://assets/cozy-characters.png")

func stop() -> void:
	path.clear()
	velocity = Vector2.ZERO
	get_parent().destination = Vector2.ZERO

func walk_to(point: Vector2) -> bool:
	path = get_parent().route(position,point)
	if path.size() > 0:
		path.remove_at(0)
	get_parent().destination = point if not path.is_empty() else Vector2.ZERO
	return not path.is_empty()

func _physics_process(delta: float) -> void:
	if Engine.is_editor_hint():
		return
	var direction := Input.get_vector("walk_left","walk_right","walk_up","walk_down") if can_move else Vector2.ZERO
	if direction != Vector2.ZERO:
		stop()
	elif can_move and not path.is_empty():
		if position.distance_to(path[0]) < 2:
			path.remove_at(0)
		if path.is_empty():
			get_parent().destination = Vector2.ZERO
			arrived.emit()
		else:
			direction = position.direction_to(path[0])
	var speed := 118.0 if Input.is_key_pressed(KEY_SHIFT) else 76.0
	velocity = direction * speed
	if not path.is_empty():
		velocity = velocity.limit_length(position.distance_to(path[0])/delta)
	if direction != Vector2.ZERO:
		facing = direction
		phase += delta * (16 if speed > 100 else 11)
		foot_clock += delta
		if foot_clock > (0.22 if speed > 100 else 0.32):
			foot_clock = 0
			footstep.emit()
	else:
		phase = 0
	move_and_slide()
	z_index = int(position.y)
	if can_move and get_slide_collision_count() > 0 and not path.is_empty():
		stop()
	queue_redraw()

func _draw() -> void:
	var cell := sprites.get_size()/Vector2(6,3)
	var frame := 0 if phase == 0 else (1 if sin(phase) > 0 else 2)
	var region := Rect2(Vector2(0,frame*cell.y),cell)
	draw_colored_polygon(PackedVector2Array([Vector2(-7,0),Vector2(6,-1),Vector2(12,4),Vector2(1,6)]),Color(0.16,0.11,0.06,0.25))
	draw_texture_rect_region(sprites,Rect2(-24,-51,48,52),region)
