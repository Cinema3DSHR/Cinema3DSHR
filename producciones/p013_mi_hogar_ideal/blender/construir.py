"""p013 «Mi hogar ideal» · etapa de Blender: importa el GLB de Godot y hace TODA la terminación artística.
Uso: /opt/tools/blendenv/bin/python construir.py <glb_godot> <salida.blend>
Cielo y luces del día→atardecer→noche, vidrios, pasto, árboles con copa, autos livianos, fuego de la chimenea con chispas,
neblina volumétrica, luces del jardín que se encienden al anochecer y ajustes de Cycles. Todo en código: reproducible."""
import sys
import math
import random
import re
import bpy
import bmesh
from mathutils import Vector, noise

GLB = sys.argv[sys.argv.index("--") + 1]
SALIDA = sys.argv[sys.argv.index("--") + 2]
FPS = 30
SEMILLA = 1313
RES = (720, 1280)          # Reel vertical 9:16 (misma cantidad de píxeles que 1280×720)
ESCALA_T = 30.0 / 24.0     # el GLB trae la animación en cuadros de 24 fps; el proyecto es de 30 fps


BRUMA = []


def f(t):
    return t * FPS


# ───────────────────────────────────────────── utilidades de materiales
def principled(m):
    return next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)


def nuevo_material(nombre):
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    return m, nt


def ruido(nt, escala, detalle=4.0, rug=0.5, w=None):
    r = nt.nodes.new("ShaderNodeTexNoise")
    r.inputs["Scale"].default_value = escala
    r.inputs["Detail"].default_value = detalle
    r.inputs["Roughness"].default_value = rug
    return r


# ───────────────────────────────────────────── tiempo: el GLB viene a 24 fps
def reescalar_tiempo():
    for act in bpy.data.actions:
        for capa in act.layers:
            for tira in capa.strips:
                for cb in tira.channelbags:
                    for fc in cb.fcurves:
                        for kp in fc.keyframe_points:
                            kp.co.x *= ESCALA_T
                            kp.handle_left.x *= ESCALA_T
                            kp.handle_right.x *= ESCALA_T
                        fc.update()


# ───────────────────────────────────────────── autos: se aligeran (el modelo del juego tiene 500 mil–1 millón de triángulos)
def aligerar_autos():
    ratios = {"carroceria": 0.12}
    hechos = {}
    for o in list(bpy.data.objects):
        if o.type != "MESH" or not re.match(r"^geometry", o.name):
            continue
        cadena = []
        p = o
        while p:
            cadena.append(p.name)
            p = p.parent
        if not any(c.startswith("carroceria") for c in cadena):
            continue
        antes = len(o.data.polygons)
        mod = o.modifiers.new("Aligerar", "DECIMATE")
        mod.decimate_type = "COLLAPSE"
        mod.ratio = max(0.04, min(0.2, 90000.0 / antes))
        mod.use_collapse_triangulate = True
        with bpy.context.temp_override(object=o, active_object=o, selected_objects=[o]):
            bpy.ops.object.modifier_apply(modifier=mod.name)
        hechos[o.name] = (antes, len(o.data.polygons))
    return hechos


def pintura_autos():
    """Barniz sobre las carrocerías de los autos y vidrios oscuros (lo que trae el modelo)."""
    n = 0
    for m in bpy.data.materials:
        if m.name in ("material_02", "material_03", "material_04") and m.use_nodes:
            b = principled(m)
            b.inputs["Coat Weight"].default_value = 0.7
            b.inputs["Coat Roughness"].default_value = 0.08
            b.inputs["Roughness"].default_value = 0.38
            b.inputs["Metallic"].default_value = 0.25
            n += 1
    for nombre, (rug, met) in {"goma": (0.8, 0.0), "flanco": (0.85, 0.0), "llanta": (0.25, 0.9), "acero_rueda": (0.25, 1.0)}.items():
        for m in bpy.data.materials:
            if m.use_nodes and (m.name == nombre or re.match(rf"^{nombre}\d*$", m.name)):
                b = principled(m)
                b.inputs["Roughness"].default_value = rug
                b.inputs["Metallic"].default_value = met
    return n


