## ACCIDENTE (cap. 1): el cupé negro avanza por la ruta de montaña bajo la lluvia, entra a una curva a la izquierda, se despista, choca contra las rocas del borde,
## vuelca (una vuelta completa) y queda destrozado cerca del precipicio. Gabriel y Elena adentro, quietos (sin reacciones a las curvas). No se explica la causa.
## Trayectoria guionada (cinemática, sin física): continua y sin saltos. Hornea a 30 fps y exporta GLB + JSON. Vertical 540×960.
## Uso: xvfb-run -a godot --path . --rendering-driver opengl3 --resolution 540x960 --script res://tools/accidente.gd -- SALIDA [segundos] [sin_glb]
extends SceneTree
const FPS := 30.0
const V0 := 22.0                       # m/s antes de la curva
const R := 60.0                        # radio de la curva (izquierda)
const S_RECTA := 190.0                 # m de recta antes de la curva
const T_SKID := 8.6                    # empieza a despistar
const T_IMPACTO := 10.3
const T_ROLL_FIN := 13.4
const T_REPOSO := 14.6
const T_EYECTA := 10.55                 # Elena sale despedida del auto durante el vuelco
const T_SALE := 16.0                    # Gabriel sale del auto
const T_DESMAYO := 44.6
const CARRIL := -2.0                   # el auto va por el carril derecho (desplazamiento lateral; positivo = izquierda)
const CHARCOS_S := [66.0, 101.0, 137.0, 172.0]   # metros de ruta donde hay charcos grandes
const PISO := -0.50                    # piso de la cabina respecto del centro del auto
const Y0 := 0.75                       # altura del centro del auto sobre el asfalto
const MEDIO_ANCHO := 4.0
var DUR := 80.0                         # sólo para simular; la duración real sale de la ruta de Gabriel
var esc: Node3D
var anim: Animation
var ap: AnimationPlayer
var carro: Node3D                      # «AutoRaiz»: se mueve con la trayectoria
var ok_car: Node3D
var da_car: Node3D
var limp_ok: Array
var limp_da: Array
var G: Actor3
var E: Actor3
var G2: Actor3                         # Gabriel de pie (sale del auto)
var ELENA_N: Node3D                    # nodo del mundo que lleva a Elena (viaja con el auto hasta ser despedida)
var elena_p := Vector3.ZERO
var elena_v := Vector3.ZERO
var RUTA_G: Array = []                 # recorrido de Gabriel: [t0, t1, clip, pos_ini, pos_fin, yaw_ini, yaw_fin, vel_clip]
var RG: RigSentado
var RE: RigSentado
var cams := {}
var ruedas := {}
var total := 0
var st_pos: Array = []                 # por cuadro: posición, yaw, pitch, roll del auto
var st_yaw: Array = []
var st_pit: Array = []
var st_rol: Array = []
var st_vel: Array = []
var DIR_SKID := Vector3.ZERO
var P_SKID := Vector3.ZERO
var YAW_SKID := 0.0
var P_IMP := Vector3.ZERO

# ───────── ruta ─────────
func centro(s: float) -> Vector3:                   # punto de la línea central a s metros (la recta va hacia −Z; después gira a la izquierda)
	if s <= S_RECTA:
		return Vector3(0, 0, 60.0 - s)
	var th := (s - S_RECTA) / R
	return Vector3(-R + R * cos(th), 0, -130.0 - R * sin(th))

func rumbo(s: float) -> float:                      # yaw del tramo (0 = hacia −Z; positivo = gira a la izquierda)
	return 0.0 if s <= S_RECTA else (s - S_RECTA) / R

func _suave(a: float, b: float, x: float) -> float:
	var u := clampf((x - a) / (b - a), 0.0, 1.0)
	return u * u * (3.0 - 2.0 * u)

# ───────── trayectoria del auto (se integra una sola vez) ─────────
func _simular() -> void:
	var dt := 1.0 / FPS
	var pos := centro(30.0) + Vector3(-1.0, 0, 0) * CARRIL * -1.0
	var s := 30.0
	var yaw := 0.0
	var vel := V0
	var dir := Vector3(0, 0, -1)
	var yaw_off := 0.0
	for g in total:
		var t := float(g) * dt
		var roll := 0.0
		var pit := 0.0
		var hop := 0.0
		if t < T_SKID:
			s += V0 * dt
			yaw = rumbo(s)
			pos = centro(s) + Vector3(-cos(yaw), 0, sin(yaw)) * CARRIL
			vel = V0
			if t + dt >= T_SKID:                               # fotograma de arranque del derrape: guarda la recta tangente
				P_SKID = pos; YAW_SKID = yaw
				DIR_SKID = Vector3(-sin(yaw), 0, -cos(yaw))
		else:
			if t < T_IMPACTO:
				vel = lerpf(V0, 15.0, _suave(T_SKID, T_IMPACTO, t))
			else:
				vel = lerpf(6.0, 0.0, _suave(T_IMPACTO, T_ROLL_FIN + 0.5, t))
				if t < T_IMPACTO + dt:
					P_IMP = pos
			# el auto gira sobre sí mismo (sobreviraje) mientras sigue en línea recta por inercia
			var t_giro := T_REPOSO - T_SKID
			var ya := 0.95 * _suave(T_SKID, T_IMPACTO, t) + 1.05 * _suave(T_IMPACTO, T_REPOSO, t)
			yaw = YAW_SKID + ya
			var ddir := DIR_SKID if t < T_IMPACTO else DIR_SKID.rotated(Vector3.UP, 0.35 * _suave(T_IMPACTO, T_ROLL_FIN, t))
			pos += ddir * vel * dt
			if t >= T_IMPACTO:
				var u := clampf((t - T_IMPACTO) / (T_ROLL_FIN - T_IMPACTO), 0.0, 1.0)
				var e := 1.0 - pow(1.0 - u, 2.2)                          # arranca rápido y se frena
				roll = TAU * e + 0.09 * _suave(T_ROLL_FIN, T_REPOSO, t)  # una vuelta completa y un resto de inclinación
				hop = 0.9 * sin(PI * u) * (1.0 - u * 0.4)                # rebota mientras vuelca
				pit = -0.22 * sin(PI * minf(u * 3.0, 1.0)) + 0.10 * sin(PI * u)
			# cabeceo del derrape
			if t < T_IMPACTO:
				roll = -0.05 * _suave(T_SKID, T_SKID + 1.0, t)
		st_pos.append(pos + Vector3(0, Y0 + hop, 0))
		st_yaw.append(yaw); st_pit.append(pit); st_rol.append(roll); st_vel.append(vel)

