"""Cabeza humana de MakeHuman (CC0) TAL CUAL sobre el cuerpo de los maniquíes del dueño.

  · La cabeza es la del modelo por defecto de MakeHuman (hombre o mujer, 25 años, sin retoques); sólo se escala
    entera (sin deformarla) para que corresponda a un cuerpo de la misma altura que el maniquí, y se apoya en la base
    del cuello del maniquí. El cuello de MakeHuman se funde de a poco con el del cuerpo hasta el corte (sin costura).
  · Rostro animable: las 59 unidades de expresión de MakeHuman como formas clave + «BlinkLeft/Right» (párpado de
    arriba que tapa todo el ojo), ojos de MakeHuman que giran (con córnea transparente e iris del color del
    personaje), boca por dentro, dientes y lengua, pestañas y cejas de pelitos que siguen a párpados y cejas.
  · Piel pintada por zonas (labios, mejillas, párpados, orejas, barba incipiente) + dispersión subsuperficial.
"""
from __future__ import annotations
import math
import random
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

from estudio import makehuman as MH
from estudio.blender import kit as K

GRUPOS_EXTRA = ("helper-upper-teeth", "helper-lower-teeth", "helper-tongue")
PESTANAS = ("helper-l-eyelashes", "helper-r-eyelashes")


def _lineal(c):
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)


def reposo(pj: dict) -> dict:
    malla, arm = pj["malla"], pj["armadura"]
    M = arm.matrix_world.inverted() @ malla.matrix_world
    me = malla.data
    n = len(me.vertices)
    co = np.empty(n * 3)
    me.vertices.foreach_get("co", co)
    A = np.array(M)
    pos = co.reshape(n, 3) @ A[:3, :3].T + A[:3, 3]
    gname = {g.index: g.name.replace("mixamorig:", "") for g in malla.vertex_groups}
    pesos = [{gname[g.group]: g.weight for g in v.groups if g.weight > 1e-4} for v in me.vertices]
    huesos = {b.name.replace("mixamorig:", ""): (Vector(b.head_local), Vector(b.tail_local)) for b in arm.data.bones}
    return {"pos": pos, "pesos": pesos, "huesos": huesos}


# ================================================================================================ injerto

