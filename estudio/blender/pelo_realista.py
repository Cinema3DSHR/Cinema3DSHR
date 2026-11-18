"""Pelo realista (preset «Ornatrix / XGen» del dueño) para los personajes humanos con cabeza de MakeHuman.

Igual que la guía del dueño (sistema de pelo con padres + hijos interpolados, aglomerado, frizz, onda y sombreador
Principled Hair de Chiang), pero armado acá cuadro por cuadro con geometría propia para controlar el peinado:
  · RAÍCES sobre el cuero cabelludo de la cabeza de MakeHuman, dentro de la línea de nacimiento (frente con
    entradas, sienes, patillas, contorno de las orejas y nuca).
  · GUÍAS (hebras padre) peinadas con un campo de direcciones por estilo, apoyadas en capas sobre el cráneo y, las
    largas, cayendo con gravedad y chocando con hombros y espalda (no atraviesan el cuerpo):
      «degrade_militar» (él): costados y nuca rebajados en degradé (de ~3 mm abajo a ~1,5 cm), arriba 4–5 cm
        peinados hacia atrás, prolijos, con poco volumen.
      «largo_suelto» (ella): raya apenas al costado, pelo largo y suelto hasta la mitad de la espalda, bien
        peinado, por detrás de los hombros, con capas y una onda suave en las puntas.
  · HIJOS: cada guía reparte hebras alrededor de su raíz que se juntan hacia la punta (mechas) con frizz.
  · Dos versiones de la misma peluca: curvas (render en Cycles, con el sombreador de pelo) y TARJETAS con textura
    transparente (alpha cards) para el EDITOR 3D del teléfono. Las curvas no van al GLB; las tarjetas no se
    renderizan.
  · Movimiento: vaivén suave en el tiempo (nodos de geometría), mayor en las puntas del pelo largo.
"""
from __future__ import annotations
import math

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree


# ------------------------------------------------------------------------------------------------ marco y cuero

def marco(pj: dict) -> dict:
    u = pj["u"]
    ojos = [np.array(o["centro"]) for o in pj["ojos"]]
    E = (ojos[0] + ojos[1]) / 2
    return {"E": E, "C": E + np.array([0, 0.075 * u, 0.012 * u]), "u": u}


# Línea de nacimiento: altura (m reales sobre los ojos) según el ángulo alrededor de la cabeza (0 = frente, π = nuca):
# frente, sienes, patilla delante de la oreja, arco por encima de la oreja, detrás de la oreja y nuca.
LINEA = {
    "degrade_militar": [(0.0, 0.083), (0.40, 0.081), (0.60, 0.072), (0.82, 0.050), (1.00, 0.028), (1.12, -0.012),
                        (1.24, -0.012), (1.32, 0.036), (1.80, 0.036), (1.95, -0.010), (2.35, -0.050),
                        (math.pi, -0.068)],
    "largo_suelto": [(0.0, 0.078), (0.40, 0.076), (0.60, 0.068), (0.82, 0.046), (1.00, 0.026), (1.12, 0.004),
                     (1.24, 0.004), (1.32, 0.036), (1.80, 0.036), (1.95, -0.010), (2.35, -0.050),
                     (math.pi, -0.068)],
}


def con_pelo(p, m, estilo, margen=0.0) -> float:
    rel = p - m["C"]
    az = math.atan2(abs(rel[0]), -rel[1])
    xs, ys = zip(*LINEA[estilo])
    linea = float(np.interp(az, xs, ys)) + margen
    z = (p[2] - m["E"][2]) / m["u"]
    return float(np.clip((z - linea) / 0.005, 0, 1))


class _Cabeza:
    def __init__(self, pj):
        bm = bmesh.new()
        bm.from_mesh(pj["cabeza_humana"]["obj"].data)
        bm.normal_update()
        self.bvh = BVHTree.FromBMesh(bm)
        bm.free()

    def capa(self, p, h, C):
        q, n, _, _ = self.bvh.find_nearest(Vector(p))
        if q is None:
            return p, (p - C) / np.linalg.norm(p - C)
        q, n = np.array(q), np.array(n)
        if np.dot(n, q - C) < 0:
            n = -n
        return q + n * h, n

    def afuera(self, p, h, C):
        q, n, _, d = self.bvh.find_nearest(Vector(p))
        if q is None:
            return p
        q, n = np.array(q), np.array(n)
        if np.dot(n, q - C) < 0:
            n = -n
        if np.dot(p - q, n) < h:
            return q + n * h
        return p


