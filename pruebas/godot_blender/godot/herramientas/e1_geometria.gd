## ETAPA 1 — Construcción: casa (cocina, comedor/living, ventilador, ventanal, hogar), exterior (vereda, calle, farolas,
## edificios) y la camioneta Kodiak estacionada de cola al ventanal. Medidas en metros; Y arriba; la cámara mira a −Z.
## La sala va de x = −11 (izquierda, hogar) a x = 12 (derecha, cocina); la pared del fondo (z = −4) tiene el ventanal.
class_name E1Geometria
extends RefCounted

const ALTO := 3.0
const VENTANA_X := Vector2(-5.5, 0.0)      # ancho del ventanal en x
const VENTANA_Y := Vector2(0.25, 2.85)
const AUTO_POS := Vector3(-2.75, -0.25, -9.6)

static func construir(raiz: Node3D) -> void:
	_casa(raiz)
	_cocina(raiz)
	_living(raiz)
	_ventilador(raiz)
	_ventanal(raiz)
	_hogar(raiz)
	_exterior(raiz)
	_camioneta(raiz)

static func _casa(raiz: Node3D) -> void:
	var g := Kit.grupo(raiz, "Casa")
	Kit.caja(g, "Piso", Vector3(23.2, 0.1, 8.2), Vector3(0.5, -0.05, 0), "piso_madera")
	Kit.caja(g, "Techo", Vector3(23.2, 0.1, 8.2), Vector3(0.5, ALTO + 0.05, 0), "techo")
	Kit.caja(g, "Pared_izq", Vector3(0.2, ALTO, 8.2), Vector3(-11.1, ALTO / 2, 0), "pared")
	Kit.caja(g, "Pared_der", Vector3(0.2, ALTO, 8.2), Vector3(12.1, ALTO / 2, 0), "pared")
	Kit.caja(g, "Pared_frente", Vector3(23.2, ALTO, 0.2), Vector3(0.5, ALTO / 2, 4.1), "pared")
	# pared del fondo con el hueco del ventanal
	var izq := VENTANA_X.x + 11.0
	Kit.caja(g, "Pared_fondo_izq", Vector3(izq, ALTO, 0.2), Vector3(-11.0 + izq / 2, ALTO / 2, -4.0), "pared")
	Kit.caja(g, "Pared_fondo_der", Vector3(12.0 - VENTANA_X.y, ALTO, 0.2), Vector3((12.0 + VENTANA_X.y) / 2, ALTO / 2, -4.0), "pared")
	var ancho := VENTANA_X.y - VENTANA_X.x
	var cx := (VENTANA_X.x + VENTANA_X.y) / 2
	Kit.caja(g, "Pared_bajo_ventana", Vector3(ancho, VENTANA_Y.x, 0.2), Vector3(cx, VENTANA_Y.x / 2, -4.0), "pared")
	Kit.caja(g, "Pared_sobre_ventana", Vector3(ancho, ALTO - VENTANA_Y.y, 0.2), Vector3(cx, (ALTO + VENTANA_Y.y) / 2, -4.0), "pared")
	Kit.caja(g, "Zocalo_fondo", Vector3(22.0, 0.08, 0.03), Vector3(0.5, 0.04, -3.885), "metal_negro")