def injertar(pj: dict, genero: float) -> dict:
    rep = reposo(pj)
    u = pj["u"]
    v = MH.cuerpo(genero)
    b = MH.base()
    vb = MH.a_blender(v)
    cuerpo_ids = sorted({k for i, g in enumerate(b["grupos"]) if g == "body" for k in b["caras"][i]})
    alto_mh = vb[cuerpo_ids, 2].max() - vb[cuerpo_ids, 2].min()
    # escala: un cuerpo de MakeHuman de la misma altura que el maniquí (la cabeza no se deforma)
    alto_maniqui = rep["pos"][:, 2].max() - rep["pos"][:, 2].min()
    s = alto_maniqui / alto_mh * pj.get("escala_cabeza", 1.0)
    n1 = MH.a_blender(MH.articulacion(v, "neck01____head")[None])[0]
    n2 = MH.a_blender(MH.articulacion(v, "neck02____head")[None])[0]
    hn = rep["huesos"]["Neck"][0]
    t = np.array([hn.x, hn.y, hn.z]) - s * n1                    # base del cuello sobre la del maniquí
    V = vb * s + t
    z_corte = (n1[2] + (n2[2] - n1[2]) * 0.35) * s + t[2]
    caras = []
    for i, g in enumerate(b["grupos"]):
        idx = b["caras"][i]
        if g == "body" and V[idx, 2].min() >= z_corte:
            caras.append(i)
        elif g.startswith(GRUPOS_EXTRA):
            caras.append(i)
    pest = [i for i, g in enumerate(b["grupos"]) if g.startswith(PESTANAS)]
    usados = sorted({k for i in caras + pest for k in b["caras"][i]})
    loc = {g: i for i, g in enumerate(usados)}
    P = V[usados].copy()
    hh = rep["huesos"]["Head"][0]
    # ---- fundido del cuello: debajo de la mandíbula el radio se acerca al del maniquí (la cara no se toca)
    bm = bmesh.new()
    me0 = pj["malla"].data
    for p in rep["pos"]:
        bm.verts.new(Vector(p))
    bm.verts.ensure_lookup_table()
    for poly in me0.polygons:
        try:
            bm.faces.new([bm.verts[i] for i in poly.vertices])
        except ValueError:
            pass
    bm.normal_update()
    bvh = BVHTree.FromBMesh(bm)
    bm.free()
    jaw = MH.a_blender(MH.articulacion(v, "jaw____tail")[None])[0] * s + t
    z_funde = jaw[2] - 0.01 * u
    eje_y = (hn.y + hh.y) * 0.5
    for k in range(len(P)):
        z = P[k, 2]
        if z >= z_funde:
            continue
        a = min(1.0, max(0.0, (z_funde - z) / max(1e-6, z_funde - z_corte)))
        a = a * a * (3 - 2 * a)
        delante = min(1.0, max(0.0, ((eje_y - P[k, 1]) - 0.035 * u) / (0.015 * u)))
        a *= 1 - delante
        if a <= 0:
            continue
        eje = Vector((hn.x, eje_y, z))
        d = Vector((P[k, 0], P[k, 1], z)) - eje
        r = d.length
        if r < 1e-6:
            continue
        d.normalize()
        hit = bvh.ray_cast(eje + d * 0.3 * u, -d, 0.3 * u)
        if hit[0] is None:
            continue
        rc = (hit[0] - eje).length
        nuevo = r + (rc + 0.0005 * u - r) * a
        P[k, 0] = eje.x + d.x * nuevo
        P[k, 1] = eje.y + d.y * nuevo
    # ---- recorte del maniquí por encima del corte
    bm = bmesh.new()
    bm.from_mesh(me0)
    bm.verts.ensure_lookup_table()
    borrar = [f for f in bm.faces if all(rep["pos"][x.index][2] > z_corte + 0.004 * u for x in f.verts)]
    bmesh.ops.delete(bm, geom=borrar, context="FACES")
    bm.to_mesh(me0)
    bm.free()
    # ---- malla
    me = bpy.data.meshes.new(f"cabeza_{pj['id']}")
    me.from_pydata(P.tolist(), [], [[loc[k] for k in b["caras"][i]] for i in caras])
    me.update()
    uvs = np.array([b["vt"][j] for i in caras for j in b["uvs"][i]])
    cuerpo_m = np.array([b["grupos"][i] == "body" for i in caras for _ in b["caras"][i]])
    lo, hi = uvs[cuerpo_m].min(axis=0), uvs[cuerpo_m].max(axis=0)
    uvn = (uvs - lo) / (hi - lo).max()
    uvn[~cuerpo_m] = 0.995
    me.uv_layers.new(name="UVMap").data.foreach_set("uv", uvn.ravel())
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    ob = bpy.data.objects.new(f"CABEZA_{pj['id']}", me)
    pj["coleccion"].objects.link(ob)
    arm = pj["armadura"]
    ob.parent = arm
    ob.matrix_parent_inverse = Matrix.Identity(4)
    # ---- pesos: la cabeza sigue al hueso Head; el cuello mezcla con los pesos del maniquí
    kd = KDTree(len(rep["pos"]))
    for i, p in enumerate(rep["pos"]):
        kd.insert(Vector(p), i)
    kd.balance()
    grupos_v = {}
    for k in range(len(P)):
        z = P[k, 2]
        a = min(1.0, max(0.0, (z - z_corte) / max(1e-6, hh.z - z_corte)))
        a = max(a * a * (3 - 2 * a), min(1.0, max(0.0, ((eje_y - P[k, 1]) - 0.035 * u) / (0.02 * u))))
        if a >= 0.999:
            pw = {"Head": 1.0}
        else:
            pw, tot = {}, 0.0
            for co, idx, dist in kd.find_n(Vector(P[k]), 4):
                w = 1.0 / max(dist, 1e-5)
                tot += w
                for g, x in rep["pesos"][idx].items():
                    pw[g] = pw.get(g, 0.0) + w * x
            pw = {g: x / tot * (1 - a) for g, x in pw.items()}
            pw["Head"] = pw.get("Head", 0.0) + a
        for g, x in pw.items():
            if x >= 0.01:
                nm = "mixamorig:" + g
                if nm not in grupos_v:
                    grupos_v[nm] = ob.vertex_groups.new(name=nm)
                grupos_v[nm].add([k], x, "REPLACE")
    ob.modifiers.new("Armature", "ARMATURE").object = arm
    # ---- formas clave: unidades de expresión de MakeHuman
    ob.shape_key_add(name="Basis", from_mix=False)
    for nombre, (idx, d) in MH.unidades_expresion().items():
        sk = ob.shape_key_add(name=nombre, from_mix=False)
        sk.value = 0.0                     # en Blender 5 una forma nueva arranca con peso 1
        co = P.copy()
        dd = MH.a_blender(d) * s
        for g, delta in zip(idx, dd):
            if g in loc:
                co[loc[g]] += delta
        sk.data.foreach_set("co", co.ravel())
    info = {"obj": ob, "s": s, "t": t, "v": v, "loc": loc, "P": P, "caras": caras,
            "grupos": [b["grupos"][i] for i in caras], "pestanas": pest, "rep": rep, "z_corte": z_corte}
    pj["cabeza_humana"] = info
    return info


