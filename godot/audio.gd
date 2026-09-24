extends Node

var music: AudioStreamPlayer
var effects: AudioStreamPlayer
var step: AudioStreamPlayer
var ambience: AudioStreamPlayer
var sounds := {}

func tone(frequency: float, duration: float, noise := false) -> AudioStreamWAV:
	var wave := AudioStreamWAV.new()
	wave.format = AudioStreamWAV.FORMAT_16_BITS
	wave.mix_rate = 22050
	var bytes := PackedByteArray()
	bytes.resize(int(22050*duration)*2)
	var random := RandomNumberGenerator.new()
	random.seed = 72
	for i in range(bytes.size()/2):
		var t := float(i)/22050.0
		var envelope := sin(minf(t*80,PI/2))*exp(-t*8/duration)
		var value := (sin(TAU*frequency*t)*0.7+sin(TAU*frequency*2*t)*0.2) * envelope
		if noise:
			value = (random.randf()*2-1)*envelope*0.4
		bytes.encode_s16(i*2,int(value*14000))
	wave.data = bytes
	return wave

func _ready() -> void:
	music = AudioStreamPlayer.new()
	music.stream = load("res://assets/mystical-piano.ogg")
	music.stream.loop = true
	add_child(music)
	music.play()
	effects = AudioStreamPlayer.new()
	step = AudioStreamPlayer.new()
	add_child(effects)
	add_child(step)
	ambience = AudioStreamPlayer.new()
	var rain := AudioStreamWAV.new()
	rain.format = AudioStreamWAV.FORMAT_16_BITS
	rain.mix_rate = 22050
	rain.loop_mode = AudioStreamWAV.LOOP_FORWARD
	rain.loop_end = 22050*4
	var rain_data := PackedByteArray()
	rain_data.resize(rain.loop_end*2)
	var random := RandomNumberGenerator.new()
	random.seed = 1930
	var filtered := 0.0
	for i in range(rain.loop_end):
		var white := random.randf()*2-1
		filtered = filtered*0.93+white*0.07
		rain_data.encode_s16(i*2,int((white*0.12+filtered*0.65)*10000))
	rain.data = rain_data
	ambience.stream = rain
	add_child(ambience)
	ambience.play()
	sounds = {"click":tone(660,0.14),"page":tone(350,0.2,true),"step":tone(130,0.1,true),"anchor":tone(880,1.5),"travel":tone(220,2.5)}
	apply({})

func apply(settings: Dictionary) -> void:
	var volume := float(settings.get("music",0.45))
	music.volume_db = linear_to_db(maxf(0.0001,volume))*1.5-8
	music.stream_paused = volume == 0
	effects.volume_db = linear_to_db(maxf(0.0001,float(settings.get("effects",0.65))))-8
	step.volume_db = effects.volume_db-9
	ambience.volume_db = effects.volume_db-12
	ambience.stream_paused = float(settings.get("effects",0.65)) == 0

func play(id: String) -> void:
	var target := step if id == "step" else effects
	target.stream = sounds[id]
	target.pitch_scale = randf_range(0.9,1.1) if id == "step" else 1.0
	target.play()

func shutdown() -> void:
	for target in [music,effects,step,ambience]:
		target.stop()
		target.stream = null
	sounds.clear()
