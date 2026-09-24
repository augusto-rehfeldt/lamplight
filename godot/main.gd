extends Node2D

const MODE_NAMES := {"campaign":"The Way Back", "free_play":"A Library of Your Own", "modern":"The Contemporary Study"}
const MODE_RULES := {"campaign":"Seven eras. Find your way home.", "free_play":"Read and write without deadlines.", "modern":"Present-day writing. Imports unavailable."}
const DIALOGUE := {"margot":"There is tea on the table. The room upstairs is yours for as long as you need it.","ada":"The flowers lean toward the window. I keep wondering what a second window would change.","elias":"An argument gets interesting when someone finds a reason to doubt it. Bring yours to our circle.","jules":"There is room on the press for one more good idea. What have you been working on?", "noor":"I found a pressed flower in this binding. Someone wanted to keep more than words.", "miso":"Miso makes room for exactly one hand beside his sunny patch."}
@onready var room = $ReadingRoom
@onready var player = $ReadingRoom/Player
@onready var ui: Control = $Interface/Root
var slot: Dictionary = {}
var settings: Dictionary = {"readable":false}
var screen := "title"
var busy := false
var connected := false
var message_text := ""
var message_label: Label
var hint: Label
var content: VBoxContainer
var writer_title: LineEdit
var writer_text: TextEdit
var writer_dirty := false
var writer_delay := 0.0
var document_id := ""
var letter_text: TextEdit
var letter_draft := ""
var autosave := 0.0
var saved_position := Vector2.ZERO
var pending_interaction := ""
var objective_label: Label
var audio_player: Node
var dialogue_label: Label
var dialogue_reveal := 0.0
var word_count: Label
var word_pattern := RegEx.new()
var ai_ready := false
var toast_time := 0.0
var request_time := 0.0
var activity_label: Label
var activity_bar: ProgressBar
var activity_box: VBoxContainer
var usage_label: Label
var ai_status: Dictionary = {}
var telemetry_busy := false
var workshop_text: TextEdit
var workshop_dirty := false
var workshop_delay := 0.0
var workshop_count: Label
var workshop_next: Button
var request_label := "Saving"
const PIXELS = preload("res://pixel_ui.gd")
const LESSONS := {
	"move":"WASD / arrows or click to walk. Hold Shift to run.",
	"shelf":"Read a summary, then Study to unlock its practice question.",
	"map":"Pick a place. Paths through the square cost no days.",
	"computer":"Choose a format and sources. Work through five saved steps with Margot.",
	"writer":"Your words autosave. Open Submission when ready to share.",
	"post":"Post spends paper and coins. Wait advances delivery by one day.",
	"compass":"Apply what you learned to repair the recorder."}


func _ready() -> void:
	word_pattern.compile("[^\\W_]+")
	audio_player = Node.new()
	audio_player.set_script(load("res://audio.gd"))
	add_child(audio_player)
	player.footstep.connect(func(): audio_player.play("step"))
	player.arrived.connect(func():
		var target := pending_interaction
		pending_interaction = ""
		if screen == "playing" and not target.is_empty():
			await interact(target))
	get_tree().auto_accept_quit = false
	for action in {"walk_left":[KEY_A,KEY_LEFT], "walk_right":[KEY_D,KEY_RIGHT], "walk_up":[KEY_W,KEY_UP], "walk_down":[KEY_S,KEY_DOWN], "interact":[KEY_E], "journal":[KEY_J]}:
		if not InputMap.has_action(action):
			InputMap.add_action(action)
		for key in {"walk_left":[KEY_A,KEY_LEFT], "walk_right":[KEY_D,KEY_RIGHT], "walk_up":[KEY_W,KEY_UP], "walk_down":[KEY_S,KEY_DOWN], "interact":[KEY_E], "journal":[KEY_J]}[action]:
			var event := InputEventKey.new()
			event.physical_keycode = key
			InputMap.action_add_event(action,event)
	apply_theme()
	var telemetry := Timer.new()
	telemetry.wait_time = 1.0
	telemetry.timeout.connect(func():
		if busy:
			await refresh_usage())
	add_child(telemetry)
	telemetry.start()
	await title_screen()
	if "--check" in OS.get_cmdline_user_args():
		await run_check()
	elif "--capture" in OS.get_cmdline_user_args():
		await capture_screens()

func apply_theme() -> void:
	var theme := Theme.new()
	theme.default_font_size = 17 if settings.get("readable",false) else 16
	if not settings.get("readable",false):
		theme.default_font = load("res://assets/pixelify.ttf")
		theme.set_font_size("font_size","Button",19)
	for type in ["Label","Button","OptionButton","ProgressBar","LineEdit","TextEdit","CheckButton","CheckBox"]:
		for state in ["font_color","font_hover_color","font_pressed_color","font_focus_color","font_hover_pressed_color"]:
			theme.set_color(state,type,Color("44382f"))
		theme.set_color("font_disabled_color",type,Color("84735c"))
	for type in ["LineEdit","TextEdit"]:
		theme.set_color("font_placeholder_color",type,Color("786a57"))
		theme.set_color("caret_color",type,Color("44382f"))
		theme.set_color("selection_color",type,Color("c8d8b1"))
		theme.set_color("font_selected_color",type,Color("2e412d"))
	for type in ["PanelContainer","Button","OptionButton","LineEdit","TextEdit"]:
		var style := StyleBoxFlat.new()
		style.bg_color = Color("fff4dff5")
		style.border_color = Color("9b7755")
		style.set_border_width_all(2)
		style.content_margin_left = 14
		style.content_margin_right = 14
		style.content_margin_top = 9
		style.content_margin_bottom = 9
		style.shadow_color = Color("62473255")
		style.shadow_size = 4
		style.shadow_offset = Vector2(2,3)
		theme.set_stylebox("panel" if type == "PanelContainer" else "normal",type,style)
		var focus := style.duplicate()
		focus.bg_color = Color.TRANSPARENT
		focus.shadow_size = 0
		focus.border_color = Color("52754b")
		theme.set_stylebox("focus",type,focus)
		var hover := style.duplicate()
		hover.bg_color = Color("e4edcf")
		hover.border_color = Color("70915c")
		theme.set_stylebox("hover",type,hover)
		theme.set_stylebox("pressed",type,hover)
		theme.set_stylebox("disabled",type,style)
	var track := StyleBoxFlat.new()
	track.bg_color = Color("d4c5a2")
	var fill := StyleBoxFlat.new()
	fill.bg_color = Color("6d8b50")
	theme.set_stylebox("background","ProgressBar",track)
	theme.set_stylebox("fill","ProgressBar",fill)
	ui.theme = theme
	if is_instance_valid(audio_player):
		audio_player.apply(settings)
	room.motion = settings.get("motion",true)

func call_api(data: Dictionary) -> Dictionary:
	if busy:
		return {}
	var url := OS.get_environment("LAMPLIGHT_URL")
	if not url.begins_with("http://127.0.0.1:") or OS.get_environment("LAMPLIGHT_TOKEN").is_empty():
		notify("Launch with python run_lamplight.py to connect the local save service.")
		return {}
	busy = true
	request_label = {"ai_test":"Checking companion", "ai_coach":"Margot is reviewing this step", "ai_generate":"Drafting", "ai_ask":"Composing a reply", "discuss":"Considering the evidence"}.get(data.get("op"),"Saving")
	if is_instance_valid(activity_box):
		activity_box.visible = true
	if is_instance_valid(workshop_text):
		workshop_text.editable = false
	player.can_move = false
	var http := HTTPRequest.new()
	http.timeout = 100.0 if data.get("op") == "ai_test" else 85.0 if str(data.get("op","")).begins_with("ai_") or data.get("op") == "discuss" else 12.0
	request_time = 0.0
	http.max_redirects = 0
	http.body_size_limit = 20_000_000
	add_child(http)
	var error := http.request(url,PackedStringArray(["Content-Type: application/json","X-Library-Token: " + OS.get_environment("LAMPLIGHT_TOKEN")]),HTTPClient.METHOD_POST,JSON.stringify(data))
	var result: Dictionary = {}
	if error == OK:
		var reply: Array = await http.request_completed
		var decoded = JSON.parse_string(reply[3].get_string_from_utf8())
		if reply[0] == HTTPRequest.RESULT_SUCCESS and reply[1] == 200 and decoded is Dictionary:
			result = decoded
			connected = true
		else:
			notify(str(decoded.get("error","The local service did not respond. Your open text is preserved.")) if decoded is Dictionary else "The local service did not respond. Your open text is preserved.")
	else:
		notify("Could not connect to the local service. Your open text is preserved.")
	http.queue_free()
	if data.get("op") == "ai_status" and not result.is_empty():
		ai_status = result
	elif str(data.get("op","")).begins_with("ai_") or data.get("op") == "discuss":
		await refresh_usage()
	busy = false
	if is_instance_valid(activity_box):
		activity_box.visible = false
	if is_instance_valid(workshop_text):
		workshop_text.editable = true
	player.can_move = screen == "playing" and get_window().has_focus()
	return result

func refresh_usage() -> void:
	if telemetry_busy:
		return
	telemetry_busy = true
	var http := HTTPRequest.new()
	http.timeout = 3.0
	add_child(http)
	var error := http.request(OS.get_environment("LAMPLIGHT_URL"),PackedStringArray(["Content-Type: application/json","X-Library-Token: " + OS.get_environment("LAMPLIGHT_TOKEN")]),HTTPClient.METHOD_POST,'{"op":"ai_status"}')
	if error == OK:
		var reply: Array = await http.request_completed
		var decoded = JSON.parse_string(reply[3].get_string_from_utf8())
		if reply[0] == HTTPRequest.RESULT_SUCCESS and reply[1] == 200 and decoded is Dictionary:
			ai_status = decoded
			if is_instance_valid(usage_label):
				usage_label.text = usage_summary()
	http.queue_free()
	telemetry_busy = false

func usage_summary() -> String:
	var usage: Dictionary = ai_status.get("usage",{})
	return "AI · %s · %d requests · %d reported tokens · ~%d estimated" % [ai_status.get("config",{}).get("model","not connected"),usage.get("requests",0),int(usage.get("input_tokens",0))+int(usage.get("output_tokens",0)),usage.get("estimated_tokens",0)]