# ================================================================================================ ojos

def _iris(ruta: Path, color, pid: str) -> bpy.types.Image:
    base = bpy.data.images.load(str(ruta), check_existing=True)
    w, h = base.size
    px = np.array(base.pixels[:], dtype=np.float32).reshape(h, w, 4)
    rgb = px[:, :, :3]
    mx, mn = rgb.max(axis=2), rgb.min(axis=2)
    sat = (mx - mn) / np.maximum(mx, 1e-4)
    masc = np.clip((sat - 0.25) / 0.2, 0, 1) * (px[:, :, 3] > 0.5)
    lum = rgb.mean(axis=2, keepdims=True)
    ref = float(np.mean(lum[masc > 0.5])) if (masc > 0.5).any() else 1.0
    nuevo = np.clip(lum / max(1e-4, ref) * np.array(color, dtype=np.float32) * 0.9, 0, 1)
    px[:, :, :3] = rgb * (1 - masc[:, :, None]) + nuevo * masc[:, :, None]
    im = bpy.data.images.new(f"ojos_{pid}", w, h, alpha=True)
    im.pixels.foreach_set(px.ravel())
    im.pack()
    return im


def ojos(pj: dict, perfil: dict) -> list:
    info = pj["cabeza_humana"]
    o = MH.ojos(info["v"])
    vb = MH.a_blender(o["v"]) * info["s"] + info["t"]
    arm = pj["armadura"]
    mat = bpy.data.materials.new(f"ojos_{pj['id']}")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = _iris(o["textura"], perfil["iris"], pj["id"])
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.08
    bsdf.inputs["Subsurface Weight"].default_value = 0.1
    cornea = bpy.data.materials.new(f"cornea_{pj['id']}")
    cornea.use_nodes = True
    cb = cornea.node_tree.nodes["Principled BSDF"]
    cb.inputs["Roughness"].default_value = 0.0
    cb.inputs["IOR"].default_value = 1.376
    cb.inputs["Transmission Weight"].default_value = 1.0
    cb.inputs["Alpha"].default_value = 0.08
    cornea.surface_render_method = "BLENDED"
    cornea["estudio"] = {"color": [1, 1, 1], "rugosidad": 0.0, "metal": 0.0, "emision": None, "fuerza": 0.0,
                         "alfa": 0.08}
    es_cornea = [bool(np.all(o["vt"][f][:, 0] > 0.85) and np.all(o["vt"][f][:, 1] < 0.16)) for f in o["uvs"]]
    head = arm.data.bones["mixamorig:Head"]
    lados = {}
    for ci, f in enumerate(o["caras"]):
        lados.setdefault("L" if vb[f, 0].mean() > 0 else "R", []).append(ci)
    objs = []
    for lado, cis in lados.items():
        usados = sorted({k for ci in cis for k in o["caras"][ci]})
        loc = {g: i for i, g in enumerate(usados)}
        P = vb[usados]
        centro = P.mean(axis=0)
        me = bpy.data.meshes.new(f"ojo{lado}_{pj['id']}")
        me.from_pydata((P - centro).tolist(), [], [[loc[k] for k in o["caras"][ci]] for ci in cis])
        me.uv_layers.new(name="UVMap").data.foreach_set(
            "uv", np.array([o["vt"][j] for ci in cis for j in o["uvs"][ci]]).ravel())
        me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
        me.materials.append(mat)
        me.materials.append(cornea)
        me.polygons.foreach_set("material_index", [1 if es_cornea[ci] else 0 for ci in cis])
        ob = bpy.data.objects.new(f"OJO_{lado}_{pj['id']}", me)
        pj["coleccion"].objects.link(ob)
        ob.parent = arm
        ob.parent_type = "BONE"
        ob.parent_bone = head.name
        ob.matrix_parent_inverse = (Matrix.Translation(head.tail_local) @ head.matrix_local.to_3x3().to_4x4()).inverted()
        ob.location = Vector(centro)
        ob["centro"] = list(centro)
        ob["radio"] = float(np.linalg.norm(P - centro, axis=1).max())
        objs.append(ob)
    pj["ojos"] = objs
    return objs


