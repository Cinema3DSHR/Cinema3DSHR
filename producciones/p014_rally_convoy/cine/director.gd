extends RefCounted
## Dirección de cámaras de «Rally Convoy». Cada plano es una función del estado REAL de la simulación (posición de los autos, ruta,
## terreno), así que nunca atraviesa el camino ni los autos. Hay cortes secos entre planos (como un montaje de carreras); dentro de
## cada plano la cámara se mueve suave. Planos: seguimiento trasero, frontal desde el auto fantasma, giratoria 360° con brazo virtual,
## interior (cabina 3D), lateral paralela, dron (no muy alto), a ras del suelo, panorámica del pelotón, zoom de lente que sigue y se aleja
## (dolly zoom), capó y paragolpes, y el auto fantasma invisible con cámara (adelante mirando hacia atrás, parado mientras lo pasan, o
## avanzando y siendo pasado).

var sc # CineScene
var core
var cam: Camera3D
var fov := 70.0
var inside_car := -1 # auto cuya cabina 3D se dibuja (cámara interior); −1 = ninguno
var focus_car := 0 # auto que se escucha
var plan: Array = [] # [{t0, t1, type, car, ...}]
var cur := -1
var _shot_t := 0.0
var _ghost_s := 0.0
var _ghost_v := 0.0
var _cam_pos := Vector3.ZERO
var _cam_look := Vector3.ZERO
var _have_prev := false
var _raise := 0.0
var _rng := RandomNumberGenerator.new()
var telemetry: Dictionary = {}
var shot_log: Array = []

func setup(p_sc) -> void:
	sc = p_sc
	core = sc.core
	cam = sc.cam
	_rng.seed = 2026
	var tf := "res://cine/telemetria.json"
	if FileAccess.file_exists(tf):
		telemetry = JSON.parse_string(FileAccess.get_file_as_string(tf))
	plan = _make_plan()
	for pl in plan:
		print("[plan] %6.1f–%6.1f  %-12s auto %d" % [float(pl["t0"]), float(pl["t1"]), str(pl["type"]), int(pl.get("car", 0))])
	if sc.args.has("cam"): # prueba: un solo plano permanente
		plan = [{"t0": 0.0, "t1": 1e9, "type": sc._arg("cam"), "car": int(sc._arg("car", "0"))}]

# ───────────────────────────── geometría de la ruta
func route_pt(s: float, lat: float, h := 0.0) -> Vector3:
	var tr = core.track
	var sc_s := clampf(s, 0.0, float(tr.length) - 3.0)
	var i: int = tr.idx_at(sc_s)
	i = clampi(i, 1, tr.n - 2)
	var u := clampf((sc_s - float(tr.cum[i - 1])) / maxf(0.01, float(tr.cum[i]) - float(tr.cum[i - 1])), 0.0, 1.0)
	var p: Vector3 = (tr.samples[i - 1] as Vector3).lerp(tr.samples[i], u)
	var l: Vector3 = (tr.laterals[i - 1] as Vector3).lerp(tr.laterals[i], u)
	return Vector3(p.x + l.x * lat, p.y + h, p.z + l.z * lat)

func route_tan(s: float) -> Vector3:
	var tr = core.track
	var i: int = clampi(tr.idx_at(clampf(s, 0.0, float(tr.length) - 3.0)), 1, tr.n - 2)
	return (tr.tangents[i] as Vector3)

func hw_at(s: float) -> float:
	var tr = core.track
	return float(tr.hwa[clampi(tr.idx_at(clampf(s, 0.0, float(tr.length) - 3.0)), 0, tr.n - 1)])

func ground_y(x: float, z: float) -> float:
	return float(core.track.ground_smooth(x, z))

func car_pos(k: int) -> Vector3:
	var p = core.cars[k].snap
	return Vector3(p.px, p.py, p.pz)

func car_basis(k: int) -> Basis:
	var p = core.cars[k].snap
	return Basis.from_euler(Vector3(p.pitch, p.yaw, p.roll), EULER_ORDER_YXZ)