# ───────── construcción del mundo ─────────
func _mat(c: Color, r := 0.5, m := 0.0) -> StandardMaterial3D:
	var s := StandardMaterial3D.new(); s.albedo_color = c; s.roughness = r; s.metallic = m; return s

func _caja(p: Node, nom: String, pos: Vector3, tam: Vector3, m: Material, rot_y := 0.0) -> MeshInstance3D:
	var mi := MeshInstance3D.new(); var b := BoxMesh.new(); b.size = tam; mi.mesh = b; mi.material_override = m; mi.name = nom; mi.position = pos; mi.rotation.y = rot_y; p.add_child(mi); return mi

func _tira(nom: String, lado: float, ancho: float, y: float, m: Material, s0: float, s1: float, paso := 2.0) -> MeshInstance3D:
	# malla de una cinta que sigue la línea central (lado = desplazamiento lateral del centro de la cinta, positivo = izquierda)
	var st := SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var n := int((s1 - s0) / paso)
	for i in n:
		var a := s0 + i * paso; var b := a + paso
		var pa := centro(a); var pb := centro(b)
		var la := Vector3(-cos(rumbo(a)), 0, 0).rotated(Vector3.UP, 0.0)          # izquierda del tramo
		var ya := rumbo(a); var yb := rumbo(b)
		var izqa := Vector3(-cos(ya), 0, sin(ya)); var izqb := Vector3(-cos(yb), 0, sin(yb))
		var a0 := pa + izqa * (lado + ancho * 0.5); var a1 := pa + izqa * (lado - ancho * 0.5)
		var b0 := pb + izqb * (lado + ancho * 0.5); var b1 := pb + izqb * (lado - ancho * 0.5)
		for v in [a0, a1, b0, a1, b1, b0]:
			st.add_vertex(v + Vector3(0, y, 0))
	st.generate_normals()
	var mi := MeshInstance3D.new(); mi.mesh = st.commit(); mi.material_override = m; mi.name = nom; esc.add_child(mi)
	return mi

func _construir_mundo() -> void:
	var asf := _mat(Color(0.016, 0.016, 0.02), 0.06, 0.3)
	var blanco := _mat(Color(0.8, 0.8, 0.75), 0.4)
	var amarillo := _mat(Color(0.7, 0.55, 0.1), 0.5)
	var metal := _mat(Color(0.2, 0.2, 0.22), 0.35, 0.8)
	_tira("Asfalto", 0.0, MEDIO_ANCHO * 2.0, 0.0, asf, 0.0, 330.0, 2.0)
	_tira("BordeIzq", MEDIO_ANCHO - 0.25, 0.14, 0.004, blanco, 0.0, 330.0, 2.0)
	_tira("BordeDer", -(MEDIO_ANCHO - 0.25), 0.14, 0.004, blanco, 0.0, 330.0, 2.0)
	for i in 36:                                                     # rayas del centro cada 9 m
		var s := 2.0 + i * 9.0
		var m := _tira("Raya_%d" % i, 0.0, 0.14, 0.004, amarillo, s, s + 3.2, 1.6)
	var roca := _mat(Color(0.05, 0.05, 0.055), 0.9)
	var rng := RandomNumberGenerator.new(); rng.seed = 4242
	# terreno: banquina de tierra en la zona del accidente y barranco más allá
	var tierra := _mat(Color(0.035, 0.03, 0.025), 0.95)
	var dir_t := DIR_SKID
	var yw := YAW_SKID
	_caja(esc, "Hombro", P_IMP + dir_t * -7.0 + Vector3(0, -0.06, 0), Vector3(70.0, 0.1, 39.6), tierra, yw)
	_caja(esc, "TerrenoAdentro", Vector3(-60.0, -0.06, -60.0), Vector3(80.0, 0.1, 420.0), tierra)
	_caja(esc, "Barranco", P_IMP + dir_t * 52.8 + Vector3(0, -30.0, 0), Vector3(140.0, 1.0, 80.0), _mat(Color(0.015, 0.015, 0.02), 1.0), yw)
	_caja(esc, "BordeBarranco", P_IMP + dir_t * 12.8 + Vector3(0, -15.0, 0), Vector3(70.0, 30.0, 1.0), _mat(Color(0.03, 0.028, 0.026), 1.0), yw)
	# baranda con postes, interrumpida donde el auto se sale (zona de la curva)
	for i in 70:
		var s := 4.0 + i * 4.0
		if s > 200.0 and s < 250.0:
			continue
		var c := centro(s); var y := rumbo(s); var izq := Vector3(-cos(y), 0, sin(y))
		var p := c - izq * (MEDIO_ANCHO + 0.5)
		_caja(esc, "Poste_%d" % i, p + Vector3(0, 0.35, 0), Vector3(0.1, 0.7, 0.1), metal, y)
		_caja(esc, "Baranda_%d" % i, p + Vector3(0, 0.62, 0) - Vector3(sin(y), 0, cos(y)) * 2.0, Vector3(0.06, 0.28, 4.05), metal, y)
	# árboles a ambos lados de la ruta
	var tronco := _mat(Color(0.04, 0.03, 0.025), 0.9); var hoja := _mat(Color(0.02, 0.05, 0.035), 0.9)
	for i in 80:
		var s := 6.0 + i * 4.1 + rng.randf_range(-1.5, 1.5)
		for lado in [-1.0, 1.0]:
			var c := centro(s); var y := rumbo(s); var izq := Vector3(-cos(y), 0, sin(y))
			var off: float = lado * rng.randf_range(MEDIO_ANCHO + 2.0, MEDIO_ANCHO + 9.0)
			if lado < 0 and s > 190.0: continue                           # no hay árboles donde el auto se sale
			var p := c + izq * off; var h := rng.randf_range(4.5, 9.0)
			var tr := MeshInstance3D.new(); var cm := CylinderMesh.new(); cm.top_radius = 0.12; cm.bottom_radius = 0.2; cm.height = h * 0.45; tr.mesh = cm; tr.material_override = tronco; tr.position = p + Vector3(0, h * 0.22, 0); tr.name = "Tronco_%d_%d" % [i, lado]; esc.add_child(tr)
			var co := MeshInstance3D.new(); var cn := CylinderMesh.new(); cn.top_radius = 0.0; cn.bottom_radius = rng.randf_range(1.1, 1.9); cn.height = h; co.mesh = cn; co.material_override = hoja; co.position = p + Vector3(0, h * 0.45 + h * 0.5, 0); co.name = "Copa_%d_%d" % [i, lado]; esc.add_child(co)
	# rocas grandes en el borde donde se estrella (alrededor del punto de impacto)
	for k in 14:
		var rp := P_IMP + Vector3(rng.randf_range(-2.8, 3.0), 0, rng.randf_range(-6.0, 4.0))
		var rm := MeshInstance3D.new(); var sm := SphereMesh.new(); sm.radius = 1.0; sm.height = 2.0; sm.radial_segments = 9; sm.rings = 6; rm.mesh = sm
		rm.material_override = roca; rm.scale = Vector3(rng.randf_range(0.7, 1.8), rng.randf_range(0.5, 1.3), rng.randf_range(0.7, 1.7)); rm.position = rp + Vector3(0, rm.scale.y * 0.5 - 0.1, 0); rm.rotation = Vector3(rng.randf() * 3, rng.randf() * 3, rng.randf() * 3); rm.name = "Roca_%d" % k; esc.add_child(rm)
	for k in 7:                                                          # montañas lejanas
		var mt := MeshInstance3D.new(); var cn2 := CylinderMesh.new(); cn2.top_radius = 0.0; cn2.bottom_radius = rng.randf_range(40, 80); cn2.height = rng.randf_range(70, 150); mt.mesh = cn2
		mt.material_override = _mat(Color(0.03, 0.035, 0.05), 1.0); mt.position = Vector3(-200 + k * 55 + rng.randf_range(-15, 15), cn2.height * 0.5 - 20, -520 + rng.randf_range(-40, 20)); mt.name = "Montana_%d" % k; esc.add_child(mt)