# ================================================================================================ piel

def zonas(info: dict) -> dict:
    U = MH.unidades_expresion()
    loc = info["loc"]
    n = len(info["P"])

    def masc(*nombres, gamma=1.0):
        m = np.zeros(n)
        for nm in nombres:
            idx, d = U[nm]
            for g, x in zip(idx, np.linalg.norm(d, axis=1)):
                if g in loc:
                    m[loc[g]] = max(m[loc[g]], x)
        if m.max() > 0:
            m /= m.max()
        return np.clip(m, 0, 1) ** gamma
    P = info["P"]
    labios = masc("LipsKiss", gamma=2.2) * masc("lowerLipForward", "UpperLipForward", gamma=0.6)
    out = {"labios": labios, "mejillas": masc("LeftCheekUp", "RightCheekUp", gamma=1.5),
           "parpados": masc("LeftUpperLidClosed", "RightUpperLidClosed", "LeftLowerLidUp", "RightLowerLidUp",
                            gamma=1.3),
           "cejas": masc("LeftBrowDown", "RightBrowDown", gamma=1.4), "nariz": masc("NoseWrinkler", gamma=1.5)}
    mand = masc("JawDrop", gamma=0.8)
    H = P[:, 2].max() - P[:, 2].min()
    frente = np.clip(((P[:, 1].mean() - P[:, 1]) - 0.10 * H) / (0.12 * H), 0, 1)
    out["barba"] = np.clip(mand * 1.4, 0, 1) * frente * (1 - labios)
    return out


