## Piezas reutilizables de la nave. Cada función devuelve una pieza (origen en el piso, frente hacia −Z).
extends RefCounted
const L = preload("res://tools/lib.gd")
const P := "res://assets/pantallas/"

static func silla_comando() -> Node3D:
	var r := L.nodo(null, "silla_comando") if false else Node3D.new()
	r.name = "silla_comando"
	var gris := L.mat(Color(0.12, 0.13, 0.16), 0.6, 0.4)
	var tela := L.mat(Color(0.07, 0.10, 0.17), 0.0, 0.8)
	var luz := L.mat(Color(0.1, 0.8, 1.0), 0, 0.3, Color(0.1, 0.8, 1.0), 3.0)
	L.cil(r, "Base", Vector3(0, 0.03, 0), 0.30, 0.04, gris)
	L.cil(r, "Columna", Vector3(0, 0.26, 0), 0.035, 0.40, gris)
	L.caja(r, "Asiento", Vector3(0, 0.50, 0), Vector3(0.50, 0.09, 0.50), tela)
	var resp := L.nodo(r, "Respaldo", Vector3(0, 0.50, 0.24), Vector3(10, 0, 0))
	L.caja(resp, "Cuerpo", Vector3(0, 0.34, 0), Vector3(0.48, 0.62, 0.07), tela)
	L.caja(resp, "Vivo", Vector3(0, 0.34, 0.04), Vector3(0.04, 0.50, 0.01), luz)
	for s in [-1, 1]:
		L.caja(r, "Apoyabrazos", Vector3(s * 0.29, 0.70, -0.02), Vector3(0.05, 0.05, 0.32), gris)
		L.caja(r, "SoporteBrazo", Vector3(s * 0.29, 0.60, 0.1), Vector3(0.04, 0.18, 0.04), gris)
	return r

static func silla_comedor() -> Node3D:
	var r := Node3D.new()
	r.name = "silla_comedor"
	var gris := L.mat(Color(0.16, 0.17, 0.2), 0.55, 0.45)
	var tela := L.mat(Color(0.10, 0.22, 0.28), 0.0, 0.75)
	L.caja(r, "Asiento", Vector3(0, 0.46, 0), Vector3(0.44, 0.06, 0.44), tela)
	var resp := L.nodo(r, "Respaldo", Vector3(0, 0.49, 0.20), Vector3(6, 0, 0))
	L.caja(resp, "Cuerpo", Vector3(0, 0.26, 0), Vector3(0.44, 0.46, 0.05), tela)
	for x in [-0.19, 0.19]:
		for z in [-0.19, 0.19]:
			L.cil(r, "Pata", Vector3(x, 0.22, z), 0.022, 0.44, gris, Vector3.ZERO, 12)
	return r

static func mesa_comedor() -> Node3D:
	var r := Node3D.new()
	r.name = "mesa_comedor"
	var tapa := L.mat(Color(0.82, 0.85, 0.88), 0.2, 0.35)
	var gris := L.mat(Color(0.14, 0.15, 0.18), 0.6, 0.4)
	var luz := L.mat(Color(0.1, 0.8, 1.0), 0, 0.3, Color(0.1, 0.8, 1.0), 2.2)
	L.caja(r, "Tapa", Vector3(0, 0.74, 0), Vector3(2.6, 0.06, 1.0), tapa)
	L.caja(r, "BordeLuz", Vector3(0, 0.705, 0), Vector3(2.5, 0.012, 0.92), luz)
	for s in [-1, 1]:
		L.caja(r, "Panel", Vector3(s * 1.0, 0.36, 0), Vector3(0.07, 0.72, 0.7), gris)
	L.caja(r, "Travesaño", Vector3(0, 0.12, 0), Vector3(2.0, 0.05, 0.08), gris)
	return r

