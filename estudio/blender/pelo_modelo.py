"""Pelos ya modelados (los que sube el dueño) puestos sobre la cabeza de MakeHuman de los personajes humanos.

Cada pelo del catálogo trae su malla (tarjetas con textura transparente) y sus texturas. Al ponerlo:
  · se junta todo en una malla, se escala y se ubica sobre el cráneo (misma coronilla, centrado, la medida tomada
    en la franja alta de la cabeza) y se EMPUJA hacia afuera todo lo que quede dentro de la cabeza o del cuerpo
    (pelo largo sobre hombros y espalda), así no atraviesa la piel;
  · la textura se tiñe del color del personaje conservando el dibujo de las hebras; la transparencia va en la misma
    imagen (recorte «MASK» en el GLB: el EDITOR 3D del teléfono la respeta);
  · sigue a la cabeza (pesos al hueso Head); el pelo largo pasa de a poco a seguir la espalda debajo del cuello.
Los archivos viven en mixamo-respaldo (personajes_pelicula/a_la_deriva/pelos).
"""
from __future__ import annotations
import math

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

from estudio import config

BASE = "mixamo:personajes_pelicula/a_la_deriva/pelos"  # «bob» no se respaldó (no se usa)
CATALOGO = {
    # el del dueño para él: corto, tarjetas en gris para teñir
    "hair02": {"archivo": f"{BASE}/hair02/hair02.fbx", "color": f"{BASE}/hair02/hair02_D.tga",
               "alfa": f"{BASE}/hair02/hair02_Alpha.tga", "normal": f"{BASE}/hair02/hair02_N.png", "gris": True},
    # largo con flequillo (tres piezas)
    "summer_girl": {"archivo": f"{BASE}/summer_girl/SKM_Hair.fbx", "color": f"{BASE}/summer_girl/T_Hair_BaseColor.tga",
                    "alfa": f"{BASE}/summer_girl/T_Hair_Alpha.tga", "normal": f"{BASE}/summer_girl/T_Hair_Normal.tga"},
    # melena corta ondulada (la transparencia viene en la textura de color)
    "bob": {"archivo": f"{BASE}/bob/Hair_Fem_Bob_01.fbx", "color": f"{BASE}/bob/Hair_Brown_DIFF.png",
            "normal": f"{BASE}/bob/Hair_Main_NRM.tga"},
}


def _cargar_imagen(ref: str):
    return bpy.data.images.load(str(config.resolver(ref)), check_existing=True)


def _textura(pid: str, info: dict, color_srgb) -> bpy.types.Image:
    """Color teñido (luminancia de las hebras × color del personaje) + transparencia en una sola imagen RGBA."""
    im = _cargar_imagen(info["color"])
    w, h = im.size
    px = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)
    if info.get("alfa"):
        a = _cargar_imagen(info["alfa"])
        pa = np.array(a.pixels[:], dtype=np.float32).reshape(a.size[1], a.size[0], 4)
        if pa.shape[:2] != (h, w):
            ys = (np.arange(h) * pa.shape[0] / h).astype(int)
            xs = (np.arange(w) * pa.shape[1] / w).astype(int)
            pa = pa[ys][:, xs]
        alfa = pa[:, :, :3].mean(axis=2)
    else:
        alfa = px[:, :, 3]
    lum = px[:, :, :3] @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    ref = float(np.median(lum[alfa > 0.5])) if (alfa > 0.5).any() else 0.5
    c = np.array(color_srgb, dtype=np.float32)
    var = np.clip(lum / max(ref, 1e-3), 0.35, 1.9)            # se conserva el dibujo de cada hebra
    rgb = np.clip(c[None, None, :] * var[:, :, None], 0, 1)
    out = np.concatenate([rgb, alfa[:, :, None]], axis=2)
    nueva = bpy.data.images.new(f"pelo_{pid}", w, h, alpha=True)
    nueva.pixels.foreach_set(out.ravel())
    nueva.pack()
    return nueva


def material(pid: str, info: dict, color_srgb) -> bpy.types.Material:
    mat = bpy.data.materials.new(f"pelo_{pid}")
    mat.use_nodes = True
    nt = mat.node_tree
    b = nt.nodes["Principled BSDF"]
    tx = nt.nodes.new("ShaderNodeTexImage")
    tx.image = _textura(pid, info, color_srgb)
    nt.links.new(tx.outputs["Color"], b.inputs["Base Color"])
    rd = nt.nodes.new("ShaderNodeMath")
    rd.operation = "ROUND"                                    # recorte por transparencia («MASK» en el GLB)
    nt.links.new(tx.outputs["Alpha"], rd.inputs[0])
    nt.links.new(rd.outputs[0], b.inputs["Alpha"])
    if info.get("normal"):
        tn = nt.nodes.new("ShaderNodeTexImage")
        tn.image = _cargar_imagen(info["normal"])
        tn.image.colorspace_settings.name = "Non-Color"
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.inputs["Strength"].default_value = 0.6
        nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Roughness"].default_value = 0.42
    b.inputs["Specular IOR Level"].default_value = 0.55
    b.inputs["Coat Weight"].default_value = 0.08
    b.inputs["Sheen Weight"].default_value = 0.25
    mat.surface_render_method = "DITHERED"
    mat.use_backface_culling = False
    return mat