def _rasterizar(me, valores: np.ndarray, T: int) -> np.ndarray:
    c = valores.shape[1]
    img = np.zeros((T, T, c), dtype=np.float32)
    lleno = np.zeros((T, T), dtype=bool)
    uv = np.empty(len(me.loops) * 2)
    me.uv_layers.active.data.foreach_get("uv", uv)
    uv = uv.reshape(-1, 2) * (T - 1)
    for poly in me.polygons:
        ls = list(poly.loop_indices)
        vs = [me.loops[l].vertex_index for l in ls]
        for k in range(1, len(ls) - 1):
            tri = (0, k, k + 1)
            a, b2, c2 = (uv[ls[i]] for i in tri)
            va, vb2, vc2 = (valores[vs[i]] for i in tri)
            xmin, ymin = np.floor(np.minimum(np.minimum(a, b2), c2)).astype(int)
            xmax, ymax = np.ceil(np.maximum(np.maximum(a, b2), c2)).astype(int)
            if xmax - xmin > T // 3 or ymax - ymin > T // 3:
                continue
            xs, ys = np.meshgrid(np.arange(xmin, xmax + 1), np.arange(ymin, ymax + 1))
            px, py = xs.ravel() + 0.5, ys.ravel() + 0.5
            den = (b2[1] - c2[1]) * (a[0] - c2[0]) + (c2[0] - b2[0]) * (a[1] - c2[1])
            if abs(den) < 1e-9:
                continue
            w1 = ((b2[1] - c2[1]) * (px - c2[0]) + (c2[0] - b2[0]) * (py - c2[1])) / den
            w2 = ((c2[1] - a[1]) * (px - c2[0]) + (a[0] - c2[0]) * (py - c2[1])) / den
            w3 = 1 - w1 - w2
            dentro = (w1 >= -0.02) & (w2 >= -0.02) & (w3 >= -0.02)
            if not dentro.any():
                continue
            X = np.clip(xs.ravel()[dentro], 0, T - 1)
            Y = np.clip(ys.ravel()[dentro], 0, T - 1)
            img[Y, X] = w1[dentro, None] * va + w2[dentro, None] * vb2 + w3[dentro, None] * vc2
            lleno[Y, X] = True
    for _ in range(6):
        vacio = ~lleno
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            src = np.roll(np.roll(img, dy, 0), dx, 1)
            sl = np.roll(np.roll(lleno, dy, 0), dx, 1)
            m = vacio & sl
            img[m] = src[m]
            lleno |= m
    return img


def _imagen(nombre, arr, color=True):
    T = arr.shape[0]
    im = bpy.data.images.new(nombre, T, T, alpha=False)
    if not color:
        im.colorspace_settings.name = "Non-Color"
    rgba = np.ones((T, T, 4), dtype=np.float32)
    if arr.shape[2] == 1:
        rgba[:, :, :3] = arr[:, :, :1]
    else:
        rgba[:, :, :3] = arr[:, :, :3]
    im.pixels.foreach_set(rgba.ravel())
    im.pack()
    return im


