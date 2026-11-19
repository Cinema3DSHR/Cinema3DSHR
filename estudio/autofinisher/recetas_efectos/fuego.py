"""Receta FUEGO (bpy, determinista por cuadro): volumen emisivo en una caja sobre el vacío FX_fuego, con ruido 4D que
sube, más angosto arriba y que se apaga hacia arriba; rampa de color rojo → naranja → amarillo.

CORRECCIÓN respecto de la prueba «Casa moderna en tormenta»: allí las llamas salían tenues en Cycles (se veían más las
brasas). Valores de la prueba → valores por defecto ahora:
  umbral    0,08 → 0,05   (más volumen pasa a ser llama)
  ganancia  9    → 12     (densidad de la llama: llega antes al máximo)
  emision   22   → 90     (unas 4× más brillo por unidad de volumen)
Los valores nuevos NO se verificaron con un render (la implementación no renderiza): si hiciera falta, se ajustan en
la receta de la escena (efectos[].parametros) sin tocar el código, y cada ajuste es una versión nueva."""
from __future__ import annotations

from mathutils import Vector

from estudio.autofinisher.recetas_efectos import nodos as K
from estudio.autofinisher.recetas_efectos._volumen import caja_volumen, ruido_subiendo

PARAMETROS_POR_DEFECTO = {
    "desplazamiento": [0.0, 0.0, 0.3],       # desde el vacío (Blender: x, y, z arriba)
    "tamano": [0.85, 0.32, 0.75],
    "velocidad": 1.4, "escala_ruido": 4.0,
    "umbral": 0.05, "ganancia": 12.0, "emision": 90.0, "angostura": 0.55, "caida": 1.4,
    "colores": {"base": [0.25, 0.02, 0.0], "medio": [1.0, 0.32, 0.03], "punta": [1.0, 0.85, 0.45], "pos_medio": 0.45},
}


def aplicar(ancla, p: dict, ctx: K.Contexto) -> dict:
    f = K.ancla_pos(ancla)
    o = caja_volumen("Fuego_volumen", f + Vector(p["desplazamiento"]), tuple(p["tamano"]), ctx.col_fx)
    m, N, L = K.material("fuego_volumen")
    nt = m.node_tree
    t = K.tiempo(N, ctx.fps)
    fac, z, r = ruido_subiendo(nt, t, p["velocidad"], p["escala_ruido"])
    lim = K.mat(nt, "MULTIPLY", K.mat(nt, "SUBTRACT", 1.0, z, -100, -700), p["angostura"], 50, -700)
    forma = K.mat(nt, "SMOOTH_MIN", K.mat(nt, "SUBTRACT", lim, r, 200, -650), 1.0, 350, -650)
    N[forma.node.name].inputs[2].default_value = 0.1
    alto = K.mat(nt, "POWER", K.mat(nt, "SUBTRACT", 1.0, z, 200, -850), p["caida"], 350, -850)
    d = K.mat(nt, "MULTIPLY", K.mat(nt, "MULTIPLY", fac, forma, 500, -300), alto, 650, -300)
    d = K.mat(nt, "MULTIPLY", K.mat(nt, "SUBTRACT", d, p["umbral"], 800, -300), p["ganancia"], 950, -300)
    N[d.node.name].use_clamp = True
    rampa = N.new("ShaderNodeValToRGB"); rampa.location = (1100, -100)
    c = p["colores"]
    e = rampa.color_ramp.elements
    e[0].position, e[0].color = 0.0, (*c["base"], 1)
    e[1].position, e[1].color = 1.0, (*c["punta"], 1)
    mid = e.new(c["pos_medio"]); mid.color = (*c["medio"], 1)
    L.new(d, rampa.inputs[0])
    em = N.new("ShaderNodeEmission"); em.location = (1400, 0)
    L.new(rampa.outputs[0], em.inputs["Color"])
    L.new(K.mat(nt, "MULTIPLY", d, p["emision"], 1250, -300), em.inputs["Strength"])
    out = N.new("ShaderNodeOutputMaterial"); out.location = (1600, 0)
    L.new(em.outputs[0], out.inputs["Volume"])
    o.data.materials.append(m)
    return {"fuego": "volumen emisivo con ruido 4D", "centro": [round(v, 3) for v in o.location],
            "umbral": p["umbral"], "ganancia": p["ganancia"], "emision": p["emision"]}