static func _cocina(raiz: Node3D) -> void:
	var g := Kit.grupo(raiz, "Cocina")
	# mesada contra la pared del fondo, alacenas, campana, heladera
	Kit.caja(g, "Bajo_mesada", Vector3(4.6, 0.86, 0.62), Vector3(9.1, 0.43, -3.58), "mueble_blanco")
	Kit.caja(g, "Mesada", Vector3(4.7, 0.05, 0.68), Vector3(9.1, 0.885, -3.56), "marmol")
	Kit.caja(g, "Zocalo_cocina", Vector3(4.6, 0.6, 0.02), Vector3(9.1, 1.21, -3.885), "azulejo")
	Kit.caja(g, "Alacenas", Vector3(3.2, 0.72, 0.36), Vector3(8.4, 2.05, -3.7), "mueble_madera")
	Kit.caja(g, "Campana", Vector3(0.9, 0.5, 0.5), Vector3(10.5, 2.15, -3.65), "acero")
	Kit.caja(g, "Anafe", Vector3(0.6, 0.012, 0.5), Vector3(10.5, 0.915, -3.55), "vidrio_negro")
	Kit.caja(g, "Bacha", Vector3(0.7, 0.012, 0.42), Vector3(8.0, 0.912, -3.55), "acero")
	Kit.cilindro(g, "Canilla", 0.015, 0.015, 0.32, Vector3(8.0, 1.07, -3.78), "acero")
	Kit.cilindro(g, "Canilla_pico", 0.012, 0.012, 0.2, Vector3(8.0, 1.22, -3.69), "acero", Vector3(90, 0, 0))
	Kit.caja(g, "Heladera", Vector3(0.9, 2.0, 0.72), Vector3(11.5, 1.0, -3.52), "acero")
	Kit.caja(g, "Heladera_manija", Vector3(0.03, 0.8, 0.04), Vector3(11.1, 1.15, -3.14), "metal_negro")
	# isla con banquetas
	Kit.caja(g, "Isla", Vector3(2.4, 0.86, 0.86), Vector3(8.9, 0.43, -1.15), "mueble_madera")
	Kit.caja(g, "Isla_tapa", Vector3(2.7, 0.06, 1.1), Vector3(8.9, 0.89, -1.1), "marmol")
	for i in 3:
		var x := 8.0 + i * 0.9
		Kit.cilindro(g, "Banqueta_%d_asiento" % i, 0.19, 0.19, 0.05, Vector3(x, 0.68, -0.25), "cuero")
		Kit.cilindro(g, "Banqueta_%d_pata" % i, 0.025, 0.025, 0.66, Vector3(x, 0.33, -0.25), "metal_negro")
		Kit.cilindro(g, "Banqueta_%d_base" % i, 0.17, 0.17, 0.02, Vector3(x, 0.01, -0.25), "metal_negro")
	# lámparas colgantes sobre la isla
	for i in 3:
		var x := 8.1 + i * 0.8
		Kit.cilindro(g, "Colgante_%d_cable" % i, 0.006, 0.006, 1.0, Vector3(x, 2.5, -1.1), "metal_negro")
		Kit.cilindro(g, "Colgante_%d_pantalla" % i, 0.05, 0.17, 0.2, Vector3(x, 1.92, -1.1), "metal_negro")
		Kit.esfera(g, "Colgante_%d_lampara" % i, 0.05, Vector3(x, 1.83, -1.1), "luz_calida")
	# decoración
	Kit.cilindro(g, "Frutera", 0.2, 0.11, 0.09, Vector3(8.4, 0.965, -1.1), "ceramica")
	for i in 5:
		var a := i * TAU / 5.0
		Kit.esfera(g, "Fruta_%d" % i, 0.045, Vector3(8.4 + cos(a) * 0.08, 1.02, -1.1 + sin(a) * 0.08), "fruta_naranja" if i % 2 == 0 else "fruta_verde")
	Kit.caja(g, "Tabla_picar", Vector3(0.45, 0.025, 0.3), Vector3(9.4, 0.932, -1.0), "madera_clara")
	for i in 3:
		Kit.cilindro(g, "Botella_%d" % i, 0.035, 0.035, 0.3, Vector3(6.95 + i * 0.1, 1.06, -3.62), ["vidrio_verde", "vidrio_ambar", "vidrio_verde"][i])
	Kit.cilindro(g, "Pava", 0.07, 0.1, 0.18, Vector3(10.35, 1.0, -3.5), "acero")
	Kit.cilindro(g, "Maceta_cocina", 0.12, 0.09, 0.22, Vector3(11.85, 0.11, -2.7), "ceramica")
	for i in 4:
		Kit.esfera(g, "Planta_cocina_%d" % i, 0.16, Vector3(11.85 + (i % 2) * 0.1 - 0.05, 0.38 + i * 0.12, -2.7 + (i / 2) * 0.1 - 0.05), "hoja")

