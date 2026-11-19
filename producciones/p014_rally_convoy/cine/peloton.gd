extends RefCounted
## Pelotón de la cinemática «Rally Convoy»: siete autos que corren JUNTOS con la física y la IA originales de Dream Racing
## (ai_driver.gd). No mueve autos: cada 0,05 s le ajusta a cada piloto de IA su tope de velocidad (`max_v`), su ritmo (`pace`) y su
## trazada (`lane_t`, con `line_free`).
##  · PUNTO GUÍA: un auto fantasma de ritmo (sin dibujo) recorre la ruta a la velocidad que TODOS pueden sostener (la mínima de los siete
##    en cada punto, con aceleración y frenada realistas). Cada auto tiene su lugar (ranura) respecto del punto guía; si se adelanta
##    de su lugar baja el ritmo, si se atrasa aprieta un poco. Como el punto guía es más lento que cualquiera, nadie queda abandonado.
##  · Formación en fila escalonada en dos carriles; cada tanto el de atrás pasa al de adelante (cambian las posiciones y el liderazgo)
##    sólo en rectas, por el carril libre. En curva y en montaña van en fila india.
##  · TRAZADA DE CARRERA: entran por afuera, tocan el vértice por adentro y salen por afuera.
##  · Separación mínima: nunca hay dos autos solapados.

const N_GAP := 14.0 # m entre ranuras de la fila
const GRID_V := 8.0 # m/s: velocidad de entrada al peaje (29 km/h)
const GRID_ACC := 0.17 # (m/s) por metro pasado el peaje: aceleración progresiva de la salida
const A_ACC := 3.3 # m/s²: aceleración que sostienen todos (la del más lento)
const A_BRK := 6.5 # m/s²
const E_TOL := 3.0 # m
const SLEW := 4.5 # m/s: velocidad con que una ranura se corre (pasadas)
const PASS_EVERY := 11.0 # s entre pasadas (en rectas)

var track
var cars: Array = []
var drivers: Array = []
var n := 0
var s := PackedFloat64Array()
var lat := PackedFloat64Array()
var spd := PackedFloat64Array()
var lane_idx := PackedInt32Array()
var lane_mix := PackedFloat64Array() # −1..1 posición actual dentro del ancho de carril (suave)
var slot := PackedFloat64Array() # ranura actual (m respecto del punto guía)
var rank := PackedInt32Array() # 0 = adelante
var vp := PackedFloat32Array() # velocidad del punto guía por muestra (m/s)
var s_p := 0.0 # posición del punto guía
var v_p := 0.0
var s_toll := 0.0
var go_t := 1e9
var t := 0.0
var stats := {"max_spread": 0.0, "passes": 0, "min_gap": 1e9}
var _tick := 0.0
var _next_pass := 0.0
var _passing := {} # {rank: [i_front, i_back]} pasadas en curso
var _rng := RandomNumberGenerator.new()
var kap_s := PackedFloat32Array() # curvatura con signo suavizada (+ izquierda)
var line_cache := PackedFloat32Array() # trazada ideal por muestra (m, + = derecha)

func setup(p_track, p_cars: Array, p_drivers: Array, s_grid: float) -> void:
	track = p_track
	cars = p_cars
	drivers = p_drivers
	n = cars.size()
	_rng.seed = 1313
	for arr in [s, lat, spd, lane_mix, slot]:
		arr.resize(n)
	lane_idx.resize(n)
	rank.resize(n)
	_measure()
	# orden inicial = orden de la parrilla (el que está más adelante en la ruta es el 0)
	var order: Array = []
	for i in n:
		order.append(i)
	order.sort_custom(func(a: int, b: int) -> bool: return s[a] > s[b] + 0.5 or (absf(s[a] - s[b]) <= 0.5 and lat[a] > lat[b]))
	for r in n:
		rank[order[r]] = r
		lane_idx[order[r]] = 1 if lat[order[r]] > 0.0 else -1
	for i in n:
		slot[i] = s[i] - s_grid
	s_p = s_grid
	_build_speed_profile()
	_build_line()
	_next_pass = 1e9

func _measure() -> void:
	for i in n:
		var d = drivers[i]
		var ph = cars[i].phys
		s[i] = float(track.cum[mini(d.idx, track.n - 1)])
		lat[i] = d.lat
		spd[i] = sqrt(ph.vx * ph.vx + ph.vz * ph.vz)

