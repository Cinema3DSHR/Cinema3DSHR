extends SceneTree
## Prueba sin imagen: corre la cinemática completa con la física y la IA reales y mide el pelotón.
const Core := preload("res://cine/cine_core.gd")
func _circle_over(pa, pb) -> float:
	var worst := 0.0
	var La: float = pa.V.wheelBase + 1.5
	var Lb: float = pb.V.wheelBase + 1.5
	var ra := maxf(0.95, pa.V.trackF * 0.5 + 0.05)
	var rb := maxf(0.95, pb.V.trackF * 0.5 + 0.05)
	for ia in 3:
		for ib in 3:
			var ka := float(ia - 1)
			var kb := float(ib - 1)
			var cx: float = (pb.px + sin(pb.yaw) * kb * Lb * 0.34) - (pa.px + sin(pa.yaw) * ka * La * 0.34)
			var cz: float = (pb.pz + cos(pb.yaw) * kb * Lb * 0.34) - (pa.pz + cos(pa.yaw) * ka * La * 0.34)
			worst = maxf(worst, ra + rb - sqrt(cx * cx + cz * cz))
	return worst

func _initialize() -> void:
	var T := 330.0
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--t="):
			T = float(a.substr(4))
	var core = Core.new()
	core.build(false)
	print("RUTA %d m · peaje en s=%.0f · estación i=%d" % [int(core.track.length), core.toll_s, core.anchor])
	var t0 := Time.get_ticks_msec()
	var next_log := 0.0
	var spread_max := 0.0
	var hits := 0
	var hit_pairs := {}
	var bucket := {}
	var offroad := 0
	var sp_log: Array = []
	var next_sp := 0.0
	var max_slip := 0.0
	var off_b := {}
	var off_n := 0
	var brk_prev := PackedByteArray()
	brk_prev.resize(7)
	var brk_edges := PackedInt32Array([0, 0, 0, 0, 0, 0, 0])
	var thr_edges := PackedInt32Array([0, 0, 0, 0, 0, 0, 0])
	var thr_prev := PackedByteArray()
	thr_prev.resize(7)
	var slip_b := {}
	while core.sim_t < T:
		core.step_to(core.sim_t + 0.05)
		if core.sim_t >= next_sp:
			next_sp += 0.5
			sp_log.append(snappedf(core.pel.s_p, 0.1))
		if core.sim_t > 95.0 and core.sim_t < 108.0 and int(core.sim_t * 20.0) % 2 == 0:
			var d2 = core.drivers[2]
			print("S2 t=%.2f v=%.1f vtgt_max=%.1f vprof=%.1f thr=%.2f brk=%.2f tff=%.2f steer=%.2f kap=%.4f" % [core.sim_t, core.pel.spd[2], d2.max_v, core.pel.v_free(2) if core.pel.has_method("v_free") else d2.prof["v"][d2.idx], d2.throttle, d2.brake, d2._tff, d2.steer, d2.prof["kap"][mini(d2.idx + 6, core.track.n - 1)]])
		if core.sim_t > 113.0 and int(core.sim_t * 20.0) % 5 == 0:
			var d3 = core.drivers[0]
			var p3 = core.cars[0].phys
			print("W0 t=%.2f y=%.3f vy=%.2f pitch=%.2f roll=%.2f contact=%s surf=%s fx=%s" % [core.sim_t, p3.py, p3.vy, p3.pitch, p3.roll, str([p3.wheels[0].contact, p3.wheels[1].contact, p3.wheels[2].contact, p3.wheels[3].contact]), str(core.cars[0].snap.wheel_fx[0]), str(core.cars[0].snap.wheel_fx[1])])
			print("TR3 t=%.2f s=%.0f lat=%.2f lane_t=%.2f steer=%.2f v=%.0f vt_cap=%.0f slip=%.0f yawrate=%.2f unstick=%.1f caution=%.2f" % [core.sim_t, core.pel.s[3], d3.lat, d3.lane_t, d3.steer, p3.vLong * 3.6, d3.max_v * 3.6, rad_to_deg(atan2(p3.vLat, maxf(1.0, absf(p3.vLong)))), p3.yawRate, d3.unstick_t, d3.caution])
		for a in core.cars.size():
			var pa = core.cars[a].phys
			var tr = core.cars[a].driver.track
			if core.sim_t > 30.0:
				var bnow := 1 if core.drivers[a].brake > 0.15 else 0
				if bnow == 1 and brk_prev[a] == 0:
					brk_edges[a] += 1
				brk_prev[a] = bnow
				var tnow := 1 if core.drivers[a].throttle > 0.6 else 0
				if tnow != thr_prev[a]:
					thr_edges[a] += 1
				thr_prev[a] = tnow
			var gix: int = mini(core.drivers[a].idx, core.track.n - 1)
			if absf(core.drivers[a].lat) > float(core.track.hwa[gix]) + float(core.track.shl[gix]) + 0.3:
				offroad += 1
				if core.sim_t > 20.0 and off_n < 14 and int(core.sim_t * 20.0) % 10 == 0:
					off_n += 1
					var dd = core.drivers[a]
					var kk: float = dd.prof["kap"][mini(dd.idx + 6, core.track.n - 1)]
					print("   s=%.0f kap=%.4f (R=%.0f) vfree=%.0f max_v=%.0f lane_t=%.2f steer=%.2f thr=%.2f brk=%.2f slip=%.0f°" % [core.pel.s[a], kk, 1.0 / maxf(kk, 1e-4), dd.prof["v"][mini(dd.idx, core.track.n - 1)] * 3.6, dd.max_v * 3.6, dd.lane_t, dd.steer, dd.throttle, dd.brake, rad_to_deg(atan2(pa.vLat, maxf(1.0, absf(pa.vLong))))])
					print("OFF car %d t=%.1f lat=%.2f hw=%.2f shl=%.2f v=%.0f kph" % [a, core.sim_t, core.drivers[a].lat, float(core.track.hwa[gix]), float(core.track.shl[gix]), pa.vLong * 3.6])
				var ob := int(core.sim_t / 20.0) * 20
				off_b[ob] = int(off_b.get(ob, 0)) + 1
			var sl := absf(atan2(pa.vLat, maxf(1.0, absf(pa.vLong))))
			max_slip = maxf(max_slip, sl)
			if sl > 0.6:
				slip_b["%d@%d" % [a, int(core.sim_t / 10.0) * 10]] = 1
			for b in range(a + 1, core.cars.size()):
				if _circle_over(pa, core.cars[b].phys) > 0.0:
					hits += 1
					hit_pairs["%d-%d" % [a, b]] = int(core.sim_t)
					if hits < 400 and hits % 6 == 1:
						print("HIT %d-%d t=%.2f s=%.0f/%.0f lat=%.1f/%.1f v=%.0f/%.0f" % [a, b, core.sim_t, core.pel.s[a], core.pel.s[b], core.drivers[a].lat, core.drivers[b].lat, pa.vLong * 3.6, core.cars[b].phys.vLong * 3.6])
					var bk := int(core.sim_t / 20.0) * 20
					bucket[bk] = int(bucket.get(bk, 0)) + 1
		if core.sim_t >= next_log:
			next_log += 5.0
			var line := "t=%5.1f |" % core.sim_t
			var smin := 1e9
			var smax := -1e9
			for i in core.cars.size():
				var ph = core.cars[i].phys
				var sp := sqrt(ph.vx * ph.vx + ph.vz * ph.vz) * 3.6
				line += " %3d" % int(sp)
				smin = minf(smin, core.pel.s[i]); smax = maxf(smax, core.pel.s[i])
			line += " | s_lead=%5.0f spread=%3.0f" % [smax, smax - smin]
			print(line)
			if core.sim_t > 40.0:
				spread_max = maxf(spread_max, smax - smin)
		var fin := true
		for i in core.cars.size():
			if core.pel.s[i] < core.track.length - 60.0:
				fin = false
		if fin:
			print("TODOS LLEGARON t=%.1f" % core.sim_t)
			break
	var offs := 0
	for dr in core.drivers:
		offs += dr.respawns
	var jf := FileAccess.open("res://cine/telemetria.json", FileAccess.WRITE)
	jf.store_string(JSON.stringify({"step": 0.5, "sp": sp_log, "t_end": snappedf(core.sim_t, 0.1)}))
	jf.close()
	print("PEDALES frenadas por auto: ", brk_edges, " · cambios de gas >60%%: ", thr_edges, " (en %.0f s)" % (core.sim_t - 30.0))
	print("BUCKETS ", bucket)
	print("OFFROAD ", off_b)
	print("DERRAPES>34° ", slip_b.keys())
	print("CHOQUES entre autos: %d cuadros con solapamiento · pares %s · fuera del camino: %d cuadros · deslizamiento máx %.0f°" % [hits, str(hit_pairs), offroad, rad_to_deg(max_slip)])
	print("RESUMEN t=%.1f s · spread_max(>40s)=%.0f m · pasadas=%d · separación mínima en el mismo carril %.1f m · respawns=%d · cálculo %.1f s" % [core.sim_t, spread_max, int(core.pel.stats["passes"]), float(core.pel.stats["min_gap"]), offs, (Time.get_ticks_msec() - t0) / 1000.0])
	quit()
