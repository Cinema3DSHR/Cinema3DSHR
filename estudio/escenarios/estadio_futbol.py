"""Escenario: estadio de fútbol 11 (modelo de Free Kick Swipe, mixamo-respaldo/futbol_free_kick_swipe).

El GLB del juego trae la geometría pero sus materiales eran shaders de Godot (llegan sin color), así que acá se
reconstruyen en Blender: césped con franjas de corte, líneas, butacas por sectores, paredes, techos, torres,
carteles LED NEUTROS (sin marcas reales), arcos con red, y el público: 13 074 hinchas 2D del atlas del juego
(6 poses × 12 personas), cada uno con su persona al azar y una pose según el ánimo de la escena.

Ejes: X = largo (arcos en x = ±52,5), Y = ancho (cancha 105 × 68 m), Z = arriba.
"""
from __future__ import annotations
import math
import random

import bpy
from estudio import config
from estudio.blender import importar as I
from estudio.blender import kit as K

REF_ESTADIO = "mixamo:futbol_free_kick_swipe/exportados/estadio_futbol11.glb"
REF_ATLAS = "mixamo:futbol_free_kick_swipe/03_estadio_publico/assets/arcade/crowd_atlas.png"
DEPENDENCIAS = ["mixamo:futbol_free_kick_swipe/exportados/estadio_futbol11.glb",
                "mixamo:futbol_free_kick_swipe/03_estadio_publico/assets/arcade/crowd_atlas.png"]

PARAMETROS = {
    "hora": "noche",                 # noche (torres encendidas) | dia
    "animo": "calma",                # calma | aplauso | festejo | tension, o [[segundo, ánimo], …] (cambia en el tiempo)
    "colores_local": [0.72, 0.04, 0.05],
    "colores_visitante": [0.05, 0.12, 0.62],
    "publico": 1.0,                  # 0..1: fracción de hinchas visibles
    "semilla": 11,
}


