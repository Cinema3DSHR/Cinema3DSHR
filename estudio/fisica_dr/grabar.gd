extends SceneTree
## Grabador de física para películas: corre la física REAL de Dream Rally (godot/game/physics/vehicle_physics.gd, sin
## cambios, 120 Hz con 2 subpasos) con un conductor que sigue la trayectoria de la escena, y graba por cuadro el estado
## de cada vehículo (carrocería, suspensión, giro y dirección de cada rueda, régimen, deslizamiento).
##
## Uso: godot --headless --path <proyecto con game/physics y game/data de Dream Rally> --script grabar.gd -- plan.json salida.json
## Coordenadas de entrada y salida: las de Blender (Z arriba). Por dentro, las del juego: (x, y, z)_godot = (x, z, −y)_blender.
##
## Plan: {fps, hz, cuadros, suelo:{tipo:"plano", altura} | {tipo:"rejilla", x0, y0, paso, nx, ny, alturas:[…] (fila por y)},
##        vehiculos:[{id, dr (id de vehicles.json), params:{…} (pisan los de fábrica), ruta:[[x,y]…], horario:[[t, s]…],
##                    previo_s, eventos:[{t0, t1, freno_mano, gas, freno, volante, volante_extra}]}]}

const VehiclePhysics := preload("res://game/physics/vehicle_physics.gd")
const VehicleParams := preload("res://game/physics/vehicle_params.gd")
const TrackBase := preload("res://game/physics/track_base.gd")
const CarBuild := preload("res://game/data/car_build.gd")

class Suelo extends "res://game/physics/track_base.gd":
	var tipo := "plano"
	var altura := 0.0
	var x0 := 0.0
	var y0 := 0.0
	var paso := 1.0
	var nx := 1
	var ny := 1
	var h := PackedFloat64Array()
	var superficie := 0

	func ground_info(x: float, z: float) -> Vector2:
		if tipo == "plano":
			return Vector2(altura, superficie)
		var bx := x
		var by := -z
		var fx := clampf((bx - x0) / paso, 0.0, nx - 1.001)
		var fy := clampf((by - y0) / paso, 0.0, ny - 1.001)
		var i := int(fx)
		var j := int(fy)
		var u := fx - i
		var v := fy - j
		var a := h[j * nx + i]
		var b := h[j * nx + i + 1]
		var c := h[(j + 1) * nx + i]
		var d := h[(j + 1) * nx + i + 1]
		return Vector2(lerpf(lerpf(a, b, u), lerpf(c, d, u), v), superficie)

class Ruta:
	var p: PackedVector2Array = PackedVector2Array()   # en el plano del juego (x, z)
	var s: PackedFloat64Array = PackedFloat64Array()
	var largo := 0.0

	func _init(puntos: Array) -> void:
		var acc := 0.0
		for i in puntos.size():
			var q := Vector2(float(puntos[i][0]), -float(puntos[i][1]))
			if i > 0:
				acc += q.distance_to(p[i - 1])
			p.append(q)
			s.append(acc)
		largo = acc

	func en(si: float) -> Vector2:
		if si <= 0.0:
			var t := (p[1] - p[0]).normalized()
			return p[0] + t * si
		if si >= largo:
			var t2 := (p[p.size() - 1] - p[p.size() - 2]).normalized()
			return p[p.size() - 1] + t2 * (si - largo)
		var lo := 0
		var hi := s.size() - 1
		while hi - lo > 1:
			var m := (lo + hi) >> 1
			if s[m] <= si:
				lo = m
			else:
				hi = m
		var k := (si - s[lo]) / maxf(1e-6, s[hi] - s[lo])
		return p[lo].lerp(p[hi], k)

	func tangente(si: float) -> Vector2:
		return (en(si + 1.0) - en(si - 1.0)).normalized()

	## s más cercano a q, buscando cerca de s0
	func proyectar(q: Vector2, s0: float) -> float:
		var mejor := s0
		var dmin := INF
		var a := s0 - 25.0
		while a <= s0 + 25.0:
			var d := en(a).distance_squared_to(q)
			if d < dmin:
				dmin = d
				mejor = a
			a += 0.25
		return mejor