## Velocidad máxima sostenible por todos en cada muestra (mínimo de los siete perfiles de la IA y del límite de cada tramo),
## con aceleración y frenada acotadas (pasada hacia adelante y hacia atrás)
func _build_speed_profile() -> void:
	var N: int = track.n
	vp.resize(N)
	for i in N:
		var v := limit_at(i)
		for d in drivers:
			v = minf(v, float(d.prof["v"][i]) * (0.82 + 0.18 * d.skill))
		vp[i] = v * 0.92
		if track.cum[i] < s_toll + 25.0:
			vp[i] = minf(vp[i], GRID_V)
		else:
			vp[i] = minf(vp[i], GRID_V + GRID_ACC * (track.cum[i] - s_toll - 25.0))
	for i in range(1, N): # aceleración
		var ds: float = track.cum[i] - track.cum[i - 1]
		vp[i] = minf(vp[i], sqrt(vp[i - 1] * vp[i - 1] + 2.0 * A_ACC * ds))
	for i in range(N - 2, -1, -1): # frenada
		var ds: float = track.cum[i + 1] - track.cum[i]
		vp[i] = minf(vp[i], sqrt(vp[i + 1] * vp[i + 1] + 2.0 * A_BRK * ds))

## Trazada de carrera por muestra: afuera antes de la curva, adentro en el vértice, afuera a la salida
func _build_line() -> void:
	var N: int = track.n
	kap_s.resize(N)
	line_cache.resize(N)
	for i in N:
		var a: Vector3 = track.samples[maxi(i - 4, 0)]
		var b: Vector3 = track.samples[i]
		var c: Vector3 = track.samples[mini(i + 4, N - 1)]
		var h1 := atan2(b.x - a.x, b.z - a.z)
		var h2 := atan2(c.x - b.x, c.z - b.z)
		var dh := atan2(sin(h2 - h1), cos(h2 - h1))
		kap_s[i] = dh / maxf(0.5, Vector2(c.x - a.x, c.z - a.z).length() * 0.5)
	# suavizado
	var sm := PackedFloat32Array()
	sm.resize(N)
	for i in N:
		var acc := 0.0
		var c := 0
		for j in range(-6, 7):
			acc += kap_s[clampi(i + j, 0, N - 1)]
			c += 1
		sm[i] = acc / float(c)
	kap_s = sm
	for i in N:
		var amax := maxf(0.0, float(track.hwa[i]) - 2.2)
		var g_here := clampf(kap_s[i] * 55.0, -1.0, 1.0)
		var g_ahead := clampf(kap_s[mini(i + 24, N - 1)] * 55.0, -1.0, 1.0) # ~60 m adelante
		var g_back := clampf(kap_s[maxi(i - 16, 0)] * 55.0, -1.0, 1.0) # salida
		# kap + = izquierda, lateral + = derecha: el vértice de una curva a la izquierda está a la izquierda (−)
		var off := -g_here + 0.85 * g_ahead * (1.0 - absf(g_here)) + 0.5 * g_back * (1.0 - absf(g_here))
		line_cache[i] = clampf(off, -1.0, 1.0) * amax * 0.8

func lane_width(i: int) -> float:
	var d = drivers[i]
	var hw := float(track.hwa[mini(d.idx, track.n - 1)])
	return clampf(hw - 2.0, 1.1, 2.0)

func curve_ahead(i: int, dist_m := 80.0) -> bool:
	var d = drivers[i]
	var kp: PackedFloat32Array = d.prof["kap"]
	var N: int = track.n
	var steps := int(dist_m / 2.5)
	for k in range(2, steps, 3):
		if kp[(d.idx + k) % N] > 1.0 / 190.0:
			return true
	return false

func vp_at(sm: float) -> float:
	var i: int = track.idx_at(sm)
	return vp[clampi(i, 0, track.n - 1)]

