"""Personajes animados con bancos de clips (NLA) — hoy: el futbolista de Free Kick Swipe.

Modelos (catalogo/personajes.json):
  futbol:jugador   jugador Tripo3D con esqueleto mixamorig de 23 huesos y 3 223 clips (f_jn_… campo,
                   k_jn_… arquero, s_jn_… escenas). Mira a +X en reposo. Uniforme pintado con máscaras.

Uso en el manifiesto (sección "personajes"):
  {"id": "tirador", "modelo": "futbol:jugador",
   "uniforme": {"camiseta": [r,g,b], "short": [..], "medias": [..], "botines": [..], "piel": [..], "pelo": [..]},
   "acciones": [
     {"clip": "f_jn_idle_ready_0012", "inicio_s": 0, "pos": [40, 0], "mirando_deg": 0},
     {"clip": "f_jn_setpiece_shot_3740", "inicio_s": 3.0, "encadenar": true},   # sigue desde donde terminó el anterior
     {"clip": "s_jn_celebrate_…", "inicio_s": 6.5, "encadenar": true, "repetir": 2}
   ]}
mirando_deg: 0 = hacia +X (arco de x = +52,5), 90 = hacia +Y, 180 = hacia −X.
Cada acción es un tramo NLA con mezcla corta entre clips. "encadenar" mide cuánto se desplazó la cadera durante el
clip anterior y ubica el siguiente ahí, así una carrera seguida de un remate no "salta" al origen.
"""
from __future__ import annotations
import math
from pathlib import Path

import bpy
from mathutils import Vector, Matrix
from estudio import config
from estudio.blender import importar as I
from estudio.blender import kit as K

MODELOS = {
    "futbol:jugador": {
        "ref": "mixamo:futbol_free_kick_swipe/exportados/jugador_con_animaciones.glb",
        "texturas": "mixamo:futbol_free_kick_swipe/02_jugador/assets/characters/player",
        "raiz": "Rig", "armadura": "Armature", "malla": "TripoBodyMesh", "ocultar": ["Icosphere"],
        "cadera": "mixamorig_Hips", "pie_der": "mixamorig_RightToeBase", "pie_izq": "mixamorig_LeftToeBase",
        "cabeza": "mixamorig_Head", "mano_der": "mixamorig_RightHand",
        "luma": {"camiseta": 0.203, "short": 0.286, "medias": 0.785, "botines": 0.088, "piel": 0.492, "pelo": 0.18},
    },
}
UNIFORME_DEFECTO = {"camiseta": (0.72, 0.04, 0.05), "short": (0.05, 0.12, 0.62), "medias": (0.9, 0.9, 0.9),
                    "botines": (0.03, 0.03, 0.035), "piel": (0.62, 0.40, 0.29), "pelo": (0.12, 0.07, 0.04)}

_BIBLIOTECAS: dict[str, dict] = {}


def _srgb_a_lineal(c):
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)


def biblioteca(modelo: str) -> dict:
    """Importa el modelo con todos sus clips UNA vez por escena y lo guarda oculto como prototipo."""
    if modelo in _BIBLIOTECAS and _BIBLIOTECAS[modelo]["raiz"].name in bpy.data.objects:
        return _BIBLIOTECAS[modelo]
    info = MODELOS[modelo]
    col = bpy.data.collections.get("BIBLIOTECA_" + modelo.replace(":", "_"))
    if col is None:
        col = bpy.data.collections.new("BIBLIOTECA_" + modelo.replace(":", "_"))
        bpy.context.scene.collection.children.link(col)
    objs = I.importar(info["ref"], col)
    por_nombre = {o.name.split(".")[0]: o for o in objs}
    col.hide_render = True
    col.hide_viewport = True
    lib = {"info": info, "coleccion": col, "objetos": objs, "raiz": por_nombre[info["raiz"]],
           "armadura": por_nombre[info["armadura"]], "malla": por_nombre[info["malla"]]}
    _BIBLIOTECAS[modelo] = lib
    return lib