def _importar(ref: str) -> tuple[np.ndarray, list, np.ndarray]:
    """Junta todas las mallas del archivo (en reposo, coordenadas de mundo) → (vértices, caras, uv por bucle)."""
    antes = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(config.resolver(ref)))
    nuevos = [o for o in bpy.data.objects if o not in antes]
    V, F, UV = [], [], []
    for o in nuevos:
        if o.type != "MESH":
            continue
        me = o.data
        M = o.matrix_world
        b0 = len(V)
        V += [tuple(M @ v.co) for v in me.vertices]
        uv = me.uv_layers.active.data if me.uv_layers else None
        for p in me.polygons:
            F.append([b0 + i for i in p.vertices])
            UV.append([tuple(uv[li].uv) if uv else (0.0, 0.0) for li in p.loop_indices])
    for o in nuevos:
        bpy.data.objects.remove(o, do_unlink=True)
    return np.array(V), F, UV


def _franja(P: np.ndarray, z0: float, z1: float):
    m = (P[:, 2] >= z0) & (P[:, 2] <= z1)
    q = P[m] if m.any() else P
    return q[:, 0].min(), q[:, 0].max(), q[:, 1].min(), q[:, 1].max()


def poner(pj: dict, nombre: str, color_srgb, holgura: float = 1.12) -> bpy.types.Object:
    info = CATALOGO[nombre]
    u = pj["u"]
    V, F, UV = _importar(info["archivo"])
    # ---- cabeza (espacio de la armadura)
    cab = pj["cabeza_humana"]["obj"]                       # la cabeza (original del maniquí o injertada)
    H = np.array([v.co[:] for v in cab.data.vertices])
    h_top = H[:, 2].max()
    hx0, hx1, hy0, hy1 = _franja(H, h_top - 0.09 * u, h_top - 0.03 * u)
    # ---- pelo (metros del archivo): misma franja relativa a su coronilla
    p_top = V[:, 2].max()
    px0, px1, py0, py1 = _franja(V, p_top - 0.10, p_top - 0.035)
    s = holgura * (hx1 - hx0) / max(1e-6, px1 - px0)
    c_h = np.array([(hx0 + hx1) / 2, (hy0 + hy1) / 2, h_top])
    c_p = np.array([(px0 + px1) / 2, (py0 + py1) / 2, p_top])
    P = (V - c_p) * s + c_h + np.array([0, 0, 0.006 * u])
    # ---- nada adentro de la cabeza ni del cuerpo
    bm = bmesh.new()
    bm.from_mesh(cab.data)
    bm.normal_update()
    bvh_cab = BVHTree.FromBMesh(bm)
    bm.free()
    centro = H.mean(axis=0)
    from estudio.blender.ropa_humana import Cuerpo
    cb = Cuerpo(pj)
    for i in range(len(P)):
        p = P[i]
        q, n, _, d = bvh_cab.find_nearest(Vector(p), 0.05 * u)
        if q is not None:
            q, n = np.array(q), np.array(n)
            if np.dot(n, q - centro) < 0:
                n = -n
            if np.dot(p - q, n) < 0.003 * u:
                P[i] = q + n * 0.003 * u
                continue
        if p[2] < h_top - 0.20 * u:                            # pelo largo: hombros y espalda
            q, n, fi, d = cb.bvh.find_nearest(Vector(p), 0.06 * u)
            if q is not None:
                q, n = np.array(q), np.array(n)
                k = cb.kd.find(Vector(q))[1]
                if np.dot(n, cb._radial(k, q)) < 0:
                    n = -n
                if np.dot(p - q, n) < 0.012 * u:
                    P[i] = q + n * 0.012 * u
    me = bpy.data.meshes.new(f"pelo_{pj['id']}")
    me.from_pydata([tuple(map(float, p)) for p in P], [], F)
    capa = me.uv_layers.new(name="UVMap")
    capa.data.foreach_set("uv", np.array([c for cara in UV for c in cara], dtype=np.float32).ravel())
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    me.materials.append(material(pj["id"], info, color_srgb))
    ob = bpy.data.objects.new(f"PELO_{pj['id']}", me)
    pj["coleccion"].objects.link(ob)
    arm = pj["armadura"]
    ob.parent = arm
    ob.matrix_parent_inverse = Matrix.Identity(4)
    # ---- pesos: cabeza; el pelo largo, de a poco, a la espalda (no gira entero con la cabeza)
    z_cuello = cb.h["Neck"][0][2]
    z_hombro = cb.h["Spine2"][0][2]
    gh = ob.vertex_groups.new(name="mixamorig:Head")
    ge = ob.vertex_groups.new(name="mixamorig:Spine2")
    for i, p in enumerate(P):
        a = float(np.clip((p[2] - z_hombro) / max(1e-6, z_cuello - z_hombro), 0, 1))
        a = a * a * (3 - 2 * a)
        if a > 0.001:
            gh.add([i], a, "REPLACE")
        if a < 0.999:
            ge.add([i], 1 - a, "REPLACE")
    ob.modifiers.new("Armature", "ARMATURE").object = arm
    pj["pelo"] = {"malla": ob, "modelo": nombre}
    return ob