class _Cuerpo:
    """Colisión del pelo largo con el cuerpo (hombros, espalda): nunca a menos de `margen` de la piel."""

    def __init__(self, pj):
        from estudio.blender.ropa_humana import Cuerpo
        self.cb = Cuerpo(pj)

    def afuera(self, p, margen):
        q, n, fi, d = self.cb.bvh.find_nearest(Vector(p), margen * 3)
        if q is None:
            return p
        q, n = np.array(q), np.array(n)
        i = self.cb.kd.find(Vector(q))[1]
        if np.dot(n, self.cb._radial(i, q)) < 0:
            n = -n
        if np.dot(p - q, n) < margen:
            return q + n * margen
        return p


def _raices(pj, m, estilo, n, rng):
    ob = pj["cabeza_humana"]["obj"]
    me = ob.data
    P = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", P)
    P = P.reshape(-1, 3)
    tris, pesos = [], []
    for poly in me.polygons:
        vs = list(poly.vertices)
        c = P[vs].mean(axis=0)
        w = con_pelo(c, m, estilo)
        if w > 0.05 and np.linalg.norm(c - m["C"]) > 0.05 * m["u"]:
            for k in range(1, len(vs) - 1):
                tris.append((vs[0], vs[k], vs[k + 1]))
                pesos.append(w)
    T = P[np.array(tris)]
    cr = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    area = 0.5 * np.linalg.norm(cr, axis=1) * np.array(pesos)
    el = rng.choice(len(T), size=n, p=area / area.sum())
    r1, r2 = rng.random(n), rng.random(n)
    s1 = np.sqrt(r1)
    R = T[el, 0] * (1 - s1)[:, None] + T[el, 1] * (s1 * (1 - r2))[:, None] + T[el, 2] * (s1 * r2)[:, None]
    N = R - m["C"]
    N /= np.linalg.norm(N, axis=1)[:, None]
    return R, N, (P, np.array(tris), np.array(pesos))


# ------------------------------------------------------------------------------------------------ peinados

def _guia_militar(p0, n0, m, cab, rng, desorden):
    u, E, C = m["u"], m["E"], m["C"]
    rel = (p0 - E) / u
    z, y = rel[2], rel[1]
    atras = np.array([0.0, 1.0, 0.0])
    abajo = np.array([0.0, 0.0, -1.0])
    arriba_cab = z > 0.072
    if arriba_cab:                         # arriba: 4–5 cm hacia atrás, prolijo, poco volumen
        L = (0.040 + 0.012 * rng.random()) * (1.0 if y < 0.08 else 0.85)
        obj = atras * 0.95 + desorden * 0.06
        h0, h1 = 0.0015, 0.0045 + (0.005 if y < 0.02 else 0.0)        # un poco de altura en el nacimiento
        pasos = 9
    else:                                  # degradé: de ~3 mm abajo a ~1,5 cm cerca de arriba
        f = np.clip((z + 0.06) / 0.13, 0, 1) ** 1.4
        L = 0.003 + 0.013 * f
        obj = abajo * 0.55 + atras * 0.6 + desorden * 0.05
        h0, h1 = 0.0004, 0.001 + 0.002 * f
        pasos = 4 if L < 0.008 else 6
    L *= u
    pts = [p0 + n0 * 0.0003 * u]
    p, d = pts[0], obj / np.linalg.norm(obj)
    for k in range(1, pasos + 1):
        fr = k / pasos
        h = (h0 + (h1 - h0) * math.sin(min(1.0, fr * 1.5) * math.pi * 0.5)) * u
        tang = d - n0 * np.dot(d, n0)
        q = p + tang / max(1e-9, np.linalg.norm(tang)) * (L / pasos)
        q, n0 = cab.capa(q, h, C)
        pts.append(q)
        p = q
    return np.array(pts), (0.15 if arriba_cab else 0.0)


