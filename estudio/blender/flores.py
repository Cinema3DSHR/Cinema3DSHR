"""Flores y plantas procedurales (para «A la deriva» E02, el pasillo botánico; reutilizables en cualquier escenario).

Cada planta es un objeto «tallo» (tallo curvo + hojas) con la cabeza floral como hijo, así la cabeza cabecea sobre el
tallo y el tallo se mece desde la base. Siete especies con variación orgánica (cantidad, largo, ancho, curvatura y
color de cada pétalo; altura y curva del tallo; hojas), nunca dos iguales:
  margarita · tulipan · rosa · campanula · espiga · orquidea · anemona
Los pétalos llevan el atributo de color «grad» (0 base → 1 punta) que el material usa para aclarar u oscurecer las
puntas; en la previsualización queda el color plano del material (propiedad "estudio").
"""
from __future__ import annotations

import math

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

ESPECIES = ("margarita", "tulipan", "rosa", "campanula", "espiga", "orquidea", "anemona")

# paletas en sRGB (base, punta)
PALETAS = [
    ((0.98, 0.96, 0.92), (1.00, 1.00, 0.98)),   # blanco cálido
    ((0.95, 0.55, 0.65), (1.00, 0.82, 0.86)),   # rosa
    ((0.85, 0.25, 0.42), (0.98, 0.55, 0.62)),   # fucsia
    ((0.98, 0.70, 0.30), (1.00, 0.88, 0.55)),   # durazno
    ((0.99, 0.84, 0.25), (1.00, 0.95, 0.60)),   # amarillo
    ((0.55, 0.45, 0.90), (0.80, 0.72, 1.00)),   # lila
    ((0.35, 0.40, 0.92), (0.65, 0.72, 1.00)),   # azul
    ((0.90, 0.30, 0.20), (1.00, 0.62, 0.40)),   # coral
    ((0.70, 0.20, 0.55), (0.95, 0.60, 0.85)),   # magenta
    ((0.97, 0.88, 0.80), (1.00, 0.70, 0.75)),   # blanco con borde rosa
    ((0.60, 0.80, 0.95), (0.90, 0.96, 1.00)),   # celeste
    ((0.92, 0.45, 0.10), (1.00, 0.75, 0.25)),   # naranja
]
VERDES = [(0.16, 0.42, 0.14), (0.24, 0.50, 0.18), (0.12, 0.34, 0.16), (0.30, 0.52, 0.22)]
CENTROS = [(0.95, 0.72, 0.10), (0.45, 0.25, 0.08), (0.20, 0.12, 0.10), (0.90, 0.85, 0.40)]

_MATS: dict = {}


def _lin(c):
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)


def reiniciar():
    _MATS.clear()


