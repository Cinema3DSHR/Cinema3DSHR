extends Pagina
## PELÍCULAS: biblioteca de producciones (películas, cortos, series, escenas sueltas).

var _col: VBoxContainer

func abrir(_d: Dictionary) -> void:
	_col = columna_desplazable()
	al_actualizar_catalogo()

func al_actualizar_catalogo() -> void:
	limpiar(_col)
	var prods: Array = api.catalogo.get("producciones", [])
	_col.add_child(titulo("Películas", "%d producción(es) en el estudio" % prods.size()))
	if prods.is_empty():
		_col.add_child(Tema.etiqueta("Todavía no hay producciones. Pedile una a Claude: «Creá una película sobre…».", 20, Tema.TEXTO2, true))
		return
	var g := GridContainer.new()
	g.columns = 3
	g.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	for p in prods:
		g.add_child(tarjeta_produccion(p, 380))
	_col.add_child(g)