static func _living(raiz: Node3D) -> void:
	var g := Kit.grupo(raiz, "Living")
	# mesa del comedor con 4 sillas
	Kit.caja(g, "Mesa_comedor", Vector3(1.9, 0.05, 1.0), Vector3(5.6, 0.75, -1.3), "madera_oscura")
	for sx in [-1, 1]:
		for sz in [-1, 1]:
			Kit.caja(g, "Mesa_comedor_pata_%d%d" % [sx + 1, sz + 1], Vector3(0.06, 0.73, 0.06), Vector3(5.6 + sx * 0.85, 0.365, -1.3 + sz * 0.42), "madera_oscura")
	for i in 4:
		var x := 5.1 + (i % 2) * 1.0
		var lado := -1.0 if i < 2 else 1.0
		var z := -1.3 + lado * 0.72
		var s := Kit.grupo(g, "Silla_%d" % i, Vector3(x, 0, z), Vector3(0, 0 if lado > 0 else 180, 0))
		Kit.caja(s, "asiento", Vector3(0.45, 0.04, 0.45), Vector3(0, 0.46, 0), "tela_gris")
		Kit.caja(s, "respaldo", Vector3(0.45, 0.45, 0.04), Vector3(0, 0.7, 0.21), "tela_gris")
		for p in 4:
			Kit.caja(s, "pata_%d" % p, Vector3(0.03, 0.46, 0.03), Vector3((p % 2 - 0.5) * 0.4, 0.23, (p / 2 - 0.5) * 0.4), "metal_negro")
	Kit.cilindro(g, "Florero", 0.06, 0.05, 0.22, Vector3(5.6, 0.885, -1.3), "ceramica")
	Kit.esfera(g, "Flores", 0.11, Vector3(5.6, 1.06, -1.3), "flor")
	# sillón, mesa ratona, mesa auxiliar redonda con velador, alfombra, biblioteca
	Kit.caja(g, "Alfombra", Vector3(3.0, 0.012, 2.2), Vector3(2.8, 0.006, -2.4), "alfombra")
	var so := Kit.grupo(g, "Sillon", Vector3(2.8, 0, -3.4))
	Kit.caja(so, "base", Vector3(2.4, 0.42, 0.9), Vector3(0, 0.21, 0), "tela_azul")
	Kit.caja(so, "respaldo", Vector3(2.4, 0.5, 0.22), Vector3(0, 0.67, -0.34), "tela_azul")
	Kit.caja(so, "brazo_i", Vector3(0.2, 0.62, 0.9), Vector3(-1.1, 0.31, 0), "tela_azul")
	Kit.caja(so, "brazo_d", Vector3(0.2, 0.62, 0.9), Vector3(1.1, 0.31, 0), "tela_azul")
	for i in 2:
		Kit.caja(so, "almohadon_%d" % i, Vector3(0.42, 0.38, 0.12), Vector3(-0.6 + i * 1.2, 0.6, -0.18), "tela_naranja", Vector3(-12, 0, 0))
	Kit.caja(g, "Mesa_ratona", Vector3(1.2, 0.05, 0.6), Vector3(2.8, 0.38, -2.2), "madera_clara")
	Kit.caja(g, "Mesa_ratona_base", Vector3(1.0, 0.33, 0.45), Vector3(2.8, 0.18, -2.2), "metal_negro")
	Kit.caja(g, "Libro_1", Vector3(0.25, 0.04, 0.18), Vector3(2.5, 0.425, -2.2), "tela_naranja", Vector3(0, 12, 0))
	Kit.caja(g, "Libro_2", Vector3(0.24, 0.035, 0.17), Vector3(2.52, 0.46, -2.19), "tela_azul", Vector3(0, -8, 0))
	Kit.cilindro(g, "Vela", 0.04, 0.04, 0.1, Vector3(3.1, 0.455, -2.2), "cera")
	Kit.cilindro(g, "Mesa_auxiliar", 0.28, 0.28, 0.03, Vector3(4.4, 0.55, -3.4), "marmol")
	Kit.cilindro(g, "Mesa_auxiliar_pie", 0.03, 0.03, 0.54, Vector3(4.4, 0.27, -3.4), "metal_negro")
	Kit.cilindro(g, "Velador_pie", 0.015, 0.06, 0.35, Vector3(4.4, 0.74, -3.45), "metal_negro")
	Kit.cilindro(g, "Velador_pantalla", 0.11, 0.17, 0.22, Vector3(4.4, 1.0, -3.45), "pantalla_tela")
	var bi := Kit.grupo(g, "Biblioteca", Vector3(0.85, 0, -3.72))
	Kit.caja(bi, "cuerpo", Vector3(1.1, 2.1, 0.32), Vector3(0, 1.05, 0), "madera_oscura")
	for i in 4:
		Kit.caja(bi, "libros_%d" % i, Vector3(0.95, 0.3, 0.24), Vector3(0, 0.3 + i * 0.48, 0.05), ["tela_naranja", "tela_azul", "tela_gris", "cuero"][i])
	# sillón individual bajo el ventilador
	var bu := Kit.grupo(g, "Butaca", Vector3(1.4, 0, -2.0), Vector3(0, 25, 0))
	Kit.caja(bu, "base", Vector3(0.8, 0.42, 0.8), Vector3(0, 0.21, 0), "cuero")
	Kit.caja(bu, "respaldo", Vector3(0.8, 0.55, 0.18), Vector3(0, 0.69, -0.31), "cuero")

