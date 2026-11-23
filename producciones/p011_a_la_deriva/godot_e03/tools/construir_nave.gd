## Construye la NAVE ÚNICA: primero guarda cada pieza como escena propia (res://piezas/*.tscn) y después arma res://nave.tscn
## instanciándolas. Corregir una pieza (o su lugar) se corrige para TODO el capítulo.
## Uso: godot --headless --path . --script res://tools/construir_nave.gd
extends SceneTree
const L = preload("res://tools/lib.gd")
const PZ = preload("res://tools/piezas.gd")
const P2 = preload("res://tools/piezas2.gd")
const A := "res://assets/pantallas/"
const ALTO := 3.2
var raiz: Node3D
var muros := {}

func _initialize() -> void:
	DirAccess.make_dir_recursive_absolute("res://piezas")
	var lista := {
		"silla_comando": PZ.silla_comando(), "silla_comedor": PZ.silla_comedor(), "mesa_comedor": PZ.mesa_comedor(), "consola_mando": PZ.consola_mando(),
		"pantalla_pared": PZ.pantalla_pared(), "cama": PZ.cama(), "escritorio": PZ.escritorio(), "armario": PZ.armario(), "estante": PZ.estante(),
		"incubadora": PZ.incubadora(), "luminaria_techo": PZ.luminaria_techo(), "marco_puerta": PZ.marco_puerta(), "holoproyector": PZ.holoproyector(),
		"nucleo_eva": PZ.nucleo_eva(), "ventanal": PZ.ventanal(), "consola_central": PZ.consola_central(), "camilla": PZ.camilla(),
		"mesita": mesita(), "florero": florero(), "heladera_vidrio": P2.heladera_vidrio(), "expendedora": P2.expendedora(), "estanteria_alimentos": P2.estanteria_alimentos(), "jardinera": P2.jardinera(), "canal_agua": P2.canal_agua(16.0), "rack_servidores": P2.rack_servidores(), "costilla": P2.costilla(), "caja_electrica": P2.caja_electrica(), "umbral": P2.umbral(), "casco": PZ.casco(), "barra_cocina": PZ.barra_cocina(), "microscopio": PZ.microscopio(), "terrario": PZ.terrario(), "soporte_suero": PZ.soporte_suero()}
	for k in lista:
		L.guardar_pieza(lista[k], "res://piezas/%s.tscn" % k)
	armar_nave()
	var ps := PackedScene.new()
	ps.pack(raiz)
	ResourceSaver.save(ps, "res://nave.tscn")
	print("NAVE_OK piezas=", lista.size())
	quit()

# ───────────────────────── piezas pequeñas propias de esta escena
func mesita() -> Node3D:
	var r := Node3D.new()
	r.name = "mesita"
	L.caja(r, "Cuerpo", Vector3(0, 0.27, 0), Vector3(0.5, 0.54, 0.45), L.mat(Color(0.82, 0.85, 0.88), 0.3, 0.35))
	L.caja(r, "Luz", Vector3(0, 0.12, -0.226), Vector3(0.4, 0.012, 0.005), L.mat(Color(0.1, 0.8, 1.0), 0, 0.3, Color(0.1, 0.8, 1.0), 2.2))
	return r

func florero() -> Node3D:
	var r := Node3D.new()
	r.name = "florero"
	L.cil(r, "Vaso", Vector3(0, 0.09, 0), 0.04, 0.18, L.mat(Color(0.7, 0.9, 1.0), 0, 0.05, Color(0, 0, 0), 0.0, 0.35), Vector3.ZERO, 20)
	L.cil(r, "Tallo", Vector3(0, 0.26, 0), 0.006, 0.22, L.mat(Color(0.25, 0.6, 0.25)), Vector3.ZERO, 8)
	for i in 6:
		var a := i * TAU / 6.0
		L.esf(r, "Petalo%d" % i, Vector3(cos(a) * 0.035, 0.38, sin(a) * 0.035), 0.03, L.mat(Color(0.98, 0.97, 0.9), 0, 0.5, Color(1, 0.95, 0.8), 0.3), Vector3(1, 0.5, 1))
	L.esf(r, "Centro", Vector3(0, 0.385, 0), 0.02, L.mat(Color(1.0, 0.75, 0.2), 0, 0.5))
	return r

# ───────────────────────── ayudas de colocación
func inst(padre: Node, pieza: String, nombre: String, pos: Vector3, mira_a: Vector3, esc := 1.0) -> Node3D:
	var n: Node3D = load("res://piezas/%s.tscn" % pieza).instantiate()
	n.name = nombre
	n.position = pos
	var d := Vector3(mira_a.x - pos.x, 0, mira_a.z - pos.z)
	n.rotation.y = atan2(-d.x, -d.z)            # el frente (−Z) apunta hacia mira_a
	n.scale = Vector3(esc, esc, esc)
	n.set_meta("mira_a", mira_a)
	n.set_meta("pieza", pieza)
	padre.add_child(n)
	return n

func sh3d(padre: Node, glb: String, nombre: String, pos: Vector3, mira_a: Vector3, esc := 1.0) -> Node3D:
	## Sweet Home: su FRENTE mira hacia +Z en el GLB → se gira medio giro para dejarlo con el frente en −Z como las demás piezas.
	var n: Node3D = Node3D.new()
	n.name = nombre
	n.position = pos
	var d := Vector3(mira_a.x - pos.x, 0, mira_a.z - pos.z)
	n.rotation.y = atan2(-d.x, -d.z)
	n.scale = Vector3(esc, esc, esc)
	n.set_meta("mira_a", mira_a)
	n.set_meta("pieza", glb)
	var g: Node3D = load("res://assets/sh3d/%s.glb" % glb).instantiate()
	g.rotation.y = PI
	n.add_child(g)
	padre.add_child(n)
	return n