def _mat_petalo(nombre: str, base, punta, sss: float = 0.35, brillo: float = 0.35) -> bpy.types.Material:
    """Pétalo: color de base a punta por el atributo «grad», algo de translucidez (subsuperficie) y terciopelo."""
    if nombre in _MATS:
        return _MATS[nombre]
    b, p = _lin(base), _lin(punta)
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    nt = m.node_tree
    bs = nt.nodes["Principled BSDF"]
    at = nt.nodes.new("ShaderNodeAttribute")
    at.attribute_name = "grad"
    rampa = nt.nodes.new("ShaderNodeValToRGB")
    rampa.color_ramp.elements[0].color = (*[x * 0.8 for x in b], 1)
    rampa.color_ramp.elements[1].color = (*p, 1)
    rampa.color_ramp.elements[0].position = 0.05
    rampa.color_ramp.elements[1].position = 0.95
    nt.links.new(at.outputs["Fac"], rampa.inputs["Fac"])
    nt.links.new(rampa.outputs["Color"], bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = 0.45
    for k, v in (("Subsurface Weight", sss), ("Sheen Weight", brillo), ("Specular IOR Level", 0.35)):
        if k in bs.inputs:
            bs.inputs[k].default_value = v
    if "Subsurface Radius" in bs.inputs:
        bs.inputs["Subsurface Radius"].default_value = (0.006, 0.004, 0.003)
    if "Subsurface Scale" in bs.inputs:
        bs.inputs["Subsurface Scale"].default_value = 0.02
    m.diffuse_color = (*[(x + y) / 2 for x, y in zip(b, p)], 1)
    m["estudio"] = {"color": [(x + y) / 2 for x, y in zip(b, p)], "rugosidad": 0.45, "metal": 0.0,
                    "emision": None, "fuerza": 0.0, "alfa": 1.0}
    m.use_backface_culling = False
    _MATS[nombre] = m
    return m


def _mat_simple(nombre: str, color, rug=0.5, sss=0.0) -> bpy.types.Material:
    if nombre in _MATS:
        return _MATS[nombre]
    c = _lin(color)
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    bs = m.node_tree.nodes["Principled BSDF"]
    bs.inputs["Base Color"].default_value = (*c, 1)
    bs.inputs["Roughness"].default_value = rug
    if sss and "Subsurface Weight" in bs.inputs:
        bs.inputs["Subsurface Weight"].default_value = sss
        bs.inputs["Subsurface Scale"].default_value = 0.01
    m.diffuse_color = (*c, 1)
    m["estudio"] = {"color": list(c), "rugosidad": rug, "metal": 0.0, "emision": None, "fuerza": 0.0, "alfa": 1.0}
    m.use_backface_culling = False
    _MATS[nombre] = m
    return m


# ------------------------------------------------------------------------------------------------ primitivas

class _Malla:
    """Acumula vértices, caras, índice de material y «grad» por vértice; termina en un objeto."""

    def __init__(self):
        self.v, self.f, self.mi, self.g = [], [], [], []

    def grilla(self, P: np.ndarray, G: np.ndarray, mat: int):
        """P: (nu+1, nv+1, 3) puntos; G: (nu+1, nv+1) grad."""
        nu, nv = P.shape[0] - 1, P.shape[1] - 1
        i0 = len(self.v)
        self.v += [tuple(x) for x in P.reshape(-1, 3)]
        self.g += list(G.reshape(-1))
        for i in range(nu):
            for j in range(nv):
                a = i0 + i * (nv + 1) + j
                self.f.append((a, a + nv + 1, a + nv + 2, a + 1))
                self.mi.append(mat)

    def tubo(self, pts: list, radios: list, mat: int, lados: int = 5):
        pts = [Vector(p) for p in pts]
        anillos = []
        for k, p in enumerate(pts):
            t = (pts[min(k + 1, len(pts) - 1)] - pts[max(k - 1, 0)]).normalized()
            a = t.orthogonal().normalized()
            b = t.cross(a)
            anillos.append([p + (a * math.cos(2 * math.pi * s / lados) + b * math.sin(2 * math.pi * s / lados)) * radios[k]
                            for s in range(lados)])
        i0 = len(self.v)
        for k, an in enumerate(anillos):
            self.v += [tuple(x) for x in an]
            self.g += [k / max(1, len(anillos) - 1)] * lados
        for k in range(len(anillos) - 1):
            for s in range(lados):
                a, b = i0 + k * lados + s, i0 + k * lados + (s + 1) % lados
                self.f.append((a, b, b + lados, a + lados))
                self.mi.append(mat)

    def esfera(self, c, r, mat: int, escala=(1, 1, 1), seg=8, an=5, grad=0.0):
        i0 = len(self.v)
        c = Vector(c)
        for i in range(an + 1):
            th = math.pi * i / an
            for j in range(seg):
                ph = 2 * math.pi * j / seg
                self.v.append(tuple(c + Vector((math.sin(th) * math.cos(ph) * r * escala[0],
                                                 math.sin(th) * math.sin(ph) * r * escala[1], math.cos(th) * r * escala[2]))))
                self.g.append(grad)
        for i in range(an):
            for j in range(seg):
                a, b = i0 + i * seg + j, i0 + i * seg + (j + 1) % seg
                self.f.append((a, b, b + seg, a + seg))
                self.mi.append(mat)

    def objeto(self, nombre: str, mats: list, col, suave=True) -> bpy.types.Object:
        me = bpy.data.meshes.new(nombre)
        me.from_pydata(self.v, [], self.f)
        me.update()
        for m in mats:
            me.materials.append(m)
        if self.f:
            me.polygons.foreach_set("material_index", self.mi)
            me.polygons.foreach_set("use_smooth", [suave] * len(self.f))
        at = me.attributes.new("grad", "FLOAT", "POINT")
        at.data.foreach_set("value", self.g)
        ob = bpy.data.objects.new(nombre, me)
        col.objects.link(ob)
        return ob


def _petalo(M: _Malla, o, du, dv, dn, largo, ancho, curva, copa, mat, rng, nu=9, nv=4, punta=0.0, ondas=0.0,
            forma=0.7, redondez=0.5):
    """Pétalo como grilla: largo hacia du, ancho hacia dv, se curva hacia dn (curva: comba a lo largo; copa: a lo
    ancho). forma < 1 ensancha la punta (tulipán), > 1 la afina (margarita)."""
    o, du, dv, dn = (np.array(x, float) for x in (o, du, dv, dn))
    P = np.zeros((nu + 1, 2 * nv + 1, 3))
    G = np.zeros((nu + 1, 2 * nv + 1))
    fase = rng.uniform(0, 6.28)
    for i in range(nu + 1):
        u = i / nu
        # perfil: angosto en la base, ancho al medio; redondez 0,5 = punta redonda, 1 = aguda
        w = ancho * (math.sin(math.pi * min(1.0, u ** forma * 0.985 + 0.015)) ** redondez) * (1 - punta * u ** 4)
        for j in range(-nv, nv + 1):
            v = j / nv
            onda = ondas * math.sin(v * 4 + fase) * u * ancho
            P[i, j + nv] = o + du * largo * u + dv * w * v + dn * (curva * largo * u * u + copa * w * v * v + onda)
            G[i, j + nv] = u
    M.grilla(P, G, mat)


def _base(d: Vector):
    """Ejes ortonormales con el primero = d."""
    d = d.normalized()
    a = d.orthogonal().normalized()
    return d, a, d.cross(a)


# ------------------------------------------------------------------------------------------------ cabezas

def _cabeza(M: _Malla, especie: str, rng, escala: float, mp: int, mc: int, mh: int):
    """Arma la cabeza floral en coordenadas locales (el tallo llega al origen por −Z; la flor mira a +Z)."""
    z = Vector((0, 0, 1))
    if especie == "margarita":
        n = int(rng.integers(14, 26))
        L = escala * rng.uniform(0.028, 0.045)
        for k in range(n):
            a = 2 * math.pi * k / n + rng.normal(0, 0.06)
            d = Vector((math.cos(a), math.sin(a), rng.uniform(-0.05, 0.25))).normalized()
            dv = z.cross(d).normalized()
            dn = d.cross(dv)
            _petalo(M, d * L * 0.18, d, dv, dn, L * rng.uniform(0.85, 1.1), L * 0.16, rng.uniform(-0.25, 0.1), 0.05,
                    mp, rng, nu=6, nv=2, forma=1.3, redondez=0.8)
        M.esfera((0, 0, L * 0.06), L * 0.24, mc, escala=(1, 1, 0.55), grad=1.0)
    elif especie == "tulipan":
        n = 6
        L = escala * rng.uniform(0.045, 0.06)
        abre = rng.uniform(0.15, 0.45)
        for k in range(n):
            a = 2 * math.pi * k / n + (0.5 if k % 2 else 0) * 0.0
            r = 1.0 if k % 2 == 0 else 0.93
            d = Vector((math.cos(a) * math.sin(abre), math.sin(a) * math.sin(abre), math.cos(abre))).normalized()
            dv = Vector((-math.sin(a), math.cos(a), 0))
            dn = d.cross(dv)
            _petalo(M, Vector((math.cos(a), math.sin(a), 0)) * L * 0.08, d, dv, -dn, L * r, L * 0.42,
                    rng.uniform(0.08, 0.2), -0.45, mp, rng, nu=10, nv=4, forma=0.55, redondez=0.35)
        M.esfera((0, 0, L * 0.25), L * 0.12, mc, escala=(1, 1, 2.0), grad=1.0)
    elif especie == "rosa":
        capas = int(rng.integers(4, 6))
        R = escala * rng.uniform(0.03, 0.042)
        k_tot = 0
        for c in range(capas):
            t = c / (capas - 1)
            n = 3 + c
            L = R * (0.55 + 0.6 * t)
            abre = 0.15 + 1.05 * t ** 1.3
            for k in range(n):
                a = 2 * math.pi * k / n + c * 0.9 + k_tot * 0.13
                d = Vector((math.cos(a) * math.sin(abre), math.sin(a) * math.sin(abre), math.cos(abre))).normalized()
                dv = Vector((-math.sin(a), math.cos(a), 0))
                dn = d.cross(dv)
                _petalo(M, Vector((math.cos(a), math.sin(a), 0)) * R * 0.1 * t, d, dv, -dn, L, L * 0.6,
                        0.25 + 0.35 * t, -0.35 * (1 - t) + 0.05, mp, rng, nu=9, nv=4, forma=0.5, ondas=0.05 * t,
                        redondez=0.3)
                k_tot += 1
    elif especie == "campanula":
        nb = int(rng.integers(3, 6))
        for b in range(nb):
            a = 2 * math.pi * b / nb + rng.normal(0, 0.3)
            off = Vector((math.cos(a) * 0.035, math.sin(a) * 0.035, -0.02 * b)) * escala
            M.tubo([(0, 0, -0.02 * b * escala), off + Vector((0, 0, 0.012 * escala)), off], [0.0016, 0.0013, 0.0011],
                   mh, lados=4)
            L = escala * rng.uniform(0.018, 0.026)
            for k in range(5):
                aa = 2 * math.pi * k / 5
                d = Vector((math.cos(aa) * 0.45, math.sin(aa) * 0.45, -1)).normalized()
                dv = Vector((-math.sin(aa), math.cos(aa), 0))
                dn = d.cross(dv)
                _petalo(M, off, d, dv, dn, L, L * 0.55, -0.35, -0.2, mp, rng, nu=6, nv=3, forma=0.6, redondez=0.6)
    elif especie == "espiga":
        alto = escala * rng.uniform(0.08, 0.13)
        n = int(rng.integers(26, 40))
        for k in range(n):
            t = k / n
            a = k * 2.4
            r = escala * 0.007 * (1 - 0.6 * t)
            M.esfera((math.cos(a) * r, math.sin(a) * r, t * alto), escala * rng.uniform(0.0035, 0.0055) * (1 - 0.4 * t),
                     mp, escala=(1, 1, 1.4), seg=6, an=3, grad=t)
        M.tubo([(0, 0, 0), (0, 0, alto * 0.98)], [0.0018, 0.001], mh, lados=4)
    elif especie == "orquidea":
        L = escala * rng.uniform(0.03, 0.04)
        for k, (a, l, w) in enumerate(((90, 1.0, 0.32), (210, 0.95, 0.3), (330, 0.95, 0.3), (150, 0.85, 0.5),
                                       (30, 0.85, 0.5))):
            ar = math.radians(a + rng.normal(0, 6))
            d = Vector((math.cos(ar), 0.15, math.sin(ar))).normalized()
            dv = Vector((-math.sin(ar), 0, math.cos(ar)))
            _petalo(M, (0, 0, 0), d, dv, Vector((0, 1, 0)), L * l, L * w, rng.uniform(0.05, 0.2), 0.1, mp, rng,
                    nu=8, nv=4, forma=0.6, ondas=0.04, redondez=0.4)
        _petalo(M, (0, 0.004, -0.004), Vector((0, 0.6, -1)).normalized(), Vector((1, 0, 0)), Vector((0, 1, 0.3)),
                L * 0.6, L * 0.38, 0.4, -0.4, mc, rng, nu=7, nv=4, forma=0.5, ondas=0.08, redondez=0.35)
    else:  # anemona / cosmos: pocos pétalos anchos y centro oscuro
        n = int(rng.integers(5, 9))
        L = escala * rng.uniform(0.03, 0.045)
        for k in range(n):
            a = 2 * math.pi * k / n + rng.normal(0, 0.08)
            d = Vector((math.cos(a), math.sin(a), rng.uniform(0.1, 0.35))).normalized()
            dv = z.cross(d).normalized()
            dn = d.cross(dv)
            _petalo(M, d * L * 0.1, d, dv, dn, L * rng.uniform(0.9, 1.08), L * 0.5, rng.uniform(-0.1, 0.12), 0.12,
                    mp, rng, nu=9, nv=4, forma=0.55, ondas=0.06, redondez=0.35)
        M.esfera((0, 0, L * 0.05), L * 0.2, mc, escala=(1, 1, 0.7), grad=1.0)
        for k in range(18):
            a = 2 * math.pi * k / 18
            M.tubo([(0, 0, L * 0.05), (math.cos(a) * L * 0.22, math.sin(a) * L * 0.22, L * 0.16)], [0.0007, 0.0005],
                   mc, lados=3)


def planta(nombre: str, base, rng, col, especie: str | None = None, alto: float | None = None,
           paleta: int | None = None, escala: float = 1.0, cortada: bool = False) -> dict:
    """Una planta con flor. Devuelve {"tallo": obj, "cabeza": obj, "especie": …}. `cortada`: sin raíz ni hojas bajas
    (la flor de la bandeja de poda), acostada sobre el eje X local."""
    especie = especie or ESPECIES[int(rng.integers(0, len(ESPECIES)))]
    paleta = int(rng.integers(0, len(PALETAS))) if paleta is None else paleta
    alto = alto or rng.uniform(0.32, 0.72) * (0.8 if especie in ("campanula", "orquidea") else 1.0)
    pb, pp = PALETAS[paleta]
    jit = rng.normal(0, 0.03, 3)
    pb = tuple(float(np.clip(c + j, 0, 1)) for c, j in zip(pb, jit))
    m_pet = _mat_petalo(f"petalo_{paleta}_{int(rng.integers(0, 4))}", pb, pp)
    m_cen = _mat_simple(f"flor_centro_{int(rng.integers(0, len(CENTROS)))}", CENTROS[int(rng.integers(0, len(CENTROS)))],
                        0.7)
    verde = VERDES[int(rng.integers(0, len(VERDES)))]
    m_hoja = _mat_simple(f"hoja_{verde}", verde, 0.45, sss=0.25)
    m_tallo = _mat_simple(f"tallo_{verde}", tuple(c * 0.85 for c in verde), 0.5)
    # tallo: curva suave con una inclinación al azar
    inc = rng.uniform(0.0, 0.22)
    rumbo = rng.uniform(0, 2 * math.pi)
    n = 9
    pts, radios = [], []
    for k in range(n):
        t = k / (n - 1)
        lat = inc * alto * t * t
        pts.append((math.cos(rumbo) * lat + rng.normal(0, 0.002), math.sin(rumbo) * lat + rng.normal(0, 0.002),
                    alto * t))
        radios.append((0.0045 - 0.0018 * t) * escala)
    M = _Malla()
    M.tubo(pts, radios, 1, lados=5)
    # hojas: lanceoladas, alternas, más grandes abajo
    nh = 0 if cortada else int(rng.integers(2, 6))
    for h in range(nh):
        t = rng.uniform(0.08, 0.6)
        k = int(t * (n - 1))
        p = Vector(pts[k])
        a = rumbo + math.pi * h + rng.normal(0, 0.5)
        d = Vector((math.cos(a), math.sin(a), rng.uniform(0.3, 0.9))).normalized()
        dv = Vector((0, 0, 1)).cross(d).normalized()
        dn = d.cross(dv)
        L = rng.uniform(0.06, 0.15) * (1.2 - t) * escala
        _petalo(M, p, d, dv, dn, L, L * rng.uniform(0.18, 0.3), rng.uniform(-0.6, -0.15), 0.15, 2, rng, nu=6, nv=2,
                forma=0.8)
    tallo = M.objeto(f"{nombre}_tallo", [m_pet, m_tallo, m_hoja], col)
    tallo.location = base
    # cabeza: hijo del tallo, en la punta, mirando en la dirección del último tramo
    C = _Malla()
    _cabeza(C, especie, rng, escala * rng.uniform(0.9, 1.25), 0, 1, 2)
    cabeza = C.objeto(f"{nombre}_flor", [m_pet, m_cen, m_tallo], col)
    sub = cabeza.modifiers.new("suave", "SUBSURF")            # sólo en el render: el visor recibe la malla liviana
    sub.levels, sub.render_levels, sub.show_viewport = 0, 1, False
    cabeza.parent = tallo
    punta = Vector(pts[-1])
    dirf = (punta - Vector(pts[-3])).normalized()
    if especie in ("campanula",):
        dirf = Vector((0, 0, 1))
    cabeza.location = punta
    cabeza.rotation_mode = "QUATERNION"
    cabeza.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(dirf)
    cabeza.rotation_mode = "XYZ"
    return {"tallo": tallo, "cabeza": cabeza, "especie": especie, "alto": alto}


def mecer(plantas: list, nf: int, fps: int = 30, paso: int = 4, rng=None, aire: float = 1.0):
    """Las plantas se mecen como con la circulación de aire de la incubadora: el tallo desde la base (1–3°) y la flor
    cabecea sobre él (2–5°), cada una con su ritmo. Llaves cada `paso` cuadros, interpolación suave."""
    rng = rng or np.random.default_rng(3)
    for pl in plantas:
        for ob, amp in ((pl["tallo"], math.radians(rng.uniform(1.0, 2.8)) * aire),
                        (pl["cabeza"], math.radians(rng.uniform(2.0, 5.0)) * aire)):
            f1, f2 = rng.uniform(0.12, 0.3), rng.uniform(0.33, 0.6)
            ph1, ph2, ph3 = rng.uniform(0, 6.28, 3)
            r0 = ob.rotation_euler.copy()
            ad = ob.animation_data_create()
            act = bpy.data.actions.new(f"mecer_{ob.name}")
            ad.action = act
            frames = list(range(1, nf + 1, paso)) + [nf]
            vals = {0: [], 1: []}
            for f in frames:
                t = f / fps
                vals[0].append(r0.x + amp * (0.7 * math.sin(2 * math.pi * f1 * t + ph1) + 0.3 * math.sin(2 * math.pi * f2 * t + ph2)))
                vals[1].append(r0.y + amp * (0.7 * math.sin(2 * math.pi * f1 * 0.83 * t + ph3) + 0.3 * math.sin(2 * math.pi * f2 * 1.1 * t + ph1)))
            for eje in (0, 1):
                ob.rotation_euler[eje] = vals[eje][0]
                ob.keyframe_insert("rotation_euler", index=eje, frame=1)
            from estudio.blender import kit as K
            for fc in K._fcurves(act):
                if fc.data_path != "rotation_euler" or fc.array_index not in (0, 1):
                    continue
                kp = fc.keyframe_points
                kp.clear()
                kp.add(len(frames))
                co = []
                for f, v in zip(frames, vals[fc.array_index]):
                    co += [f, v]
                kp.foreach_set("co", co)
                for k in kp:
                    k.interpolation = "BEZIER"
                    k.handle_left_type = k.handle_right_type = "AUTO_CLAMPED"
                fc.update()
