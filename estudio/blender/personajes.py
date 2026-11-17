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
        "raices": "mixamo:futbol_free_kick_swipe/raices_clips.json",
        "raiz": "Rig", "armadura": "Armature", "malla": "TripoBodyMesh", "ocultar": ["Icosphere"],
        "cadera": "mixamorig_Hips", "pie_der": "mixamorig_RightToeBase", "pie_izq": "mixamorig_LeftToeBase",
        "cabeza": "mixamorig_Head", "mano_der": "mixamorig_RightHand",
        "luma": {"camiseta": 0.203, "short": 0.286, "medias": 0.785, "botines": 0.088, "piel": 0.492, "pelo": 0.18},
    },
}
MODELOS["mixamo:jefa"] = {
    "tipo": "mixamo65", "ref": "mixamo:modelos_pelicula/jefa_o_novia.glb", "escala": 1.70,
    "ocultar": ["Icosphere"], "cadera": "mixamorig:Hips", "pie_der": "mixamorig:RightToeBase",
    "pie_izq": "mixamorig:LeftToeBase", "cabeza": "mixamorig:Head", "mano_der": "mixamorig:RightHand",
    "frente": math.pi / 2,   # el modelo mira a −Y; con mirando_deg = 0 debe mirar a +X
    "adelante_deg": -90,     # hacia dónde mira el modelo en su propio marco (0 = +X, −90 = −Y); lo usan las cámaras
}
for _id, _ref in (("ch49", "extraction:characters/personajes/Ch49.glb"), ("ch15", "extraction:characters/personajes/Ch15.glb"),
                  ("ch35", "extraction:characters/personajes/Ch35.glb"), ("operador", "nexus:personajes/operador_character.fbx")):
    MODELOS[f"soldado:{_id}"] = {
        "tipo": "mixamo65", "ref": _ref, "escala": 1.0,          # miden ~1,8 m nativos (medido)
        "ocultar": ["Icosphere"], "cadera": "mixamorig:Hips", "pie_der": "mixamorig:RightToeBase",
        "pie_izq": "mixamorig:LeftToeBase", "cabeza": "mixamorig:Head", "mano_der": "mixamorig:RightHand",
        "frente": math.pi / 2, "adelante_deg": -90,              # miran a −Y (medido con el avance de «walk_forward»)
        "clip_arma": "mixamo:packs/Pro_Rifle_Pack/idle_aiming.fbx", "frame_arma": 20,
    }
# Protagonistas de «Operación Tren Fantasma» (Tripo3D → FBX, normalizados a 1 m de alto) y piloto de Dream Rally.
for _id, _ref, _alto in (("lucia", "mixamo:personajes_pelicula/protagonista_femenina/tripo_convert_5669269a-5647-4c37-ad7b-71abe72fe517.fbx", 1.68),
                         ("mateo", "mixamo:personajes_pelicula/protagonista_masculino/tripo_convert_83c2a1e7-3bcc-46c6-b430-400ef54f0b81.fbx", 1.80)):
    MODELOS[f"pelicula:{_id}"] = {
        "tipo": "mixamo65", "ref": _ref, "escala": _alto,        # miden 1,0 m al importar (medido)
        "ocultar": [], "cadera": "mixamorig:Hips", "pie_der": "mixamorig:RightToeBase", "pie_izq": "mixamorig:LeftToeBase",
        "cabeza": "mixamorig:Head", "mano_der": "mixamorig:RightHand", "frente": math.pi / 2, "adelante_deg": -90,
        "clip_arma": "mixamo:packs/Pro_Rifle_Pack/idle_aiming.fbx", "frame_arma": 20,
    }
# «Al vacío» (p007): Messi y Cristiano Ronaldo, modelos Tripo3D con esqueleto mixamorig que mandó el dueño (fuera de Git)
for _id, _ref, _alto, _tex in (
        ("messi", "mixamo:personajes_pelicula/messi/tripo_convert_db2fb7b2-b201-48ab-90fe-625fa86f28f4.fbx", 1.70, {}),
        ("cristiano", "mixamo:personajes_pelicula/cristiano/tripo_convert_14aa6baf-3faf-4c85-b305-f9d50faf739f.fbx", 1.87,
         {"basecolor": "mixamo:personajes_pelicula/cristiano/basecolor_nombre_corregido.png"})):   # nombre de la espalda legible
    MODELOS[f"pelicula:{_id}"] = {
        "tipo": "mixamo65", "ref": _ref, "escala": _alto, "ocultar": [], "cadera": "mixamorig:Hips",
        "pie_der": "mixamorig:RightToeBase", "pie_izq": "mixamorig:LeftToeBase", "cabeza": "mixamorig:Head",
        "mano_der": "mixamorig:RightHand", "frente": math.pi / 2, "adelante_deg": -90, "texturas": _tex,
        "sin_metal": True,
    }