func _pista(n: Node, pos := true, rot := true, sc := false) -> Array:
	var p := esc.get_path_to(n); var r := [-1, -1, -1]
	if pos: r[0] = anim.add_track(Animation.TYPE_POSITION_3D); anim.track_set_path(r[0], p)
	if rot: r[1] = anim.add_track(Animation.TYPE_ROTATION_3D); anim.track_set_path(r[1], p)
	if sc: r[2] = anim.add_track(Animation.TYPE_SCALE_3D); anim.track_set_path(r[2], p)
	return r

func _clave(pt: Array, n: Node3D, t: float, glob := false) -> void:
	if pt[0] >= 0: anim.position_track_insert_key(pt[0], t, n.global_position if glob else n.position)
	if pt[1] >= 0:
		var bq: Basis = n.global_transform.basis if glob else n.transform.basis
		anim.rotation_track_insert_key(pt[1], t, Quaternion.IDENTITY if bq.get_scale().length() < 1e-5 else bq.orthonormalized().get_rotation_quaternion())
	if pt[2] >= 0: anim.scale_track_insert_key(pt[2], t, n.scale)

func _montar(prefijo: String, sin_glb: bool) -> void:
	await process_frame                                              # el árbol de escena recién está activo después del primer cuadro
	total = int(ceil(DUR * FPS)) + 1
	_simular()
	esc = Node3D.new(); esc.name = "Escena"; root.add_child(esc)
	var Au = load("res://tools/auto.gd"); var Da = load("res://tools/dano.gd")
	var we: WorldEnvironment = Au.entorno_noche(); we.name = "Entorno"; esc.add_child(we)
	anim = Animation.new(); anim.length = float(total - 1) / FPS; anim.step = 1.0 / FPS; anim.loop_mode = Animation.LOOP_NONE
	ap = AnimationPlayer.new(); ap.name = "Anim"; esc.add_child(ap)
	var lado0 := DIR_SKID.rotated(Vector3.UP, PI * 0.5)
	for td in [8.6, 9.4, 10.3, 11.0, 12.0, 13.4, 14.6, 20.0, 29.9]:
		var gg := int(td * FPS); var rel: Vector3 = st_pos[gg] - P_IMP
		print("TRAYECTORIA t=", td, " a lo largo ", snappedf(rel.dot(DIR_SKID), 0.1), " lateral ", snappedf(rel.dot(lado0), 0.1), " v ", snappedf(st_vel[gg], 0.1), " yaw ", snappedf(rad_to_deg(st_yaw[gg] - YAW_SKID), 1.0), " roll ", snappedf(rad_to_deg(st_rol[gg]), 1.0))
	_construir_mundo()
	carro = Node3D.new(); carro.name = "AutoRaiz"; esc.add_child(carro)
	ok_car = Au.crear(); ok_car.name = "AutoIntacto"; carro.add_child(ok_car); limp_ok = Au.limpiaparabrisas(ok_car)
	da_car = Au.crear(); da_car.name = "AutoDestruido"; carro.add_child(da_car); limp_da = Au.limpiaparabrisas(da_car)
	await process_frame
	Da.destruir(da_car, 0.65)
	for rn in [["Rueda_FL", -0.73, -1.2], ["Rueda_FR", 0.73, -1.2], ["Rueda_RL", -0.74, 1.34], ["Rueda_RR", 0.74, 1.34]]:
		var em := Node3D.new(); em.name = rn[0]; em.position = Vector3(rn[1], -0.75, rn[2]); carro.add_child(em)
	# luces
	for lado in [-1.0, 1.0]:
		var sp := SpotLight3D.new(); sp.name = "Faro_" + ("L" if lado < 0 else "R"); sp.position = Vector3(lado * 0.52, -0.02, -1.95); sp.rotation_degrees = Vector3(-5.0, 0, 0)
		sp.spot_range = 55.0; sp.spot_angle = 24.0; sp.spot_attenuation = 0.6; sp.light_energy = 9.0; sp.light_color = Color(1.0, 0.94, 0.8); carro.add_child(sp)
	var cola := OmniLight3D.new(); cola.name = "Luz_Trasera"; cola.position = Vector3(0, -0.05, 2.35); cola.light_color = Color(1, 0.05, 0.03); cola.light_energy = 0.12; cola.omni_range = 2.5; carro.add_child(cola)
	var rayo := DirectionalLight3D.new(); rayo.name = "Luz_Rayo"; rayo.rotation_degrees = Vector3(-50, 40, 0); rayo.light_color = Color(0.7, 0.8, 1.0); rayo.light_energy = 0.0; esc.add_child(rayo)
	var luna := DirectionalLight3D.new(); luna.name = "Luz_Luna"; luna.rotation_degrees = Vector3(-60, -30, 0); luna.light_color = Color(0.4, 0.5, 0.8); luna.light_energy = 0.8; esc.add_child(luna)
	for par in [["ok", ok_car], ["da", da_car]]:
		for nm in ["Wheel FL", "Wheel FR", "Wheel RL", "Wheel RR"]:
			var w := par[1].find_child(nm, true, false) as MeshInstance3D
			var padre := w.get_parent() as Node3D
			var Pb: Basis = (par[1].global_transform.affine_inverse() * padre.global_transform).basis
			var cen: Vector3 = w.transform * w.get_aabb().get_center()               # centro de la rueda en el espacio del padre
			var pv := Node3D.new(); pv.name = "RuedaPivote_" + par[0] + nm.replace(" ", "_")
			padre.add_child(pv); pv.transform = Transform3D(Basis.IDENTITY, cen)
			var wt := w.transform
			padre.remove_child(w); pv.add_child(w); w.transform = Transform3D(Basis.IDENTITY, -cen) * wt
			ruedas[par[0] + nm] = [pv, (Pb.inverse() * Vector3.RIGHT).normalized()]        # eje de giro (el del auto) en el espacio del padre
	var vol_ok := ok_car.find_child("rul", true, false) as Node3D
	# personajes dentro del auto (hijos del auto: viajan con él)
	G = Actor3.new(); G.cargar("gabriel", "res://assets/aiden.glb", "res://assets/aiden_meta.json", carro)
	ELENA_N = Node3D.new(); ELENA_N.name = "elena_mundo"; esc.add_child(ELENA_N)
	E = Actor3.new(); E.cargar("elena", "res://assets/kate.glb", "res://assets/kate_meta.json", ELENA_N)
	G2 = Actor3.new(); G2.cargar("gabriel_fuera", "res://assets/aiden.glb", "res://assets/aiden_meta.json", esc)
	G.raiz.position = Vector3(0.36, PISO, 0.20); G.raiz.rotation.y = PI
	E.raiz.position = Vector3(0.0, -0.30, 0.0); E.raiz.rotation.y = PI        # ELENA_N va a la altura de su cadera
	await process_frame
	_ruta_gabriel()
	RG = RigSentado.new(G.sk, G.raiz); RE = RigSentado.new(E.sk, E.raiz)
	print("rigs ", RG.ok, " ", RE.ok, " impacto en ", P_IMP.snapped(Vector3(0.1, 0.1, 0.1)))
	# pistas
	var p_carro := _pista(carro); var p_ok := _pista(ok_car, false, false, true); var p_da := _pista(da_car, false, false, true)
	var p_rued := {}; for k in ruedas: p_rued[k] = _pista(ruedas[k][0], false, true)
	var p_limp := []; for pv in limp_ok + limp_da: p_limp.append(_pista(pv, false, true))
	var p_sk := {}
	for ac in [G, E, G2]:
		var d := {}
		for h in ac.sk.get_bone_count():
			var tq := anim.add_track(Animation.TYPE_ROTATION_3D); anim.track_set_path(tq, NodePath("%s:%s" % [esc.get_path_to(ac.sk), ac.sk.get_bone_name(h)])); d[h] = tq
		var th := anim.add_track(Animation.TYPE_POSITION_3D); anim.track_set_path(th, NodePath("%s:%s" % [esc.get_path_to(ac.sk), ac.sk.get_bone_name(ac.hueso_cadera)])); d["pos"] = th
		p_sk[ac.id] = d
	var p_enodo := _pista(ELENA_N, true, true, true); var p_g_sc := _pista(G.raiz, false, false, true); var p_g2 := _pista(G2.raiz, true, true, true)
	var puerta_n := _puerta_conductor()
	var p_puerta := _pista(puerta_n, true, true)
	var puerta_base: Transform3D = da_car.global_transform.affine_inverse() * puerta_n.global_transform
	var tomas := _tomas()
	var p_cam := {}
	for tm in tomas:
		var c := Camera3D.new(); c.name = tm["camara"]; c.fov = tm["fov"]; c.near = 0.05; c.far = 700.0; esc.add_child(c); cams[tm["id"]] = c; p_cam[tm["id"]] = _pista(c)
	var inv_g := G.raiz.global_transform.affine_inverse()
	var ang := {}
	for k in ruedas: ang[k] = 0.0
	var cam_p := {}                                                     # posición suavizada de cada cámara de seguimiento
	var cam_m := {}
	var acc_f := Vector3.ZERO
	for g in total:
		var t := float(g) / FPS
		carro.global_transform = Transform3D(Basis.from_euler(Vector3(st_pit[g], st_yaw[g], st_rol[g]), EULER_ORDER_YXZ), st_pos[g])
		_clave(p_carro, carro, t)
		# el intacto hasta el impacto, el destruido desde el impacto (se esconde con escala 0)
		var imp: bool = t >= T_IMPACTO
		ok_car.scale = Vector3.ONE * 0.0005 if imp else Vector3.ONE; da_car.scale = Vector3.ONE if imp else Vector3.ONE * 0.0005
		_clave(p_ok, ok_car, t); _clave(p_da, da_car, t)
		for k in ruedas:
			var rodando := 1.0 if t < T_IMPACTO else (1.0 - _suave(T_IMPACTO, T_REPOSO, t))
			ang[k] += minf(st_vel[g] / 22.0, 1.0) * 0.26 * (1.0 if t < T_SKID else (0.55 if t < T_IMPACTO else rodando * 0.5))
			var w: Node3D = ruedas[k][0]
			w.transform.basis = Basis(ruedas[k][1], -ang[k])                       # sólo rotación sobre el centro de la rueda (sin movimiento de posición: no vibra)
			_clave(p_rued[k], w, t)
		var ia := 0
		for pv in limp_ok + limp_da:
			var bs := Basis(Quaternion(Vector3(0, 0, 1), Vector3(0, 0.80, -0.60).normalized()))
			var off := 0.0 if t < T_IMPACTO + 0.6 else 0.0
			pv.basis = bs * Basis(Vector3(0, 0, 1), Au.angulo_limpia(t) if t < T_REPOSO else 0.4); _clave(p_limp[ia], pv, t); ia += 1
		# conductor: manos al volante; sólo corrige el volante durante el derrape
		var steer := 0.015 * sin(t * 0.5) + (0.0 if t < T_SKID else -0.85 * _suave(T_SKID, T_SKID + 0.6, t) * (1.0 - 0.5 * _suave(T_IMPACTO, T_REPOSO, t)))
		var wc: Vector3 = inv_g * Vector3(0.36, 0.18, -0.20)
		var nrm: Vector3 = (inv_g.basis * Vector3(0, 0.25, 1)).normalized()
		var wX := Vector3.UP.cross(nrm).normalized(); var wY := nrm.cross(wX)
		var manos := []
		for par in [["Left", 2.5 + steer], ["Right", 0.64 + steer]]:
			var ph: float = par[1]
			var gp := wc + wX * cos(ph) * 0.19 + wY * sin(ph) * 0.19; var rr := (gp - wc).normalized()
			manos.append({"side": par[0], "wrist": gp + nrm * 0.075 + rr * 0.05, "fdir": (rr * -0.15 + nrm * -0.85).normalized(), "back": (rr * 0.9 + nrm * 0.25).normalized(), "pole": Vector3(0.55, -0.55, -0.30)})
		# inercia del cuerpo: aceleración del auto en su marco, filtrada (sólo choque/vuelco); en marcha normal casi nada
		var a_w := Vector3.ZERO
		if g > 1 and g < total - 1:
			a_w = (st_pos[g + 1] - 2.0 * st_pos[g] + st_pos[g - 1]) * FPS * FPS
		var a_loc := (carro.global_transform.basis.inverse() * a_w)
		acc_f = acc_f.lerp(a_loc, 0.18)
		var lat := clampf(-acc_f.x * 0.0035, -0.07, 0.07); var lon := clampf(-acc_f.z * 0.0030, -0.08, 0.08); var ver := clampf(-acc_f.y * 0.0015, -0.04, 0.04)
		var tras := _suave(T_IMPACTO, T_IMPACTO + 0.4, t)                    # después del golpe: aturdidos, la cabeza cae
		var sw := Vector3(0.002 * sin(t * 1.1), 0.003 * sin(t * 1.9), 0) + Vector3(lat, ver, lon)
		var hip := Vector3(0, 0.30, 0) + sw * 0.4
		RG.pose({"hips": hip, "head": hip + Vector3(sw.x * 1.6, 0.60 + sw.y, 0.03 + sw.z * 1.6 + 0.10 * tras), "roll": 0.02 + 0.5 * sw.x + 0.35 * tras, "look": 0.0, "look_y": -0.08 - 0.5 * tras, "hands": manos, "grip": 1.2 + 0.3 * _suave(T_SKID, T_SKID + 0.5, t),
			"feet": [{"side": "Left", "pos": Vector3(0.13, 0.13, 0.58)}, {"side": "Right", "pos": Vector3(-0.13, 0.13, 0.55)}]})
		RE.pose({"hips": hip, "head": hip + Vector3(sw.x * 1.6, 0.60 + sw.y, sw.z * 1.6 + 0.08 * tras), "roll": 0.5 * sw.x - 0.3 * tras, "look": 0.0, "look_y": -0.10 - 0.4 * tras, "grip": 0.9 + 0.4 * _suave(T_SKID, T_SKID + 0.5, t),
			"hands": [{"side": "Left", "wrist": Vector3(0.20, 0.42, 0.26), "fdir": Vector3(0, -0.25, 1).normalized(), "back": Vector3(0, 1, 0), "pole": Vector3(0.5, -0.6, -0.3)},
					  {"side": "Right", "wrist": Vector3(-0.18, 0.42, 0.28), "fdir": Vector3(0, -0.25, 1).normalized(), "back": Vector3(0, 1, 0), "pole": Vector3(0.5, -0.6, -0.3)}],
			"feet": [{"side": "Left", "pos": Vector3(0.13, 0.12, 0.55)}, {"side": "Right", "pos": Vector3(-0.13, 0.12, 0.55)}]})
		_elena_cuadro(g, t, p_enodo, RE)
		_puerta_cuadro(t, puerta_n, puerta_base, p_puerta)
		_gabriel_cuadro(g, t, p_g2, p_g_sc)
		for ac in [G, E, G2]:
			var d: Dictionary = p_sk[ac.id]
			for h in ac.sk.get_bone_count():
				anim.rotation_track_insert_key(d[h], t, ac.sk.get_bone_pose_rotation(h))
			anim.position_track_insert_key(d["pos"], t, ac.sk.get_bone_pose_position(ac.hueso_cadera))
		# cámaras
		for tm in tomas:
			var c: Camera3D = cams[tm["id"]]
			_poner_camara(tm, c, g, t, cam_p, cam_m)
			_clave(p_cam[tm["id"]], c, t, true)
	var lib := AnimationLibrary.new(); lib.add_animation("escena", anim); ap.add_animation_library("", lib); ap.assigned_animation = "escena"
	for tm in tomas:
		var tc: float = (float(tm["t0"]) + float(tm["t1"])) * 0.5
		(cams[tm["id"]] as Camera3D).current = true
		ap.seek(tc, true)
		for i in 4: await process_frame
		root.get_viewport().get_texture().get_image().save_png("%s_%s.png" % [prefijo, tm["id"]])
	if OS.get_cmdline_user_args().size() > 3 and OS.get_cmdline_user_args()[3] == "diag":
		var dc := Camera3D.new(); dc.name = "DIAG"; dc.fov = 50; dc.far = 800.0; esc.add_child(dc)
		var lado2 := DIR_SKID.rotated(Vector3.UP, PI * 0.5)
		dc.look_at_from_position(P_IMP + lado2 * 20.0 + DIR_SKID * -14.0 + Vector3(0, 16.0, 0), P_IMP + DIR_SKID * 4.0); dc.current = true
		var i := 0
		for td in [8.0, 8.8, 9.4, 10.0, 10.4, 10.9, 11.5, 12.2, 13.0, 14.0, 14.8, 16.0]:
			ap.seek(td, true)
			for q in 3: await process_frame
			root.get_viewport().get_texture().get_image().save_png("%s_diag%02d.png" % [prefijo, i]); i += 1
	if sin_glb:
		print("SIN_GLB"); quit(); return
	ap.seek(0.0, true)
	var doc := GLTFDocument.new(); var stt := GLTFState.new()
	doc.append_from_scene(esc, stt)
	print("GLB ", prefijo, ".glb err=", doc.write_to_filesystem(stt, prefijo + ".glb"))
	var cj := []
	for tm in tomas:
		cj.append({"id": tm["id"], "camara": tm["camara"], "inicio_s": tm["t0"], "fin_s": tm["t1"], "frame_inicio": int(tm["t0"] * FPS) + 1, "frame_fin": int(minf(tm["t1"] * FPS, total - 1)) + 1, "lente_mm": 12.0 / tan(deg_to_rad(tm["fov"]) / 2.0)})
	var js := {"formato": "estudio.previa_godot/1", "produccion": "p022_la_mujer_que_volvio", "escena_id": "accidente", "version": 1, "titulo": "El accidente", "fps": int(FPS), "frames": total, "duracion_s": float(total - 1) / FPS,
		"resolucion": [540, 960], "animacion": "escena", "actores": [{"id": "gabriel", "nodo": "gabriel", "modelo": "aiden"}, {"id": "elena", "nodo": "elena", "modelo": "kate"}, {"id": "gabriel_fuera", "nodo": "gabriel_fuera", "modelo": "aiden"}], "tomas": cj,
		"eventos": {"elena_despedida_s": T_EYECTA, "gabriel_sale_s": T_SALE, "desmayo_s": T_DESMAYO_REAL, "derrape_s": T_SKID, "impacto_s": T_IMPACTO, "vuelco_fin_s": T_ROLL_FIN, "reposo_s": T_REPOSO, "relampagos_s": [5.1, 11.6, 19.7], "balizas_desde_s": T_REPOSO,
			"punto_impacto": [P_IMP.x, P_IMP.y, P_IMP.z], "dir_deslizamiento": [DIR_SKID.x, DIR_SKID.y, DIR_SKID.z], "ruta_gabriel": RUTA_G.map(func(r): return {"clip": r["clip"], "t0": r["t0"], "dur": r["dur"], "p0": [r["p0"].x, r["p0"].z], "p1": [r["p1"].x, r["p1"].z]}), "auto_intacto": "AutoIntacto", "auto_destruido": "AutoDestruido", "se_cambia_en_s": T_IMPACTO},
		"charcos": CHARCOS_S.map(func(ss): var pp := centro(ss) + Vector3(-cos(rumbo(ss)), 0, sin(rumbo(ss))) * CARRIL; return {"s": ss, "x": pp.x, "z": pp.z, "yaw": rumbo(ss), "t_paso_s": (ss - 30.0) / V0}),
		"limpiaparabrisas": {"periodo_s": 1.4, "barrido_rad": 1.65}, "velocidad_ms": V0,
		"efectos_blender": ["lluvia real", "charcos con reflejos", "agua que levanta el auto al pisar charcos", "gotas en el parabrisas", "niebla", "relámpagos", "barniz negro brillante", "conos volumétricos de los faros", "chispas y vidrios al chocar", "polvo y barro", "humo del motor", "balizas"],
		"tiempo": {"pelicula": "t = (cuadro − 1) / fps"}}
	var fa := FileAccess.open(prefijo + ".json", FileAccess.WRITE); fa.store_string(JSON.stringify(js, "  ")); fa.close()
	quit()