static func consola_mando() -> Node3D:
	var r := Node3D.new()
	r.name = "consola_mando"
	var cuerpo := L.mat(Color(0.11, 0.13, 0.17), 0.65, 0.35)
	var tapa := L.mat(Color(0.07, 0.09, 0.13), 0.5, 0.3)
	var luz := L.mat(Color(0.1, 0.8, 1.0), 0, 0.3, Color(0.1, 0.8, 1.0), 2.6)
	L.caja(r, "Cuerpo", Vector3(0, 0.40, 0.05), Vector3(2.4, 0.80, 0.8), cuerpo)
	L.caja(r, "Tapa", Vector3(0, 0.82, 0.0), Vector3(2.44, 0.05, 0.84), tapa)
	L.caja(r, "LuzFrente", Vector3(0, 0.12, -0.352), Vector3(2.2, 0.02, 0.01), luz)
	L.caja(r, "Teclado", Vector3(-0.2, 0.855, -0.2), Vector3(0.62, 0.02, 0.2), L.mat(Color(0.03, 0.05, 0.09), 0.3, 0.4, Color(0.1, 0.6, 1.0), 0.0))
	var tec := L.pantalla(r, "TecladoLuces", Vector3(-0.2, 0.868, -0.2), 0.6, 0.18, L.mat_tex(P + "botonera.png", 1.8), Vector3(-90, 0, 0))
	tec.rotation_degrees = Vector3(-90, 180, 0)
	# pantallas sobre soportes, inclinadas hacia el operador
	var pm := [L.mat_tex(P + "navegacion.png"), L.mat_tex(P + "estado_nave.png"), L.mat_tex(P + "mapa_estelar.png")]
	for i in 3:
		var x := (i - 1) * 0.74
		L.caja(r, "Soporte%d" % i, Vector3(x, 0.98, 0.3), Vector3(0.06, 0.3, 0.05), cuerpo)
		L.caja(r, "Marco%d" % i, Vector3(x, 1.28, 0.28), Vector3(0.70, 0.42, 0.04), cuerpo, Vector3(-8, 0, 0))
		L.pantalla(r, "Pantalla%d" % i, Vector3(x, 1.285, 0.255), 0.64, 0.36, pm[i], Vector3(-8, 0, 0))
	# almohadilla holográfica de EVA (miniatura) junto al teclado
	L.cil(r, "HoloPad", Vector3(0.78, 0.855, -0.18), 0.12, 0.012, tapa)
	L.toro(r, "HoloPadAro", Vector3(0.78, 0.862, -0.18), 0.095, 0.115, luz)
	return r

static func pantalla_pared(textura := "navegacion.png") -> Node3D:
	var r := Node3D.new()
	r.name = "pantalla_pared"
	var marco := L.mat(Color(0.10, 0.12, 0.16), 0.7, 0.3)
	var luz := L.mat(Color(0.1, 0.8, 1.0), 0, 0.3, Color(0.1, 0.8, 1.0), 2.4)
	L.caja(r, "Marco", Vector3(0, 0, 0), Vector3(1.72, 1.02, 0.07), marco)
	L.caja(r, "Filete", Vector3(0, -0.52, -0.03), Vector3(1.72, 0.012, 0.01), luz)
	L.pantalla(r, "Pantalla", Vector3(0, 0, -0.037), 1.6, 0.9, L.mat_tex(P + textura))
	return r

static func cama(color_manta := Color(0.12, 0.2, 0.3)) -> Node3D:
	var r := Node3D.new()
	r.name = "cama"
	var base := L.mat(Color(0.13, 0.14, 0.18), 0.6, 0.4)
	var luz := L.mat(Color(0.1, 0.8, 1.0), 0, 0.3, Color(0.1, 0.8, 1.0), 2.2)
	L.caja(r, "Base", Vector3(0, 0.15, 0), Vector3(1.1, 0.30, 2.1), base)
	L.caja(r, "LuzBase", Vector3(0, 0.05, -1.07), Vector3(1.0, 0.012, 0.01), luz)
	L.caja(r, "Colchon", Vector3(0, 0.39, 0), Vector3(1.02, 0.18, 2.0), L.mat(Color(0.82, 0.85, 0.88), 0, 0.8))
	L.caja(r, "Manta", Vector3(0, 0.49, -0.3), Vector3(1.04, 0.06, 1.25), L.mat(color_manta, 0, 0.85))
	L.caja(r, "Almohada", Vector3(0, 0.54, 0.78), Vector3(0.55, 0.12, 0.32), L.mat(Color(0.88, 0.9, 0.93), 0, 0.9))
	L.caja(r, "Cabecera", Vector3(0, 0.75, 1.04), Vector3(1.24, 0.9, 0.07), base)
	L.caja(r, "CabeceraLuz", Vector3(0, 0.95, 1.0), Vector3(0.9, 0.025, 0.01), luz)
	return r