func update(dt: float, tt: float) -> void:
	t = tt
	_tick += dt
	if _tick < 0.05:
		return
	var h := _tick
	_tick = 0.0
	_measure()
	if _next_pass > 1e8 and tt >= go_t:
		_next_pass = go_t + 16.0
	# punto guía
	if tt >= go_t:
		v_p = vp_at(s_p)
		s_p += v_p * h
	# estadísticas
	var smin := 1e18
	var smax := -1e18
	for i in n:
		smin = minf(smin, s[i])
		smax = maxf(smax, s[i])
	stats["max_spread"] = maxf(float(stats["max_spread"]), smax - smin)
	var curvy := PackedByteArray()
	curvy.resize(n)
	var any_curve := false
	for i in n:
		curvy[i] = 1 if curve_ahead(i, 110.0) else 0
		if curvy[i] == 1:
			any_curve = true
	# ranuras objetivo según el rango (formación en fila escalonada); las pasadas intercambian rangos
	var started := tt >= go_t + 6.0
	if started and tt >= _next_pass and _passing.is_empty() and tt > go_t + 14.0:
		var r := _rng.randi_range(0, n - 2) # el del rango r+1 pasa al del rango r
		var i_front := -1
		var i_back := -1
		for i in n:
			if rank[i] == r:
				i_front = i
			elif rank[i] == r + 1:
				i_back = i
		_next_pass = tt + 3.0 # si ahora no se puede (curva) se reintenta enseguida
		if curvy[i_front] == 0 and curvy[i_back] == 0 and float(track.hwa[mini(drivers[i_front].idx, track.n - 1)]) >= 4.0:
			_passing[r] = [i_front, i_back]
			_next_pass = tt + PASS_EVERY + _rng.randf_range(-3.0, 4.0)
			stats["passes"] = int(stats["passes"]) + 1
		# el de atrás se corre al lado opuesto del de adelante para pasar (ya van en carriles opuestos: se mantienen)
	for r in _passing.keys():
		var pr: Array = _passing[r]
		var a: int = pr[0]
		var b: int = pr[1]
		if curvy[a] == 1 or curvy[b] == 1:
			pass # en curva la pasada espera (la fila no se desarma)
		if s[b] > s[a] + 6.0 and absf(lat[b] - lat[a]) > 0.0:
			# ya pasó: intercambian rangos y carriles
			rank[a] = r + 1
			rank[b] = r
			var la := lane_idx[a]
			lane_idx[a] = lane_idx[b]
			lane_idx[b] = la
			_passing.erase(r)
	# ── control de cada auto
	for i in n:
		var d = drivers[i]
		if tt < go_t + 0.35 * float(n - 1 - rank[i]): # el de adelante arranca primero
			d.enabled = false
			continue
		d.enabled = true
		d.line_free = true
		# ranura: hacia el lugar de su rango (si va pasando, hacia el del que pasa)
		var want_rank := rank[i]
		for r in _passing.keys():
			var pr: Array = _passing[r]
			if i == pr[1]:
				want_rank = r # el que pasa va hacia adelante
			elif i == pr[0]:
				want_rank = r + 1 # el pasado se deja ir hacia atrás
		var gap_f := N_GAP * (1.0 if tt > go_t + 6.0 else 0.8)
		var tgt := float(3 - want_rank) * gap_f
		slot[i] = move_toward(slot[i], tgt, SLEW * h) if tt > go_t + 4.0 else slot[i] + (spd[i] - v_p) * h
		var e: float = s[i] - (s_p + slot[i])
		var gi: int = mini(d.idx, track.n - 1)
		var cap := vp[gi] * 1.06 # un poco más rápido que el punto guía para alcanzar su lugar (el perfil de cada auto sigue mandando en las curvas)
		if e > E_TOL:
			cap = minf(cap, maxf(6.0, vp[gi] * (1.0 - clampf(0.05 * (e - E_TOL), 0.0, 0.75))))
		d.pace = 1.0 # nunca por encima de lo que da su propio perfil: no hay curva que se tome pasado
		# separación: ningún auto se acerca a otro
		for j in n:
			if j == i:
				continue
			var gap := s[j] - s[i]
			if gap <= 0.0 or gap > 70.0:
				continue
			stats["min_gap"] = minf(float(stats["min_gap"]), gap if absf(lat[j] - lat[i]) < 2.6 else 1e9)
			var req := 13.0 if (lane_idx[j] == lane_idx[i] or curvy[i] == 1 or absf(lat[j] - lat[i]) < 3.0) else 6.5
			req += 0.10 * maxf(0.0, spd[i] - 15.0)
			req += pow(maxf(0.0, spd[i] - spd[j]), 2.0) / 9.0 # si se acerca rápido, frena con tiempo
			if gap < req:
				cap = minf(cap, maxf(4.0, spd[j] * 0.97 - 0.9 * (req - gap)))
		d.max_v = cap
		# trazada: línea de carrera + posición en el carril (el carril se cierra en curva y en caminos angostos: fila india)
		var lw := lane_width(i) * (0.0 if curvy[i] == 1 else 1.0)
		var tgt_lane := float(lane_idx[i]) * lw
		lane_mix[i] = move_toward(lane_mix[i], tgt_lane, 1.2 * h)
		var look := mini(track.n - 1, gi + int(spd[i] * 0.45 / 2.5))
		d.lane_t = clampf(float(line_cache[look]) + lane_mix[i], -(float(track.hwa[gi]) - 1.8), float(track.hwa[gi]) - 1.8)

## Límite de velocidad de la cinemática por ambiente (m/s). En montaña no hay tope: manda el perfil de la IA (frena para cada curva).
func limit_at(i: int) -> float:
	var b := int(track.biomea[i])
	var f := int(track.flaga[i])
	if (f & 2) != 0:
		return 36.0 # puente
	match b:
		0: return 30.0 # ciudad (108 km/h)
		1: return 41.0 # campo (148 km/h)
		2: return 34.0 # bosque
	return 90.0
