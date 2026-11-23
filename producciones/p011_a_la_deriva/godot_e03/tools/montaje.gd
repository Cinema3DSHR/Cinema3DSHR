## Monta UNA escena del capítulo 3 sobre la nave única: personajes con clips de Mixamo, cara y labios por la voz real, objetos en las manos,
## mirada, cámaras y línea de tiempo. Todo se hornea a 30 cuadros/s en una Animation; sale un GLB para el visor + un JSON.
## Uso: xvfb-run -a godot --path . --rendering-driver opengl3 --script res://tools/montaje.gd -- <escena> <salida_prefijo> [capturas]
##   <escena> = clave de data/storyboard_e03.json → escenas   ·   salida: <prefijo>.glb, <prefijo>.json, <prefijo>_verif.json
## «capturas» = lista de segundos (p. ej. 1.5,4,9) para guardar fotos fijas de revisión (<prefijo>_t<seg>.png): NO es un render.
extends SceneTree

const FPS := 30.0
const Actor := preload("res://tools/actor.gd")
const Cara := preload("res://tools/cara.gd")

var SB: Dictionary
var esc: Node3D
var anim: Animation
var ap: AnimationPlayer
var actores := {}               # id → Actor
var props := {}                 # id → Node3D
var planes := {}                # id → Array de segmentos
var total := 0
var verif := {"problemas": [], "pies": {}}

func _initialize() -> void:
	var a := OS.get_cmdline_user_args()
	var clave: String = a[0]
	var salida: String = a[1]
	var caps: Array = [] if a.size() < 3 else Array(a[2].split(",")).map(func(s): return float(s))
	var sbj = JSON.parse_string(FileAccess.get_file_as_string("res://data/storyboard_e03.json"))
	SB = sbj["escenas"][clave]
	SB["_global"] = sbj.get("global", {})
	root.size = Vector2i(1280, 720)
	DisplayServer.window_set_size(Vector2i(1280, 720))
	await _montar(clave, salida, caps)
	quit()

# ───────────────────────────────────────────────────────────── montaje
func _montar(clave: String, salida: String, caps: Array) -> void:
	esc = Node3D.new()
	esc.name = "Escena"
	root.add_child(esc)
	var nave: Node3D = load("res://nave.tscn").instantiate()
	esc.add_child(nave)
	total = int(ceil(float(SB["dur"]) * FPS)) + 1
	anim = Animation.new()
	anim.length = float(total - 1) / FPS
	anim.step = 1.0 / FPS
	ap = AnimationPlayer.new()
	ap.name = "Anim"
	esc.add_child(ap)
	# actores
	for id in SB["actores"]:
		var d: Dictionary = SB["actores"][id]
		var ac := Actor.new()
		ac.cargar(id, "res://assets/personajes/%s.glb" % d["modelo"], "res://assets/personajes/%s_meta.json" % d["modelo"], esc)
		_materiales(ac, d)
		actores[id] = ac
		ac.raiz.position = Vector3(d["inicio"]["pos"][0], d["inicio"].get("y", 0.0), d["inicio"]["pos"][1])
		ac.raiz.rotation.y = deg_to_rad(float(d["inicio"]["yaw"]))
		ac.escala = float(d.get("escala", 1.0))
		ac.raiz.scale = Vector3.ONE * ac.escala
	# objetos
	for pid in SB.get("props", {}):
		props[pid] = _crear_prop(pid, SB["props"][pid])
	await process_frame
	# planes
	for id in actores:
		planes[id] = _planificar(id)
	# pista de cada nodo
	anim.loop_mode = Animation.LOOP_NONE
	await _hornear()
	var lib := AnimationLibrary.new()
	lib.add_animation("escena", anim)
	ap.add_animation_library("", lib)
	ap.assigned_animation = "escena"
	await _camaras_y_salida(clave, salida, caps)

