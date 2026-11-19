## ETAPA 3 — Animación (30 s a 30 fps): cámara en UN movimiento continuo de derecha a izquierda (sin cortes),
## aspas del ventilador girando, destellos del relámpago (luz, cielo y rayo) y parpadeo de la luz del hogar.
## La cámara se muestrea cuadro por cuadro (claves lineales): así el GLB y Blender la reciben exacta.
class_name E3Animacion
extends RefCounted

const FPS := 30
const DURACION := 30.0
const RPS_VENTILADOR := 1.3
## (segundo, posición, yaw°, pitch°) — yaw positivo gira hacia −X (izquierda)
const PASOS := [
	[0.0, Vector3(10.4, 1.55, 2.2), -10.0, -8.0],    # cocina
	[2.5, Vector3(9.4, 1.5, 2.0), -4.0, -10.0],
	[5.0, Vector3(7.2, 1.5, 2.0), 0.0, -10.0],        # mesas y living
	[7.5, Vector3(5.6, 1.45, 1.9), 2.0, -14.0],
	[10.0, Vector3(3.6, 1.45, 1.8), 4.0, -8.0],       # ventilador
	[12.0, Vector3(2.3, 1.55, 1.5), 14.0, 20.0],
	[14.0, Vector3(0.9, 1.5, 1.6), 6.0, 4.0],         # ventanal, camioneta, farolas, lluvia
	[17.5, Vector3(-1.6, 1.4, 1.7), 4.0, 0.0],
	[21.0, Vector3(-3.0, 1.4, 1.4), 0.0, 5.0],        # tormenta y relámpagos
	[24.0, Vector3(-4.8, 1.45, 1.3), -2.0, 9.0],
	[26.0, Vector3(-6.2, 1.4, 1.4), 8.0, 2.0],        # hogar
	[30.0, Vector3(-7.5, 1.15, 0.6), 16.0, -7.0],
]
## destellos: (segundo, intensidad 0..1, con rayo visible)
const DESTELLOS := [[14.6, 0.35, false], [17.8, 0.6, false], [21.3, 1.0, true], [22.6, 0.5, false],
	[24.2, 1.0, true], [25.4, 0.4, false], [28.4, 0.3, false]]


static func _muestra(t: float) -> Array:
	var n := PASOS.size()
	var i := 0
	while i < n - 2 and t > PASOS[i + 1][0]:
		i += 1
	var vals := []
	for idx in [i, i + 1]:
		var p: Array = PASOS[idx]
		vals.append([p[1].x, p[1].y, p[1].z, p[2], p[3]])
	var t0: float = PASOS[i][0]
	var t1: float = PASOS[i + 1][0]
	var h := t1 - t0
	var u := clampf((t - t0) / h, 0.0, 1.0)
	var res := []
	for c in 5:
		var tg := []
		for idx in [i, i + 1]:
			if idx == 0 or idx == n - 1:
				tg.append(0.0)
			else:
				var a: Array = PASOS[idx - 1]
				var b: Array = PASOS[idx + 1]
				var va := [a[1].x, a[1].y, a[1].z, a[2], a[3]][c] as float
				var vb := [b[1].x, b[1].y, b[1].z, b[2], b[3]][c] as float
				tg.append((vb - va) / (b[0] - a[0]))
		var p0: float = vals[0][c]
		var p1: float = vals[1][c]
		var u2 := u * u
		var u3 := u2 * u
		res.append((2 * u3 - 3 * u2 + 1) * p0 + (u3 - 2 * u2 + u) * h * tg[0] + (-2 * u3 + 3 * u2) * p1 + (u3 - u2) * h * tg[1])
	return res