def material_piel(nombre, color, rug=0.5, textura=None, rug_tex=None):
    mat = bpy.data.materials.new(nombre)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    lin = _lineal(color)
    bsdf.inputs["Base Color"].default_value = (*lin, 1)
    bsdf.inputs["Roughness"].default_value = rug
    for k, val in (("Subsurface Weight", 0.25), ("Subsurface Scale", 0.012), ("Specular IOR Level", 0.45),
                   ("Coat Weight", 0.05), ("Coat Roughness", 0.35)):
        bsdf.inputs[k].default_value = val
    bsdf.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.2)
    if textura is not None:
        tx = nt.nodes.new("ShaderNodeTexImage")
        tx.image = textura
        nt.links.new(tx.outputs["Color"], bsdf.inputs["Base Color"])
    if rug_tex is not None:
        tr = nt.nodes.new("ShaderNodeTexImage")
        tr.image = rug_tex
        sep = nt.nodes.new("ShaderNodeSeparateColor")
        nt.links.new(tr.outputs["Color"], sep.inputs[0])
        nt.links.new(sep.outputs[0], bsdf.inputs["Roughness"])
    vo = nt.nodes.new("ShaderNodeTexVoronoi")
    vo.inputs["Scale"].default_value = 900.0
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 300.0
    mx = nt.nodes.new("ShaderNodeMath")
    mx.operation = "ADD"
    nt.links.new(vo.outputs["Distance"], mx.inputs[0])
    nt.links.new(nz.outputs["Fac"], mx.inputs[1])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.1
    bump.inputs["Distance"].default_value = 0.0004
    nt.links.new(mx.outputs[0], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    mat.diffuse_color = (*lin, 1)
    if textura is None:            # con textura, el visor del teléfono la conserva (sin color plano)
        mat["estudio"] = {"color": list(lin), "rugosidad": rug, "metal": 0.0, "emision": None, "fuerza": 0.0,
                          "alfa": 1.0}
    return mat


def pintar(pj: dict, perfil: dict, T: int = 2048):
    info = pj["cabeza_humana"]
    ob = info["obj"]
    me = ob.data
    z = zonas(info)
    piel = np.array(perfil["piel"])                           # la imagen es sRGB: se pinta en sRGB
    n = len(info["P"])
    rng = np.random.default_rng(7)
    col = np.tile(piel, (n, 1))

    def mezclar(m, c, k):
        nonlocal col
        col = col * (1 - k * m[:, None]) + np.array(c) * k * m[:, None]
    mezclar(z["mejillas"], (0.86, 0.55, 0.50), 0.22)
    mezclar(z["nariz"], (0.86, 0.55, 0.50), 0.15)
    mezclar(z["parpados"], (0.66, 0.50, 0.47), 0.20)
    mezclar(z["cejas"], tuple(piel * 0.88), 0.3)
    mezclar(z["labios"], perfil["labios"], 0.85)
    if perfil.get("barba"):
        mezclar(z["barba"], (0.40, 0.33, 0.30), perfil["barba"])
    col *= 1 + rng.normal(0, 0.012, (n, 1))
    img = _imagen(f"piel_{pj['id']}", _rasterizar(me, col, T))
    rug = np.full((n, 1), 0.48)
    rug[:, 0] -= 0.2 * z["labios"] + 0.08 * z["nariz"]
    img_r = _imagen(f"piel_rug_{pj['id']}", _rasterizar(me, rug, 512), color=False)
    me.materials.clear()
    me.materials.append(material_piel(f"piel_cara_{pj['id']}", perfil["piel"], 0.48, img, img_r))
    dientes = K.material(f"dientes_{pj['id']}", _lineal((0.93, 0.91, 0.85)), 0.25)
    lengua = material_piel(f"lengua_{pj['id']}", (0.74, 0.40, 0.42), 0.35)
    me.materials.append(dientes)
    me.materials.append(lengua)
    for pi, poly in enumerate(me.polygons):
        g = info["grupos"][pi]
        poly.material_index = 1 if "teeth" in g else 2 if g.startswith("helper-tongue") else 0
    _boca_interior(pj, z)
    cuerpo = material_piel(f"piel_cuerpo_{pj['id']}", perfil["piel"], 0.5)
    pj["malla"].data.materials.clear()
    pj["malla"].data.materials.append(cuerpo)
    pj["mat_piel"] = cuerpo


def _boca_interior(pj: dict, z: dict):
    info = pj["cabeza_humana"]
    P = info["P"]
    u = pj["u"]
    lab = z["labios"] > 0.5
    if not lab.any():
        return
    c = P[lab].mean(axis=0) + np.array([0, 0.022 * u, -0.004 * u])
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=12, radius=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * 0.024 * u + c[0], v.co.y * 0.022 * u + c[1], v.co.z * 0.017 * u + c[2]))
    me = bpy.data.meshes.new(f"boca_{pj['id']}")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(K.material(f"boca_{pj['id']}", _lineal((0.22, 0.07, 0.07)), 0.6))
    ob = bpy.data.objects.new(f"BOCA_{pj['id']}", me)
    pj["coleccion"].objects.link(ob)
    ob.parent = pj["armadura"]
    ob.matrix_parent_inverse = Matrix.Identity(4)
    ob.vertex_groups.new(name="mixamorig:Head").add(list(range(len(me.vertices))), 1.0, "REPLACE")
    ob.modifiers.new("Armature", "ARMATURE").object = pj["armadura"]