func car_fwd(k: int) -> Vector3:
	var p = core.cars[k].snap
	return Vector3(sin(p.yaw), 0, cos(p.yaw))

func car_speed(k: int) -> float:
	var p = core.cars[k].snap
	return sqrt(p.vx * p.vx + p.vz * p.vz)

func pack_center() -> Vector3:
	var a := Vector3.ZERO
	for k in core.cars.size():
		a += car_pos(k)
	return a / float(core.cars.size())

func leader() -> int:
	var b := 0
	for k in core.cars.size():
		if core.pel.s[k] > core.pel.s[b]:
			b = k
	return b

func rearmost() -> int:
	var b := 0
	for k in core.cars.size():
		if core.pel.s[k] < core.pel.s[b]:
			b = k
	return b

# ───────────────────────────── el plan (qué plano va en cada momento)
## Reparto de planos por tramo de la ruta. La duración sale de la telemetría (hora en que el punto guía pasa por cada lugar).
func _t_at_s(sm: float) -> float:
	if telemetry.is_empty():
		return sm / 28.0
	var arr: Array = telemetry["sp"] # s del punto guía cada 0,5 s
	var step := float(telemetry.get("step", 0.5))
	for i in arr.size():
		if float(arr[i]) >= sm:
			return float(i) * step
	return float(arr.size()) * step

func _make_plan() -> Array:
	var p: Array = []
	var tr = core.track
	var s_toll: float = core.toll_s
	var bridge_s0 := 0.0
	var bridge_s1 := 0.0
	var mount_s0 := 0.0
	for e in tr.events:
		if str(e["t"]) == "bridge":
			bridge_s0 = float(tr.cum[int(e["i"])])
			bridge_s1 = float(tr.cum[int(e["i1"])])
	for i in tr.n:
		if int(tr.biomea[i]) == 3:
			mount_s0 = float(tr.cum[i])
			break
	var T_go := 4.0
	var T_toll := _t_at_s(s_toll)
	var T_toll_out := _t_at_s(s_toll + 60.0)
	var T_end := minf(float(telemetry.get("t_end", 320.0)), 296.0)
	var cut_prev := func(tc: float) -> void:
		while not p.is_empty() and float(p.back()["t0"]) >= tc:
			p.pop_back()
		if not p.is_empty() and float(p.back()["t1"]) > tc:
			p.back()["t1"] = tc
	# 1) salida: la estación con los siete reunidos, los pilotos, el arranque y el peaje
	p.append({"t0": 0.0, "t1": 3.2, "type": "grid_orbit", "car": 3})
	p.append({"t0": 3.2, "t1": 4.8, "type": "interior", "car": 4})
	p.append({"t0": 4.8, "t1": 6.4, "type": "interior", "car": 0})
	p.append({"t0": 6.4, "t1": 8.6, "type": "side", "car": 1})
	p.append({"t0": 8.6, "t1": T_toll_out - 1.5, "type": "ghost_hold", "car": 0, "s_off": 70.0})
	p.append({"t0": T_toll_out - 1.5, "t1": T_toll_out + 3.5, "type": "chase", "car": 2})
	# 2) resto del recorrido: se alternan los planos y los autos; hay planos especiales en el puente y en las curvas cerradas
	# (sin planos aéreos salvo el del puente: no gustaron) — se alternan seguimiento, fantasma, interior, lateral, a ras del suelo y zoom
	var rot := ["ghost_close", "chase", "orbit", "ghost_back", "side", "ghost_close", "ground", "interior", "zoom", "ghost_hold", "front_pack", "hood", "ghost_close", "ghost_run", "dolly", "ghost_close", "bumper"]
	var t := T_toll_out + 3.5
	var idx := 0
	var last_car := -1
	var bridge_done := false
	while t < T_end - 3.0:
		var type: String = rot[idx % rot.size()]
		idx += 1
		var dur := _rng.randf_range(4.2, 8.0)
		var car := _rng.randi_range(0, core.cars.size() - 1)
		if car == last_car:
			car = (car + 3) % core.cars.size()
		last_car = car
		# puente: plano aéreo orbitando el puente y plano lateral rasante
		if not bridge_done and t >= _t_at_s(bridge_s0 - 120.0):
			bridge_done = true
			var tb0 := _t_at_s(bridge_s0 - 120.0)
			var tb1 := _t_at_s(bridge_s1 + 80.0)
			cut_prev.call(tb0)
			var seg := (tb1 - tb0) / 4.0
			p.append({"t0": tb0, "t1": tb0 + seg, "type": "drone", "car": 5})
			p.append({"t0": tb0 + seg, "t1": tb0 + 2.0 * seg, "type": "bridge_side", "car": 0, "s_ref": (bridge_s0 + bridge_s1) * 0.5})
			p.append({"t0": tb0 + 2.0 * seg, "t1": tb0 + 3.0 * seg, "type": "ghost_back", "car": 1})
			p.append({"t0": tb0 + 3.0 * seg, "t1": tb1, "type": "orbit", "car": 4})
			t = tb1
			continue
		# montaña: más cámara baja y interior para ver el trabajo de la dirección y de la suspensión
		if t > _t_at_s(mount_s0):
			# montaña: más planos con el auto fantasma por delante de los autos que suben (pedido del dueño), el resto cerca y bajo
			var mrot := ["ghost_close", "interior", "ghost_close", "chase", "ghost_close", "side", "zoom", "ghost_close", "ground"]
			type = mrot[idx % mrot.size()]
			dur = _rng.randf_range(3.8, 6.2)
		p.append({"t0": t, "t1": minf(t + dur, T_end), "type": type, "car": car})
		t += dur
	# 3) final: plano general y cierre
	p.append({"t0": T_end - 3.0, "t1": T_end + 8.0, "type": "ghost_back", "car": 0})
	return p

