"""Ruido 4D que sube dentro de una caja (común al fuego y al humo). Copiado de la prueba (b8_efectos._ruido_subiendo)."""
from __future__ import annotations

from estudio.autofinisher.recetas_efectos import nodos as K


def ruido_subiendo(nt, t, velocidad, escala, x0=-900, y0=0):
    """Coordenadas generadas (0..1) con el ruido 4D desplazándose hacia arriba: devuelve (factor, z 0..1, dist. xy)."""
    N, L = nt.nodes, nt.links
    tc = N.new("ShaderNodeTexCoord"); tc.location = (x0 - 400, y0)
    sp = N.new("ShaderNodeSeparateXYZ"); sp.location = (x0 - 200, y0 - 200)
    L.new(tc.outputs["Generated"], sp.inputs[0])
    sube = K.mat(nt, "MULTIPLY", t, -velocidad, x0 - 200, y0 + 200)
    mv = N.new("ShaderNodeVectorMath"); mv.operation = "ADD"; mv.location = (x0, y0)
    cz = N.new("ShaderNodeCombineXYZ"); cz.location = (x0 - 200, y0 + 100)
    L.new(sube, cz.inputs[2])
    L.new(tc.outputs["Generated"], mv.inputs[0]); L.new(cz.outputs[0], mv.inputs[1])
    nz = N.new("ShaderNodeTexNoise"); nz.noise_dimensions = "4D"; nz.location = (x0 + 200, y0)
    nz.inputs["Scale"].default_value = escala
    nz.inputs["Detail"].default_value = 6.0
    nz.inputs["Roughness"].default_value = 0.6
    L.new(mv.outputs[0], nz.inputs["Vector"])
    L.new(K.mat(nt, "MULTIPLY", t, 0.9, x0, y0 - 350), nz.inputs["W"])
    dx = K.mat(nt, "SUBTRACT", sp.outputs[0], 0.5, x0, y0 - 500)
    dy = K.mat(nt, "SUBTRACT", sp.outputs[1], 0.5, x0, y0 - 600)
    cxy = N.new("ShaderNodeCombineXYZ"); cxy.location = (x0 + 200, y0 - 550)
    L.new(dx, cxy.inputs[0]); L.new(dy, cxy.inputs[1])
    ln = N.new("ShaderNodeVectorMath"); ln.operation = "LENGTH"; ln.location = (x0 + 400, y0 - 550)
    L.new(cxy.outputs[0], ln.inputs[0])
    return nz.outputs["Fac"], sp.outputs[2], ln.outputs["Value"]


def caja_volumen(nombre, centro, tam, col):
    o = K.caja(nombre, centro, tam, col)
    o.visible_shadow = False
    return o