static func escritorio() -> Node3D:
	var r := Node3D.new()
	r.name = "escritorio"
	var tapa := L.mat(Color(0.18, 0.19, 0.23), 0.5, 0.35)
	var gris := L.mat(Color(0.10, 0.11, 0.14), 0.6, 0.4)
	var luz := L.mat(Color(1.0, 0.65, 0.2), 0, 0.3, Color(1.0, 0.65, 0.2), 2.0)
	L.caja(r, "Tapa", Vector3(0, 0.75, 0), Vector3(1.8, 0.05, 0.8), tapa)
	L.caja(r, "BordeLuz", Vector3(0, 0.722, -0.40), Vector3(1.7, 0.01, 0.01), luz)
	for s in [-1, 1]:
		L.caja(r, "Panel", Vector3(s * 0.84, 0.36, 0), Vector3(0.06, 0.72, 0.7), gris)
	L.caja(r, "Cajonera", Vector3(0.55, 0.40, 0.03), Vector3(0.5, 0.58, 0.66), gris)
	return r

static func armario() -> Node3D:
	var r := Node3D.new()
	r.name = "armario"
	var cuerpo := L.mat(Color(0.20, 0.22, 0.26), 0.45, 0.4)
	var luz := L.mat(Color(0.1, 0.8, 1.0), 0, 0.3, Color(0.1, 0.8, 1.0), 2.2)
	L.caja(r, "Cuerpo", Vector3(0, 1.1, 0), Vector3(1.4, 2.2, 0.6), cuerpo)
	L.caja(r, "Juntura", Vector3(0, 1.1, -0.302), Vector3(0.012, 2.1, 0.005), L.mat(Color(0.04, 0.05, 0.07)))
	for s in [-1, 1]:
		L.caja(r, "Tirador", Vector3(s * 0.08, 1.1, -0.31), Vector3(0.015, 0.4, 0.02), luz)
	return r

static func estante(frasco := Color(0.2, 0.9, 0.6)) -> Node3D:
	var r := Node3D.new()
	r.name = "estante"
	var gris := L.mat(Color(0.17, 0.18, 0.22), 0.5, 0.4)
	for s in [-1, 1]:
		L.caja(r, "Montante", Vector3(s * 0.55, 1.0, 0), Vector3(0.04, 2.0, 0.34), gris)
	var rng := RandomNumberGenerator.new()
	rng.seed = 5
	for i in 5:
		L.caja(r, "Repisa%d" % i, Vector3(0, 0.25 + i * 0.42, 0), Vector3(1.14, 0.03, 0.34), gris)
		for j in 6:
			var h := rng.randf_range(0.14, 0.26)
			var c := Color.from_hsv(rng.randf_range(0.5, 0.62), rng.randf_range(0.3, 0.8), rng.randf_range(0.4, 0.9))
			if i % 2 == 1 and j % 2 == 0:
				c = frasco
			L.cil(r, "Frasco%d_%d" % [i, j], Vector3(-0.46 + j * 0.18, 0.265 + i * 0.42 + h / 2, 0), 0.05, h, L.mat(c, 0.0, 0.3, c, 0.5 if i % 2 == 1 else 0.0), Vector3.ZERO, 16)
	return r