def parpadeo(pj: dict):
    """«BlinkLeft/Right»: las unidades de MakeHuman cierran el párpado a medias; se extrapolan y se apoyan sobre una
    esfera apenas más grande que el ojo (el párpado tapa todo el ojo sin atravesarlo)."""
    info = pj["cabeza_humana"]
    ob = info["obj"]
    kb = ob.data.shape_keys.key_blocks
    base = np.empty(len(ob.data.vertices) * 3)
    kb["Basis"].data.foreach_get("co", base)
    base = base.reshape(-1, 3)
    for lado_mh, lado in (("Left", "L"), ("Right", "R")):
        ojo = next(o for o in pj["ojos"] if o.name.startswith(f"OJO_{lado}_"))
        c, r = np.array(ojo["centro"]), ojo["radio"]
        co = np.empty_like(base.ravel())
        kb[f"{lado_mh}UpperLidClosed"].data.foreach_get("co", co)
        d_sup = co.reshape(-1, 3) - base
        kb[f"{lado_mh}LowerLidUp"].data.foreach_get("co", co)
        d_inf = co.reshape(-1, 3) - base
        nuevo = base + d_sup * 3.2 + d_inf * 0.6
        for i in np.nonzero(np.linalg.norm(d_sup, axis=1) > 1e-7)[0]:
            w = nuevo[i] - c
            dist = np.linalg.norm(w)
            if dist < r * 1.05:
                nuevo[i] = c + w / max(dist, 1e-9) * r * 1.05
        sk = ob.shape_key_add(name=f"Blink{lado_mh}", from_mix=False)
        sk.value = 0.0
        sk.data.foreach_set("co", nuevo.ravel())


# ================================================================================================ cejas y pestañas

def _deltas(pj: dict) -> dict[str, np.ndarray]:
    ob = pj["cabeza_humana"]["obj"]
    kb = ob.data.shape_keys.key_blocks
    base = np.empty(len(ob.data.vertices) * 3)
    kb["Basis"].data.foreach_get("co", base)
    out = {}
    for k in kb[1:]:
        co = np.empty_like(base)
        k.data.foreach_get("co", co)
        out[k.name] = (co - base).reshape(-1, 3)
    return out


def _cintas(nombre, pj, trazos, anchos, raices, mat, formas):
    verts, caras, raiz_de = [], [], []
    for tr, an, ra in zip(trazos, anchos, raices):
        n = len(tr)
        b0 = len(verts)
        for i in range(n):
            d = tr[min(i + 1, n - 1)] - tr[max(i - 1, 0)]
            d /= max(1e-9, np.linalg.norm(d))
            lado = np.cross(d, [0.0, -1.0, 0.0])
            if np.linalg.norm(lado) < 1e-6:
                lado = np.array([1.0, 0, 0])
            lado /= np.linalg.norm(lado)
            w = an * (1 - 0.85 * i / max(1, n - 1))
            verts += [tr[i] - lado * w, tr[i] + lado * w]
            raiz_de += [ra, ra]
        for i in range(n - 1):
            a = b0 + 2 * i
            caras.append([a, a + 1, a + 3, a + 2])
    me = bpy.data.meshes.new(nombre)
    me.from_pydata([list(map(float, v)) for v in verts], [], caras)
    me.materials.append(mat)
    ob = bpy.data.objects.new(nombre, me)
    pj["coleccion"].objects.link(ob)
    ob.parent = pj["armadura"]
    ob.matrix_parent_inverse = Matrix.Identity(4)
    ob.vertex_groups.new(name="mixamorig:Head").add(list(range(len(verts))), 1.0, "REPLACE")
    ob.modifiers.new("Armature", "ARMATURE").object = pj["armadura"]
    ob.shape_key_add(name="Basis", from_mix=False)
    base = np.array(verts, dtype=float)
    for nf, delta in formas.items():
        co = base + delta[np.array(raiz_de)]
        sk = ob.shape_key_add(name=nf, from_mix=False)
        sk.value = 0.0
        sk.data.foreach_set("co", co.ravel())
    return ob