func usage_screen() -> void:
	if not await save_workshop() or not await save_writer():
		return
	screen = "usage"
	panel("Your AI usage")
	await refresh_usage()
	var usage: Dictionary = ai_status.get("usage",{})
	label_text(usage_summary(),content,18)
	label_text("%d successful · %d failed · %.1fs total response time" % [usage.get("successes",0),usage.get("failures",0),usage.get("seconds",0)],content,16)
	label_text("Provider-reported: %d input / %d output tokens" % [usage.get("input_tokens",0),usage.get("output_tokens",0)])
	label_text("Local totals across your libraries, recorded from this update onward. Estimates are separate and use characters ÷ 4 when token usage is unavailable. Failed requests can also consume provider tokens. Account balance and billed cost are not supplied by this connection.",content,14)
	label_text("Recent requests",content,20)
	var recent: Array = usage.get("recent",[]).duplicate()
	recent.reverse()
	for record in recent:
		label_text("%s · %s · %.1fs · %s" % [str(record.started).left(19).replace("T"," ")+" UTC",record.model,record.seconds,"completed" if record.success else "failed"],content,14)
	if recent.is_empty():
		label_text("No AI requests recorded yet.")

func notify(text: String) -> void:
	message_text = text
	toast_time = 6.0
	if is_instance_valid(message_label):
		message_label.text = text

func clear_ui() -> void:
	activity_label = null
	activity_bar = null
	activity_box = null
	workshop_text = null
	workshop_count = null
	workshop_next = null
	workshop_dirty = false
	word_count = null
	objective_label = null
	dialogue_label = null
	for child in ui.get_children():
		ui.remove_child(child)
		child.queue_free()
	writer_title = null
	writer_text = null
	writer_dirty = false
	letter_text = null
	hint = null
	message_label = Label.new()
	message_label.position = Vector2(26,518)
	message_label.size = Vector2(905,32)
	message_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	message_label.add_theme_font_size_override("font_size",13)
	message_label.text = message_text if toast_time > 0 else ""
	ui.add_child(message_label)
	usage_label = Label.new()
	var usage_strip := PanelContainer.new()
	usage_strip.position = Vector2(24,494)
	usage_strip.size = Vector2(912,20)
	var usage_style := StyleBoxFlat.new()
	usage_style.bg_color = Color("fff4dff0")
	usage_style.content_margin_left = 8
	usage_style.content_margin_top = 1
	usage_style.content_margin_bottom = 1
	usage_strip.add_theme_stylebox_override("panel",usage_style)
	usage_strip.mouse_filter = Control.MOUSE_FILTER_IGNORE
	ui.add_child(usage_strip)
	usage_label.add_theme_font_override("font",ThemeDB.fallback_font)
	usage_label.add_theme_font_size_override("font_size",12)
	usage_label.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	usage_label.text = usage_summary()
	usage_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	usage_strip.add_child(usage_label)

func label_text(text: String, parent: Node = content, size := 16) -> Label:
	var label := Label.new()
	label.text = text
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	label.add_theme_color_override("font_shadow_color",Color("fff7e766"))
	label.add_theme_constant_override("shadow_offset_y",1)
	label.add_theme_font_size_override("font_size",size)
	parent.add_child(label)
	return label

func button(text: String, callback: Callable, parent: Node = content) -> Button:
	var control := Button.new()
	control.text = text
	control.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	control.icon = PIXELS.icon("map" if "map" in text.to_lower() else "ai" if "ai" in text.to_lower() else "arrow")
	control.expand_icon = true
	control.add_theme_constant_override("icon_max_width",16)
	control.custom_minimum_size.y = 38
	control.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	control.pressed.connect(func():
		if not busy:
			audio_player.play("click")
			callback.call())
	parent.add_child(control)
	return control

func portrait_row(id: String, display_name: String, parent: Node = content) -> VBoxContainer:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation",18)
	parent.add_child(row)
	var path := "res://assets/portraits/%s.png" % id
	if ResourceLoader.exists(path):
		var portrait := TextureRect.new()
		portrait.texture = load(path)
		portrait.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		portrait.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		portrait.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		portrait.custom_minimum_size = Vector2(128,128)
		portrait.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
		portrait.mouse_filter = Control.MOUSE_FILTER_IGNORE
		portrait.tooltip_text = display_name
		row.add_child(portrait)
	var details := VBoxContainer.new()
	details.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	details.add_theme_constant_override("separation",8)
	row.add_child(details)
	return details

func panel(title: String) -> void:
	player.can_move = false
	player.stop()
	pending_interaction = ""
	clear_ui()
	var shade := ColorRect.new()
	shade.color = Color(0.20,0.16,0.10,0.12 if screen in ["title","dialogue","intro"] else 0.30)
	shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	ui.add_child(shade)
	var box := PanelContainer.new()
	box.position = Vector2(64,40)
	box.size = Vector2(832,450)
	if screen in ["workshop","generation","writer"]:
		box.position = Vector2(24,24)
		box.size = Vector2(912,466)
	if screen == "title":
		box.position = Vector2(48,76)
		box.size = Vector2(415,425)
	elif screen == "dialogue":
		box.position = Vector2(60,164)
		box.size = Vector2(840,342)
	elif screen == "intro":
		box.position = Vector2(70,198)
		box.size = Vector2(820,307)
	ui.add_child(box)
	if settings.get("motion",true):
		box.modulate.a = 0.0
		create_tween().tween_property(box,"modulate:a",1.0,0.15)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation",10)
	box.add_child(column)
	var heading := label_text(title,column,36 if screen == "title" else 24)
	if not settings.get("readable",false):
		heading.add_theme_font_override("font",load("res://assets/pixelify.ttf"))
	heading.add_theme_color_override("font_color",Color("536b45"))
	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	column.add_child(scroll)
	content = VBoxContainer.new()
	content.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	content.add_theme_constant_override("separation",10)
	scroll.add_child(content)
	activity_box = VBoxContainer.new()
	activity_box.visible = false
	column.add_child(activity_box)
	activity_label = label_text("",activity_box,14)
	activity_bar = ProgressBar.new()
	activity_bar.custom_minimum_size.y = 6
	activity_bar.show_percentage = false
	activity_bar.indeterminate = settings.get("motion",true)
	activity_box.add_child(activity_bar)
	if screen not in ["title","intro","draft_review"]:
		var back := button("Back to title" if slot.is_empty() or screen in ["ai_setup","benchmark"] else "Return to the room",return_to_title if screen in ["ai_setup","benchmark"] else close_panel,column)
		back.grab_focus()
	ui.move_child(message_label,ui.get_child_count()-1)

func title_screen() -> void:
	screen = "title"
	panel("L A M P L I G H T")
	
	var data := await call_api({"op":"list"})
	if not data.is_empty():
		settings = data.settings
		var status := await call_api({"op":"ai_status"})
		ai_ready = status.get("ready",false)
		apply_theme()
		var saves: Array = data.slots
		if not saves.is_empty():
			button("Continue · " + saves[0].name + " · " + str(saves[0].mode).replace("_"," ").capitalize(),func(): await load_slot(saves[0].id))
		button("New game",new_game_screen).grab_focus()
		button("Free Play",func(): await create_slot("free_play"))
		button("Saved libraries (" + str(saves.size()) + ")",func(): saves_screen(saves))
		button("Settings",settings_screen)
		button("AI · " + ("ready" if ai_ready else "setup"),ai_setup_screen)
		button("AI usage",usage_screen)
	else:
		label_text("Open this project through python run_lamplight.py --editor, then press F5.\nThe launcher keeps the Python save service alive while you work.")
		button("Retry connection",title_screen)
	button("Quit",request_quit)

func new_game_screen() -> void:
	if not ai_ready:
		await ai_setup_screen()
		return
	screen = "new"
	panel("Choose a library")
	var save_name := LineEdit.new()
	save_name.placeholder_text = "Save name (optional)"
	save_name.max_length = 60
	content.add_child(save_name)
	for mode in MODE_NAMES:
		button(MODE_NAMES[mode] + " · " + mode.replace("_"," ").capitalize(),func(): await create_slot(mode,save_name.text))
		label_text(MODE_RULES[mode],content,14)

func create_slot(mode: String, save_name := "") -> void:
	if not ai_ready:
		await ai_setup_screen()
		return
	var result := await call_api({"op":"create","mode":mode,"name":MODE_NAMES[mode] if save_name.strip_edges().is_empty() else save_name.strip_edges()})
	if not result.is_empty():
		enter_slot(result)

func saves_screen(saves: Array) -> void:
	screen = "saves"
	panel("Your saved libraries")
	for saved in saves:
		button(saved.name + " · " + str(saved.mode).replace("_"," ").capitalize(),func(): await load_slot(saved.id))
	if saves.is_empty():
		label_text("Your first library is waiting. Choose New game on the title screen.")

func load_slot(id: String) -> void:
	if not ai_ready:
		await ai_setup_screen()
		return
	var result := await call_api({"op":"load","slot":id})
	if not result.is_empty():
		enter_slot(result)

func enter_slot(result: Dictionary) -> void:
	slot = result
	room.mode = slot.mode
	room.configure(slot.place)
	saved_position = Vector2(slot.position[0],slot.position[1])
	player.position = room.safe_position(saved_position)
	document_id = "" if slot.documents.is_empty() else str(slot.documents[-1].id)
	letter_draft = ""
	notify(place_name(slot.place))
	show_room()
	if slot.mode == "campaign" and (not slot.journey.introduced or int(slot.journey.seen_era) != int(slot.campaign.era)):
		intro_screen()