static func _ventilador(raiz: Node3D) -> void:
	var g := Kit.grupo(raiz, "Ventilador", Vector3(1.6, ALTO, -1.0))
	Kit.cilindro(g, "Florón", 0.09, 0.09, 0.05, Vector3(0, -0.025, 0), "metal_bronce")
	Kit.cilindro(g, "Barra", 0.016, 0.016, 0.42, Vector3(0, -0.24, 0), "metal_bronce")
	Kit.cilindro(g, "Motor", 0.15, 0.13, 0.14, Vector3(0, -0.5, 0), "metal_bronce")
	var aspas := Kit.grupo(g, "Ventilador_aspas", Vector3(0, -0.56, 0))
	for i in 5:
		var brazo := Kit.grupo(aspas, "Aspa_%d" % i, Vector3.ZERO, Vector3(0, i * 72.0, 0))
		Kit.caja(brazo, "soporte", Vector3(0.22, 0.012, 0.04), Vector3(0.2, 0, 0), "metal_bronce")
		Kit.caja(brazo, "pala", Vector3(0.6, 0.01, 0.15), Vector3(0.58, -0.005, 0), "madera_oscura", Vector3(8, 0, 0))
	Kit.esfera(g, "Plafon", 0.16, Vector3(0, -0.66, 0), "vidrio_opalino", Vector3(1, 0.55, 1))

static func _ventanal(raiz: Node3D) -> void:
	var g := Kit.grupo(raiz, "Ventanal")
	var ancho := VENTANA_X.y - VENTANA_X.x
	var cx := (VENTANA_X.x + VENTANA_X.y) / 2
	var alto := VENTANA_Y.y - VENTANA_Y.x
	var cy := (VENTANA_Y.x + VENTANA_Y.y) / 2
	Kit.caja(g, "Vidrio_ventanal", Vector3(ancho, alto, 0.02), Vector3(cx, cy, -4.0), "vidrio")
	for i in 3:
		Kit.caja(g, "Parante_%d" % i, Vector3(0.07, alto, 0.12), Vector3(VENTANA_X.x + i * ancho / 2, cy, -4.0), "metal_negro")
	Kit.caja(g, "Marco_abajo", Vector3(ancho + 0.07, 0.07, 0.14), Vector3(cx, VENTANA_Y.x, -4.0), "metal_negro")
	Kit.caja(g, "Marco_arriba", Vector3(ancho + 0.07, 0.07, 0.14), Vector3(cx, VENTANA_Y.y, -4.0), "metal_negro")

