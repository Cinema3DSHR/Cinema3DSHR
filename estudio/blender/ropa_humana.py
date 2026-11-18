"""Ropa y zapatos de los personajes humanos (estudio/blender/humanos.py).

Cada prenda es una cáscara sobre el cuerpo del maniquí: se copian las caras de la zona (por los pesos de los huesos y
la altura), se separan de la piel el grosor de la tela, se alisan (la ropa no marca abdominales) sin dejar que entren
en el cuerpo, y se engrosan. Siguen al esqueleto con los mismos pesos del cuerpo. La piel tapada se borra.
Detalles armados aparte, con los pesos del cuerpo más cercano: capucha caída, bolsillo canguro, cordones con
punteras, puños y cintura acanalados, bolsillos y costuras de jean con hilo naranja, botones y remaches, cuello y
bolsillos con tapa de la campera, zapatillas con suela de goma, cordones y talón, cartera cruzada y aros.

VESTUARIO (PERFIL): {"prendas": ["buzo_capucha", "jean_recto", "zapatillas"], "colores": {...}}
Todas las medidas se dan en metros reales y se pasan a unidades del modelo con `u` (pj["u"]).
"""
from __future__ import annotations
import math

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree


# ------------------------------------------------------------------------------------------------ materiales

def _lin(c):
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)