# ───────── cámaras ─────────
func _punto(p) -> Vector3:
	if p is Array:
		return Vector3(p[0], p[1], p[2])
	var lado := DIR_SKID.rotated(Vector3.UP, PI * 0.5)                 # izquierda de la dirección del deslizamiento
	match String(p):
		"IMP_LADO": return P_IMP + lado * 7.5 + DIR_SKID * 2.0 + Vector3(0, 1.3, 0)
		"IMP_ACERC0": return P_IMP + lado * 13.0 + DIR_SKID * -6.0 + Vector3(0, 1.7, 0)
		"IMP_ACERC1": return P_IMP + lado * 4.8 + DIR_SKID * 1.5 + Vector3(0, 1.1, 0)
	return Vector3.ZERO

func _tomas() -> Array:
	return [
		{"id": "t1", "camara": "C1_exterior_seguimiento", "t0": 0.0, "t1": 3.4, "modo": "rel", "off": [-2.7, 0.15, -6.5], "off_fin": [-2.3, 0.30, -5.0], "mira": [0.0, 0.1, -1.2], "fov": 40.0},
		{"id": "t1b", "camara": "C1b_trasera_rocio", "t0": 3.4, "t1": 5.4, "modo": "rel", "off": [2.4, 0.05, 6.6], "off_fin": [1.7, 0.18, 4.9], "mira": [0.5, -0.45, 1.6], "fov": 42.0},
		{"id": "t2", "camara": "C2_interior_hombro", "t0": 5.4, "t1": 8.4, "modo": "rel", "off": [0.52, 0.52, 1.15], "off_fin": [0.46, 0.50, 0.95], "mira": [0.25, 0.22, -0.7], "fov": 58.0},
		{"id": "t3", "camara": "C3_lateral_curva", "t0": 8.4, "t1": 9.6, "modo": "fija", "pos": [6.0, 1.2, -160.0], "mira_seg": 0.9, "fov": 36.0},
		{"id": "t4", "camara": "C4_primera_persona", "t0": 9.6, "t1": 11.8, "modo": "pov", "fov": 70.0},
		{"id": "t5", "camara": "C5_rocas_vuelco", "t0": 11.8, "t1": 15.0, "modo": "fija", "pos": "IMP_LADO", "mira_seg": 0.8, "fov": 38.0},
		{"id": "t6", "camara": "C6_acercamiento_accidente", "t0": 15.0, "t1": 22.0, "modo": "fija_mov", "pos": "IMP_ACERC0", "pos_fin": "IMP_ACERC1", "mira_seg": 1.0, "fov": 34.0},
		{"id": "t7", "camara": "C7_busqueda_media", "t0": 22.0, "t1": T_DESMAYO_REAL - 16.0, "modo": "sigue_g", "base": "cabeza", "off": [4.2, -0.05, 5.2], "alt": -0.65, "fov": 36.0},
		{"id": "t8", "camara": "C8_rostro_sangre", "t0": T_DESMAYO_REAL - 16.0, "t1": T_DESMAYO_REAL - 4.5, "modo": "sigue_g", "base": "cabeza", "off": [0.9, -0.12, 1.45], "alt": 0.0, "fov": 30.0},
		{"id": "t9", "camara": "C9_desmayo", "t0": T_DESMAYO_REAL - 4.5, "t1": DUR, "modo": "sigue_g", "off": [3.4, 0.55, -3.2], "alt": 0.5, "fov": 34.0}]