MODELOS["rally:piloto"] = {
    "tipo": "mixamo65", "ref": "rally:godot/game/models/pilot.glb", "escala": 1.0, "ocultar": ["Icosphere"],
    "renombrar_huesos": ("mixamorig6:", "mixamorig:"),          # el piloto del juego usa otro prefijo
    "cadera": "mixamorig:Hips", "pie_der": "mixamorig:RightToeBase", "pie_izq": "mixamorig:LeftToeBase",
    "cabeza": "mixamorig:Head", "mano_der": "mixamorig:RightHand",
    # el piloto del juego viene de Godot, que mira a −Z: en Blender queda mirando a +Y (al revés que los de Mixamo);
    # con «frente» = π/2 los moteros iban sentados al revés en la moto
    "frente": -math.pi / 2, "adelante_deg": 90,
}
from estudio.blender.stickman import REFS as SM_REFS  # noqa: E402  (los modelos definitivos, una sola lista)
# «Dúo Cero» (p009): Stickman blancos del dueño (0,98 m al importar, miran a −Y; los definitivos del 17/11/2026). Vestuario, pelo y cara 2D los pone
# estudio/blender/stickman.py; «alto_m» del personaje fija su estatura.
for _id, _alto in (("masculino", 0.979), ("femenino", 0.979)):
    MODELOS[f"stickman:{_id}"] = {
        "tipo": "mixamo65", "stickman": True, "alto_modelo": _alto, "escala": 1.75 / _alto, "ocultar": [],
        "cadera": "mixamorig:Hips", "pie_der": "mixamorig:RightToeBase", "pie_izq": "mixamorig:LeftToeBase",
        "cabeza": "mixamorig:Head", "mano_der": "mixamorig:RightHand", "frente": math.pi / 2, "adelante_deg": -90,
        "clip_arma": "mixamo:packs/Pro_Rifle_Pack/idle_aiming.fbx", "frame_arma": 20, "sin_metal": True,
    }
MODELOS["stickman:masculino"]["ref"] = SM_REFS["stickman:masculino"]
MODELOS["stickman:femenino"]["ref"] = SM_REFS["stickman:femenino"]
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


def _aparecer(pj: dict, spec: dict, fps: int):
    """"aparece_s": el personaje está oculto hasta ese momento (p. ej. se baja de un auto donde iba otro modelo)."""
    if spec.get("aparece_s") is None:
        return
    f = int(round(spec["aparece_s"] * fps)) + 1
    pila = [pj["raiz"]]
    while pila:
        o = pila.pop()
        pila.extend(o.children)
        if o.type == "MESH":
            for fr, v in ((1, True), (f, False)):
                o.hide_render = o.hide_viewport = v
                o.keyframe_insert("hide_render", frame=fr)
                o.keyframe_insert("hide_viewport", frame=fr)


def crear(spec: dict, fps: int = 30, col=None) -> dict:
    """Crea un personaje (copia liviana del prototipo) y programa sus acciones. Devuelve sus datos."""
    if MODELOS[spec.get("modelo", "futbol:jugador")].get("tipo") == "mixamo65":
        pj = _crear_mixamo(spec, fps, col)
        if pj["info"].get("stickman"):
            from estudio.blender import stickman as SM
            SM.preparar(pj, spec, fps, int(spec.get("_nf") or bpy.context.scene.frame_end))
        _aparecer(pj, spec, fps)
        return pj
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
    raices = _raices(info)
    pos = Vector((0, 0, 0))
    rumbo = 0.0
    tramos = []
    ultimo_fin = 1
    for i, ac in enumerate(spec.get("acciones", [])):
        accion = bpy.data.actions.get(ac["clip"])
        if accion is None:
            raise KeyError(f"El clip {ac['clip']} no está en {spec.get('modelo')} (ver catalogo/futbol.json)")
        f0 = int(round(ac["inicio_s"] * fps)) + 1
        vel = ac.get("velocidad", 1.0)
        rep = ac.get("repetir", 1)
        if ac.get("encadenar") and tramos:
            pos, rumbo = tramos[-1]["pos"], tramos[-1]["rumbo"]  # se recalcula abajo con el recorrido real
        else:
            if "pos" in ac:
                p = ac["pos"]
                pos = Vector((p[0], p[1], p[2] if len(p) > 2 else 0.0))
            if "mirando_deg" in ac:
                rumbo = math.radians(ac["mirando_deg"])
        if tramos and tramos[-1]["strip"].frame_end > f0 - 0.01:
            # el tramo anterior (o sus repeticiones) se corta donde empieza este
            tramos[-1]["strip"].frame_end = f0 - 0.01
            tramos[-1]["fin"] = f0 - 0.01
        st = pista.strips.new(f"{i:02d}_{ac['clip']}", f0, accion)
        st.scale = 1.0 / vel
        st.repeat = rep
        st.blend_in = st.blend_out = 0
        st.extrapolation = "HOLD"
        if ac.get("desde_clip_s"):
            st.action_frame_start = st.action_frame_start + ac["desde_clip_s"] * fps
        tramos.append({"accion": accion, "f0": f0, "fin": st.frame_end, "pos": pos.copy(), "rumbo": rumbo,
                       "strip": st, "raiz": raices.get(ac["clip"], {}), "vel": vel, "rep": rep})
    # recortes por superposición ya aplicados: ahora el desplazamiento (root_path) cuadro por cuadro
    for k, tr in enumerate(tramos):
        f_fin = int(tramos[k + 1]["f0"]) - 1 if k + 1 < len(tramos) else int(tr["fin"])
        if k > 0 and spec["acciones"][k].get("encadenar"):
            tr["pos"], tr["rumbo"] = tramos[k - 1]["pos_fin"], (math.radians(spec["acciones"][k]["mirando_deg"])
                                                                 if "mirando_deg" in spec["acciones"][k]
                                                                 else tramos[k - 1]["rumbo_fin"])
        pf, rf = tr["pos"], tr["rumbo"]
        for f in range(tr["f0"], f_fin + 1):
            pf, rf = _raiz_en(tr, (f - tr["f0"]) / fps)
            raiz.location = pf
            raiz.rotation_euler = (0, 0, rf)
            raiz.keyframe_insert("location", frame=f)
            raiz.keyframe_insert("rotation_euler", frame=f)
        tr["pos_fin"], tr["rumbo_fin"] = pf, rf
        ultimo_fin = max(ultimo_fin, f_fin)
    if spec.get("sobre"):                    # viaja encima de un objeto (plataforma, ascensor): acciones en su marco
        padre = bpy.data.objects.get(spec["sobre"])
        if padre is None:
            raise KeyError(f"{pid}: no existe el objeto '{spec['sobre']}' para viajar encima")
        raiz.parent = padre
    return {"id": pid, "raiz": raiz, "armadura": arm, "malla": malla, "tramos": tramos, "info": info,
            "fin": ultimo_fin}