# ───────────────────────────── ejecución
func update(dt: float) -> void:
	var t: float = sc.t_now
	if cur < 0 or t >= float(plan[cur]["t1"]) or t < float(plan[cur]["t0"]):
		cur = _find(t)
		_shot_t = 0.0
		_have_prev = false
		_raise = 0.0
		_ghost_init()
		shot_log.append([snappedf(t, 0.1), plan[cur]["type"], plan[cur]["car"]])
	_shot_t += dt
	var sh: Dictionary = plan[cur]
	inside_car = -1
	focus_car = int(sh.get("car", 0))
	var r := _eval(sh, dt)
	_apply(r, dt)

func _find(t: float) -> int:
	for i in plan.size():
		if t >= float(plan[i]["t0"]) and t < float(plan[i]["t1"]):
			return i
	return plan.size() - 1

func _apply(r: Dictionary, dt: float) -> void:
	var pos: Vector3 = r["pos"]
	var look: Vector3 = r["look"]
	# nunca bajo el suelo
	var gy := ground_y(pos.x, pos.z)
	pos.y = maxf(pos.y, gy + float(r.get("min_h", 0.35)))
	# línea de vista: si el terreno (un cerro, un talud) se interpone entre la cámara y lo que mira, la cámara sube lo necesario (nunca queda adentro de la montaña)
	var raise_need := 0.0
	for q in range(1, 11):
		var uq := float(q) / 11.0
		var pq := pos.lerp(look, uq)
		var need := (ground_y(pq.x, pq.z) + 0.7 - pq.y) / maxf(0.05, 1.0 - uq)
		raise_need = maxf(raise_need, need)
	if r.get("min_h", 0.35) != 0.0 or true:
		_raise = lerpf(_raise, clampf(raise_need, 0.0, 22.0), 1.0 - exp(-dt * (6.0 if raise_need > _raise else 1.5)))
		pos.y += _raise
	var sm: float = float(r.get("smooth", 0.0))
	if sm > 0.0 and _have_prev:
		var k := 1.0 - exp(-dt * sm)
		pos = _cam_pos.lerp(pos, k)
		look = _cam_look.lerp(look, 1.0 - exp(-dt * sm * 1.6))
	_cam_pos = pos
	_cam_look = look
	_have_prev = true
	cam.position = pos
	var up := Vector3.UP
	if r.has("up"):
		up = r["up"]
	if (look - pos).length() > 0.01:
		cam.look_at(look, up)
	fov = float(r.get("fov", 70.0))