func _poner_camara(tm: Dictionary, c: Camera3D, g: int, t: float, cp: Dictionary, cm: Dictionary) -> void:
	var u := clampf((t - tm["t0"]) / maxf(tm["t1"] - tm["t0"], 0.001), 0.0, 1.0); var e := smoothstep(0.0, 1.0, u)
	var cg: Transform3D = Transform3D(Basis.from_euler(Vector3(0, st_yaw[g], 0), EULER_ORDER_YXZ), st_pos[g])       # marco del auto sin cabeceo ni vuelco
	match tm["modo"]:
		"rel":
			var a: Array = tm["off"]; var b: Array = tm["off_fin"]
			c.global_position = cg * Vector3(a[0], a[1], a[2]).lerp(Vector3(b[0], b[1], b[2]), e)
			var m: Array = tm["mira"]
			c.look_at(cg * Vector3(m[0], m[1], m[2]), Vector3.UP)
			if tm["id"] == "t2":
				c.position += Vector3(sin(t * 0.7), sin(t * 0.9 + 1.0), 0) * 0.003
		"fija", "fija_mov":
			var pos := _punto(tm["pos"])
			if tm["modo"] == "fija_mov":
				pos = pos.lerp(_punto(tm["pos_fin"]), e)
			c.global_position = pos
			var objetivo: Vector3 = st_pos[g] + Vector3(0, 0.1, 0)
			var key: String = tm["id"]
			var prev: Vector3 = cm.get(key, objetivo)
			var s: float = (1.0 - exp(-4.0 / FPS * 2.0)) if g > int(tm["t0"] * FPS) else 1.0                          # suaviza el seguimiento: sin saltos
			prev = prev.lerp(objetivo, s) if cm.has(key) else objetivo
			cm[key] = prev
			c.look_at(prev, Vector3.UP)
		"sigue_g":
			var o: Array = tm["off"]
			var base_g: Vector3 = G2.raiz.global_position
			if tm.get("base", "") == "cabeza":
				base_g = G2.sk.global_transform * G2.sk.get_bone_global_pose(G2.cabeza).origin          # sigue la cabeza real (aunque esté agachado o arrodillado)
				base_g.y -= float(tm["alt"]) * 0.0
			var objetivo2: Vector3 = base_g + Vector3(o[0], o[1], o[2])
			var k2: String = tm["id"] + "_p"
			var pp: Vector3 = cm.get(k2, objetivo2)
			pp = pp.lerp(objetivo2, 0.14) if cm.has(k2) else objetivo2
			cm[k2] = pp
			c.global_position = pp
			var mir: Vector3 = base_g + Vector3(0, float(tm["alt"]), 0)
			var kk2: String = tm["id"] + "_m"
			var mm: Vector3 = cm.get(kk2, mir)
			mm = mm.lerp(mir, 0.40) if cm.has(kk2) else mir
			cm[kk2] = mm
			c.look_at(mm, Vector3.UP)
		"pov":
			var cabeza: Vector3 = G.raiz.global_transform * Vector3(0.0, 0.98, 0.24)                     # ojos de Gabriel
			c.global_position = cabeza
			var fw: Vector3 = (carro.global_transform.basis * Vector3(0, 0.03, -1)).normalized()
			var arriba: Vector3 = carro.global_transform.basis * Vector3.UP
			c.look_at(cabeza + fw, arriba)