func show_room() -> void:
	screen = "playing"
	clear_ui()
	room.mode = slot.mode
	room.choice = "arrival" if slot.choice.is_empty() else slot.choice
	room.era = int(slot.campaign.era) if slot.mode == "campaign" else 0
	room.compass_active = slot.mode == "campaign" and slot.journey.ready
	room.queue_redraw()
	player.can_move = true
	var bar := HBoxContainer.new()
	bar.position = Vector2(24,10)
	bar.size.x = 912
	bar.add_theme_constant_override("separation",12)
	ui.add_child(bar)
	var stats_box := PanelContainer.new()
	stats_box.custom_minimum_size = Vector2(90,38)
	bar.add_child(stats_box)
	var year_label := label_text(str(int(slot.campaign.year)) if slot.mode == "campaign" else "Lamplight",stats_box,18)
	year_label.autowrap_mode = TextServer.AUTOWRAP_OFF
	var spacer := Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	bar.add_child(spacer)
	var introduced: bool = slot.mode != "campaign" or "moved" in slot.journey.flags or not slot.conversations.is_empty()
	if introduced:
		button("Notebook",pause_screen,bar)
	button("AI usage",usage_screen,bar)
	if slot.mode != "campaign" or "studied" in slot.journey.flags:
		button("Map",map_screen,bar)
	if slot.mode == "campaign" and slot.guidance:
		var quest := PanelContainer.new()
		quest.position = Vector2(24,66)
		quest.size = Vector2(280,34)
		quest.mouse_filter = Control.MOUSE_FILTER_IGNORE
		ui.add_child(quest)
		objective_label = label_text(slot.journey.objective,quest,16)
	lesson("move")
	hint = Label.new()
	hint.position = Vector2(30,482)
	hint.size.x = 890
	hint.add_theme_font_size_override("font_size",15)
	ui.add_child(hint)
	hint.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hint.add_theme_color_override("font_shadow_color",Color("fff3d9"))
	hint.add_theme_constant_override("shadow_outline_size",2)

func _process(delta: float) -> void:
	toast_time = maxf(0.0,toast_time-delta)
	if toast_time == 0 and is_instance_valid(message_label):
		message_label.text = ""
	if busy:
		request_time += delta
		if is_instance_valid(activity_label):
			var activity: String = ai_status.get("activity","")
			activity_label.text = (request_label if activity.is_empty() else activity) + " · %ds elapsed" % int(request_time)
	if is_instance_valid(dialogue_label) and dialogue_label.visible_ratio < 1:
		dialogue_reveal += delta * 55
		dialogue_label.visible_characters = int(dialogue_reveal)
	if screen == "writer" and writer_dirty:
		writer_delay += delta
		if writer_delay >= 1.2 and not busy:
			writer_delay = 0.0
			if await save_writer():
					notify("Manuscript saved to this library.")
	if screen == "workshop" and workshop_dirty:
		workshop_delay += delta
		if workshop_delay >= 1.2 and not busy:
			workshop_delay = 0.0
			await save_workshop()
	if screen != "playing" or slot.is_empty():
		return
	if is_instance_valid(hint):
		var near: String = room.nearest(player.position)
		room.highlight = room.clicked(room.get_local_mouse_position())
		hint.text = "E / click · " + landmark_name(near) if not near.is_empty() else ""
	autosave += delta
	if autosave >= 3.0 and not busy:
		autosave = 0.0
		await save_position()

func save_position() -> bool:
	if slot.is_empty() or player.position.distance_to(saved_position) < 0.1:
		return true
	var point: Vector2 = player.position
	var result := await call_api({"op":"position","slot":slot.id,"position":[point.x,point.y]})
	if result.is_empty():
		return false
	saved_position = point
	if (not "move" in slot.get("tutorial",[]) or (slot.mode == "campaign" and not "moved" in slot.journey.flags)) and point.distance_to(Vector2(240,204)) > 16:
		var refreshed := await call_api({"op":"load","slot":slot.id})
		if not refreshed.is_empty():
			slot = refreshed
			if screen == "playing":
				show_room()
	return true

func _unhandled_input(event: InputEvent) -> void:
	if busy:
		return
	if screen == "dialogue" and event.is_action_pressed("interact") and is_instance_valid(dialogue_label):
		dialogue_label.visible_ratio = 1
		return
	if screen == "playing" and event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		var point: Vector2 = room.get_local_mouse_position()
		var target: String = room.clicked(point)
		pending_interaction = target
		if not target.is_empty():
			point = room.landmarks[target]+Vector2(0,8)
			if player.position.distance_to(room.landmarks[target]) < 30:
				await interact(target)
				return
		if not player.walk_to(point):
			pending_interaction = ""
			notify("Choose a clear patch of floor, or click a person or object.")
		get_viewport().set_input_as_handled()
		return
	if event.is_action_pressed("ui_cancel"):
		get_viewport().set_input_as_handled()
		if screen == "playing":
			pause_screen()
		else:
			await close_panel()
	elif screen == "playing" and event.is_action_pressed("journal"):
		pause_screen()
	elif screen == "playing" and event.is_action_pressed("interact"):
		await interact(room.nearest(player.position))

func interact(id: String) -> void:
	audio_player.play("page")
	match id:
		"exit": await travel("town")
		"library","workshop","garden": await travel(id)
		"computer": computer_screen()
		"author": authors_screen()
		"notice": village_notice()
		"observation": observation_screen()
		"shelf": catalog_screen()
		"writer": writer_screen()
		"post": post_screen()
		"compass":
			if slot.mode == "campaign" and not "lens" in slot.journey.flags:
				if await save_position():
					await story_action("lens")
			compass_screen()
		"margot", "miso", "ada", "elias", "jules", "noor": await talk(id)

func pause_screen() -> void:
	screen = "paused"
	panel("The library journal")
	if slot.mode == "campaign":
		label_text("%d coins · %d paper · Day %d" % [slot.campaign.money,slot.campaign.paper,slot.campaign.day],content,17)
		for step in slot.journey.steps:
			label_text(("✓  " if step.done else "◇  ") + step.title,content,15)
		button("The time recorder & route home",compass_screen)
		button("Recall this chapter",intro_screen)
	if slot.guidance:
		var objective := "Choose a book or begin a manuscript."
		if slot.mode == "campaign":
			objective = slot.journey.hint
		label_text(objective)
	button("Browse the shelf",catalog_screen)
	button("My manuscripts",writer_screen)
	button("Village map & people",map_screen)
	button("My computer · library desk",computer_screen)
	if slot.mode == "campaign" and not slot.campaign.publications.is_empty() and slot.choice.is_empty():
		button("Restore a shared reading table",func(): await choose("shared"))
		button("Restore patron-supported study equipment",func(): await choose("patron"))
	button("Hide guidance" if slot.guidance else "Show guidance",func():
		var result := await call_api({"op":"guidance","slot":slot.id,"enabled":not slot.guidance})
		if not result.is_empty():
			slot = result
			pause_screen())
	button("Settings",settings_screen)
	button("AI setup",ai_setup_screen)
	button("Replay tutorial",func():
		var result := await call_api({"op":"tutorial","slot":slot.id,"lesson":"replay"})
		if not result.is_empty():
			slot = result
			show_room())
	button("Save and return to title",return_to_title)

func talk(resident: String) -> void:
	var result := await call_api({"op":"talk","slot":slot.id,"resident":resident})
	if result.is_empty():
		return
	slot = result
	screen = "dialogue"
	panel(resident_name(resident) + "  /  " + {"margot":"Custodian","ada":"Lens maker","elias":"Teacher","jules":"Printer","noor":"Bookbinder","miso":"Resident cat"}[resident])
	var words: String = DIALOGUE[resident]
	if resident == "margot" and slot.mode != "campaign":
		words = "Make yourself at home. Pick a book from the shelf or open a new manuscript at the desk. We can stay with a question as long as it needs."
	if slot.mode == "campaign" and int(slot.campaign.era) > 0:
		words = {"margot":"You match the portrait in our family journal. I used to think it was a story.\n\n" + slot.journey.clue,"ada":"My predecessors kept your observations. I was born in this century; I know you only through their words. Let us check the new calibration source together.","elias":"You look at this room as though someone is missing. There are names in our ledger that may answer your questions. Your next report can preserve what they taught you.","jules":"The press has changed since your last visit. The bargain is still fair: write a sourced commission and I will pay for it. In this era, include a delivered letter as well.","noor":"Someone kept your seat for fifty years. You do not owe us a promise to stay. But write down what you remember before you leave again.","miso":"A different cat occupies the same warm patch. He inspects your compass, unimpressed. The household has kept this tradition too."}[resident]
	if resident == "margot" and not slot.choice.is_empty():
		words += "\n\n" + ("The shared table keeps new readers coming. Your decision made that possible." if slot.choice == "shared" else "The patron's instruments survive. We still argue over who gets to use them.")
	var line := portrait_row(resident,resident_name(resident))
	dialogue_label = label_text(words,line,16)
	dialogue_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	dialogue_label.custom_minimum_size.y = 132
	dialogue_label.visible_characters = 0
	dialogue_reveal = 0
	var replies := HBoxContainer.new()
	replies.add_theme_constant_override("separation",10)
	content.add_child(replies)
	button("Reveal · E",func(): dialogue_label.visible_ratio = 1,replies)
	if resident == "margot" and slot.mode == "campaign":
		button("Where should I start?",pause_screen,replies)
	if resident != "miso":
		button("Find the reading circle",map_screen,replies)

func catalog_screen() -> void:
	screen = "catalog"
	panel("The period shelf" if slot.mode == "campaign" else "The reading collection")
	lesson("shelf")
	if slot.mode != "campaign":
		label_text("Uncached books download when opened.",content,13)
	var search := LineEdit.new()
	search.placeholder_text = "Search title or author"
	content.add_child(search)
	var results := VBoxContainer.new()
	content.add_child(results)
	var refresh := func(query: String):
		for child in results.get_children():
			results.remove_child(child)
			child.queue_free()
		var count := 0
		for book in slot.books:
			if not query.is_empty() and not (str(book.title) + str(book.authors)).to_lower().contains(query.to_lower()):
				continue
			var title: String = str(book.title)
			if slot.mode == "campaign" and int(book.id) == int(slot.journey.trial.book):
				title = "FEATURED  /  " + title
			button(title,func(): await read_book(int(book.id)),results)
			count += 1
			if count >= 40:
				label_text("Showing 40 matches. Refine the search to find another title.",results,13)
				break
	search.text_changed.connect(refresh)
	refresh.call("")
	search.grab_focus()