static func _hogar(raiz: Node3D) -> void:
	var g := Kit.grupo(raiz, "Hogar", Vector3(-8.6, 0, -3.9))
	Kit.caja(g, "Columna_izq", Vector3(0.45, 1.15, 0.5), Vector3(-0.95, 0.575, 0.25), "piedra")
	Kit.caja(g, "Columna_der", Vector3(0.45, 1.15, 0.5), Vector3(0.95, 0.575, 0.25), "piedra")
	Kit.caja(g, "Dintel", Vector3(2.35, 0.3, 0.55), Vector3(0, 1.3, 0.27), "piedra")
	Kit.caja(g, "Repisa", Vector3(2.6, 0.08, 0.36), Vector3(0, 1.49, 0.42), "madera_oscura")
	Kit.caja(g, "Chimenea", Vector3(1.9, 1.5, 0.45), Vector3(0, 2.25, 0.2), "piedra")
	Kit.caja(g, "Fogon_fondo", Vector3(1.45, 1.15, 0.05), Vector3(0, 0.575, 0.03), "hollin")
	Kit.caja(g, "Fogon_techo", Vector3(1.45, 0.05, 0.5), Vector3(0, 1.14, 0.25), "hollin")
	Kit.caja(g, "Base_hogar", Vector3(2.8, 0.12, 0.95), Vector3(0, 0.06, 0.48), "piedra_oscura")
	Kit.caja(g, "Parrilla", Vector3(0.9, 0.04, 0.3), Vector3(0, 0.17, 0.3), "metal_negro")
	Kit.cilindro(g, "Leño_1", 0.07, 0.07, 0.8, Vector3(-0.05, 0.25, 0.25), "leña", Vector3(0, 0, 90))
	Kit.cilindro(g, "Leño_2", 0.065, 0.065, 0.75, Vector3(0.05, 0.25, 0.4), "leña", Vector3(0, 12, 90))
	Kit.cilindro(g, "Leño_3", 0.06, 0.06, 0.7, Vector3(0.0, 0.37, 0.32), "leña", Vector3(0, -20, 78))
	for i in 9:
		Kit.esfera(g, "Brasa_%d" % i, 0.035 + (i % 3) * 0.01, Vector3(-0.35 + i * 0.087, 0.2, 0.18 + (i % 2) * 0.22), "brasa")
	Kit.cilindro(g, "Atizador", 0.01, 0.01, 0.9, Vector3(1.32, 0.45, 0.55), "metal_negro", Vector3(0, 0, -8))
	Kit.caja(g, "Cuadro", Vector3(1.1, 0.7, 0.03), Vector3(0, 2.25, 0.44), "cuadro")
	for i in 3:
		Kit.cilindro(g, "Vela_repisa_%d" % i, 0.035, 0.035, 0.12 + i * 0.05, Vector3(0.7 + i * 0.13, 1.59 + i * 0.025, 0.45), "cera")

