"""NAVE A LA DERIVA — set único de la serie «A la deriva» (p011): el espacio, la nave por fuera y el centro de
operaciones por dentro. Se construye UNA vez y se reutiliza en todos los episodios (cambian las escenas, no el set).

Ejes: la nave está en el origen; el centro de operaciones tiene el piso en z = 0 y el ventanal panorámico mira a +Y
(la Tierra se ve a través de él). Todo el espacio cabe dentro de ~700 m (el visor del teléfono ve hasta 800 m):
  · CIELO: una esfera de 700 m con una imagen panorámica generada acá (estrellas de colores y brillos, la Vía Láctea,
    nebulosas y polvo) → se ve igual en Cycles y en el EDITOR 3D.
  · TIERRA pequeña y distante (océanos, continentes, casquetes, nubes y atmósfera), un PLANETA GIGANTE con ANILLOS
    (bandas, sombra del anillo, anillos con huecos y transparencia), una LUNA y el SOL (disco + luz).
  · LA NAVE por fuera (para la apertura): módulo de mando con el ventanal, cuerpo cilíndrico con anillos, alas de
    paneles solares, radiadores, motores con brillo tenue, antena parabólica, luces de navegación que titilan.
  · EL CENTRO DE OPERACIONES: piso de rejilla con tiras de luz, paredes de paneles, techo con plafones, ventanal
    panorámico con marco y nervios y vidrio real, consola curva con teclados y tres monitores, pantallas en las
    paredes (telemetría, trayectoria, combustible y energía, comunicaciones), el NÚCLEO DE EVA (anillos que laten
    cuando habla), la pantalla del MÓDULO DE KATE (pasa a «SIN RESPUESTA»), la silla del puesto (Sweet Home), caños,
    cables, lucecitas ámbar y rojas, y una puerta abierta a un pasillo en penumbra (profundidad hacia otros módulos).
Las imágenes de las pantallas se dibujan acá (Pillow) y se ven igual en el render y en el teléfono.

Eventos: `eva_habla` (anillos del núcleo con la voz de EVA), `estado_kate` (la pantalla pasa a SIN RESPUESTA).
Anclas: silla, puesto (cabeza de Aiden), consola, ventanal, tierra, planeta, nave_exterior, nucleo_eva, kate_pantalla.
"""
from __future__ import annotations
import math
import random
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

from estudio.blender import kit as K
from estudio.blender import importar as I

# Recursos externos (para que Actions baje sólo esto): la silla de oficina de Sweet Home 3D (Nexus).
DEPENDENCIAS = ["sh3d:models/chair_office_chair.glb"]

PARAMETROS = {"semilla": 11}

# ---------------------------------------------------------------------------------------------- posiciones clave
TIERRA = Vector((-34.0, 420.0, 26.0))
R_TIERRA = 6.5
PLANETA = Vector((230.0, 520.0, 120.0))
R_PLANETA = 46.0
LUNA = Vector((-120.0, 380.0, 70.0))
R_LUNA = 3.2
SOL_DIR = Vector((0.55, 0.35, 0.28)).normalized()      # desde la nave hacia el Sol
R_CIELO = 700.0

SALA = {"x": 3.6, "y0": -3.2, "y1": 3.0, "alto": 2.9}   # centro de operaciones (interior)
VENTANA = {"x": 2.7, "z0": 0.85, "z1": 2.55}
SILLA = Vector((0.0, 0.55, 0.0))


def _lin(c):
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)


# =============================================================================================== imágenes
def _imagen(nombre: str, arr: np.ndarray) -> bpy.types.Image:
    h, w = arr.shape[:2]
    rgba = np.ones((h, w, 4), dtype=np.float32)
    rgba[:, :, :arr.shape[2]] = arr[:, :, :4]
    im = bpy.data.images.new(nombre, w, h, alpha=arr.shape[2] == 4)
    im.pixels.foreach_set(rgba[::-1].ravel())                 # Blender guarda de abajo hacia arriba
    im.pack()
    return im