def reiniciar():
    _BIBLIOTECAS.clear()


def _material_uniforme(nombre: str, info: dict, colores: dict) -> bpy.types.Material:
    """Recrea player_kit.gdshader: tinte por región = color × (luminancia / luminancia media de la región)."""
    carpeta = config.resolver(info["texturas"])
    mat = bpy.data.materials.new(nombre)
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.78
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    uv = nt.nodes.new("ShaderNodeUVMap")
    uv.uv_map = "UVMap"

    def tex(archivo, color=True):
        t = nt.nodes.new("ShaderNodeTexImage")
        img = bpy.data.images.load(str(carpeta / archivo), check_existing=True)
        if not color:
            img.colorspace_settings.name = "Non-Color"
        t.image = img
        t.extension = "EXTEND"
        nt.links.new(uv.outputs["UV"], t.inputs["Vector"])
        return t
    alb = tex("player_albedo.jpg")
    ma = tex("player_mask_a.png", False)
    mb = tex("player_mask_b.png", False)
    sep_a = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(ma.outputs["Color"], sep_a.inputs["Color"])
    sep_b = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(mb.outputs["Color"], sep_b.inputs["Color"])
    lum = nt.nodes.new("ShaderNodeRGBToBW")
    # la luminancia del juego se mide en espacio gamma: se vuelve a gamma con una potencia 1/2,2
    gam = nt.nodes.new("ShaderNodeMath")
    gam.operation = "POWER"
    gam.inputs[1].default_value = 1 / 2.2
    nt.links.new(alb.outputs["Color"], lum.inputs["Color"])
    nt.links.new(lum.outputs["Val"], gam.inputs[0])
    regiones = [("camiseta", sep_a, "Red"), ("short", sep_a, "Green"), ("medias", sep_a, "Blue"),
                ("botines", ma, "Alpha"), ("piel", sep_b, "Red"), ("pelo", sep_b, "Green")]
    acum = None
    peso = None
    for reg, fuente, canal in regiones:
        col = _srgb_a_lineal(colores.get(reg, UNIFORME_DEFECTO[reg]))
        sh = nt.nodes.new("ShaderNodeMath")
        sh.operation = "DIVIDE"
        sh.inputs[1].default_value = info["luma"][reg]
        nt.links.new(gam.outputs["Value"], sh.inputs[0])
        cl = nt.nodes.new("ShaderNodeMath")
        cl.operation = "MINIMUM"
        cl.inputs[1].default_value = 1.6
        nt.links.new(sh.outputs["Value"], cl.inputs[0])
        m = nt.nodes.new("ShaderNodeMath")  # factor = máscara × sombreado
        m.operation = "MULTIPLY"
        salida_mascara = fuente.outputs[canal] if canal != "Alpha" else fuente.outputs["Alpha"]
        nt.links.new(salida_mascara, m.inputs[0])
        nt.links.new(cl.outputs["Value"], m.inputs[1])
        c = nt.nodes.new("ShaderNodeMix")
        c.data_type = "RGBA"
        c.blend_type = "MULTIPLY"
        c.inputs["Factor"].default_value = 1.0
        c.inputs["A"].default_value = (1, 1, 1, 1)
        c.inputs["B"].default_value = (*col, 1)
        sc = nt.nodes.new("ShaderNodeVectorMath")
        sc.operation = "SCALE"
        nt.links.new(c.outputs["Result"], sc.inputs[0])
        nt.links.new(m.outputs["Value"], sc.inputs["Scale"])
        if acum is None:
            acum = sc.outputs["Vector"]
        else:
            ad = nt.nodes.new("ShaderNodeVectorMath")
            ad.operation = "ADD"
            nt.links.new(acum, ad.inputs[0])
            nt.links.new(sc.outputs["Vector"], ad.inputs[1])
            acum = ad.outputs["Vector"]
        mm = nt.nodes.new("ShaderNodeMath")
        mm.operation = "ADD"
        if peso is None:
            mm.inputs[0].default_value = 0.0
        else:
            nt.links.new(peso, mm.inputs[0])
        nt.links.new(salida_mascara, mm.inputs[1])
        peso = mm.outputs["Value"]
    # donde no hay ninguna región, queda el albedo original
    resto = nt.nodes.new("ShaderNodeMath")
    resto.operation = "SUBTRACT"
    resto.inputs[0].default_value = 1.0
    resto.use_clamp = True
    nt.links.new(peso, resto.inputs[1])
    base = nt.nodes.new("ShaderNodeVectorMath")
    base.operation = "SCALE"
    nt.links.new(alb.outputs["Color"], base.inputs[0])
    nt.links.new(resto.outputs["Value"], base.inputs["Scale"])
    fin = nt.nodes.new("ShaderNodeVectorMath")
    fin.operation = "ADD"
    nt.links.new(acum, fin.inputs[0])
    nt.links.new(base.outputs["Vector"], fin.inputs[1])
    nt.links.new(fin.outputs["Vector"], bsdf.inputs["Base Color"])
    mat["estudio"] = {"color": list(colores.get("camiseta", UNIFORME_DEFECTO["camiseta"])), "rugosidad": 0.78,
                      "metal": 0.0, "emision": None, "fuerza": 0.0, "alfa": 1.0}
    return mat