func _materiales(ac, d: Dictionary) -> void:
	## Ajustes de materiales para Godot/GLB: traje (azul marino con vivos), botas, pelo sin desaparecer, piel con tono natural y EVA como holograma de revisión.
	var holo: bool = d.get("holograma", false)
	for m in ac.modelo.find_children("*", "MeshInstance3D", true, false):
		var mi: MeshInstance3D = m
		if mi.mesh == null:
			continue
		for s in mi.mesh.get_surface_count():
			var mat := mi.mesh.surface_get_material(s)
			if mat == null:
				continue
			var nm := mat.resource_name
			var nuevo: StandardMaterial3D = null
			if holo:
				nuevo = StandardMaterial3D.new()
				nuevo.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
				nuevo.albedo_color = Color(0.3, 0.7, 1.0, 0.42)
				nuevo.emission_enabled = true
				nuevo.emission = Color(0.15, 0.55, 1.0)
				nuevo.emission_energy_multiplier = 0.9
				nuevo.cull_mode = BaseMaterial3D.CULL_DISABLED
				if nm.begins_with(("EM3D_Cornea")) or nm.begins_with("EM3D_Eye_O") or nm.begins_with("EM3D_Tearline") or nm.begins_with("EM3D_Upper_Teeth") or nm.begins_with("EM3D_Lower_Teeth") or nm.begins_with("EM3D_Tongue"):
					nuevo.albedo_color.a = 0.0       # sin interior de ojos ni boca visible
				if nm.begins_with("traje_luz"):
					nuevo.albedo_color = Color(0.5, 0.9, 1.0, 0.9); nuevo.emission_energy_multiplier = 2.5
			elif nm.begins_with("traje_tela"):
				nuevo = StandardMaterial3D.new(); nuevo.albedo_color = Color(0.035, 0.06, 0.11); nuevo.roughness = 0.5; nuevo.metallic = 0.1
			elif nm.begins_with("traje_luz"):
				nuevo = StandardMaterial3D.new(); nuevo.albedo_color = Color(0.1, 0.75, 1.0); nuevo.emission_enabled = true; nuevo.emission = Color(0.1, 0.75, 1.0); nuevo.emission_energy_multiplier = 3.0
			elif nm.begins_with("traje_bota"):
				nuevo = StandardMaterial3D.new(); nuevo.albedo_color = Color(0.03, 0.032, 0.04); nuevo.roughness = 0.45; nuevo.metallic = 0.15; nuevo.cull_mode = BaseMaterial3D.CULL_DISABLED
			elif nm.begins_with("EM3D_Skin") or nm.begins_with("EM3D_Nails"):
				nuevo = (mat as StandardMaterial3D).duplicate()
				nuevo.albedo_color = Color(nuevo.albedo_color.r * 0.72, nuevo.albedo_color.g * 0.68, nuevo.albedo_color.b * 0.66)
			elif nm.begins_with("Hair") or nm.begins_with("Slicked") or nm.begins_with("Female_Flat") or nm.begins_with("Scalp") or nm.begins_with("Eyebrows") or nm.begins_with("EM3D_Eyelash"):
				nuevo = (mat as StandardMaterial3D).duplicate()
				nuevo.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_DEPTH_PRE_PASS
				nuevo.cull_mode = BaseMaterial3D.CULL_DISABLED
				if "Scalp" in nm:
					if d.has("cuero"):
						var cu: Array = d["cuero"]
						nuevo.albedo_color = Color(cu[0], cu[1], cu[2])      # cuero cabelludo del color del pelo (pelo largo cubre todo)
					else:
						nuevo.albedo_color = Color(nuevo.albedo_color.r * 0.72, nuevo.albedo_color.g * 0.68, nuevo.albedo_color.b * 0.66)
			if nuevo != null:
				mi.set_surface_override_material(s, nuevo)

func _crear_prop(pid: String, d: Dictionary) -> Node3D:
	var n := Node3D.new()
	n.name = pid
	esc.add_child(n)
	var tipo: String = d["tipo"]
	if tipo == "glb":
		var g: Node3D = (load(d["glb"]) as PackedScene).instantiate()
		g.name = "Modelo"
		g.scale = Vector3.ONE * float(d.get("esc", 1.0))
		n.add_child(g)
	elif tipo == "tablet":
		var cuerpo := MeshInstance3D.new(); var bm := BoxMesh.new(); bm.size = Vector3(0.24, 0.015, 0.17); cuerpo.mesh = bm
		var m := StandardMaterial3D.new(); m.albedo_color = Color(0.06, 0.07, 0.09); m.metallic = 0.6; m.roughness = 0.35; cuerpo.material_override = m
		n.add_child(cuerpo)
		var pant := MeshInstance3D.new(); var qm := QuadMesh.new(); qm.size = Vector2(0.22, 0.15); pant.mesh = qm
		pant.rotation_degrees = Vector3(-90, 0, 0); pant.position = Vector3(0, 0.0082, 0)
		var m2 := StandardMaterial3D.new(); m2.albedo_texture = load("res://assets/pantallas/chat_tablet.png"); m2.emission_enabled = true; m2.emission_texture = m2.albedo_texture; m2.emission_energy_multiplier = 1.2
		pant.material_override = m2
		n.add_child(pant)
	var p: Array = d["pos"]
	n.position = Vector3(p[0], p[1], p[2])
	n.rotation_degrees = Vector3(d.get("rot", [0, 0, 0])[0], d.get("rot", [0, 0, 0])[1], d.get("rot", [0, 0, 0])[2])
	n.set_meta("reposo", n.transform)
	return n