# ───────── Elena despedida, puerta, Gabriel que sale y busca ─────────
func _yaw_a(a: Vector3, b: Vector3) -> float:
	return atan2(b.x - a.x, b.z - a.z)

func _ruta_gabriel() -> void:
	var W: Vector3 = st_pos[st_pos.size() - 1]; W.y = 0.0
	var cb := Basis.from_euler(Vector3(st_pit[st_pit.size() - 1], st_yaw[st_yaw.size() - 1], st_rol[st_rol.size() - 1]), EULER_ORDER_YXZ)
	var der: Vector3 = (cb * Vector3.RIGHT); der.y = 0.0; der = der.normalized()
	var puerta := W + der * 1.35
	var d := DIR_SKID; var l := d.rotated(Vector3.UP, PI * 0.5)
	var A := P_IMP + d * 6.6 + l * 4.4; var B := P_IMP + d * 10.4 + l * 3.4; var C := P_IMP + d * 9.4 + l * -2.8; var D := P_IMP + d * 7.8 + l * -0.6
	# [clip, modo, duración (s; 0 = según distancia), destino de la caminata, hacia dónde mira]
	var seq := [["exit_car", "clip", 175.0 / FPS, puerta, A], ["look_around2", "quieto", 3.4, null, A], ["inj_walk", "ruta", 0.0, A, null], ["calling", "quieto", 2.7, null, B], ["nerv_look", "quieto", 2.6, null, B],
		["sad_walk", "ruta", 0.0, B, null], ["look_down", "quieto", 3.6, null, B], ["sad_walk", "ruta", 0.0, C, null], ["calling", "quieto", 2.7, null, C], ["inj_walk", "ruta", 0.0, D, null],
		["dizzy", "quieto", 2.4, null, D], ["kneel_down", "quieto", 84.0 / FPS, null, D], ["fall_fwd", "quieto", 78.0 / FPS, null, D]]
	RUTA_G = []
	var t := T_SALE; var pos := puerta
	for sg in seq:
		var modo: String = sg[1]; var dur: float = sg[2]
		var p1 := pos; var yaw := _yaw_a(pos, sg[4]) if sg[4] != null else _yaw_cur
		if modo == "ruta":
			p1 = sg[3]; yaw = _yaw_a(pos, p1); dur = maxf(pos.distance_to(p1) / 0.85, 1.0)
		elif modo == "clip":
			p1 = pos + Basis(Vector3.UP, yaw) * Vector3(0.0, 0.0, 1.9)
		if sg[4] != null and modo == "quieto":
			yaw = _yaw_a(pos, sg[4]) if pos.distance_to(sg[4]) > 0.5 else _yaw_cur
		_yaw_cur = yaw
		RUTA_G.append({"clip": sg[0], "modo": modo, "t0": t, "dur": dur, "p0": pos, "p1": p1, "yaw0": yaw, "obj": sg[4]})
		t += dur; pos = p1
	T_DESMAYO_REAL = RUTA_G[RUTA_G.size() - 1]["t0"]
	DUR = t + 3.2
	total = int(ceil(DUR * FPS)) + 1
	anim.length = float(total - 1) / FPS