func read_book(id: int) -> void:
	if slot.get("writing",{}).has("id") and not await save_workshop():
		return
	var result := await call_api({"op":"book","slot":slot.id,"book":id})
	if result.is_empty():
		return
	screen = "reader"
	panel(result.title)
	var text := TextEdit.new()
	text.text = result.text
	text.editable = false
	text.wrap_mode = TextEdit.LINE_WRAPPING_BOUNDARY
	text.custom_minimum_size.y = 160
	content.add_child(text)
	if slot.mode == "campaign":
		label_text("Study-note reference: [B%s]" % absi(id))
		if not slot.campaign.studied.any(func(value): return int(value) == id):
			button("Study this summary · 1 day",func():
				await campaign_action({"action":"study","book":id})
				await read_book(id))
		else:
			label_text("Studied. Rereading is free.")
			button("Check my understanding · no day cost",func(): await quiz_screen(id))
		button("Discuss in the garden",map_screen)
	if slot.get("writing",{}).has("id") and not slot.writing.has("document"):
		button("Return to my writing step",workshop_screen)

func writer_screen() -> void:
	screen = "writer"
	panel("The writing desk")
	lesson("writer")
	button("Write step by step with Margot",func():
		if await save_writer():
			generation_screen("article"))
	var document: Dictionary = {}
	for candidate in slot.documents:
		if candidate.id == document_id:
			document = candidate
	writer_title = LineEdit.new()
	writer_title.placeholder_text = "Manuscript title"
	writer_title.text = document.get("title","Untitled manuscript")
	content.add_child(writer_title)
	writer_text = TextEdit.new()
	writer_text.placeholder_text = "Begin with something you noticed..."
	writer_text.text = document.get("text","")
	writer_text.wrap_mode = TextEdit.LINE_WRAPPING_BOUNDARY
	writer_text.add_theme_font_override("font",ThemeDB.fallback_font)
	writer_text.custom_minimum_size.y = 185
	content.add_child(writer_text)
	writer_title.text_changed.connect(func(_text): mark_writer())
	writer_text.text_changed.connect(mark_writer)
	word_count = label_text("",content,12)
	update_word_count()
	var writer_actions := HBoxContainer.new()
	writer_actions.add_theme_constant_override("separation",10)
	content.add_child(writer_actions)
	button("Save",func():
		if await save_writer():
			notify("Manuscript saved to this library."),writer_actions)
	if slot.mode == "campaign":
		var submission_options := VBoxContainer.new()
		submission_options.visible = false
		button("Submission",func(): submission_options.visible = not submission_options.visible,writer_actions)
		content.add_child(submission_options)
		var editor_content := content
		content = submission_options
		button("File this field report · record an anchor",func():
			if await save_writer():
				await story_action("report",{"document":document_id}))
		label_text("%d words · %d sources · %d paper + 2 days → %d coins." % [slot.campaign.commission.words,slot.campaign.commission.sources,slot.campaign.commission.paper,slot.campaign.commission.payment],content,13)
		button("Insert studied-source references",func():
			for id in slot.campaign.studied:
				writer_text.text += "\n[B%s] " % absi(int(id)) + str(campaign_book_title(int(id)))
			mark_writer())
		button("Submit this commission",func():
			if await save_writer():
				var cited: Array = slot.campaign.studied.filter(func(id): return writer_text.text.contains("[B%d]" % absi(int(id))))
				var submission := {"action":"publish","document":document_id,"books":cited}
				for letter in slot.campaign.letters:
					if letter.delivered and int(letter.era) == int(slot.campaign.era) and writer_text.text.contains("[L" + letter.id + "]"):
						submission["letter"] = letter.id
				await campaign_action(submission))
		for letter in slot.campaign.letters:
			if letter.delivered and int(letter.era) == int(slot.campaign.era):
				button("Cite delivered letter · " + letter.name,func():
					writer_text.text += "\n[L" + letter.id + "] " + letter.name
					mark_writer())
		content = editor_content
	button("New",func():
		if await save_writer():
			document_id = ""
			writer_screen(),writer_actions)
	for saved in slot.documents:
		button("Open · " + saved.title,func():
			if await save_writer():
				document_id = saved.id
				writer_screen())

func campaign_book_title(id: int) -> String:
	for book in slot.books:
		if int(book.id) == id:
			return book.title
	return "Study note"

func mark_writer() -> void:
	update_word_count()
	writer_dirty = true
	writer_delay = 0.0
	notify("Saving your manuscript…")

func update_word_count() -> void:
	if is_instance_valid(word_count) and is_instance_valid(writer_text):
		word_count.text = "%d words · Autosave enabled" % word_pattern.search_all(writer_text.text).size()
		if slot.mode == "campaign":
			word_count.text += " · Report: 45 / Commission: %d" % int(slot.campaign.commission.words)

func save_writer() -> bool:
	if not is_instance_valid(writer_text):
		return true
	var title := writer_title.text
	var text := writer_text.text
	for saved in slot.documents:
		if saved.id == document_id and saved.title == title and saved.text == text:
			writer_dirty = false
			return true
	var result := await call_api({"op":"document","slot":slot.id,"document":document_id,"title":title,"text":text})
	if result.is_empty():
		return false
	slot = result
	if document_id.is_empty():
		document_id = str(slot.documents[-1].id)
	writer_dirty = title != writer_title.text or text != writer_text.text
	return not writer_dirty

func post_screen() -> void:
	screen = "post"
	panel("Letters and quiet days")
	if slot.mode != "campaign":
		label_text("Historical correspondence belongs to Campaign. In this library, your reading and writing have no era deadlines.")
		return
	lesson("post")
	label_text("Post: %s coins + 1 paper" % (4+int(slot.campaign.era)),content,14)
	letter_text = TextEdit.new()
	letter_text.placeholder_text = "Ask a question about a studied observation (20–3000 characters)."
	letter_text.text = letter_draft
	letter_text.custom_minimum_size.y = 100
	letter_text.wrap_mode = TextEdit.LINE_WRAPPING_BOUNDARY
	letter_text.text_changed.connect(func(): letter_draft = letter_text.text)
	content.add_child(letter_text)
	for figure in slot.campaign.figures:
		var recipient := portrait_row(figure.id,figure.name)
		button("Send to " + figure.name,func():
			var result := await call_api({"op":"campaign","slot":slot.id,"action":"letter","figure":figure.id,"text":letter_draft,"language":"en"})
			if not result.is_empty():
				slot = result
				letter_draft = ""
				post_screen(),recipient)
	button("Wait · 1 day",func(): await campaign_action({"action":"wait"}))
	button("Copying shift · 1 day · earn %s coins and 1 paper" % (12+3*int(slot.campaign.era)),func(): await campaign_action({"action":"work"}))
	for letter in slot.campaign.letters:
		label_text(letter.name + (" · Delivered\n" + letter.answer if letter.delivered else " · Arrives day " + str(int(letter.due))))

func campaign_action(data: Dictionary) -> void:
	data.merge({"op":"campaign","slot":slot.id})
	var result := await call_api(data)
	if not result.is_empty():
		slot = result
		audio_player.play("anchor")
		notify("Saved. " + slot.journey.objective)
		show_room()
		if data.get("action") == "jump":
			audio_player.play("travel")
			intro_screen()
			if settings.get("motion",true):
				var veil := ColorRect.new()
				veil.color = Color("0c1a35")
				veil.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
				veil.mouse_filter = Control.MOUSE_FILTER_IGNORE
				ui.add_child(veil)
				var crossing := create_tween()
				crossing.tween_property(veil,"modulate:a",0.0,1.2)
				crossing.tween_callback(veil.queue_free)

func choose(choice: String) -> void:
	screen = "choice"
	panel("A lasting place in the library")
	label_text("A shared table invites readers to compare observations. This choice will be remembered in later correspondence." if choice == "shared" else "Patron-supported instruments improve the study. Questions of access will be remembered in later correspondence.")
	label_text("Choose deliberately. This opening decision does not lock a future route.")
	button("Confirm this improvement",func():
		var result := await call_api({"op":"choice","slot":slot.id,"choice":choice})
		if not result.is_empty():
			slot = result
			show_room())

func settings_screen() -> void:
	screen = "settings"
	panel("Sound & reading comfort")
	var readable := CheckButton.new()
	readable.text = "Use a larger, readable interface font"
	readable.button_pressed = settings.get("readable",false)
	content.add_child(readable)
	var sliders := {}
	for setting in ["music","effects"]:
		label_text("Background music" if setting == "music" else "Sound effects",content,15)
		var slider := HSlider.new()
		slider.min_value = 0
		slider.max_value = 1
		slider.step = 0.05
		slider.value = settings.get(setting,0.45 if setting == "music" else 0.65)
		slider.custom_minimum_size = Vector2(400,28)
		content.add_child(slider)
		sliders[setting] = slider
	var motion := CheckButton.new()
	motion.text = "Animate rain, light and motes (off reduces motion)"
	motion.button_pressed = settings.get("motion",true)
	content.add_child(motion)
	button("Apply",func():
		var result := await call_api({"op":"settings","readable":readable.button_pressed,"music":sliders.music.value,"effects":sliders.effects.value,"motion":motion.button_pressed})
		if not result.is_empty():
			settings = result.settings
			apply_theme()
			await close_panel())
	button("AI companion setup",ai_setup_screen)
	label_text("Music: Mystical Piano — Indieteur (CC0). Original sound effects.\nControls: WASD / arrows or click to move. Shift to run. E to interact. J / Esc to pause.\nMusic and effects can each be muted by moving their slider fully left.",content,13)

func resident_name(id: String) -> String:
	if slot.get("mode") == "campaign":
		if id == "margot":
			return slot.journey.custodian
		if int(slot.campaign.era) > 0:
			return {"ada":"The researcher","elias":"The teacher","jules":"The publisher","noor":"The first reader","miso":"The house cat"}.get(id,id.capitalize())
	return id.capitalize()