# ───────────────────────────────────────────────────────────── planificación de movimientos
# Segmento: {f0, nf, clip, repetir, modo: "quieto"|"clip"|"ruta", p0:Vector2, yaw0, yaw1, ruta:[Vector2], vel, dy0, dy1, fade}
func _planificar(id: String) -> Array:
	var ac = actores[id]
	var d: Dictionary = SB["actores"][id]
	var segs: Array = []
	var pos := Vector2(d["inicio"]["pos"][0], d["inicio"]["pos"][1])
	var yaw := deg_to_rad(float(d["inicio"]["yaw"]))
	var dy := float(d["inicio"].get("y", 0.0))
	var f := 0
	var clip_prev: String = d["inicio"].get("clip", "idle")
	var postura: String = d["inicio"].get("postura", "de_pie")
	var ev_list: Array = d["eventos"]
	for ev in ev_list:
		var f_ev := f
		# espera hasta el instante absoluto, repitiendo el clip anterior o el de reposo de la postura
		if ev.has("t"):
			var fe := int(round(float(ev["t"]) * FPS))
			if fe > f:
				var reposo: String = "sit_idle" if postura == "sentado" else "idle"
				var cl: String = ev.get("espera_clip", clip_prev if _es_estable(clip_prev) else reposo)
				segs.append(_seg(f, fe - f, cl, true, "quieto", pos, yaw, yaw, dy, dy))
				f = fe
				clip_prev = cl
		f_ev = f
		_registrar_manos(id, ev, f_ev)
		if ev.has("clip") and not ev.has("walk") and not ev.has("sentarse") and not ev.has("gira"):
			var cl2: String = ev["clip"]
			var rep: bool = not ev.get("una_vez", false)
			var nf: int = int(round(float(ev["dur"]) * FPS)) if ev.has("dur") else ac.duracion_cuadros(cl2) - 1
			var modo := "quieto" if rep else "clip"
			var s := _seg(f, nf, cl2, rep, modo, pos, yaw, yaw, dy, dy)
			if ev.has("yaw"):
				s["yaw1"] = deg_to_rad(float(ev["yaw"]))
			segs.append(s)
			if modo == "clip":
				var rc: Vector2 = ac.raiz_clip(cl2, nf)
				pos += _rotar(rc, yaw)
			yaw = s["yaw1"]
			f += nf
			clip_prev = cl2
			postura = ev.get("postura", postura)
		elif ev.has("gira"):
			var nf2 := int(round(float(ev.get("dur", 0.6)) * FPS))
			var y1 := deg_to_rad(float(ev["gira"]))
			var cl3: String = ev.get("clip", "sit_idle" if postura == "sentado" else "idle")
			segs.append(_seg(f, nf2, cl3, true, "quieto", pos, yaw, y1, dy, dy))
			yaw = y1
			f += nf2
			clip_prev = cl3
		elif ev.has("walk"):
			var ruta: Array = []
			for p in ev["walk"]:
				ruta.append(Vector2(p[0], p[1]))
			var cl4: String = ev.get("clip", "walk")
			var vel := _velocidad(ac, cl4) * float(ev.get("rapidez", 1.0))
			var largo := 0.0
			var prev := pos
			for q in ruta:
				largo += prev.distance_to(q)
				prev = q
			var nf3 := maxi(int(ceil(largo / vel * FPS)), 1)
			var s2 := _seg(f, nf3, cl4, true, "ruta", pos, yaw, yaw, dy, dy)
			s2["ruta"] = ruta
			s2["vel"] = largo / (float(nf3) / FPS)
			s2["yaw_final"] = deg_to_rad(float(ev["yaw_final"])) if ev.has("yaw_final") else NAN
			segs.append(s2)
			var ult: Vector2 = ruta[ruta.size() - 1]
			var pen: Vector2 = ruta[ruta.size() - 2] if ruta.size() > 1 else pos
			var dir := ult - pen
			yaw = atan2(dir.x, dir.y) if not is_nan(dir.x) and dir.length() > 0.001 else yaw
			if ev.has("yaw_final"):
				yaw = deg_to_rad(float(ev["yaw_final"]))
			pos = ult
			f += nf3
			clip_prev = cl4
			postura = "de_pie"
		elif ev.has("sentarse"):
			var sd: Dictionary = ev["sentarse"]
			var cl5: String = sd.get("clip", "stand_to_sit")
			var nf5: int = ac.duracion_cuadros(cl5) - 1
			var ysit := deg_to_rad(float(sd["yaw"]))
			var asiento := Vector2(sd["pos"][0], sd["pos"][1])
			var rc2: Vector2 = ac.raiz_clip(cl5, nf5)
			var ini := asiento - _rotar(rc2, ysit)
			# gira en el lugar hacia el asiento
			if pos.distance_to(ini) > 0.05:
				var sr := _seg(f, int(0.01 * FPS) + 1, "idle", true, "quieto", pos, yaw, yaw, dy, dy)
				segs.append(sr); f += int(0.01 * FPS) + 1
				segs[segs.size() - 1]["salta_a"] = ini
				pos = ini
			var s5 := _seg(f, nf5, cl5, false, "clip", pos, ysit, ysit, dy, dy + float(sd.get("dy", 0.0)))
			segs.append(s5)
			pos = asiento; yaw = ysit; dy = dy + float(sd.get("dy", 0.0))
			f += nf5
			clip_prev = "sit_idle"
			postura = "sentado"
		else:
			push_warning("evento no entendido en " + id + ": " + str(ev))
	var fin := total - 1
	if f < fin:
		var rep2: String = "sit_idle" if postura == "sentado" else "idle"
		segs.append(_seg(f, fin - f + 1, d.get("clip_final", clip_prev if _es_estable(clip_prev) else rep2), true, "quieto", pos, yaw, yaw, dy, dy))
	return segs