def crear(spec: dict, fps: int = 30, col=None) -> dict:
    """Crea un personaje (copia liviana del prototipo) y programa sus acciones. Devuelve sus datos."""
    lib = biblioteca(spec.get("modelo", "futbol:jugador"))
    info = lib["info"]
    col = col or K.coleccion("personajes")
    pid = spec["id"]
    raiz = bpy.data.objects.new(f"PJ_{pid}", None)
    raiz.empty_display_type = "ARROWS"
    col.objects.link(raiz)
    # copia de la jerarquía Rig → TripoBody → Armature → malla (malla y armadura comparten datos con el prototipo)
    copias = {}
    proto = lib["raiz"]

    def copiar(o, padre):
        n = o.copy()
        if o.type == "ARMATURE":
            n.animation_data_clear()
        col.objects.link(n)
        n.parent = padre
        copias[o.name.split(".")[0]] = n
        for h in o.children:
            if h.name.split(".")[0] in info["ocultar"] or h.type == "EMPTY" and "PhysicalBone" in h.name:
                continue
            copiar(h, n)
        return n
    rig = copiar(proto, raiz)
    rig.location = (0, 0, 0)
    arm = copias[info["armadura"]]
    malla = copias[info["malla"]]
    for m in malla.modifiers:
        if m.type == "ARMATURE":
            m.object = arm
    malla.data = malla.data  # (compartida)
    mat = _material_uniforme(f"uniforme_{pid}", info, spec.get("uniforme", {}))
    malla.material_slots[0].link = "OBJECT"
    malla.material_slots[0].material = mat
    arm.animation_data_create()
    # mismo truco de giro: el Rig de Godot viene con Y arriba ya convertido; +X es el frente
    pista = arm.animation_data.nla_tracks.new()
    pista.name = "acciones"
    pos = Vector((0, 0, 0))
    rumbo = 0.0
    tramos = []
    ultimo_fin = 1
    for i, ac in enumerate(spec.get("acciones", [])):
        accion = bpy.data.actions.get(ac["clip"])
        if accion is None:
            raise KeyError(f"El clip {ac['clip']} no está en {spec.get('modelo')} (ver catalogo/futbol.json)")
        f0 = int(round(ac["inicio_s"] * fps)) + 1
        a0, a1 = accion.frame_range
        vel = ac.get("velocidad", 1.0)
        rep = ac.get("repetir", 1)
        if ac.get("encadenar") and tramos:
            cadera_fin, rumbo = _fin_de_tramo(arm, raiz, tramos[-1], info["cadera"])
            if "mirando_deg" in ac:
                rumbo = math.radians(ac["mirando_deg"])
            ini = Matrix.Rotation(rumbo, 3, "Z") @ _cadera_local(arm, raiz, accion, a0, info["cadera"])
            pos = cadera_fin - ini
        else:
            if "pos" in ac:
                p = ac["pos"]
                pos = Vector((p[0], p[1], p[2] if len(p) > 2 else 0.0))
            if "mirando_deg" in ac:
                rumbo = math.radians(ac["mirando_deg"])
        raiz.location = pos
        raiz.rotation_euler = (0, 0, rumbo)
        raiz.keyframe_insert("location", frame=f0)
        raiz.keyframe_insert("rotation_euler", frame=f0)
        if tramos and tramos[-1]["strip"].frame_end > f0 - 0.01:
            # el tramo anterior (o sus repeticiones) se corta donde empieza este
            tramos[-1]["strip"].frame_end = f0 - 0.01
            tramos[-1]["fin"] = f0 - 0.01
        st = pista.strips.new(f"{i:02d}_{ac['clip']}", f0, accion)
        st.scale = 1.0 / vel
        st.repeat = rep
        st.blend_in = st.blend_out = 0
        st.extrapolation = "HOLD"
        fin = st.frame_end
        tramos.append({"accion": accion, "f0": f0, "fin": fin, "pos": pos.copy(), "rumbo": rumbo, "strip": st})
        ultimo_fin = fin
    # las claves de ubicación son escalones (cada tramo arranca en su lugar)
    if raiz.animation_data and raiz.animation_data.action:
        for fc in K._fcurves(raiz.animation_data.action):
            for k in fc.keyframe_points:
                k.interpolation = "CONSTANT"
    # recortar cada tramo para que no se pise con el siguiente
    for a, b in zip(tramos, tramos[1:]):
        if a["strip"].frame_end > b["f0"]:
            a["strip"].frame_end = b["f0"]
            a["fin"] = b["f0"]
    return {"id": pid, "raiz": raiz, "armadura": arm, "malla": malla, "tramos": tramos, "info": info,
            "fin": ultimo_fin}


