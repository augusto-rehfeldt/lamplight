@tool
extends Node2D

const MAPS := {
	"library":{"frame":0,"people":["margot"],"landmarks":{"shelf":Vector2(116,142),"margot":Vector2(175,175),"computer":Vector2(397,173),"compass":Vector2(250,137),"miso":Vector2(284,227),"exit":Vector2(240,238)},"blocks":[Rect2(371,122,88,37)],"hits":{"shelf":Rect2(55,27,137,112),"computer":Rect2(370,95,89,69),"compass":Rect2(228,80,39,57)}},
	"town":{"frame":1,"people":["noor"],"landmarks":{"library":Vector2(85,164),"workshop":Vector2(323,174),"garden":Vector2(438,215),"noor":Vector2(266,185),"notice":Vector2(205,154)},"blocks":[Rect2(20,140,43,48)],"hits":{"library":Rect2(65,70,45,95),"workshop":Rect2(301,76,51,93),"garden":Rect2(423,174,35,64),"notice":Rect2(170,107,45,43)}},
	"workshop":{"frame":2,"people":["jules"],"landmarks":{"jules":Vector2(295,185),"writer":Vector2(397,180),"post":Vector2(333,156),"exit":Vector2(240,238)},"blocks":[Rect2(46,122,91,41),Rect2(374,122,85,41)],"hits":{"writer":Rect2(373,88,87,84),"post":Rect2(305,85,48,69)}},
	"garden":{"frame":3,"people":["ada","elias"],"landmarks":{"ada":Vector2(348,174),"elias":Vector2(145,203),"author":Vector2(91,153),"observation":Vector2(321,222),"exit":Vector2(240,238)},"blocks":[Rect2(218,116,52,47)],"hits":{"author":Rect2(69,113,39,43),"observation":Rect2(302,203,38,33)}}
}
const BOUNDS := [Rect2(0,0,480,122),Rect2(0,110,20,160),Rect2(460,110,20,160),Rect2(0,250,480,20)]
@export_enum("campaign","free_play","modern") var mode := "campaign"
@export_enum("arrival","shared","patron") var choice := "arrival"
var place := "library"
var era := 0
var motion := true
var compass_active := false
var elapsed := 0.0
var navigation := AStarGrid2D.new()
var backdrop: Sprite2D
var destination := Vector2.ZERO
var highlight := ""
var cast := {}
var characters: Texture2D
var cat: Sprite2D
var visitor: Sprite2D
var bodies: Array[Node] = []
var landmarks: Dictionary = MAPS.library.landmarks

func _ready() -> void:
	backdrop = Sprite2D.new()
	backdrop.texture = load("res://assets/cozy-world.png")
	backdrop.hframes = 2
	backdrop.vframes = 2
	backdrop.centered = false
	backdrop.scale = Vector2(480,270)/(backdrop.texture.get_size()/2)
	backdrop.z_index = -10
	add_child(backdrop)
	characters = load("res://assets/cozy-characters.png")
	var column := 1
	for id in ["margot","ada","elias","jules","noor"]:
		var person := Sprite2D.new()
		person.texture = characters
		person.hframes = 6
		person.vframes = 3
		person.frame = column
		person.scale = Vector2(48,52)/(characters.get_size()/Vector2(6,3))
		add_child(person)
		cast[id] = person
		column += 1
	cat = Sprite2D.new()
	cat.texture = load("res://assets/miso.png")
	cat.hframes = 3
	cat.scale = Vector2(18,18)/(cat.texture.get_size()/Vector2(3,1))
	add_child(cat)
	visitor = Sprite2D.new()
	visitor.texture = characters
	visitor.hframes = 6
	visitor.vframes = 3
	visitor.frame = 3
	visitor.scale = Vector2(48,52)/(characters.get_size()/Vector2(6,3))
	visitor.modulate = Color("e0cdac")
	add_child(visitor)
	navigation.region = Rect2i(0,0,60,34)
	navigation.cell_size = Vector2(8,8)
	navigation.offset = Vector2(4,4)
	navigation.diagonal_mode = AStarGrid2D.DIAGONAL_MODE_ONLY_IF_NO_OBSTACLES
	configure("library")