func _registrar_manos(id: String, ev: Dictionary, f_ev: int) -> void:
	## «agarra»: {prop, mano, en (s desde el inicio del evento), off:[x,y,z,rx,ry,rz], hasta (s absolutos) o suelta_en…}
	if ev.has("agarra"):
		var a: Dictionary = ev["agarra"]
		var p: Dictionary = SB["props"][a["prop"]]
		if not p.has("manos"):
			p["manos"] = []
		var tr := {"actor": id, "mano": a.get("mano", "R"), "t0": float(f_ev) / FPS + float(a.get("en", 0.0)), "t1": float(a.get("hasta", SB["dur"])), "off": a.get("off", [0, 0, 0, 0, 0, 0])}
		if a.has("suelta_en"):
			tr["suelta_en"] = a["suelta_en"]
		p["manos"].append(tr)
		if a.has("agarre"):      # cierre de los dedos: segundos antes/después
			tr["dedos"] = a["agarre"]

func _es_estable(c: String) -> bool:
	return c in ["idle", "sit_idle", "sit_idle2", "sit_talk", "talk1", "talk2", "talk3", "thinking", "type", "tablet", "working", "bashful", "walk"]

func _seg(f0: int, nf: int, clip: String, rep: bool, modo: String, p0: Vector2, y0: float, y1: float, dy0: float, dy1: float) -> Dictionary:
	return {"f0": f0, "nf": nf, "clip": clip, "repetir": rep, "modo": modo, "p0": p0, "yaw0": y0, "yaw1": y1, "dy0": dy0, "dy1": dy1, "ruta": [], "vel": 0.0, "yaw_final": NAN}

func _rotar(v: Vector2, yaw: float) -> Vector2:
	# v = (x local, z local) → mundo (x, z) con el frente +Z girado `yaw` (rotación Y de Godot)
	return Vector2(v.x * cos(yaw) + v.y * sin(yaw), -v.x * sin(yaw) + v.y * cos(yaw))

func _velocidad(ac, clip: String) -> float:
	var m: Dictionary = ac.meta[clip]
	var d: Array = m["desp"]
	var frames: Array = m["frames"]
	var dur := float(frames[1] - frames[0]) / FPS
	return Vector2(float(d[0]), float(d[1])).length() / dur