static func incubadora() -> Node3D:
	var r := Node3D.new()
	r.name = "incubadora"
	var blanco := L.mat(Color(0.88, 0.9, 0.92), 0.3, 0.3)
	var vidrio := L.mat(Color(0.7, 0.9, 1.0), 0.0, 0.05, Color(0, 0, 0), 0.0, 0.18)
	var luzc := L.mat(Color(0.9, 0.6, 1.0), 0, 0.3, Color(0.85, 0.55, 1.0), 3.0)
	var agua := L.mat(Color(0.2, 0.55, 0.7), 0, 0.1, Color(0.1, 0.4, 0.55), 0.6, 0.7)
	var tierra := L.mat(Color(0.18, 0.11, 0.07), 0, 0.95)
	L.caja(r, "Gabinete", Vector3(0, 0.45, 0), Vector3(2.0, 0.9, 0.8), blanco)
	L.caja(r, "Agua", Vector3(0, 0.95, 0), Vector3(1.9, 0.12, 0.7), agua)
	L.caja(r, "Sustrato", Vector3(0, 1.05, 0), Vector3(1.9, 0.09, 0.7), tierra)
	var rng := RandomNumberGenerator.new()
	rng.seed = 9
	for i in 9:
		var x := -0.8 + i * 0.2
		var h := rng.randf_range(0.18, 0.38)
		L.cil(r, "Tallo%d" % i, Vector3(x, 1.1 + h / 2, rng.randf_range(-0.2, 0.2)), 0.012, h, L.mat(Color(0.2, 0.55, 0.2)), Vector3.ZERO, 8)
		L.esf(r, "Hoja%d" % i, Vector3(x, 1.1 + h, 0), 0.08, L.mat(Color(0.25, 0.7, 0.28), 0, 0.6), Vector3(1.4, 0.7, 1.0))
	L.caja(r, "Vidrio", Vector3(0, 1.48, 0), Vector3(1.96, 0.78, 0.74), vidrio)
	L.caja(r, "Techo", Vector3(0, 1.9, 0), Vector3(2.0, 0.06, 0.8), blanco)
	L.caja(r, "LuzCultivo", Vector3(0, 1.85, -0.2), Vector3(1.8, 0.03, 0.12), luzc)
	return r

static func luminaria_techo() -> Node3D:
	var r := Node3D.new()
	r.name = "luminaria_techo"
	L.caja(r, "Panel", Vector3(0, 0, 0), Vector3(1.4, 0.04, 0.45), L.mat(Color(1, 1, 1), 0, 0.3, Color(0.85, 0.92, 1.0), 2.6))
	L.caja(r, "Marco", Vector3(0, 0.025, 0), Vector3(1.5, 0.02, 0.55), L.mat(Color(0.1, 0.11, 0.14), 0.6, 0.4))
	return r

static func marco_puerta() -> Node3D:
	var r := Node3D.new()
	r.name = "marco_puerta"
	var gris := L.mat(Color(0.12, 0.14, 0.18), 0.65, 0.35)
	var luz := L.mat(Color(0.1, 0.8, 1.0), 0, 0.3, Color(0.1, 0.8, 1.0), 2.6)
	for s in [-1, 1]:
		L.caja(r, "Jamba", Vector3(s * 0.68, 1.1, 0), Vector3(0.10, 2.2, 0.32), gris)
		L.caja(r, "JambaLuz", Vector3(s * 0.62, 1.1, -0.16), Vector3(0.012, 2.1, 0.01), luz)
	L.caja(r, "Dintel", Vector3(0, 2.25, 0), Vector3(1.46, 0.14, 0.32), gris)
	L.caja(r, "DintelLuz", Vector3(0, 2.17, -0.16), Vector3(1.3, 0.012, 0.01), luz)
	return r

static func holoproyector() -> Node3D:
	var r := Node3D.new()
	r.name = "holoproyector"
	var gris := L.mat(Color(0.09, 0.10, 0.13), 0.7, 0.3)
	var luz := L.mat(Color(0.1, 0.8, 1.0), 0, 0.3, Color(0.1, 0.8, 1.0), 3.0)
	L.cil(r, "Disco", Vector3(0, 0.02, 0), 0.8, 0.04, gris)
	L.toro(r, "Aro", Vector3(0, 0.045, 0), 0.74, 0.79, luz)
	L.toro(r, "AroInterno", Vector3(0, 0.045, 0), 0.38, 0.40, luz)
	return r