func configure(location: String) -> void:
	place = location
	landmarks = MAPS[place].landmarks.duplicate()
	backdrop.frame = int(MAPS[place].frame)
	destination = Vector2.ZERO
	highlight = ""
	for body in bodies:
		body.free()
	bodies.clear()
	var obstacles: Array = BOUNDS + MAPS[place].blocks
	for rect in obstacles:
		var body := StaticBody2D.new()
		var collider := CollisionShape2D.new()
		var shape := RectangleShape2D.new()
		shape.size = rect.size
		collider.shape = shape
		body.position = rect.get_center()
		body.add_child(collider)
		add_child(body)
		bodies.append(body)
	navigation.update()
	for x in range(60):
		for y in range(34):
			var blocked := false
			for rect in obstacles:
				if rect.grow(6).has_point(Vector2(x*8+4,y*8+4)):
					blocked = true
			navigation.set_point_solid(Vector2i(x,y),blocked)
	for id in cast:
		cast[id].visible = id in MAPS[place].people
		if cast[id].visible:
			cast[id].position = landmarks[id]+Vector2(0,-25)
			cast[id].z_index = int(landmarks[id].y)
	cat.visible = place == "library"
	cat.position = Vector2(284,220)
	cat.z_index = 227
	visitor.visible = place == "garden" and mode == "campaign"
	visitor.position = Vector2(91,128)
	visitor.z_index = 153
	queue_redraw()

func route(from: Vector2, to: Vector2) -> PackedVector2Array:
	var start := Vector2i(from/8)
	var finish := Vector2i(to/8)
	if not navigation.is_in_boundsv(start) or not navigation.is_in_boundsv(finish):
		return PackedVector2Array()
	if navigation.is_point_solid(start) or navigation.is_point_solid(finish):
		return PackedVector2Array()
	return navigation.get_point_path(start,finish)

func safe_position(point: Vector2) -> Vector2:
	var cell := Vector2i(point/8)
	if navigation.is_in_boundsv(cell) and not navigation.is_point_solid(cell):
		return point
	var best := Vector2(240,204)
	var distance := INF
	for x in range(60):
		for y in range(34):
			var candidate := Vector2(x*8+4,y*8+4)
			if not navigation.is_point_solid(Vector2i(x,y)) and candidate.distance_squared_to(point) < distance:
				best = candidate
				distance = candidate.distance_squared_to(point)
	return best

func clicked(point: Vector2) -> String:
	for id in MAPS[place].people:
		if Rect2(landmarks[id]-Vector2(20,51),Vector2(40,56)).has_point(point):
			return id
	for id in MAPS[place].hits:
		if MAPS[place].hits[id].has_point(point):
			return id
	for id in ["exit","miso"]:
		if landmarks.has(id) and Rect2(landmarks[id]-Vector2(16,18),Vector2(32,30)).has_point(point):
			return id
	return ""

func nearest(point: Vector2, radius := 28.0) -> String:
	var found := ""
	for key in landmarks:
		var distance: float = point.distance_to(landmarks[key])
		if distance < radius:
			radius = distance
			found = key
	return found

func _process(delta: float) -> void:
	if motion:
		elapsed += delta
	for id in cast:
		if cast[id].visible:
			var anchor: Vector2 = MAPS[place].landmarks[id]
			var cycle := fmod(elapsed+anchor.x,20.0)
			var offset := Vector2(sin(cycle*PI/5)*10,0) if motion and cycle < 10 else Vector2.ZERO
			var point := anchor+offset
			var cell := Vector2i(point/8)
			if navigation.is_in_boundsv(cell) and not navigation.is_point_solid(cell):
				landmarks[id] = point
			cast[id].position = landmarks[id]+Vector2(0,-25)
			cast[id].z_index = int(landmarks[id].y)
			var column: int = ["","margot","ada","elias","jules","noor"].find(id)
			cast[id].frame = column+(6*(1+int(elapsed*4)%2) if offset.length() > 1 else 0)
	if is_instance_valid(cat):
		cat.frame = [0,0,0,1,0,2][int(elapsed*2)%6]
	queue_redraw()

func _draw() -> void:
	if not is_instance_valid(backdrop):
		return
	for key in MAPS[place].people:
		draw_set_transform(landmarks[key])
		draw_colored_polygon(PackedVector2Array([Vector2(-7,0),Vector2(7,0),Vector2(11,4),Vector2(-3,5)]),Color(0.16,0.11,0.06,0.23))
	draw_set_transform(Vector2.ZERO)
	if place in ["town","garden"]:
		for i in range(8):
			var at := Vector2(40+fmod(i*57+elapsed*5,400),140+sin(elapsed+i)*12+i*11)
			draw_rect(Rect2(at,Vector2(1.5,0.7)),Color("efd6a1"))
	if place == "library":
		# An ordinary repair kit, without magical lights. The laptop belongs to the traveler.
		draw_rect(Rect2(245,124,12,7),Color("795f47"))
		draw_rect(Rect2(248,125,6,4),Color("d6c39a"))
	if destination != Vector2.ZERO:
		draw_arc(destination,4,0,TAU,16,Color("665040"),0.8)
	if not highlight.is_empty() and landmarks.has(highlight):
		var mark: Vector2 = landmarks[highlight]+Vector2(0,-57 if highlight in MAPS[place].people or highlight == "author" else -37)
		draw_colored_polygon(PackedVector2Array([mark,mark+Vector2(-3,-4),mark+Vector2(3,-4)]),Color("7b593c"))