static func crear(raiz: Node3D) -> void:
	var cam := Camera3D.new()
	cam.name = "Camara"
	cam.fov = 68.0
	cam.near = 0.05
	cam.far = 300.0
	raiz.add_child(cam)
	var anim := Animation.new()
	anim.length = DURACION
	anim.step = 1.0 / FPS
	# cámara
	var tp := anim.add_track(Animation.TYPE_POSITION_3D)
	var tr := anim.add_track(Animation.TYPE_ROTATION_3D)
	anim.track_set_path(tp, "Camara")
	anim.track_set_path(tr, "Camara")
	for f in int(DURACION * FPS) + 1:
		var t := float(f) / FPS
		var s := _muestra(t)
		anim.position_track_insert_key(tp, t, Vector3(s[0], s[1], s[2]))
		anim.rotation_track_insert_key(tr, t, Quaternion.from_euler(Vector3(deg_to_rad(s[4]), deg_to_rad(s[3]), 0)))
	var p0 := _muestra(0.0)
	cam.position = Vector3(p0[0], p0[1], p0[2])
	cam.rotation = Vector3(deg_to_rad(p0[4]), deg_to_rad(p0[3]), 0)
	# ventilador: una clave cada 1/8 de vuelta (el cuaternión siempre toma el camino corto)
	var tv := anim.add_track(Animation.TYPE_ROTATION_3D)
	anim.track_set_path(tv, "Ventilador/Ventilador_aspas")
	var paso := 1.0 / (RPS_VENTILADOR * 8.0)
	var k := 0
	while k * paso <= DURACION + 1e-4:
		anim.rotation_track_insert_key(tv, k * paso, Quaternion(Vector3.UP, -k * TAU / 8.0))
		k += 1
	# relámpagos
	var te := anim.add_track(Animation.TYPE_VALUE)
	anim.track_set_path(te, "Luces/Relampago_luz:light_energy")
	var tc := anim.add_track(Animation.TYPE_SCALE_3D)
	anim.track_set_path(tc, "Luces/Relampago_cielo")
	var tb := anim.add_track(Animation.TYPE_SCALE_3D)
	anim.track_set_path(tb, "Exterior/Relampago_rayo")
	var apagado := Vector3.ONE * 0.001
	anim.track_insert_key(te, 0.0, 0.0)
	anim.scale_track_insert_key(tc, 0.0, apagado)
	anim.scale_track_insert_key(tb, 0.0, apagado)
	var dt := 1.0 / FPS
	for d in DESTELLOS:
		var t0: float = d[0]
		var a: float = d[1]
		var forma := [[-dt, 0.0], [0.0, 1.0], [2 * dt, 0.35], [4 * dt, 0.85], [7 * dt, 0.2], [10 * dt, 0.5], [16 * dt, 0.0]]
		for fk in forma:
			anim.track_insert_key(te, t0 + fk[0], 7.0 * a * fk[1])
			anim.scale_track_insert_key(tc, t0 + fk[0], Vector3.ONE * maxf(0.001, a * fk[1]))
		if d[2]:
			anim.scale_track_insert_key(tb, t0 - dt, apagado)
			anim.scale_track_insert_key(tb, t0, Vector3.ONE)
			anim.scale_track_insert_key(tb, t0 + 5 * dt, Vector3.ONE)
			anim.scale_track_insert_key(tb, t0 + 6 * dt, apagado)
	anim.track_insert_key(te, DURACION, 0.0)
	anim.scale_track_insert_key(tc, DURACION, apagado)
	anim.scale_track_insert_key(tb, DURACION, apagado)
	# fuego: parpadeo con semilla fija (siempre igual)
	var tf := anim.add_track(Animation.TYPE_VALUE)
	anim.track_set_path(tf, "Luces/Luz_fuego:light_energy")
	var rng := RandomNumberGenerator.new()
	rng.seed = 7
	var tt := 0.0
	while tt <= DURACION:
		anim.track_insert_key(tf, tt, rng.randf_range(1.5, 2.5))
		tt += rng.randf_range(0.07, 0.16)
	var lib := AnimationLibrary.new()
	lib.add_animation("toma", anim)
	var ap := AnimationPlayer.new()
	ap.name = "Animacion"
	ap.add_animation_library("", lib)
	ap.autoplay = "toma"
	raiz.add_child(ap)