class Conductor:
	var ruta: Ruta
	var horario: Array        # [[t, s]…] ordenado
	var eventos: Array
	var s_act := 0.0
	var integ := 0.0

	func s_obj(t: float) -> Array:
		## [s objetivo, velocidad objetivo] interpolando el horario (antes del primer punto: velocidad constante)
		var H := horario
		if t <= float(H[0][0]):
			var v0 := (float(H[1][1]) - float(H[0][1])) / maxf(1e-6, float(H[1][0]) - float(H[0][0]))
			return [float(H[0][1]) + v0 * (t - float(H[0][0])), v0]
		for i in range(1, H.size()):
			if t <= float(H[i][0]):
				var t0 := float(H[i - 1][0])
				var t1 := float(H[i][0])
				var k := (t - t0) / maxf(1e-6, t1 - t0)
				var v := (float(H[i][1]) - float(H[i - 1][1])) / maxf(1e-6, t1 - t0)
				return [lerpf(float(H[i - 1][1]), float(H[i][1]), k), v]
		var n := H.size()
		var vf := (float(H[n - 1][1]) - float(H[n - 2][1])) / maxf(1e-6, float(H[n - 1][0]) - float(H[n - 2][0]))
		return [float(H[n - 1][1]) + vf * (t - float(H[n - 1][0])), vf]

	func manejar(ph: VehiclePhysics, t: float, h: float) -> Array:
		var q := Vector2(ph.px, ph.pz)
		s_act = ruta.proyectar(q, s_act)
		var so: Array = s_obj(t)
		var v := ph.vLong
		var v_cmd := maxf(0.0, float(so[1]) + 0.6 * (float(so[0]) - s_act))
		var err := v_cmd - v
		integ = clampf(integ + err * h, -6.0, 6.0)
		var a_req := 1.6 * err + 0.35 * integ
		var thr := clampf(a_req / 3.0 + 0.12 * clampf(v_cmd / 25.0, 0.0, 1.0), 0.0, 1.0)
		var brk := clampf(-a_req / 7.0, 0.0, 1.0)
		if v_cmd < 0.3 and v < 0.5:
			thr = 0.0
			brk = 1.0
		# pure pursuit sobre la trayectoria
		var ld := clampf(4.0 + 0.42 * absf(v), 5.0, 32.0)
		var obj := ruta.en(s_act + ld)
		var fwd := Vector2(sin(ph.yaw), cos(ph.yaw))
		var izq := Vector2(cos(ph.yaw), -sin(ph.yaw))
		var d := obj - q
		var alpha := atan2(d.dot(izq), d.dot(fwd))
		var delta := atan(2.0 * ph.V.wheelBase * sin(alpha) / ld)    # + = a la izquierda
		var spd := sqrt(ph.vx * ph.vx + ph.vz * ph.vz)
		var st := clampf(-delta / (ph.V.maxSteer * ph.steer_scale(spd)), -1.0, 1.0)
		var hb := false
		for e in eventos:
			if t >= float(e["t0"]) and t < float(e["t1"]):
				if e.has("gas"):
					thr = float(e["gas"])
				if e.has("freno"):
					brk = float(e["freno"])
				if e.has("volante"):
					st = float(e["volante"])
				st = clampf(st + float(e.get("volante_extra", 0.0)), -1.0, 1.0)
				hb = bool(e.get("freno_mano", false))
		return [thr, brk, st, hb]