func planta(padre: Node, glb: String, nombre: String, pos: Vector3, giro_deg := 0.0, esc := 1.0, desfase := 0.0, hundida := false) -> Node3D:
	## Planta real (modelada en Blender) con su viento en bucle: envoltorio con el script planta_viva.gd + el GLB.
	var w := Node3D.new()
	w.name = nombre
	w.position = pos
	w.rotation_degrees = Vector3(0, giro_deg, 0)
	w.scale = Vector3(esc, esc, esc)
	w.set_script(load("res://tools/planta_viva.gd"))
	w.set("desfase", desfase)
	w.set("velocidad", 0.8 + fmod(desfase * 7.0, 0.5))
	w.set_meta("pieza", glb)
	if hundida:
		w.set_meta("hundida", true)
	var g: Node3D = load("res://assets/plantas/%s.glb" % glb).instantiate()
	g.name = "Modelo"
	w.add_child(g)
	padre.add_child(w)
	return w

func decorar(s: Node, x0: float, x1: float, z0: float, z1: float, lado_pasillo: int, ritmo := 2.4) -> void:
	## Estructura de nave: cuadernas en los muros laterales y de fondo, ductos y bandeja de cables en el techo.
	var tub := L.mat(Color(0.14, 0.16, 0.20), 0.75, 0.35)
	var anillo := L.mat(Color(0.1, 0.8, 1.0), 0, 0.3, Color(0.1, 0.8, 1.0), 2.2)
	var n := int((x1 - x0) / ritmo)
	for i in range(1, n):
		var x := x0 + i * (x1 - x0) / n
		var zf := z1 if lado_pasillo < 0 else z0
		var giro := Vector3(x, 0, zf + (-5 if lado_pasillo < 0 else 5))
		if absf(x - (x0 + x1) / 2) > 2.2:
			inst(s, "costilla", "CostillaFondo_%d" % i, Vector3(x, 0, zf + (0.1 if lado_pasillo > 0 else -0.1) * -1.0), giro)
	var m := int(absf(z1 - z0) / ritmo)
	for j in range(1, m):
		var z := z0 + j * (z1 - z0) / m
		inst(s, "costilla", "CostillaO_%d" % j, Vector3(x0 + 0.1, 0, z), Vector3(x1, 0, z))
		inst(s, "costilla", "CostillaE_%d" % j, Vector3(x1 - 0.1, 0, z), Vector3(x0, 0, z))
	for z in [z0 + 0.25, z1 - 0.25]:
		L.cil(s, "Ducto", Vector3((x0 + x1) / 2, ALTO - 0.18, z), 0.07, x1 - x0 - 0.4, tub, Vector3(0, 0, 90), 14)
		for k in 6:
			L.cil(s, "DuctoAro", Vector3(x0 + 0.5 + k * (x1 - x0 - 1.0) / 5.0, ALTO - 0.18, z), 0.076, 0.025, anillo, Vector3(0, 0, 90), 14)
	L.caja(s, "BandejaCables", Vector3((x0 + x1) / 2, ALTO - 0.1, (z0 + z1) / 2), Vector3(0.4, 0.06, absf(z1 - z0) - 0.6), tub)

func pared_x(p: Node, nom: String, z: float, x0: float, x1: float, huecos: Array, m: Material, y0 := 0.0, y1 := ALTO) -> void:
	## Muro paralelo a X en z, con huecos [[x_centro, ancho], …] (puertas de 2,2 m).
	var tramos := [[x0, x1]]
	for h in huecos:
		var nt := []
		for t in tramos:
			var a: float = h[0] - h[1] / 2.0
			var b: float = h[0] + h[1] / 2.0
			if b <= t[0] or a >= t[1]:
				nt.append(t)
			else:
				if a > t[0]:
					nt.append([t[0], a])
				if b < t[1]:
					nt.append([b, t[1]])
				L.caja_uv(p, "%s_dintel" % nom, Vector3((a + b) / 2, (2.2 + y1) / 2, z), Vector3(b - a, y1 - 2.2, 0.2), m)
		tramos = nt
	var i := 0
	for t in tramos:
		L.caja_uv(p, "%s_%d" % [nom, i], Vector3((t[0] + t[1]) / 2, (y0 + y1) / 2, z), Vector3(t[1] - t[0], y1 - y0, 0.2), m)
		i += 1

func pared_z(p: Node, nom: String, x: float, z0: float, z1: float, huecos: Array, m: Material) -> void:
	var tramos := [[z0, z1]]
	for h in huecos:
		var nt := []
		for t in tramos:
			var a: float = h[0] - h[1] / 2.0
			var b: float = h[0] + h[1] / 2.0
			if b <= t[0] or a >= t[1]:
				nt.append(t)
			else:
				if a > t[0]:
					nt.append([t[0], a])
				if b < t[1]:
					nt.append([b, t[1]])
				L.caja_uv(p, "%s_dintel" % nom, Vector3(x, (2.2 + ALTO) / 2, (a + b) / 2), Vector3(0.2, ALTO - 2.2, b - a), m)
		tramos = nt
	var i := 0
	for t in tramos:
		L.caja_uv(p, "%s_%d" % [nom, i], Vector3(x, ALTO / 2, (t[0] + t[1]) / 2), Vector3(0.2, ALTO, t[1] - t[0]), m)
		i += 1

