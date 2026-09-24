extends Control

signal destination_selected(place: String)
const POINTS := {"library":Vector2(76,92),"town":Vector2(180,92),"workshop":Vector2(284,92),"garden":Vector2(180,30)}
var current := "library"
var visited: Array = []
var motion := true
var elapsed := 0.0

func _ready() -> void:
	custom_minimum_size = Vector2(736,300)
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	for place in POINTS:
		var pin := Button.new()
		pin.text = {"library":"Library","town":"Square","workshop":"Print shop","garden":"Garden"}[place]
		pin.position = POINTS[place]*2+Vector2(-54,23)
		pin.size = Vector2(108,30)
		pin.disabled = place == current
		pin.tooltip_text = "You are here" if place == current else "Walk to " + pin.text + " · no day cost"
		pin.pressed.connect(func(): destination_selected.emit(place))
		add_child(pin)
	queue_redraw()

func _process(delta: float) -> void:
	if motion:
		elapsed += delta
		queue_redraw()

func _draw() -> void:
	draw_set_transform(Vector2.ZERO,0,Vector2(2,2))
	draw_rect(Rect2(0,0,368,150),Color("a2c5be"))
	var land := PackedVector2Array([Vector2(14,30),Vector2(30,30),Vector2(30,12),Vector2(310,12),Vector2(310,24),Vector2(350,24),Vector2(350,124),Vector2(328,124),Vector2(328,142),Vector2(20,142),Vector2(20,120),Vector2(8,120),Vector2(8,50),Vector2(14,50)])
	draw_colored_polygon(land,Color("6f9362"))
	for i in range(75):
		var point := Vector2(30+(i*47)%298,20+(i*31)%112)
		draw_rect(Rect2(point,Vector2(3,2)),Color("83a36b"))
	# The river crosses the same east-west road as the bridge, keeping paths legible.
	draw_rect(Rect2(228,12,14,130),Color("a2c5be"))
	for i in range(9):
		draw_rect(Rect2(230,17+i*14+int(elapsed*3)%6,7,1),Color("d0dfc5"))
	draw_rect(Rect2(72,89,216,8),Color("ddc18a"))
	draw_rect(Rect2(176,30,8,66),Color("ddc18a"))
	draw_rect(Rect2(224,85,22,16),Color("866044"))
	for x in range(226,245,4):
		draw_rect(Rect2(x,85,2,16),Color("c29965"))
	for i in range(18):
		var at := Vector2(40+i*17,126 if i%2 else 52)
		if at.x > 222 and at.x < 246:
			continue
		draw_rect(Rect2(at+Vector2(-1,0),Vector2(3,6)),Color("755841"))
		draw_rect(Rect2(at+Vector2(-5,-8),Vector2(11,9)),Color("456d4b"))
		draw_rect(Rect2(at+Vector2(-3,-12),Vector2(7,6)),Color("527e50"))
	for place in POINTS:
		var at: Vector2 = POINTS[place]
		if place in ["library","workshop"]:
			draw_rect(Rect2(at+Vector2(-16,-19),Vector2(32,21)),Color("eed9a5"))
			draw_rect(Rect2(at+Vector2(-20,-24),Vector2(40,7)),Color("a76e50"))
			draw_rect(Rect2(at+Vector2(-15,-29),Vector2(30,6)),Color("b78358"))
			draw_rect(Rect2(at+Vector2(-4,-7),Vector2(8,9)),Color("755841"))
			for x in [-12,8]:
				draw_rect(Rect2(at+Vector2(x,-13),Vector2(5,5)),Color("a2c5be"))
		elif place == "town":
			draw_rect(Rect2(at-Vector2(15,14),Vector2(30,24)),Color("c8bc97"))
			draw_rect(Rect2(at-Vector2(7,10),Vector2(14,12)),Color("a2c5be"))
			draw_rect(Rect2(at-Vector2(2,14),Vector2(4,12)),Color("f2dfb6"))
		else:
			draw_rect(Rect2(at-Vector2(22,12),Vector2(44,24)),Color("486c49"))
			for i in range(8):
				draw_rect(Rect2(at+Vector2(-17+i*5,-8+(i%2)*10),Vector2(3,3)),Color("eec896"))
		if place in visited:
			draw_rect(Rect2(at+Vector2(18,-5),Vector2(4,4)),Color("fce4a7"))
	var here: Vector2 = POINTS[current]+Vector2(0,-38-int(sin(elapsed*3)*2))
	draw_rect(Rect2(here-Vector2(3,3),Vector2(6,6)),Color("fff4d9"))
	draw_colored_polygon(PackedVector2Array([here+Vector2(-4,2),here+Vector2(4,2),here+Vector2(0,7)]),Color("fff4d9"))
	# Pixel compass rose.
	draw_line(Vector2(338,39),Vector2(338,59),Color("f5e5bc"),2)
	draw_line(Vector2(331,49),Vector2(345,49),Color("f5e5bc"),2)
	draw_colored_polygon(PackedVector2Array([Vector2(338,33),Vector2(334,41),Vector2(342,41)]),Color("f5e5bc"))