# ───────────────────────────────────────────────────────────── horneado cuadro a cuadro
func _hornear() -> void:
	var rutas := {}
	var cf := Cara.new()
	cf.preparar(SB, actores)
	# pistas
	var tr_raiz := {}
	var tr_hueso := {}
	for id in actores:
		var ac = actores[id]
		var pr := _ruta(ac.raiz)
		var tp := anim.add_track(Animation.TYPE_POSITION_3D); anim.track_set_path(tp, pr)
		var tq := anim.add_track(Animation.TYPE_ROTATION_3D); anim.track_set_path(tq, pr)
		var tsc := anim.add_track(Animation.TYPE_SCALE_3D); anim.track_set_path(tsc, pr)
		tr_raiz[id] = [tp, tq, tsc]
		var hs := {}
		for h in ac.clips["idle"]["rot"]:
			var tt := anim.add_track(Animation.TYPE_ROTATION_3D)
			anim.track_set_path(tt, NodePath("%s:%s" % [_ruta(ac.sk), ac.sk.get_bone_name(h)]))
			hs[h] = tt
		var th := anim.add_track(Animation.TYPE_POSITION_3D)
		anim.track_set_path(th, NodePath("%s:%s" % [_ruta(ac.sk), ac.sk.get_bone_name(ac.hueso_cadera)]))
		hs["pos"] = th
		tr_hueso[id] = hs
	# pistas de objetos
	var tr_prop := {}
	for pid in props:
		var pn: Node3D = props[pid]
		var tp2 := anim.add_track(Animation.TYPE_POSITION_3D); anim.track_set_path(tp2, _ruta(pn))
		var tq2 := anim.add_track(Animation.TYPE_ROTATION_3D); anim.track_set_path(tq2, _ruta(pn))
		var ts2 := anim.add_track(Animation.TYPE_SCALE_3D); anim.track_set_path(ts2, _ruta(pn))
		tr_prop[pid] = [tp2, tq2, ts2]
	cf.crear_pistas(anim, esc)
	var hist := {}
	for id in actores:
		hist[id] = []
	SB["_hist"] = hist
	var pos_ant := {}
	for g in total:
		var t := float(g) / FPS
		for id in actores:
			var ac = actores[id]
			var sg := _segmento(id, g)
			var seg: Dictionary = planes[id][sg]
			var k := g - int(seg["f0"])
			var pose := _pose_seg(ac, seg, k)
			if k < int(SB["_global"].get("fundido_cuadros", 8)) and sg > 0:
				var pv: Dictionary = planes[id][sg - 1]
				var kp := g - int(pv["f0"])
				var pose_p := _pose_seg(ac, pv, kp)
				var w := float(k + 1) / float(SB["_global"].get("fundido_cuadros", 8) + 1)
				w = w * w * (3.0 - 2.0 * w)
				pose = Actor.mezcla(pose_p, pose, w)
			ac.poner_pose(pose)
			_agarres(id, ac, t)
			# cara y mirada (encima de la pose)
			cf.aplicar(id, ac, t, g)
			# raíz
			var rr := _raiz(ac, seg, k)
			ac.raiz.position = Vector3(rr[0].x, rr[1], rr[0].y)
			ac.raiz.rotation.y = rr[2]
		for id in actores:
			SB["_hist"][id].append(actores[id].raiz.global_position)
		# objetos en manos (después de poner todas las poses)
		for pid in props:
			_prop_cuadro(pid, t)
		# claves
		for id in actores:
			var ac2 = actores[id]
			var tr: Array = tr_raiz[id]
			anim.position_track_insert_key(tr[0], t, ac2.raiz.position)
			anim.rotation_track_insert_key(tr[1], t, Quaternion(Vector3.UP, ac2.raiz.rotation.y))
			var vis := _visible(id, t)
			ac2.raiz.scale = Vector3.ONE * ac2.escala * maxf(vis, 0.0001)
			anim.scale_track_insert_key(tr[2], t, ac2.raiz.scale)
			var hs2: Dictionary = tr_hueso[id]
			for h in hs2:
				if h is String:
					continue
				anim.rotation_track_insert_key(hs2[h], t, ac2.sk.get_bone_pose_rotation(h))
			anim.position_track_insert_key(hs2["pos"], t, ac2.sk.get_bone_pose_position(ac2.hueso_cadera))
			cf.claves(id, anim, t)
			_medir_pies(id, ac2, g)
		for pid in props:
			var pn2: Node3D = props[pid]
			var tr3: Array = tr_prop[pid]
			anim.position_track_insert_key(tr3[0], t, pn2.position)
			anim.rotation_track_insert_key(tr3[1], t, pn2.transform.basis.get_rotation_quaternion())
			anim.scale_track_insert_key(tr3[2], t, pn2.scale)
	# dejar a cada nodo en su pose del cuadro 0 (para el GLB: la animación manda)
	return

func _visible(id: String, t: float) -> float:
	## 0..1: aparece/desaparece creciendo desde los pies (EVA holograma). Sin lista = siempre visible.
	var d: Dictionary = SB["actores"][id]
	if not d.has("visible"):
		return 1.0
	var v := 0.0
	for tr in d["visible"]:
		var a := clampf((t - float(tr[0])) / 0.9, 0.0, 1.0)
		var b := clampf((float(tr[1]) - t) / 0.9, 0.0, 1.0)
		v = maxf(v, minf(a, b))
	return smoothstep(0.0, 1.0, v)

func _ruta(n: Node) -> NodePath:
	return esc.get_path_to(n)

func _segmento(id: String, g: int) -> int:
	var arr: Array = planes[id]
	var r := arr.size() - 1
	for i in arr.size():
		if g < int(arr[i]["f0"]) + int(arr[i]["nf"]):
			r = i
			break
	return r

func _pose_seg(ac, seg: Dictionary, k: int) -> Dictionary:
	return ac.pose_clip(seg["clip"], k, seg["repetir"])