def _guia_larga(p0, n0, m, cab, cuerpo, rng, desorden, largo):
    u, E, C = m["u"], m["E"], m["C"]
    x_raya = E[0] + 0.018 * u
    lado = 1.0 if p0[0] >= x_raya else -1.0
    rel = (p0 - E) / u
    paso = 0.010 * u
    h = (0.0018 + 0.006 * rng.random()) * u
    pts = [p0 + n0 * 0.0003 * u]
    p = pts[0]
    lateral = np.array([lado, 0.0, 0.0])
    atras = np.array([0.0, 1.0, 0.0])
    abajo = np.array([0.0, 0.0, -1.0])
    largo_total = largo * u
    hecho = 0.0
    d = None
    # 1) por el cráneo: desde la raya hacia el costado y hacia abajo; lo del frente se va hacia las orejas
    for k in range(60):
        frente = rel[1] < 0.05
        obj = lateral * 0.75 + abajo * 0.65 + (atras * 0.55 if frente else atras * 0.1) + desorden * 0.05
        nn = (p - C) / np.linalg.norm(p - C)
        tang = obj - nn * np.dot(obj, nn)
        tang /= max(1e-9, np.linalg.norm(tang))
        q, _ = cab.capa(p + tang * paso, h, C)
        hecho += np.linalg.norm(q - p)
        pts.append(q)
        d = q - p
        p = q
        r = (p - E) / u
        if (abs(r[0]) > 0.062 and r[2] < 0.01) or (r[1] > 0.11 and r[2] < 0.02) or r[2] < -0.03:
            break
    d = d / max(1e-9, np.linalg.norm(d)) if d is not None else abajo
    # 2) cae con la gravedad, por detrás de los hombros, sin atravesar cabeza ni cuerpo; onda suave al final
    hombro_z = E[2] - 0.18 * u
    fase = rng.random() * 6.28
    while hecho < largo_total:
        f = hecho / largo_total
        atras_k = 0.55 if p[2] > hombro_z - 0.06 * u else 0.08
        d = d * 0.55 + abajo * 0.45 + atras * atras_k * 0.4 + lateral * 0.03 + desorden * 0.02
        d /= np.linalg.norm(d)
        q = p + d * paso
        q += np.array([math.sin(fase + f * 9) * 0.0012 * u * f, 0, 0])            # onda suave hacia la punta
        q = cab.afuera(q, h * 0.8, C)
        q = cuerpo.afuera(q, 0.022 * u)
        hecho += np.linalg.norm(q - p)
        pts.append(q)
        p = q
    return np.array(pts), 0.9


def guias(pj, estilo, rng):
    m = marco(pj)
    cab = _Cabeza(pj)
    cuerpo = _Cuerpo(pj) if estilo == "largo_suelto" else None
    n = 2600 if estilo == "degrade_militar" else 1700
    R, N, _ = _raices(pj, m, estilo, n, rng)
    grupos = 220 if estilo == "degrade_militar" else 160
    cent = R[rng.choice(len(R), grupos, replace=False)]
    des = rng.normal(0, 1, (grupos, 3))
    out = []
    for i in range(len(R)):
        gi = int(np.argmin(np.linalg.norm(cent - R[i], axis=1)))
        if estilo == "degrade_militar":
            pts, suelto = _guia_militar(R[i], N[i], m, cab, rng, des[gi])
        else:
            rel = (R[i] - m["E"]) / m["u"]
            largo = 0.50 + 0.05 * rng.random() - (0.07 if rel[1] < 0.04 else 0.0)       # capas: adelante más corto
            pts, suelto = _guia_larga(R[i], N[i], m, cab, cuerpo, rng, des[gi], largo)
        out.append({"pts": pts, "suelto": suelto})
    return out


def hijos(gs: list, estilo: str, u: float, rng) -> list:
    """Hebras hijas alrededor de cada guía, que se juntan hacia la punta (mechas) con frizz."""
    n_h = 7 if estilo == "degrade_militar" else 14
    radio = (0.0025 if estilo == "degrade_militar" else 0.0045) * u
    aglom = 0.35 if estilo == "degrade_militar" else 0.6
    frizz = (0.0004 if estilo == "degrade_militar" else 0.0012) * u
    out = []
    for g in gs:
        P = g["pts"]
        n = len(P)
        s = np.linspace(0, 1, n)[:, None]
        for _ in range(n_h):
            off = rng.normal(0, radio, 3)
            ruido = np.cumsum(rng.normal(0, 1, (n, 3)), axis=0) / math.sqrt(n) * frizz
            Q = P + off * (1 - aglom * s ** 1.5) + ruido * s
            out.append({"pts": Q, "suelto": g["suelto"]})
    return gs + out


# ------------------------------------------------------------------------------------------------ materiales