func _puerta_conductor() -> Node3D:
	for nm in ["dver L", "Dver R"]:
		var n := da_car.find_child(nm, true, false) as MeshInstance3D
		var c := (da_car.global_transform.affine_inverse() * (n.global_transform * n.get_aabb().get_center())).x
		if c > 0.0: return n
	return da_car.find_child("Dver R", true, false) as Node3D

func _puerta_cuadro(t: float, n: Node3D, base: Transform3D, pt: Array) -> void:
	var ang := deg_to_rad(68.0) * _suave(T_SALE - 1.2, T_SALE - 0.2, t)
	var pivote := Vector3(0.76, 0.0, -0.60)
	var m := Transform3D(Basis.IDENTITY, pivote) * Transform3D(Basis(Vector3.UP, ang), Vector3.ZERO) * Transform3D(Basis.IDENTITY, -pivote)
	n.global_transform = da_car.global_transform * m * base
	_clave(pt, n, t)

func _elena_cuadro(g: int, t: float, pt: Array, rig: RigSentado) -> void:
	if t < T_EYECTA:
		ELENA_N.global_transform = carro.global_transform * Transform3D(Basis.IDENTITY, Vector3(-0.36, PISO + 0.30, 0.20))
		ELENA_N.scale = Vector3.ONE
	else:
		if t < T_EYECTA + 1.0 / FPS:
			elena_p = ELENA_N.global_position
			elena_v = DIR_SKID * 12.5 + Vector3(0, 3.6, 0) + DIR_SKID.rotated(Vector3.UP, PI * 0.5) * 1.6
		elena_v.y -= 9.8 / FPS
		elena_p += elena_v / FPS
		var d_ref: float = (elena_p - P_IMP).dot(DIR_SKID)
		if elena_p.y < 0.35 and d_ref < 12.6 and elena_v.y < 0.0:
			elena_p.y = 0.35; elena_v.y *= -0.22; elena_v.x *= 0.86; elena_v.z *= 0.86
		var tr := t - T_EYECTA
		var giro := Basis.from_euler(Vector3(2.4 * tr, 0.9 * tr, 1.5 * tr))
		if E.clips.has("fly_back"):
			E.poner_pose(E.pose_clip("fly_back", int(tr * FPS), false))
		ELENA_N.global_transform = Transform3D(giro, elena_p)
		ELENA_N.scale = Vector3.ONE if elena_p.y > -26.0 else Vector3.ONE * 0.0005
	if t >= T_EYECTA and int(round(t * 10.0)) % 5 == 0 and g % 3 == 0 and t < 15.0:
		print("ELENA t=", snappedf(t, 0.1), " a lo largo ", snappedf((ELENA_N.global_position - P_IMP).dot(DIR_SKID), 0.1), " altura ", snappedf(ELENA_N.global_position.y, 0.1))
	_clave(pt, ELENA_N, t)