func _ghost_init() -> void:
	var sh: Dictionary = plan[cur]
	var lead_s: float = core.pel.s[leader()]
	match str(sh["type"]):
		"ghost_back":
			_ghost_s = lead_s + 55.0
		"ghost_hold":
			_ghost_s = float(core.toll_s) + 55.0 if sh.has("s_off") else lead_s + 90.0
		"ghost_close":
			_ghost_s = core.pel.s[int(sh.get("car", 0))] + 44.0
		"ghost_run":
			_ghost_s = lead_s + 45.0

func _eval(sh: Dictionary, dt: float) -> Dictionary:
	var k: int = int(sh.get("car", 0))
	var ty: String = sh["type"]
	var u := _shot_t
	var cp := car_pos(k)
	var fw := car_fwd(k)
	var rt := Vector3(fw.z, 0, -fw.x) # derecha del auto
	var d_s: float = float(sh["t1"]) - float(sh["t0"])
	match ty:
		"chase": # seguimiento trasero bajo, un poco hacia un costado
			var side := 1.0 if (k % 2 == 0) else -1.0
			var tgt := cp - fw * (6.5 + 1.2 * sin(u * 0.4)) + rt * (1.2 * side) + Vector3(0, 1.5 + 0.2 * sin(u * 0.6), 0)
			return {"pos": tgt, "look": cp + fw * 4.0 + Vector3(0, 0.6, 0), "fov": 68.0 + minf(car_speed(k) * 0.12, 6.0), "smooth": 4.0}
		"hood":
			var b := car_basis(k)
			var pv := cp + b * Vector3(0, 1.12, 0.95)
			return {"pos": pv, "look": pv + b * Vector3(0, -0.05, 8.0), "fov": 78.0, "smooth": 0.0, "up": b.y, "min_h": 0.0}
		"bumper":
			var b := car_basis(k)
			var pv := cp + b * Vector3(0.0, 0.38, 2.25)
			return {"pos": pv, "look": pv + b * Vector3(0, 0.02, 10.0), "fov": 84.0, "smooth": 0.0, "up": b.y, "min_h": 0.0}
		"interior":
			inside_car = k
			var d: Dictionary = sc.cockpits[k].camera_local("onboard", core.cars[k].snap, sc.t_now, 0.1)
			var vis: Node3D = core.cars[k].visual
			var tf := vis.global_transform
			var base := Vector3(0, -core.cars[k].phys.V.comHeight + core.cars[k].phys.V.rideOffset, 0)
			var wp: Vector3 = tf * (base + (d["pos"] as Vector3))
			var wl: Vector3 = tf * (base + (d["look"] as Vector3))
			return {"pos": wp, "look": wl, "fov": 72.0, "up": tf.basis.y, "min_h": 0.0}
		"orbit": # brazo virtual anclado al auto: gira 360° alrededor mientras lo sigue
			var ang := u * 0.62 + float(k) * 1.3
			var r := 5.2 + 1.2 * sin(u * 0.5)
			var h := 0.8 + 1.0 * (0.5 + 0.5 * sin(u * 0.7 + 1.0))
			var off := Basis(Vector3.UP, atan2(fw.x, fw.z) + ang) * Vector3(0, 0, -r)
			return {"pos": cp + off + Vector3(0, h, 0), "look": cp + Vector3(0, 0.5, 0), "fov": 66.0, "smooth": 7.0}
		"grid_orbit": # los siete reunidos en la estación, la cámara gira alrededor
			var c := pack_center()
			var ang := -0.9 + u * 0.55
			return {"pos": c + Vector3(sin(ang) * 17.0, 3.6 - u * 0.3, cos(ang) * 17.0), "look": c + Vector3(0, 0.6, 0), "fov": 62.0}
		"side": # paralela a un costado
			var off := rt * (6.0 + 0.8 * sin(u * 0.5)) * (1.0 if (k % 2 == 0) else -1.0)
			return {"pos": cp + off + Vector3(0, 1.1, 0) - fw * 1.0, "look": cp + fw * 0.5 + Vector3(0, 0.5, 0), "fov": 62.0, "smooth": 6.0}
		"drone": # dron: sigue al pelotón desde arriba y atrás, no muy alto
			var c := pack_center()
			var l: int = leader()
			var fwd := car_fwd(l)
			var hgt := 11.0 + 3.0 * sin(u * 0.4)
			var pos := c - fwd * (14.0 - 4.0 * sin(u * 0.3)) + Vector3(0, hgt, 0) + Vector3(fwd.z, 0, -fwd.x) * (5.0 * sin(u * 0.35))
			return {"pos": pos, "look": c + fwd * 9.0, "fov": 62.0, "smooth": 3.0, "min_h": 3.0}
		"pack_wide": # panorámica del grupo, más alto
			var c := pack_center()
			var fwd := car_fwd(leader())
			var pos := c - fwd * 26.0 + Vector3(0, 17.0, 0) + Vector3(fwd.z, 0, -fwd.x) * (10.0 * sin(u * 0.3))
			return {"pos": pos, "look": c + fwd * 12.0, "fov": 66.0, "smooth": 2.5, "min_h": 4.0}
		"ground": # fija a ras del asfalto en la banquina, adelante del pelotón: los autos pasan frente a la cámara
			var tgt_s: float = core.pel.s[leader()]
			var mtn := int(core.track.biomea[clampi(core.track.idx_at(tgt_s), 0, core.track.n - 1)]) == 3
			if not sh.has("s_fix"):
				sh["s_fix"] = tgt_s + (34.0 if mtn else 62.0)
			var sf: float = float(sh["s_fix"])
			var side := 1.0 if (k % 2 == 0) else -1.0
			var shl_g := float(core.track.shl[clampi(core.track.idx_at(sf), 0, core.track.n - 1)])
			var base := route_pt(sf, (hw_at(sf) + shl_g + 1.1) * side, 0.95) # detrás del guardarraíl y por encima de él: los rieles no tapan la imagen
			var nearest_q := 0
			var ndist := 1e9
			for q in core.cars.size():
				var dq := car_pos(q).distance_to(base)
				if dq < ndist:
					ndist = dq
					nearest_q = q
			var road_pt := route_pt(sf - 34.0, 0.0, 0.8) # mientras el pelotón se acerca mira el camino por donde viene
			var lk := car_pos(nearest_q) + Vector3(0, 0.6, 0) if (ndist < 55.0 and core.pel.s[nearest_q] < sf + 25.0) else road_pt
			if core.pel.s[leader()] > sf + 12.0: # ya pasaron: los sigue de espaldas
				lk = pack_center() + Vector3(0, 0.6, 0)
			return {"pos": base, "look": lk, "fov": 70.0, "min_h": 0.8, "smooth": 4.0}
		"front_pack": # delante del pelotón, mirando hacia ellos
			var l: int = leader()
			var fwd := car_fwd(l)
			var pl := car_pos(l) + fwd * (24.0 + 6.0 * sin(u * 0.4))
			return {"pos": pl + Vector3(0, 1.3, 0), "look": pack_center() + Vector3(0, 0.6, 0), "fov": 64.0, "smooth": 5.0}
		"ghost_back": # auto fantasma invisible por delante del pelotón con cámara mirando hacia atrás
			var lead_s: float = core.pel.s[leader()]
			var want := lead_s + 46.0 + 8.0 * sin(u * 0.4)
			_ghost_s = lerpf(_ghost_s, want, 1.0 - exp(-dt * 2.0))
			var gp := route_pt(_ghost_s, 0.9 * sin(u * 0.5), 1.5 + 0.4 * sin(u * 0.8))
			return {"pos": gp, "look": pack_center() + Vector3(0, 0.5, 0), "fov": 66.0, "smooth": 6.0}
		"ghost_close": # el fantasma va por delante de un auto elegido: ese auto se le acerca despacio y al final lo pasa
			var kk: int = k
			var prog := clampf(u / maxf(d_s, 1.0), 0.0, 1.0)
			var dist := lerpf(44.0, 11.0, prog * prog)
			_ghost_s = core.pel.s[kk] + dist
			var lat_c: float = core.pel.lat[kk]
			var hw_g := hw_at(_ghost_s) - 0.4
			var side_g := -1.0 if lat_c > 0.0 else 1.0 # del lado opuesto al auto: nunca en su camino
			var gp3 := route_pt(_ghost_s, clampf(lat_c + side_g * 3.0, -hw_g, hw_g), 0.75 + 0.5 * prog)
			var tgt_c := car_pos(kk) + Vector3(0, 0.55, 0)
			return {"pos": gp3, "look": tgt_c, "fov": lerpf(58.0, 74.0, prog), "smooth": 7.0, "min_h": 0.35}
		"ghost_hold": # el fantasma queda quieto en la ruta (a ras del suelo, en la banquina) y el pelotón lo pasa
			var side := 1.0
			var sf2: float = _ghost_s
			var base2 := route_pt(sf2, (hw_at(sf2) - 0.7) * side, 0.55)
			var lead_k: int = leader()
			var tgt_p := car_pos(lead_k)
			var near := base2.distance_to(tgt_p)
			var behind := route_pt(sf2 - 40.0, 0.0, 0.7)
			var lk := tgt_p if near < 70.0 else behind
			return {"pos": base2, "look": lk + Vector3(0, 0.6, 0), "fov": 74.0, "min_h": 0.3, "smooth": 3.0}
		"ghost_run": # el fantasma avanza algo más lento y el pelotón lo va pasando
			var v_g := maxf(10.0, float(core.pel.v_p) * 0.82)
			_ghost_s += v_g * dt
			var gp2 := route_pt(_ghost_s, hw_at(_ghost_s) * 0.45, 1.1)
			var nearest := 0
			var nd := 1e9
			for q in core.cars.size():
				var dd := car_pos(q).distance_to(gp2)
				if dd < nd:
					nd = dd
					nearest = q
			var tgt2 := car_pos(nearest) if core.pel.s[nearest] > _ghost_s - 80.0 else pack_center()
			return {"pos": gp2, "look": tgt2 + Vector3(0, 0.6, 0), "fov": 66.0, "smooth": 5.0}
		"zoom": # lente que sigue y se aleja: el auto mantiene su tamaño mientras el fondo se comprime (dolly zoom)
			var dd2 := 6.0 + 10.0 * clampf(u / maxf(d_s, 1.0), 0.0, 1.0)
			var ang2 := 0.35
			var off2 := Basis(Vector3.UP, atan2(fw.x, fw.z) + PI + ang2) * Vector3(0, 0, dd2)
			var fov_h := rad_to_deg(2.0 * atan(2.4 / dd2))
			return {"pos": cp + Vector3(off2.x, 1.3, off2.z), "look": cp + Vector3(0, 0.7, 0), "fov": clampf(fov_h * 2.1, 22.0, 80.0), "smooth": 8.0}
		"dolly": # seguimiento con zoom que se abre: arranca con teleobjetivo y retrocede
			var p_u := clampf(u / maxf(d_s, 1.0), 0.0, 1.0)
			var dd3 := 9.0 + 6.0 * p_u
			var tgt3 := cp - fw * dd3 + rt * 1.6 + Vector3(0, 1.0, 0)
			return {"pos": tgt3, "look": cp + Vector3(0, 0.6, 0), "fov": lerpf(30.0, 62.0, p_u), "smooth": 6.0}
		"bridge_side": # a un costado del puente, rasante, con los autos cruzando
			var sm := float(sh.get("s_ref", 0.0))
			var pos4 := route_pt(sm - 14.0, hw_at(sm) + 9.0, 7.0 + 1.5 * sin(u * 0.5))
			return {"pos": pos4, "look": pack_center() + Vector3(0, 0.8, 0), "fov": 58.0, "smooth": 2.0, "min_h": 5.0}
	return {"pos": cp + Vector3(0, 3, -8), "look": cp, "fov": 70.0}