func _raiz(ac, seg: Dictionary, k: int) -> Array:
	var kk := clampi(k, 0, int(seg["nf"]))
	var u := float(kk) / maxf(float(seg["nf"]), 1.0)
	var y := lerpf(seg["yaw0"], seg["yaw1"], smoothstep(0.0, 1.0, u)) if not is_equal_approx(seg["yaw0"], seg["yaw1"]) else float(seg["yaw0"])
	var dy := lerpf(seg["dy0"], seg["dy1"], smoothstep(0.0, 1.0, u))
	var p: Vector2 = seg["p0"]
	if seg.has("salta_a"):
		p = seg["salta_a"]
	match seg["modo"]:
		"clip":
			p = p + _rotar(ac.raiz_clip(seg["clip"], kk), float(seg["yaw0"]))
		"ruta":
			var ruta: Array = seg["ruta"]
			var dist: float = float(kk) / FPS * float(seg["vel"])
			var pts: Array = [seg["p0"]]
			pts.append_array(ruta)
			var acum := 0.0
			var pos2: Vector2 = pts[pts.size() - 1]
			var dir2 := Vector2.ZERO
			for i in range(pts.size() - 1):
				var l: float = (pts[i] as Vector2).distance_to(pts[i + 1])
				if dist <= acum + l or i == pts.size() - 2:
					var f := clampf((dist - acum) / maxf(l, 0.0001), 0.0, 1.0)
					pos2 = (pts[i] as Vector2).lerp(pts[i + 1], f)
					break
				acum += l
			p = pos2
			# rumbo: promedio suave del rumbo de los tramos cercanos (giro continuo, sin saltos)
			y = _rumbo(pts, dist, float(seg["yaw0"]), seg["yaw_final"], float(seg["nf"]) / FPS * float(seg["vel"]))
	return [p, dy, y]

func _rumbo(pts: Array, dist: float, yaw_ini: float, yaw_fin: float, largo: float) -> float:
	# rumbo = dirección del camino a `dist + 0.5 m`; al principio parte del rumbo inicial y al final se alinea a yaw_final
	var obj := dist + 0.45
	var acum := 0.0
	var dir2 := Vector2.ZERO
	for i in range(pts.size() - 1):
		var l: float = (pts[i] as Vector2).distance_to(pts[i + 1])
		dir2 = ((pts[i + 1] as Vector2) - (pts[i] as Vector2)).normalized()
		if obj <= acum + l:
			break
		acum += l
	var yaw_c := atan2(dir2.x, dir2.y)
	# giro suave entre tramos: mezcla con el rumbo del tramo siguiente en los últimos 0,5 m de cada tramo
	var u_ini := clampf(dist / 0.7, 0.0, 1.0)
	var y := lerp_angle(yaw_ini, yaw_c, smoothstep(0.0, 1.0, u_ini))
	if not is_nan(yaw_fin):
		var u_fin := clampf((dist - (largo - 0.8)) / 0.8, 0.0, 1.0)
		y = lerp_angle(y, yaw_fin, smoothstep(0.0, 1.0, u_fin))
	return y

func _agarres(id: String, ac, t: float) -> void:
	## cierre de los dedos de la mano que sostiene un objeto: sube 0,35 s antes del agarre y se abre 0,35 s después de soltarlo
	for pid in props:
		for tr in SB["props"][pid].get("manos", []):
			if tr["actor"] != id:
				continue
			var a := clampf((t - (float(tr["t0"]) - 0.35)) / 0.35, 0.0, 1.0)
			var b := clampf(((float(tr["t1"]) + 0.35) - t) / 0.35, 0.0, 1.0)
			var w := smoothstep(0.0, 1.0, minf(a, b))
			if w > 0.001:
				ac.aplicar_agarre(tr["mano"], w)