static func _exterior(raiz: Node3D) -> void:
	var g := Kit.grupo(raiz, "Exterior")
	Kit.caja(g, "Vereda", Vector3(40, 0.1, 2.6), Vector3(-2, -0.12, -5.4), "vereda_mojada")
	Kit.caja(g, "Cordon", Vector3(40, 0.18, 0.2), Vector3(-2, -0.16, -6.75), "cordon")
	Kit.caja(g, "Calle", Vector3(80, 0.1, 40), Vector3(-2, -0.3, -26.85), "asfalto_mojado")
	for i in 7:
		Kit.caja(g, "Raya_%d" % i, Vector3(2.0, 0.005, 0.12), Vector3(-16 + i * 5.0, -0.248, -13.5), "pintura_vial")
	Kit.caja(g, "Vereda_enfrente", Vector3(80, 0.1, 4), Vector3(-2, -0.17, -38.0), "vereda_mojada")
	# farolas (dos alumbran la camioneta desde atrás y de costado)
	for i in 4:
		var x: float = [-9.0, -5.3, -0.4, 4.0][i]
		var f := Kit.grupo(g, "Farola_%d" % i, Vector3(x, -0.07, -6.45))
		Kit.cilindro(f, "poste", 0.06, 0.09, 4.6, Vector3(0, 2.3, 0), "metal_poste")
		Kit.cilindro(f, "brazo", 0.035, 0.035, 1.2, Vector3(0, 4.55, -0.55), "metal_poste", Vector3(90, 0, 0))
		Kit.caja(f, "cabezal", Vector3(0.32, 0.12, 0.55), Vector3(0, 4.5, -1.1), "metal_poste")
		Kit.caja(f, "lampara", Vector3(0.26, 0.02, 0.45), Vector3(0, 4.43, -1.1), "luz_farola")
	# edificios de enfrente (siluetas con algunas ventanas encendidas)
	var anchos := [6.0, 4.5, 7.0, 5.0, 6.5, 4.0, 5.5]
	var altos := [6.0, 8.5, 4.5, 9.5, 7.0, 5.0, 8.0]
	var x0 := -22.0
	for i in anchos.size():
		var w: float = anchos[i]
		var h: float = altos[i]
		var b := Kit.caja(g, "Edificio_%d" % i, Vector3(w, h, 6), Vector3(x0 + w / 2, h / 2 - 0.2, -43.0), "edificio")
		for v in maxi(1, int(h / 3.0)):
			if (i + v) % 3 == 0:
				Kit.caja(g, "Ventana_ed_%d_%d" % [i, v], Vector3(0.9, 1.1, 0.05), Vector3(x0 + w * 0.3 + (v % 2) * w * 0.35, 1.8 + v * 3.2, -39.97), "ventana_lejana")
		x0 += w + 0.6
	Kit.caja(g, "Cerros", Vector3(220, 16, 4), Vector3(0, 3, -110), "cerros")
	Kit.esfera(g, "Cielo", 160.0, Vector3(0, 0, -10), "cielo_tormenta", Vector3(1, 0.6, 1))
	# rayo: cajas finas en zigzag sobre los edificios (aparece sólo en los destellos; escala 0 el resto del tiempo)
	var pts := PackedVector3Array([Vector3(-5.5, 34, -80), Vector3(-3.6, 27, -80), Vector3(-6.4, 20, -80), Vector3(-4.2, 14, -80),
		Vector3(-5.8, 8, -80), Vector3(-4.9, 2, -80)])
	var rayo := Kit.polilinea(g, "Relampago_rayo", pts, 0.5, "rayo")
	Kit.polilinea(rayo, "Relampago_rama", PackedVector3Array([Vector3(-3.6, 27, -80), Vector3(-0.8, 22, -80), Vector3(0.2, 16, -80)]), 0.3, "rayo")

static func _camioneta(raiz: Node3D) -> void:
	# CÓNDOR Kodiak Raid (Dream Racing, modelo del dueño). El modelo trae carrocería sin ruedas (el juego las arma):
	# se agregan ruedas con las medidas de kodiak.json (radio 0,4, ancho 0,33, ejes en z +1,366 y −1,604).
	# El frente del modelo mira a +Z: se gira 180° para que la cola quede hacia el ventanal.
	var g := Kit.grupo(raiz, "Camioneta_Kodiak", AUTO_POS, Vector3(0, 180, 0))
	var car: Node3D = load("res://modelos/kodiak.glb").instantiate()
	car.name = "Kodiak_carroceria"
	g.add_child(car)
	for z in [1.3665, -1.6041]:
		for x in [-0.86, 0.86]:
			var n := "Rueda_%s_%s" % ["del" if z > 0 else "tras", "izq" if x > 0 else "der"]
			var r := Kit.grupo(g, n, Vector3(x, 0.4, z))
			Kit.cilindro(r, "cubierta", 0.4, 0.4, 0.33, Vector3.ZERO, "goma", Vector3(0, 0, 90), 32)
			Kit.cilindro(r, "llanta", 0.25, 0.25, 0.34, Vector3.ZERO, "llanta", Vector3(0, 0, 90), 16)
