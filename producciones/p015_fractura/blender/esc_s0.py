"""s0 «Ojo» (0–180): macro del ojo de Aiden; los párpados se abren, en la córnea se refleja una explosión y la cámara entra por la pupila."""
import math
import bpy
from mathutils import Vector
import lib
from lib import *
import marco


def mat_ojo(nombre):
    """Esclerótica + iris con fibras + pupila que se dilata. Coordenadas de objeto: el ojo mira hacia −Y."""
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    M = lambda op, a=None, c=None: _m(nt, op, a, c)
    # radio frontal normalizado r = sqrt(x²+z²)/R  (R=1)
    x2 = M("MULTIPLY", sep.outputs["X"], sep.outputs["X"])
    z2 = M("MULTIPLY", sep.outputs["Z"], sep.outputs["Z"])
    r = M("SQRT", M("ADD", x2, z2))
    ang = M("ARCTAN2", sep.outputs["X"], sep.outputs["Z"])
    # fibras: ruido a lo largo del ángulo
    vc = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(M("MULTIPLY", ang, 3.0), vc.inputs["X"])
    nt.links.new(M("MULTIPLY", r, 7.0), vc.inputs["Y"])
    ru = nt.nodes.new("ShaderNodeTexNoise")
    ru.inputs["Scale"].default_value = 3.5
    ru.inputs["Detail"].default_value = 10.0
    ru.inputs["Roughness"].default_value = 0.7
    nt.links.new(vc.outputs[0], ru.inputs["Vector"])
    # rampa del iris: del borde de la pupila al limbo
    rp = nt.nodes.new("ShaderNodeValToRGB")
    cr = rp.color_ramp
    cr.elements[0].position = 0.0
    cr.elements[0].color = (0.02, 0.05, 0.06, 1)
    e1 = cr.elements.new(0.45)
    e1.color = (0.05, 0.28, 0.24, 1)
    cr.elements[-1].position = 1.0
    cr.elements[-1].color = (0.30, 0.38, 0.12, 1)
    nt.links.new(M("ADD", M("MULTIPLY", ru.outputs["Fac"], 0.7), M("MULTIPLY", r, 1.2)), rp.inputs["Fac"])
    # esclerótica con venas rojas suaves
    vn = nt.nodes.new("ShaderNodeTexNoise")
    vn.inputs["Scale"].default_value = 9.0
    vn.inputs["Detail"].default_value = 12.0
    nt.links.new(tc.outputs["Object"], vn.inputs["Vector"])
    vr = nt.nodes.new("ShaderNodeValToRGB")
    vr.color_ramp.elements[0].position = 0.55
    vr.color_ramp.elements[0].color = (0.92, 0.88, 0.84, 1)
    vr.color_ramp.elements[1].position = 0.75
    vr.color_ramp.elements[1].color = (0.75, 0.25, 0.22, 1)
    nt.links.new(vn.outputs["Fac"], vr.inputs["Fac"])
    # máscaras: pupila (r<rp), iris (r<0.44) y sólo hemisferio frontal (y<0)
    pup = nt.nodes.new("ShaderNodeValue")
    pup.outputs[0].default_value = 0.17
    es_pupila = M("LESS_THAN", r, pup.outputs[0])
    frente = M("LESS_THAN", sep.outputs["Y"], 0.0)
    es_iris = M("MULTIPLY", M("LESS_THAN", r, 0.46), frente)
    mix1 = nt.nodes.new("ShaderNodeMix")
    mix1.data_type = "RGBA"
    nt.links.new(es_iris, mix1.inputs["Factor"])
    nt.links.new(vr.outputs["Color"], mix1.inputs["A"])
    nt.links.new(rp.outputs["Color"], mix1.inputs["B"])
    mix2 = nt.nodes.new("ShaderNodeMix")
    mix2.data_type = "RGBA"
    nt.links.new(M("MULTIPLY", es_pupila, frente), mix2.inputs["Factor"])
    nt.links.new(mix1.outputs["Result"], mix2.inputs["A"])
    mix2.inputs["B"].default_value = (0.0, 0.0, 0.0, 1)
    nt.links.new(mix2.outputs["Result"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.25
    b.inputs["Specular IOR Level"].default_value = 0.6
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    return m, pup.outputs[0]


def _m(nt, op, a, c):
    n = nt.nodes.new("ShaderNodeMath")
    n.operation = op
    for i, v in ((0, a), (1, c)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = float(v)
        else:
            nt.links.new(v, n.inputs[i])
    return n.outputs[0]


def construir(ctx, i, f0, f1):
    col = coleccion("S0_Ojo")
    O = Vector(ctx.desp(i))
    R = 1.0
    m_ojo, pupila = mat_ojo("ojo_aiden")
    globo = esfera("globo", O, R, col, m_ojo, 96, 64)
    m_cor = mat_vidrio("cornea", (1, 1, 1), 0.0, 1.38)
    cornea = esfera("cornea", O + Vector((0, -0.04, 0)), R * 1.03, col, m_cor, 96, 64, esc=(1, 1.06, 1))
    piel = mat("piel_aiden", (0.55, 0.33, 0.26), rug=0.45)
    b = piel.node_tree.nodes["Principled BSDF"]
    b.inputs["Subsurface Weight"].default_value = 0.3
    b.inputs["Subsurface Radius"].default_value = (0.9, 0.35, 0.2)
    pr = bpy.data.node_groups  # sin uso
    # párpados: hemisferios que giran sobre el eje X del globo
    lids = []
    for nom, signo in (("sup", 1), ("inf", -1)):
        bm = bmesh_hemis(R * 1.09, signo)
        me = bpy.data.meshes.new("lid_" + nom)
        bm.to_mesh(me)
        bm.free()
        o = bpy.data.objects.new("lid_" + nom, me)
        col.objects.link(o)
        o.location = O
        me.materials.append(piel)
        for p in me.polygons:
            p.use_smooth = True
        sol = o.modifiers.new("grosor", "SOLIDIFY")
        sol.thickness = 0.08
        lids.append(o)
    sup, inf = lids
    # pestañas
    pest = mat("pestana", (0.02, 0.015, 0.015), rug=0.6)
    r_ = random.Random(5)
    for k in range(70):
        a = math.radians(-80 + 160 * k / 69.0)
        base = Vector((math.sin(a) * R * 1.09, -math.cos(a) * R * 1.09, 0))
        for lid, sg in ((sup, 1), (inf, -1)):
            L = r_.uniform(0.12, 0.34) * (1.0 if sg > 0 else 0.55)
            cn = cilindro(f"pe_{lid.name}_{k}", (0, 0, 0), 0.007, L, col, pest, seg=5, suave=False)
            d = Vector((math.sin(a) * 0.4, -math.cos(a) * 0.5, sg * 0.8)).normalized()
            cn.parent = lid
            cn.location = base + d * L * 0.5
            cn.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    # luces y reflejos en la córnea: la explosión (naranja) a la izquierda y un filo frío a la derecha
    fuego = mat_emisivo("fuego_refl", (1.0, 0.42, 0.08), 9.0)
    for k, (x, y, z, s) in enumerate([(-3.6, -5.0, 2.0, 1.3), (-4.2, -4.0, -0.9, 0.8), (-2.2, -6.0, 3.6, 0.55)]):
        e = esfera(f"refl_fuego_{k}", O + Vector((x, y, z)), s, col, fuego, 16, 10)
        e.visible_shadow = False
        for f in range(f0, f1, 3):
            e.scale = tuple(v * (0.82 + 0.3 * math.sin(f * 0.7 + k * 2.1) * math.sin(f * 0.31 + k)) for v in (1, 1, 1))
            e.keyframe_insert("scale", frame=f)
    anillo = mat_emisivo("anillo_refl", (0.45, 0.7, 1.0), 6.0)
    toro("anillo_refl", O + Vector((6, -10, 2)), 3.6, 0.22, col, anillo, rot=(math.radians(80), 0, math.radians(20)))
    sol_ = bpy.data.lights.new("sol_ojo", "AREA")
    sol_.energy = 500.0
    sol_.shape = "RECTANGLE"
    sol_.size, sol_.size_y = 5.0, 3.0
    sol_.color = (1.0, 0.55, 0.25)
    lo = bpy.data.objects.new("luz_naranja", sol_)
    col.objects.link(lo)
    lo.location = O + Vector((-6, -7, 2))
    lo.rotation_euler = Vector((O + Vector((0, 0, 0)) - lo.location)).to_track_quat("-Z", "Y").to_euler()
    fr = bpy.data.lights.new("filo_ojo", "AREA")
    fr.energy = 300.0
    fr.color = (0.5, 0.75, 1.0)
    fr.size = 4.0
    lf = bpy.data.objects.new("luz_fria", fr)
    col.objects.link(lf)
    lf.location = O + Vector((6, -5, 3))
    lf.rotation_euler = Vector((O - lf.location)).to_track_quat("-Z", "Y").to_euler()
    # animación: párpados (cerrado → abierto), latido, pupila
    def ang_sup(f):
        u = suave((f - 45) / 50.0)
        return math.radians(lerp(0, -38, u)) + (math.radians(-3) * math.sin(f * 0.9) * suave((f - 95) / 20.0))
    for f in range(f0, f1 + 1, 2):
        sup.rotation_euler = (ang_sup(f), 0, 0)
        sup.keyframe_insert("rotation_euler", frame=f)
        u = suave((f - 55) / 45.0)
        inf.rotation_euler = (math.radians(lerp(0, 14, u)), 0, 0)
        inf.keyframe_insert("rotation_euler", frame=f)
        pupila.default_value = 0.17
    # pupila: se dilata al final
    for f, v in ((f0, 0.14), (100, 0.16), (150, 0.12), (175, 0.2)):
        pupila.default_value = v
        pupila.keyframe_insert("default_value", frame=f)
    # cámara: macro 100 mm, empuja hacia la pupila
    cam = Camara("cam_ojo", col, lente=62.0)
    cam.claves(f0, f1,
               lambda f: O + Vector((lerp(0.7, 0.0, suave((f - 60) / 110.0)), lerp(-7.0, -1.35, suave((f - 40) / 135.0) ** 1.4), lerp(0.25, 0.0, suave((f - 60) / 110.0)))),
               lambda f: O + Vector((0, 0, 0)),
               flente=lambda f: lerp(62.0, 38.0, suave((f - 110) / 70.0)),
               fdof=lambda f: ((O + Vector((0, -1.0, 0)) - (O + Vector((lerp(0.7, 0.0, suave((f - 60) / 110.0)), lerp(-7.0, -1.35, suave((f - 40) / 135.0) ** 1.4), 0)))).length, 2.8))
    v = ctx.dir.corte(f0, cam)
    v.rampa(f0, f0 + 20, 1.0, 0.0, (0, 0, 0))
    v.rampa(f1 - 14, f1, 0.0, 1.0, (0, 0, 0))
    ctx.escena_activa(col, f0, f1)
    return cam


def bmesh_hemis(radio, signo):
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=64, v_segments=32, radius=radio)
    borrar = [v for v in bm.verts if v.co.z * signo < -1e-4]
    bmesh.ops.delete(bm, geom=borrar, context="VERTS")
    return bm


import random
