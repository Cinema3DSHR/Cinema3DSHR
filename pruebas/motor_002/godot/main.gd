extends Node3D
## Medición: la escena de la mansión (GLB liviano del visor) en Godot, ruta Movie Maker. t_inicio = segundo de la toma.
var anim: AnimationPlayer
var t0_ms := 0
var frames := 0
const T_INICIO := 13.0   # toma t04_grua
const CAM := "CAM_t04_grua"
func _ready() -> void:
	var doc := GLTFDocument.new(); var st := GLTFState.new()
	doc.append_from_file("res://visor.glb", st)
	var m: Node = doc.generate_scene(st); add_child(m)
	var env := Environment.new(); env.background_mode = Environment.BG_COLOR; env.background_color = Color(0.02, 0.025, 0.04)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR; env.ambient_light_color = Color(0.35, 0.38, 0.5); env.ambient_light_energy = 0.35
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	var we := WorldEnvironment.new(); we.environment = env; add_child(we)
	var luces := 0
	for n in m.find_children("*", "Light3D", true, false):
		luces += 1
		n.shadow_enabled = false
		if n is OmniLight3D: n.light_energy = 0.8; n.omni_range = 6.0
		elif n is SpotLight3D: n.light_energy = 1.5; n.spot_range = 18.0
		elif n is DirectionalLight3D: n.light_energy = 0.25
	var cam: Camera3D = m.find_child(CAM, true, false); cam.current = true
	anim = m.find_children("*", "AnimationPlayer", true, false)[0]
	var todo := Animation.new()
	for nombre in anim.get_animation_list():
		var a := anim.get_animation(nombre); todo.length = maxf(todo.length, a.length)
		for i in a.get_track_count(): a.copy_track(i, todo)
	var lib := AnimationLibrary.new(); lib.add_animation("e", todo); anim.add_animation_library("est", lib)
	anim.play("est/e"); anim.seek(T_INICIO, true)
	print("LUCES ", luces, " CAM ", cam.name, " ANIM ", todo.length)
	t0_ms = Time.get_ticks_msec()
func _process(_d: float) -> void:
	frames += 1
	if frames == 3: t0_ms = Time.get_ticks_msec(); frames = 0   # ignora los 3 primeros (carga de shaders)
	elif frames == 60:
		var s := (Time.get_ticks_msec() - t0_ms) / 1000.0
		print("MEDIDA 60 fotogramas en ", s, " s -> ", s / 60.0, " s/fotograma  memoria_estatica_MB ", OS.get_static_memory_usage() / 1048576.0)
		get_viewport().get_texture().get_image().save_png("res://godot_t04.png")
		get_tree().quit()
