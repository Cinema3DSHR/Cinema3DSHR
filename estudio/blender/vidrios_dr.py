"""Vidrios de los autos de Dream Rally en Cycles.

Los GLB de los autos del juego son una sola malla con la textura pintada: los vidrios no son una pieza aparte. El juego
los dibuja con su sombreador (`car_visual.gd` → LIVERY_SHADER: `glass_strip` para parabrisas y luneta, `glass_side`
para las ventanillas) a partir de las medidas del `<id>.json` (`glass.ws`, `glass.rg`, `glass.poly`, `cab_hw`). Acá se
arma la misma máscara con nodos (mismas fórmulas, coordenadas del modelo: x lateral, y arriba, z adelante) y donde vale
1 la carrocería pasa a vidrio: polarizado como en el juego, o translúcido (`claro=True`, la opción «Ver los pilotos
desde las cámaras de afuera») para que se vean la cabina y los pilotos.
"""
from __future__ import annotations
import bpy


class _N:
    """Valor escalar de un árbol de nodos con operadores (+ − × ÷, min, max…) → ShaderNodeMath."""

    def __init__(self, nt, salida):
        self.nt, self.s = nt, salida

    def _op(self, op, otro=None, otro2=None):
        n = self.nt.nodes.new("ShaderNodeMath")
        n.operation = op
        self.nt.links.new(self.s, n.inputs[0])
        for i, v in ((1, otro), (2, otro2)):
            if v is None:
                continue
            if isinstance(v, _N):
                self.nt.links.new(v.s, n.inputs[i])
            else:
                n.inputs[i].default_value = float(v)
        return _N(self.nt, n.outputs[0])

    def __add__(self, o): return self._op("ADD", o)
    def __radd__(self, o): return self._op("ADD", o)
    def __sub__(self, o): return self._op("SUBTRACT", o)
    def __rsub__(self, o): return (self * -1.0) + o
    def __mul__(self, o): return self._op("MULTIPLY", o)
    def __rmul__(self, o): return self._op("MULTIPLY", o)
    def __truediv__(self, o): return self._op("DIVIDE", o)
    def __neg__(self): return self * -1.0
    def abs(self): return self._op("ABSOLUTE")
    def max(self, o): return self._op("MAXIMUM", o)
    def min(self, o): return self._op("MINIMUM", o)
    def exp(self): return self._op("EXPONENT")
    def log(self): return self._op("LOGARITHM", 2.718281828)
    def sqrt(self): return self._op("SQRT")
    def clamp(self, a=0.0, b=1.0): return self.max(a).min(b)

    def smooth(self, a, b):
        """smoothstep(a, b, self)"""
        t = ((self - a) / (b - a)).clamp()
        return t * t * (t * -2.0 + 3.0)


def _sep(nt, vec_salida):
    s = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(vec_salida, s.inputs[0])
    return [_N(nt, s.outputs[i]) for i in range(3)]


def _rbox(px, py, bx, by, r):
    qx = px.abs() - bx + r
    qy = py.abs() - by + r
    largo = (qx.max(0.0) * qx.max(0.0) + qy.max(0.0) * qy.max(0.0)).sqrt()
    return largo + qx.max(qy).min(0.0) - r


def _strip(x, y, z, nx, ny, nz, seg, w):
    import math
    ax, ay = seg[0], seg[1]
    dx, dy = seg[2] - ax, seg[3] - ay
    L = max(math.hypot(dx, dy), 0.001)
    ux, uy = dx / L, dy / L
    nnx, nny = -uy, ux
    if nny < 0:
        nnx, nny = -nnx, -nny
    qx, qy = z - ax, y - ay
    t = qx * ux + qy * uy
    dist = qx * nnx + qy * nny
    hw = (t / L).clamp() * (w[1] - w[0]) + w[0]
    sd = _rbox(x, t - L * 0.5, hw, L * 0.5, 0.10)
    plano = 1.0 - dist.abs().smooth(0.05, 0.08)
    alinea = (nz * nnx + ny * nny).smooth(0.78, 0.92)
    return (1.0 - sd.smooth(-0.006, 0.004)) * plano * alinea


def _lado(x, y, z, nx, poly, cab_hw):
    import math
    c = (sum(p[0] for p in poly) / 4, sum(p[1] for p in poly) / 4)
    acc = None
    for i in range(4):
        a, b = poly[i], poly[(i + 1) % 4]
        ex, ey = b[0] - a[0], b[1] - a[1]
        ln = max(math.hypot(ex, ey), 1e-6)
        nnx, nny = -ey / ln, ex / ln
        if nnx * (a[0] - c[0]) + nny * (a[1] - c[1]) < 0:
            nnx, nny = -nnx, -nny
        term = (((z - a[0]) * nnx + (y - a[1]) * nny + 0.035) * 30.0).exp()
        acc = term if acc is None else acc + term
    d = acc.log() / 30.0
    lat = nx.abs().smooth(0.35, 0.6) * x.abs().smooth(0.55 * cab_hw, 0.7 * cab_hw)
    return (1.0 - d.smooth(-0.004, 0.004)) * lat