# ───────────────────────────────────────────────────────────── objetos agarrados con la mano
func _prop_cuadro(pid: String, t: float) -> void:
	var pn: Node3D = props[pid]
	var reposo: Transform3D = pn.get_meta("reposo")
	var d: Dictionary = SB["props"][pid]
	var activo = null
	for tr in d.get("manos", []):
		if t >= float(tr["t0"]) and t <= float(tr["t1"]):
			activo = tr
	if activo == null:
		# después del último agarre queda donde se soltó
		var ult = null
		for tr in d.get("manos", []):
			if t > float(tr["t1"]):
				ult = tr
		if ult != null and ult.has("suelta_en"):
			var se: Array = ult["suelta_en"]
			pn.transform = Transform3D(Basis.from_euler(Vector3(deg_to_rad(se[3]), deg_to_rad(se[4]), deg_to_rad(se[5]))), Vector3(se[0], se[1], se[2]))
		else:
			pn.transform = reposo
		pn.scale = Vector3.ONE
		return
	var ac = actores[activo["actor"]]
	var h: int = ac.mano[activo["mano"]]
	var gp: Transform3D = ac.sk.global_transform * ac.sk.get_bone_global_pose(h)
	var o: Array = activo.get("off", [0, 0, 0, 0, 0, 0])
	# escala del esqueleto (×0,01) fuera: se queda sólo con posición y orientación
	var b := gp.basis.orthonormalized()
	var off := Transform3D(Basis.from_euler(Vector3(deg_to_rad(o[3]), deg_to_rad(o[4]), deg_to_rad(o[5]))), Vector3(o[0], o[1], o[2]))
	var tf := Transform3D(b, gp.origin) * off
	pn.global_transform = tf
	pn.scale = Vector3.ONE * float(d.get("esc", 1.0))

# ───────────────────────────────────────────────────────────── verificación de apoyo de los pies
func _medir_pies(id: String, ac, g: int) -> void:
	var minimo := 1e9
	for nm in ["EM3D_Base_L_Foot", "EM3D_Base_R_Foot", "EM3D_Base_L_ToeBase", "EM3D_Base_R_ToeBase"]:
		var h: int = ac.sk.find_bone(nm)
		var y: float = (ac.sk.global_transform * ac.sk.get_bone_global_pose(h)).origin.y
		minimo = minf(minimo, y)
	var d: Dictionary = verif["pies"].get(id, {"min": 1e9, "max": -1e9})
	d["min"] = minf(d["min"], minimo)
	d["max"] = maxf(d["max"], minimo)
	verif["pies"][id] = d

