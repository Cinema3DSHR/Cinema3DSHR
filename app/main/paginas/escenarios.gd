extends Pagina
## ESCENARIOS: biblioteca de escenarios reutilizables, con su versión liviana para el visor 3D.

var _col: VBoxContainer

func abrir(_d: Dictionary) -> void:
	_col = columna_desplazable()
	al_actualizar_catalogo()

func al_actualizar_catalogo() -> void:
	limpiar(_col)
	var lista: Array = api.catalogo.get("escenarios", [])
	_col.add_child(titulo("Escenarios", "Escenarios reutilizables del estudio. Tocá uno para recorrerlo en 3D."))
	if lista.is_empty():
		_col.add_child(Tema.etiqueta("Todavía no hay escenarios publicados. Pedile uno a Claude: «Creá una mansión moderna de lujo».", 20, Tema.TEXTO2, true))
		return
	var g := GridContainer.new()
	g.columns = 3
	for e in lista:
		var p := Tema.panel(12)
		p.custom_minimum_size.x = 380
		var v := VBoxContainer.new()
		p.add_child(v)
		v.add_child(Tema.imagen(api, e.get("portada"), Vector2(356, 200)))
		v.add_child(Tema.etiqueta(str(e.get("nombre", "")), 20, Tema.TEXTO, true))
		v.add_child(Tema.etiqueta(", ".join(e.get("etiquetas", []).slice(0, 6)), 15, Tema.TEXTO2, true))
		var vis = e.get("visor")
		var b := Tema.boton("🧊  RECORRER EN 3D" + ("  (%s)" % Tema.bytes(int(vis.get("bytes", 0))) if vis is Dictionary else ""),
			func(): app.ir("visor", {"archivo": vis, "titulo": e.get("nombre", "")}), "azul", 17)
		b.disabled = not (vis is Dictionary)
		v.add_child(b)
		g.add_child(p)
	_col.add_child(g)
