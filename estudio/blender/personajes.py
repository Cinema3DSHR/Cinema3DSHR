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
    if MODELOS[spec.get("modelo", "futbol:jugador")].get("tipo") == "mixamo65":
        return _crear_mixamo(spec, fps, col)
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
    t_clip = t * tr["vel"]
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


def _rt(modelo: str, ref: str, arm, raiz, info: dict, dueno: str):
    """Acción retargeteada de un clip FBX de Mixamo para ESTE personaje (con caché por personaje)."""
    from estudio.blender import retarget as R
    clave = (dueno, ref)
    if clave not in _RETARGETS or _RETARGETS[clave].name not in bpy.data.actions:
        antes = set(bpy.data.actions)
        tmp = I.importar(ref)
        acc = next(a for a in bpy.data.actions if a not in antes)
        tarm = next(o for o in tmp if o.type == "ARMATURE")
        raiz.rotation_euler = (0, 0, 0)
        raiz.location = (0, 0, 0)
        nombre = f"rt_{dueno}_{Path(ref).stem}"
        _RETARGETS[clave] = R.retarget(tarm, acc, arm, nombre, info["cadera"])
        for o in tmp:
            bpy.data.objects.remove(o)
        for ac in list(bpy.data.actions):          # el clip original ya no hace falta (ahorra memoria)
            if ac == acc:
                bpy.data.actions.remove(ac)
    return _RETARGETS[clave]


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
    raiz.scale = (info["escala"],) * 3
    arm = next(o for o in objs if o.type == "ARMATURE")
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
    pos = Vector((0, 0, 0))
    rumbo = 0.0
    tramos = []
    llaves = []
    for i, ac in enumerate(spec.get("acciones", [])):
        ref = ac["clip"]
        accion = _rt(modelo, ref, arm, raiz, info, f"{pid}")
        f0 = int(round(ac["inicio_s"] * fps)) + 1
        if ac.get("encadenar") and tramos:
            pos, rumbo = tramos[-1]["pos_fin"], tramos[-1]["rumbo_fin"]
        if "pos" in ac:
            p = ac["pos"]
            pos = Vector((p[0], p[1], p[2] if len(p) > 2 else 0.0))
        if "mirando_deg" in ac:
            rumbo = math.radians(ac["mirando_deg"])
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
        st.extrapolation = "HOLD"
        d = Vector(accion.get("desplazamiento_cadera_m", (0, 0, 0)))
        d.z = 0
        vueltas = max(1, int(st.repeat))
        giro = Matrix.Rotation(rumbo + info["frente"], 3, "Z")
        pos_fin = pos + giro @ (d * vueltas)
        tramos.append({"accion": accion, "f0": f0, "fin": st.frame_end, "pos": pos.copy(), "rumbo": rumbo,
                       "strip": st, "pos_fin": pos_fin, "rumbo_fin": rumbo})
        # en cada repetición la cadera vuelve al punto de partida del clip: el personaje avanza lo que avanzó el ciclo
        por_ciclo = (st.frame_end - st.frame_start) / vueltas
        for k in range(vueltas):
            llaves.append((f0 + k * por_ciclo, pos + giro @ (d * k), rumbo + info["frente"]))
    raiz.animation_data_create()
    for f0, pz, rz in llaves:
        raiz.location = pz
        raiz.rotation_euler = (0, 0, rz)
        raiz.keyframe_insert("location", frame=f0)
        raiz.keyframe_insert("rotation_euler", frame=f0)
    # (los tramos con repeticiones recortadas por el siguiente dejan claves de más: son inofensivas)
    if raiz.animation_data and raiz.animation_data.action:
        for fc in K._fcurves(raiz.animation_data.action):
            for k in fc.keyframe_points:
                k.interpolation = "CONSTANT"
    fin = max((t["fin"] for t in tramos), default=1)
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
