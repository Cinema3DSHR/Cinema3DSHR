"""Corrige una zona de la textura de un personaje Tripo3D proyectando una foto de referencia ortogonal (p. ej. el
nombre y el número de la espalda de la camiseta, que Tripo deja ilegibles).

Uso (con el Python que trae bpy):
    python -m estudio.blender.proyectar_textura <modelo.fbx> <foto.png> <salida.png> --vista espalda \
        --escala 1119 --centro_x 652.5 --pie_y 1104 --caja "560,205,760,470"

La foto es una vista ortogonal del personaje en la misma pose (T): `escala` px por metro del modelo normalizado a 1 m,
`centro_x` el eje del cuerpo en la foto, `pie_y` la fila de las suelas. `caja` = x0,y0,x1,y1 (px de la foto) de la
zona a reemplazar. Se pinta cada triángulo de la malla que mira a la cámara y cae en la caja, con el color medio de la
foto llevado al de la textura y un borde suave. El original no se toca: la textura corregida va a `salida`.
"""
from __future__ import annotations
import argparse
import math
import sys
import numpy as np


def proyectar(fbx, foto, salida, vista="espalda", escala=1119.0, centro_x=652.5, pie_y=1104.0, caja=(560, 205, 760, 470),
              borde_px=10.0):
    import bpy
    from mathutils import Vector

    def leer(ruta):
        im = bpy.data.images.load(str(ruta), check_existing=False)
        w, h = im.size
        px = np.empty(w * h * 4, dtype=np.float32)
        im.pixels.foreach_get(px)
        return (px.reshape(h, w, 4)[::-1] * 255.0).astype(np.float64)        # filas de arriba hacia abajo

    def guardar(arr, ruta):
        h, w = arr.shape[:2]
        im = bpy.data.images.new("corregida", w, h, alpha=True)
        im.pixels.foreach_set((arr[::-1] / 255.0).astype(np.float32).ravel())
        im.filepath_raw = str(ruta)
        im.file_format = "PNG"
        im.save()
    from estudio.blender import importar as I
    bpy.ops.wm.read_factory_settings(use_empty=True)
    objs = I.importar(fbx)
    malla = next(o for o in objs if o.type == "MESH")
    from pathlib import Path as _P
    ruta_tex = next((_P(fbx).with_suffix(".fbm")).glob("*basecolor*"))     # la textura de color que trae Tripo
    tex = leer(ruta_tex)
    H, W = tex.shape[:2]
    ph = leer(foto)[..., :3]
    PH, PW = ph.shape[:2]
    # normalizar el modelo a 1 m de alto con los pies en z = 0 (como se midió la foto)
    pts = [malla.matrix_world @ v.co for v in malla.data.vertices]
    zmin = min(p.z for p in pts)
    zmax = max(p.z for p in pts)
    k = 1.0                                           # la escala de la foto se midió con el modelo tal cual (1 m)
    signo = -1.0 if vista == "espalda" else 1.0       # de espaldas, la derecha de la foto es −X del modelo
    mira = Vector((0, 1, 0)) if vista == "espalda" else Vector((0, -1, 0))

    def a_foto(p):
        x = (p.x) * k
        z = (p.z - zmin) * k
        return centro_x + signo * x * escala, pie_y - z * escala
    x0, y0, x1, y1 = caja
    uv = malla.data.uv_layers.active.data
    malla.data.calc_loop_triangles()
    acum = np.zeros((H, W, 3))
    peso = np.zeros((H, W))
    nm = malla.matrix_world.to_3x3()
    for tri in malla.data.loop_triangles:
        n = (nm @ tri.normal).normalized()
        if n.dot(mira) < 0.25:
            continue
        ps = [a_foto(pts[i]) for i in tri.vertices]
        if not all(x0 - 30 <= px <= x1 + 30 and y0 - 30 <= py <= y1 + 30 for px, py in ps):
            continue
        ts = [uv[l].uv for l in tri.loops]
        tx = np.array([[t.x * W, (1 - t.y) * H] for t in ts])
        fx = np.array(ps)
        bx0, by0 = np.floor(tx.min(0)).astype(int)
        bx1, by1 = np.ceil(tx.max(0)).astype(int)
        bx0, by0 = max(bx0, 0), max(by0, 0)
        bx1, by1 = min(bx1, W - 1), min(by1, H - 1)
        if bx1 < bx0 or by1 < by0:
            continue
        gx, gy = np.meshgrid(np.arange(bx0, bx1 + 1) + 0.5, np.arange(by0, by1 + 1) + 0.5)
        (ax, ay), (bxx, byy), (cx, cy) = tx
        den = (byy - cy) * (ax - cx) + (cx - bxx) * (ay - cy)
        if abs(den) < 1e-9:
            continue
        l1 = ((byy - cy) * (gx - cx) + (cx - bxx) * (gy - cy)) / den
        l2 = ((cy - ay) * (gx - cx) + (ax - cx) * (gy - cy)) / den
        l3 = 1 - l1 - l2
        dentro = (l1 >= -0.02) & (l2 >= -0.02) & (l3 >= -0.02)
        if not dentro.any():
            continue
        px = l1 * fx[0, 0] + l2 * fx[1, 0] + l3 * fx[2, 0]
        py = l1 * fx[0, 1] + l2 * fx[1, 1] + l3 * fx[2, 1]
        # peso: 1 adentro de la caja, baja a 0 en `borde_px`
        d = np.minimum.reduce([px - x0, x1 - px, py - y0, y1 - py])
        w = np.clip(d / borde_px, 0, 1) * dentro
        xi = np.clip(px.astype(int), 0, PW - 1)
        yi = np.clip(py.astype(int), 0, PH - 1)
        col = ph[yi, xi]
        yy, xx = np.mgrid[by0:by1 + 1, bx0:bx1 + 1]
        acum[yy, xx] += col * w[..., None]
        peso[yy, xx] += w
    m = peso > 1e-6
    nuevo = np.zeros_like(acum)
    nuevo[m] = acum[m] / peso[m][:, None]
    # color: el rojo medio de la foto llevado al de la textura en la misma zona (sólo píxeles rojos)
    rojo_f = (nuevo[..., 0] > 100) & (nuevo[..., 1] < 90) & m
    if rojo_f.sum() > 50:
        ganancia = tex[..., :3][rojo_f].mean(0) / np.maximum(nuevo[rojo_f].mean(0), 1)
        ganancia = np.clip(ganancia, 0.6, 1.6)
        blanco = nuevo.min(2) > 170
        nuevo[~blanco & m] *= ganancia
    a = np.clip(np.minimum(peso, 1.0), 0, 1)[..., None]
    out = tex.copy()
    out[..., :3] = tex[..., :3] * (1 - a) + np.clip(nuevo, 0, 255) * a
    guardar(np.clip(out, 0, 255), salida)
    print(f"textura corregida: {salida} ({int(m.sum())} píxeles de la foto, textura {W}×{H})")
    return salida


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("fbx")
    ap.add_argument("foto")
    ap.add_argument("salida")
    ap.add_argument("--vista", default="espalda")
    ap.add_argument("--escala", type=float, default=1119.0)
    ap.add_argument("--centro_x", type=float, default=652.5)
    ap.add_argument("--pie_y", type=float, default=1104.0)
    ap.add_argument("--caja", default="560,205,760,470")
    a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else None)
    proyectar(a.fbx, a.foto, a.salida, a.vista, a.escala, a.centro_x, a.pie_y, tuple(float(v) for v in a.caja.split(",")))