func landmark_name(id: String) -> String:
	return {"shelf":"Book summaries","writer":"Writing desk","post":"Post table","compass":"Time recorder","computer":"My computer","exit":"Town square","library":"Library door","workshop":"Print shop door","garden":"Garden path","author":"Reading circle","notice":"Village noticeboard","observation":"Observe the garden"}.get(id,resident_name(id))

func place_name(id: String) -> String:
	return {"library":"The library","town":"Town square","workshop":"The print shop","garden":"Reading garden"}.get(id,id)

func travel(destination: String) -> void:
	if not await save_writer() or not await save_position():
		return
	var result := await call_api({"op":"travel","slot":slot.id,"destination":destination})
	if not result.is_empty():
		enter_slot(result)
		notify(place_name(destination))
		if settings.get("motion",true):
			room.modulate.a = 0.25
			create_tween().tween_property(room,"modulate:a",1.0,0.3)

func map_screen() -> void:
	screen = "map"
	panel("The village · " + place_name(slot.place))
	lesson("map")
	var map := Control.new()
	map.set_script(load("res://village_map.gd"))
	map.current = slot.place
	map.visited = slot.visited
	map.motion = settings.get("motion",true)
	map.destination_selected.connect(travel_route)
	content.add_child(map)

func travel_route(destination: String) -> void:
	if destination == slot.place:
		return
	if slot.place != "town" and destination != "town":
		await travel("town")
		if slot.place != "town":
			return
	await travel(destination)

func village_notice() -> void:
	screen = "notice"
	panel("Noticeboard")
	label_text(slot.journey.objective if slot.mode == "campaign" else "An idea worth sharing starts with a book.",content,22)
	button("Explore the village",map_screen)

func observation_screen() -> void:
	screen = "observation"
	panel("A small observation")
	label_text("The flowers near the wall are taller than those beside the path. What could account for the difference?",content,20)
	label_text("Sunlight, water, soil, age, and damage are possible explanations. One afternoon cannot distinguish them. A good notebook separates observation from interpretation.",content,17)
	button("Keep an observation note",func():
		var result := await call_api({"op":"document","slot":slot.id,"title":"Garden observation","text":"Observation: flowers near the wall are taller than those beside the path.\nPossible explanations: sunlight, water, soil, age or damage.\nNext check: compare the conditions over several days.\nUncertainty: this is one observation; it does not establish a cause."})
		if not result.is_empty():
			slot = result
			document_id = slot.documents[-1].id
			notify("Observation saved. Develop it in your notebook or at the computer."))

func quiz_button(prefix: String) -> Button:
	for control in content.find_children("*","Button",true,false):
		if control.text.begins_with(prefix):
			return control
	return null

func press_quiz(prefix: String) -> void:
	quiz_button(prefix).pressed.emit()
	while busy:
		await get_tree().process_frame
	await get_tree().process_frame

func slot_mastered(data: Dictionary, id: int) -> bool:
	return data.get("learning",{}).get(str(id),{}).get("mastered",false)

func quiz_screen(id: int) -> void:
	var book := await call_api({"op":"book","slot":slot.id,"book":id})
	if book.is_empty():
		return
	screen = "quiz"
	panel("Check your understanding")
	var quiz: Dictionary = book.quiz
	var progress := "Mastered · practice question" if quiz.mastered else "Question %d of %d" % [int(quiz.index) + 1, int(quiz.total)]
	label_text(book.title + " · " + progress,content,14)
	label_text(quiz.question,content,21)
	var feedback := label_text("Choose an answer. Retry freely; each learning reward is earned once.",content,14)
	var answers: Array[Button] = []
	var after := HBoxContainer.new()
	for i in range(quiz.options.size()):
		answers.append(button("ABC"[i] + ".  " + quiz.options[i],func():
			var result := await call_api({"op":"quiz","slot":slot.id,"book":id,"answer":i,"question":quiz.index})
			if not result.is_empty():
				slot = result.slot
				feedback.text = result.feedback + "\n\n" + result.explanation
				audio_player.play("anchor" if result.correct else "page")
				if result.correct:
					for answer in answers:
						answer.disabled = true
				if result.get("next",false):
					button("Next question",func(): await quiz_screen(id),after).grab_focus()
					after.move_child(after.get_child(-1),0)))
	content.add_child(HSeparator.new())
	after.add_theme_constant_override("separation",10)
	content.add_child(after)
	button("Review the summary",func(): await read_book(id),after)
	button("Discuss in the garden",map_screen,after)

func authors_screen() -> void:
	screen = "authors"
	panel("The garden reading circle")
	if slot.mode != "campaign":
		label_text("Historical thinker discussions belong to Campaign. Ada and Elias are here for an ordinary conversation.")
		return
	label_text("Meet the ideas of intellectuals active in this era. These encounters are educational fiction, not authentic conversations or quotations.",content,15)
	for figure in slot.campaign.figures:
		var details := portrait_row(figure.id,figure.name)
		label_text(figure.name,details,22)
		var studied: bool = slot.campaign.studied.any(func(i): return int(i) == int(figure.book))
		if not studied:
			button("Read their summary first",func(): await read_book(int(figure.book)),details)
		else:
			for topic in ["claim","evidence","challenge"]:
				button({"claim":"What is the central claim?","evidence":"What evidence supports it?","challenge":"What is the strongest objection?"}[topic],func(): await discuss_figure(figure,topic),details)

func discuss_figure(figure: Dictionary, topic: String) -> void:
	var result := await call_api({"op":"discuss","slot":slot.id,"figure":figure.id,"topic":topic})
	if result.is_empty():
		return
	slot = result.slot
	screen = "discussion"
	panel(result.name + " · " + topic.capitalize())
	var details := portrait_row(figure.id,result.name)
	label_text(result.text,details,19)
	label_text(result.simulation,content,12)
	button("Explore another question",authors_screen)
	button("Make a note of this exchange",func():
		var saved := await call_api({"op":"document","slot":slot.id,"title":figure.name + " · " + topic,"text":result.text + "\n[B%d]" % absi(int(figure.book))})
		if not saved.is_empty():
			slot = saved
			document_id = slot.documents[-1].id
			notify("Discussion note saved. Add your own response in the notebook."))

func computer_screen() -> void:
	screen = "computer"
	panel("My computer")
	if slot.place != "library":
		label_text("Use your laptop at the library desk.",content,20)
		button("Find the library",map_screen)
		return
	lesson("computer")
	label_text("One idea, one step at a time",content,24)
	label_text("Shape a question, find evidence, plan, draft and revise. Margot reviews each step; you decide when to move on.",content,16)
	if slot.get("writing",{}).has("id") and not slot.writing.has("document"):
		button("Resume · " + slot.writing.title,workshop_screen)
	
	var types := HBoxContainer.new()
	types.add_theme_constant_override("separation",10)
	content.add_child(types)
	button("Study notes",func(): generation_screen("study_notes"),types)
	button("Article",func(): generation_screen("article"),types)
	button("Letter",func(): generation_screen("letter"),types)
	button("Open my manuscripts",writer_screen)
	label_text("Discuss an idea with a village reader",content,18)
	var readers := HBoxContainer.new()
	content.add_child(readers)
	for resident in ["margot","ada","elias","jules","noor"]:
		button(resident_name(resident),func(): ai_chat_screen(resident),readers)
	if slot.mode == "campaign":
		label_text("Correspond with a thinker from this era",content,18)
		for figure in slot.campaign.figures:
			if slot.campaign.studied.any(func(i): return int(i) == int(figure.book)):
				button("Ask " + figure.name + " · AI correspondence",func(): ai_chat_screen("margot",figure.id))
	button("Set up / test my AI",ai_setup_screen)
	

func generation_screen(kind: String) -> void:
	if slot.get("writing",{}).has("id") and not slot.writing.has("document"):
		workshop_screen()
		return
	screen = "generation"
	panel("Begin a writing workshop · " + kind.replace("_"," ").capitalize())
	label_text("Question → Evidence → Outline → Draft → Revision",content,18)
	var brief := LineEdit.new()
	brief.placeholder_text = "Give this piece a working title or question"
	brief.max_length = 300
	content.add_child(brief)
	label_text("Pick 1–8 sources to work with. Margot receives these excerpts and your workshop steps when you ask for a review.",content,13)
	var selected := {}
	var eligible: Array = []
	for book in slot.books:
		if slot.mode == "campaign" and not slot.campaign.studied.any(func(i): return int(i) == int(book.id)):
			continue
		eligible.append(book)
	if eligible.is_empty():
		label_text("Study a summary to use it as a source.")
		button("Browse summaries",catalog_screen)
		return
	selected[int(eligible[0].id)] = true
	var search := LineEdit.new()
	search.placeholder_text = "Find a source by title or author"
	content.add_child(search)
	var sources := VBoxContainer.new()
	content.add_child(sources)
	var refresh := func(query: String):
		for child in sources.get_children():
			sources.remove_child(child)
			child.queue_free()
		var count := 0
		for book in eligible:
			if not query.is_empty() and not (str(book.title)+str(book.authors)).to_lower().contains(query.to_lower()):
				continue
			var pick := CheckBox.new()
			pick.text = book.title
			pick.clip_text = true
			pick.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
			pick.tooltip_text = book.title
			pick.button_pressed = selected.get(int(book.id),false)
			pick.toggled.connect(func(value): selected[int(book.id)] = value)
			sources.add_child(pick)
			count += 1
			if count == 40:
				label_text("First 40 matches. Search to narrow.",sources,12)
				break
	search.text_changed.connect(refresh)
	refresh.call("")
	button("Begin · shape my question",func():
		var ids: Array = []
		for id in selected:
			if selected[id]:
				ids.append(id)
		var result := await call_api({"op":"writing_start","slot":slot.id,"kind":kind,"title":brief.text,"books":ids})
		if not result.is_empty():
			slot = result
			workshop_screen(),content.get_parent().get_parent())