static func nucleo_eva() -> Node3D:
	## Pared del núcleo de EVA: anillo con el «ojo», rendijas de luz y parlantes a los costados. Delante, nada.
	var r := Node3D.new()
	r.name = "nucleo_eva"
	var oscuro := L.mat(Color(0.05, 0.06, 0.08), 0.8, 0.25)
	var luz := L.mat(Color(0.1, 0.8, 1.0), 0, 0.3, Color(0.1, 0.8, 1.0), 2.8)
	L.caja(r, "Fondo", Vector3(0, 1.6, 0), Vector3(5.6, 3.2, 0.12), oscuro)
	L.toro(r, "AroExterior", Vector3(0, 1.7, -0.07), 1.20, 1.30, luz, Vector3(90, 0, 0))
	L.toro(r, "AroInterior", Vector3(0, 1.7, -0.07), 0.86, 0.90, oscuro, Vector3(90, 0, 0))
	var ojo := L.mat_tex(P + "eva_nucleo.png", 2.4)
	L.pantalla(r, "Ojo", Vector3(0, 1.7, -0.075), 1.76, 1.76, ojo)
	for s in [-1, 1]:
		for i in 9:
			L.caja(r, "Parlante%d_%d" % [s, i], Vector3(s * (1.9 + (i % 3) * 0.17), 1.1 + int(i / 3) * 0.55, -0.065), Vector3(0.1, 0.4, 0.02), L.mat(Color(0.09, 0.11, 0.15), 0.5, 0.4, Color(0.1, 0.6, 0.8), 0.5))
		L.caja(r, "Rendija%d" % s, Vector3(s * 1.6, 1.7, -0.065), Vector3(0.025, 2.2, 0.01), luz)
	return r

static func ventanal(ancho := 4.0, alto := 2.2) -> Node3D:
	var r := Node3D.new()
	r.name = "ventanal"
	var marco := L.mat(Color(0.10, 0.12, 0.16), 0.7, 0.3)
	L.caja(r, "Vidrio", Vector3(0, alto / 2, 0), Vector3(ancho, alto, 0.03), L.mat(Color(0.6, 0.8, 1.0), 0.0, 0.05, Color(0, 0, 0), 0.0, 0.06))
	for x in [-ancho / 2, ancho / 2]:
		L.caja(r, "MarcoV", Vector3(x, alto / 2, 0), Vector3(0.14, alto + 0.14, 0.2), marco)
	for y in [0.0, alto]:
		L.caja(r, "MarcoH", Vector3(0, y, 0), Vector3(ancho + 0.14, 0.14, 0.2), marco)
	for i in 3:
		L.caja(r, "Divisor%d" % i, Vector3(-ancho / 2 + (i + 1) * ancho / 4, alto / 2, 0), Vector3(0.05, alto, 0.1), marco)
	return r

static func consola_central() -> Node3D:
	## Central de control curva (versión propia): tres tramos inclinados con botoneras y pantallas.
	var r := Node3D.new()
	r.name = "consola_central"
	var cuerpo := L.mat(Color(0.10, 0.12, 0.16), 0.7, 0.3)
	var luz := L.mat(Color(0.1, 0.8, 1.0), 0, 0.3, Color(0.1, 0.8, 1.0), 2.6)
	var botones := L.mat_tex(P + "botonera.png", 2.0)
	var pant := [L.mat_tex(P + "comunicaciones.png"), L.mat_tex(P + "mapa_estelar.png"), L.mat_tex(P + "estado_nave.png")]
	for i in 3:
		var ang := (i - 1) * 28.0
		var seg := L.nodo(r, "Tramo%d" % i, Vector3(sin(deg_to_rad(ang)) * 1.7, 0, -(1.0 - cos(deg_to_rad(ang))) * 1.7), Vector3(0, ang, 0))
		L.caja(seg, "Cuerpo", Vector3(0, 0.45, 0), Vector3(1.6, 0.9, 0.9), cuerpo)
		L.caja(seg, "Tapa", Vector3(0, 0.92, 0), Vector3(1.64, 0.05, 0.94), L.mat(Color(0.06, 0.08, 0.12), 0.5, 0.3))
		L.pantalla(seg, "Botonera", Vector3(0, 0.955, -0.12), 1.4, 0.5, botones, Vector3(-90, 0, 0))
		L.caja(seg, "LuzBase", Vector3(0, 0.12, -0.452), Vector3(1.5, 0.02, 0.01), luz)
		L.caja(seg, "Marco", Vector3(0, 1.5, 0.3), Vector3(1.5, 0.82, 0.05), cuerpo, Vector3(-6, 0, 0))
		L.pantalla(seg, "Pantalla", Vector3(0, 1.5, 0.272), 1.4, 0.74, pant[i], Vector3(-6, 0, 0))
	return r