def tela(nombre: str, color_srgb, rug=0.85, tipo="algodon", brillo=0.0) -> bpy.types.Material:
    """Tela para Cycles. tipo: algodon (felpa del buzo, remera), jean (sarga diagonal), cuero, goma, metal, hilo."""
    if nombre in bpy.data.materials:
        return bpy.data.materials[nombre]
    c = _lin(color_srgb)
    mat = bpy.data.materials.new(nombre)
    mat.use_nodes = True
    nt = mat.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*c, 1)
    b.inputs["Roughness"].default_value = rug
    metal = 1.0 if tipo == "metal" else 0.0
    b.inputs["Metallic"].default_value = metal
    if tipo in ("algodon", "jean"):
        b.inputs["Sheen Weight"].default_value = 0.6 if tipo == "algodon" else 0.25
        b.inputs["Sheen Roughness"].default_value = 0.4
        b.inputs["Sheen Tint"].default_value = (*[min(1, x * 2.5 + 0.1) for x in c], 1)
    if tipo == "cuero":
        b.inputs["Coat Weight"].default_value = 0.25
        b.inputs["Coat Roughness"].default_value = 0.35
    geo = nt.nodes.new("ShaderNodeTexCoord")
    if tipo == "jean":
        # sarga: rayas finas en diagonal + desgaste (aclarado) con ruido
        w = nt.nodes.new("ShaderNodeTexWave")
        w.wave_type = "BANDS"
        w.bands_direction = "DIAGONAL"
        w.inputs["Scale"].default_value = 900.0
        w.inputs["Distortion"].default_value = 1.5
        nt.links.new(geo.outputs["Object"], w.inputs["Vector"])
        nz = nt.nodes.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = 9.0
        nz.inputs["Detail"].default_value = 8.0
        nt.links.new(geo.outputs["Object"], nz.inputs["Vector"])
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.35
        ramp.color_ramp.elements[0].color = (*[x * 0.75 for x in c], 1)
        ramp.color_ramp.elements[1].position = 0.75
        ramp.color_ramp.elements[1].color = (*[min(1, x * 1.6 + 0.01) for x in c], 1)
        nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = 0.25
        nt.links.new(ramp.outputs["Color"], mix.inputs[6])
        nt.links.new(w.outputs["Color"], mix.inputs[7])
        nt.links.new(mix.outputs[2], b.inputs["Base Color"])
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.35
        bump.inputs["Distance"].default_value = 0.0006
        nt.links.new(w.outputs["Fac"], bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    elif tipo in ("algodon", "cuero", "goma", "acanalado"):
        nz = nt.nodes.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = {"algodon": 420.0, "cuero": 160.0, "goma": 60.0, "acanalado": 40.0}[tipo]
        nz.inputs["Detail"].default_value = 10.0
        nt.links.new(geo.outputs["Object"], nz.inputs["Vector"])
        alto = nz.outputs["Fac"]
        if tipo == "acanalado":
            w = nt.nodes.new("ShaderNodeTexWave")
            w.wave_type = "BANDS"
            w.bands_direction = "Z"
            w.inputs["Scale"].default_value = 260.0
            nt.links.new(geo.outputs["Object"], w.inputs["Vector"])
            alto = w.outputs["Fac"]
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = {"algodon": 0.25, "cuero": 0.18, "goma": 0.1, "acanalado": 0.5}[tipo]
        bump.inputs["Distance"].default_value = 0.0008
        nt.links.new(alto, bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    mat.diffuse_color = (*c, 1)
    mat["estudio"] = {"color": list(c), "rugosidad": rug, "metal": metal, "emision": None, "fuerza": 0.0,
                      "alfa": 1.0}
    return mat


# ------------------------------------------------------------------------------------------------ utilidades

def _reposo(pj: dict) -> dict:
    """Posiciones y normales de reposo (espacio de la armadura), pesos por vértice y huesos del maniquí."""
    malla, arm = pj["malla"], pj["armadura"]
    M = arm.matrix_world.inverted() @ malla.matrix_world
    me = malla.data
    n = len(me.vertices)
    co = np.empty(n * 3)
    me.vertices.foreach_get("co", co)
    no = np.empty(n * 3)
    me.vertices.foreach_get("normal", no)
    A = np.array(M)
    pos = co.reshape(n, 3) @ A[:3, :3].T + A[:3, 3]
    nor = no.reshape(n, 3) @ np.array(M.to_3x3().inverted().transposed()).T
    nor /= np.maximum(1e-9, np.linalg.norm(nor, axis=1))[:, None]
    gname = {g.index: g.name.replace("mixamorig:", "") for g in malla.vertex_groups}
    pesos = [{gname[g.group]: g.weight for g in v.groups if g.weight > 1e-4} for v in me.vertices]
    huesos = {b.name.replace("mixamorig:", ""): (Vector(b.head_local), Vector(b.tail_local)) for b in arm.data.bones}
    return {"pos": pos, "nor": nor, "pesos": pesos, "huesos": huesos, "M": M}


class Cuerpo:
    """El cuerpo en reposo (espacio de la armadura) para medir, proyectar y copiar pesos."""

    def __init__(self, pj: dict):
        self.rep = _reposo(pj)
        self.pj = pj
        me = pj["malla"].data
        self.caras = [list(p.vertices) for p in me.polygons]
        self.pos = self.rep["pos"]
        self.nor = self.rep["nor"]
        self.pesos = self.rep["pesos"]
        self.h = {k: (np.array(a), np.array(b)) for k, (a, b) in self.rep["huesos"].items()}
        bm = bmesh.new()
        for p in self.pos:
            bm.verts.new(Vector(p))
        bm.verts.ensure_lookup_table()
        for f in self.caras:
            try:
                bm.faces.new([bm.verts[i] for i in f])
            except ValueError:
                pass
        bm.normal_update()
        self.bvh = BVHTree.FromBMesh(bm)
        bm.free()
        self.kd = KDTree(len(self.pos))
        for i, p in enumerate(self.pos):
            self.kd.insert(Vector(p), i)
        self.kd.balance()
        self.u = pj["u"]
        self.nor = self._hacia_afuera()
        vec = {}
        for i, f in enumerate(self.caras):
            for a, b2 in zip(f, f[1:] + f[:1]):
                vec.setdefault(a, set()).add(b2)
                vec.setdefault(b2, set()).add(a)
        self.vecinos = vec

    def _radial(self, i: int, p=None) -> np.ndarray:
        p = self.pos[i] if p is None else p
        pw = self.pesos[i]
        if not pw:
            return np.zeros(3)
        g = max(pw, key=pw.get)
        if g not in self.h:
            return np.zeros(3)
        a, b = self.h[g]
        ab = b - a
        t = np.clip(np.dot(p - a, ab) / max(1e-12, np.dot(ab, ab)), 0, 1)
        r = p - (a + ab * t)
        return r / max(1e-9, np.linalg.norm(r))

    def _hacia_afuera(self) -> np.ndarray:
        """Normales del maniquí orientadas hacia afuera (algunas vienen invertidas): se compara con la dirección
        desde el hueso que mueve al vértice y, si no coincide, se da vuelta; se mezclan un poco las dos."""
        out = self.nor.copy()
        for i in range(len(out)):
            r = self._radial(i)
            if not r.any():
                continue
            n = out[i]
            if np.dot(n, r) < 0:
                n = -n
            m = n * 0.6 + r * 0.4
            out[i] = m / max(1e-9, np.linalg.norm(m))
        return out

    def w(self, i: int, *nombres) -> float:
        return sum(x for k, x in self.pesos[i].items() if any(k.startswith(n) for n in nombres))

    def sobre(self, p, h: float):
        """Punto de la superficie más cercano, llevado h hacia afuera."""
        q, n, _, _ = self.bvh.find_nearest(Vector(p), 10.0)
        if q is None:
            return np.asarray(p, dtype=float), np.array([0.0, -1.0, 0.0])
        return np.array(q) + np.array(n) * h, np.array(n)

    def pesos_de(self, p) -> dict:
        out, tot = {}, 0.0
        for co, i, d in self.kd.find_n(Vector(p), 3):
            k = 1.0 / max(d, 1e-5)
            tot += k
            for g, x in self.pesos[i].items():
                out[g] = out.get(g, 0.0) + k * x
        return {g: x / tot for g, x in out.items()}


def _objeto(nombre: str, pj: dict, V, F, mats, mat_idx=None, pesos=None, cuerpo: Cuerpo | None = None,
            suave=True, subdiv=0, solidificar=0.0):
    me = bpy.data.meshes.new(nombre)
    me.from_pydata([list(map(float, v)) for v in V], [], [list(f) for f in F])
    me.update()
    for m in mats:
        me.materials.append(m)
    if mat_idx is not None and len(me.polygons):
        me.polygons.foreach_set("material_index", list(mat_idx))
    me.polygons.foreach_set("use_smooth", [suave] * len(me.polygons))
    ob = bpy.data.objects.new(nombre, me)
    pj["coleccion"].objects.link(ob)
    arm = pj["armadura"]
    ob.parent = arm
    ob.matrix_parent_inverse = Matrix.Identity(4)
    if pesos is None and cuerpo is not None:
        pesos = [cuerpo.pesos_de(v) for v in V]
    grupos = {}
    for i, pw in enumerate(pesos or []):
        for g, x in pw.items():
            if x < 0.01:
                continue
            nm = "mixamorig:" + g
            if nm not in grupos:
                grupos[nm] = ob.vertex_groups.new(name=nm)
            grupos[nm].add([i], x, "REPLACE")
    if solidificar:
        so = ob.modifiers.new("grosor", "SOLIDIFY")
        so.thickness = solidificar
        so.offset = -1.0
        so.use_rim = True
        so.use_even_offset = True
    if subdiv:
        sd = ob.modifiers.new("suave", "SUBSURF")
        sd.levels = 0
        sd.render_levels = subdiv
    ob.modifiers.new("Armature", "ARMATURE").object = arm
    return ob


def _tubo(puntos, radio: float, lados: int = 6):
    """Tubo a lo largo de una polilínea: (vértices, caras)."""
    puntos = np.asarray(puntos, dtype=float)
    V, F = [], []
    n = len(puntos)
    for k in range(n):
        d = puntos[min(k + 1, n - 1)] - puntos[max(k - 1, 0)]
        d /= max(1e-9, np.linalg.norm(d))
        a = np.cross(d, [0, 0, 1.0]) if abs(d[2]) < 0.9 else np.cross(d, [1.0, 0, 0])
        a /= np.linalg.norm(a)
        b = np.cross(d, a)
        for j in range(lados):
            t = 2 * math.pi * j / lados
            V.append(puntos[k] + (a * math.cos(t) + b * math.sin(t)) * radio)
    for k in range(n - 1):
        for j in range(lados):
            a0 = k * lados + j
            a1 = k * lados + (j + 1) % lados
            F.append([a0, a1, a1 + lados, a0 + lados])
    return V, F


def _juntar(partes):
    V, F = [], []
    for v, f in partes:
        base = len(V)
        V += list(v)
        F += [[base + i for i in c] for c in f]
    return V, F


# ------------------------------------------------------------------------------------------------ cáscaras

def cascara(cb: Cuerpo, nombre: str, mascara: np.ndarray, grosor: np.ndarray, mats: list, suavizado: int = 10,
            minimo: float | None = None, mat_cara=None, solidificar: float = 0.0, borrar_piel=True, extra_caras=None):
    """Prenda desde las caras del cuerpo donde mascara es verdadera."""
    sel = [i for i, f in enumerate(cb.caras) if all(mascara[v] for v in f)]
    if extra_caras is not None:
        sel = [i for i in sel if extra_caras(i)]
    usados = sorted({v for i in sel for v in cb.caras[i]})
    loc = {g: k for k, g in enumerate(usados)}
    P = cb.pos[usados] + cb.nor[usados] * grosor[usados][:, None]
    F = [[loc[v] for v in cb.caras[i]] for i in sel]
    # vecinos dentro de la prenda (borde: menos alisado)
    vec = [[loc[x] for x in cb.vecinos.get(g, ()) if x in loc] for g in usados]
    borde = np.array([len(cb.vecinos.get(g, ())) != len(v) for g, v in zip(usados, vec)])
    g_min = grosor[usados] * 0.8 if minimo is None else np.full(len(usados), minimo)
    nb = [np.array(vs, dtype=np.int64) for vs in vec]
    for it in range(suavizado):
        # alisado: borra músculos y relieves del cuerpo; lo que encoge lo devuelve el control de distancia mínima
        for factor in (0.6,):
            Q = P.copy()
            for k, vs in enumerate(nb):
                if len(vs):
                    Q[k] = P[k] + (P[vs].mean(axis=0) - P[k]) * factor * (0.5 if borde[k] else 1.0)
            P = Q
        if it % 2 == 1 or it == suavizado - 1:
            for k in range(len(P)):
                q, n, fi, _ = cb.bvh.find_nearest(Vector(P[k]), 10.0)
                if q is None:
                    continue
                q, n = np.array(q), np.array(n)
                r = cb._radial(usados[k], q)
                if np.dot(n, r) < 0:
                    n = -n
                if np.linalg.norm(P[k] - q) > 4 * g_min[k] + 1e-6:
                    continue                           # la superficie más cercana es otra parte (mentón): no empujar
                if np.dot(P[k] - q, n) < g_min[k]:
                    P[k] = q + n * g_min[k]
    idx = [mat_cara(i) for i in sel] if mat_cara else None
    ob = _objeto(nombre, cb.pj, P, F, mats, idx, pesos=[cb.pesos[g] for g in usados], subdiv=1,
                 solidificar=solidificar)
    if borrar_piel:
        # la piel tapada se borra (menos un anillo en el borde, para que no se vea un hueco)
        dentro = set(usados)
        for g in usados:
            if any(x not in dentro for x in cb.vecinos.get(g, ())):
                dentro.discard(g)
        cb.pj.setdefault("_piel_tapada", set()).update(dentro)
    ob["usados"] = len(usados)
    return ob, P, usados


def borrar_piel_tapada(pj: dict):
    tap = pj.pop("_piel_tapada", set())
    if not tap:
        return
    me = pj["malla"].data
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    caras = [f for f in bm.faces if all(v.index in tap for v in f.verts)]
    bmesh.ops.delete(bm, geom=caras, context="FACES_ONLY")
    bm.to_mesh(me)
    bm.free()


# ------------------------------------------------------------------------------------------------ medidas

def _medidas(cb: Cuerpo) -> dict:
    h = cb.h
    u = cb.u
    z_cadera = h["LeftUpLeg"][0][2]
    z_cuello = h["Neck"][0][2]
    z_tobillo = h["LeftFoot"][0][2]
    return {"z_cadera": z_cadera, "z_cuello": z_cuello, "z_tobillo": z_tobillo, "u": u,
            "z_cintura": z_cadera + 0.09 * u, "x0": h["Hips"][0][0], "y0": h["Hips"][0][1],
            "z_piso": cb.pos[:, 2].min()}


def _zona(cb: Cuerpo):
    """Clasificación por vértice: torso, brazo (hasta la muñeca), mano, pierna, pie, cuello/cabeza."""
    n = len(cb.pos)
    z = cb.pos[:, 2]
    M = _medidas(cb)
    mano = np.array([cb.w(i, "LeftHand", "RightHand") > 0.35 for i in range(n)])
    brazo = np.array([cb.w(i, "LeftArm", "RightArm", "LeftForeArm", "RightForeArm") > 0.35 for i in range(n)]) & ~mano
    pie = np.array([cb.w(i, "LeftFoot", "RightFoot", "LeftToe", "RightToe") > 0.4 for i in range(n)])
    pierna = np.array([cb.w(i, "LeftUpLeg", "RightUpLeg", "LeftLeg", "RightLeg") > 0.3 for i in range(n)]) & ~pie
    cabeza = np.array([cb.w(i, "Head", "Neck") > 0.5 for i in range(n)])
    torso = ~(mano | brazo | pie | pierna | cabeza)
    return {"mano": mano, "brazo": brazo, "pie": pie, "pierna": pierna, "cabeza": cabeza, "torso": torso,
            "z": z, "M": M}


# ------------------------------------------------------------------------------------------------ prendas

def buzo_capucha(cb: Cuerpo, Z: dict, color=(0.035, 0.035, 0.04), nombre="buzo"):
    pj, u, M = cb.pj, cb.u, Z["M"]
    z = Z["z"]
    # largo: hasta la cadera; sin cuello (el escote va al pie del cuello)
    tapa = (Z["torso"] | Z["brazo"] | (Z["cabeza"] & (z < M["z_cuello"] - 0.005 * u)) |
            (Z["pierna"] & (z > M["z_cadera"] - 0.02 * u)))
    tapa &= z > M["z_cadera"] - 0.06 * u
    # el buzo «cuelga»: más holgado en el torso que en los brazos
    gro = np.where(Z["brazo"], 0.022 * u, 0.032 * u)
    gro = np.where(Z["torso"] & (z < M["z_cintura"]), 0.038 * u, gro)
    base = tela(f"{nombre}_{pj['id']}", color, 0.92, "algodon")
    rib = tela(f"{nombre}_rib_{pj['id']}", tuple(c * 0.9 for c in color), 0.95, "acanalado")
    # puños y cintura acanalados: caras a pocos cm del borde de la prenda
    mano_cent = {}
    for lado in ("Left", "Right"):
        mano_cent[lado] = cb.h[f"{lado}Hand"][0]

    def mat_cara(i):
        vs = cb.caras[i]
        p = cb.pos[vs].mean(axis=0)
        if p[2] < M["z_cadera"] - 0.06 * u + 0.055 * u:
            return 1
        for lado, c in mano_cent.items():
            if np.linalg.norm(p - c) < 0.075 * u and Z["brazo"][vs].all():
                return 1
        return 0
    ob, P, usados = cascara(cb, f"BUZO_{pj['id']}", tapa, gro, [base, rib], suavizado=30, mat_cara=mat_cara,
                            solidificar=0.003 * u)
    partes = [ob]
    # --- capucha caída sobre la espalda: un parche de la espalda inflado, con el borde enrollado
    sel = [k for k, g in enumerate(usados) if cb.pos[g][1] > M["y0"] - 0.005 * u and
           M["z_cuello"] - 0.20 * u < cb.pos[g][2] < M["z_cuello"] + 0.01 * u and
           abs(cb.pos[g][0] - M["x0"]) < 0.13 * u and not Z["brazo"][g]]
    if sel:
        selset = set(sel)
        loc = {k: i for i, k in enumerate(sel)}
        caras = []
        for f in ob.data.polygons:
            if all(v in selset for v in f.vertices):
                caras.append([loc[v] for v in f.vertices])
        Q = []
        for k in sel:
            g = usados[k]
            p = P[k]
            fz = (p[2] - (M["z_cuello"] - 0.20 * u)) / (0.21 * u)
            fx = 1 - (abs(p[0] - M["x0"]) / (0.13 * u)) ** 2
            bulto = 0.035 * u * math.sin(max(0.0, min(1.0, fz)) * math.pi * 0.85) * max(0.0, fx) ** 0.6
            Q.append(p + cb.nor[g] * (0.008 * u + bulto * 1.5))
        partes.append(_objeto(f"CAPUCHA_{pj['id']}", pj, Q, caras, [base], cuerpo=cb, subdiv=1,
                              solidificar=0.004 * u))
        # borde enrollado de la capucha alrededor del cuello
        cen = cb.h["Neck"][0]
        r_c = np.median([np.linalg.norm((cb.pos[i] - cen)[:2]) for i in range(len(cb.pos))
                         if Z["cabeza"][i] and abs(cb.pos[i][2] - cen[2]) < 0.02 * u]) if True else 0.06 * u
        ruta = []
        for a in np.linspace(-0.15 * math.pi, 1.15 * math.pi, 28):
            ruta.append(cen + np.array([math.cos(a) * (r_c + 0.045 * u), math.sin(a) * (r_c + 0.05 * u) + 0.012 * u,
                                        0.015 * u * math.sin(a)]))
        V, F = _tubo(ruta, 0.02 * u, 10)
        partes.append(_objeto(f"CAPUCHA_BORDE_{pj['id']}", pj, V, F, [base], cuerpo=cb, subdiv=1))
        # cordones con punteras
        cordon = tela(f"cordon_{pj['id']}", (0.82, 0.82, 0.80), 0.8, "algodon")
        metal = tela(f"puntera_{pj['id']}", (0.75, 0.75, 0.78), 0.25, "metal")
        cords, punt = [], []
        for lado in (-1, 1):
            p0 = cen + np.array([lado * 0.035 * u, -(r_c + 0.025 * u), -0.01 * u])
            pts = []
            for k in range(10):
                q = p0 + np.array([lado * 0.003 * u * k / 9, 0, -0.16 * u * k / 9])
                q, _ = cb.sobre(q, 0.046 * u)
                pts.append(q)
            cords.append(_tubo(pts, 0.0028 * u, 6))
            punt.append(_tubo([pts[-1], pts[-1] + (pts[-1] - pts[-2]) * 0.5], 0.0032 * u, 8))
        V, F = _juntar(cords)
        partes.append(_objeto(f"CORDONES_{pj['id']}", pj, V, F, [cordon], cuerpo=cb))
        V, F = _juntar(punt)
        partes.append(_objeto(f"PUNTERAS_{pj['id']}", pj, V, F, [metal], cuerpo=cb))
    # --- bolsillo canguro: parche del frente de la panza
    sel = [k for k, g in enumerate(usados) if cb.pos[g][1] < M["y0"] - 0.02 * u and
           M["z_cadera"] - 0.0 * u < cb.pos[g][2] < M["z_cintura"] + 0.06 * u and
           abs(cb.pos[g][0] - M["x0"]) < 0.11 * u * (1 - 0.3 * (cb.pos[g][2] - M["z_cadera"]) / (0.15 * u))
           and not Z["brazo"][g]]
    if sel:
        selset = set(sel)
        loc = {k: i for i, k in enumerate(sel)}
        caras = [[loc[v] for v in f.vertices] for f in ob.data.polygons if all(v in selset for v in f.vertices)]
        Q = [P[k] + cb.nor[usados[k]] * 0.007 * u for k in sel]
        partes.append(_objeto(f"BOLSILLO_{pj['id']}", pj, Q, caras, [base], cuerpo=cb, subdiv=1,
                              solidificar=0.003 * u))
    return partes


def remera(cb: Cuerpo, Z: dict, color=(0.06, 0.08, 0.20), nombre="remera"):
    pj, u, M = cb.pj, cb.u, Z["M"]
    z = Z["z"]
    hombro = {l: cb.h[f"{l}Arm"][0] for l in ("Left", "Right")}
    brazo_corto = np.array([Z["brazo"][i] and min(np.linalg.norm(cb.pos[i] - c) for c in hombro.values()) < 0.14 * u
                            for i in range(len(cb.pos))])
    tapa = (Z["torso"] | brazo_corto | (Z["pierna"] & (z > M["z_cadera"] - 0.01 * u))) & (z > M["z_cadera"] - 0.04 * u)
    # escote redondo: un poco más bajo adelante
    tapa &= ~((z > M["z_cuello"] - 0.025 * u) & (cb.pos[:, 1] < M["y0"] - 0.02 * u))
    tapa &= z < M["z_cuello"] + 0.002 * u
    gro = np.full(len(cb.pos), 0.008 * u)
    ob, P, us = cascara(cb, f"REMERA_{pj['id']}", tapa, gro, [tela(f"{nombre}_{pj['id']}", color, 0.85)],
                        suavizado=16, solidificar=0.0018 * u)
    return [ob]


def campera_jean(cb: Cuerpo, Z: dict, color=(0.30, 0.42, 0.58), nombre="campera"):
    pj, u, M = cb.pj, cb.u, Z["M"]
    z = Z["z"]
    x = cb.pos[:, 0] - M["x0"]
    adelante = cb.pos[:, 1] < M["y0"] - 0.0
    abierta = adelante & (np.abs(x) < 0.05 * u) & (z < M["z_cuello"] - 0.02 * u)
    tapa = (Z["torso"] | Z["brazo"]) & (z > M["z_cintura"] - 0.02 * u) & ~abierta
    gro = np.where(Z["brazo"], 0.022 * u, 0.030 * u)
    jean = tela(f"{nombre}_{pj['id']}", color, 0.8, "jean")
    ob, P, usados = cascara(cb, f"CAMPERA_{pj['id']}", tapa, gro, [jean], suavizado=26,
                            solidificar=0.0035 * u, borrar_piel=False)
    partes = [ob]
    hilo = tela(f"hilo_{pj['id']}", (0.78, 0.48, 0.18), 0.6)
    boton = tela(f"boton_{pj['id']}", (0.62, 0.42, 0.22), 0.3, "metal")
    # cuello volcado: anillo ancho alrededor del pie del cuello, abierto adelante
    cen = cb.h["Neck"][0]
    r_c = 0.068 * u
    filas = []
    for t in np.linspace(0, 1, 4):
        fila = []
        for a in np.linspace(-0.38 * math.pi, 1.38 * math.pi, 30):
            r = r_c + 0.012 * u + 0.03 * u * t
            fila.append(cen + np.array([math.cos(a) * r, math.sin(a) * r * 1.05 + 0.008 * u,
                                        0.012 * u - 0.03 * u * t]))
        filas.append(fila)
    V = [p for f in filas for p in f]
    n = len(filas[0])
    F = [[i * n + j, i * n + j + 1, (i + 1) * n + j + 1, (i + 1) * n + j] for i in range(3) for j in range(n - 1)]
    partes.append(_objeto(f"CUELLO_CAMPERA_{pj['id']}", pj, V, F, [jean], cuerpo=cb, subdiv=1,
                          solidificar=0.003 * u))
    # bolsillos con tapa en el pecho, botones y costuras en hilo naranja
    piezas_b, piezas_h = [], []
    pecho_z = cb.h["Spine2"][0][2] + 0.02 * u
    for lado in (-1, 1):
        cx = M["x0"] + lado * 0.085 * u
        # tapa del bolsillo: cuadrito proyectado sobre la campera
        tapa_pts = []
        for j, zz in enumerate(np.linspace(pecho_z + 0.03 * u, pecho_z - 0.01 * u, 3)):
            fila = []
            for xx in np.linspace(cx - 0.05 * u, cx + 0.05 * u, 6):
                q, _ = cb.sobre(np.array([xx, M["y0"] - 0.2 * u, zz]), 0.028 * u)
                fila.append(q)
            tapa_pts.append(fila)
        V = [p for f in tapa_pts for p in f]
        F = [[i * 6 + j, i * 6 + j + 1, (i + 1) * 6 + j + 1, (i + 1) * 6 + j] for i in range(2) for j in range(5)]
        partes.append(_objeto(f"TAPA_BOLSILLO_{lado}_{pj['id']}", pj, V, F, [jean], cuerpo=cb,
                              solidificar=0.003 * u))
        piezas_h.append(_tubo(tapa_pts[-1], 0.0007 * u, 4))
        bq, _ = cb.sobre(np.array([cx, M["y0"] - 0.2 * u, pecho_z - 0.006 * u]), 0.033 * u)
        piezas_b.append(_esfera(bq, 0.0055 * u))
        # botones del frente, al borde de la abertura
        for zz in np.linspace(M["z_cintura"] + 0.02 * u, M["z_cuello"] - 0.06 * u, 5):
            bq, _ = cb.sobre(np.array([M["x0"] + lado * 0.058 * u, M["y0"] - 0.2 * u, zz]), 0.026 * u)
            piezas_b.append(_esfera(bq, 0.0065 * u))
        # costura vertical (pinza) del bolsillo a la cintura
        ruta = [cb.sobre(np.array([cx, M["y0"] - 0.2 * u, zz]), 0.025 * u)[0]
                for zz in np.linspace(pecho_z - 0.02 * u, M["z_cintura"] + 0.01 * u, 12)]
        piezas_h.append(_tubo(ruta, 0.0006 * u, 4))
    V, F = _juntar(piezas_b)
    partes.append(_objeto(f"BOTONES_{pj['id']}", pj, V, F, [boton], cuerpo=cb))
    V, F = _juntar(piezas_h)
    partes.append(_objeto(f"COSTURAS_CAMPERA_{pj['id']}", pj, V, F, [hilo], cuerpo=cb))
    return partes


def _esfera(c, r, n=8):
    V, F = [], []
    for i in range(n + 1):
        th = math.pi * i / n
        for j in range(n * 2):
            ph = 2 * math.pi * j / (n * 2)
            V.append(c + r * np.array([math.sin(th) * math.cos(ph), math.sin(th) * math.sin(ph), math.cos(th) * 0.55]))
    for i in range(n):
        for j in range(n * 2):
            a = i * n * 2 + j
            b = i * n * 2 + (j + 1) % (n * 2)
            F.append([a, b, b + n * 2, a + n * 2])
    return V, F


def jean(cb: Cuerpo, Z: dict, color=(0.06, 0.065, 0.08), holgura=0.011, nombre="jean"):
    pj, u, M = cb.pj, cb.u, Z["M"]
    z = Z["z"]
    # todo lo que está entre el tobillo y la cintura (el pie del maniquí tiene peso hasta media pantorrilla)
    tapa = ~(Z["mano"] | Z["brazo"] | Z["cabeza"]) & (z < M["z_cintura"]) & (z > M["z_tobillo"] + 0.01 * u)
    # recto: la botamanga cae derecha (más holgura de la rodilla para abajo); chupín: parejo
    rodilla = (cb.h["LeftLeg"][0][2] + cb.h["RightLeg"][0][2]) / 2
    caida = np.clip((rodilla - z) / max(1e-6, rodilla - M["z_tobillo"]), 0, 1)
    gro = (holgura + (0.012 if holgura > 0.009 else 0.002) * caida) * u
    gro = np.where(z > M["z_cadera"] - 0.03 * u, holgura * 0.75 * u, gro)
    tj = tela(f"{nombre}_{pj['id']}", color, 0.82, "jean")
    cint = tela(f"{nombre}_cintura_{pj['id']}", tuple(c * 0.92 for c in color), 0.8, "jean")

    def mat_cara(i):
        return 1 if cb.pos[cb.caras[i]].mean(axis=0)[2] > M["z_cintura"] - 0.035 * u else 0
    ob, P, usados = cascara(cb, f"JEAN_{pj['id']}", tapa, gro, [tj, cint], suavizado=22, mat_cara=mat_cara,
                            solidificar=0.0025 * u)
    partes = [ob]
    hilo = tela(f"hilo_jean_{pj['id']}", (0.80, 0.50, 0.20), 0.6)
    metal = tela(f"remache_{pj['id']}", (0.72, 0.55, 0.30), 0.3, "metal")
    h_l, h_r = [], []
    zc = M["z_cintura"]
    # costuras laterales (de la cintura al tobillo, por el costado de cada pierna)
    for lado in ("Left", "Right"):
        cad = cb.h[f"{lado}UpLeg"][0]
        rod = cb.h[f"{lado}Leg"][0]
        tob = cb.h[f"{lado}Foot"][0]
        sgn = 1 if cad[0] > M["x0"] else -1
        ruta = []
        for t in np.linspace(0, 1, 26):
            if t < 0.5:
                c = np.array([cad[0], cad[1], zc]) + (rod - np.array([cad[0], cad[1], zc])) * (t / 0.5)
            else:
                c = rod + (tob + np.array([0, 0, 0.04 * u]) - rod) * ((t - 0.5) / 0.5)
            hit = cb.bvh.ray_cast(Vector(c + np.array([sgn * 0.3 * u, 0, 0])), Vector((-sgn, 0, 0)), 0.3 * u)
            if hit[0] is not None:
                ruta.append(np.array(hit[0]) + np.array(hit[1]) * (holgura + 0.003) * u)
        if len(ruta) > 3:
            h_l.append(_tubo(ruta, 0.0006 * u, 4))
        # bolsillo trasero: pentágono de costura
        cx = cad[0] * 0.75 + M["x0"] * 0.25
        pent = [(-0.07, 0.0), (0.07, 0.0), (0.065, -0.11), (0.0, -0.135), (-0.065, -0.11), (-0.07, 0.0)]
        ruta = []
        for (dx, dz) in pent:
            for s in np.linspace(0, 1, 4)[:-1]:
                pass
            hit = cb.bvh.ray_cast(Vector((cx + dx * u * 0.85, M["y0"] + 0.4 * u, zc - 0.035 * u + dz * u)),
                                  Vector((0, -1, 0)), 0.5 * u)
            if hit[0] is not None:
                ruta.append(np.array(hit[0]) + np.array(hit[1]) * (holgura + 0.004) * u)
        if len(ruta) == len(pent):
            densa = []
            for a, b in zip(ruta, ruta[1:]):
                for s in np.linspace(0, 1, 6)[:-1]:
                    densa.append(a + (b - a) * s)
            densa.append(ruta[-1])
            h_r.append(_tubo(densa, 0.0007 * u, 4))
            # remaches en las esquinas de arriba
            h_r.append(_esfera(ruta[0], 0.0025 * u, 5))
            h_r.append(_esfera(ruta[1], 0.0025 * u, 5))
        # bolsillo delantero: curva
        ruta = []
        for t in np.linspace(0, 1, 10):
            px = M["x0"] + sgn * (0.06 + 0.07 * t) * u
            pz = zc - 0.005 * u - 0.07 * u * (1 - t) ** 1.5
            hit = cb.bvh.ray_cast(Vector((px, M["y0"] - 0.4 * u, pz)), Vector((0, 1, 0)), 0.5 * u)
            if hit[0] is not None:
                ruta.append(np.array(hit[0]) + np.array(hit[1]) * (holgura + 0.003) * u)
        if len(ruta) > 3:
            h_l.append(_tubo(ruta, 0.0006 * u, 4))
    # botón de la cintura y la bragueta
    hit = cb.bvh.ray_cast(Vector((M["x0"], M["y0"] - 0.4 * u, zc - 0.015 * u)), Vector((0, 1, 0)), 0.5 * u)
    if hit[0] is not None:
        h_r.append(_esfera(np.array(hit[0]) + np.array(hit[1]) * (holgura + 0.004) * u, 0.0065 * u))
    ruta = []
    for t in np.linspace(0, 1, 8):
        px = M["x0"] + 0.025 * u * math.sin(t * math.pi * 0.5)
        pz = zc - 0.03 * u - 0.10 * u * t
        hit = cb.bvh.ray_cast(Vector((px, M["y0"] - 0.4 * u, pz)), Vector((0, 1, 0)), 0.5 * u)
        if hit[0] is not None:
            ruta.append(np.array(hit[0]) + np.array(hit[1]) * (holgura + 0.003) * u)
    if len(ruta) > 3:
        h_l.append(_tubo(ruta, 0.0006 * u, 4))
    V, F = _juntar(h_l)
    partes.append(_objeto(f"COSTURAS_JEAN_{pj['id']}", pj, V, F, [hilo], cuerpo=cb))
    V, F = _juntar(h_r)
    partes.append(_objeto(f"BOLSILLOS_JEAN_{pj['id']}", pj, V, F, [hilo, metal], cuerpo=cb,
                          mat_idx=None))
    # presillas del cinturón (cinco rectangulitos)
    pres = []
    for a in (-0.11, -0.06, 0.06, 0.11, 0.0):
        for frente in ((-1,) if a != 0.0 else (1,)):
            hit = cb.bvh.ray_cast(Vector((M["x0"] + a * u, M["y0"] + frente * 0.4 * u, zc - 0.018 * u)),
                                  Vector((0, -frente, 0)), 0.5 * u)
            if hit[0] is not None:
                c = np.array(hit[0]) + np.array(hit[1]) * (holgura + 0.004) * u
                pres.append(_tubo([c + np.array([0, 0, 0.012 * u]), c - np.array([0, 0, 0.012 * u])],
                                  0.0022 * u, 4))
    if pres:
        V, F = _juntar(pres)
        partes.append(_objeto(f"PRESILLAS_{pj['id']}", pj, V, F, [tj], cuerpo=cb))
    return partes


def _horma(cb: Cuerpo, lado: str) -> dict:
    """Medidas del pie: eje talón→punta, largo, ancho y alto por tramo (de los vértices del pie del maniquí)."""
    u = cb.u
    ids = [i for i in range(len(cb.pos)) if cb.w(i, f"{lado}Foot", f"{lado}Toe") > 0.4 and
           cb.pos[i][2] < cb.h[f"{lado}Foot"][0][2] + 0.01 * u]
    P = cb.pos[ids]
    tob = cb.h[f"{lado}Foot"][0]
    dedo = cb.h[f"{lado}ToeBase"][0]
    eje = dedo - tob
    eje[2] = 0
    eje /= np.linalg.norm(eje)
    perp = np.cross([0, 0, 1.0], eje)
    t = (P - tob) @ eje
    x = (P - tob) @ perp
    t0, t1 = t.min(), t.max()
    tramos = []
    for k in range(21):
        tt = t0 + (t1 - t0) * k / 20
        m = np.abs(t - tt) < (t1 - t0) / 18
        if m.sum() < 3:
            m = np.abs(t - tt) < (t1 - t0) / 8
        tramos.append((tt, x[m].min(), x[m].max(), P[m, 2].max()))
    return {"tob": tob, "eje": eje, "perp": perp, "t0": t0, "t1": t1, "tramos": tramos,
            "piso": cb.pos[:, 2].min()}


def zapatillas(cb: Cuerpo, Z: dict, color=(0.95, 0.95, 0.94), suela=(0.97, 0.96, 0.93), detalle=(0.75, 0.75, 0.76),
               nombre="zapa"):
    """Zapatillas urbanas armadas sobre la horma del pie: capellada redondeada, suela de goma con canto, puntera,
    contrafuerte, franja lateral, cordones cruzados y lengüeta. La piel del pie se borra."""
    pj, u = cb.pj, cb.u
    m_cuero = tela(f"{nombre}_{pj['id']}", color, 0.5, "cuero")
    m_suela = tela(f"{nombre}_suela_{pj['id']}", suela, 0.7, "goma")
    m_franja = tela(f"{nombre}_franja_{pj['id']}", detalle, 0.55, "cuero")
    cord = tela(f"{nombre}_cordon_{pj['id']}", detalle, 0.8, "algodon")
    partes = []
    for lado in ("Left", "Right"):
        H = _horma(cb, lado)
        tob, eje, perp, piso = H["tob"], H["eje"], H["perp"], H["piso"]
        alto_suela = 0.026 * u
        holg = 0.007 * u
        anillos_c, anillos_s = [], []
        nseg = 18
        tob_z = tob[2]
        for k, (tt, xmin, xmax, ztop) in enumerate(H["tramos"]):
            f = k / 20
            # punta y talón redondeados: se achica en los extremos
            redondeo = math.sqrt(max(0.0, 1 - (max(0.0, f - 0.82) / 0.18) ** 2)) * \
                math.sqrt(max(0.0, 1 - (max(0.0, 0.10 - f) / 0.10) ** 2))
            tt2 = H["t0"] - 0.012 * u + (H["t1"] - H["t0"] + 0.024 * u) * f
            cx = (xmin + xmax) / 2
            ancho = ((xmax - xmin) / 2 + holg) * (0.55 + 0.45 * redondeo)
            techo = max(ztop + holg, piso + alto_suela + 0.02 * u)
            if f < 0.42:                                   # talón y empeine alto: hasta arriba del tobillo
                techo = max(techo, tob_z + 0.012 * u * (1 - f / 0.42))
            techo = piso + alto_suela + (techo - piso - alto_suela) * (0.35 + 0.65 * redondeo)
            base = tob + eje * tt2 + perp * cx
            fila_c, fila_s = [], []
            for j in range(nseg):
                a = 2 * math.pi * j / nseg
                ca, sa = math.cos(a), math.sin(a)
                ex = np.sign(ca) * abs(ca) ** 0.6
                ez = np.sign(sa) * abs(sa) ** 0.8
                zc = piso + alto_suela * 0.9
                z = zc + (techo - zc) * max(0.0, ez) + min(0.0, ez) * 0.004 * u
                fila_c.append(base + perp * ex * ancho + np.array([0, 0, z - base[2]]))
                zs = piso - 0.004 * u + (alto_suela + 0.004 * u) * (0.5 + 0.5 * ez)
                fila_s.append(base + perp * ex * (ancho + 0.004 * u) + np.array([0, 0, zs - base[2]]))
            anillos_c.append(fila_c)
            anillos_s.append(fila_s)
        for nombre_p, anillos, mats in (("CAPELLADA", anillos_c, [m_cuero, m_franja]), ("SUELA", anillos_s, [m_suela])):
            V = [p for fila in anillos for p in fila]
            n = nseg
            F, idx = [], []
            for i in range(len(anillos) - 1):
                for j in range(n):
                    a = i * n + j
                    b = i * n + (j + 1) % n
                    F.append([a, b, b + n, a + n])
                    # franja lateral: una banda en los costados de la capellada (mitad trasera)
                    lat = (0.25 < i / 20 < 0.62) and (j in (1, 2, n // 2 - 2, n // 2 - 1, n // 2 + 1, n - 1))
                    idx.append(1 if (nombre_p == "CAPELLADA" and lat and (j in (1, n // 2 - 1) or i % 7 == 0)) else 0)
            # tapas en la punta y el talón
            for i in (0, len(anillos) - 1):
                c = len(V)
                V.append(np.mean(anillos[i], axis=0))
                for j in range(n):
                    a = i * n + j
                    b = i * n + (j + 1) % n
                    F.append([a, b, c] if i else [b, a, c])
                    idx.append(0)
            partes.append(_objeto(f"{nombre_p}_{lado}_{pj['id']}", pj, V, F, mats, idx if nombre_p == "CAPELLADA"
                                  else None, cuerpo=cb, subdiv=1))
        # cordones cruzados y lengüeta sobre el empeine
        piezas = []
        for k, f in enumerate(np.linspace(0.36, 0.66, 6)):
            i = int(round(f * 20))
            fila = anillos_c[i]
            arriba = fila[nseg // 4]
            izq, der = fila[nseg // 4 - 2], fila[nseg // 4 + 2]
            piezas.append(_tubo([izq + np.array([0, 0, 0.002 * u]), arriba + np.array([0, 0, 0.004 * u]),
                                 der + np.array([0, 0, 0.002 * u])], 0.0016 * u, 5))
        top = anillos_c[int(0.30 * 20)][nseg // 4]
        piezas.append(_tubo([top, top + np.array([0, 0, 0.022 * u]) - eje * 0.004 * u], 0.007 * u, 8))
        V, F = _juntar(piezas)
        partes.append(_objeto(f"CORDONES_{lado}_{pj['id']}", pj, V, F, [cord], cuerpo=cb))
    # el pie (y el tobillo) quedan adentro: se borran
    tap = {i for i in range(len(cb.pos)) if cb.w(i, "LeftFoot", "RightFoot", "LeftToe", "RightToe") > 0.5}
    pj.setdefault("_piel_tapada", set()).update(tap)
    return partes


def cartera(cb: Cuerpo, Z: dict, color=(0.36, 0.20, 0.10)):
    """Cartera cruzada de cuero: correa del hombro derecho a la cadera izquierda, por delante y por la espalda."""
    pj, u, M = cb.pj, cb.u, Z["M"]
    cuero = tela(f"cartera_{pj['id']}", color, 0.45, "cuero")
    metal = tela(f"hebilla_{pj['id']}", (0.78, 0.66, 0.40), 0.25, "metal")
    hombro = cb.h["RightShoulder"][1]
    cad = cb.h["LeftUpLeg"][0]
    centro_c = np.array([cad[0] + 0.05 * u * np.sign(cad[0] - M["x0"]), M["y0"] + 0.01 * u, M["z_cadera"] + 0.02 * u])
    piezas = []
    for frente in (-1, 1):
        ruta = []
        for t in np.linspace(0, 1, 30):
            p = hombro + (centro_c - hombro) * t
            p = p + np.array([0, 0, 0.04 * u * math.sin(t * math.pi)])
            hit = cb.bvh.ray_cast(Vector((p[0], M["y0"] + frente * 0.5 * u, p[2])), Vector((0, -frente, 0)), 0.6 * u)
            if hit[0] is not None:
                ruta.append(np.array(hit[0]) + np.array(hit[1]) * 0.03 * u)
        if len(ruta) > 4:
            piezas.append(_tubo(ruta, 0.006 * u, 6))
    # por arriba del hombro
    arco = []
    for a in np.linspace(-1, 1, 9):
        arco.append(hombro + np.array([0, a * 0.06 * u, 0.035 * u * math.cos(a * math.pi / 2) + 0.02 * u]))
    piezas.append(_tubo(arco, 0.006 * u, 6))
    V, F = _juntar(piezas)
    partes = [_objeto(f"CORREA_{pj['id']}", pj, V, F, [cuero], cuerpo=cb)]
    # la cartera: caja redondeada al costado de la cadera
    import bmesh as _bm
    bm = _bm.new()
    _bm.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= 0.05 * u
        v.co.y *= 0.20 * u
        v.co.z *= 0.15 * u
    _bm.ops.bevel(bm, geom=list(bm.edges), offset=0.012 * u, segments=3, affect="EDGES")
    lado = np.sign(cad[0] - M["x0"])
    hit = cb.bvh.ray_cast(Vector((M["x0"] + lado * 0.5 * u, centro_c[1], centro_c[2] - 0.03 * u)),
                          Vector((-lado, 0, 0)), 0.6 * u)
    base = np.array(hit[0]) + np.array([lado * 0.055 * u, 0, 0]) if hit[0] is not None else centro_c
    V = [np.array(v.co) + base for v in bm.verts]
    F = [[v.index for v in f.verts] for f in bm.faces]
    bm.free()
    partes.append(_objeto(f"CARTERA_{pj['id']}", pj, V, F, [cuero], cuerpo=cb, subdiv=1))
    V, F = _tubo([base + np.array([lado * 0.026 * u, -0.012 * u, 0.04 * u]),
                  base + np.array([lado * 0.026 * u, 0.012 * u, 0.04 * u])], 0.004 * u, 8)
    partes.append(_objeto(f"HEBILLA_{pj['id']}", pj, V, F, [metal], cuerpo=cb))
    return partes


def aros(pj: dict, u: float):
    """Aros finos dorados en los lóbulos de las orejas (siguen a la cabeza)."""
    from estudio.blender import stickman as SM
    cab = pj["cabeza"]
    metal = tela(f"aros_{pj['id']}", (0.86, 0.70, 0.40), 0.18, "metal")
    M = SM._modelo_a_armadura(pj)
    piezas = []
    for lado in (1, -1):
        lob = np.array(cab.punto(lado * 1.52, -0.30, 0.02))
        c = lob + np.array([lado * 0.004 * u, 0, -0.011 * u])
        ruta = [c + np.array([0, math.sin(a) * 0.011 * u, math.cos(a) * 0.011 * u]) for a in np.linspace(0, 2 * math.pi, 25)]
        piezas.append(_tubo([np.array(M @ Vector(p)) for p in ruta], 0.0009 * u, 6))
    V, F = _juntar(piezas)
    return [_objeto(f"AROS_{pj['id']}", pj, V, F, [metal], pesos=[{"Head": 1.0}] * len(V))]


def reloj(cb: Cuerpo, Z: dict, lado="Left"):
    pj, u = cb.pj, cb.u
    a, b = cb.h[f"{lado}ForeArm"][0], cb.h[f"{lado}Hand"][0]
    c = b + (a - b) * 0.12
    eje = (b - a) / np.linalg.norm(b - a)
    t1 = np.cross(eje, [0, 0, 1.0])
    t1 /= np.linalg.norm(t1)
    t2 = np.cross(eje, t1)
    radios = []
    for k in range(16):
        ang = 2 * math.pi * k / 16
        d = t1 * math.cos(ang) + t2 * math.sin(ang)
        hit = cb.bvh.ray_cast(Vector(c + d * 0.1 * u), Vector(-d), 0.1 * u)
        r = np.linalg.norm(np.array(hit[0]) - c) if hit[0] is not None else 0.028 * u
        radios.append(c + d * (r + 0.004 * u))
    radios.append(radios[0])
    cuero = tela(f"malla_reloj_{pj['id']}", (0.12, 0.10, 0.09), 0.5, "cuero")
    metal = tela(f"reloj_{pj['id']}", (0.70, 0.70, 0.72), 0.2, "metal")
    V, F = _tubo(radios, 0.0035 * u, 6)
    partes = [_objeto(f"MALLA_RELOJ_{pj['id']}", pj, V, F, [cuero], cuerpo=cb)]
    tope = radios[4]
    V, F = _tubo([tope, tope + (tope - c) / np.linalg.norm(tope - c) * 0.007 * u], 0.012 * u, 16)
    partes.append(_objeto(f"RELOJ_{pj['id']}", pj, V, F, [metal], cuerpo=cb))
    return partes


PRENDAS = {"buzo_capucha": buzo_capucha, "remera": remera, "campera_jean": campera_jean, "jean": jean,
           "zapatillas": zapatillas, "cartera": cartera, "reloj": reloj}


def vestir(pj: dict, vestuario: list[dict]):
    """vestuario: [{"prenda": "jean", "color": [r,g,b] (sRGB), …}] en orden de adentro hacia afuera."""
    cb = Cuerpo(pj)
    Z = _zona(cb)
    hechas = []
    for item in vestuario:
        kw = {k: tuple(v) if isinstance(v, list) else v for k, v in item.items() if k != "prenda"}
        if item["prenda"] == "aros":
            hechas += aros(pj, cb.u)
            continue
        hechas += PRENDAS[item["prenda"]](cb, Z, **kw)
    borrar_piel_tapada(pj)
    pj["ropa"] = hechas
    return hechas