def _mat_cesped():
    mat = bpy.data.materials.new("cesped_cancha")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.85
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Position"], sep.inputs["Vector"])
    franja = nt.nodes.new("ShaderNodeMath")
    franja.operation = "DIVIDE"
    franja.inputs[1].default_value = 10.5
    nt.links.new(sep.outputs["X"], franja.inputs[0])
    fr = nt.nodes.new("ShaderNodeMath")
    fr.operation = "FRACT"
    nt.links.new(franja.outputs["Value"], fr.inputs[0])
    st = nt.nodes.new("ShaderNodeMath")
    st.operation = "GREATER_THAN"
    st.inputs[1].default_value = 0.5
    nt.links.new(fr.outputs["Value"], st.inputs[0])
    ruido = nt.nodes.new("ShaderNodeTexNoise")
    ruido.inputs["Scale"].default_value = 2.5
    nt.links.new(geo.outputs["Position"], ruido.inputs["Vector"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs["A"].default_value = (0.012, 0.075, 0.012, 1)
    mix.inputs["B"].default_value = (0.022, 0.11, 0.02, 1)
    nt.links.new(st.outputs["Value"], mix.inputs["Factor"])
    var = nt.nodes.new("ShaderNodeMix")
    var.data_type = "RGBA"
    var.blend_type = "MULTIPLY"
    var.inputs["Factor"].default_value = 0.35
    nt.links.new(mix.outputs["Result"], var.inputs["A"])
    nt.links.new(ruido.outputs["Color"], var.inputs["B"])
    nt.links.new(var.outputs["Result"], bsdf.inputs["Base Color"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.15
    fino = nt.nodes.new("ShaderNodeTexNoise")
    fino.inputs["Scale"].default_value = 180
    nt.links.new(geo.outputs["Position"], fino.inputs["Vector"])
    nt.links.new(fino.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    mat["estudio"] = {"color": [0.02, 0.1, 0.02], "rugosidad": 0.85, "metal": 0, "emision": None, "fuerza": 0, "alfa": 1}
    return mat


def _mat_butacas(c_a, c_b):
    mat = bpy.data.materials.new("butacas")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.6
    uv = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(uv.outputs["UV"], sep.inputs["Vector"])
    fila = nt.nodes.new("ShaderNodeMath")
    fila.operation = "WRAP"
    fila.inputs[1].default_value = 1.05
    fila.inputs[2].default_value = 0.0
    nt.links.new(sep.outputs["Y"], fila.inputs[0])
    esc = nt.nodes.new("ShaderNodeMath")
    esc.operation = "LESS_THAN"
    esc.inputs[1].default_value = 0.4
    nt.links.new(fila.outputs["Value"], esc.inputs[0])
    sector = nt.nodes.new("ShaderNodeMath")
    sector.operation = "WRAP"
    sector.inputs[1].default_value = 28.0
    sector.inputs[2].default_value = 0.0
    nt.links.new(sep.outputs["X"], sector.inputs[0])
    sec = nt.nodes.new("ShaderNodeMath")
    sec.operation = "GREATER_THAN"
    sec.inputs[1].default_value = 14.0
    nt.links.new(sector.outputs["Value"], sec.inputs[0])
    col = nt.nodes.new("ShaderNodeMix")
    col.data_type = "RGBA"
    col.inputs["A"].default_value = (*c_a, 1)
    col.inputs["B"].default_value = (*c_b, 1)
    nt.links.new(sec.outputs["Value"], col.inputs["Factor"])
    fin = nt.nodes.new("ShaderNodeMix")
    fin.data_type = "RGBA"
    fin.inputs["A"].default_value = (0.03, 0.035, 0.045, 1)
    nt.links.new(esc.outputs["Value"], fin.inputs["Factor"])
    nt.links.new(col.outputs["Result"], fin.inputs["B"])
    nt.links.new(fin.outputs["Result"], bsdf.inputs["Base Color"])
    nt.links.new(fin.outputs["Result"], bsdf.inputs["Emission Color"])
    bsdf.inputs["Emission Strength"].default_value = 0.6
    mat["estudio"] = {"color": list(c_a), "rugosidad": 0.6, "metal": 0, "emision": None, "fuerza": 0, "alfa": 1}
    return mat


def _mat_publico(atlas_ruta, animo: str):
    """Hinchas 2D: fila del atlas al azar por hincha, columna (pose) según el ánimo, alternando cuadros."""
    mat = bpy.data.materials.new("publico")
    mat.use_nodes = True
    try:
        mat.surface_render_method = "DITHERED"
    except Exception:
        pass
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    emi = nt.nodes.new("ShaderNodeEmission")  # el juego los dibuja sin sombreado (unshaded)
    emi.inputs["Strength"].default_value = 0.9
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mixs = nt.nodes.new("ShaderNodeMixShader")
    info = nt.nodes.new("ShaderNodeObjectInfo")
    uv = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(uv.outputs["UV"], sep.inputs["Vector"])
    fila = nt.nodes.new("ShaderNodeMath")
    fila.operation = "MULTIPLY"
    fila.inputs[1].default_value = 12.0
    nt.links.new(info.outputs["Random"], fila.inputs[0])
    filaf = nt.nodes.new("ShaderNodeMath")
    filaf.operation = "FLOOR"
    nt.links.new(fila.outputs["Value"], filaf.inputs[0])
    # ánimo en el tiempo: [(segundo, ánimo), …] → columna base del atlas y ritmo de la animación
    cols = {"calma": 0, "aplauso": 1, "festejo": 2, "tension": 4}
    tramos = animo if isinstance(animo, list) else [[0, animo]]
    fps = bpy.context.scene.render.fps
    expr_col, expr_rit = "0", "40"
    for seg, a in sorted(tramos, key=lambda t: t[0]):
        f = int(seg * fps) + 1
        expr_col = f"({cols.get(a, 0)} if frame >= {f} else {expr_col})"
        expr_rit = f"({40 if a == 'calma' else 5} if frame >= {f} else {expr_rit})"
    base = nt.nodes.new("ShaderNodeValue")
    base.outputs[0].driver_add("default_value").driver.expression = expr_col
    cuadro = nt.nodes.new("ShaderNodeValue")
    d = cuadro.outputs[0].driver_add("default_value").driver
    d.expression = f"floor(frame / {expr_rit})"
    suma = nt.nodes.new("ShaderNodeMath")
    suma.operation = "ADD"
    nt.links.new(cuadro.outputs[0], suma.inputs[0])
    fase = nt.nodes.new("ShaderNodeMath")
    fase.operation = "MULTIPLY"
    fase.inputs[1].default_value = 7.0
    nt.links.new(info.outputs["Random"], fase.inputs[0])
    nt.links.new(fase.outputs["Value"], suma.inputs[1])
    alterna = nt.nodes.new("ShaderNodeMath")
    alterna.operation = "WRAP"
    alterna.inputs[1].default_value = 2.0
    alterna.inputs[2].default_value = 0.0
    fl = nt.nodes.new("ShaderNodeMath")
    fl.operation = "FLOOR"
    nt.links.new(suma.outputs["Value"], fl.inputs[0])
    nt.links.new(fl.outputs["Value"], alterna.inputs[0])
    col = nt.nodes.new("ShaderNodeMath")
    col.operation = "ADD"
    nt.links.new(base.outputs[0], col.inputs[1])
    nt.links.new(alterna.outputs["Value"], col.inputs[0])
    # u = (uv.x + col)/6 ; v = 1 - (row + (1 - uv.y))/12  (las imágenes de Blender tienen el origen abajo)
    u1 = nt.nodes.new("ShaderNodeMath")
    u1.operation = "ADD"
    nt.links.new(sep.outputs["X"], u1.inputs[0])
    nt.links.new(col.outputs["Value"], u1.inputs[1])
    u2 = nt.nodes.new("ShaderNodeMath")
    u2.operation = "DIVIDE"
    u2.inputs[1].default_value = 6.0
    nt.links.new(u1.outputs["Value"], u2.inputs[0])
    v0 = nt.nodes.new("ShaderNodeMath")
    v0.operation = "SUBTRACT"
    v0.inputs[0].default_value = 1.0
    nt.links.new(sep.outputs["Y"], v0.inputs[1])
    v1 = nt.nodes.new("ShaderNodeMath")
    v1.operation = "ADD"
    nt.links.new(v0.outputs["Value"], v1.inputs[0])
    nt.links.new(filaf.outputs["Value"], v1.inputs[1])
    v2 = nt.nodes.new("ShaderNodeMath")
    v2.operation = "DIVIDE"
    v2.inputs[1].default_value = 12.0
    nt.links.new(v1.outputs["Value"], v2.inputs[0])
    v3 = nt.nodes.new("ShaderNodeMath")
    v3.operation = "SUBTRACT"
    v3.inputs[0].default_value = 1.0
    nt.links.new(v2.outputs["Value"], v3.inputs[1])
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(u2.outputs["Value"], comb.inputs["X"])
    nt.links.new(v3.outputs["Value"], comb.inputs["Y"])
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(atlas_ruta), check_existing=True)
    tex.interpolation = "Closest"
    nt.links.new(comb.outputs["Vector"], tex.inputs["Vector"])
    nt.links.new(tex.outputs["Color"], emi.inputs["Color"])
    nt.links.new(tex.outputs["Alpha"], mixs.inputs["Fac"])
    nt.links.new(tr.outputs["BSDF"], mixs.inputs[1])
    nt.links.new(emi.outputs["Emission"], mixs.inputs[2])
    nt.links.new(mixs.outputs["Shader"], out.inputs["Surface"])
    mat["estudio"] = {"color": [0.3, 0.3, 0.35], "rugosidad": 1, "metal": 0, "emision": None, "fuerza": 0, "alfa": 1}
    return mat


def _red(nombre, x, sentido, mat, col):
    """Red del arco: grilla de alambre (malla de 12 cm) atrás, a los costados y arriba."""
    import bmesh
    ancho, alto, fondo = 7.32, 2.44, 2.0
    bm = bmesh.new()
    paso = 0.12
    def cara(o, a, b, na, nb):
        vs = [[bm.verts.new(o + a * (i / na) + b * (j / nb)) for j in range(nb + 1)] for i in range(na + 1)]
        for i in range(na):
            for j in range(nb):
                bm.faces.new((vs[i][j], vs[i + 1][j], vs[i + 1][j + 1], vs[i][j + 1]))
    from mathutils import Vector as V
    x0 = x + sentido * 0.06
    x1 = x + sentido * fondo
    na, nb, nf = int(ancho / paso), int(alto / paso), int(fondo / paso)
    cara(V((x1, -ancho / 2, 0)), V((0, ancho, 0)), V((0, 0, alto * 0.75)), na, nb)        # fondo
    cara(V((x0, -ancho / 2, alto)), V((0, ancho, 0)), V((x1 - x0, 0, -alto * 0.25)), na, nf)  # techo inclinado
    for y in (-ancho / 2, ancho / 2):
        cara(V((x0, y, 0)), V((x1 - x0, 0, 0)), V((0, 0, alto)), nf, nb)                   # costados
    me = bpy.data.meshes.new(nombre)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(nombre, me)
    me.materials.append(mat)
    col.objects.link(ob)
    w = ob.modifiers.new("alambre", "WIREFRAME")
    w.thickness = 0.008
    w.use_replace = True
    return ob


# tribunas del modelo: borde interior (z 2,2) a 43 m (laterales) / 61,5 m (cabeceras) y exterior (z 18,2) 26 m más afuera
TRIBUNAS = [
    # (eje a lo largo, signo hacia afuera, largo, rotación del hincha en Z)
    ("x", +1, 123.0, 0.0),            # lateral norte (y > 0): miran a −Y
    ("x", -1, 123.0, math.pi),        # lateral sur (y < 0): miran a +Y
    ("y", +1, 86.0, -math.pi / 2),    # cabecera este (x > 0): miran a −X
    ("y", -1, 86.0, math.pi / 2),     # cabecera oeste (x < 0): miran a +X
]


def _sentar_publico(hinchas, rnd, densidad=1.0):
    asientos = []
    paso_fila, paso_butaca = 1.05, 0.62
    largo_pend = math.hypot(26.0, 16.0)
    for eje, signo, largo, rot in TRIBUNAS:
        borde = 43.0 if eje == "x" else 61.5
        filas = int(largo_pend / paso_fila)
        for f in range(1, filas):
            t = (f + 0.3) / filas * 26.0
            z = 2.2 + t * 16.0 / 26.0
            for b in range(int(largo / paso_butaca)):
                a = -largo / 2 + (b + 0.5) * paso_butaca
                if eje == "x":
                    asientos.append(((a, signo * (borde + t), z), rot))
                else:
                    asientos.append(((signo * (borde + t), a, z), rot))
    rnd.shuffle(asientos)
    usar = min(len(hinchas), int(len(asientos) * min(1.0, densidad)))
    for o, (pos, rot) in zip(hinchas[:usar], asientos):
        o.parent = None
        o.location = (pos[0] + rnd.uniform(-0.08, 0.08), pos[1], pos[2] - rnd.uniform(0.25, 0.45))
        o.rotation_euler = (0, 0, rot + rnd.uniform(-0.15, 0.15))
        esc = rnd.uniform(0.92, 1.08)
        o.scale = (esc, esc, esc)
    for o in hinchas[usar:]:
        o.hide_render = True


def construir(parametros: dict | None = None) -> dict:
    p = {**PARAMETROS, **(parametros or {})}
    rnd = random.Random(p["semilla"])
    s = bpy.context.scene
    col = K.coleccion("ESCENARIO_estadio")
    objs = I.importar(REF_ESTADIO, col)
    # quitar las luces casi nulas que exporta Godot y ocultar formas de colisión
    for o in list(objs):
        if o.type == "LIGHT":
            bpy.data.objects.remove(o)
            objs.remove(o)
        elif o.type == "EMPTY":
            o.hide_render = True
    c_loc = tuple(p["colores_local"])
    c_vis = tuple(p["colores_visitante"])
    cesped = _mat_cesped()
    lineas = K.material("lineas_cancha", (0.85, 0.85, 0.82), 0.7)
    butacas = _mat_butacas(c_loc, c_vis)
    pared = K.material("pared_estadio", (0.02, 0.03, 0.07), 0.6)
    techo = K.material("techo_estadio", (0.06, 0.065, 0.07), 0.45, 0.6)
    torre = K.material("torre_estadio", (0.25, 0.26, 0.28), 0.4, 0.8)
    poste = K.material("poste_arco", (0.95, 0.95, 0.95), 0.25)
    red_m = K.material("red_arco", (0.9, 0.9, 0.9), 0.6)
    publico = _mat_publico(config.resolver(REF_ATLAS), p["animo"])
    hinchas = 0
    # varias piezas comparten la misma malla (los 13 000 hinchas son UNA malla instanciada): se decide el material
    # por malla, con el nombre del material ORIGINAL, y se asigna una sola vez
    originales = {}
    for o in objs:
        if o.type == "MESH" and o.data not in originales:
            originales[o.data] = o.data.materials[0].name if o.data.materials and o.data.materials[0] else None
    hechas = set()
    for o in objs:
        if o.type != "MESH":
            continue
        mname = originales[o.data]
        nombre = o.name.split(".")[0]
        if nombre == "Grass":
            nuevo = cesped
        elif nombre == "Lines":
            nuevo = lineas
        elif mname is None and len(o.data.vertices) == 4:
            nuevo = publico
            hinchas += 1
            if rnd.random() > p["publico"]:
                o.hide_render = True
        elif mname == "Material_44":
            nuevo = butacas
        elif mname == "Material_45":
            nuevo = pared
        elif mname in ("Material_46", "Material_47", "Material_48", "Material_49"):
            nuevo = techo
        elif mname in ("Material_50", "Material_51"):
            nuevo = torre
        elif mname in ("Material_2", "Material_4"):
            nuevo = poste
        else:
            # carteles perimetrales: LED con degradé de los colores de los equipos (sin marcas)
            i = int(mname.split("_")[-1]) if mname and mname.split("_")[-1].isdigit() else 0
            c = c_loc if i % 2 else c_vis
            nuevo = K.material(f"cartel_led_{i % 2}", (0.02, 0.02, 0.02), 0.4, emision=c, fuerza=1.2,
                               ruido=0.4, escala_ruido=0.8, ruido_en_emision=True, animar_ruido=0.4)
        if o.data in hechas:
            continue
        hechas.add(o.data)
        if len(o.data.materials):
            o.data.materials[0] = nuevo  # asignar en el lugar (clear() + append() es muy lento con miles de mallas)
        else:
            o.data.materials.append(nuevo)
    # la red de tela de Godot llega como superficie opaca: se oculta y se usa la red de alambre propia
    for o in objs:
        if o.name.startswith("ClothMesh"):
            o.hide_render = True
            o["visor_omitir"] = True
    # el GLB perdió la ubicación de cada hincha (todos en el origen): se los sienta butaca por butaca
    _sentar_publico([o for o in objs if o.type == "MESH" and o.data.materials and o.data.materials[0] == publico
                     and len(o.data.vertices) == 4], rnd, p["publico"])
    # redes
    for x, sentido in ((52.5, 1), (-52.5, -1)):
        _red(f"red_{'este' if x > 0 else 'oeste'}", x, sentido, red_m, col)
    # luz y cielo
    if p["hora"] == "dia":
        K.cielo_noche(s, cenit=(0.08, 0.16, 0.42), horizonte=(0.5, 0.6, 0.75), estrellas=False, fuerza=1.0)
        K.luz("sol", "SUN", (0, 0, 80), 4.0, (1, 0.96, 0.9), col, rot=(math.radians(40), 0, math.radians(35)))
    else:
        K.cielo_noche(s, fuerza=1.0)
        for tx in (-69.5, 69.5):
            for ty in (-51.0, 51.0):
                L = K.luz(f"torre_{tx}_{ty}", "SPOT", (tx * 0.97, ty * 0.97, 39.0), 2.6e5, (1.0, 0.97, 0.92), col,
                          angulo_spot=math.radians(70), radio=1.5)
                K.mirar_a(L, (tx * 0.15, ty * 0.15, 0))
        K.luz("relleno_cielo", "SUN", (0, 0, 60), 0.08, (0.6, 0.7, 1.0), col, rot=(math.radians(20), 0, 0),
              sombra=False)
    anclas = {
        "centro": (0, 0, 0), "arco_este": (52.5, 0, 0), "arco_oeste": (-52.5, 0, 0),
        "penal_este": (41.5, 0, 0), "penal_oeste": (-41.5, 0, 0),
        "medialuna_este": (32.35, 0, 0), "medialuna_oeste": (-32.35, 0, 0),
        "corner_ne": (52.5, 34, 0), "corner_se": (52.5, -34, 0), "corner_no": (-52.5, 34, 0), "corner_so": (-52.5, -34, 0),
        "banco_local": (-8, -36.5, 0), "banco_visitante": (8, -36.5, 0),
        "camara_tv": (0, -62, 22), "detras_arco_este": (60, 0, 2.5), "detras_arco_oeste": (-60, 0, 2.5),
        "tribuna_este": (66, 0, 9), "angulo_superior_der_este": (52.5, -3.4, 2.25),
        "angulo_superior_izq_este": (52.5, 3.4, 2.25),
    }
    print(f"[estadio] {hinchas} hinchas, ánimo {p['animo']}, hora {p['hora']}")
    # el público no va al visor del teléfono (13 000 planos): se marca para que el exportador lo omita
    for o in objs:
        if o.type == "MESH" and o.data.materials and o.data.materials[0] == publico and len(o.data.vertices) == 4:
            o["visor_omitir"] = True
    return {"anclas": anclas, "animables": {}, "parametros": p}