def material_hebras(pid, color, melanina, rojizo):
    mat = bpy.data.materials.new(f"pelo_{pid}")
    mat.use_nodes = True
    nt = mat.node_tree
    for nd in list(nt.nodes):
        if nd.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(nd)
    out = next(nd for nd in nt.nodes if nd.type == "OUTPUT_MATERIAL")
    h = nt.nodes.new("ShaderNodeBsdfHairPrincipled")
    h.model = "CHIANG"
    h.parametrization = "MELANIN"
    for k, v in (("Melanin", melanina), ("Melanin Redness", rojizo), ("Roughness", 0.26),
                 ("Radial Roughness", 0.55), ("Coat", 0.14), ("IOR", 1.55), ("Offset", math.radians(6.0)),
                 ("Random Roughness", 0.42), ("Random Color", 0.14)):
        h.inputs[k].default_value = v
    h.inputs["Tint"].default_value = (1.0, 0.94, 0.86, 1)
    nt.links.new(h.outputs[0], out.inputs["Surface"])
    return mat


def _textura_mechon(pid, color, T=256):
    """Textura de las tarjetas: hebras finas verticales con transparencia, más ralas en la punta."""
    rng = np.random.default_rng(5)
    alto = T * 4
    img = np.zeros((alto, T, 4), dtype=np.float32)
    c = np.array(color, dtype=np.float32)
    ys = np.linspace(0, 1, alto)[:, None]                      # 0 = raíz (abajo de la imagen) … 1 = punta
    for _ in range(150):
        x = rng.uniform(0.06, 0.94) * T
        w = rng.uniform(0.6, 1.6)
        fin = rng.uniform(0.7, 1.0)
        xs = np.arange(T)[None, :]
        a = np.clip(1 - np.abs(xs - x - np.sin(ys * rng.uniform(3, 8)) * 3) / w, 0, 1) * (ys < fin)
        tono = c * rng.uniform(0.7, 1.35)
        img[:, :, :3] = np.maximum(img[:, :, :3], a[:, :, None] * tono)
        img[:, :, 3] = np.maximum(img[:, :, 3], a)
    img[:, :, :3] = np.where(img[:, :, 3:] > 0, img[:, :, :3] / np.maximum(img[:, :, 3:], 1e-4), c)
    im = bpy.data.images.new(f"mechon_{pid}", T, alto, alpha=True)
    im.pixels.foreach_set(img.ravel())
    im.pack()
    return im


def material_tarjetas(pid, color):
    mat = bpy.data.materials.new(f"pelo_tarjetas_{pid}")
    mat.use_nodes = True
    nt = mat.node_tree
    b = nt.nodes["Principled BSDF"]
    tx = nt.nodes.new("ShaderNodeTexImage")
    tx.image = _textura_mechon(pid, color)
    nt.links.new(tx.outputs["Color"], b.inputs["Base Color"])
    rd = nt.nodes.new("ShaderNodeMath")
    rd.operation = "ROUND"                                        # recorte por transparencia (glTF «MASK»)
    nt.links.new(tx.outputs["Alpha"], rd.inputs[0])
    nt.links.new(rd.outputs[0], b.inputs["Alpha"])
    b.inputs["Roughness"].default_value = 0.4
    mat.surface_render_method = "DITHERED"
    mat.use_backface_culling = False
    return mat


# ------------------------------------------------------------------------------------------------ objetos

def _a_hueso(ob, pj):
    arm = pj["armadura"]
    head = arm.data.bones["mixamorig:Head"]
    ob.parent = arm
    ob.parent_type = "BONE"
    ob.parent_bone = head.name
    ob.matrix_parent_inverse = (Matrix.Translation(head.tail_local) @ head.matrix_local.to_3x3().to_4x4()).inverted()


def _a_cabeza(ob, pj):
    """Mallas del pelo (tarjetas, cuero): pesos de piel al hueso de la cabeza, como las cejas (el GLB del visor lo
    respeta igual que la cabeza; colgarlas del hueso las corría de lugar en el teléfono)."""
    ob.parent = pj["armadura"]
    ob.matrix_parent_inverse = Matrix.Identity(4)
    ob.vertex_groups.new(name="mixamorig:Head").add(list(range(len(ob.data.vertices))), 1.0, "REPLACE")
    ob.modifiers.new("Armature", "ARMATURE").object = pj["armadura"]