## Cabina y tripulación de Dream Rally (car/cockpit.gd: habitáculo, butacas, tablero, volante, palancas, pedales y los dos
## pilotos con su cinemática inversa y sus fuerzas G) movidas cuadro a cuadro por el mismo estado de la física, grabadas en
## una animación y exportadas a GLB (ejes del modelo del auto: +z adelante, +x izquierda, y desde el piso).
class Grabadora:
	var nodo
	var snap: RefCounted
	var fps := 30
	var anim := Animation.new()
	var huesos := []      # [{skel, i, pista_r, pista_p}]
	var piezas := []      # [{nodo, pista_p, pista_r}]
	var opciones: Dictionary
	var n := 0

	func _init(op: Dictionary, V, p_fps: int) -> void:
		opciones = op
		fps = p_fps
		var Cockpit = load("res://game/car/cockpit.gd")
		var Snap = load("res://game/car/car_snapshot.gd")
		var pin: Array = op.get("pintura", [0.1, 0.31, 0.88])
		var acc: Array = op.get("acento", [1.0, 0.42, 0.03])
		nodo = Cockpit.new(str(op["tipo"]), Color(pin[0], pin[1], pin[2]), Color(acc[0], acc[1], acc[2]))
		nodo.name = "cabina_" + str(op["tipo"])
		nodo.set_engine(V.maxRpm, V.shiftUpRpm)
		snap = Snap.new()

	func _preparar() -> void:
		for r in nodo.rig:
			var sk: Skeleton3D = r.skel
			for i in sk.get_bone_count():
				var base := str(nodo.get_path_to(sk)) + ":" + sk.get_bone_name(i)
				var pr := anim.add_track(Animation.TYPE_ROTATION_3D)
				anim.track_set_path(pr, NodePath(base))
				var pp := -1
				if i == r.B["Hips"]:
					pp = anim.add_track(Animation.TYPE_POSITION_3D)
					anim.track_set_path(pp, NodePath(base))
				huesos.append({"skel": sk, "i": i, "r": pr, "p": pp})
		for nm in ["rim", "gear_lever", "hb_lever", "pedal_thr", "pedal_brk", "notes"]:
			var nd: Node3D = nodo.get(nm)
			if nd == null:
				continue
			nd.name = "cab_" + nm
			var ruta := str(nodo.get_path_to(nd))
			var pp2 := anim.add_track(Animation.TYPE_POSITION_3D)
			anim.track_set_path(pp2, NodePath(ruta))
			var pr2 := anim.add_track(Animation.TYPE_ROTATION_3D)
			anim.track_set_path(pr2, NodePath(ruta))
			piezas.append({"nodo": nd, "p": pp2, "r": pr2})

	func cuadro(f: int, t: float, freno_mano: bool) -> void:
		if n == 0:
			nodo.set_inside(true, true)
			_preparar()
		n += 1
		snap.sample(t)
		var dt := 1.0 / fps
		nodo.update_crew(dt, snap, freno_mano, t, float(opciones.get("rugosidad", 0.0)))
		nodo.update_cabin(dt, snap, freno_mano, t)
		var tk := float(f) / fps
		for hb in huesos:
			var sk: Skeleton3D = hb["skel"]
			anim.rotation_track_insert_key(hb["r"], tk, sk.get_bone_pose_rotation(hb["i"]))
			if hb["p"] >= 0:
				anim.position_track_insert_key(hb["p"], tk, sk.get_bone_pose_position(hb["i"]))
		for pz in piezas:
			var nd: Node3D = pz["nodo"]
			anim.position_track_insert_key(pz["p"], tk, nd.position)
			anim.rotation_track_insert_key(pz["r"], tk, nd.quaternion)

	func exportar() -> String:
		anim.length = float(n + 1) / fps
		var ap := AnimationPlayer.new()
		ap.name = "animacion"
		var lib := AnimationLibrary.new()
		lib.add_animation("cabina", anim)
		nodo.add_child(ap)
		ap.add_animation_library("", lib)
		# nombre de cada malla del interior según su material (roof, door, glass… se pueden esconder desde afuera)
		var claves := {}
		for k in nodo._mats:
			claves[nodo._mats[k]] = k
		var j := 0
		for c in nodo.interior.get_children():
			if c is MeshInstance3D and claves.has((c as MeshInstance3D).material_override):
				c.name = "cab_%s_%d" % [claves[(c as MeshInstance3D).material_override], j]
				j += 1
		# lo escondido (gotas de lluvia, domo, etc.) no se exporta: el glTF lo marcaría con KHR_node_visibility
		var pila: Array = [nodo]
		var fuera: Array = []
		while pila.size() > 0:
			var x: Node = pila.pop_back()
			for c in x.get_children():
				if c is SubViewport or c is Label3D or (c is Node3D and not (c as Node3D).visible):
					fuera.append(c)
				else:
					pila.append(c)
		for c in fuera:
			c.get_parent().remove_child(c)
			c.free()
		var doc := GLTFDocument.new()
		var st := GLTFState.new()
		var err := doc.append_from_scene(nodo, st)
		if err == OK:
			err = doc.write_to_filesystem(st, str(opciones["glb"]))
		return str(opciones["glb"]) if err == OK else "error %d" % err