_RAICES: dict[str, dict] = {}


def _raices(info: dict) -> dict:
    ref = info.get("raices")
    if not ref:
        return {}
    if ref not in _RAICES:
        import json
        _RAICES[ref] = json.loads(config.resolver(ref).read_text())
    return _RAICES[ref]


def _raiz_en(tr: dict, t: float):
    """Posición y rumbo de la raíz a t segundos del inicio del tramo, como SpActor.body_at del juego:
    origen + adelante·x + derecha·y (root_path a 30 fps) y giro del cuerpo si el clip es de tipo "turn"."""
    datos = tr["raiz"]
    rp = datos.get("root_path") or []
    t_clip = t * tr["vel"] + tr.get("desde", 0.0)
    rumbo0 = tr["rumbo"]
    if len(rp) < 2:
        return tr["pos"].copy(), rumbo0
    largo = (len(rp) - 1) / 30.0
    vuelta = int(t_clip // largo) if t_clip >= largo else 0
    vuelta = min(vuelta, tr["rep"] - 1) if tr["rep"] > 1 else 0
    tl = min(t_clip - vuelta * largo, largo)
    fi = tl * 30.0
    i = min(int(fi), len(rp) - 2)
    a = fi - i
    rx = rp[i][0] + (rp[i + 1][0] - rp[i][0]) * a + vuelta * rp[-1][0]
    ry = rp[i][1] + (rp[i + 1][1] - rp[i][1]) * a + vuelta * rp[-1][1]
    adelante = Vector((math.cos(rumbo0), math.sin(rumbo0), 0))
    derecha = Vector((math.sin(rumbo0), -math.cos(rumbo0), 0))
    pos = tr["pos"] + adelante * rx + derecha * ry
    rumbo = rumbo0
    hp = datos.get("heading_path") or []
    if datos.get("meta", {}).get("heading_mode") == "turn" and len(hp) > 1:
        # igual que ActionMotion.heading_rel: grados, relativos al primer cuadro, + = izquierda
        fh = min(tl * 30.0, len(hp) - 1.0)
        j = min(int(fh), len(hp) - 2)
        rumbo = rumbo0 + math.radians(hp[j] + (hp[j + 1] - hp[j]) * (fh - j) - hp[0])
    return pos, rumbo


_RETARGETS: dict[tuple, bpy.types.Action] = {}


def _rt(modelo: str, ref: str, arm, raiz, info: dict, dueno: str, hasta_s: float | None = None):
    """Acción retargeteada de un clip FBX de Mixamo para ESTE personaje (con caché por personaje). `hasta_s`: sólo
    los primeros segundos del clip (los clips de 40 s cuestan minutos y muchas veces se usan 10)."""
    from estudio.blender import retarget as R
    clave = (dueno, ref, hasta_s)
    if ref.startswith("futbol:") and (clave not in _RETARGETS or _RETARGETS[clave].name not in bpy.data.actions):
        # clip del juego (futbolista de Free Kick Swipe, huesos «mixamorig_X»): se retargetea desde la biblioteca
        lib = biblioteca("futbol:jugador")
        origen = lib["armadura"]
        clip = ref.split(":", 1)[1]
        acc = bpy.data.actions[clip]
        lib["coleccion"].hide_viewport = False           # oculta, no se evalúa la pose
        raiz.rotation_euler = (0, 0, 0)
        raiz.location = (0, 0, 0)
        try:
            nueva = R.retarget(origen, acc, arm, f"rt_{dueno}_{clip}", info["cadera"],
                               nombres={b.name: b.name.replace("mixamorig:", "mixamorig_") for b in arm.data.bones},
                               cadera_origen="mixamorig_Hips",
                               # el futbolista mira a +X (adelante_deg 0); el modelo Mixamo, a su «adelante_deg» (−90 = −Y)
                               giro_z=math.radians(info.get("adelante_deg", -90.0)))
        finally:
            lib["coleccion"].hide_viewport = True
        nueva["futbol_clip"] = clip
        _RETARGETS[clave] = nueva
        return nueva
    if clave not in _RETARGETS or _RETARGETS[clave].name not in bpy.data.actions:
        antes = set(bpy.data.actions)
        tmp = I.importar(ref)
        acc = next(a for a in bpy.data.actions if a not in antes)
        tarm = next(o for o in tmp if o.type == "ARMATURE")
        raiz.rotation_euler = (0, 0, 0)
        raiz.location = (0, 0, 0)
        nombre = f"rt_{dueno}_{Path(ref).stem}"
        rango = None
        if hasta_s:
            f0c = int(acc.frame_range[0])
            rango = (f0c, min(int(acc.frame_range[1]), f0c + int(round(hasta_s * 30))))
        _RETARGETS[clave] = R.retarget(tarm, acc, arm, nombre, info["cadera"], fotogramas=rango)
        for o in tmp:
            bpy.data.objects.remove(o)
        for ac in list(bpy.data.actions):          # el clip original ya no hace falta (ahorra memoria)
            if ac == acc:
                bpy.data.actions.remove(ac)
    return _RETARGETS[clave]


def _giro_extra(ac: dict):
    """Giro adicional del cuerpo (radianes) a t s del inicio del tramo: "giro_deg" entre "giro_desde_s" y
    "giro_desde_s" + "giro_dur_s" (suave)."""
    g = math.radians(ac.get("giro_deg", 0.0))
    a = ac.get("giro_desde_s", 0.0)
    d = max(1e-3, ac.get("giro_dur_s", 0.5))

    def f(t):
        u = min(1.0, max(0.0, (t - a) / d))
        return g * u * u * (3 - 2 * u)
    return f


# Poses superpuestas a un clip (sólo los huesos que nombran; el resto sigue el clip). Direcciones en el marco del
# personaje: +Z arriba, −Y adelante (los modelos Mixamo miran a −Y), +X su izquierda.
POSES = {
    # «Dúo Cero»: la radio en la mano (a la altura del pecho), la radio en la boca y la tableta con las dos manos
    "radio_mano": {
        "brazos": {"mixamorig:RightArm": (-0.35, -0.25, -0.9), "mixamorig:RightForeArm": (0.25, -0.75, 0.6),
                   "mixamorig:RightHand": (0.3, -0.6, 0.75)},
        "cerrar": ("Index", "Middle", "Ring", "Pinky"), "abrir": (), "cabeza": -8.0,
    },
    "radio_boca": {
        "brazos": {"mixamorig:RightArm": (-0.25, -0.45, -0.85), "mixamorig:RightForeArm": (0.35, -0.45, 0.82),
                   "mixamorig:RightHand": (0.35, -0.35, 0.87)},
        "cerrar": ("Index", "Middle", "Ring", "Pinky"), "abrir": (), "cabeza": 0.0,
    },
    "tableta": {
        "brazos": {"mixamorig:LeftArm": (0.25, -0.35, -0.9), "mixamorig:LeftForeArm": (-0.2, -0.95, 0.15),
                   "mixamorig:LeftHand": (-0.25, -0.95, 0.15), "mixamorig:RightArm": (-0.25, -0.35, -0.9),
                   "mixamorig:RightForeArm": (0.2, -0.95, 0.15), "mixamorig:RightHand": (0.25, -0.95, 0.15)},
        "cerrar": (), "abrir": ("Thumb", "Index", "Middle", "Ring", "Pinky"), "cabeza": -24.0,
    },
    "dedos_al_cielo": {     # el festejo de Messi: los dos índices al cielo, la cabeza arriba
        "brazos": {"mixamorig:LeftArm": (0.25, -0.15, 1.0), "mixamorig:LeftForeArm": (0.12, -0.12, 1.0),
                   "mixamorig:LeftHand": (0.05, -0.1, 1.0), "mixamorig:RightArm": (-0.25, -0.15, 1.0),
                   "mixamorig:RightForeArm": (-0.12, -0.12, 1.0), "mixamorig:RightHand": (-0.05, -0.1, 1.0)},
        "cerrar": ("Thumb", "Middle", "Ring", "Pinky"), "abrir": ("Index",),
        "cabeza": 28.0,
    },
    "pose_a": {             # la parada de Cristiano antes del tiro libre: piernas abiertas, brazos rectos un poco afuera
        "brazos": {"mixamorig:LeftArm": (0.3, 0.02, -0.95), "mixamorig:LeftForeArm": (0.28, 0.0, -0.96),
                   "mixamorig:LeftHand": (0.25, 0.0, -0.97), "mixamorig:RightArm": (-0.3, 0.02, -0.95),
                   "mixamorig:RightForeArm": (-0.28, 0.0, -0.96), "mixamorig:RightHand": (-0.25, 0.0, -0.97)},
        "cerrar": (), "abrir": ("Thumb", "Index", "Middle", "Ring", "Pinky"),
        "cabeza": 6.0,
    },
    "siu": {                # el aterrizaje del «Siu» de Cristiano: brazos rectos hacia abajo y afuera, pecho arriba
        "brazos": {"mixamorig:LeftArm": (0.62, -0.05, -0.78), "mixamorig:LeftForeArm": (0.6, -0.05, -0.8),
                   "mixamorig:LeftHand": (0.55, -0.05, -0.83), "mixamorig:RightArm": (-0.62, -0.05, -0.78),
                   "mixamorig:RightForeArm": (-0.6, -0.05, -0.8), "mixamorig:RightHand": (-0.55, -0.05, -0.83)},
        "cerrar": (), "abrir": ("Thumb", "Index", "Middle", "Ring", "Pinky"),
        "cabeza": 14.0,
    },
}


def _pose_encima(arm, nombre: str, f0: int, f1: int, fps: int, pid: str):
    """Pista NLA encima de las acciones con la pose `nombre` en los huesos de brazos, dedos y cabeza (entra y sale
    en 0,35 s). Las rotaciones se calculan una vez, con el cuerpo en reposo."""
    from mathutils import Quaternion
    pose = POSES[nombre]
    sc = bpy.context.scene
    ad = arm.animation_data
    viejo_nla = ad.use_nla
    ad.use_nla = False
    vieja = ad.action
    ad.action = None
    for pb in arm.pose.bones:
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.location = (0, 0, 0)
    bpy.context.view_layer.update()
    rot = {}
    raiz = arm.parent
    while raiz is not None and raiz.parent is not None and not raiz.name.startswith("PJ_"):
        raiz = raiz.parent
    a_personaje = ((raiz.matrix_world.inverted() if raiz else Matrix()) @ arm.matrix_world).to_3x3()
    a_armadura = a_personaje.inverted()
    for nb, d in pose["brazos"].items():          # padres primero (el orden del diccionario)
        pb = arm.pose.bones.get(nb)
        if pb is None:
            continue
        objetivo = (a_armadura @ Vector(d)).normalized()
        actual = (pb.matrix.to_3x3() @ Vector((0, 1, 0))).normalized()
        delta = actual.rotation_difference(objetivo)
        m = pb.matrix.copy()
        nueva = delta.to_matrix().to_4x4() @ Matrix.Translation(-m.translation) @ m
        nueva.translation = m.translation
        pb.matrix = nueva
        bpy.context.view_layer.update()
        rot[nb] = pb.rotation_quaternion.copy()
    for pb in arm.pose.bones:
        n = pb.name
        if any(k in n for k in pose["cerrar"]) and ("Hand" in n):
            rot[n] = Quaternion((1, 0, 0), math.radians(70))
        elif any(k in n for k in pose["abrir"]) and ("Hand" in n):
            rot[n] = Quaternion()
    for nb in ("mixamorig:Neck", "mixamorig:Head"):
        if arm.pose.bones.get(nb):
            rot[nb] = Quaternion((1, 0, 0), -math.radians(pose["cabeza"] / 2))
    accion = bpy.data.actions.new(f"pose_{pid}_{nombre}")
    ad.action = accion
    for n, q in rot.items():
        pb = arm.pose.bones[n]
        pb.rotation_quaternion = q
        pb.keyframe_insert("rotation_quaternion", frame=1)
    ad.action = vieja
    ad.use_nla = viejo_nla
    pista = ad.nla_tracks.new()
    pista.name = f"pose_{nombre}"
    st = pista.strips.new(f"pose_{nombre}", f0, accion)
    try:
        st.action_slot = accion.slots[0]
    except Exception:
        pass
    st.frame_end = max(f0 + 2, f1)
    st.blend_type = "REPLACE"
    st.blend_in = st.blend_out = min(0.35 * fps, (st.frame_end - f0) / 2 - 1)
    st.extrapolation = "NOTHING"


def _arreglar_texturas(objs, info: dict):
    """Las texturas de un FBX de Tripo quedan con la ruta donde se descomprimió: si no existe, se buscan en la carpeta
    .fbm al lado del modelo. `info["texturas"]` = {parte del nombre: ref} reemplaza una (p. ej. el color corregido)."""
    base = config.resolver(info["ref"])
    fbm = base.with_suffix(".fbm")
    reemplazos = {k: config.resolver(v) for k, v in (info.get("texturas") or {}).items()}
    for o in objs:
        if o.type != "MESH":
            continue
        for m in o.data.materials:
            if not m or not m.use_nodes:
                continue
            for n in m.node_tree.nodes:
                if n.type != "TEX_IMAGE" or not n.image:
                    continue
                ruta = Path(bpy.path.abspath(n.image.filepath))
                nueva = next((r for k, r in reemplazos.items() if k in ruta.name.lower()), None)
                if nueva is None and not ruta.exists() and (fbm / ruta.name).exists():
                    nueva = fbm / ruta.name
                if nueva is not None:
                    cs = n.image.colorspace_settings.name
                    n.image = bpy.data.images.load(str(nueva), check_existing=True)
                    n.image.colorspace_settings.name = cs
            if info.get("sin_metal"):
                # el mapa metálico de Tripo pinta piel y tela de metal (se ven cromados): tela y piel no son metal
                b = next((x for x in m.node_tree.nodes if x.type == "BSDF_PRINCIPLED"), None)
                if b is not None:
                    for ent in ("Metallic", "Roughness"):
                        for l in list(b.inputs[ent].links):
                            m.node_tree.links.remove(l)
                    b.inputs["Metallic"].default_value = 0.0
                    b.inputs["Roughness"].default_value = 0.62


def _crear_mixamo(spec: dict, fps: int, col=None) -> dict:
    """Personaje con esqueleto mixamorig de 65 huesos (p. ej. la Jefa). Sus clips son FBX de Mixamo
    ("clip": "mixamo:packs/…/walking.fbx") que se RETARGETEAN al esqueleto del personaje (estudio/blender/retarget.py)."""
    from estudio.blender import retarget as R
    modelo = spec.get("modelo", "mixamo:jefa")
    info = MODELOS[modelo]
    col = col or K.coleccion("personajes")
    pid = spec["id"]
    objs = I.importar(info["ref"], col)
    raiz = bpy.data.objects.new(f"PJ_{pid}", None)
    raiz.empty_display_type = "ARROWS"
    col.objects.link(raiz)
    for o in objs:
        if o.name.split(".")[0] in info["ocultar"]:
            o.hide_render = o.hide_viewport = True
        if o.parent is None:
            o.parent = raiz
    raiz.scale = ((spec["alto_m"] / info["alto_modelo"]) if spec.get("alto_m") and info.get("alto_modelo")
                  else info["escala"],) * 3
    _arreglar_texturas(objs, info)
    arm = next(o for o in objs if o.type == "ARMATURE")
    if info.get("renombrar_huesos"):
        viejo, nuevo = info["renombrar_huesos"]
        for b in arm.data.bones:
            if b.name.startswith(viejo):
                b.name = nuevo + b.name[len(viejo):]       # Blender renombra también los grupos de vértices
    if spec.get("material"):
        mt = K.material(f"ropa_{pid}", tuple(spec["material"]["color"]), spec["material"].get("rugosidad", 0.6))
        for o in objs:
            if o.type == "MESH" and o.name.split(".")[0] not in info["ocultar"]:
                o.data.materials.clear()
                o.data.materials.append(mt)
    malla = next(o for o in objs if o.type == "MESH" and o.name.split(".")[0] not in info["ocultar"])
    arm.animation_data_create()
    arma_obj = None
    if spec.get("arma"):
        from estudio.blender import armas as AR
        ref_acc = _rt(modelo, info["clip_arma"], arm, raiz, info, pid)
        arma_obj = AR.acoplar(arm, spec["arma"], ref_acc, info.get("frame_arma", 20), col)
        arma_obj.name = f"ARMA_{pid}"
    pista = arm.animation_data.nla_tracks.new()
    pista.name = "acciones"
    pista_base = pista
    pos = Vector((0, 0, 0))
    rumbo = 0.0
    tramos = []
    llaves = []
    for i, ac in enumerate(spec.get("acciones", [])):
        ref = ac["clip"]
        accion = _rt(modelo, ref, arm, raiz, info, f"{pid}", ac.get("clip_hasta_s"))
        f0 = int(round(ac["inicio_s"] * fps)) + 1
        if ac.get("encadenar") and tramos:
            if tramos[-1].get("futbol"):              # clip del juego: termina donde lo dejó su root_path al cortarse
                _tf = (f0 - tramos[-1]["f0"]) / fps
                _p, _r = _raiz_en(tramos[-1]["futbol"], _tf)
                tramos[-1]["pos_fin"], tramos[-1]["rumbo_fin"] = _p, _r + tramos[-1]["futbol"].get("extra", lambda s: 0.0)(_tf)
            pos, rumbo = tramos[-1]["pos_fin"], tramos[-1]["rumbo_fin"]
        if "pos" in ac:
            p = ac["pos"]
            pos = Vector((p[0], p[1], p[2] if len(p) > 2 else 0.0))
        rumbo_ant = rumbo
        if "mirando_deg" in ac:
            rumbo = math.radians(ac["mirando_deg"])
        mez = int(round(ac.get("mezcla_s", spec.get("mezcla_s", 0.0)) * fps)) if tramos else 0
        if mez > 0:
            # fundido entre clips: el nuevo va en su propia pista, arriba, y entra en `mez` cuadros sobre el anterior
            if tramos[-1]["strip"].frame_end > f0 + 1:
                tramos[-1]["strip"].frame_end = f0 + 1
                tramos[-1]["fin"] = f0 + 1
            # los clips siguientes van en esta pista (la de arriba reemplaza a las de abajo desde que empieza)
            pista = arm.animation_data.nla_tracks.new(prev=pista)
            pista.name = f"acciones_{i:02d}"
            st = pista.strips.new(f"{i:02d}_{accion.name}", max(1, f0 - mez), accion)
        else:
            if tramos and tramos[-1]["strip"].frame_end > f0 - 0.01:
                tramos[-1]["strip"].frame_end = f0 - 0.01
                tramos[-1]["fin"] = f0 - 0.01
            st = pista.strips.new(f"{i:02d}_{accion.name}", f0, accion)
        try:
            st.action_slot = accion.slots[0]
        except Exception:
            pass
        st.scale = 1.0 / ac.get("velocidad", 1.0)
        st.repeat = ac.get("repetir", 1)
        st.blend_in = st.blend_out = 0
        # la pista de abajo sostiene antes y después; las de arriba sólo desde su primer clip en adelante
        st.extrapolation = "HOLD" if pista == pista_base else "HOLD_FORWARD"
        if mez > 0:
            st.blend_in = max(0.0, min(float(mez), (st.frame_end - st.frame_start) / 2 - 1))
        d = Vector(accion.get("desplazamiento_cadera_m", (0, 0, 0)))
        d.z = 0
        vueltas = max(1, int(st.repeat))
        giro = Matrix.Rotation(rumbo + info["frente"], 3, "Z")
        pos_fin = pos + giro @ (d * vueltas)
        tramos.append({"accion": accion, "f0": f0, "fin": st.frame_end, "pos": pos.copy(), "rumbo": rumbo,
                       "strip": st, "pos_fin": pos_fin, "rumbo_fin": rumbo})
        if accion.get("futbol_clip"):
            # clip del juego: la raíz sigue su root_path cuadro a cuadro (como el futbolista), no la cadera
            raices = _raices(MODELOS["futbol:jugador"])
            desde = float(ac.get("desde_s", 0.0))          # entra a mitad del clip (como ShotCatalog.start_time_near)
            fut = {"raiz": raices.get(accion["futbol_clip"], {}), "vel": ac.get("velocidad", 1.0),
                   "rep": int(st.repeat), "pos": pos.copy(), "rumbo": rumbo, "desde": desde}
            if desde > 0:
                a0 = st.action_frame_start
                st.action_frame_start = a0 + desde * fps
                tramos[-1]["fin"] = st.frame_end
            tramos[-1]["futbol"] = fut
            largo_f = int(st.frame_end - f0)
            extra = _giro_extra(ac)
            # empalme: desde donde estaba parado hasta la carrera del clip, en `empalme_s`
            ofs = Vector((0, 0, 0))
            if ac.get("desde_pos") is not None:
                p_ini, _r = _raiz_en(fut, 0.0)
                q = ac["desde_pos"]
                ofs = Vector((q[0], q[1], 0.0)) - p_ini
            emp = max(1e-3, float(ac.get("empalme_s", 0.45)))
            mover = ac.get("mover_a")                    # SpActor.move_to del juego: trota de pos a mover_a (clip en bucle)
            mover_s = float(ac.get("mover_s", 1.0))
            for j in range(largo_f + 1):
                if mover is not None:
                    u = min(1.0, (j / fps) / max(1e-3, mover_s))
                    pj_ = pos + (Vector((mover[0], mover[1], 0.0)) - pos) * u
                    llaves.append((f0 + j, pj_, rumbo + info["frente"]))
                    continue
                pj_, rj = _raiz_en(fut, j / fps)
                u = min(1.0, (j / fps) / emp)
                pj_ = pj_ + ofs * (1 - u * u * (3 - 2 * u))
                llaves.append((f0 + j, pj_, rj + extra(j / fps) + info["frente"]))
            pfin, rfin = _raiz_en(fut, largo_f / fps)
            if mover is not None:
                pfin, rfin = Vector((mover[0], mover[1], 0.0)), rumbo
                fut["mover"] = (pos.copy(), pfin.copy(), mover_s)
            tramos[-1]["pos_fin"], tramos[-1]["rumbo_fin"] = pfin, rfin + extra(1e9)
            fut["extra"] = extra
            continue
        if ac.get("giro_deg"):
            # giro en el lugar durante el clip (p. ej. el salto con media vuelta del «Siu»)
            extra = _giro_extra(ac)
            largo_f = int(st.frame_end - f0)
            d_cad = Vector(accion.get("desplazamiento_cadera_m", (0, 0, 0)))
            for j in range(largo_f + 1):
                llaves.append((f0 + j, pos, rumbo + extra(j / fps) + info["frente"]))
            tramos[-1]["pos_fin"], tramos[-1]["rumbo_fin"] = pos, rumbo + extra(1e9)
            continue
        # en cada repetición la cadera vuelve al punto de partida del clip: el personaje avanza lo que avanzó el ciclo
        por_ciclo = (st.frame_end - st.frame_start) / vueltas
        # "giro_s": el rumbo pasa del anterior al nuevo de forma suave durante los primeros `giro_s` segundos del tramo
        nf = int(round(ac.get("giro_s", 0.0) * fps)) if (tramos[:-1] and "pos" not in ac) else 0
        nf = min(nf, int(por_ciclo) - 1)
        dr = (rumbo - rumbo_ant + math.pi) % math.tau - math.pi
        for k in range(vueltas):
            r = rumbo + info["frente"]
            if k == 0 and nf > 1:
                for j in range(nf):
                    u = j / nf
                    u = u * u * (3 - 2 * u)
                    llaves.append((f0 + j, pos, rumbo_ant + info["frente"] + dr * u))
            llaves.append((f0 + k * por_ciclo + (nf if k == 0 and nf > 1 else 0), pos + giro @ (d * k), r))
    raiz.animation_data_create()
    # un tramo nuevo puede empezar antes de que terminen las claves cuadro a cuadro del anterior: manda el nuevo
    inicios = sorted(tr["f0"] for tr in tramos)
    def _vigente(f):
        dueno = max((s for s in inicios if s <= f + 1e-6), default=inicios[0] if inicios else 1)
        return dueno
    por_frame = {}
    for f0, pz, rz in llaves:
        por_frame[round(f0, 3)] = (pz, rz)
    claves = sorted(por_frame.items())
    lineal = []
    prev = None
    for f0, (pz, rz) in claves:
        if prev is not None and f0 - prev[0] > 1.001:
            lineal.append((f0 - 0.01, prev[1], prev[2]))        # sostener hasta el salto (no se arrastra)
        lineal.append((f0, pz, rz))
        prev = (f0, pz, rz)
    for f0, pz, rz in lineal:
        raiz.location = pz
        raiz.rotation_euler = (0, 0, rz)
        raiz.keyframe_insert("location", frame=f0)
        raiz.keyframe_insert("rotation_euler", frame=f0)
    # lineal: en cámara lenta (sub-cuadros) el cuerpo no avanza a saltos
    if raiz.animation_data and raiz.animation_data.action:
        for fc in K._fcurves(raiz.animation_data.action):
            for k in fc.keyframe_points:
                k.interpolation = "LINEAR"
    fin = max((t["fin"] for t in tramos), default=1)
    for ac, tr in zip(spec.get("acciones", []), tramos):
        if ac.get("pose"):
            _pose_encima(arm, ac["pose"], tr["f0"], tr["f0"] + int(ac.get("pose_dur_s", 3.0) * fps), fps, pid)
    for po in spec.get("poses", []):          # poses de brazos por tiempo, encima de lo que esté haciendo
        f0 = int(round(po["inicio_s"] * fps)) + 1
        _pose_encima(arm, po["pose"], f0, f0 + int(round(po["dur_s"] * fps)), fps, pid)
    if spec.get("sobre"):
        padre = bpy.data.objects.get(spec["sobre"])
        if padre is None:
            raise KeyError(f"{pid}: no existe el objeto '{spec['sobre']}' para viajar encima")
        raiz.parent = padre                  # las posiciones y rumbos de las acciones quedan en el marco del objeto
    if arma_obj is not None and spec.get("disparos"):
        from estudio.blender import efectos as EF
        EF.fogonazos(arma_obj, [int(round(t * fps)) + 1 for t in spec["disparos"]], col)
    return {"id": pid, "raiz": raiz, "armadura": arm, "malla": malla, "tramos": tramos, "info": info, "fin": fin, "arma": arma_obj}


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