def _vaiven(ob, intensidad):
    ng = bpy.data.node_groups.new(f"vaiven_{ob.name}", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N, L = ng.nodes, ng.links
    gi, go = N.new("NodeGroupInput"), N.new("NodeGroupOutput")
    sp = N.new("GeometryNodeSetPosition")
    t = N.new("GeometryNodeInputSceneTime")
    pos = N.new("GeometryNodeInputPosition")
    par = N.new("GeometryNodeSplineParameter")
    att = N.new("GeometryNodeInputNamedAttribute")
    att.data_type = "FLOAT"
    att.inputs["Name"].default_value = "suelto"
    vt = N.new("ShaderNodeMath")
    vt.operation = "MULTIPLY"
    vt.inputs[1].default_value = 0.3
    L.new(t.outputs["Seconds"], vt.inputs[0])
    ct = N.new("ShaderNodeCombineXYZ")
    L.new(vt.outputs[0], ct.inputs["Z"])
    esc = N.new("ShaderNodeVectorMath")
    esc.operation = "SCALE"
    esc.inputs["Scale"].default_value = 6.0
    L.new(pos.outputs["Position"], esc.inputs[0])
    sm = N.new("ShaderNodeVectorMath")
    sm.operation = "ADD"
    L.new(esc.outputs[0], sm.inputs[0])
    L.new(ct.outputs[0], sm.inputs[1])
    nz = N.new("ShaderNodeTexNoise")
    L.new(sm.outputs[0], nz.inputs["Vector"])
    cen = N.new("ShaderNodeVectorMath")
    cen.operation = "SUBTRACT"
    cen.inputs[1].default_value = (0.5, 0.5, 0.5)
    L.new(nz.outputs["Color"], cen.inputs[0])
    p2 = N.new("ShaderNodeMath")
    p2.operation = "POWER"
    p2.inputs[1].default_value = 2.0
    L.new(par.outputs["Factor"], p2.inputs[0])
    m1 = N.new("ShaderNodeMath")
    m1.operation = "MULTIPLY"
    L.new(p2.outputs[0], m1.inputs[0])
    L.new(att.outputs["Attribute"], m1.inputs[1])
    m2 = N.new("ShaderNodeMath")
    m2.operation = "MULTIPLY"
    m2.inputs[1].default_value = intensidad
    L.new(m1.outputs[0], m2.inputs[0])
    off = N.new("ShaderNodeVectorMath")
    off.operation = "SCALE"
    L.new(cen.outputs[0], off.inputs[0])
    L.new(m2.outputs[0], off.inputs["Scale"])
    L.new(gi.outputs["Geometry"], sp.inputs["Geometry"])
    L.new(off.outputs[0], sp.inputs["Offset"])
    L.new(sp.outputs["Geometry"], go.inputs["Geometry"])
    ob.modifiers.new("vaiven", "NODES").node_group = ng


def _tarjetas(pj, gs, estilo, mat, u, rng):
    """Una tarjeta por guía (de cada pocas): cinta acostada sobre el cráneo con la textura de mechón."""
    m = marco(pj)
    C = m["C"]
    V, F, UV = [], [], []
    paso = 1
    ancho = (0.0075 if estilo == "degrade_militar" else 0.012) * u
    for g in gs[::paso]:
        P = g["pts"]
        n = len(P)
        b0 = len(V)
        ux = rng.random() * 0.6
        for k in range(n):
            d = P[min(k + 1, n - 1)] - P[max(k - 1, 0)]
            d /= max(1e-9, np.linalg.norm(d))
            radial = P[k] - C
            lado = np.cross(d, radial)
            lado /= max(1e-9, np.linalg.norm(lado))
            w = ancho * (1 - 0.5 * k / max(1, n - 1))
            V += [P[k] - lado * w, P[k] + lado * w]
            v = k / max(1, n - 1)
            UV += [(ux, v), (ux + 0.4, v)]
        for k in range(n - 1):
            a = b0 + 2 * k
            q = [a, a + 1, a + 3, a + 2]
            # todas las tarjetas mirando hacia afuera del cráneo (el visor del teléfono descarta las de espaldas)
            v0, v1, v3 = V[a], V[a + 1], V[a + 2]
            nrm = np.cross(v1 - v0, v3 - v0)
            if np.dot(nrm, (v0 + v1) / 2 - C) < 0:
                q = q[::-1]
            F.append(q)
    me = bpy.data.meshes.new(f"pelo_visor_{pj['id']}")
    me.from_pydata([list(map(float, x)) for x in V], [], F)
    uv = np.array([UV[li] for poly in me.polygons for li in poly.vertices])
    me.uv_layers.new(name="UVMap").data.foreach_set("uv", uv.ravel())
    me.materials.append(mat)
    ob = bpy.data.objects.new(f"PELO_VISOR_{pj['id']}", me)
    pj["coleccion"].objects.link(ob)
    _a_cabeza(ob, pj)
    ob.hide_render = True
    return ob


def _cuero(pj, estilo, color):
    """Cuero cabelludo teñido del color del pelo debajo de las hebras (da densidad; en el degradé se ve como en una
    persona real)."""
    from estudio.blender import kit as K
    m = marco(pj)
    me0 = pj["cabeza_humana"]["obj"].data
    P = np.empty(len(me0.vertices) * 3)
    me0.vertices.foreach_get("co", P)
    P = P.reshape(-1, 3)
    nor = np.empty(len(me0.vertices) * 3)
    me0.vertices.foreach_get("normal", nor)
    nor = nor.reshape(-1, 3)
    tris, bajo = [], []
    for poly in me0.polygons:
        vs = list(poly.vertices)
        w = np.mean([con_pelo(P[x], m, estilo, 0.003) for x in vs])
        if w > 0.5:
            z = (P[vs, 2].mean() - m["E"][2]) / m["u"]
            for k in range(1, len(vs) - 1):
                tris.append((vs[0], vs[k], vs[k + 1]))
                bajo.append(estilo == "degrade_militar" and z < 0.045)
    usados = sorted({x for t in tris for x in t})
    loc = {g: i for i, g in enumerate(usados)}
    C = m["C"]
    V = []
    for g in usados:
        n = nor[g] if np.dot(nor[g], P[g] - C) > 0 else -nor[g]
        V.append(P[g] + n * 0.0006 * m["u"])
    caras = []
    for t in tris:
        c = [loc[a] for a in t]
        nrm = np.cross(V[c[1]] - V[c[0]], V[c[2]] - V[c[0]])
        caras.append(c if np.dot(nrm, V[c[0]] - C) > 0 else c[::-1])
    me = bpy.data.meshes.new(f"cuero_{pj['id']}")
    me.from_pydata([list(map(float, v)) for v in V], [], caras)
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    me.materials.append(K.material(f"cuero_{pj['id']}", tuple(c ** 2.2 * 0.85 for c in color), 0.75))
    # en el degradé, abajo se ve la piel a través del pelo cortito: un tono entre el pelo y la piel
    piel = pj["perfil"]["piel"]
    me.materials.append(K.material(f"cuero_bajo_{pj['id']}",
                                   tuple((c * 0.8 + p * 0.2) ** 2.2 * 0.9 for c, p in zip(color, piel)), 0.85))
    me.polygons.foreach_set("material_index", [1 if b else 0 for b in bajo])
    ob = bpy.data.objects.new(f"CUERO_{pj['id']}", me)
    pj["coleccion"].objects.link(ob)
    _a_cabeza(ob, pj)
    return ob


def construir(pj: dict, estilo: str, color, melanina: float, rojizo: float, semilla: int = 3) -> dict:
    rng = np.random.default_rng(semilla)
    u = pj["u"]
    gs = guias(pj, estilo, rng)
    todos = hijos(gs, estilo, u, rng)
    cv = bpy.data.hair_curves.new(f"pelo_{pj['id']}")
    cv.add_curves([len(h["pts"]) for h in todos])
    cv.attributes["position"].data.foreach_set(
        "vector", np.concatenate([h["pts"] for h in todos]).astype(np.float32).ravel())
    r0 = (0.00005 if estilo == "degrade_militar" else 0.000045) * u
    radio = cv.attributes.new("radius", "FLOAT", "POINT")
    radio.data.foreach_set("value", np.concatenate(
        [np.linspace(r0, r0 * 0.35, len(h["pts"])) for h in todos]).astype(np.float32))
    su = cv.attributes.new("suelto", "FLOAT", "POINT")
    su.data.foreach_set("value", np.concatenate(
        [np.full(len(h["pts"]), h["suelto"]) for h in todos]).astype(np.float32))
    cv.materials.append(material_hebras(pj["id"], color, melanina, rojizo))
    ob = bpy.data.objects.new(f"PELO_{pj['id']}", cv)
    pj["coleccion"].objects.link(ob)
    _a_hueso(ob, pj)
    _vaiven(ob, (0.004 if estilo == "degrade_militar" else 0.03) * u)
    ov = _tarjetas(pj, gs, estilo, material_tarjetas(pj["id"], color), u, rng)
    cuero = _cuero(pj, estilo, color)
    pj["pelo"] = {"curvas": ob, "visor": ov, "cuero": cuero, "hebras": len(todos)}
    return pj["pelo"]