def cejas_y_pestanas(pj: dict, perfil: dict):
    info = pj["cabeza_humana"]
    P = info["P"]
    u = pj["u"]
    rng = random.Random(sum(map(ord, pj["id"])))
    hombre = perfil["genero"] > 0.5
    bm = bmesh.new()
    bm.from_mesh(info["obj"].data)
    bm.normal_update()
    bvh = BVHTree.FromBMesh(bm)
    bm.free()
    kd = KDTree(len(P))
    for i, p in enumerate(P):
        kd.insert(Vector(p), i)
    kd.balance()
    y0 = P[:, 1].min() - 0.05 * u
    trazos, anchos, raices = [], [], []
    for oj in pj["ojos"]:
        c = Vector(oj["centro"])
        lado = 1 if c.x > 0 else -1
        r = oj["radio"]
        for _ in range(450 if hombre else 360):
            q = rng.random()
            x = c.x - lado * r * 1.0 + lado * r * 2.55 * q
            arco = math.sin(min(1.0, q / 0.68) * math.pi * 0.5) * r * 0.30 - max(0.0, q - 0.68) * r * 0.85
            gro = r * (0.62 if hombre else 0.46) * (1 - 0.55 * q)
            zz = c.z + r * 1.35 + arco + (rng.random() - 0.5) * gro
            hit = bvh.ray_cast(Vector((x, y0, zz)), Vector((0, 1, 0)), 1.0)
            if hit[0] is None:
                continue
            p, n = np.array(hit[0]), np.array(hit[1])
            if n[1] > 0:
                n = -n
            ang = math.radians((70 - 95 * q) + rng.uniform(-14, 14))
            d = np.array([lado * math.cos(ang), 0.0, math.sin(ang)])
            d = d - n * np.dot(d, n)
            d /= np.linalg.norm(d)
            L = (0.0075 + 0.0045 * rng.random()) * (1.0 if hombre else 0.85) * u
            pts = [p + n * 0.0003 * u]
            for k in range(1, 4):
                pts.append(pts[-1] + d * (L / 3) + n * (0.0004 * u * (1 - k / 3)))
            trazos.append(np.array(pts))
            anchos.append((0.0001 if hombre else 0.00008) * u)
            raices.append(kd.find(p)[1])
    b = MH.base()
    loc = info["loc"]
    for fi in info["pestanas"]:
        vs = [loc[k] for k in b["caras"][fi]]
        pts = P[vs]
        ojo = min(pj["ojos"], key=lambda o: (Vector(o["centro"]) - Vector(pts.mean(axis=0))).length)
        cen = np.array(ojo["centro"])
        orden = np.argsort(np.linalg.norm(pts - cen, axis=1))
        ra, rb = pts[orden[0]], pts[orden[1]]
        punta = pts[orden[2:]].mean(axis=0)
        sup = punta[2] > cen[2]
        if not sup and rng.random() < 0.5:
            continue
        t = rng.random()
        r0 = ra + (rb - ra) * t
        d = punta - (ra + rb) * 0.5
        d /= max(np.linalg.norm(d), 1e-9)
        L = (0.0085 if sup else 0.0045) * (1.15 if not hombre else 1.0) * (0.8 + 0.4 * rng.random()) * u
        arriba = np.array([0, 0, 1.0 if sup else -1.0])
        trazos.append(np.array([r0 + d * L * f + arriba * L * 0.35 * f * f for f in np.linspace(0, 1, 5)]))
        anchos.append(0.00006 * u)
        raices.append(vs[orden[0]] if t < 0.5 else vs[orden[1]])
    m = K.material(f"cejas_{pj['id']}", _lineal(perfil["cejas"]), 0.55)
    pj["cejas"] = [_cintas(f"CEJAS_{pj['id']}", pj, trazos, anchos, raices, m, _deltas(pj))]
    return pj["cejas"]


def armar(pj: dict, perfil: dict):
    injertar(pj, perfil["genero"])
    ojos(pj, perfil)
    pintar(pj, perfil)
    parpadeo(pj)
    cejas_y_pestanas(pj, perfil)
    return pj["cabeza_humana"]