def mascara(nt, meta: dict):
    """Salida (socket) con la máscara de vidrio 0–1 del auto `meta` (el .json del juego)."""
    g = meta.get("glass")
    if not isinstance(g, dict):
        return None
    tc = nt.nodes.new("ShaderNodeTexCoord")
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    # normal en coordenadas del objeto
    vt = nt.nodes.new("ShaderNodeVectorTransform")
    vt.vector_type = "NORMAL"
    vt.convert_from = "WORLD"
    vt.convert_to = "OBJECT"
    nt.links.new(geo.outputs["Normal"], vt.inputs[0])
    bx, by, bz = _sep(nt, tc.outputs["Object"])
    nbx, nby, nbz = _sep(nt, vt.outputs[0])
    # Blender (objeto importado del glTF): x, y = −z del juego, z = y del juego
    x, y, z = bx, bz, -by
    nx, ny, nz = nbx, nbz, -nby
    ws, rg, pl = g["ws"], g["rg"], g["poly"]
    if abs(float(ws[0][0]) - float(ws[1][0])) < 0.35:
        pass                                      # el juego usa ws tal cual en el sombreador
    cab = float(g["cab_hw"])
    m_ws = _strip(x, y, z, nx, ny, nz, (ws[0][0], ws[0][1], ws[1][0], ws[1][1]),
                  (cab * float(g.get("ws_w0", 1.22)), cab * float(g.get("ws_w1", 0.92))))
    m_rg = _strip(x, y, z, nx, ny, nz, (rg[0][0], rg[0][1], rg[1][0], rg[1][1]),
                  (cab * float(g.get("rg_w0", 0.9)), cab * float(g.get("rg_w1", 1.1))))
    m_sd = _lado(x, y, z, nx, [tuple(p) for p in pl], cab)
    return m_ws.max(m_rg).max(m_sd).s


def aplicar(objetos, meta: dict, claro: bool = True):
    """Pone los vidrios en los materiales de la carrocería (copias propias del auto)."""
    hechos = {}
    for o in objetos:
        if o.type != "MESH":
            continue
        for i, slot in enumerate(o.material_slots):
            m = slot.material
            if m is None or not m.use_nodes:
                continue
            if m.name not in hechos:
                mc = m.copy()
                mc.name = f"{m.name}_vidrios_{meta.get('id', '')}"
                nt = mc.node_tree
                out = next((n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"), None)
                if out is None or not out.inputs["Surface"].is_linked:
                    hechos[m.name] = m
                    continue
                sup = out.inputs["Surface"].links[0].from_socket
                gm = mascara(nt, meta)
                if gm is None:
                    hechos[m.name] = m
                    continue
                fres = nt.nodes.new("ShaderNodeLayerWeight")
                fres.inputs["Blend"].default_value = 0.25
                brillo = nt.nodes.new("ShaderNodeBsdfGlossy")
                brillo.inputs["Roughness"].default_value = 0.03
                brillo.inputs["Color"].default_value = (0.9, 0.93, 0.96, 1)
                if claro:
                    trans = nt.nodes.new("ShaderNodeBsdfTransparent")
                    trans.inputs["Color"].default_value = (0.5, 0.56, 0.6, 1)
                    vid = nt.nodes.new("ShaderNodeMixShader")
                    nt.links.new(fres.outputs["Facing"], vid.inputs[0])
                    nt.links.new(trans.outputs[0], vid.inputs[1])
                    nt.links.new(brillo.outputs[0], vid.inputs[2])
                else:
                    oscuro = nt.nodes.new("ShaderNodeBsdfDiffuse")
                    oscuro.inputs["Color"].default_value = (0.02, 0.03, 0.045, 1)
                    vid = nt.nodes.new("ShaderNodeMixShader")
                    nt.links.new(fres.outputs["Facing"], vid.inputs[0])
                    nt.links.new(oscuro.outputs[0], vid.inputs[1])
                    nt.links.new(brillo.outputs[0], vid.inputs[2])
                mez = nt.nodes.new("ShaderNodeMixShader")
                nt.links.new(gm, mez.inputs[0])
                nt.links.new(sup, mez.inputs[1])
                nt.links.new(vid.outputs[0], mez.inputs[2])
                nt.links.new(mez.outputs[0], out.inputs["Surface"])
                if hasattr(mc, "blend_method"):
                    mc.blend_method = "HASHED"
                hechos[m.name] = mc
            slot.material = hechos[m.name]
    return list(hechos.values())
