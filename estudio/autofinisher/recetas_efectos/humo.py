"""Receta HUMO (bpy, determinista por cuadro): volumen gris (Principled Volume) con ruido 4D que sube, en una caja
sobre el vacío FX_humo. `z_centro` fija la altura absoluta del centro de la caja (en la prueba, el techo del fogón);
si no está, se usa el desplazamiento desde el vacío."""
from __future__ import annotations

from mathutils import Vector

from estudio.autofinisher.recetas_efectos import nodos as K
from estudio.autofinisher.recetas_efectos._volumen import caja_volumen, ruido_subiendo

PARAMETROS_POR_DEFECTO = {
    "desplazamiento": [0.0, 0.0, 0.5], "z_centro": None, "tamano": [1.3, 0.42, 0.56],
    "velocidad": 0.5, "escala_ruido": 3.0, "umbral": 0.48, "ganancia": 6.0, "densidad": 1.6,
    "color": [0.3, 0.29, 0.28], "anisotropia": 0.3,
}


def aplicar(ancla, p: dict, ctx: K.Contexto) -> dict:
    h = K.ancla_pos(ancla)
    centro = Vector((h.x, h.y, p["z_centro"])) if p.get("z_centro") is not None else h + Vector(p["desplazamiento"])
    oh = caja_volumen("Humo_volumen", centro, tuple(p["tamano"]), ctx.col_fx)
    m, N, L = K.material("humo_volumen")
    nt = m.node_tree
    t = K.tiempo(N, ctx.fps)
    fac, z, r = ruido_subiendo(nt, t, p["velocidad"], p["escala_ruido"])
    alto = K.mat(nt, "MULTIPLY", z, K.mat(nt, "SUBTRACT", 1.0, r, 200, -900), 350, -850)
    d = K.mat(nt, "MULTIPLY", K.mat(nt, "SUBTRACT", fac, p["umbral"], 500, -300), alto, 650, -300)
    d = K.mat(nt, "MULTIPLY", d, p["ganancia"], 800, -300)
    N[d.node.name].use_clamp = True
    pv = N.new("ShaderNodeVolumePrincipled"); pv.location = (1100, 0)
    pv.inputs["Color"].default_value = (*p["color"], 1)
    pv.inputs["Anisotropy"].default_value = p["anisotropia"]
    L.new(K.mat(nt, "MULTIPLY", d, p["densidad"], 950, -300), pv.inputs["Density"])
    out = N.new("ShaderNodeOutputMaterial"); out.location = (1400, 0)
    L.new(pv.outputs[0], out.inputs["Volume"])
    oh.data.materials.append(m)
    return {"humo": "volumen principled", "centro": [round(v, 3) for v in oh.location]}