static func camilla() -> Node3D:
	var r := Node3D.new()
	r.name = "camilla"
	var gris := L.mat(Color(0.82, 0.86, 0.9), 0.5, 0.3)
	var luz := L.mat(Color(0.2, 1.0, 0.6), 0, 0.3, Color(0.2, 1.0, 0.6), 2.2)
	L.caja(r, "Colchon", Vector3(0, 0.82, 0), Vector3(0.8, 0.12, 2.0), L.mat(Color(0.75, 0.82, 0.9), 0, 0.7))
	L.caja(r, "Estructura", Vector3(0, 0.74, 0), Vector3(0.7, 0.05, 1.9), gris)
	L.caja(r, "Pie", Vector3(0, 0.37, 0), Vector3(0.28, 0.74, 0.5), gris)
	L.caja(r, "Base", Vector3(0, 0.03, 0), Vector3(0.9, 0.06, 0.9), L.mat(Color(0.14, 0.15, 0.18), 0.6, 0.4))
	L.caja(r, "Luz", Vector3(0.4, 0.8, 0), Vector3(0.01, 0.01, 1.8), luz)
	return r

static func casco() -> Node3D:
	var r := Node3D.new()
	r.name = "casco"
	L.esf(r, "Cascara", Vector3(0, 0.15, 0), 0.15, L.mat(Color(0.85, 0.86, 0.88), 0.4, 0.3), Vector3(1, 1.05, 1.1))
	L.esf(r, "Visor", Vector3(0, 0.16, -0.085), 0.12, L.mat(Color(0.05, 0.08, 0.12), 0.9, 0.1, Color(1.0, 0.6, 0.2), 0.4), Vector3(1.0, 0.6, 0.6))
	L.cil(r, "Cuello", Vector3(0, 0.02, 0), 0.11, 0.04, L.mat(Color(0.15, 0.16, 0.2), 0.7, 0.3))
	return r

static func barra_cocina() -> Node3D:
	var r := Node3D.new()
	r.name = "barra_cocina"
	var cuerpo := L.mat(Color(0.82, 0.85, 0.88), 0.3, 0.35)
	var tapa := L.mat(Color(0.10, 0.12, 0.16), 0.6, 0.25)
	var luz := L.mat(Color(0.1, 0.8, 1.0), 0, 0.3, Color(0.1, 0.8, 1.0), 2.2)
	L.caja(r, "Cuerpo", Vector3(0, 0.45, 0), Vector3(3.2, 0.9, 0.7), cuerpo)
	L.caja(r, "Tapa", Vector3(0, 0.92, 0), Vector3(3.24, 0.05, 0.74), tapa)
	for i in 4:
		L.caja(r, "Puerta%d" % i, Vector3(-1.2 + i * 0.8, 0.45, -0.355), Vector3(0.76, 0.8, 0.01), L.mat(Color(0.7, 0.74, 0.78), 0.3, 0.4))
	L.caja(r, "LuzBajo", Vector3(0, 0.06, -0.36), Vector3(3.1, 0.012, 0.01), luz)
	L.caja(r, "Dispensador", Vector3(-1.0, 1.15, 0.1), Vector3(0.55, 0.45, 0.3), L.mat(Color(0.14, 0.16, 0.2), 0.6, 0.3))
	L.caja(r, "DispLuz", Vector3(-1.0, 1.2, -0.056), Vector3(0.4, 0.2, 0.01), L.mat(Color(0.1, 0.8, 1.0), 0, 0.3, Color(0.1, 0.8, 1.0), 2.0))
	L.cil(r, "Cafetera", Vector3(0.6, 1.1, 0.0), 0.11, 0.3, L.mat(Color(0.2, 0.22, 0.26), 0.7, 0.3))
	L.cil(r, "Taza", Vector3(0.1, 0.99, -0.1), 0.045, 0.09, L.mat(Color(0.95, 0.95, 0.97), 0, 0.3))
	return r