func recinto(nombre: String, x0: float, x1: float, z0: float, z1: float, mm: Material, ms: Material, mt: Material) -> Node3D:
	var s := L.nodo(raiz, nombre)
	L.caja_uv(s, "Suelo", Vector3((x0 + x1) / 2, -0.05, (z0 + z1) / 2), Vector3(x1 - x0, 0.1, z1 - z0), ms, 2.0)
	L.caja(s, "Techo", Vector3((x0 + x1) / 2, ALTO + 0.05, (z0 + z1) / 2), Vector3(x1 - x0, 0.1, z1 - z0), mt)
	return s

func luces_techo(s: Node, x0: float, x1: float, z0: float, z1: float, col: Color, nx: int, nz: int, energia := 2.4, rango := 9.0) -> void:
	for i in nx:
		for j in nz:
			var x := x0 + (i + 0.5) * (x1 - x0) / nx
			var z := z0 + (j + 0.5) * (z1 - z0) / nz
			inst(s, "luminaria_techo", "Luminaria_%d_%d" % [i, j], Vector3(x, ALTO - 0.03, z), Vector3(x, 0, z + 1.0))
			L.luz(s, "Luz_%d_%d" % [i, j], Vector3(x, ALTO - 0.5, z), col, energia, rango)

func registrar(n: Node, o: Node) -> void:
	for c in n.get_children():
		c.owner = o
		if c.scene_file_path == "":
			registrar(c, o)
		else:
			o.set_editable_instance(c, true)       # permite guardar ajustes dentro de la pieza instanciada (p. ej. la imagen de una pantalla)