func workshop_screen() -> void:
	screen = "workshop"
	panel(slot.writing.title)
	var flow: Dictionary = slot.writing
	var index := int(flow.stage)
	var step: Dictionary = flow.steps[index]
	var stages := HBoxContainer.new()
	content.add_child(stages)
	for i in range(flow.steps.size()):
		var title: Control
		if i < index:
			title = button("✓ " + flow.steps[i].name,func(): await revisit_workshop(i),stages)
			title.tooltip_text = "Revisit this step. Your text is kept; this and later steps will need fresh reviews."
		else:
			title = label_text("%d %s" % [i+1,flow.steps[i].name],stages,16)
		title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		title.add_theme_color_override("font_color",Color("52754b") if i <= index else Color("897b67"))
	var progress := ProgressBar.new()
	progress.max_value = 5
	progress.value = index
	progress.show_percentage = false
	progress.custom_minimum_size.y = 7
	content.add_child(progress)
	label_text("Step %d of 5 · %s" % [index+1,step.instruction],content,16)
	var columns := HBoxContainer.new()
	columns.add_theme_constant_override("separation",20)
	content.add_child(columns)
	var paper := VBoxContainer.new()
	paper.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	paper.size_flags_stretch_ratio = 1.8
	columns.add_child(paper)
	workshop_text = TextEdit.new()
	workshop_text.wrap_mode = TextEdit.LINE_WRAPPING_BOUNDARY
	workshop_text.add_theme_font_override("font",ThemeDB.fallback_font)
	workshop_text.add_theme_font_size_override("font_size",16)
	workshop_text.custom_minimum_size.y = 170
	workshop_text.text = step.text
	workshop_text.placeholder_text = step.instruction
	paper.add_child(workshop_text)
	workshop_count = label_text("%d words · Saved locally · %d/5 steps approved" % [word_pattern.search_all(step.text).size(),index],paper,12)
	var companion := VBoxContainer.new()
	companion.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	columns.add_child(companion)
	label_text("MARGOT · YOUR EDITOR",companion,18)
	var review: Dictionary = step.review
	label_text("Ready for your approval" if review.get("ready",false) else "Let's work on this step",companion,14)
	var feedback := RichTextLabel.new()
	feedback.custom_minimum_size.y = 132
	feedback.size_flags_vertical = Control.SIZE_EXPAND_FILL
	feedback.add_theme_font_override("normal_font",ThemeDB.fallback_font)
	feedback.add_theme_color_override("default_color",Color("44382f"))
	feedback.add_theme_font_size_override("normal_font_size",15)
	feedback.text = review.get("feedback","Write your first thought, then ask me to review it. If you're stuck, I can offer an example for this step.")
	feedback.bbcode_enabled = false
	feedback.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	companion.add_child(feedback)
	if settings.get("motion",true) and not review.is_empty():
		feedback.visible_ratio = 0
		create_tween().tween_property(feedback,"visible_ratio",1.0,minf(1.5,feedback.text.length()/100.0))
	var actions := HBoxContainer.new()
	actions.add_theme_constant_override("separation",10)
	content.add_child(actions)
	button("Ask Margot to review",review_workshop,actions)
	if not str(review.get("suggestion","")).is_empty():
		button("See example",func():
			var example := AcceptDialog.new()
			example.title = "Margot's example · adapt it in your own words"
			var example_text := TextEdit.new()
			example_text.text = review.suggestion
			example_text.editable = false
			example_text.wrap_mode = TextEdit.LINE_WRAPPING_BOUNDARY
			example.add_child(example_text)
			example.get_ok_button().text = "Use as a starting point"
			example.add_cancel_button("Keep my text")
			example.confirmed.connect(func():
				if is_instance_valid(workshop_text):
					workshop_text.select_all()
					workshop_text.insert_text_at_caret(review.suggestion)
				example.queue_free())
			example.canceled.connect(func(): example.queue_free())
			add_child(example)
			example.popup_centered(Vector2i(660,400)),actions)
	workshop_next = button("Keep finished manuscript" if index == 4 else "Approve & continue",advance_workshop,actions)
	workshop_next.disabled = not review.get("ready",false)
	workshop_text.text_changed.connect(func():
		workshop_dirty = true
		workshop_delay = 0.0
		workshop_next.disabled = true
		workshop_count.text = "%d words · Saving… · Review needed after edits" % word_pattern.search_all(workshop_text.text).size())
	var reference_notes := VBoxContainer.new()
	reference_notes.visible = false
	button("Sources & approved notes",func(): reference_notes.visible = not reference_notes.visible)
	content.add_child(reference_notes)
	for id in flow.books:
		button("[B%d] %s · read source" % [absi(int(id)),campaign_book_title(int(id))],func():
			if await save_workshop():
				await read_book(int(id)),reference_notes)
	for i in range(index):
		label_text(flow.steps[i].name + "\n" + flow.steps[i].text,reference_notes,14)

func save_workshop() -> bool:
	if not is_instance_valid(workshop_text) or not workshop_dirty:
		return true
	var text := workshop_text.text
	var flow: Dictionary = slot.writing
	var result := await call_api({"op":"writing_save","slot":slot.id,"writing":flow.id,"stage":flow.stage,"text":text})
	if result.is_empty():
		return false
	slot = result
	workshop_dirty = workshop_text.text != text
	workshop_count.text = "%d words · Saved locally · Ask for a fresh review" % word_pattern.search_all(text).size()
	return not workshop_dirty

func review_workshop() -> void:
	if not await save_workshop():
		return
	var flow: Dictionary = slot.writing
	var result := await call_api({"op":"ai_coach","slot":slot.id,"writing":flow.id,"stage":flow.stage})
	if not result.is_empty():
		slot = result.slot
		workshop_screen()

func advance_workshop() -> void:
	if not await save_workshop():
		return
	var flow: Dictionary = slot.writing
	var result := await call_api({"op":"writing_advance","slot":slot.id,"writing":flow.id,"stage":flow.stage})
	if not result.is_empty():
		slot = result
		if slot.writing.has("document"):
			document_id = slot.writing.document
			audio_player.play("click")
			notify("Five steps complete. Your manuscript is saved; submission is a separate decision.")
			writer_screen()
		else:
			workshop_screen()

func revisit_workshop(target: int) -> void:
	if not await save_workshop():
		return
	var flow: Dictionary = slot.writing
	var result := await call_api({"op":"writing_revisit","slot":slot.id,"writing":flow.id,"stage":flow.stage,"target":target})
	if not result.is_empty():
		slot = result
		workshop_screen()

func intro_screen(page := 0) -> void:
	screen = "intro"
	if slot.campaign.completed:
		panel("2026  /  The light you left behind")
		label_text("You catch your sister's hand before the archive lamp falls. Rain taps the glass. A moment has passed.\n\nIn your coat are seven reports, a letter in Margot's hand, and the names of people who spent their lives making your return possible. They stayed in their own years. You carried their words home.",content,19)
		button("Keep their stories · return to your journal",show_room)
		return
	panel(("PROLOGUE" if int(slot.campaign.era) == 0 else "CROSSING %d" % int(slot.campaign.era)) + "  /  " + slot.journey.title)
	if page == 0:
		label_text(slot.journey.introduction,content,20)
		button("Remember what happened  →",func(): intro_screen(1)).grab_focus()
	else:
		label_text("YOUR WAY HOME",content,13).add_theme_color_override("font_color",Color("88dacd"))
		label_text("Your laptop still works. There is a book on the shelf and someone waiting to meet you.",content,20)
		button("Step into the room · begin tutorial",func():
			await story_action("intro")
			show_room()).grab_focus()
		

func story_action(action: String, extra: Dictionary = {}) -> bool:
	var data := {"op":"story","slot":slot.id,"action":action}
	data.merge(extra)
	var result := await call_api(data)
	if result.is_empty():
		return false
	slot = result
	audio_player.play("anchor")
	notify("Anchor recorded." if action == "report" else "")
	if screen == "playing":
		show_room()
	return true

func compass_screen() -> void:
	if slot.is_empty() or slot.mode != "campaign":
		return
	screen = "compass"
	panel("The time recorder  /  %d of 7 chapters documented" % int(slot.journey.anchors))
	lesson("compass")
	if slot.campaign.completed:
		label_text("Home · 2026. Your seven anchors and the people who made them possible remain in your journal.",content,20)
		button("Read the ending again",intro_screen)
		return
	label_text("1630  →  1680  →  1730  →  1780  →  1830  →  1880  →  1930  →  HOME",content,14).add_theme_color_override("font_color",Color("91ddcf"))
	
	label_text(slot.journey.clue,content,18)
	var flags: Array = slot.journey.flags
	if not "lens" in flags:
		label_text("Your repair kit is below the library window. Approach it and press E, or click it.")
	elif not "studied" in flags:
		label_text("Lens recovered. Study a note from the current era at the shelf to find a calibration method.")
	elif not "aligned" in flags:
		label_text("CALIBRATION  /  " + slot.journey.trial.question,content,16)
		for option in slot.journey.trial.options:
			button(option.text,func():
				if await story_action("aligned",{"answer":option.id}):
					compass_screen())
	elif not "report" in flags:
		label_text("Aligned. Record what you observed, how someone could check it, and what remains uncertain. Save 45 words and a studied [Bnumber] marker at the desk.")
		button("Open the field notebook",writer_screen)
		if not document_id.is_empty():
			button("File the selected manuscript as this era's field report",func():
				if await story_action("report",{"document":document_id}):
					compass_screen())
	else:
		label_text("ANCHOR RECORDED  /  Field report reward received once for this era.",content,14)
	if not "mastered" in flags:
		button("Practice this era's learning questions",func(): await quiz_screen(int(slot.journey.trial.book)))
	if not "discussed" in flags:
		label_text("Before leaving, discuss a studied work at the garden reading circle.",content,14)
	var needed: Dictionary = slot.campaign.requirements
	for key in needed:
		var current: int = int(slot.campaign.era_publications if key == "publications" else slot.campaign[key])
		label_text(("✓  " if current >= int(needed[key]) else "◇  ") + key.capitalize() + ": %d / %d" % [current,int(needed[key])],content,14)
	label_text("Crossing consumes the coins and paper shown above. Prestige and knowledge stay with you. Finish correspondence in transit before leaving.",content,13)
	if slot.journey.ready and slot.campaign.can_jump:
		button("Prepare the crossing →",func():
			screen = "crossing"
			panel("Leave this century?")
			label_text("The people you know will remain here. Their lives will continue while you cross. Your manuscripts and the room's lasting choice will travel forward as records.\n\n" + ("The next light is home." if int(slot.campaign.era) == 6 else "Say your goodbyes, then activate the compass."),content,20)
			button("Activate · return to 2026" if int(slot.campaign.era) == 6 else "Activate · cross fifty years",func(): await campaign_action({"action":"jump"})))
	button("Review objectives in the journal",pause_screen)