# ───────────────────────────────────────────── materiales de la casa y el terreno
def vidrio_real():
    """Vidrio de ventanas y puertas: refracción para los reflejos, transparente para las sombras (entra la luz del sol)."""
    cuenta = 0
    for m in bpy.data.materials:
        if m.name not in ("vidrio", "glass", "glass2", "glass3", "Glass2", "Glass3") or not m.use_nodes:
            continue
        nt = m.node_tree
        for n in list(nt.nodes):
            nt.nodes.remove(n)
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        vid = nt.nodes.new("ShaderNodeBsdfGlass")
        vid.inputs["Color"].default_value = (0.82, 0.92, 0.95, 1.0) if m.name == "vidrio" else (0.7, 0.75, 0.78, 1.0)
        vid.inputs["Roughness"].default_value = 0.02
        vid.inputs["IOR"].default_value = 1.45
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        lp = nt.nodes.new("ShaderNodeLightPath")
        mez = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(lp.outputs["Is Shadow Ray"], mez.inputs["Fac"])
        nt.links.new(vid.outputs[0], mez.inputs[1])
        nt.links.new(tr.outputs[0], mez.inputs[2])
        nt.links.new(mez.outputs[0], out.inputs["Surface"])
        cuenta += 1
    return cuenta


def pasto():
    """Césped y colinas: dos verdes con ruido a gran escala y un relieve fino; sin neón."""
    for nombre, (c1, c2, esc) in {"cesped": ((0.035, 0.1, 0.015, 1), (0.07, 0.15, 0.03, 1), 0.55),
                                  "colina": ((0.03, 0.075, 0.015, 1), (0.055, 0.11, 0.025, 1), 0.08)}.items():
        m = bpy.data.materials.get(nombre)
        if not m:
            continue
        nt = m.node_tree
        for n in list(nt.nodes):
            nt.nodes.remove(n)
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        b = nt.nodes.new("ShaderNodeBsdfPrincipled")
        tc = nt.nodes.new("ShaderNodeTexCoord")
        r1 = ruido(nt, esc, 5.0, 0.55)
        r2 = ruido(nt, esc * 14, 3.0, 0.5)
        nt.links.new(tc.outputs["Object"], r1.inputs["Vector"])
        nt.links.new(tc.outputs["Object"], r2.inputs["Vector"])
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.inputs["A"].default_value = c1
        mix.inputs["B"].default_value = c2
        nt.links.new(r1.outputs["Fac"], mix.inputs["Factor"])
        # variación fina (manchas)
        mix2 = nt.nodes.new("ShaderNodeMix")
        mix2.data_type = "RGBA"
        mix2.blend_type = "MULTIPLY"
        mix2.inputs["Factor"].default_value = 0.35
        mix2.inputs["B"].default_value = (0.7, 0.8, 0.5, 1)
        nt.links.new(mix.outputs["Result"], mix2.inputs["A"])
        nt.links.new(r2.outputs["Fac"], mix2.inputs["Factor"])
        nt.links.new(mix2.outputs["Result"], b.inputs["Base Color"])
        b.inputs["Roughness"].default_value = 0.92
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.6
        bump.inputs["Distance"].default_value = 0.05
        r3 = ruido(nt, 120.0, 2.0, 0.6)
        nt.links.new(tc.outputs["Object"], r3.inputs["Vector"])
        nt.links.new(r3.outputs["Fac"], bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
        nt.links.new(b.outputs[0], out.inputs["Surface"])


def superficies():
    """Asfalto, vereda, estuco, piedra: rugosidad y relieve. Metales y espejo."""
    tc_map = {}
    for m in bpy.data.materials:
        if not m.use_nodes:
            continue
        b = principled(m)
        if not b:
            continue
        n = m.name
        if n == "asfalto":
            b.inputs["Base Color"].default_value = (0.035, 0.035, 0.04, 1)
            b.inputs["Roughness"].default_value = 0.86
        elif n in ("estuco", "estuco_int"):
            b.inputs["Roughness"].default_value = 0.9
        elif n in ("piedra", "hormigon", "hormigon_piso", "vereda", "piso_piedra"):
            b.inputs["Roughness"].default_value = 0.88
        elif n == "piso_madera":
            b.inputs["Base Color"].default_value = (0.2, 0.115, 0.06, 1)
            b.inputs["Roughness"].default_value = 0.5
            b.inputs["Coat Weight"].default_value = 0.12
            b.inputs["Coat Roughness"].default_value = 0.15
        elif n in ("acero", "marco"):
            b.inputs["Metallic"].default_value = 1.0 if n == "acero" else 0.6
            b.inputs["Roughness"].default_value = 0.3
        elif n == "espejo":
            b.inputs["Base Color"].default_value = (0.9, 0.93, 0.95, 1)
            b.inputs["Metallic"].default_value = 1.0
            b.inputs["Roughness"].default_value = 0.02
        elif n in ("marmol", "ceramica", "azulejo"):
            b.inputs["Roughness"].default_value = 0.18
            b.inputs["Coat Weight"].default_value = 0.35
        elif n == "cera":
            b.inputs["Roughness"].default_value = 0.5
        elif n == "cortina":
            b.inputs["Roughness"].default_value = 0.95
            b.inputs["Sheen Weight"].default_value = 0.6
        elif n.startswith("tela_") or n in ("alfombra", "alfombra2", "felpudo"):
            b.inputs["Roughness"].default_value = 0.97
            b.inputs["Sheen Weight"].default_value = 0.5
        elif n == "pantalla_negra":
            b.inputs["Roughness"].default_value = 0.05
            b.inputs["Coat Weight"].default_value = 0.6
    return len(tc_map)


EMISIONES = {"neon_magenta": 14.0, "neon_violeta": 14.0, "luz_calida": 10.0, "pantalla": 2.4}


def emisiones():
    """Neones, tiras LED y la tele: la emisión de Godot llega en otra unidad, se fija en Blender."""
    for nombre, fuerza in EMISIONES.items():
        m = bpy.data.materials.get(nombre)
        if m and m.use_nodes:
            principled(m).inputs["Emission Strength"].default_value = fuerza
    # farolitos del jardín: apagados de día, encendidos de noche (se animan en luces())
    m = bpy.data.materials.get("luz_jardin")
    if m:
        principled(m).inputs["Emission Strength"].default_value = 0.4
        sock = principled(m).inputs["Emission Strength"]
        sock.default_value = 0.2
        sock.keyframe_insert("default_value", frame=f(84.0))
        sock.default_value = 12.0
        sock.keyframe_insert("default_value", frame=f(88.5))
        sock.default_value = 0.2
        sock.keyframe_insert("default_value", frame=0)
        # la curva queda ordenada por tiempo
        if m.node_tree.animation_data and m.node_tree.animation_data.action:
            for cap in m.node_tree.animation_data.action.layers:
                for ti in cap.strips:
                    for cb in ti.channelbags:
                        for fc in cb.fcurves:
                            fc.keyframe_points.sort()
                            fc.update()


# ───────────────────────────────────────────── árboles: copas sólidas con ruido sobre cada follaje
def blobs_base():
    """Tres variantes de «bola de hojas» (icosfera con ruido) compartidas por todos los árboles."""
    mallas = []
    for k in range(3):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
        for v in bm.verts:
            n = noise.noise(v.co * 1.7 + Vector((k * 13.1, k * 7.7, k * 3.3)))
            n2 = noise.noise(v.co * 5.2 + Vector((k * 5.3, 1.0, 9.0)))
            v.co *= 1.0 + 0.22 * n + 0.07 * n2
        me = bpy.data.meshes.new(f"copa_base_{k}")
        bm.to_mesh(me)
        bm.free()
        for p in me.polygons:
            p.use_smooth = True
        mallas.append(me)
    return mallas


def material_hojas():
    m, nt = nuevo_material("Follaje_p013")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    at = nt.nodes.new("ShaderNodeAttribute")
    at.attribute_type = "OBJECT"
    at.attribute_name = '["tinte"]'
    oi = nt.nodes.new("ShaderNodeObjectInfo")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    rr = ruido(nt, 3.5, 6.0, 0.6)
    nt.links.new(tc.outputs["Object"], rr.inputs["Vector"])
    rampa = nt.nodes.new("ShaderNodeValToRGB")
    rampa.color_ramp.elements[0].position = 0.35
    rampa.color_ramp.elements[0].color = (0.16, 0.26, 0.09, 1)
    rampa.color_ramp.elements[1].position = 0.72
    rampa.color_ramp.elements[1].color = (0.45, 0.5, 0.18, 1)
    nt.links.new(rr.outputs["Fac"], rampa.inputs["Fac"])
    mul = nt.nodes.new("ShaderNodeMix")
    mul.data_type = "RGBA"
    mul.blend_type = "MULTIPLY"
    mul.inputs["Factor"].default_value = 1.0
    nt.links.new(at.outputs["Color"], mul.inputs["A"])
    nt.links.new(rampa.outputs["Color"], mul.inputs["B"])
    nt.links.new(mul.outputs["Result"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.72
    b.inputs["Subsurface Weight"].default_value = 0.2
    b.inputs["Subsurface Radius"].default_value = (0.4, 0.8, 0.2)
    b.inputs["Specular IOR Level"].default_value = 0.3
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.5
    r2 = ruido(nt, 22.0, 3.0, 0.6)
    nt.links.new(tc.outputs["Object"], r2.inputs["Vector"])
    nt.links.new(r2.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    return m


def material_corteza():
    m, nt = nuevo_material("Corteza_p013")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    r = ruido(nt, 14.0, 6.0, 0.65)
    nt.links.new(tc.outputs["Object"], r.inputs["Vector"])
    rampa = nt.nodes.new("ShaderNodeValToRGB")
    rampa.color_ramp.elements[0].color = (0.05, 0.03, 0.02, 1)
    rampa.color_ramp.elements[1].color = (0.2, 0.13, 0.08, 1)
    nt.links.new(r.outputs["Fac"], rampa.inputs["Fac"])
    nt.links.new(rampa.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.9
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.8
    nt.links.new(r.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    return m


TINTES = {"sc_pine": (0.5, 0.75, 0.55), "sc_cypress": (0.45, 0.7, 0.5), "sc_acacia": (0.95, 1.05, 0.6),
          "tree_weeping_willow": (1.1, 1.15, 0.65), "tree_birch": (1.05, 1.1, 0.7), "tree_lombardy_poplar": (0.8, 1.0, 0.6),
          "tree_quaking_aspen": (1.0, 1.1, 0.65), "tree_black_tupelo": (0.8, 0.95, 0.55), "tree_sassafras": (0.9, 1.0, 0.55),
          "tree_tree": (0.85, 1.0, 0.55), "sc_palm_tree": (0.7, 0.95, 0.5), "tree_fan_palm_tree": (0.7, 0.95, 0.5)}


def arboles(col):
    mallas = blobs_base()
    m_hoja = material_hojas()
    m_corteza = material_corteza()
    n_copas, n_arboles = 0, 0
    rng = random.Random(SEMILLA)
    raices = [o for o in bpy.data.objects if re.match(r"^(tree_(?!Mesh)|sc_(acacia|pine|cypress|palm))", o.name)]
    for r in raices:
        tipo = re.sub(r"_\d+$", "", r.name)
        hojas, troncos = [], []
        for c in r.children_recursive:
            if c.type != "MESH":
                continue
            nombre = c.name.lower()
            if re.match(r"^(leav|foil|stems|branchtw|oldleav)", nombre):
                hojas.append(c)
            elif re.match(r"^(trunk|branches)", nombre):
                troncos.append(c)
        for c in hojas:
            c.data.materials.clear()
            c.data.materials.append(m_hoja)
            c["tinte"] = TINTES.get(tipo, (0.9, 1.0, 0.6))
        for c in troncos:
            if not any(n.type == "TEX_IMAGE" for mm in c.data.materials if mm and mm.use_nodes for n in mm.node_tree.nodes):
                c.data.materials.clear()
                c.data.materials.append(m_corteza)
        n_arboles += 1
        if not hojas or tipo in ("sc_palm_tree", "tree_fan_palm_tree"):
            continue
        for c in hojas:
            pts = [c.matrix_world @ Vector(v) for v in c.bound_box]
            lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
            hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
            ctr, dim = (lo + hi) / 2, hi - lo
            if dim.x < 0.2 or dim.y < 0.2:
                continue
            ancho = max(dim.x, dim.y)
            if tipo in ("sc_pine",):            # cono: bolas que se achican hacia arriba
                n = 5
                specs = [(Vector((0, 0, lo.z + dim.z * (0.18 + 0.2 * k))), (ancho * 0.5 * (1.0 - 0.17 * k), ) * 2 + (dim.z * 0.2,)) for k in range(n)]
            elif tipo in ("sc_cypress", "tree_lombardy_poplar"):   # columna
                n = 4
                specs = [(Vector((0, 0, lo.z + dim.z * (0.15 + 0.23 * k))), (ancho * 0.48 * (1.0 - 0.1 * abs(k - 1.4)), ) * 2 + (dim.z * 0.2,)) for k in range(n)]
            else:                                # copa redonda: bolas repartidas dentro de la caja
                n = 5 if ancho > 3 else 4
                specs = []
                for k in range(n):
                    ang = rng.uniform(0, 6.28)
                    rad = rng.uniform(0.0, 0.28) * ancho
                    specs.append((Vector((math.cos(ang) * rad, math.sin(ang) * rad, lo.z + dim.z * rng.uniform(0.3, 0.75))),
                                  (ancho * rng.uniform(0.27, 0.36), ancho * rng.uniform(0.27, 0.36), dim.z * rng.uniform(0.28, 0.38))))
            for k, (off, esc) in enumerate(specs):
                o = bpy.data.objects.new(f"copa_{r.name}_{k}", mallas[(k + n_copas) % 3])
                o.location = Vector((ctr.x, ctr.y, 0)) + Vector((off.x, off.y, off.z))
                o.scale = Vector(esc)
                o.rotation_euler = (0, 0, rng.uniform(0, 6.28))
                o.data.materials.clear() if False else None
                if not o.data.materials:
                    o.data.materials.append(m_hoja)
                o["tinte"] = TINTES.get(tipo, (0.9, 1.0, 0.6))
                col.objects.link(o)
                o.parent = r.parent if False else None
                # sigue la animación de aparición del árbol (escala del contenedor): se emparenta al árbol conservando la pose
                o.parent = r
                o.matrix_parent_inverse = r.matrix_world.inverted()
                n_copas += 1
    return n_arboles, n_copas


# ───────────────────────────────────────────── cielo y luces: día → atardecer → noche
def cielo_y_sol():
    s = bpy.context.scene
    w = bpy.data.worlds.new("Mundo_p013")
    s.world = w
    w.use_nodes = True
    nt = w.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputWorld")
    fondo = nt.nodes.new("ShaderNodeBackground")
    sky = nt.nodes.new("ShaderNodeTexSky")
    sky.sky_type = "MULTIPLE_SCATTERING"
    sky.sun_disc = False
    sky.altitude = 40.0
    sky.air_density = 1.0
    sky.aerosol_density = 1.0
    sky.ozone_density = 1.0
    sky.sun_rotation = math.radians(200.0)
    nt.links.new(sky.outputs["Color"], fondo.inputs["Color"])
    nt.links.new(fondo.outputs[0], out.inputs["Surface"])
    # curva solar: (segundo, elevación, intensidad del fondo, densidad de neblina)
    curva = [(0.0, 48.0, 0.5, 0.0006), (60.0, 38.0, 0.5, 0.0006), (74.0, 24.0, 0.5, 0.0012), (80.0, 12.0, 0.5, 0.0018),
             (85.0, 4.0, 0.6, 0.0026), (88.5, -3.0, 0.7, 0.0045), (91.0, -9.0, 0.55, 0.006), (99.5, -14.0, 0.5, 0.007)]
    sol = bpy.data.objects.get("Luz_sol")
    if sol is None:
        d = bpy.data.lights.new("Luz_sol", "SUN")
        sol = bpy.data.objects.new("Luz_sol", d)
        bpy.context.collection.objects.link(sol)
    sol.parent = None                      # el GLB lo trae colgado de la casa (rotada): se suelta para fijar su dirección en el mundo
    sol.data.angle = math.radians(1.2)
    sol.rotation_mode = "XYZ"
    for t, el, inten, dens in curva:
        sky.sun_elevation = math.radians(max(el, -12.0))
        sky.keyframe_insert("sun_elevation", frame=f(t))
        fondo.inputs["Strength"].default_value = inten
        fondo.inputs["Strength"].keyframe_insert("default_value", frame=f(t))
        BRUMA.append((t, dens))
        # lámpara de sol: viene del frente de la casa (cara sur = −Y en Blender)
        sol.rotation_euler = (math.radians(90.0 - max(el, 0.0)), 0.0, math.radians(25.0))
        sol.keyframe_insert("rotation_euler", frame=f(t))
        # intensidad y color: dorado al bajar, se apaga bajo el horizonte
        calidez = max(0.0, min(1.0, (48.0 - el) / 44.0))
        sol.data.color = (1.0, 0.93 - 0.35 * calidez, 0.82 - 0.55 * calidez)
        sol.data.energy = 0.0 if el <= -1.0 else (3.0 * (0.45 + 0.55 * min(1.0, el / 25.0)) if el > 0 else 0.6)
        sol.data.keyframe_insert("color", frame=f(t))
        sol.data.keyframe_insert("energy", frame=f(t))
    # luna: azul suave que aparece con el anochecer
    luna_d = bpy.data.lights.new("Luna", "SUN")
    luna = bpy.data.objects.new("Luna", luna_d)
    bpy.context.collection.objects.link(luna)
    luna_d.color = (0.55, 0.65, 1.0)
    luna_d.angle = math.radians(2.0)
    luna.rotation_euler = (math.radians(55.0), 0.0, math.radians(-30.0))
    for t, e in ((0.0, 0.0), (84.0, 0.0), (89.0, 0.35), (99.5, 0.4)):
        luna_d.energy = e
        luna_d.keyframe_insert("energy", frame=f(t))
    # luz de relleno del cielo para interiores (muy baja, sólo evita negros duros)
    return curva


LUCES = {  # nombre (prefijo) → (vatios, color, radio, apagada_de_día)
    "Luz_sala": (170.0, None, 0.12, False), "Luz_comedor": (150.0, None, 0.12, False), "Luz_cocina": (160.0, None, 0.12, False),
    "Luz_isla": (60.0, None, 0.08, False), "Luz_principal": (130.0, None, 0.12, False), "Luz_velador": (18.0, None, 0.05, False),
    "Luz_neon_cama": (45.0, None, 0.1, False), "Luz_neon_tv": (55.0, None, 0.1, False), "Luz_cuarto2": (120.0, None, 0.12, False),
    "Luz_estudio": (120.0, None, 0.12, False), "Luz_bano": (110.0, None, 0.12, False), "Luz_indirecta_pared": (300.0, None, 0.1, False),
    "Luz_chimenea": (150.0, None, 0.1, False), "Luz_entrada": (120.0, None, 0.1, True), "Luz_fachada": (170.0, None, 0.1, True),
    "Luz_cochera": (200.0, None, 0.1, True), "Luz_porton": (45.0, None, 0.06, True), "Luz_jardin": (38.0, None, 0.06, True),
    "Luz_calle": (900.0, None, 0.12, True),
}


def luces():
    """Las luces de Godot llegan con energía casi cero: se fijan en vatios de Blender. Las exteriores se encienden al anochecer."""
    info = {}
    for o in bpy.data.objects:
        if o.type != "LIGHT":
            continue
        k = next((p for p in LUCES if o.name.startswith(p)), None)
        if k is None:
            continue
        w, _, radio, exterior = LUCES[k]
        L = o.data
        if L.type == "SPOT":
            L.spot_size = math.radians(80.0)
            L.spot_blend = 0.5
        L.shadow_soft_size = radio
        if exterior:
            L.energy = 0.0
            L.keyframe_insert("energy", frame=0)
            L.energy = 0.0
            L.keyframe_insert("energy", frame=f(84.0))
            L.energy = w
            L.keyframe_insert("energy", frame=f(88.0))
        else:
            L.energy = w
        info[o.name] = round(L.energy, 1)
    return info


# ───────────────────────────────────────────── fuego de la chimenea (llama volumétrica + chispas)
def fuego(col):
    marca = bpy.data.objects.get("FX_fuego_chimenea")
    if marca is None:
        return "sin marcador"
    base = marca.matrix_world.translation.copy()
    m, nt = nuevo_material("Llama_p013")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    emi = nt.nodes.new("ShaderNodeEmission")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    r = ruido(nt, 6.0, 5.0, 0.6)
    r.noise_dimensions = "4D"
    nt.links.new(tc.outputs["Object"], r.inputs["Vector"])
    d = r.inputs["W"].driver_add("default_value")
    d.driver.type = "SCRIPTED"
    d.driver.expression = "frame / 30.0 * 2.6"
    rampa = nt.nodes.new("ShaderNodeValToRGB")
    rampa.color_ramp.elements[0].position = 0.25
    rampa.color_ramp.elements[0].color = (1.0, 0.08, 0.0, 1)
    rampa.color_ramp.elements[1].position = 0.75
    rampa.color_ramp.elements[1].color = (1.0, 0.75, 0.2, 1)
    nt.links.new(r.outputs["Fac"], rampa.inputs["Fac"])
    nt.links.new(rampa.outputs["Color"], emi.inputs["Color"])
    emi.inputs["Strength"].default_value = 28.0
    nt.links.new(emi.outputs[0], out.inputs["Surface"])
    llamas = []
    for k, (dx, dz, esc) in enumerate(((0.0, 0.0, 1.0), (-0.16, 0.05, 0.75), (0.17, -0.04, 0.8), (0.04, 0.1, 0.6))):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=0.5, location=(base.x + dx, base.y + dz, base.z + 0.18 * esc))
        o = bpy.context.active_object
        o.name = f"Llama_{k}"
        o.scale = (0.2 * esc, 0.12 * esc, 0.46 * esc)
        o.data.materials.append(m)
        for c in o.users_collection:
            c.objects.unlink(o)
        col.objects.link(o)
        # parpadeo: la llama cambia de altura con el tiempo (curva con ruido)
        o.keyframe_insert("scale", frame=0)
        fc = [c for c in o.animation_data.action.layers[0].strips[0].channelbags[0].fcurves if c.data_path == "scale"]
        for c in fc:
            md = c.modifiers.new("NOISE")
            md.scale = 5.0 + 2 * k
            md.strength = 0.2 * esc
            md.phase = k * 7.0
        llamas.append(o.name)
    # luz de la chimenea con parpadeo
    lz = bpy.data.objects.get("Luz_chimenea")
    if lz:
        lz.data.energy = 150.0
        lz.data.color = (1.0, 0.45, 0.15)
        lz.data.keyframe_insert("energy", frame=0)
        fcs = [c for c in lz.data.animation_data.action.layers[0].strips[0].channelbags[0].fcurves if c.data_path == "energy"]
        for c in fcs:
            md = c.modifiers.new("NOISE")
            md.scale = 4.0
            md.strength = 70.0
            md.phase = 3.0
    # chispas: sistema de partículas sobre un emisor chico (determinista por cuadro, sin horneado)
    bpy.ops.mesh.primitive_plane_add(size=0.3, location=(base.x, base.y, base.z + 0.22))
    em = bpy.context.active_object
    em.name = "Emisor_chispas"
    for c in em.users_collection:
        c.objects.unlink(em)
    col.objects.link(em)
    em.hide_render = True
    em.display_type = "WIRE"
    bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=6, radius=0.012, location=(0, 0, -50))
    chispa = bpy.context.active_object
    chispa.name = "Chispa"
    mc, nc = nuevo_material("Chispa_p013")
    oc = nc.nodes.new("ShaderNodeOutputMaterial")
    ec = nc.nodes.new("ShaderNodeEmission")
    ec.inputs["Color"].default_value = (1.0, 0.45, 0.08, 1)
    ec.inputs["Strength"].default_value = 60.0
    nc.links.new(ec.outputs[0], oc.inputs["Surface"])
    chispa.data.materials.append(mc)
    for c in chispa.users_collection:
        c.objects.unlink(c) if False else None
    for c in list(chispa.users_collection):
        c.objects.unlink(chispa)
    col.objects.link(chispa)
    chispa.hide_render = True
    ps = em.modifiers.new("Chispas", "PARTICLE_SYSTEM").particle_system
    st = ps.settings
    st.count = 70
    st.frame_start = 0
    st.frame_end = int(f(99.5))
    st.lifetime = 38
    st.lifetime_random = 0.6
    st.emit_from = "FACE"
    st.normal_factor = 0.55
    st.object_align_factor = (0.0, 0.0, 0.6)
    st.factor_random = 0.35
    st.effector_weights.gravity = -0.03
    st.render_type = "OBJECT"
    st.instance_object = chispa
    st.particle_size = 1.0
    st.size_random = 0.6
    ps.seed = SEMILLA
    return llamas


def bruma(col):
    """Bruma atmosférica en un volumen acotado alrededor de la casa (un volumen de mundo infinito tapa el cielo)."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=(9.0, -10.0, 9.0))
    c = bpy.context.active_object
    c.name = "Bruma_atmosfera"
    c.scale = (260.0, 260.0, 18.0)
    for k in list(c.users_collection):
        k.objects.unlink(c)
    col.objects.link(c)
    c.display_type = "WIRE"
    m, nt = nuevo_material("Bruma_atmosfera")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    pv = nt.nodes.new("ShaderNodeVolumeScatter")
    pv.inputs["Color"].default_value = (0.85, 0.9, 1.0, 1.0)
    pv.inputs["Anisotropy"].default_value = 0.4
    nt.links.new(pv.outputs[0], out.inputs["Volume"])
    sock = pv.inputs["Density"]
    for t, d in BRUMA:
        sock.default_value = d * 0.15
        sock.keyframe_insert("default_value", frame=f(t))
    c.data.materials.append(m)
    return c.name


# ───────────────────────────────────────────── neblina baja en el jardín al anochecer
def neblina_jardin(col):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(9.0, -14.0, 0.45))        # centro del jardín (Blender: y = −z de Godot)
    c = bpy.context.active_object
    c.name = "Neblina_jardin"
    c.scale = (44.0, 36.0, 1.1)
    for k in list(c.users_collection):
        k.objects.unlink(c)
    col.objects.link(c)
    c.display_type = "WIRE"
    m, nt = nuevo_material("Neblina_jardin")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    pv = nt.nodes.new("ShaderNodeVolumePrincipled")
    pv.inputs["Color"].default_value = (0.75, 0.8, 0.95, 1)
    pv.inputs["Anisotropy"].default_value = 0.3
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    r = ruido(nt, 2.2, 3.0, 0.55)
    r.noise_dimensions = "4D"
    nt.links.new(tc.outputs["Object"], r.inputs["Vector"])
    d = r.inputs["W"].driver_add("default_value")
    d.driver.type = "SCRIPTED"
    d.driver.expression = "frame / 30.0 * 0.05"
    # se desvanece hacia arriba y hacia los bordes
    za = nt.nodes.new("ShaderNodeMapRange")
    za.inputs["From Min"].default_value = 0.1
    za.inputs["From Max"].default_value = 0.5
    za.inputs["To Min"].default_value = 1.0
    za.inputs["To Max"].default_value = 0.0
    nt.links.new(sep.outputs["Z"], za.inputs["Value"])
    za.clamp = True
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    nt.links.new(r.outputs["Fac"], mul.inputs[0])
    nt.links.new(za.outputs["Result"], mul.inputs[1])
    ds = nt.nodes.new("ShaderNodeMath")
    ds.operation = "MULTIPLY"
    nt.links.new(mul.outputs[0], ds.inputs[0])
    ds.inputs[1].default_value = 0.0
    nt.links.new(ds.outputs[0], pv.inputs["Density"])
    nt.links.new(pv.outputs[0], out.inputs["Volume"])
    # la densidad sube al anochecer
    ds.inputs[1].keyframe_insert("default_value", frame=0)
    for t, v in ((80.0, 0.0), (86.0, 0.5), (99.5, 0.9)):
        ds.inputs[1].default_value = v
        ds.inputs[1].keyframe_insert("default_value", frame=f(t))
    ds.inputs[1].default_value = 0.0
    ds.inputs[1].keyframe_insert("default_value", frame=0)
    c.data.materials.append(m)
    return c.name


# ───────────────────────────────────────────── cámara, tiempo y Cycles
def camara_y_tiempo(total_s):
    s = bpy.context.scene
    s.render.fps = FPS
    s.render.fps_base = 1.0
    s.frame_start = 0
    s.frame_end = int(round(total_s * FPS)) - 1
    cam = bpy.data.objects.get("Camara")
    s.camera = cam
    cam.data.sensor_fit = "VERTICAL"
    cam.data.clip_start = 0.08
    cam.data.clip_end = 900.0
    return cam.name


def cycles(s):
    s.render.engine = "CYCLES"
    s.render.resolution_x, s.render.resolution_y = RES
    s.render.resolution_percentage = 100
    s.render.pixel_aspect_x = s.render.pixel_aspect_y = 1.0
    s.render.image_settings.file_format = "PNG"
    s.render.use_motion_blur = False
    s.render.use_persistent_data = True
    s.view_settings.view_transform = "AgX"
    s.view_settings.look = "AgX - Medium High Contrast"
    for t, ex in ((0.0, -0.9), (74.0, -0.9), (82.0, -0.4), (88.0, 0.0), (99.5, 0.0)):   # el día entra más claro que la noche
        s.view_settings.exposure = ex
        s.view_settings.keyframe_insert("exposure", frame=f(t))
    c = s.cycles
    c.device = "CPU"
    c.samples = 6
    c.use_adaptive_sampling = True
    c.adaptive_threshold = 0.05
    c.use_denoising = True
    c.denoiser = "OPENIMAGEDENOISE"
    c.denoising_input_passes = "RGB_ALBEDO_NORMAL"
    c.max_bounces = 6
    c.diffuse_bounces = 3
    c.glossy_bounces = 3
    c.transmission_bounces = 6
    c.transparent_max_bounces = 12
    c.volume_bounces = 1
    c.use_light_tree = True
    c.use_animated_seed = False
    c.seed = SEMILLA
    c.caustics_reflective = False
    c.caustics_refractive = False
    c.sample_clamp_indirect = 8.0
    c.volume_step_rate = 2.0
    c.volume_max_steps = 64


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=GLB)
    s.render.fps = FPS
    reescalar_tiempo()
    total = max(a.frame_range[1] for a in bpy.data.actions) / FPS
    info = {"total_s": round(total, 2)}
    col = bpy.data.collections.new("Efectos_p013")
    s.collection.children.link(col)
    info["autos"] = aligerar_autos()
    info["pintura_autos"] = pintura_autos()
    info["vidrios"] = vidrio_real()
    pasto()
    superficies()
    emisiones()
    s.frame_set(int(total * FPS) - 2)            # pose final: los árboles ya aparecieron (escala 1)
    info["arboles"] = arboles(col)
    s.frame_set(0)
    info["cielo"] = [c[:3] for c in cielo_y_sol()]
    info["luces"] = len(luces())
    info["llamas"] = fuego(col)
    info["neblina"] = neblina_jardin(col)
    info["bruma"] = bruma(col)
    info["camara"] = camara_y_tiempo(total)
    cycles(s)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=SALIDA, compress=True)
    print("INFORME", info)


main()