def _ruido(h, w, rng, octavas=6, base=4):
    out = np.zeros((h, w), dtype=np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octavas):
        f = base * 2 ** o
        g = rng.random((f // 2 + 2, f + 2)).astype(np.float32)
        ys = np.linspace(0, f // 2, h)
        xs = np.linspace(0, f, w)
        y0, x0 = ys.astype(int), xs.astype(int)
        ty, tx = (ys - y0)[:, None], (xs - x0)[None, :]
        ty, tx = ty * ty * (3 - 2 * ty), tx * tx * (3 - 2 * tx)
        a = g[y0][:, x0] * (1 - tx) + g[y0][:, x0 + 1] * tx
        b = g[y0 + 1][:, x0] * (1 - tx) + g[y0 + 1][:, x0 + 1] * tx
        out += amp * (a * (1 - ty) + b * ty)
        tot += amp
        amp *= 0.55
    return out / tot


def cielo_panoramico(rng, W=4096, H=2048) -> np.ndarray:
    """Panorámica equirectangular: negro profundo, Vía Láctea en diagonal con polvo oscuro, nebulosas de color y
    miles de estrellas (tamaño y color según su «temperatura»)."""
    img = np.zeros((H, W, 3), dtype=np.float32)
    v, u = np.mgrid[0:H, 0:W].astype(np.float32)
    lat = (0.5 - v / H) * math.pi
    lon = (u / W) * 2 * math.pi
    # banda galáctica: gran círculo inclinado
    d = np.stack([np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)], -1)
    eje = np.array([0.35, -0.25, 0.9])
    eje /= np.linalg.norm(eje)
    b = np.abs(d @ eje)
    banda = np.exp(-(b / 0.17) ** 2)
    n1 = _ruido(H, W, rng, 7, 6)
    n2 = _ruido(H, W, rng, 6, 10)
    polvo = np.clip((n2 - 0.45) * 3, 0, 1) * np.exp(-(b / 0.08) ** 2)
    nucleo = np.exp(-((d @ np.array([0.7, 0.5, -0.1]) / 1.0 - 1.0) ** 2) / 0.08)
    brillo = banda * (0.35 + 0.65 * n1) * (1 - 0.8 * polvo) + 0.5 * nucleo * banda
    img += brillo[..., None] * np.array([0.10, 0.09, 0.11]) * 1.6
    img += (nucleo * banda)[..., None] * np.array([0.10, 0.07, 0.04])
    # nebulosas de color (azul-violeta y rojizo), sutiles
    for color, centro, ancho in (((0.05, 0.06, 0.16), (0.25, 0.85), 0.18), ((0.12, 0.03, 0.06), (0.62, 0.35), 0.14),
                                 ((0.03, 0.09, 0.10), (0.85, 0.65), 0.12)):
        cy_, cx_ = centro
        dd = ((v / H - cy_) ** 2 + ((u / W - cx_) * 2) ** 2)
        m = np.exp(-dd / (ancho ** 2)) * np.clip(_ruido(H, W, rng, 6, 5) * 1.6 - 0.35, 0, 1)
        img += m[..., None] * np.array(color) * 2.2
    # estrellas: muchas chiquitas, algunas medianas y pocas brillantes con halo
    def estrellas(n, rmax, brillo_rng, halo=False):
        ys = rng.integers(0, H, n)
        xs = rng.integers(0, W, n)
        # más densas sobre la banda galáctica
        keep = rng.random(n) < (0.35 + 0.65 * banda[ys, xs])
        for y, x in zip(ys[keep], xs[keep]):
            t = rng.random()
            col = np.array([1.0, 0.85, 0.7]) if t < 0.25 else np.array([0.75, 0.85, 1.0]) if t < 0.55 else np.ones(3)
            br = rng.uniform(*brillo_rng)
            r = rmax if halo else 1
            y0_, y1_, x0_, x1_ = max(0, y - r), min(H, y + r + 1), max(0, x - r), min(W, x + r + 1)
            yy, xx = np.mgrid[y0_:y1_, x0_:x1_]
            dist = np.sqrt((yy - y) ** 2 + (xx - x) ** 2)
            g = np.exp(-(dist / (0.6 if not halo else rmax * 0.25)) ** 2)
            img[y0_:y1_, x0_:x1_] += g[..., None] * col * br
    estrellas(26000, 1, (0.08, 0.5))
    estrellas(2200, 1, (0.5, 1.6))
    estrellas(140, 6, (1.5, 4.0), halo=True)
    return np.clip(img, 0, 8)


def textura_tierra(rng, W=1024, H=512) -> tuple[np.ndarray, np.ndarray]:
    v, u = np.mgrid[0:H, 0:W].astype(np.float32)
    lat = (0.5 - v / H) * 180
    n = _ruido(H, W, rng, 7, 4)
    tierra = n > 0.53
    hielo = np.abs(lat) > 68
    col = np.zeros((H, W, 3), np.float32)
    agua = np.array([0.02, 0.08, 0.22]) + (n[..., None] - 0.4) * np.array([0.0, 0.05, 0.12])
    verde = np.array([0.10, 0.20, 0.07]) * (0.8 + 0.4 * _ruido(H, W, rng, 5, 12)[..., None])
    arena = np.array([0.38, 0.30, 0.18])
    seco = (np.abs(lat) < 32) & (np.abs(lat) > 12) & (_ruido(H, W, rng, 4, 6) > 0.5)
    col[:] = agua
    col[tierra] = verde[tierra]
    col[tierra & seco] = arena
    col[hielo] = (0.85, 0.88, 0.92)
    nubes = np.clip((_ruido(H, W, rng, 7, 6) - 0.48) * 3.2, 0, 1)
    return col, nubes


def textura_gigante(rng, W=1024, H=512) -> np.ndarray:
    v, u = np.mgrid[0:H, 0:W].astype(np.float32)
    y = v / H
    turb = _ruido(H, W, rng, 6, 8)
    yy = y + (turb - 0.5) * 0.04
    bandas = np.sin(yy * 38) * 0.5 + 0.5
    finas = np.sin(yy * 150 + turb * 6) * 0.5 + 0.5
    c1, c2, c3 = np.array([0.80, 0.66, 0.46]), np.array([0.62, 0.44, 0.28]), np.array([0.92, 0.84, 0.68])
    col = c1 * (1 - bandas[..., None]) + c2 * bandas[..., None]
    col = col * (0.85 + 0.15 * finas[..., None])
    col = col * (1 - 0.25 * np.exp(-((y - 0.5) / 0.06) ** 2))[..., None] + c3 * 0.25 * np.exp(-((y - 0.5) / 0.06) ** 2)[..., None]
    # gran tormenta ovalada
    d = ((u / W - 0.62) * 2.2) ** 2 + ((y - 0.62) * 6) ** 2
    col = col * (1 - np.exp(-d / 0.02)[..., None] * 0.4) + np.array([0.75, 0.38, 0.22]) * np.exp(-d / 0.02)[..., None] * 0.4
    return col


def textura_anillos(rng, W=1024) -> np.ndarray:
    """Franja radial (x = del borde de adentro al de afuera): color y transparencia con huecos."""
    x = np.linspace(0, 1, W)
    dens = 0.55 + 0.45 * np.sin(x * 90 + np.sin(x * 23) * 2)
    dens *= 0.6 + 0.4 * np.sin(x * 330) ** 2
    dens[(x > 0.56) & (x < 0.62)] *= 0.05                       # división principal
    dens[(x > 0.86) & (x < 0.88)] *= 0.2
    dens *= np.clip(x / 0.05, 0, 1) * np.clip((1 - x) / 0.04, 0, 1)
    col = np.array([0.82, 0.74, 0.60]) * (0.75 + 0.25 * np.sin(x * 47)[..., None] * 0.5 + 0.25)
    out = np.ones((8, W, 4), np.float32)
    out[:, :, :3] = col
    out[:, :, 3] = np.clip(dens, 0, 1) * 0.92
    return out


# ---------------------------------------------------------------------------------------------- pantallas (UI)
def _fuente(tam: int):
    from PIL import ImageFont
    for f in ("DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "FreeSansBold.ttf"):
        try:
            return ImageFont.truetype(f, tam)
        except OSError:
            continue
    return ImageFont.load_default(size=tam)


CIAN, AMBAR, ROJO, VERDE = (90, 210, 255), (255, 176, 60), (255, 70, 60), (90, 230, 160)


def _lienzo(w, h):
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (w, h), (4, 10, 18))
    d = ImageDraw.Draw(im)
    for x in range(0, w, 32):
        d.line([(x, 0), (x, h)], fill=(10, 24, 36))
    for y in range(0, h, 32):
        d.line([(0, y), (w, y)], fill=(10, 24, 36))
    d.rectangle([2, 2, w - 3, h - 3], outline=(30, 90, 130), width=3)
    return im, d


def _a_np(im) -> np.ndarray:
    return np.asarray(im).astype(np.float32) / 255.0


def ui_trayectoria(rng):
    im, d = _lienzo(1024, 640)
    cx, cy = 300, 330
    for r in (60, 130, 210):
        d.ellipse([cx - r, cy - r * 0.62, cx + r, cy + r * 0.62], outline=(20, 70, 100), width=2)
    d.ellipse([cx - 22, cy - 22, cx + 22, cy + 22], fill=(40, 110, 200), outline=CIAN, width=2)   # la Tierra
    pts = [(cx + 210 * math.cos(t) * (1 + 0.0 * t), cy + 130 * math.sin(t)) for t in np.linspace(-0.5, 1.2, 30)]
    pts += [(pts[-1][0] + 18 * k, pts[-1][1] + 9 * k + 0.6 * k * k) for k in range(1, 30)]
    for a, b in zip(pts, pts[1:]):
        d.line([a, b], fill=AMBAR, width=3)
    for k in range(0, len(pts), 4):
        x, y = pts[k]
        d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=AMBAR)
    x, y = pts[-1]
    d.ellipse([x - 8, y - 8, x + 8, y + 8], outline=ROJO, width=3)
    for i in range(18):                                         # retornos intentados (líneas tenues)
        t0 = rng.uniform(-0.3, 1.0)
        a = (cx + 210 * math.cos(t0), cy + 130 * math.sin(t0))
        d.line([a, (cx + rng.uniform(-40, 40), cy + rng.uniform(-30, 30))], fill=(70, 30, 30), width=1)
    f = _fuente(30)
    d.text((620, 40), "TRAYECTORIA", fill=CIAN, font=f)
    d.text((620, 90), "RETORNO: NO VIABLE", fill=ROJO, font=_fuente(26))
    for i in range(6):
        d.rectangle([620, 160 + i * 52, 620 + int(rng.uniform(120, 360)), 182 + i * 52], fill=(20, 80, 110))
    return _a_np(im)


def ui_telemetria(rng):
    im, d = _lienzo(1024, 640)
    for k, color in enumerate((CIAN, VERDE, AMBAR)):
        y0 = 90 + k * 180
        base = rng.uniform(0.3, 0.7)
        ys = base + np.cumsum(rng.normal(0, 0.03, 120))
        ys = np.clip(ys, 0.05, 0.95)
        pts = [(40 + i * 8, y0 + 140 - v * 130) for i, v in enumerate(ys)]
        d.line(pts, fill=color, width=3)
        d.line([(40, y0 + 140), (1000, y0 + 140)], fill=(20, 60, 80), width=2)
    f = _fuente(26)
    d.text((40, 30), "TELEMETRÍA · CONSTANTES · SOPORTE VITAL", fill=CIAN, font=f)
    return _a_np(im)


def ui_energia(rng):
    im, d = _lienzo(640, 1024)
    f = _fuente(34)
    for k, (nombre, val, color) in enumerate((("COMBUSTIBLE", 0.07, ROJO), ("ENERGÍA", 0.46, AMBAR),
                                              ("O2", 0.71, VERDE), ("CO2 FILTRO", 0.58, CIAN))):
        y0 = 80 + k * 230
        d.text((50, y0), nombre, fill=color, font=f)
        d.rectangle([50, y0 + 60, 590, y0 + 130], outline=color, width=3)
        d.rectangle([56, y0 + 66, 56 + int(528 * val), y0 + 124], fill=color)
        for t in range(1, 10):
            x = 50 + t * 54
            d.line([(x, y0 + 130), (x, y0 + 145)], fill=color, width=2)
    return _a_np(im)


def ui_comunicaciones(rng):
    im, d = _lienzo(1024, 640)
    f = _fuente(30)
    d.text((40, 30), "COMUNICACIONES", fill=CIAN, font=f)
    for c in range(6):
        y = 120 + c * 80
        d.rectangle([40, y, 980, y + 56], outline=(25, 80, 110), width=2)
        d.text((60, y + 12), f"CANAL {c + 1:02d}", fill=(90, 160, 200), font=_fuente(24))
        d.text((700, y + 12), "SIN SEÑAL" if c != 2 else "MÓDULO K", fill=ROJO if c != 2 else AMBAR, font=_fuente(24))
    return _a_np(im)


def ui_kate(rng, estado: str):
    im, d = _lienzo(1024, 640)
    d.text((50, 40), "MÓDULO K · TRIPULANTE: KATE", fill=CIAN, font=_fuente(34))
    if estado == "espera":
        d.text((50, 260), "ENLACE: EN ESPERA", fill=AMBAR, font=_fuente(52))
        d.ellipse([880, 60, 940, 120], fill=AMBAR)
    else:
        d.rectangle([40, 210, 984, 420], outline=ROJO, width=6)
        d.text((80, 250), "COMUNICACIÓN", fill=ROJO, font=_fuente(64))
        d.text((80, 330), "SIN RESPUESTA", fill=ROJO, font=_fuente(64))
        d.text((50, 480), "ÚLTIMA RESPUESTA: HACE 9 DÍAS", fill=(220, 120, 110), font=_fuente(32))
        d.ellipse([880, 60, 940, 120], fill=ROJO)
    return _a_np(im)


def ui_eva(rng):
    im, d = _lienzo(1024, 1024)
    c = 512
    for r, w in ((420, 3), (330, 2), (250, 6), (170, 2)):
        d.ellipse([c - r, c - r, c + r, c + r], outline=(40, 140, 200), width=w)
    for k in range(72):
        a = k / 72 * 2 * math.pi
        r0, r1 = 440, 440 + (18 if k % 6 == 0 else 8)
        d.line([(c + r0 * math.cos(a), c + r0 * math.sin(a)), (c + r1 * math.cos(a), c + r1 * math.sin(a))],
               fill=(60, 170, 230), width=3)
    d.text((c - 70, c + 300), "E.V.A.", fill=(120, 220, 255), font=_fuente(56))
    return _a_np(im)


def ui_teclado(rng):
    im, d = _lienzo(1024, 256)
    for f_ in range(4):
        for k in range(24):
            x, y = 20 + k * 41, 20 + f_ * 58
            on = rng.random() < 0.18
            d.rectangle([x, y, x + 34, y + 46], fill=(30, 90, 130) if on else (12, 28, 40), outline=(30, 70, 95))
    return _a_np(im)


def _mat_pantalla(nombre: str, arr: np.ndarray, fuerza: float = 2.2) -> bpy.types.Material:
    """Pantalla: la imagen como color y emisión (se ve en el teléfono con su textura)."""
    mat = bpy.data.materials.new(nombre)
    mat.use_nodes = True
    nt = mat.node_tree
    b = nt.nodes["Principled BSDF"]
    tx = nt.nodes.new("ShaderNodeTexImage")
    tx.image = _imagen(nombre, arr)
    nt.links.new(tx.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(tx.outputs["Color"], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = fuerza
    b.inputs["Roughness"].default_value = 0.15
    b.inputs["Specular IOR Level"].default_value = 0.6
    return mat


def _plano_uv(nombre, centro, ancho, alto, mat, col, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_plane_add(size=1)
    ob = bpy.context.active_object
    ob.name = nombre
    ob.scale = (ancho, alto, 1)
    ob.location = centro
    ob.rotation_euler = rot
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ob.data.materials.append(mat)
    for c in ob.users_collection:
        c.objects.unlink(ob)
    col.objects.link(ob)
    return ob


# =============================================================================================== espacio
def _esfera_uv(nombre, centro, radio, mat, col, seg=64, anillos=32, invertir=False):
    bm = bmesh.new()
    bm.loops.layers.uv.new("UVMap")                         # sin capa UV la textura no se exporta al GLB
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=anillos, radius=radio, calc_uvs=True)
    if invertir:
        bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(nombre)
    bm.to_mesh(me)
    bm.free()
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    if mat:
        me.materials.append(mat)
    ob = bpy.data.objects.new(nombre, me)
    ob.location = centro
    col.objects.link(ob)
    return ob


def _mat_emision_imagen(nombre, img, fuerza=1.0, alfa=False):
    mat = bpy.data.materials.new(nombre)
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tx = nt.nodes.new("ShaderNodeTexImage")
    tx.image = img
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = fuerza
    nt.links.new(tx.outputs["Color"], em.inputs["Color"])
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    return mat


def espacio(col, rng):
    s = bpy.context.scene
    w = bpy.data.worlds.new("espacio")
    s.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0, 0, 0, 1)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.0
    # cielo
    cielo = _esfera_uv("CIELO", (0, 0, 0), R_CIELO, None, col, 96, 48, invertir=True)
    img = _imagen("cielo_espacio", cielo_panoramico(rng))
    m = _mat_emision_imagen("cielo_espacio", img, 1.0)
    cielo.data.materials.append(m)
    cielo.visible_shadow = False
    cielo.visible_diffuse = False
    cielo.visible_glossy = True
    # sol: luz + disco
    sol = K.luz("SOL", "SUN", (0, 0, 0), 4.0, (1.0, 0.96, 0.9), col)
    sol.rotation_euler = SOL_DIR.to_track_quat("-Z", "Y").to_euler()
    sol.rotation_euler.rotate_axis("X", math.pi)
    sol.data.angle = math.radians(0.6)
    disco = _esfera_uv("SOL_DISCO", SOL_DIR * (R_CIELO - 20), 9.0, K.emisivo("sol_disco", (1.0, 0.95, 0.85), 60.0),
                       col, 24, 12)
    disco.visible_shadow = False
    halo = _esfera_uv("SOL_HALO", SOL_DIR * (R_CIELO - 30), 26.0, None, col, 24, 12)
    mh = bpy.data.materials.new("sol_halo")
    mh.use_nodes = True
    b = mh.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (1, 0.9, 0.7, 1)
    b.inputs["Emission Color"].default_value = (1, 0.85, 0.6, 1)
    b.inputs["Emission Strength"].default_value = 3.0
    b.inputs["Alpha"].default_value = 0.12
    mh.surface_render_method = "BLENDED"
    halo.data.materials.append(mh)
    halo.visible_shadow = False
    # Tierra
    ct, nubes = textura_tierra(rng)
    mt = bpy.data.materials.new("tierra")
    mt.use_nodes = True
    bt = mt.node_tree.nodes["Principled BSDF"]
    tx = mt.node_tree.nodes.new("ShaderNodeTexImage")
    tx.image = _imagen("tierra", ct)
    mt.node_tree.links.new(tx.outputs["Color"], bt.inputs["Base Color"])
    bt.inputs["Roughness"].default_value = 0.6
    tierra = _esfera_uv("TIERRA", TIERRA, R_TIERRA, mt, col, 64, 32)
    tierra.rotation_euler = (math.radians(23), 0, math.radians(200))
    mn = bpy.data.materials.new("nubes")
    mn.use_nodes = True
    bn = mn.node_tree.nodes["Principled BSDF"]
    txn = mn.node_tree.nodes.new("ShaderNodeTexImage")
    nub = np.ones((nubes.shape[0], nubes.shape[1], 4), np.float32)
    nub[..., 3] = nubes
    txn.image = _imagen("nubes", nub)
    bn.inputs["Base Color"].default_value = (0.95, 0.96, 1, 1)
    mn.node_tree.links.new(txn.outputs["Alpha"], bn.inputs["Alpha"])
    mn.surface_render_method = "BLENDED"
    capa = _esfera_uv("TIERRA_NUBES", TIERRA, R_TIERRA * 1.012, mn, col, 64, 32)
    capa.rotation_euler = (math.radians(23), 0, math.radians(140))
    atm = _esfera_uv("TIERRA_ATMOSFERA", TIERRA, R_TIERRA * 1.06, None, col, 48, 24)
    ma = bpy.data.materials.new("atmosfera")
    ma.use_nodes = True
    ba = ma.node_tree.nodes["Principled BSDF"]
    ba.inputs["Base Color"].default_value = (0.3, 0.55, 1.0, 1)
    ba.inputs["Emission Color"].default_value = (0.25, 0.5, 1.0, 1)
    ba.inputs["Emission Strength"].default_value = 1.2
    ba.inputs["Alpha"].default_value = 0.18
    ma.surface_render_method = "BLENDED"
    atm.data.materials.append(ma)
    # planeta gigante con anillos
    mg = bpy.data.materials.new("gigante")
    mg.use_nodes = True
    bg = mg.node_tree.nodes["Principled BSDF"]
    txg = mg.node_tree.nodes.new("ShaderNodeTexImage")
    txg.image = _imagen("gigante", textura_gigante(rng))
    mg.node_tree.links.new(txg.outputs["Color"], bg.inputs["Base Color"])
    bg.inputs["Roughness"].default_value = 0.8
    gig = _esfera_uv("PLANETA", PLANETA, R_PLANETA, mg, col, 96, 48)
    incl = Matrix.Rotation(math.radians(24), 4, "X") @ Matrix.Rotation(math.radians(-18), 4, "Y")
    gig.matrix_world = Matrix.Translation(PLANETA) @ incl
    r0, r1 = R_PLANETA * 1.25, R_PLANETA * 2.35
    N = 160
    V, F, UV = [], [], []
    for i in range(N):
        a = 2 * math.pi * i / N
        V += [(r0 * math.cos(a), r0 * math.sin(a), 0), (r1 * math.cos(a), r1 * math.sin(a), 0)]
    for i in range(N):
        j = (i + 1) % N
        F.append((2 * i, 2 * i + 1, 2 * j + 1, 2 * j))
    me = bpy.data.meshes.new("anillos")
    me.from_pydata(V, [], F)
    uv = []
    for p in me.polygons:
        for vi in p.vertices:
            uv.append((0.0 if vi % 2 == 0 else 1.0, 0.5))
    me.uv_layers.new(name="UVMap").data.foreach_set("uv", np.array(uv, np.float32).ravel())
    mr = bpy.data.materials.new("anillos")
    mr.use_nodes = True
    br = mr.node_tree.nodes["Principled BSDF"]
    txr = mr.node_tree.nodes.new("ShaderNodeTexImage")
    txr.image = _imagen("anillos", textura_anillos(rng))
    mr.node_tree.links.new(txr.outputs["Color"], br.inputs["Base Color"])
    mr.node_tree.links.new(txr.outputs["Alpha"], br.inputs["Alpha"])
    br.inputs["Roughness"].default_value = 0.9
    mr.surface_render_method = "BLENDED"
    mr.use_backface_culling = False
    me.materials.append(mr)
    anillos = bpy.data.objects.new("ANILLOS", me)
    col.objects.link(anillos)
    anillos.matrix_world = Matrix.Translation(PLANETA) @ incl
    # luna
    ml = K.material("luna", (0.55, 0.53, 0.5), 0.9, ruido=0.35, escala_ruido=3.0, relieve=0.3)
    _esfera_uv("LUNA", LUNA, R_LUNA, ml, col, 48, 24)
    # para el visor del teléfono: estos materiales con textura se exportan tal cual (sin color plano)
    return {"tierra": tierra, "planeta": gig}


# =============================================================================================== la nave por fuera
def nave_exterior(col):
    casco = K.material("casco", (0.78, 0.79, 0.80), 0.45, 0.25, ruido=0.12, escala_ruido=6.0, relieve=0.08)
    oscuro = K.material("casco_oscuro", (0.18, 0.19, 0.21), 0.5, 0.6, ruido=0.1)
    panel = K.material("panel_solar", (0.05, 0.08, 0.20), 0.25, 0.8, ladrillo=((0.03, 0.05, 0.14), 6.0))
    oro = K.material("lamina_oro", (0.85, 0.62, 0.22), 0.3, 1.0, ruido=0.3, escala_ruido=12, relieve=0.25)
    motor = K.material("tobera", (0.25, 0.25, 0.27), 0.35, 0.9)
    brillo = K.emisivo("motor_brillo", (0.35, 0.6, 1.0), 6.0)
    sx, y0, y1, h = SALA["x"], SALA["y0"], SALA["y1"], SALA["alto"]
    e = 0.25                                                    # espesor del casco
    # módulo de mando: cáscara alrededor de la sala, con el hueco del ventanal adelante
    K.caja("casco_piso", (0, (y0 + y1) / 2, -e / 2 - 0.05), (2 * sx + 2 * e, y1 - y0 + 2 * e, e), casco, col, 0.08)
    K.caja("casco_techo", (0, (y0 + y1) / 2, h + e / 2 + 0.05), (2 * sx + 2 * e, y1 - y0 + 2 * e, e), casco, col, 0.08)
    for sgn in (-1, 1):
        K.caja(f"casco_lado_{sgn}", (sgn * (sx + e / 2 + 0.05), (y0 + y1) / 2, h / 2), (e, y1 - y0 + 2 * e, h + 2 * e),
               casco, col, 0.06)
    vx, vz0, vz1 = VENTANA["x"], VENTANA["z0"], VENTANA["z1"]
    yf = y1 + e / 2 + 0.06
    K.caja("casco_frente_bajo", (0, yf, vz0 / 2 - 0.05), (2 * sx + 2 * e, e, vz0 + 0.3), casco, col, 0.05)
    K.caja("casco_frente_alto", (0, yf, (vz1 + h + e) / 2 + 0.05), (2 * sx + 2 * e, e, h + e - vz1 + 0.2), casco, col, 0.05)
    for sgn in (-1, 1):
        K.caja(f"casco_frente_{sgn}", (sgn * (vx + (sx + e - vx) / 2), yf, h / 2), (sx + e - vx, e, h), casco, col, 0.05)
    # visera sobre el ventanal y cuerpo cilíndrico hacia atrás con anillos
    K.caja("visera", (0, y1 + 0.6, h + 0.15), (2 * sx + 0.6, 1.0, 0.18), oscuro, col, 0.05)
    cuerpo_y = y0 - 9.0
    K.cilindro("cuerpo", (0, cuerpo_y, h / 2), 2.6, 16.0, casco, col, 40, "Y")
    for k in range(5):
        K.cilindro(f"anillo_{k}", (0, y0 - 2.0 - k * 3.4, h / 2), 2.85, 0.35, oscuro, col, 40, "Y")
    K.cilindro("modulo_k", (5.4, cuerpo_y + 2.0, h / 2), 1.5, 6.0, oro, col, 32, "Y")       # el módulo de Kate
    K.caja("conector_k", (3.4, cuerpo_y + 2.0, h / 2), (2.0, 1.2, 1.2), oscuro, col, 0.05)
    # alas de paneles solares
    for sgn in (-1, 1):
        K.cilindro(f"mastil_{sgn}", (sgn * 6.0, cuerpo_y - 3.0, h / 2), 0.12, 7.0, oscuro, col, 12, "X")
        for k in range(3):
            K.caja(f"panel_{sgn}_{k}", (sgn * (5.0 + 3.4 * (k + 1)), cuerpo_y - 3.0, h / 2), (3.2, 4.2, 0.06),
                   panel, col)
        K.caja(f"radiador_{sgn}", (sgn * 3.6, cuerpo_y + 4.5, h / 2 + 2.2), (2.6, 3.0, 0.05), casco, col)
    # motores
    for i, (dx, dz) in enumerate(((-1.2, 0.3), (1.2, 0.3), (0, -0.9), (0, 1.5))):
        K.cilindro(f"tobera_{i}", (dx, cuerpo_y - 9.2, h / 2 + dz - 0.3), 0.75, 1.6, motor, col, 24, "Y")
        K.cilindro(f"tobera_brillo_{i}", (dx, cuerpo_y - 10.05, h / 2 + dz - 0.3), 0.55, 0.05, brillo, col, 24, "Y")
    # antena parabólica
    K.cilindro("antena_mastil", (-2.0, cuerpo_y + 5, h + 1.8), 0.08, 3.0, oscuro, col, 8)
    K.esfera("antena_plato", (-2.0, cuerpo_y + 5, h + 3.4), 1.1, casco, col, 2, (1, 1, 0.3))
    # luces de navegación (titilan)
    luces = []
    for nombre, pos, colr in (("nav_roja", (-sx - 0.4, y1 - 0.4, h * 0.6), (1, 0.08, 0.05)),
                              ("nav_verde", (sx + 0.4, y1 - 0.4, h * 0.6), (0.1, 1, 0.3)),
                              ("baliza", (0, cuerpo_y - 6.0, h / 2 + 2.9), (1, 1, 1))):
        o = K.esfera(nombre, pos, 0.09, K.emisivo(nombre, colr, 40.0), col, 2)
        luces.append(o)
    return {"luces": luces, "centro": Vector((0, cuerpo_y + 3, h / 2))}


# =============================================================================================== centro de operaciones
def interior(col, rng):
    sx, y0, y1, h = SALA["x"], SALA["y0"], SALA["y1"], SALA["alto"]
    pared = K.material("pared_panel", (0.20, 0.22, 0.25), 0.55, 0.35, ladrillo=((0.16, 0.17, 0.20), 1.6), relieve=0.15)
    gris = K.material("metal_gris", (0.32, 0.34, 0.37), 0.4, 0.7, ruido=0.15)
    oscuro = K.material("metal_oscuro", (0.07, 0.075, 0.085), 0.45, 0.6)
    piso = K.material("piso_rejilla", (0.10, 0.11, 0.12), 0.6, 0.6, ladrillo=((0.05, 0.05, 0.06), 6.0), relieve=0.3)
    tira = K.emisivo("tira_azul", (0.25, 0.6, 1.0), 4.0)
    plafon = K.emisivo("plafon", (0.75, 0.85, 1.0), 3.0)
    ambar = K.emisivo("led_ambar", (1.0, 0.55, 0.1), 12.0)
    rojo = K.emisivo("led_rojo", (1.0, 0.06, 0.05), 12.0)
    marco = K.material("marco_ventanal", (0.12, 0.13, 0.15), 0.35, 0.8)
    vidrio = bpy.data.materials.new("vidrio_ventanal")
    vidrio.use_nodes = True
    bv = vidrio.node_tree.nodes["Principled BSDF"]
    bv.inputs["Base Color"].default_value = (0.85, 0.92, 1.0, 1)
    bv.inputs["Roughness"].default_value = 0.02
    bv.inputs["IOR"].default_value = 1.5
    bv.inputs["Transmission Weight"].default_value = 1.0
    bv.inputs["Alpha"].default_value = 0.12
    bv.inputs["Coat Weight"].default_value = 0.3
    vidrio.surface_render_method = "BLENDED"
    vidrio["estudio"] = {"color": [0.85, 0.92, 1.0], "rugosidad": 0.02, "metal": 0.0, "emision": None, "fuerza": 0.0,
                         "alfa": 0.12}
    # cáscara: piso, techo, paredes (el frente tiene el ventanal)
    K.caja("piso", (0, (y0 + y1) / 2, -0.05), (2 * sx, y1 - y0, 0.1), piso, col)
    K.caja("techo", (0, (y0 + y1) / 2, h + 0.05), (2 * sx, y1 - y0, 0.1), gris, col)
    for sgn in (-1, 1):
        K.caja(f"pared_{sgn}", (sgn * (sx + 0.05), (y0 + y1) / 2, h / 2), (0.1, y1 - y0, h), pared, col)
        K.caja(f"tira_piso_{sgn}", (sgn * (sx - 0.12), (y0 + y1) / 2, 0.03), (0.04, y1 - y0 - 0.4, 0.02), tira, col)
        K.caja(f"tira_techo_{sgn}", (sgn * (sx - 0.4), (y0 + y1) / 2, h - 0.02), (0.06, y1 - y0 - 1.0, 0.02), tira, col)
    # pared de atrás con la puerta abierta al pasillo
    puerta_w, puerta_h = 1.3, 2.2
    K.caja("pared_atras_izq", (-(sx + puerta_w / 2) / 2, y0 - 0.05, h / 2), (sx - puerta_w / 2, 0.1, h), pared, col)
    K.caja("pared_atras_der", ((sx + puerta_w / 2) / 2, y0 - 0.05, h / 2), (sx - puerta_w / 2, 0.1, h), pared, col)
    K.caja("pared_atras_dintel", (0, y0 - 0.05, (puerta_h + h) / 2), (puerta_w, 0.1, h - puerta_h), pared, col)
    K.caja("marco_puerta", (0, y0 - 0.02, puerta_h + 0.04), (puerta_w + 0.1, 0.12, 0.08), ambar, col)
    # pasillo en penumbra
    pas_l = 7.0
    K.caja("pasillo_piso", (0, y0 - pas_l / 2, -0.05), (puerta_w + 0.6, pas_l, 0.1), piso, col)
    K.caja("pasillo_techo", (0, y0 - pas_l / 2, puerta_h + 0.3), (puerta_w + 0.6, pas_l, 0.1), gris, col)
    for sgn in (-1, 1):
        K.caja(f"pasillo_pared_{sgn}", (sgn * (puerta_w / 2 + 0.35), y0 - pas_l / 2, (puerta_h + 0.3) / 2),
               (0.1, pas_l, puerta_h + 0.3), pared, col)
    for k in range(4):
        K.caja(f"pasillo_luz_{k}", (0, y0 - 1.0 - k * 1.7, puerta_h + 0.24), (0.5, 0.12, 0.02), tira, col)
    K.caja("pasillo_fondo", (0, y0 - pas_l, (puerta_h + 0.3) / 2), (puerta_w + 0.6, 0.1, puerta_h + 0.3), oscuro, col)
    K.luz("luz_pasillo", "POINT", (0, y0 - 3.0, puerta_h - 0.2), 25, (0.4, 0.6, 1.0), col, radio=0.2)
    # ventanal: marco + nervios + vidrio
    vx, vz0, vz1 = VENTANA["x"], VENTANA["z0"], VENTANA["z1"]
    K.caja("frente_bajo", (0, y1 + 0.05, vz0 / 2), (2 * sx, 0.1, vz0), pared, col)
    K.caja("frente_alto", (0, y1 + 0.05, (vz1 + h) / 2), (2 * sx, 0.1, h - vz1), pared, col)
    for sgn in (-1, 1):
        K.caja(f"frente_lado_{sgn}", (sgn * (vx + (sx - vx) / 2), y1 + 0.05, h / 2), (sx - vx, 0.1, h), pared, col)
    for z in (vz0, vz1):
        K.caja(f"marco_h_{z:.2f}", (0, y1 - 0.02, z), (2 * vx + 0.12, 0.18, 0.1), marco, col, 0.02)
    for x in (-vx, -vx / 3, vx / 3, vx):
        K.caja(f"nervio_{x:.2f}", (x, y1 - 0.02, (vz0 + vz1) / 2), (0.09, 0.2, vz1 - vz0 + 0.1), marco, col, 0.02)
    K.caja("VIDRIO", (0, y1 + 0.02, (vz0 + vz1) / 2), (2 * vx, 0.02, vz1 - vz0), vidrio, col)
    # techo: plafones y caños
    for i, y in enumerate((-1.8, -0.2, 1.4)):
        K.caja(f"plafon_{i}", (0, y, h - 0.03), (1.6, 0.35, 0.03), plafon, col)
    for sgn in (-1, 1):
        for k in range(3):
            K.cilindro(f"cano_{sgn}_{k}", (sgn * (sx - 0.25 - k * 0.12), (y0 + y1) / 2, h - 0.15 - k * 0.04), 0.045,
                       y1 - y0 - 0.2, gris if k != 1 else oscuro, col, 12, "Y")
    # consola curva (arco alrededor del puesto) con teclados
    cons_c = Vector((0.0, SILLA.y - 0.35, 0.0))
    R = 1.65
    tecl = _mat_pantalla("teclado", ui_teclado(rng), 1.2)
    for k, a in enumerate(np.linspace(-62, 62, 7)):
        ang = math.radians(a)
        p = cons_c + Vector((math.sin(ang) * R, math.cos(ang) * R, 0))
        mesa = K.caja(f"consola_{k}", (p.x, p.y, 0.39), (0.66, 0.62, 0.78), oscuro, col, 0.03, rot_z=-ang)
        tapa = K.caja(f"consola_tapa_{k}", (p.x, p.y, 0.79), (0.68, 0.66, 0.04), gris, col, 0.01, rot_z=-ang)
        q = cons_c + Vector((math.sin(ang) * (R - 0.12), math.cos(ang) * (R - 0.12), 0))
        _plano_uv(f"teclado_{k}", (q.x, q.y, 0.815), 0.5, 0.14, tecl, col, (0, 0, -ang))
        for j in range(3):
            led = ambar if (k + j) % 4 else rojo
            K.caja(f"led_{k}_{j}", (p.x + math.cos(ang) * (j - 1) * 0.12, p.y - math.sin(ang) * (j - 1) * 0.12, 0.6),
                   (0.03, 0.66, 0.03), led, col)
    # tres monitores grandes sobre la consola + pantallas en las paredes
    pantallas = {}
    imgs = {"trayectoria": ui_trayectoria(rng), "telemetria": ui_telemetria(rng), "energia": ui_energia(rng),
            "comunicaciones": ui_comunicaciones(rng)}
    for nombre, a, ancho, alto in (("telemetria", -38, 0.78, 0.48), ("trayectoria", 0, 1.05, 0.62),
                                   ("comunicaciones", 38, 0.78, 0.48)):
        ang = math.radians(a)
        p = cons_c + Vector((math.sin(ang) * (R + 0.08), math.cos(ang) * (R + 0.08), 0))
        nrm = Vector((math.sin(ang), math.cos(ang), 0))             # hacia afuera (lejos de la silla)
        mc = p + nrm * 0.025
        K.caja(f"monitor_marco_{nombre}", (mc.x, mc.y, 1.16), (ancho + 0.06, 0.04, alto + 0.06), oscuro, col, 0.01,
               rot_z=-ang)
        pc = p + nrm * 0.06
        K.cilindro(f"monitor_pie_{nombre}", (pc.x, pc.y, 0.92), 0.025, 0.25, gris, col, 8)
        ps = p - nrm * 0.004
        o = _plano_uv(f"PANTALLA_{nombre}", (ps.x, ps.y, 1.16), ancho, alto,
                      _mat_pantalla(f"ui_{nombre}", imgs[nombre]), col, (math.radians(90), 0, -ang))
        pantallas[nombre] = o
        K.luz(f"luz_pantalla_{nombre}", "AREA", (p.x, p.y - 0.25, 1.16), 6, (0.4, 0.75, 1.0), col,
              rot=(math.radians(-90), 0, -ang), tam=0.5, sombra=False)
    # pantalla vertical de energía en la pared derecha, comunicaciones/K en la izquierda
    K.caja("marco_energia", (sx - 0.025, 1.4, 1.55), (0.03, 0.68, 1.05), oscuro, col)
    o = _plano_uv("PANTALLA_energia", (sx - 0.045, 1.4, 1.55), 0.62, 0.99, _mat_pantalla("ui_energia", imgs["energia"]),
                  col, (math.radians(90), 0, math.radians(-90)))
    pantallas["energia"] = o
    k_esp = _plano_uv("PANTALLA_kate_espera", (-sx + 0.045, 1.2, 1.62), 1.0, 0.62,
                      _mat_pantalla("ui_kate_espera", ui_kate(rng, "espera")), col, (math.radians(90), 0, math.radians(90)))
    k_sin = _plano_uv("PANTALLA_kate_sin_respuesta", (-sx + 0.047, 1.2, 1.62), 1.0, 0.62,
                      _mat_pantalla("ui_kate_sin", ui_kate(rng, "sin"), 3.0), col, (math.radians(90), 0, math.radians(90)))
    K.caja("marco_kate", (-sx + 0.025, 1.2, 1.62), (0.03, 1.06, 0.68), oscuro, col)
    k_sin.hide_render = k_sin.hide_viewport = True
    # núcleo de EVA: sobre el ventanal, al centro (anillos que laten cuando habla)
    eva_c = Vector((0.0, y1 - 0.08, h - 0.2))
    o = _plano_uv("EVA_PANEL", eva_c, 0.62, 0.62, _mat_pantalla("ui_eva", ui_eva(rng), 1.8), col,
                  (math.radians(90), 0, 0))
    anillos = []
    m_eva = K.emisivo("eva_anillo", (0.35, 0.8, 1.0), 10.0)
    for i, r in enumerate((0.11, 0.17, 0.23)):
        bm = bmesh.new()
        bmesh.ops.create_circle(bm, cap_ends=False, segments=48, radius=r)
        me = bpy.data.meshes.new(f"eva_anillo_{i}")
        bm.to_mesh(me)
        bm.free()
        ob = bpy.data.objects.new(f"EVA_ANILLO_{i}", me)
        col.objects.link(ob)
        ob.location = eva_c + Vector((0, -0.02 - 0.005 * i, 0))
        ob.rotation_euler = (math.radians(90), 0, 0)
        # un aro fino: se le da ancho con un borde extruido
        bm = bmesh.new()
        bm.from_mesh(me)
        res = bmesh.ops.extrude_edge_only(bm, edges=bm.edges[:])
        for v in [e for e in res["geom"] if isinstance(e, bmesh.types.BMVert)]:
            v.co *= 1.08
        bm.to_mesh(me)
        bm.free()
        me.materials.append(m_eva)
        anillos.append(ob)
    K.luz("luz_eva", "POINT", eva_c + Vector((0, -0.3, -0.1)), 8, (0.35, 0.75, 1.0), col, radio=0.15, sombra=False)
    # silla del puesto: la de oficina de Sweet Home (reutilizada)
    silla_objs = I.importar("sh3d:models/chair_office_chair.glb", col)
    raiz_silla = [o for o in silla_objs if o.parent is None]
    for o in raiz_silla:
        o.location = SILLA
        o.rotation_mode = "XYZ"                                # el GLB trae cuaterniones: sin esto no gira
        o.rotation_euler = (0, 0, math.radians(180))           # respaldo atrás (−Y), asiento mirando a la consola
    tapizado = K.material("silla_tapizado", (0.09, 0.10, 0.12), 0.7, ruido=0.1)
    for o in silla_objs:                                       # tapizado gris oscuro (el original es tela azul)
        if o.type == "MESH":
            for i, m in enumerate(o.data.materials):
                if m and (sum(m.diffuse_color[:3]) > 0.6 or any(n.type == "TEX_IMAGE" for n in m.node_tree.nodes)):
                    o.data.materials[i] = tapizado
    # cables por el piso hasta la consola, lucecitas en las paredes, gabinetes
    for k in range(5):
        pts = [Vector((-2.4 + k * 0.08, -2.6, 0.02)), Vector((-1.5 + k * 0.1, -0.5, 0.02)),
               Vector((-1.2 + k * 0.12, 1.0, 0.02)), Vector((-0.9 + k * 0.1, 1.45, 0.05))]
        cv = bpy.data.curves.new(f"cable_{k}", "CURVE")
        cv.dimensions = "3D"
        sp = cv.splines.new("BEZIER")
        sp.bezier_points.add(len(pts) - 1)
        for bp, p in zip(sp.bezier_points, pts):
            bp.co = p
            bp.handle_left_type = bp.handle_right_type = "AUTO"
        cv.bevel_depth = 0.012
        cv.bevel_resolution = 2
        ob = bpy.data.objects.new(f"CABLE_{k}", cv)
        ob.data.materials.append(oscuro)
        col.objects.link(ob)
    for sgn in (-1, 1):
        for k in range(3):
            K.caja(f"gabinete_{sgn}_{k}", (sgn * (sx - 0.3), -2.4 + k * 0.75, 0.9), (0.5, 0.68, 1.8), gris, col, 0.02)
            for j in range(4):
                K.caja(f"gab_led_{sgn}_{k}_{j}", (sgn * (sx - 0.56), -2.55 + k * 0.75 + j * 0.08, 1.5),
                       (0.02, 0.03, 0.03), ambar if j % 3 else rojo, col)
    # luces: ambiente frío y bajo, sol que entra por el ventanal, relleno ámbar desde abajo de la consola
    K.luz("luz_techo", "AREA", (0, -0.2, h - 0.08), 60, (0.65, 0.78, 1.0), col, rot=(0, 0, 0), tam=2.2)
    K.luz("luz_ambar_consola", "POINT", (0, 1.4, 0.3), 12, (1.0, 0.55, 0.2), col, radio=0.3)
    K.luz("luz_relleno_fondo", "POINT", (0, -2.4, 1.8), 15, (0.4, 0.55, 0.9), col, radio=0.5)
    return {"pantallas": pantallas, "kate": (k_esp, k_sin), "eva_anillos": anillos, "eva_c": eva_c}


# =============================================================================================== armado y eventos
def construir(parametros: dict | None = None) -> dict:
    p = {**PARAMETROS, **(parametros or {})}
    rng = np.random.default_rng(p["semilla"])
    col = K.coleccion("ESCENARIO_nave_deriva")
    c_esp, c_ext, c_int = (K.coleccion(n, col) for n in ("espacio", "nave_exterior", "centro_operaciones"))
    esp = espacio(c_esp, rng)
    ext = nave_exterior(c_ext)
    inn = interior(c_int, rng)
    s = bpy.context.scene
    try:
        s.view_settings.view_transform = "AgX"
        s.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        pass
    anclas = {
        "silla": tuple(SILLA + Vector((0, 0, 0.5))),
        "puesto": tuple(SILLA + Vector((0, 0.05, 1.22))),
        "hombro": tuple(SILLA + Vector((0.18, 0.0, 1.35))),
        "consola": (0.0, SILLA.y + 1.3, 0.95),
        "pantalla_trayectoria": tuple(inn["pantallas"]["trayectoria"].location),
        "pantalla_telemetria": tuple(inn["pantallas"]["telemetria"].location),
        "pantalla_energia": tuple(inn["pantallas"]["energia"].location),
        "kate_pantalla": tuple(inn["kate"][0].location),
        "nucleo_eva": tuple(inn["eva_c"]),
        "ventanal": (0.0, SALA["y1"], (VENTANA["z0"] + VENTANA["z1"]) / 2),
        "tierra": tuple(TIERRA),
        "planeta": tuple(PLANETA),
        "nave_exterior": tuple(ext["centro"]),
        "fondo_sala": (0.0, SALA["y0"] + 0.4, 1.5),
    }
    return {"anclas": anclas, "animables": {"eva_anillos": inn["eva_anillos"], "kate": inn["kate"],
                                            "luces_nav": ext["luces"]},
            "personajes": []}


def eva_habla(animables: dict, frame_inicio: int = 1, lineas: list | None = None, fps: int = 30, nf: int = 1800,
              **_):
    """Los anillos del núcleo de EVA laten con el volumen de su voz (escala) y quedan respirando en reposo."""
    from estudio import config
    from estudio.blender import stickman as SM
    amp = np.zeros(nf + 1)
    for ln in lineas or []:
        ruta = config.ruta_recurso(ln["audio"])
        if not ruta.exists():
            raise FileNotFoundError(f"eva_habla: falta el audio {ln['audio']}")
        env = SM._envolvente_audio(ruta, fps)[:, 0]
        f0 = int(round(ln["inicio_s"] * fps)) + 1
        n = min(len(env), nf + 1 - f0)
        if n > 0:
            amp[f0:f0 + n] = np.maximum(amp[f0:f0 + n], env[:n])
    amp = np.convolve(amp, np.ones(3) / 3, mode="same")
    for i, ob in enumerate(animables["eva_anillos"]):
        for f in range(1, nf + 1, 2):
            reposo = 1.0 + 0.03 * math.sin(f / fps * 2 * math.pi * 0.25 + i)
            k = reposo + amp[f] * (0.18 + 0.1 * i)
            ob.scale = (k, k, k)
            ob.keyframe_insert("scale", frame=f)


def estado_kate(animables: dict, frame_inicio: int = 1, **_):
    """La pantalla del módulo de Kate pasa de «EN ESPERA» a «COMUNICACIÓN SIN RESPUESTA»."""
    esp, sin = animables["kate"]
    for o, antes, despues in ((esp, False, True), (sin, True, False)):
        for fr, v in ((1, antes), (frame_inicio, despues)):
            o.hide_render = o.hide_viewport = v
            o.keyframe_insert("hide_render", frame=fr)
            o.keyframe_insert("hide_viewport", frame=fr)


def luces_navegacion(animables: dict, frame_inicio: int = 1, nf: int = 1800, fps: int = 30, **_):
    """Las luces de navegación de la nave titilan (se ven en la apertura)."""
    for i, o in enumerate(animables["luces_nav"]):
        periodo = int(fps * (1.0 + 0.3 * i))
        for f in range(1, nf + 1, periodo):
            for fr, k in ((f, 1.0), (f + 4, 0.3), (f + 8, 0.3)):
                o.scale = (k, k, k)
                o.keyframe_insert("scale", frame=fr)