# ───────────────────────────────────────────────────────────── cámaras, exportación y capturas
func _camaras_y_salida(clave: String, salida: String, caps: Array) -> void:
	var cams_json := []
	var camn := {}
	for tm in SB["tomas"]:
		var c := Camera3D.new()
		c.name = tm["camara"]
		c.fov = float(tm.get("fov", 50))
		c.near = 0.1
		c.far = 200.0
		esc.add_child(c)
		camn[tm["id"]] = c
		var tp := anim.add_track(Animation.TYPE_POSITION_3D); anim.track_set_path(tp, _ruta(c))
		var tq := anim.add_track(Animation.TYPE_ROTATION_3D); anim.track_set_path(tq, _ruta(c))
		var f0 := int(round(float(tm["t0"]) * FPS))
		var f1 := mini(int(round(float(tm["t1"]) * FPS)), total - 1)
		var suave_pos := Vector3.ZERO
		var suave_mira := Vector3.ZERO
		var rot_ant := Quaternion.IDENTITY
		for g in range(0, total):
			var u := clampf(float(g - f0) / maxf(float(f1 - f0), 1.0), 0.0, 1.0)
			var e := smoothstep(0.0, 1.0, u) if tm.get("suave", true) else u
			var pa: Array = tm["pos"]; var pb: Array = tm.get("pos_fin", pa)
			var p := Vector3(pa[0], pa[1], pa[2]).lerp(Vector3(pb[0], pb[1], pb[2]), e)
			var mira := _mira(tm, g, e)
			if g == 0 or g == f0:
				suave_mira = mira
			suave_mira = suave_mira.lerp(mira, 0.12 if tm.has("sigue") else 1.0)
			c.global_position = p
			c.look_at(suave_mira, Vector3.UP)
			# balanceo lento de mano (seno de baja frecuencia, nunca ruido por cuadro)
			var amp := float(tm.get("mano", 0.0))
			if amp > 0.0:
				c.position += Vector3(sin(g / FPS * 0.7), sin(g / FPS * 0.9 + 1.0), 0.0) * amp
			var q := c.global_transform.basis.get_rotation_quaternion()
			anim.position_track_insert_key(tp, float(g) / FPS, c.global_position)
			anim.rotation_track_insert_key(tq, float(g) / FPS, q)
		cams_json.append({"id": tm["id"], "camara": tm["camara"], "plano": tm.get("plano", ""), "tipo": "godot", "inicio_s": float(tm["t0"]), "fin_s": float(tm["t1"]),
			"frame_inicio": f0 + 1, "frame_fin": f1 + 1, "lente_mm": _fov_a_mm(float(tm.get("fov", 50)), 720.0 / 1280.0)})
	anim.length = float(total - 1) / FPS
	# capturas de revisión (no son render)
	for ts in caps:
		var g2 := clampi(int(round(ts * FPS)), 0, total - 1)
		ap.seek(float(g2) / FPS, true)
		var vis_cam: Camera3D = null
		for tm2 in SB["tomas"]:
			if ts >= float(tm2["t0"]) and ts <= float(tm2["t1"]):
				vis_cam = camn[tm2["id"]]
				break
		if vis_cam == null:
			vis_cam = camn[SB["tomas"][0]["id"]]
		vis_cam.current = true
		for i in 4:
			await process_frame
		root.get_texture().get_image().save_png("%s_t%s.png" % [salida, str(ts)])
		print("CAP ", ts)
	# fotos de diagnóstico de cerca (cara, manos, pies): no entran en el GLB
	for dg in SB.get("diag", []):
		var dc := Camera3D.new()
		dc.fov = float(dg.get("fov", 30)); dc.near = 0.02
		esc.add_child(dc)
		var gd := clampi(int(round(float(dg["t"]) * FPS)), 0, total - 1)
		ap.seek(float(gd) / FPS, true)
		var objetivo: Vector3
		var off: Array = dg["off"]
		var delta := Vector3(off[0], off[1], off[2])
		if dg.has("hueso"):
			# apunta a un hueso (cabeza, manos…); el desplazamiento va en el marco del personaje (derecha, arriba, adelante)
			var acd = actores[dg["sigue"]]
			var hb: int = acd.sk.find_bone("EM3D_Base_" + String(dg["hueso"]))
			objetivo = (acd.sk.global_transform * acd.sk.get_bone_global_pose(hb)).origin
			var bs: Basis = acd.raiz.global_transform.basis.orthonormalized()
			delta = bs.x * off[0] + bs.y * off[1] + bs.z * off[2]
		elif dg.has("sigue"):
			objetivo = (SB["_hist"][dg["sigue"]][gd] as Vector3) + Vector3(0, float(dg.get("alto", 1.5)), 0)
		else:
			objetivo = Vector3(dg["mira"][0], dg["mira"][1], dg["mira"][2])
		for nm in dg.get("ocultar", []):
			var mm = actores[dg["sigue"]].modelo.find_child(nm, true, false)
			if mm:
				mm.visible = false
		dc.global_position = objetivo + delta
		dc.look_at(objetivo, Vector3.UP)
		dc.current = true
		for i in 4:
			await process_frame
		root.get_texture().get_image().save_png("%s_diag_%s.png" % [salida, dg["n"]])
		dc.queue_free()
		for nm in dg.get("ocultar", []):
			var mm2 = actores[dg["sigue"]].modelo.find_child(nm, true, false)
			if mm2:
				mm2.visible = true
	# exportar GLB
	ap.seek(0.0, true)
	var doc := GLTFDocument.new()
	var st := GLTFState.new()
	doc.append_from_scene(esc, st)
	var err := doc.write_to_filesystem(st, salida + ".glb")
	print("GLB ", salida, ".glb err=", err)
	# JSON para el visor
	var nodos_actor := []
	for id in actores:
		nodos_actor.append({"id": id, "nodo": id, "modelo": SB["actores"][id]["modelo"]})
	var js := {"formato": "estudio.previa_godot/1", "produccion": "p011_a_la_deriva", "escena_id": "e03_" + clave, "version": 1, "titulo": SB.get("titulo", clave),
		"fps": int(FPS), "frames": total, "duracion_s": float(total - 1) / FPS, "resolucion": [1280, 720], "animacion": "escena",
		"actores": nodos_actor, "tomas": cams_json, "voces": SB.get("voces", []), "tiempo": {"pelicula": "t = (cuadro − 1) / fps"}}
	var fa := FileAccess.open(salida + ".json", FileAccess.WRITE)
	fa.store_string(JSON.stringify(js, "  "))
	fa.close()
	var fv := FileAccess.open(salida + "_verif.json", FileAccess.WRITE)
	fv.store_string(JSON.stringify(verif, "  "))
	fv.close()
	print("VERIF ", JSON.stringify(verif))

func _fov_a_mm(fov_v: float, aspecto_inv: float) -> float:
	return 36.0 / 2.0 / tan(deg_to_rad(fov_v) / 2.0) * 0.0 + (24.0 / 2.0) / tan(deg_to_rad(fov_v) / 2.0)

func _mira(tm: Dictionary, g: int, e: float) -> Vector3:
	if tm.has("sigue"):
		var alto := float(tm.get("sigue_alto", 1.3))
		var h: Array = SB["_hist"][tm["sigue"]]
		return (h[clampi(g, 0, h.size() - 1)] as Vector3) + Vector3(0, alto, 0)
	var ma: Array = tm["mira"]
	var mb: Array = tm.get("mira_fin", ma)
	return Vector3(ma[0], ma[1], ma[2]).lerp(Vector3(mb[0], mb[1], mb[2]), e)