func ai_setup_screen() -> void:
	screen = "ai_setup"
	panel("Connect your companion")
	var status := await call_api({"op":"ai_status"})
	if status.is_empty():
		return
	ai_ready = status.ready
	var config: Dictionary = status.config
	label_text("3 AI checks: sources, history and game rules. Pass 80/100 to play.",content,14)
	var provider_row := HBoxContainer.new()
	content.add_child(provider_row)
	var providers := OptionButton.new()
	for name in ["Ollama · local, no API fee", "Groq · free tier", "OpenRouter · select a free model", "Custom provider"]:
		providers.add_item(name)
	providers.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	provider_row.add_child(providers)
	var endpoint := LineEdit.new()
	endpoint.placeholder_text = "API base URL"
	endpoint.text = config.get("url","http://localhost:11434/v1")
	content.add_child(endpoint)
	var model := LineEdit.new()
	model.placeholder_text = "Exact model ID"
	model.text = config.get("model","")
	model.max_length = 160
	content.add_child(model)
	var key := LineEdit.new()
	key.secret = true
	key.placeholder_text = "Key loaded · leave blank to keep" if status.key_present else "API key · session only"
	key.max_length = 500
	content.add_child(key)
	var urls := ["http://localhost:11434/v1","https://api.groq.com/openai/v1","https://openrouter.ai/api/v1",""]
	var links := ["https://docs.ollama.com/quickstart","https://console.groq.com/docs/rate-limits","https://openrouter.ai/collections/free-models",""]
	providers.selected = urls.find(endpoint.text) if endpoint.text in urls else 3
	providers.item_selected.connect(func(index):
		endpoint.text = urls[index]
		model.text = ""
		key.text = ""
		key.placeholder_text = "API key · session only")
	button("Setup ↗",func():
		if not links[providers.selected].is_empty():
			OS.shell_open(links[providers.selected]),provider_row)
	label_text("Fictional test data only · up to 90s · provider rates apply",content,13)
	button("Connect & benchmark",func():
		var saved := await call_api({"op":"ai_config","url":endpoint.text.strip_edges(),"model":model.text.strip_edges(),"key":key.text,"enabled":true})
		if saved.is_empty():
			return
		key.text = ""
		ai_ready = false
		screen = "benchmark"
		panel("Companion trial")
		label_text("Source grounding · Period knowledge · Gameplay reasoning",content,16)
		var result := await call_api({"op":"ai_test"})
		if result.is_empty():
			label_text(message_text,content,16)
			button("Retry setup",ai_setup_screen)
			return
		ai_ready = result.passed
		benchmark_result(result),content.get_parent().get_parent())
	if not status.benchmark.is_empty():
		button("Last result · %d/100%s" % [status.benchmark.score," · ready" if ai_ready else " · retest required"],func(): benchmark_result(status.benchmark))
	if ai_ready:
		button("Continue",close_panel)

func benchmark_result(result: Dictionary) -> void:
	screen = "benchmark"
	panel("%d / 100 · %s" % [result.score,result.rating])
	var meter := ProgressBar.new()
	meter.value = result.score
	meter.custom_minimum_size.y = 20
	content.add_child(meter)
	for task in result.cases:
		label_text("%s  ·  %d/100  ·  %.1fs" % [task.name,task.score,task.seconds],content,18)
		var missed: Array = []
		for criterion in task.checks:
			if not task.checks[criterion]:
				missed.append(criterion.replace("_"," "))
		if not missed.is_empty():
			label_text("Retry: " + ", ".join(missed),content,13)
	label_text("%.1fs · Pass: 80 overall, 75 per task, all critical rules." % result.seconds,content,14)
	button("Play" if ai_ready else "Retry / change model",close_panel if ai_ready else ai_setup_screen)

func lesson(id: String) -> void:
	if slot.is_empty() or not slot.guidance or id in slot.get("tutorial",[]):
		return
	var tip := PanelContainer.new()
	if screen == "playing":
		tip.position = Vector2(24,420)
		tip.size = Vector2(780,44)
		ui.add_child(tip)
	else:
		content.add_child(tip)
	var row := HBoxContainer.new()
	tip.add_child(row)
	var text := label_text(LESSONS[id],row,15)
	text.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	button("Got it",func():
		var result := await call_api({"op":"tutorial","slot":slot.id,"lesson":id})
		if not result.is_empty():
			slot = result
			tip.queue_free(),row)

func ai_chat_screen(resident: String, figure_id := "") -> void:
	screen = "ai_chat"
	var name := resident_name(resident)
	if not figure_id.is_empty():
		for figure in slot.campaign.figures:
			if figure.id == figure_id:
				name = figure.name
	panel("Computer correspondence · " + name)
	var details := portrait_row(figure_id if not figure_id.is_empty() else resident,name)
	label_text(name,details,22)
	label_text("AI educational fiction · check against your sources.",details,13)
	var prompt := TextEdit.new()
	prompt.placeholder_text = "Ask about a studied observation, or paste a passage you want feedback on…"
	prompt.custom_minimum_size.y = 110
	prompt.wrap_mode = TextEdit.LINE_WRAPPING_BOUNDARY
	details.add_child(prompt)
	var answer := label_text("",content,16)
	button("Send question to my configured AI",func():
		answer.text = "Waiting for your model…"
		var data := {"op":"ai_ask","slot":slot.id,"resident":resident,"text":prompt.text}
		if not figure_id.is_empty():
			data["figure"] = figure_id
		var result := await call_api(data)
		answer.text = result.text if not result.is_empty() else message_text)
	button("Configure AI / fix connection",ai_setup_screen)
	button("Return to computer",computer_screen)

func close_panel() -> void:
	if screen == "draft_review":
		notify("Keep the generated draft or choose Discard before leaving this review.")
		return
	if busy or not await save_workshop() or not await save_writer():
		return
	if slot.is_empty():
		await title_screen()
	elif not ai_ready:
		await ai_setup_screen()
	else:
		show_room()

func return_to_title() -> void:
	if busy or not await save_workshop() or not await save_writer() or not await save_position():
		return
	slot = {}
	document_id = ""
	await title_screen()

func request_quit() -> void:
	if screen == "draft_review":
		notify("Keep the generated draft or choose Discard before quitting.")
		return
	if busy:
		notify("Please wait for the current save before closing.")
		return
	if await save_workshop() and await save_writer() and await save_position():
		await finish_game()

func finish_game() -> void:
	player.can_move = false
	audio_player.shutdown()
	await get_tree().process_frame
	await get_tree().create_timer(0.08).timeout
	get_tree().quit()

func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_CLOSE_REQUEST:
		request_quit()
	if is_instance_valid(player):
		if what == NOTIFICATION_APPLICATION_FOCUS_OUT:
			player.can_move = false
		elif what == NOTIFICATION_APPLICATION_FOCUS_IN:
			player.can_move = screen == "playing" and not busy

func check(condition: bool, message: String) -> void:
	if not condition:
		push_error("FAIL: " + message)
		get_tree().quit(1)
		assert(condition,message)