func _gabriel_cuadro(g: int, t: float, pt: Array, pt_sc: Array) -> void:
	var fuera := t >= T_SALE
	G.raiz.scale = Vector3.ONE * 0.0005 if fuera else Vector3.ONE
	G2.raiz.scale = Vector3.ONE if fuera else Vector3.ONE * 0.0005
	_clave(pt_sc, G.raiz, t)
	if not fuera:
		G2.poner_pose(G2.pose_clip("idle", 0, true))
		G2.raiz.position = Vector3(0, -5.0, 0); _clave(pt, G2.raiz, t); return
	var sg: Dictionary = RUTA_G[RUTA_G.size() - 1]
	for s in RUTA_G:
		if t < float(s["t0"]) + float(s["dur"]):
			sg = s; break
	var k := int((t - float(sg["t0"])) * FPS)
	var clip: String = sg["clip"]
	var rep := (clip in ["inj_walk", "sad_walk", "look_around2", "nerv_look", "dizzy"])
	var pose := G2.pose_clip(clip, int(k * (0.8 if clip == "inj_walk" else 1.0)), rep)
	# fundido de 9 cuadros desde la pose anterior
	var u := clampf((t - float(sg["t0"])) / 0.30, 0.0, 1.0)
	if _pose_ant.size() > 0 and u < 1.0:
		pose = Actor3.mezcla(_pose_ant, pose, smoothstep(0.0, 1.0, u))
	G2.poner_pose(pose); _pose_ant = pose
	var uu := clampf((t - float(sg["t0"])) / maxf(float(sg["dur"]), 0.001), 0.0, 1.0)
	var pos: Vector3
	var yaw: float = float(sg["yaw0"])
	if sg["modo"] == "clip":
		var rc := G2.raiz_clip("exit_car", mini(k, 174))
		pos = (sg["p0"] as Vector3) + Basis(Vector3.UP, yaw) * Vector3(rc.x, 0.0, rc.y)
	elif sg["modo"] == "ruta":
		pos = (sg["p0"] as Vector3).lerp(sg["p1"], uu)
	else:
		pos = sg["p0"]
	_yaw_cur = lerp_angle(_yaw_cur, yaw, 0.10) if t > T_SALE + 0.2 else yaw
	G2.raiz.position = Vector3(pos.x, 0.0, pos.z)
	G2.raiz.rotation.y = _yaw_cur
	_clave(pt, G2.raiz, t)

var _pose_ant: Dictionary = {}
var _yaw_cur := 0.0
var T_DESMAYO_REAL := 40.0

func _initialize() -> void:
	var a := OS.get_cmdline_user_args()
	if a.size() > 1 and a[1].is_valid_float():
		DUR = float(a[1])
	_montar(a[0], a.size() > 2 and a[2] == "sin_glb")
