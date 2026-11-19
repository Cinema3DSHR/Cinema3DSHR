## ETAPA 4 — Efectos preliminares en Godot (partículas GPU: NO viajan en el GLB; quedan como nodos vacíos con su
## nombre y posición, que Blender usa de marcadores): lluvia fuerte (choca con la camioneta y el piso), fuego, brasas y
## humo del hogar.
class_name E4Efectos
extends RefCounted

static func _mat_part(color: Color, aditivo: bool, alfa: float) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.vertex_color_use_as_albedo = true
	m.albedo_color = Color(color, alfa)
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	if aditivo:
		m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	return m

static func _particulas(padre: Node3D, nombre: String, pos: Vector3, cantidad: int, vida: float, proc: ParticleProcessMaterial, malla: Mesh) -> GPUParticles3D:
	var p := GPUParticles3D.new()
	p.name = nombre
	p.position = pos
	p.amount = cantidad
	p.lifetime = vida
	p.preprocess = vida * 2.0
	p.process_material = proc
	p.draw_pass_1 = malla
	p.visibility_aabb = AABB(Vector3(-20, -15, -20), Vector3(40, 30, 40))
	padre.add_child(p)
	return p

static func _rampa(colores: Array) -> GradientTexture1D:
	var g := Gradient.new()
	g.offsets = PackedFloat32Array(colores.map(func(c): return c[0]))
	g.colors = PackedColorArray(colores.map(func(c): return c[1]))
	var t := GradientTexture1D.new()
	t.gradient = g
	return t

static func _curva(puntos: Array) -> CurveTexture:
	var c := Curve.new()
	for p in puntos:
		c.add_point(Vector2(p[0], p[1]))
	var t := CurveTexture.new()
	t.curve = c
	return t

static func crear(raiz: Node3D) -> void:
	var g := Kit.grupo(raiz, "Efectos")
	# LLUVIA: gotas alargadas alineadas con la velocidad, viento leve; cubre la calle, la vereda y la camioneta
	var pl := ParticleProcessMaterial.new()
	pl.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	pl.emission_box_extents = Vector3(16, 0.5, 11)
	pl.direction = Vector3(0.12, -1, 0)
	pl.spread = 3.0
	pl.initial_velocity_min = 11.0
	pl.initial_velocity_max = 14.0
	pl.gravity = Vector3(0, -9.8, 0)
	pl.particle_flag_align_y = true
	pl.collision_mode = ParticleProcessMaterial.COLLISION_HIDE_ON_CONTACT
	var gota := BoxMesh.new()
	gota.size = Vector3(0.008, 0.45, 0.008)
	gota.material = _mat_part(Color(0.75, 0.82, 0.95), false, 0.45)
	_particulas(g, "FX_lluvia", Vector3(-2.5, 11.0, -15.0), 9000, 1.1, pl, gota)
	# superficies donde choca la lluvia: la camioneta (techo, caja y capó) y el piso
	var cc := GPUParticlesCollisionBox3D.new()
	cc.name = "Colision_lluvia_camioneta"
	cc.size = Vector3(2.0, 1.75, 5.0)
	cc.position = E1Geometria.AUTO_POS + Vector3(0, 0.9, 0.25)
	g.add_child(cc)
	var cp := GPUParticlesCollisionBox3D.new()
	cp.name = "Colision_lluvia_piso"
	cp.size = Vector3(80, 1.0, 40)
	cp.position = Vector3(-2, -0.75, -24)
	g.add_child(cp)
	var ct := GPUParticlesCollisionBox3D.new()
	ct.name = "Colision_lluvia_techo_casa"
	ct.size = Vector3(24, 1.0, 8.6)
	ct.position = Vector3(0.5, 3.4, 0)
	g.add_child(ct)
	# FUEGO del hogar: lenguas que suben y se achican, de amarillo a rojo
	var base := Vector3(-8.6, 0.0, -3.9)
	var pf := ParticleProcessMaterial.new()
	pf.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	pf.emission_box_extents = Vector3(0.32, 0.03, 0.1)
	pf.direction = Vector3.UP
	pf.spread = 12.0
	pf.initial_velocity_min = 0.5
	pf.initial_velocity_max = 0.9
	pf.gravity = Vector3(0, 0.8, 0)
	pf.scale_min = 0.6
	pf.scale_max = 1.1
	pf.scale_curve = _curva([[0.0, 0.7], [0.3, 1.0], [1.0, 0.1]])
	pf.color_ramp = _rampa([[0.0, Color(1.0, 0.8, 0.35, 0.55)], [0.4, Color(1.0, 0.42, 0.08, 0.45)], [1.0, Color(0.6, 0.08, 0.02, 0.0)]])
	pf.turbulence_enabled = true
	pf.turbulence_noise_strength = 0.4
	var llama := QuadMesh.new()
	llama.size = Vector2(0.22, 0.32)
	var ml := _mat_part(Color.WHITE, true, 1.0)
	ml.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	llama.material = ml
	_particulas(g, "FX_fuego", base + Vector3(0, 0.3, 0.32), 80, 0.7, pf, llama)
	# BRASAS: chispas chicas que suben lento y se apagan
	var pb := ParticleProcessMaterial.new()
	pb.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	pb.emission_box_extents = Vector3(0.3, 0.02, 0.1)
	pb.direction = Vector3.UP
	pb.spread = 25.0
	pb.initial_velocity_min = 0.4
	pb.initial_velocity_max = 0.9
	pb.gravity = Vector3(0, 0.15, 0)
	pb.turbulence_enabled = true
	pb.turbulence_noise_strength = 1.2
	pb.color_ramp = _rampa([[0.0, Color(1.0, 0.7, 0.3, 1.0)], [0.7, Color(1.0, 0.3, 0.05, 0.9)], [1.0, Color(0.5, 0.05, 0.0, 0.0)]])
	var chispa := QuadMesh.new()
	chispa.size = Vector2(0.018, 0.018)
	var mc := _mat_part(Color.WHITE, true, 1.0)
	mc.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	chispa.material = mc
	_particulas(g, "FX_brasas", base + Vector3(0, 0.25, 0.3), 45, 2.2, pb, chispa)
	# HUMO: sube por el tiro de la chimenea, gris, se agranda y se desvanece
	var ph := ParticleProcessMaterial.new()
	ph.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	ph.emission_box_extents = Vector3(0.25, 0.05, 0.08)
	ph.direction = Vector3.UP
	ph.spread = 10.0
	ph.initial_velocity_min = 0.25
	ph.initial_velocity_max = 0.4
	ph.gravity = Vector3(0, 0.1, -0.05)
	ph.scale_curve = _curva([[0.0, 0.4], [1.0, 1.0]])
	ph.color_ramp = _rampa([[0.0, Color(0.35, 0.33, 0.32, 0.0)], [0.2, Color(0.35, 0.33, 0.32, 0.35)], [1.0, Color(0.45, 0.45, 0.45, 0.0)]])
	ph.turbulence_enabled = true
	ph.turbulence_noise_strength = 0.3
	var bocanada := QuadMesh.new()
	bocanada.size = Vector2(0.45, 0.45)
	var mh := _mat_part(Color.WHITE, false, 1.0)
	mh.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	bocanada.material = mh
	_particulas(g, "FX_humo", base + Vector3(0, 0.75, 0.2), 40, 2.8, ph, bocanada)