func _process(_d: float) -> bool:
	var args := OS.get_cmdline_user_args()
	var plan: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	var base_veh: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://game/data/vehicles.json"))
	var fps := int(plan.get("fps", 30))
	var hz := int(plan.get("hz", 120))
	var cuadros := int(plan["cuadros"])
	var sp: Dictionary = plan.get("suelo", {"tipo": "plano", "altura": 0.0})
	var suelo := Suelo.new()
	suelo.tipo = str(sp.get("tipo", "plano"))
	suelo.altura = float(sp.get("altura", 0.0))
	suelo.superficie = int(sp.get("superficie", 0))
	if suelo.tipo == "rejilla":
		suelo.x0 = float(sp["x0"])
		suelo.y0 = float(sp["y0"])
		suelo.paso = float(sp["paso"])
		suelo.nx = int(sp["nx"])
		suelo.ny = int(sp["ny"])
		suelo.h = PackedFloat64Array(sp["alturas"])
	var W := Basis(Vector3(1, 0, 0), Vector3(0, 0, 1), Vector3(0, -1, 0))   # columnas: juego → Blender
	var M := Basis(Vector3(-1, 0, 0), Vector3(0, 0, 1), Vector3(0, 1, 0))   # local Blender (X der, Y adelante, Z arriba) ↔ local juego
	var salida := {"fps": fps, "hz": hz, "cuadros": cuadros, "vehiculos": {}}
	for vp in plan["vehiculos"]:
		var d: Dictionary = CarBuild.build_params(base_veh[str(vp["dr"])], {})
		for k in (vp.get("params", {}) as Dictionary):
			d[k] = vp["params"][k]
		var V: VehicleParams = VehicleParams.from_dict(d)
		var ph := VehiclePhysics.new(suelo, V)
		var ruta := Ruta.new(vp["ruta"])
		var cond := Conductor.new()
		cond.ruta = ruta
		cond.horario = vp["horario"]
		cond.eventos = vp.get("eventos", [])
		var previo := float(vp.get("previo_s", 3.0))
		var t := -previo
		var so: Array = cond.s_obj(t)
		cond.s_act = float(so[0])
		var p0 := ruta.en(cond.s_act)
		var tg := ruta.tangente(cond.s_act)
		var yaw := atan2(tg.x, tg.y)
		ph.reset(p0.x, p0.y, yaw)
		var v0 := float(so[1])
		ph.vx = sin(yaw) * v0
		ph.vz = cos(yaw) * v0
		ph.vLong = v0
		for w in ph.wheels:
			w.omega = v0 / V.wheelRadius
		if V.gears.size() > 0 and v0 > 1.0:
			var g := 1
			for gi in V.gears.size():
				var r: float = v0 / V.wheelRadius * V.gears[gi] * V.finalDrive * 60.0 / TAU
				if r > V.shiftDownRpm * 1.15:
					g = gi + 1
			ph.gear = g
			ph.clutchLocked = true
			ph.rpm = v0 / V.wheelRadius * V.gears[g - 1] * V.finalDrive * 60.0 / TAU
		var h := 1.0 / hz
		var sub := int(hz / fps)
		var base: float = V.comHeight + V.hardpointY - V.rideOffset
		var ang := [0.0, 0.0, 0.0, 0.0]
		var reg := {"pos": [], "rot": [], "ruedas_z": [], "ruedas_giro": [], "direccion": [], "v": [], "rpm": [], "marcha": [],
					"desliz": [], "contacto": [], "entradas": []}
		var n_prev := int(round(previo * hz))
		var total := n_prev + cuadros * sub
		var ent := [0.0, 0.0, 0.0, false]
		var cab: Grabadora = null
		if vp.has("cabina"):
			cab = Grabadora.new(vp["cabina"], V, fps)
			root.add_child(cab.nodo)
		for i in total:
			var tt := -previo + i * h
			ent = cond.manejar(ph, tt, h)
			ph.step(h, ent[0], ent[1], ent[2], ent[3])
			for k in 4:
				ang[k] += ph.wheels[k].omega * h
			if cab != null:
				cab.snap.push(tt + h, ph)
			var j := i + 1 - n_prev
			if cab != null and j > 0 and j % sub == 0:
				cab.cuadro(j / sub, tt + h, ent[3])
			if j > 0 and j % sub == 0:
				var B := Basis.from_euler(Vector3(ph.pitch, ph.yaw, ph.roll), EULER_ORDER_YXZ)
				var origen := Vector3(ph.px, ph.py, ph.pz) + B * Vector3(0, -V.comHeight + V.rideOffset, 0)
				var ob := W * origen
				var R := W * B * M
				reg["pos"].append([snappedf(ob.x, 0.0001), snappedf(ob.y, 0.0001), snappedf(ob.z, 0.0001)])
				reg["rot"].append([snappedf(R.x.x, 1e-5), snappedf(R.y.x, 1e-5), snappedf(R.z.x, 1e-5),
								   snappedf(R.x.y, 1e-5), snappedf(R.y.y, 1e-5), snappedf(R.z.y, 1e-5),
								   snappedf(R.x.z, 1e-5), snappedf(R.y.z, 1e-5), snappedf(R.z.z, 1e-5)])
				var zs := []
				var gs := []
				var ds := []
				var cs := []
				for k in 4:
					var w = ph.wheels[k]
					zs.append(snappedf(base - w.s, 0.0001))
					gs.append(snappedf(ang[k], 0.0001))
					ds.append(snappedf(w.slip, 0.001))
					cs.append(1 if w.contact else 0)
				reg["ruedas_z"].append(zs)
				reg["ruedas_giro"].append(gs)
				reg["desliz"].append(ds)
				reg["contacto"].append(cs)
				reg["direccion"].append(snappedf(ph.steerAngle, 0.0001))
				reg["v"].append(snappedf(ph.vLong, 0.001))
				reg["rpm"].append(int(ph.rpm))
				reg["marcha"].append(ph.gear)
				reg["entradas"].append([snappedf(ent[0], 0.01), snappedf(ent[1], 0.01), snappedf(ent[2], 0.01), 1 if ent[3] else 0])
		# orden de las ruedas del juego: 0 del. izq · 1 del. der · 2 tras. izq · 3 tras. der
		reg["ruedas"] = [{"x": -V.trackF / 2.0, "y": ph.a, "delantera": true}, {"x": V.trackF / 2.0, "y": ph.a, "delantera": true},
						 {"x": -V.trackR / 2.0, "y": -ph.b, "delantera": false}, {"x": V.trackR / 2.0, "y": -ph.b, "delantera": false}]
		reg["radio"] = V.wheelRadius
		if cab != null:
			reg["cabina"] = cab.exportar()
		reg["reposo_z"] = base - ph.wheels[0].sStatic
		salida["vehiculos"][str(vp["id"])] = reg
	var f := FileAccess.open(args[1], FileAccess.WRITE)
	f.store_string(JSON.stringify(salida))
	f.close()
	print("fisica_dr: ", (plan["vehiculos"] as Array).size(), " vehículos, ", cuadros, " cuadros")
	quit(0)
	return true
