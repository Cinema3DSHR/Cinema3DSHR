## Hace que una planta importada (GLB con animación de viento) se mueva sola, en bucle, con su propio ritmo.
extends Node3D
@export var velocidad := 1.0
@export var desfase := 0.0
func _ready() -> void:
	var ap := _buscar(self)
	if ap == null:
		return
	var lista := ap.get_animation_list()
	for n in lista:
		if n == "RESET":
			continue
		var an := ap.get_animation(n)
		an.loop_mode = Animation.LOOP_LINEAR
		ap.speed_scale = velocidad
		ap.play(n)
		ap.seek(desfase * an.length, true)
		break
func _buscar(n: Node) -> AnimationPlayer:
	for c in n.get_children():
		if c is AnimationPlayer:
			return c
		var r := _buscar(c)
		if r != null:
			return r
	return null