func run_check() -> void:
	check(connected,"Engine must connect to the real local service")
	check(ui.theme.get_stylebox("focus","Button").bg_color.a == 0.0,"Keyboard focus must not cover button hover")
	check(content.get_children().any(func(child): return child is Button and child.text == "Free Play"),"Title offers Free Play")
	var blocked := await call_api({"op":"create","mode":"campaign","name":"Must be blocked"})
	check(blocked.is_empty(),"Unqualified game creation is blocked by service")
	await call_api({"op":"ai_config","url":"http://localhost:11434/v1","model":"test-chat","key":"","enabled":true})
	var qualification := await call_api({"op":"ai_test"})
	check(qualification.get("passed",false),"Three-task AI qualification passes through HTTP")
	ai_ready = true
	await create_slot("campaign")
	var campaign_id: String = slot.id
	check(slot.mode == "campaign" and int(slot.campaign.year) == 1630,"Campaign creation")
	check(screen == "intro","New campaign introduces the accident")
	check(await story_action("intro"),"Introduction persists")
	show_room()
	check(player.walk_to(Vector2(284,204)),"Native mouse route exists")
	player.can_move = true
	for frame in range(110):
		await get_tree().physics_frame
	check(player.position.distance_to(Vector2(284,204)) < 6,"Click route moves the character")
	check(await save_position(),"Tutorial movement persists")
	check("moved" in slot.journey.flags,"Movement completes tutorial step")
	check(room.route(Vector2(240,204),Vector2(400,140)).is_empty(),"Mouse movement rejects furniture")
	check(room.route(Vector2(350,146),Vector2(430,184)).size() > 0,"Mouse route goes around furniture")
	await talk("margot")
	check(screen == "dialogue" and not player.can_move,"Dialogue pauses movement")
	check(content.find_children("*","TextureRect",true,false)[0].texture.resource_path.ends_with("/margot.png"),"Resident dialogue shows its dedicated portrait")
	await close_panel()
	check(screen == "playing","Dialogue returns to room")
	await read_book(-1)
	check(screen == "reader","Native reader loads period notes")
	await campaign_action({"action":"study","book":-1})
	check(slot.campaign.studied.any(func(value): return int(value) == -1),"Successful study persists: " + message_text)
	await quiz_screen(-1)
	check(screen == "quiz","Learning check opens")
	check(content.get_child(0).text.ends_with("Question 1 of 2"),"Learning check shows its progress")
	await press_quiz("B.")
	check(not slot_mastered(slot,-1) and quiz_button("Next question") != null,"First answer leaves one question to master")
	await press_quiz("Next question")
	check(content.get_child(0).text.ends_with("Question 2 of 2"),"Next question opens the second check")
	await press_quiz("B.")
	check(slot_mastered(slot,-1) and quiz_button("A.").disabled,"Both answers master the source")
	await travel("town")
	map_screen()
	check(content.get_child(0).get_script() == load("res://village_map.gd"),"Map renders native geography")
	show_room()
	check(slot.place == "town" and room.cast.noor.visible and not room.cast.margot.visible,"Town has its own residents")
	await travel("workshop")
	check(room.cast.jules.visible,"Printer is in the workshop")
	await travel_route("garden")
	check(slot.place == "garden","Map routes between buildings through the square")
	check(room.cast.ada.visible and room.visitor.visible,"Garden hosts readers and period thinker")
	check(is_equal_approx(room.cast.ada.scale.y*room.characters.get_height()/3,52.0),"Residents use the proportional world scale")
	check(room.clicked(room.cast.ada.position) == "ada","Enlarged residents have matching click targets")
	authors_screen()
	check(content.find_children("*","TextureRect",true,false)[0].texture.resource_path.ends_with("/galileo.png"),"Reading circle shows the current thinker")
	await discuss_figure(slot.campaign.figures[0],"evidence")
	check(screen == "discussion","Period discussion works")
	check(content.find_children("*","TextureRect",true,false)[0].texture.resource_path.ends_with("/galileo.png"),"Debate reply keeps the same thinker portrait")
	await travel("town")
	await travel("library")
	computer_screen()
	check(screen == "computer","AI work belongs to the computer")
	for control in content.find_children("*","Button",true,false):
		if control.text == resident_name("ada"):
			control.pressed.emit()
			break
	check(screen == "ai_chat","Computer reader selection opens correspondence")
	check(content.find_children("*","TextureRect",true,false)[0].texture.resource_path.ends_with("/ada.png"),"AI correspondence shows the selected reader")
	var fallback := portrait_row("missing-portrait","Reader")
	check(fallback.get_parent().get_child_count() == 1,"Missing artwork leaves conversation text usable")
	generation_screen("article")
	check(screen == "generation","Computer can prepare a sourced article")
	show_room()
	await get_tree().process_frame
	for child in ui.get_children():
		if child is HBoxContainer:
			check(child.size.y < 60,"Minimal HUD does not wrap into tall columns")
	player.position = Vector2(250,143)
	check(await save_position(),"Compass approach saves")
	await interact("compass")
	check("lens" in slot.journey.flags and screen == "compass","Recover lens through native interaction")
	check(await story_action("aligned",{"answer":"repeat"}),"Observation calibrates compass")
	writer_screen()
	writer_title.text = "Native manuscript"
	writer_text.text = "A saved observation. [B1]\n<script>This remains plain text.</script>"
	check(await save_writer(),"Native editor saves")
	var saved_id := document_id
	await close_panel()
	player.position = Vector2(250,220)
	check(await save_position(),"Position saves")
	await return_to_title()
	await create_slot("modern")
	check(slot.documents.is_empty() and slot.campaign == null,"Modern has isolated documents and progression")
	await return_to_title()
	for child in content.get_children():
		if child is Button and child.text == "Free Play":
			child.pressed.emit()
			break
	while busy:
		await get_tree().process_frame
	check(slot.mode == "free_play","Title Free Play button opens the mode")
	check(slot.documents.is_empty() and slot.books.size() >= 1200,"Free Play has an open built-in catalogue")
	await return_to_title()
	await load_slot(campaign_id)
	check(slot.documents.size() == 1 and slot.documents[0].id == saved_id,"Campaign manuscript survives mode switches")
	check(player.position == Vector2(250,220),"Saved position resumes")
	check("margot" in slot.conversations and slot.campaign.studied.any(func(value): return int(value) == -1),"Guidance evidence survives reload")
	await get_tree().physics_frame
	var wall_test: Transform2D = player.global_transform
	wall_test.origin = room.to_global(Vector2(240,125))
	check(player.test_move(wall_test,Vector2(0,-60)),"Native physics blocks the upper wall")
	pause_screen()
	check(not player.can_move,"Pause freezes movement")
	var workshop := await call_api({"op":"writing_start","slot":slot.id,"kind":"article","title":"Guided observation","books":[-1]})
	slot = workshop
	workshop_screen()
	check(screen == "workshop" and workshop_next.disabled,"Writing starts at a review-gated question")
	for stage in range(5):
		workshop_text.text = "Repeated observations support a limited claim; compare the conditions before extending it. [B1]"
		workshop_text.text_changed.emit()
		check(await save_workshop(),"Workshop saves each step")
		await review_workshop()
		check(not workshop_next.disabled,"Companion review unlocks approval")
		if stage == 0:
			for control in content.find_children("*","Button",true,false):
				if control.text == "See example":
					control.pressed.emit()
					break
			await get_tree().process_frame
			var examples := get_children().filter(func(child): return child is AcceptDialog)
			check(examples.size() == 1,"Optional example opens in a dialog")
			examples[0].confirmed.emit()
			await get_tree().process_frame
			check(workshop_dirty and workshop_next.disabled,"Using an example requires reviewing the resulting text")
			await review_workshop()
		await advance_workshop()
	check(screen == "writer" and slot.documents.size() == 2,"Five reviewed steps create one saved manuscript")
	await usage_screen()
	check(ai_status.usage.requests >= 8,"Native usage includes benchmark and writing reviews")
	ai_setup_screen()
	await get_tree().create_timer(0.15).timeout
	check(screen == "ai_setup","AI setup opens without a provider call")
	check(audio_player.music.stream != null and audio_player.sounds.has("step"),"Music and effects loaded")
	print("PASS: cozy village travel, distributed residents, learning checks, discussions, computer, tutorial, mouse movement, audio and isolated saves")
	await finish_game()

func capture(name: String) -> void:
	await get_tree().create_timer(0.4).timeout
	await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var path := OS.get_environment("LAMPLIGHT_CAPTURE_DIR").path_join(name + ".png")
	var error := get_viewport().get_texture().get_image().save_png(path)
	check(error == OK,"Save rendered screenshot")

func capture_screens() -> void:
	await ai_setup_screen()
	await capture("ai-required-1280")
	await call_api({"op":"ai_config","url":"http://localhost:11434/v1","model":"test-chat","key":"","enabled":true})
	var qualification := await call_api({"op":"ai_test"})
	ai_ready = qualification.get("passed",false)
	benchmark_result(qualification)
	await capture("benchmark-1280")
	await title_screen()
	await capture("title-1280")
	new_game_screen()
	await capture("modes-1280")
	await create_slot("campaign")
	await capture("intro-1280")
	await story_action("intro")
	show_room()
	await capture("room-1280")
	map_screen()
	await capture("map-1280")
	show_room()
	await talk("margot")
	dialogue_label.visible_ratio = 1
	await capture("dialogue-1280")
	await talk("miso")
	dialogue_label.visible_ratio = 1
	await capture("miso-1280")
	await close_panel()
	writer_screen()
	writer_title.text = "An observation by the window"
	writer_text.text = "One evening of observation is a beginning, not a conclusion.\n\nWhat would another reader need in order to check the claim? [B1]"
	mark_writer()
	await capture("writer-1280")
	check(await save_writer(),"Capture manuscript save")
	await close_panel()
	await campaign_action({"action":"study","book":-1})
	await quiz_screen(-1)
	await capture("learning-1280")
	computer_screen()
	await capture("computer-1280")
	ai_chat_screen("margot","galileo")
	await capture("correspondence-1280")
	post_screen()
	await capture("post-1280")
	generation_screen("article")
	await capture("generation-1280")
	var workshop := await call_api({"op":"writing_start","slot":slot.id,"kind":"article","title":"What can a repeated observation tell us?","books":[-1]})
	slot = workshop
	workshop_screen()
	workshop_text.text = "What can repeated observations establish about the moon? My tentative claim is that a changing pattern gives us grounds for comparison, while a single evening leaves too much uncertain."
	workshop_text.text_changed.emit()
	await save_workshop()
	await review_workshop()
	await get_tree().create_timer(1.6).timeout
	await capture("workshop-question-1280")
	await advance_workshop()
	await capture("workshop-evidence-1280")
	settings["motion"] = false
	settings["readable"] = true
	apply_theme()
	get_window().size = Vector2i(960,540)
	workshop_screen()
	check(not activity_bar.indeterminate,"Reduced motion uses a static activity indicator")
	await capture("workshop-readable-960")
	settings["motion"] = true
	settings["readable"] = false
	apply_theme()
	get_window().size = Vector2i(1280,720)
	await usage_screen()
	await capture("usage-1280")
	await close_panel()
	get_window().size = Vector2i(1920,1080)
	await capture("room-1920")
	await travel("town")
	await capture("town-1920")
	await travel("workshop")
	await capture("workshop-1920")
	await travel("town")
	await travel("garden")
	await capture("garden-1920")
	authors_screen()
	await capture("thinker-1920")
	await discuss_figure(slot.campaign.figures[0],"evidence")
	await capture("debate-1920")
	get_window().size = Vector2i(1280,720)
	authors_screen()
	await capture("thinker-1280")
	await discuss_figure(slot.campaign.figures[0],"challenge")
	await capture("debate-1280")
	# Render every bundled portrait together without changing campaign eligibility.
	get_window().size = Vector2i(1920,1080)
	var portrait_groups := {"residents":["margot","ada","elias","jules","noor","miso"],"thinkers":["galileo","boyle","swift","franklin","shelley","darwin","curie"]}
	for group in portrait_groups:
		panel("Portrait review · " + group)
		var gallery := GridContainer.new()
		gallery.columns = 4
		content.add_child(gallery)
		for id in portrait_groups[group]:
			var card := VBoxContainer.new()
			gallery.add_child(card)
			portrait_row(id,id.capitalize(),card)
			label_text(id.capitalize(),card,13)
		await capture("portraits-" + group + "-1920")
	await return_to_title()
	await create_slot("modern")
	await capture("modern-1920")
	await ai_setup_screen()
	await capture("ai-setup-1920")
	print("PASS: native Godot screenshots written to " + OS.get_environment("LAMPLIGHT_CAPTURE_DIR"))
	await finish_game()