def _cadera_local(arm, raiz, accion, frame: float, cadera: str) -> Vector:
    """Posición de la cadera en el espacio de la raíz del personaje para un cuadro del clip (sin NLA)."""
    sc = bpy.context.scene
    ad = arm.animation_data
    vieja, nla = ad.action, ad.use_nla
    ad.use_nla = False
    ad.action = accion
    sc.frame_set(int(round(frame)))
    rel = raiz.matrix_world.inverted() @ arm.matrix_world
    p = rel @ arm.pose.bones[cadera].head
    ad.action = vieja
    ad.use_nla = nla
    return Vector((p.x, p.y, 0.0))


def _fin_de_tramo(arm, raiz, tramo, cadera: str):
    """Dónde quedó la cadera (en el mundo, sobre el piso) al terminar el tramo, y el rumbo."""
    accion = tramo["accion"]
    a0, a1 = accion.frame_range
    fin_clip = min(a1, a0 + (tramo["fin"] - tramo["f0"]) / max(1e-6, tramo["strip"].scale))
    loc = _cadera_local(arm, raiz, accion, fin_clip, cadera)
    rot = Matrix.Rotation(tramo["rumbo"], 3, "Z")
    return tramo["pos"] + rot @ loc, tramo["rumbo"]


def punto_hueso(pj: dict, hueso: str, frame: int) -> Vector:
    sc = bpy.context.scene
    sc.frame_set(frame)
    arm = pj["armadura"]
    return (arm.matrix_world @ arm.pose.bones[hueso].head).copy()