# ───────────────────────── la nave (v2: chapa de nave, cuartos compactos y llenos, jardín botánico real, comedor con depósito)
func armar_nave() -> void:
	raiz = Node3D.new()
	raiz.name = "Nave"
	var muro := func(c: Color): return L.mat_muro(A + "muro_nave.png", c)
	var mm_pas = muro.call(Color(1.0, 1.0, 1.05))
	var mm_com = muro.call(Color(0.9, 1.0, 1.15))
	var mm_aid = muro.call(Color(1.25, 1.0, 0.8))
	var mm_kat = muro.call(Color(0.8, 1.2, 1.15))
	var mm_bot = muro.call(Color(0.85, 1.2, 0.95))
	var mm_enf = muro.call(Color(1.1, 1.15, 1.2))
	var suelo := L.mat_muro(A + "suelo_nave.png", Color(1, 1, 1))
	var techo := L.mat(Color(0.10, 0.12, 0.15), 0.7, 0.4)
	var alfombra_a := L.mat(Color(0.28, 0.13, 0.05), 0, 0.95)
	var alfombra_k := L.mat(Color(0.10, 0.28, 0.28), 0, 0.95)
	cielo()
	# ── PASILLO CENTRAL
	var pas := recinto("Pasillo", -20, 20, -1.6, 1.6, mm_pas, suelo, techo)
	pared_x(pas, "MuroNorte", -1.6, -20, 20, [[-13, 1.4], [0, 1.4], [13, 1.4]], mm_pas)
	pared_x(pas, "MuroSur", 1.6, -20, 20, [[-13, 1.4], [3, 1.4], [17, 1.4]], mm_pas)
	L.caja(pas, "BandaLuzSuelo", Vector3(0, 0.012, -1.3), Vector3(40, 0.012, 0.05), L.mat(Color(0.1, 0.8, 1.0), 0, 0.3, Color(0.1, 0.8, 1.0), 2.5))
	L.caja(pas, "BandaLuzSuelo2", Vector3(0, 0.012, 1.3), Vector3(40, 0.012, 0.05), L.mat(Color(0.1, 0.8, 1.0), 0, 0.3, Color(0.1, 0.8, 1.0), 2.5))
	luces_techo(pas, -19, 19, -1.6, 1.6, Color(0.8, 0.9, 1.0), 10, 1, 2.2, 7.0)
	var tub := L.mat(Color(0.14, 0.16, 0.20), 0.75, 0.35)
	var anillo := L.mat(Color(0.1, 0.8, 1.0), 0, 0.3, Color(0.1, 0.8, 1.0), 2.4)
	for s in [-1, 1]:
		L.cil(pas, "Tuberia", Vector3(0, 3.0, s * 1.42), 0.07, 40.0, tub, Vector3(0, 0, 90), 16)
		L.cil(pas, "Tuberia2", Vector3(0, 2.75, s * 1.45), 0.045, 40.0, tub, Vector3(0, 0, 90), 12)
		for k in 19:
			L.cil(pas, "AnilloTuberia", Vector3(-18.0 + k * 2.0, 3.0, s * 1.42), 0.075, 0.03, anillo, Vector3(0, 0, 90), 16)
	for k in 20:
		L.caja(pas, "Viga", Vector3(-19.0 + k * 2.0, ALTO - 0.12, 0), Vector3(0.14, 0.22, 3.2), tub)
	for x in [-16.0, -10.0, -5.0, 5.0, 8.0, 11.0, 15.0, 19.0]:
		for s in [-1, 1]:
			inst(pas, "costilla", "CostillaPasillo_%d_%d" % [int(x), s], Vector3(x, 0, s * 1.5), Vector3(x, 0, 0))
	for x in [-6.0, 6.0]:
		inst(pas, "caja_electrica", "CajaElectricaN_%d" % int(x), Vector3(x, 1.5, -1.49), Vector3(x, 1.5, 0))
		inst(pas, "caja_electrica", "CajaElectricaS_%d" % int(x), Vector3(x + 1.0, 1.5, 1.49), Vector3(x + 1.0, 1.5, 0))
	var rot_n := {-13: "aiden", 0: "comedor", 13: "kate"}
	for x in rot_n:
		L.pantalla(pas, "Rotulo_" + rot_n[x], Vector3(x, 2.62, -1.49), 1.4, 0.35, L.mat_tex(A + "rot_%s.png" % rot_n[x], 1.8), Vector3(0, 180, 0))
		inst(pas, "umbral", "Umbral_N_%d" % x, Vector3(x, 0, -1.25), Vector3(x, 0, 5))
	var rot_s := {-13: "comunicaciones", 3: "botanico", 17: "enfermeria"}
	for x in rot_s:
		L.pantalla(pas, "Rotulo_" + rot_s[x], Vector3(x, 2.62, 1.49), 1.4, 0.35, L.mat_tex(A + "rot_%s.png" % rot_s[x], 1.8))
		inst(pas, "umbral", "Umbral_S_%d" % x, Vector3(x, 0, 1.25), Vector3(x, 0, -5))
	inst(pas, "ventanal", "VentanalFondo", Vector3(19.9, 0.5, 0), Vector3(0, 0.5, 0))
	for x in [-13, 0, 13]:
		inst(pas, "marco_puerta", "Puerta_N_%d" % x, Vector3(x, 0, -1.6), Vector3(x, 0, 5))
	for x in [-13, 3, 17]:
		inst(pas, "marco_puerta", "Puerta_S_%d" % x, Vector3(x, 0, 1.6), Vector3(x, 0, -5))
	# ── CENTRO DE OPERACIONES (x −34…−20, z ±7)
	var co := recinto("CentroOperaciones", -34, -20, -7, 7, mm_com, suelo, techo)
	pared_z(co, "MuroOeste", -34, -7, 7, [], mm_com)
	pared_z(co, "MuroEste", -20, -7, 7, [[0, 2.0]], mm_com)
	pared_x(co, "MuroNorte", -7, -34, -20, [], mm_com)
	pared_x(co, "MuroSur", 7, -34, -20, [[-27, 8.0]], mm_com)
	inst(co, "ventanal", "VentanalSur", Vector3(-27, 0.5, 6.95), Vector3(-27, 0.5, 0), 2.0).scale = Vector3(2.0, 1.45, 1.0)
	inst(co, "nucleo_eva", "NucleoEVA", Vector3(-33.85, 0, 0), Vector3(0, 0, 0))
	inst(co, "holoproyector", "ProyectorHolograma", Vector3(-29.5, 0, 0), Vector3(-20, 0, 0))
	for i in 2:
		var x := -26.5 + i * 4.0
		inst(co, "consola_mando", "ConsolaMando%d" % i, Vector3(x, 0, -6.15), Vector3(x, 0, 0))
		inst(co, "silla_comando", "SillaMando%d" % i, Vector3(x + (0.35 if i == 0 else 0.0), 0, -4.5), Vector3(x, 0, -6.15))
	var tex := ["mapa_estelar.png", "navegacion.png", "estado_nave.png"]
	for i in 3:
		inst(co, "pantalla_pared", "PantallaGrande%d" % i, Vector3(-27.5 + i * 3.4, 2.3, -6.9), Vector3(-27.5 + i * 3.4, 2.3, 0), 1.5).get_node("Pantalla").material_override = L.mat_tex(A + tex[i])
	inst(co, "consola_central", "ConsolaCentral", Vector3(-27, 0, 4.7), Vector3(-27, 0, -10))
	for i in 2:
		inst(co, "silla_comando", "SillaCentral%d" % i, Vector3(-28.4 + i * 2.8, 0, 2.6), Vector3(-27, 0, 4.7))
	for z in [-3.0, 3.0]:
		inst(co, "rack_servidores", "RackOeste_%d" % int(z), Vector3(-33.55, 0, z * 1.6 + (0.0)), Vector3(-26, 0, z * 1.6)) if absf(z) > 99 else null
	for z in [-4.8, 4.8]:
		inst(co, "rack_servidores", "RackNucleo_%d" % int(z * 10), Vector3(-33.6, 0, z), Vector3(-26, 0, z))
	luces_techo(co, -33, -21, -6, 6, Color(0.75, 0.88, 1.0), 3, 2, 2.0, 10.5)
	L.luz(co, "LuzEVA", Vector3(-31.5, 2.2, 0), Color(0.2, 0.8, 1.0), 2.0, 9.0)
	decorar(co, -34, -20, -7, 7, 1, 3.0)
	# ── CUARTO DE AIDEN (x −17…−9, z −8…−1.6): piloto, grafito y ámbar
	var ca := recinto("CuartoAiden", -17, -9, -8, -1.6, mm_aid, suelo, techo)
	pared_z(ca, "MuroOeste", -17, -8, -1.6, [], mm_aid)
	pared_z(ca, "MuroEste", -9, -8, -1.6, [], mm_aid)
	pared_x(ca, "MuroFondo", -8, -17, -9, [[-13, 4.0]], mm_aid)
	inst(ca, "ventanal", "VentanalAiden", Vector3(-13, 0.5, -7.95), Vector3(-13, 0.5, 0), 1.0)
	L.caja(ca, "Alfombra", Vector3(-12.9, 0.006, -4.9), Vector3(2.8, 0.012, 2.4), alfombra_a)
	inst(ca, "cama", "Cama", Vector3(-15.75, 0, -5.0), Vector3(-9, 0, -5.0)).get_node("Manta").material_override = L.mat(Color(0.18, 0.2, 0.26), 0, 0.85)
	inst(ca, "mesita", "MesitaNoche", Vector3(-16.65, 0, -3.8), Vector3(-9, 0, -3.8))
	sh3d(ca, "table_desk_lamp", "LamparaMesita", Vector3(-16.65, 0.54, -3.8), Vector3(-9, 0, -3.8), 0.9)
	inst(ca, "escritorio", "Escritorio", Vector3(-9.55, 0, -5.6), Vector3(-13, 0, -5.6))
	inst(ca, "silla_comando", "SillaEscritorio", Vector3(-10.75, 0, -5.6), Vector3(-9.55, 0, -5.6))
	inst(ca, "pantalla_pared", "MonitorEscritorioA", Vector3(-9.15, 1.4, -6.2), Vector3(-13, 0, -6.2), 0.6).get_node("Pantalla").material_override = L.mat_tex(A + "navegacion.png")
	inst(ca, "pantalla_pared", "MonitorEscritorioB", Vector3(-9.15, 1.4, -5.0), Vector3(-13, 0, -5.0), 0.6).get_node("Pantalla").material_override = L.mat_tex(A + "mapa_estelar.png")
	inst(ca, "casco", "CascoDePiloto", Vector3(-9.45, 0.775, -6.7), Vector3(-13, 0, -6.7))
	inst(ca, "armario", "Armario", Vector3(-16.7, 0, -2.5), Vector3(-9, 0, -2.5))
	inst(ca, "estante", "EstanteLibros", Vector3(-10.8, 0, -7.65), Vector3(-10.8, 0, 0), 0.9)
	inst(ca, "pantalla_pared", "MapaSobreLaCama", Vector3(-16.85, 1.9, -5.0), Vector3(-9, 1.9, -5.0), 1.0).get_node("Pantalla").material_override = L.mat_tex(A + "mapa_estelar.png")
	inst(ca, "caja_electrica", "CajaElectrica", Vector3(-12.0, 1.8, -1.72), Vector3(-12, 1.8, -8))
	luces_techo(ca, -16.5, -9.5, -7.5, -2.0, Color(1.0, 0.86, 0.68), 2, 2, 2.0, 7.5)
	L.luz(ca, "LuzAmbar", Vector3(-13, 1.2, -4.0), Color(1.0, 0.6, 0.2), 0.8, 6.0)
	decorar(ca, -17, -9, -8, -1.6, -1, 2.6)
	# ── COMEDOR (x −5…5, z −10…−1.6): cocina, expendedoras, depósito, heladeras de vidrio
	var cd := recinto("Comedor", -5, 5, -10, -1.6, mm_pas, suelo, techo)
	pared_z(cd, "MuroOeste", -5, -10, -1.6, [], mm_pas)
	pared_z(cd, "MuroEste", 5, -10, -1.6, [], mm_pas)
	pared_x(cd, "MuroFondo", -10, -5, 5, [[0, 3.0]], mm_pas)
	inst(cd, "ventanal", "VentanalComedor", Vector3(0, 0.5, -9.95), Vector3(0, 0.5, 0), 0.75)
	for k in 2:
		var mx := -2.2 + k * 4.4
		inst(cd, "mesa_comedor", "Mesa%d" % k, Vector3(mx, 0, -5.6), Vector3(mx, 0, -3))
		for j in 3:
			var sx := mx - 0.8 + j * 0.8
			inst(cd, "silla_comedor", "Silla%d_N%d" % [k, j], Vector3(sx, 0, -6.5), Vector3(mx, 0, -5.6))
			inst(cd, "silla_comedor", "Silla%d_S%d" % [k, j], Vector3(sx, 0, -4.7), Vector3(mx, 0, -5.6))
	for i in 3:
		inst(cd, "expendedora", "Expendedora%d" % i, Vector3(-4.5, 0, -3.1 - i * 1.1), Vector3(0, 0, -3.1 - i * 1.1))
	for i in 2:
		inst(cd, "heladera_vidrio", "HeladeraVidrio%d" % i, Vector3(4.5, 0, -3.4 - i * 1.75), Vector3(0, 0, -3.4 - i * 1.75))
	inst(cd, "barra_cocina", "BarraCocina", Vector3(-3.3, 0, -9.55), Vector3(-3.3, 0, 0), 0.9)
	inst(cd, "estanteria_alimentos", "DepositoA", Vector3(3.3, 0, -9.7), Vector3(3.3, 0, 0), 1.0)
	inst(cd, "estanteria_alimentos", "DepositoB", Vector3(1.5, 0, -9.7), Vector3(1.5, 0, 0), 1.0) if false else null
	planta(cd, "planta_hojas_anchas", "PlantaComedor", Vector3(-4.45, 0, -9.3), 30.0, 0.9, 0.1)
	inst(cd, "pantalla_pared", "PantallaComedor", Vector3(-4.85, 2.4, -5.6), Vector3(0, 2.4, -5.6), 0.9).get_node("Pantalla").material_override = L.mat_tex(A + "mapa_estelar.png")
	luces_techo(cd, -4.5, 4.5, -9.5, -2.0, Color(1.0, 0.95, 0.88), 2, 3, 2.2, 8.5)
	decorar(cd, -5, 5, -10, -1.6, -1, 2.8)
	# ── CUARTO DE KATE (x 9…17, z −8…−1.6): bióloga, blanco y verdeazulado, plantas reales
	var ck := recinto("CuartoKate", 9, 17, -8, -1.6, mm_kat, suelo, techo)
	pared_z(ck, "MuroOeste", 9, -8, -1.6, [], mm_kat)
	pared_z(ck, "MuroEste", 17, -8, -1.6, [], mm_kat)
	pared_x(ck, "MuroFondo", -8, 9, 17, [[13, 4.0]], mm_kat)
	inst(ck, "ventanal", "VentanalKate", Vector3(13, 0.5, -7.95), Vector3(13, 0.5, 0), 1.0)
	L.caja(ck, "Alfombra", Vector3(12.9, 0.006, -4.9), Vector3(2.8, 0.012, 2.4), alfombra_k)
	inst(ck, "cama", "Cama", Vector3(15.75, 0, -5.0), Vector3(9, 0, -5.0)).get_node("Manta").material_override = L.mat(Color(0.16, 0.36, 0.36), 0, 0.85)
	inst(ck, "mesita", "MesitaNoche", Vector3(16.65, 0, -3.8), Vector3(9, 0, -3.8))
	inst(ck, "florero", "FloreroConLaFlor", Vector3(16.65, 0.54, -3.8), Vector3(9, 0, -3.8))
	L.pantalla(ck, "TabletKate", Vector3(16.55, 0.56, -3.95), 0.3, 0.19, L.mat_tex(A + "chat_tablet.png", 1.4), Vector3(-80, 270, 0))
	inst(ck, "escritorio", "BancoDeTrabajo", Vector3(9.55, 0, -5.6), Vector3(13, 0, -5.6))
	inst(ck, "silla_comando", "SillaBanco", Vector3(10.75, 0, -5.6), Vector3(9.55, 0, -5.6))
	inst(ck, "pantalla_pared", "PantallaMuestras", Vector3(9.15, 1.4, -5.6), Vector3(13, 0, -5.6), 0.7).get_node("Pantalla").material_override = L.mat_tex(A + "muestras.png")
	inst(ck, "microscopio", "Microscopio", Vector3(9.8, 0.775, -6.4), Vector3(13, 0, -6.4))
	inst(ck, "terrario", "Terrario", Vector3(9.75, 0.775, -4.9), Vector3(13, 0, -4.9))
	inst(ck, "armario", "Armario", Vector3(16.7, 0, -2.5), Vector3(9, 0, -2.5)).get_node("Cuerpo").material_override = L.mat(Color(0.84, 0.88, 0.9), 0.3, 0.35)
	inst(ck, "estante", "EstanteMuestras", Vector3(11.0, 0, -7.65), Vector3(11, 0, 0), 0.9)
	planta(ck, "planta_hojas_anchas", "PlantaHojasAnchas", Vector3(9.9, 0, -7.1), 20.0, 0.8, 0.3)
	planta(ck, "helecho", "HelechoRincon", Vector3(16.3, 0, -7.2), 0.0, 1.0, 0.55)
	planta(ck, "enredadera", "EnredaderaColgante", Vector3(13.0, ALTO - 0.2, -7.0), 0.0, 1.0, 0.8, true)
	L.cil(ck, "CableEnredadera", Vector3(13.0, ALTO - 0.1, -7.0), 0.004, 0.2, L.mat(Color(0.1, 0.1, 0.12)), Vector3.ZERO, 6)
	inst(ck, "caja_electrica", "CajaElectrica", Vector3(14.5, 1.8, -1.72), Vector3(14.5, 1.8, -8))
	luces_techo(ck, 9.5, 16.5, -7.5, -2.0, Color(0.88, 1.0, 0.96), 2, 2, 2.0, 7.5)
	L.luz(ck, "LuzVerde", Vector3(13, 1.2, -4.0), Color(0.5, 1.0, 0.8), 0.8, 6.0)
	decorar(ck, 9, 17, -8, -1.6, -1, 2.6)
	# ── COMUNICACIONES (x −17…−9, z 1.6…8)
	var cm := recinto("Comunicaciones", -17, -9, 1.6, 8, mm_com, suelo, techo)
	pared_z(cm, "MuroOeste", -17, 1.6, 8, [], mm_com)
	pared_z(cm, "MuroEste", -9, 1.6, 8, [], mm_com)
	pared_x(cm, "MuroFondo", 8, -17, -9, [[-13, 5.0]], mm_com)
	inst(cm, "ventanal", "VentanalComunicaciones", Vector3(-13, 0.5, 7.95), Vector3(-13, 0.5, 0), 1.0).scale = Vector3(1.25, 1.2, 1.0)
	inst(cm, "consola_central", "CentralComunicaciones", Vector3(-13, 0, 6.1), Vector3(-13, 0, -10), 1.0)
	for i in 2:
		inst(cm, "silla_comando", "SillaCom%d" % i, Vector3(-14.2 + i * 2.4, 0, 4.1), Vector3(-13, 0, 6.1))
	inst(cm, "pantalla_pared", "PantallaOeste", Vector3(-16.85, 1.8, 4.5), Vector3(-9, 1.8, 4.5), 1.2).get_node("Pantalla").material_override = L.mat_tex(A + "comunicaciones.png")
	inst(cm, "pantalla_pared", "PantallaEste", Vector3(-9.15, 1.8, 4.5), Vector3(-17, 1.8, 4.5), 1.2).get_node("Pantalla").material_override = L.mat_tex(A + "registros.png")
	for z in [2.7, 3.6]:
		inst(cm, "rack_servidores", "RackO_%d" % int(z * 10), Vector3(-16.6, 0, z + 3.2), Vector3(-9, 0, z + 3.2))
		inst(cm, "rack_servidores", "RackE_%d" % int(z * 10), Vector3(-9.4, 0, z + 3.2), Vector3(-17, 0, z + 3.2))
	luces_techo(cm, -16.5, -9.5, 2.0, 7.5, Color(0.72, 0.86, 1.0), 2, 2, 2.0, 7.5)
	decorar(cm, -17, -9, 1.6, 8, 1, 2.6)
	# ── MÓDULO BOTÁNICO (x −6…12, z 1.6…12): JARDÍN con plantas reales, canal de agua, incubadoras
	var bo := recinto("ModuloBotanico", -6, 12, 1.6, 12, mm_bot, suelo, techo)
	pared_z(bo, "MuroOeste", -6, 1.6, 12, [], mm_bot)
	pared_z(bo, "MuroEste", 12, 1.6, 12, [], mm_bot)
	pared_x(bo, "MuroFondo", 12, -6, 12, [[3, 6.0]], mm_bot)
	inst(bo, "ventanal", "VentanalBotanico", Vector3(3, 0.5, 11.95), Vector3(3, 0.5, 0), 1.0).scale = Vector3(1.5, 1.2, 1.0)
	for i in 6:
		var x := -4.2 + i * 2.5
		if absf(x - 3.0) < 3.1:
			continue
		inst(bo, "incubadora", "IncubadoraFondo%d" % i, Vector3(x, 0, 11.45), Vector3(x, 0, 0))
		planta(bo, "helecho", "HelechoIncubadora%d" % i, Vector3(x, 1.1, 11.45), 0.0, 0.4, 0.17 * i, true)
	inst(bo, "canal_agua", "CanalDeAgua", Vector3(3.0, 0, 7.6), Vector3(3, 0, 20))
	# jardineras y rosales
	var rosas := ["rosal_rojo", "rosal_blanco", "rosal_amarillo"]
	var xs := [-3.6, -1.0, 7.0, 9.6]
	for i in xs.size():
		inst(bo, "jardinera", "JardineraA%d" % i, Vector3(xs[i], 0, 3.9), Vector3(xs[i], 0, 20))
		planta(bo, rosas[i % 3], "RosalA%d_1" % i, Vector3(xs[i] - 0.6, 0.63, 3.9), 20.0 * i, 0.9, 0.13 * i)
		planta(bo, rosas[(i + 1) % 3], "RosalA%d_2" % i, Vector3(xs[i] + 0.6, 0.63, 3.9), 70.0 * i, 0.9, 0.31 + 0.1 * i)
	var xs2 := [-4.2, -1.7, 0.8, 5.2, 7.7, 10.2]
	for i in xs2.size():
		inst(bo, "jardinera", "JardineraB%d" % i, Vector3(xs2[i], 0, 9.6), Vector3(xs2[i], 0, 20))
		planta(bo, "planta_hojas_anchas" if i % 2 == 0 else rosas[i % 3], "PlantaB%d" % i, Vector3(xs2[i], 0.63, 9.6), 40.0 * i, 0.75 if i % 2 == 0 else 0.9, 0.09 * i)
	planta(bo, "ficus", "FicusEntradaO", Vector3(-5.1, 0, 2.7), 0.0, 1.0, 0.2)
	planta(bo, "ficus", "FicusEntradaE", Vector3(11.1, 0, 2.7), 90.0, 1.0, 0.6)
	planta(bo, "ficus", "FicusCanalO", Vector3(-5.0, 0, 7.6), 45.0, 0.9, 0.4)
	planta(bo, "ficus", "FicusCanalE", Vector3(11.0, 0, 7.6), 200.0, 0.9, 0.9)
	for i in 6:
		planta(bo, "enredadera", "EnredaderaTecho%d" % i, Vector3(-3.5 + i * 2.6, ALTO - 0.2, 6.0 + (i % 2) * 0.9), i * 60.0, 1.0, 0.15 * i, true)
		L.cil(bo, "CableEnredadera%d" % i, Vector3(-3.5 + i * 2.6, ALTO - 0.1, 6.0 + (i % 2) * 0.9), 0.004, 0.2, L.mat(Color(0.1, 0.1, 0.12)), Vector3.ZERO, 6)
	inst(bo, "pantalla_pared", "PantallaBotanico", Vector3(-5.85, 1.9, 5.5), Vector3(0, 1.9, 5.5), 1.3).get_node("Pantalla").material_override = L.mat_tex(A + "botanico.png")
	luces_techo(bo, -5, 11, 2.5, 11, Color(0.92, 1.0, 0.94), 4, 2, 2.2, 9.5)
	L.luz(bo, "LuzCultivo", Vector3(3, 2.6, 8.0), Color(0.8, 0.55, 1.0), 1.4, 9.0)
	decorar(bo, -6, 12, 1.6, 12, 1, 3.0)
	# ── ENFERMERÍA (x 14…20, z 1.6…8)
	var en := recinto("Enfermeria", 14, 20, 1.6, 8, mm_enf, suelo, techo)
	pared_z(en, "MuroOeste", 14, 1.6, 8, [], mm_enf)
	pared_z(en, "MuroEste", 20, 1.6, 8, [], mm_enf)
	pared_x(en, "MuroFondo", 8, 14, 20, [], mm_enf)
	inst(en, "camilla", "CamillaA", Vector3(16.0, 0, 5.0), Vector3(16.0, 0, 0))
	inst(en, "camilla", "CamillaB", Vector3(18.4, 0, 5.0), Vector3(18.4, 0, 0))
	inst(en, "soporte_suero", "SoporteSueroA", Vector3(15.1, 0, 5.9), Vector3(16, 0, 5.9))
	inst(en, "soporte_suero", "SoporteSueroB", Vector3(19.5, 0, 5.9), Vector3(18.6, 0, 5.9))
	inst(en, "pantalla_pared", "PantallaSignos", Vector3(17.0, 1.7, 7.85), Vector3(17, 1.7, 0), 1.2).get_node("Pantalla").material_override = L.mat_tex(A + "signos_vitales.png")
	inst(en, "estante", "EstanteMedico", Vector3(14.35, 0, 6.8), Vector3(17, 0, 6.8), 0.9)
	luces_techo(en, 14.5, 19.5, 2.0, 7.5, Color(0.92, 0.97, 1.0), 2, 2, 2.0, 7.5)
	decorar(en, 14, 20, 1.6, 8, 1, 2.6)
	registrar(raiz, raiz)