static func microscopio() -> Node3D:
	var r := Node3D.new()
	r.name = "microscopio"
	var g := L.mat(Color(0.88, 0.9, 0.93), 0.4, 0.3)
	var n := L.mat(Color(0.12, 0.13, 0.16), 0.7, 0.3)
	L.caja(r, "Base", Vector3(0, 0.02, 0), Vector3(0.22, 0.04, 0.3), g)
	L.cil(r, "Columna", Vector3(0, 0.18, 0.1), 0.025, 0.32, g, Vector3.ZERO, 16)
	L.cil(r, "Tubo", Vector3(0, 0.30, -0.02), 0.035, 0.26, n, Vector3(-30, 0, 0), 16)
	L.cil(r, "Platina", Vector3(0, 0.12, -0.04), 0.07, 0.015, n, Vector3.ZERO, 20)
	L.caja(r, "Led", Vector3(0, 0.07, -0.04), Vector3(0.04, 0.01, 0.04), L.mat(Color(0.2, 1.0, 0.6), 0, 0.3, Color(0.2, 1.0, 0.6), 3.0))
	return r

static func terrario() -> Node3D:
	var r := Node3D.new()
	r.name = "terrario"
	var vid := L.mat(Color(0.7, 0.9, 1.0), 0.0, 0.05, Color(0, 0, 0), 0.0, 0.2)
	L.caja(r, "Base", Vector3(0, 0.03, 0), Vector3(0.7, 0.06, 0.4), L.mat(Color(0.12, 0.13, 0.16), 0.6, 0.4))
	L.caja(r, "Tierra", Vector3(0, 0.09, 0), Vector3(0.66, 0.06, 0.36), L.mat(Color(0.18, 0.11, 0.07), 0, 0.95))
	var rng := RandomNumberGenerator.new()
	rng.seed = 4
	for i in 7:
		var h := rng.randf_range(0.1, 0.26)
		L.cil(r, "Tallo%d" % i, Vector3(-0.27 + i * 0.09, 0.12 + h / 2, rng.randf_range(-0.1, 0.1)), 0.008, h, L.mat(Color(0.2, 0.55, 0.2)), Vector3.ZERO, 8)
		L.esf(r, "Hoja%d" % i, Vector3(-0.27 + i * 0.09, 0.12 + h, 0), 0.05, L.mat(Color(0.25, 0.72, 0.3), 0, 0.6, Color(0.1, 0.4, 0.15), 0.3), Vector3(1.3, 0.7, 1))
	L.caja(r, "Vidrio", Vector3(0, 0.23, 0), Vector3(0.7, 0.34, 0.4), vid)
	L.caja(r, "Luz", Vector3(0, 0.41, 0), Vector3(0.7, 0.015, 0.4), L.mat(Color(0.9, 1.0, 0.95), 0, 0.3, Color(0.9, 1.0, 0.95), 2.2))
	return r

static func soporte_suero() -> Node3D:
	var r := Node3D.new()
	r.name = "soporte_suero"
	var g := L.mat(Color(0.78, 0.8, 0.84), 0.7, 0.3)
	L.cil(r, "Base", Vector3(0, 0.03, 0), 0.22, 0.04, g, Vector3.ZERO, 20)
	L.cil(r, "Mastil", Vector3(0, 0.9, 0), 0.015, 1.8, g, Vector3.ZERO, 12)
	L.caja(r, "Bolsa", Vector3(0, 1.62, -0.05), Vector3(0.12, 0.2, 0.03), L.mat(Color(0.85, 0.95, 1.0), 0, 0.2, Color(0.4, 0.8, 1.0), 0.6, 0.7))
	L.caja(r, "Monitor", Vector3(0, 1.2, -0.04), Vector3(0.18, 0.12, 0.03), L.mat(Color(0.1, 0.8, 0.6), 0, 0.3, Color(0.2, 1.0, 0.6), 2.0))
	return r
