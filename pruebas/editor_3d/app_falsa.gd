extends Control
## «App» mínima para probar páginas sueltas sin catálogo ni red.
var api: EstudioApi
var avisos: Array = []
func _init() -> void:
	api = EstudioApi.new()
	add_child(api)
func pantalla_completa(_a: bool) -> void:
	pass
func mostrar_aviso(t: String, _s := 3.0) -> void:
	avisos.append(t)
	print("AVISO ", t)
func atras() -> bool:
	return true
func ir(_n: String, _d := {}, _r := false) -> void:
	pass