func cielo() -> void:
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.004, 0.006, 0.014)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.45, 0.55, 0.75)
	env.ambient_light_energy = 1.1
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.glow_enabled = true
	env.glow_intensity = 0.7
	env.glow_bloom = 0.1
	var we := WorldEnvironment.new()
	we.name = "Ambiente"
	we.environment = env
	raiz.add_child(we)
	var fondo := L.nodo(raiz, "Espacio")
	# Estrellas (MultiMesh de puntos emisivos)
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	var sm := SphereMesh.new()
	sm.radius = 0.9
	sm.height = 1.8
	sm.radial_segments = 6
	sm.rings = 3
	mm.mesh = sm
	mm.instance_count = 1400
	var rng := RandomNumberGenerator.new()
	rng.seed = 21
	for i in 1400:
		var d := Vector3(rng.randfn(), rng.randfn(), rng.randfn()).normalized()
		var s := rng.randf_range(0.4, 1.6)
		mm.set_instance_transform(i, Transform3D(Basis().scaled(Vector3(s, s, s)), d * 520.0))
	var mi := MultiMeshInstance3D.new()
	mi.name = "Estrellas"
	mi.multimesh = mm
	mi.material_override = L.mat(Color(1, 1, 1), 0, 1, Color(0.9, 0.95, 1.0), 3.0)
	fondo.add_child(mi)
	# Nebulosa de fondo (esfera interior)
	var neb := MeshInstance3D.new()
	var ns := SphereMesh.new()
	ns.radius = 540.0
	ns.height = 1080.0
	neb.mesh = ns
	var nm := StandardMaterial3D.new()
	nm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	nm.albedo_texture = load("res://assets/fondo/nebulosa.png")
	nm.cull_mode = BaseMaterial3D.CULL_FRONT
	neb.material_override = nm
	neb.name = "Nebulosa"
	fondo.add_child(neb)
	# Tierra
	var t := MeshInstance3D.new()
	var ts := SphereMesh.new()
	ts.radius = 130.0
	ts.height = 260.0
	ts.radial_segments = 64
	ts.rings = 32
	t.mesh = ts
	var tm := StandardMaterial3D.new()
	tm.albedo_texture = load("res://assets/fondo/tierra.png")
	tm.emission_enabled = true
	tm.emission_texture = tm.albedo_texture
	tm.emission_energy_multiplier = 0.35
	tm.roughness = 0.8
	t.material_override = tm
	t.name = "Tierra"
	t.position = Vector3(-50, 40, -330)
	fondo.add_child(t)
	var halo := MeshInstance3D.new()
	var hs := SphereMesh.new()
	hs.radius = 136.0
	hs.height = 272.0
	halo.mesh = hs
	halo.material_override = L.mat(Color(0.3, 0.6, 1.0), 0, 1, Color(0.3, 0.6, 1.0), 0.6, 0.18)
	halo.position = t.position
	halo.name = "AtmosferaTierra"
	fondo.add_child(halo)
	# Luna
	var lu := L.esf(fondo, "Luna", Vector3(120, 60, -300), 18.0, L.mat(Color(0.72, 0.72, 0.74), 0, 0.95, Color(0.4, 0.4, 0.42), 0.4))
	# Sol
	var sol := DirectionalLight3D.new()
	sol.name = "Sol"
	sol.light_color = Color(1.0, 0.95, 0.85)
	sol.light_energy = 0.9
	sol.rotation_degrees = Vector3(-25, 150, 0)
	fondo.add_child(sol)
	var solm := L.esf(fondo, "DiscoSolar", Vector3(260, 120, 420), 14.0, L.mat(Color(1, 0.95, 0.8), 0, 1, Color(1.0, 0.95, 0.75), 6.0))
