"""Stickman de «Dúo Cero»: vestuario pintado, pelo y cara 2D animada sobre los modelos blancos que mandó el dueño.

Los FBX (Tripo3D, esqueleto mixamorig de 65 huesos, 0,9 m de alto, miran a −Y) no se tocan: el estudio les pone encima
  · una textura nueva pintada por zonas del cuerpo (estilos «urbano», «deportivo», «tactico», «elegante», como las
    láminas del dueño) calculada en el espacio UV desde la posición de reposo de cada punto de la malla;
  · un casco de pelo (mechones en punta, peinado al costado o el de Luna con cola de caballo);
  · la cara 2D: ojos con brillo, párpados, cejas, boca y rubor como formas planas apoyadas sobre la esfera de la cabeza,
    colgadas del hueso Head, con formas clave (shape keys) para parpadeo, miradas, expresiones y las vocales al hablar.

Uso en el manifiesto (sección "personajes", modelos «stickman:masculino» / «stickman:femenino»):
  {"id": "nico", "modelo": "stickman:masculino", "alto_m": 1.78,
   "vestuario": {"estilo": "tactico", "pelo": "puntas", "color_pelo": [0.32, 0.18, 0.08]},
   "cara": {"expresiones": [{"t": 0.0, "expr": "neutral"}, {"t": 4.2, "expr": "picara"}],
            "miradas": [{"t": 2.0, "u": 0.6, "v": 0.0}], "habla": [{"inicio_s": 3.1, "audio": "<mp3>", "texto": "…"}]},
   "acciones": [...]}
"""
from __future__ import annotations
import hashlib
import math
import random
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector

from estudio import config
from estudio.blender import kit as K

# Modelos definitivos del dueño (17/11/2026): proporcionados a las animaciones de Mixamo (0,98 m al importar)
REFS = {
    "stickman:masculino": "subidas:stickman/stickman_masculino_v2/tripo_convert_e14b4acf-be93-476b-93c0-684fed3e5838.fbx",
    "stickman:femenino": "subidas:stickman/stickman_femenino_v2/tripo_convert_029c826d-6f9c-4653-95dc-4cabaf1c19c3.fbx",
}
ALTO_MODELO = {"stickman:masculino": 0.979, "stickman:femenino": 0.979}

# El vestuario se dibujó midiendo los primeros Stickman (0,90 m). Para que sirva con cualquier modelo, la posición
# de reposo se lleva a esas proporciones por hitos de los huesos (alturas, brazos, piernas, ancho del torso).
HITOS_Z = ["ToeBase", "Foot", "Leg", "UpLeg", "Hips", "Spine1", "Spine2", "Shoulder", "Neck", "Head", "HeadTop_End"]
REFERENCIA = {
    False: {"z": [0.018, 0.069, 0.253, 0.424, 0.448, 0.530, 0.585, 0.635, 0.651, 0.698, 0.810],
            "brazo": [0.064, 0.213, 0.370], "pierna": 0.041, "torso": 0.0575},
    True: {"z": [0.012, 0.078, 0.261, 0.418, 0.441, 0.522, 0.579, 0.629, 0.644, 0.683, 0.774],
           "brazo": [0.059, 0.216, 0.353], "pierna": 0.040, "torso": 0.0589},
}

# ------------------------------------------------------------------------------------------------- vestuario
BLANCO = (0.86, 0.86, 0.86)

ESTILOS = {
    "urbano": {"remera": (0.018, 0.018, 0.02), "detalle": (0.32, 0.32, 0.33), "pantalon": (0.02, 0.02, 0.022),
               "zapato": (0.015, 0.015, 0.017), "suela": BLANCO, "manga": "corta"},
    "deportivo": {"remera": (0.02, 0.11, 0.62), "detalle": BLANCO, "pantalon": (0.02, 0.11, 0.62),
                  "zapato": (0.02, 0.11, 0.62), "suela": BLANCO, "medias": BLANCO, "manga": "corta"},
    "tactico": {"remera": (0.16, 0.20, 0.06), "chaleco": (0.12, 0.155, 0.045), "detalle": (0.05, 0.06, 0.02),
                "pantalon": (0.15, 0.185, 0.055), "zapato": (0.012, 0.012, 0.013), "suela": (0.03, 0.03, 0.03),
                "cinturon": (0.012, 0.012, 0.013), "hebilla": (0.45, 0.45, 0.45), "rodillera": (0.012, 0.012, 0.014),
                "cordones": (0.25, 0.25, 0.25), "manga": "corta"},
    "elegante": {"remera": (0.012, 0.012, 0.014), "camisa": BLANCO, "corbata": (0.008, 0.008, 0.01),
                 "detalle": (0.55, 0.55, 0.55), "pantalon": (0.012, 0.012, 0.014), "zapato": (0.01, 0.01, 0.011),
                 "suela": (0.03, 0.03, 0.03), "manga": "larga"},
}

GRUPO_REGION = {"Head": "cabeza", "Neck": "cabeza", "HeadTop_End": "cabeza",
                "Spine": "torso", "Spine1": "torso", "Spine2": "torso", "Hips": "torso",
                "LeftShoulder": "torso", "RightShoulder": "torso", "LeftArm": "brazo", "RightArm": "brazo",
                "LeftForeArm": "antebrazo", "RightForeArm": "antebrazo",
                "LeftUpLeg": "pierna", "RightUpLeg": "pierna", "LeftLeg": "pierna", "RightLeg": "pierna",
                "LeftFoot": "pie", "RightFoot": "pie", "LeftToeBase": "pie", "RightToeBase": "pie"}
REGIONES = ["cabeza", "torso", "brazo", "antebrazo", "mano", "pierna", "pie"]


def _region(nombre_grupo: str) -> int:
    n = nombre_grupo.replace("mixamorig:", "")
    return REGIONES.index(GRUPO_REGION.get(n, "mano" if "Hand" in n else "torso"))


def datos_reposo(malla, raiz) -> dict:
    """Posición y normal de reposo de cada vértice en unidades del modelo (0,9 m de alto, frente a −Y) y su región."""
    m = raiz.matrix_world.inverted() @ malla.matrix_world
    rot = m.to_3x3().normalized()
    n = len(malla.data.vertices)
    co = np.empty(n * 3)
    malla.data.vertices.foreach_get("co", co)
    co = co.reshape(n, 3)
    no = np.empty(n * 3)
    malla.data.vertices.foreach_get("normal", no)
    no = no.reshape(n, 3)
    M = np.array(m)
    R = np.array(rot)
    pos = co @ M[:3, :3].T + M[:3, 3]
    nor = no @ R.T
    nor /= np.maximum(1e-9, np.linalg.norm(nor, axis=1))[:, None]
    gname = {g.index: g.name for g in malla.vertex_groups}
    reg = np.zeros(n, dtype=np.int32)
    for v in malla.data.vertices:
        if v.groups:
            g = max(v.groups, key=lambda g: g.weight)
            reg[v.index] = _region(gname[g.group])
    hitos = {}
    arm = next((md.object for md in malla.modifiers if md.type == "ARMATURE" and md.object), None)
    if arm is not None:
        ma = raiz.matrix_world.inverted() @ arm.matrix_world
        for b in arm.data.bones:
            hitos[b.name.replace("mixamorig:", "")] = ma @ b.head_local
    return {"pos": pos, "nor": nor, "reg": reg, "hitos": hitos}


def normalizar(datos: dict, femenino: bool):
    """Posición de reposo llevada a las proporciones de los Stickman de referencia (sólo para pintar el vestuario)."""
    h = datos.get("hitos") or {}
    pos = datos["pos"].copy()
    if "Hips" not in h:
        return pos
    ref = REFERENCIA[femenino]
    lado = lambda n: (h["Left" + n].x - h["Right" + n].x) / 2 if ("Left" + n in h and "Right" + n in h) else None
    zs = []
    for n in HITOS_Z:
        if n in h:
            zs.append(h[n].z)
        else:
            zs.append((h["Left" + n].z + h["Right" + n].z) / 2)
    pos[:, 2] = np.interp(pos[:, 2], [0.0] + zs + [zs[-1] + 1.0], [0.0] + ref["z"] + [ref["z"][-1] + 1.0])
    x = datos["pos"][:, 0]
    ax = np.abs(x)
    reg = datos["reg"]
    brazo = (reg == REGIONES.index("brazo")) | (reg == REGIONES.index("antebrazo")) | (reg == REGIONES.index("mano"))
    pierna = (reg == REGIONES.index("pierna")) | (reg == REGIONES.index("pie"))
    nb = [lado("Arm"), lado("ForeArm"), lado("Hand")]
    nax = ax.copy()
    if None not in nb:
        nax[brazo] = np.interp(ax[brazo], [0.0] + nb + [nb[-1] + 1.0], [0.0] + ref["brazo"] + [ref["brazo"][-1] + 1.0])
    lp = lado("Leg")
    if lp is not None:
        nax[pierna] = np.maximum(0.0, ax[pierna] - (lp - ref["pierna"]))
    torso = ~brazo & ~pierna
    zt = (datos["pos"][:, 2] > h["Spine1"].z) & (datos["pos"][:, 2] < h["Spine2"].z) & (reg == REGIONES.index("torso"))
    if zt.sum() > 10:
        k = ref["torso"] / float(np.percentile(ax[zt], 95))
        nax[torso] = ax[torso] * k
    pos[:, 0] = np.sign(x) * nax
    return pos


def _rasterizar(malla, datos: dict, T: int):
    """Muestras por texel de la textura (espacio UV): índice de píxel, posición, normal y región de reposo."""
    me = malla.data
    me.calc_loop_triangles()
    uvl = me.uv_layers.active.data
    nt = len(me.loop_triangles)
    loops = np.empty(nt * 3, dtype=np.int64)
    me.loop_triangles.foreach_get("loops", loops)
    verts = np.empty(nt * 3, dtype=np.int64)
    me.loop_triangles.foreach_get("vertices", verts)
    uv = np.empty(len(uvl) * 2)
    uvl.foreach_get("uv", uv)
    uv = uv.reshape(-1, 2)[loops].reshape(nt, 3, 2) * T - 0.5
    verts = verts.reshape(nt, 3)
    pix, w_all, tri_all = [], [], []
    for t in range(nt):
        a, b, c = uv[t]
        x0, y0 = np.floor(np.minimum(np.minimum(a, b), c)).astype(int)
        x1, y1 = np.ceil(np.maximum(np.maximum(a, b), c)).astype(int)
        x0, y0 = max(x0, 0), max(y0, 0)
        x1, y1 = min(x1, T - 1), min(y1, T - 1)
        if x1 < x0 or y1 < y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        px, py = gx.ravel().astype(float), gy.ravel().astype(float)
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-12:
            continue
        w0 = ((b[1] - c[1]) * (px - c[0]) + (c[0] - b[0]) * (py - c[1])) / den
        w1 = ((c[1] - a[1]) * (px - c[0]) + (a[0] - c[0]) * (py - c[1])) / den
        w2 = 1 - w0 - w1
        ok = (w0 >= -0.02) & (w1 >= -0.02) & (w2 >= -0.02)
        if not ok.any():
            continue
        pix.append((gy.ravel()[ok] * T + gx.ravel()[ok]))
        w_all.append(np.stack([w0[ok], w1[ok], w2[ok]], 1))
        tri_all.append(np.full(ok.sum(), t))
    pix = np.concatenate(pix)
    w = np.clip(np.concatenate(w_all), 0, 1)
    w /= w.sum(1, keepdims=True)
    tri = np.concatenate(tri_all)
    vv = verts[tri]
    pos = (datos["pos"][vv] * w[:, :, None]).sum(1)
    nor = (datos["nor"][vv] * w[:, :, None]).sum(1)
    nor /= np.maximum(1e-9, np.linalg.norm(nor, axis=1))[:, None]
    reg = datos["reg"][vv[np.arange(len(vv)), w.argmax(1)]]
    return pix, pos, nor, reg


def _caja(x, z, cx, cz, hx, hz):
    return (np.abs(x - cx) < hx) & (np.abs(z - cz) < hz)


def _borde_caja(x, z, cx, cz, hx, hz, e):
    dentro = _caja(x, z, cx, cz, hx, hz)
    return dentro & ~_caja(x, z, cx, cz, hx - e, hz - e)


def _siete_seg(x, z, cx, cz, alto, digito):
    """Máscara de un dígito de 7 segmentos (para el número de la camiseta/short)."""
    segs = {"0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc", "5": "afgcd", "6": "afgedc",
            "7": "abc", "8": "abcdefg", "9": "abcfgd"}[digito]
    a, g = alto / 2, alto * 0.13
    w = alto * 0.32
    m = np.zeros_like(x, dtype=bool)
    rect = {"a": (0, a - g / 2, w, g / 2), "g": (0, 0, w, g / 2), "d": (0, -a + g / 2, w, g / 2),
            "f": (-w + g / 2, a / 2, g / 2, a / 2), "b": (w - g / 2, a / 2, g / 2, a / 2),
            "e": (-w + g / 2, -a / 2, g / 2, a / 2), "c": (w - g / 2, -a / 2, g / 2, a / 2)}
    for s in segs:
        ox, oz, hx, hz = rect[s]
        m |= _caja(x, z, cx + ox, cz + oz, hx, hz)
    return m


def _tres_rayas(pie, y, z, nor):
    """Tres rayas anchas sobre el empeine (como las zapatillas de las láminas)."""
    banda = (z > 0.035) & (z < 0.075) & (y < -0.02) & (y > -0.085) & (nor[:, 2] > 0.35)
    fase = ((y + 0.02) / -0.065 * 3.0) % 1.0
    return pie & banda & (fase > 0.15) & (fase < 0.55)


def _colorear(estilo: str, pos, nor, reg, colores: dict, femenino: bool):
    """Color por texel según el estilo (las láminas del dueño: Urbano, Deportivo, Táctico, Elegante)."""
    e = {**ESTILOS[estilo], **{k: tuple(v) for k, v in (colores or {}).items()}}
    x, y, z = pos[:, 0], pos[:, 1], pos[:, 2]
    ax = np.abs(x)
    R = {n: reg == i for i, n in enumerate(REGIONES)}
    col = np.tile(np.array(BLANCO), (len(x), 1))

    def pintar(mask, c):
        col[mask] = c

    frente = nor[:, 1] < -0.35
    atras = nor[:, 1] > 0.35
    costado = (np.abs(nor[:, 0]) > 0.55) & (np.sign(nor[:, 0]) == np.sign(x))
    larga = e.get("manga") == "larga"
    fin_manga = 0.355 if larga else 0.192
    cintura = 0.455
    tobillo = 0.125 if estilo == "tactico" else 0.088
    torso = R["torso"] & (z > cintura - 0.003) & ~((z > 0.643) & (ax < 0.034))
    manga = (R["brazo"] | (R["antebrazo"] & larga) | (R["torso"] & (ax > 0.05))) & (ax < fin_manga) & (z > 0.55)
    remera = torso | manga
    pantalon = (R["pierna"] | (R["torso"] & (z <= cintura))) & (z > tobillo)
    pie = R["pie"] | ((R["pierna"]) & (z <= tobillo))
    pintar(remera, e["remera"])
    pintar(pantalon, e["pantalon"])
    pintar(pie, e["zapato"])
    pintar(pie & (z < 0.017), e["suela"])

    if estilo == "urbano":
        pintar(manga & (ax > fin_manga - 0.014), e["detalle"])                       # puño de la manga
        pintar(torso & (z > 0.634) & (ax < 0.05), e["detalle"])                       # cuello
        pintar((R["torso"] | R["pierna"]) & (z > cintura - 0.012) & (z < cintura + 0.004), e["detalle"])   # cinturón
        bolsillo = R["pierna"] & costado & _caja(y, z, 0.012, 0.335, 0.026, 0.036)
        pintar(bolsillo, e["detalle"])
        pintar(_tres_rayas(pie, y, z, nor), e["suela"])
    elif estilo == "deportivo":
        pintar(R["torso"] & (z > cintura) & (ax > 0.046) & (ax < 0.056) & (z < 0.63), e["detalle"])   # franjas
        pintar(manga & (ax > fin_manga - 0.012), e["detalle"])
        v = frente & torso & (z > 0.595) & (np.abs(ax - (z - 0.595) * 0.9) < 0.0045)
        pintar(v, e["detalle"])
        pintar(torso & (z > 0.637) & (ax < 0.048), e["detalle"])
        medias = R["pierna"] & (z < 0.30) & (z > tobillo)
        pintar(medias, e["medias"])
        pintar(medias & (((z > 0.205) & (z < 0.218)) | ((z > 0.228) & (z < 0.241))), e["remera"])
        pintar(R["pierna"] & costado & (z > 0.30) & (np.abs(y - 0.012) < 0.006), e["detalle"])
        num = R["pierna"] & frente & (x > 0) & (_siete_seg(x, z, 0.036, 0.322, 0.04, "1")
                                              | _siete_seg(x, z, 0.06, 0.322, 0.04, "0"))
        pintar(num, e["detalle"])
        pintar(pie & (y < -0.098) & (z > 0.017), BLANCO)
        pintar(_tres_rayas(pie, y, z, nor), BLANCO)
    elif estilo == "tactico":
        pecho = 0.60 if femenino else 0.61
        chaleco = R["torso"] & (z > cintura + 0.012) & (z < 0.628) & (ax < 0.064)
        pintar(chaleco, e["chaleco"])
        # bolsillos del chaleco: dos filas de tres al frente
        for fila, cz in enumerate((0.505, 0.548)):
            for cx in (-0.03, 0.0, 0.03):
                b = chaleco & frente & _caja(x, z, cx, cz, 0.0125, 0.018)
                pintar(b, e["chaleco"])
                pintar(chaleco & frente & _borde_caja(x, z, cx, cz, 0.0125, 0.018, 0.0022), e["detalle"])
                pintar(chaleco & frente & _caja(x, z, cx, cz + 0.013, 0.0125, 0.0018), e["detalle"])
        pintar(chaleco & frente & (z > pecho) & (z < pecho + 0.003), e["detalle"])
        tirantes = R["torso"] & (z > 0.585) & (np.abs(ax - 0.04) < 0.008)
        pintar(tirantes, e["cinturon"])
        cint = (R["torso"] | R["pierna"]) & (z > cintura - 0.006) & (z < cintura + 0.012)
        pintar(cint, e["cinturon"])
        pintar(cint & frente & (ax < 0.011) & (z > cintura - 0.003) & (z < cintura + 0.009), e["hebilla"])
        pintar(cint & frente & (ax < 0.006) & (z > cintura) & (z < cintura + 0.006), e["cinturon"])
        bols = R["pierna"] & costado & _caja(y, z, 0.012, 0.33, 0.028, 0.035)
        pintar(bols, e["pantalon"])
        pintar(R["pierna"] & costado & (_borde_caja(y, z, 0.012, 0.33, 0.028, 0.035, 0.003)
                                         | _caja(y, z, 0.012, 0.358, 0.028, 0.003)), e["detalle"])
        xr = np.abs(ax - 0.05)
        rod = R["pierna"] & (nor[:, 1] < -0.15) & (((z - 0.245) / 0.03) ** 2 + (xr / 0.03) ** 2 < 1)
        pintar(rod, e["rodillera"])
        bota = pie | (R["pierna"] & (z <= tobillo))
        pintar(bota, e["zapato"])
        pintar(bota & (z < 0.017), e["suela"])
        cord = bota & frente & (z > 0.03) & (z < tobillo - 0.006) & (np.abs(ax - 0.055) < 0.014) & ((z * 110) % 1.0 < 0.35)
        pintar(cord, e["cordones"])
        pintar(R["pierna"] & (z > tobillo - 0.004) & (z < tobillo + 0.002), e["detalle"])
    elif estilo == "elegante":
        camisa = frente & torso & (z > 0.53) & (ax < (z - 0.53) * 0.36)
        pintar(camisa, e["camisa"])
        corbata = camisa & (ax < 0.0065 + (0.62 - z).clip(0) * 0.03) & (z < 0.628)
        pintar(corbata, e["corbata"])
        solapa = frente & torso & (z > 0.50) & (np.abs(ax - (z - 0.53) * 0.36) < 0.0016)
        pintar(solapa & (z > 0.53), e["detalle"])
        pintar(frente & torso & (z > 0.495) & (z < 0.53) & (np.abs(ax - 0.0) < 0.0014), e["detalle"])
        bol = frente & torso & (z > 0.485) & (z < 0.4885) & (ax > 0.025) & (ax < 0.05)
        pintar(bol, e["detalle"])
        pintar(frente & torso & (z > 0.585) & (z < 0.588) & (x > 0.028) & (x < 0.045), e["detalle"])
        pintar(manga & (ax > fin_manga - 0.004), e["detalle"])
        pintar(_tres_rayas(pie, y, z, nor), (0.55, 0.55, 0.55))
    return col


def _dilatar(img, lleno, pasos=6):
    T = img.shape[0]
    for _ in range(pasos):
        vacio = ~lleno
        if not vacio.any():
            break
        acc = np.zeros_like(img)
        cnt = np.zeros((T, T))
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            sh = np.roll(np.roll(img, dy, 0), dx, 1)
            sl = np.roll(np.roll(lleno, dy, 0), dx, 1)
            acc[sl] += sh[sl]
            cnt[sl] += 1
        nuevo = vacio & (cnt > 0)
        img[nuevo] = acc[nuevo] / cnt[nuevo][:, None]
        lleno = lleno | nuevo
    return img


def textura_vestuario(malla, raiz, modelo: str, estilo: str, colores: dict | None, T: int = 2048) -> bpy.types.Image:
    """Pinta (o lee de caché) la textura del estilo para este modelo y devuelve la imagen de Blender."""
    clave = hashlib.sha1(repr((REFS[modelo], estilo, sorted((colores or {}).items()), T, 4)).encode()).hexdigest()[:16]
    carpeta = config.SALIDA / "cache_stickman"
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / f"{modelo.split(':')[1]}_{estilo}_{clave}.png"
    if not ruta.exists():
        datos = datos_reposo(malla, raiz)
        datos = {**datos, "pos": normalizar(datos, modelo.endswith("femenino"))}
        pix, pos, nor, reg = _rasterizar(malla, datos, T)
        col = _colorear(estilo, pos, nor, reg, colores, modelo.endswith("femenino"))
        img = np.zeros((T * T, 3))
        lleno = np.zeros(T * T, dtype=bool)
        img[pix] = col
        lleno[pix] = True
        img = _dilatar(img.reshape(T, T, 3), lleno.reshape(T, T))
        rgba = np.concatenate([img, np.ones((T, T, 1))], 2).astype(np.float32)
        im = bpy.data.images.new(f"vest_tmp_{clave}", T, T, alpha=False, float_buffer=False)
        im.colorspace_settings.name = "Non-Color"         # ya son valores lineales; se guardan tal cual
        im.pixels.foreach_set(rgba.ravel())
        im.filepath_raw = str(ruta)
        im.file_format = "PNG"
        im.save()
        bpy.data.images.remove(im)
    im = bpy.data.images.load(str(ruta), check_existing=True)
    im.colorspace_settings.name = "Non-Color"
    return im


def vestir(pj: dict, modelo: str, vest: dict):
    """Reemplaza el material blanco del modelo por el del estilo pedido (el FBX original no se toca)."""
    malla, raiz = pj["malla"], pj["raiz"]
    estilo = vest.get("estilo", "urbano")
    im = textura_vestuario(malla, raiz, modelo, estilo, vest.get("colores"))
    mat = bpy.data.materials.new(f"vest_{pj['id']}_{estilo}")
    mat.use_nodes = True
    nt = mat.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    tx = nt.nodes.new("ShaderNodeTexImage")
    tx.image = im
    tx.interpolation = "Linear"
    nt.links.new(tx.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.55
    b.inputs["Metallic"].default_value = 0.0
    if "Specular IOR Level" in b.inputs:
        b.inputs["Specular IOR Level"].default_value = 0.35
    if "Coat Weight" in b.inputs:
        b.inputs["Coat Weight"].default_value = 0.08
    malla.data = malla.data.copy()                 # el prototipo importado no comparte el material nuevo
    malla.data.materials.clear()
    malla.data.materials.append(mat)
    return mat


# ------------------------------------------------------------------------------------------------- esfera de la cabeza
def esfera_cabeza(datos: dict) -> tuple[Vector, float]:
    """Centro y radio de la cabeza (ajuste de esfera por mínimos cuadrados a los vértices de la parte alta)."""
    z_cab = datos["hitos"]["Head"].z if "Head" in datos.get("hitos", {}) else 0.70
    p = datos["pos"][(datos["reg"] == 0) & (datos["pos"][:, 2] > z_cab)]
    A = np.c_[2 * p, np.ones(len(p))]
    f = (p ** 2).sum(1)
    sol, *_ = np.linalg.lstsq(A, f, rcond=None)
    c = sol[:3]
    r = math.sqrt(sol[3] + (c ** 2).sum())
    return Vector(c), r


class Cabeza:
    """Marco de la cara: u hacia la derecha de quien mira (izquierda del personaje, +X), v hacia arriba (radianes).
    Los puntos se apoyan sobre la superficie REAL de la cabeza (rayo desde el centro contra la malla): la cabeza no es
    una esfera perfecta y con una esfera ajustada la boca quedaba tapada por la mejilla."""
    def __init__(self, centro: Vector, radio: float, bvh=None):
        self.c, self.r, self.bvh = centro, radio, bvh

    def punto(self, u: float, v: float, sobre: float = 0.0) -> Vector:
        d = Vector((math.sin(u) * math.cos(v), -math.cos(u) * math.cos(v), math.sin(v)))
        dist = self.r
        if self.bvh is not None:
            hit, _n, _i, dd = self.bvh.ray_cast(self.c, d, self.r * 2.5)
            if hit is not None:
                dist = dd
        return self.c + d * (dist + self.r * sobre)


def bvh_cabeza(malla, datos: dict):
    """Árbol de búsqueda de la malla en reposo (unidades del modelo) para apoyar la cara y el pelo sobre la cabeza."""
    from mathutils.bvhtree import BVHTree
    caras = [tuple(p.vertices) for p in malla.data.polygons]
    return BVHTree.FromPolygons([tuple(v) for v in datos["pos"]], caras)


def _a_hueso(obj, pj: dict, hueso: str = "mixamorig:Head"):
    """Cuelga `obj` (vértices en espacio de la armadura) del hueso sin moverlo: sigue la cabeza cuadro a cuadro."""
    arm = pj["armadura"]
    b = arm.data.bones[hueso]
    obj.parent = arm
    obj.parent_type = "BONE"
    obj.parent_bone = hueso
    obj.matrix_parent_inverse = (b.matrix_local @ Matrix.Translation((0, b.length, 0))).inverted()
    obj.matrix_basis = Matrix.Identity(4)


def _modelo_a_armadura(pj: dict) -> Matrix:
    return (pj["raiz"].matrix_world.inverted() @ pj["armadura"].matrix_world).inverted()


def _malla_con_formas(nombre: str, pj: dict, cab: Cabeza, formas: dict, caras, sobre, mats, mat_idx, col):
    """Malla cuyos vértices salen de puntos 2D (u, v) proyectados sobre la cabeza; cada forma es una shape key."""
    M = _modelo_a_armadura(pj)
    base = formas["base"]

    def proyectar(pts):
        return [M @ cab.punto(u, v, s) for (u, v), s in zip(pts, sobre)]
    me = bpy.data.meshes.new(nombre)
    me.from_pydata([tuple(p) for p in proyectar(base)], [], caras)
    for i, idx in enumerate(mat_idx):
        me.polygons[i].material_index = idx
    for m in mats:
        me.materials.append(m)
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(nombre, me)
    col.objects.link(ob)
    ob.visible_shadow = False
    ob.shape_key_add(name="Basis")
    for k, pts in formas.items():
        if k == "base":
            continue
        sk = ob.shape_key_add(name=k)
        for i, p in enumerate(proyectar(pts)):
            sk.data[i].co = p
    _a_hueso(ob, pj)
    return ob


def _abanico(n_borde: int):
    """Triángulos de un abanico: vértice 0 = centro, 1..n = borde."""
    return [(0, 1 + i, 1 + (i + 1) % n_borde) for i in range(n_borde)]


# ------------------------------------------------------------------------------------------------- partes de la cara
def _ojo(lado: int, P: dict):
    """Formas 2D del ojo (óvalo negro con brillo). lado = +1 ojo de la derecha de la imagen (izq. del personaje)."""
    N = 28
    cx, cy, rx, ry = lado * P["ojo_sep"], P["ojo_alto"], P["ojo_rx"], P["ojo_ry"]
    ts = [2 * math.pi * i / N for i in range(N)]

    def ovalo(sx=1.0, sy=1.0, dx=0.0, dy=0.0, techo=None, piso=None):
        pts = [(cx + dx, cy + dy)]
        for t in ts:
            x, y = cx + dx + rx * sx * math.cos(t), cy + dy + ry * sy * math.sin(t)
            if techo is not None:
                y = min(y, cy + dy + techo * ry)
            if piso is not None:
                y = max(y, cy + dy + piso * ry)
            pts.append((x, y))
        return pts

    def arco(curva, grosor, dy=0.0):
        pts = [(cx, cy + dy + curva * ry)]
        for t in ts:
            k = math.cos(t)
            pts.append((cx + rx * 1.05 * k, cy + dy + curva * ry * (1 - k * k) + grosor * ry * math.sin(t)))
        return pts
    hx, hy, hr = cx + rx * 0.32, cy + ry * 0.38, rx * 0.30
    M = 10
    hs = [2 * math.pi * i / M for i in range(M)]

    def brillo(dx=0.0, dy=0.0, k=1.0):
        return [(hx + dx, hy + dy)] + [(hx + dx + hr * k * math.cos(t), hy + dy + hr * k * math.sin(t)) for t in hs]
    g = P["mirada"]
    oculto = [(cx, cy - 0.3 * ry)] * (M + 1)
    formas = {
        "base": ovalo() + brillo(),
        "cerrado": arco(-0.35, 0.09, -0.15 * ry) + oculto,
        "feliz": arco(0.45, 0.10, -0.3 * ry) + [(cx, cy)] * (M + 1),
        "entrecerrado": ovalo(techo=0.15) + brillo(dy=-0.42 * ry, k=0.7),
        "abajo_parpado": ovalo(piso=-0.2) + brillo(),
        "grande": ovalo(1.22, 1.22) + brillo(0.04 * rx, 0.06 * ry, 1.15),
        "mirar_der": ovalo(dx=g * rx) + brillo(dx=g * rx),
        "mirar_izq": ovalo(dx=-g * rx) + brillo(dx=-g * rx),
        "mirar_arriba": ovalo(dy=0.5 * g * ry) + brillo(dy=0.5 * g * ry),
        "mirar_abajo": ovalo(dy=-0.6 * g * ry) + brillo(dy=-0.6 * g * ry),
    }
    caras = _abanico(N) + [(N + 1, N + 2 + i, N + 2 + (i + 1) % M) for i in range(M)]
    sobre = [P["sobre"]] * (N + 1) + [P["sobre"] * 1.6] * (M + 1)
    mat_idx = [0] * N + [1] * M
    if P.get("pestanas"):
        # índices del contorno cerca de 25° y 55° hacia afuera (el lado de afuera depende del ojo)
        ks = [round(N * (a if lado > 0 else 0.5 - a)) % N for a in (0.07, 0.15)]
        base = len(formas["base"])
        for nombre_f, pts in formas.items():
            cen = Vector(pts[0])
            extra = []
            for k in ks:
                a1, a2 = Vector(pts[1 + k]), Vector(pts[1 + (k + 1) % N])
                mid = (a1 + a2) / 2
                d = mid - cen
                if d.length < 1e-6:
                    d = Vector((lado, 0.3))
                tip = mid + d.normalized() * rx * 0.55 + Vector((lado * rx * 0.15, ry * 0.05))
                extra += [tuple(a1), tuple(a2), tuple(tip)]
            pts.extend(extra)
        for j in range(len(ks)):
            caras.append((base + 3 * j, base + 3 * j + 1, base + 3 * j + 2))
            mat_idx.append(0)
        sobre += [P["sobre"]] * (3 * len(ks))
    return formas, caras, sobre, mat_idx


def _ceja(lado: int, P: dict):
    """Ceja gruesa y redondeada. Con lado = +1 queda a la derecha de la imagen; «interior» es el extremo hacia la nariz."""
    K_ = 9
    cx, cy, w, gro = lado * P["ojo_sep"], P["ceja_alto"], P["ceja_w"], P["ceja_g"]

    def tira(arco=0.25, dy=0.0, gir=0.0, esc=1.0):
        # gir > 0: el extremo interior baja (enojo); < 0: sube (preocupación)
        sup, inf = [], []
        for i in range(K_):
            s = -1 + 2 * i / (K_ - 1)                  # −1 = interior (nariz), +1 = exterior
            x = cx + lado * s * w * esc
            yc = cy + dy + arco * w * (1 - s * s) * 0.35 - gir * w * 0.45 * (-s)
            g = gro * (0.55 + 0.45 * (1 - abs(s) ** 1.6)) * (1.08 if s < 0 else 1.0)
            sup.append((x, yc + g / 2))
            inf.append((x, yc - g / 2))
        return sup + inf
    formas = {"base": tira(), "arriba": tira(0.4, 0.07), "enojo": tira(0.05, -0.012, 0.75),
              "preocupado": tira(0.15, 0.03, -0.7), "plana": tira(0.0, -0.01)}
    caras = []
    for i in range(K_ - 1):
        caras.append((i, i + 1, K_ + i + 1, K_ + i))
    return formas, caras, [P["sobre"]] * (2 * K_), [0] * len(caras)


def _boca(P: dict):
    """Boca 2D: contorno superior e inferior con las esquinas compartidas; cada gesto y vocal es una forma clave."""
    N = 13
    y0, W = P["boca_alto"], P["boca_w"]
    ts = [-1 + 2 * i / (N - 1) for i in range(N)]

    def forma(sup, inf, ancho=1.0, dy=0.0, ladeo=0.0):
        up, lo = [], []
        for t in ts:
            x = t * W * ancho
            tilt = ladeo * t * W
            up.append((x, y0 + dy + tilt + sup(t)))
            lo.append((x, y0 + dy + tilt + inf(t)))
        return up + lo
    g = 0.030                                                     # grosor de la línea con la boca cerrada
    formas = {
        "base": forma(lambda t: 0.006 * (1 - t * t), lambda t: 0.006 * (1 - t * t) - g * (1 - t * t) ** 0.5),
        "sonrisa": forma(lambda t: -0.06 * (1 - t * t), lambda t: -0.06 * (1 - t * t) - g * (1 - t * t) ** 0.5, 1.05, 0.02),
        "sonrisa_abierta": forma(lambda t: -0.025 * (1 - t * t), lambda t: -0.19 * (1 - t * t) ** 0.85, 1.0, 0.03),
        "picara": forma(lambda t: -0.035 * (1 - t * t) + 0.02 * t, lambda t: -0.035 * (1 - t * t) + 0.02 * t - g * (1 - t * t) ** 0.5,
                        0.9, 0.0, 0.16),
        "triste": forma(lambda t: 0.06 * (1 - t * t), lambda t: 0.06 * (1 - t * t) - g * (1 - t * t) ** 0.5, 0.85, -0.03),
        "A": forma(lambda t: 0.03 * (1 - t * t), lambda t: -0.16 * (1 - t * t) ** 0.75, 0.82),
        "E": forma(lambda t: 0.015 * (1 - t * t), lambda t: -0.075 * (1 - t * t) ** 0.8, 1.0),
        "O": forma(lambda t: 0.07 * (1 - t * t) ** 0.5, lambda t: -0.10 * (1 - t * t) ** 0.5, 0.42),
        "M": forma(lambda t: 0.0, lambda t: -0.008 * (1 - t * t) ** 0.5, 0.8),
    }
    caras = [(i, i + 1, N + i + 1, N + i) for i in range(N - 1)]
    return formas, caras, [P["sobre"]] * (2 * N), [0] * len(caras)


def _rubor(lado: int, P: dict):
    N = 14
    cx, cy = lado * (P["ojo_sep"] + 0.10), P["ojo_alto"] - 0.27
    rx, ry = 0.12, 0.055
    cent = [(cx, cy)] * (N + 1)
    lleno = [(cx, cy)] + [(cx + rx * math.cos(2 * math.pi * i / N), cy + ry * math.sin(2 * math.pi * i / N)) for i in range(N)]
    return {"base": cent, "visible": lleno}, _abanico(N), [P["sobre"] * 0.6] * (N + 1), [0] * N


PROPORCIONES = {
    "nico": {"ojo_sep": 0.31, "ojo_alto": 0.06, "ojo_rx": 0.10, "ojo_ry": 0.175, "mirada": 0.35, "ceja_alto": 0.34,
             "ceja_w": 0.15, "ceja_g": 0.06, "boca_alto": -0.37, "boca_w": 0.22, "sobre": 0.012},
    "luna": {"ojo_sep": 0.30, "ojo_alto": 0.05, "ojo_rx": 0.105, "ojo_ry": 0.19, "mirada": 0.35, "ceja_alto": 0.33,
             "ceja_w": 0.14, "ceja_g": 0.042, "boca_alto": -0.37, "boca_w": 0.19, "sobre": 0.012, "pestanas": True},
}


def armar_cara(pj: dict, cab: Cabeza, tipo: str = "nico", color_cejas=(0.03, 0.02, 0.015), col=None) -> dict:
    col = col or pj["raiz"].users_collection[0]
    P = PROPORCIONES[tipo]
    negro = K.material(f"cara_negro_{pj['id']}", (0.012, 0.012, 0.014), 0.45)
    brillo = K.material(f"cara_brillo_{pj['id']}", (0.95, 0.95, 0.95), 0.3, emision=(1, 1, 1), fuerza=0.6)
    boca_m = K.material(f"cara_boca_{pj['id']}", (0.09, 0.012, 0.018), 0.5)
    ceja_m = K.material(f"cara_ceja_{pj['id']}", tuple(color_cejas), 0.6)
    rubor_m = K.material(f"cara_rubor_{pj['id']}", (0.9, 0.36, 0.42), 0.6)
    partes = {}
    for lado, nom in ((1, "izq"), (-1, "der")):            # izq/der del PERSONAJE (+X = su izquierda)
        f, c, s, mi = _ojo(lado, P)
        partes[f"ojo_{nom}"] = _malla_con_formas(f"CARA_{pj['id']}_ojo_{nom}", pj, cab, f, c, s, [negro, brillo], mi, col)
        f, c, s, mi = _ceja(lado, P)
        partes[f"ceja_{nom}"] = _malla_con_formas(f"CARA_{pj['id']}_ceja_{nom}", pj, cab, f, c, s, [ceja_m], mi, col)
        f, c, s, mi = _rubor(lado, P)
        partes[f"rubor_{nom}"] = _malla_con_formas(f"CARA_{pj['id']}_rubor_{nom}", pj, cab, f, c, s, [rubor_m], mi, col)
    f, c, s, mi = _boca(P)
    partes["boca"] = _malla_con_formas(f"CARA_{pj['id']}_boca", pj, cab, f, c, s, [boca_m], mi, col)
    return partes


# ------------------------------------------------------------------------------------------------- pelo
def _pelo_malla(nombre, pj, cab: Cabeza, estilo: str, col, mat):
    """Casco de pelo: esfera cortada por una línea de nacimiento que depende del ángulo alrededor de la cabeza; las
    filas que quedan debajo se aplastan sobre la línea y forman las puntas del flequillo."""
    M = _modelo_a_armadura(pj)
    NU, NV = 72, 26
    rnd = random.Random(sum(map(ord, nombre)))
    picos = 0

    def nacimiento(az):
        a = abs(az)
        if estilo == "kingsman":
            return _nacimiento_kingsman(az)
        tabla = {"puntas": [(0, 0.62), (0.9, 0.50), (1.35, 0.22), (1.9, 0.02), (math.pi, -0.18)],
                 "peinado": [(0, 0.46), (0.9, 0.36), (1.35, 0.08), (1.9, -0.1), (math.pi, -0.28)],
                 "corto": [(0, 0.55), (0.9, 0.42), (1.35, 0.15), (1.9, 0.0), (math.pi, -0.18)],
                 "luna": [(0, 0.40), (0.9, 0.24), (1.35, -0.05), (1.9, -0.35), (math.pi, -0.55)]}[estilo]
        for (a0, b0), (a1, b1) in zip(tabla, tabla[1:]):
            if a <= a1:
                k = (a - a0) / (a1 - a0)
                b = b0 + (b1 - b0) * (k * k * (3 - 2 * k))
                break
        if estilo == "peinado":
            b += 0.10 * math.sin(az) if a < 1.2 else 0.0            # raya al costado
        if estilo == "luna" and a < 1.1:
            b += 0.16 * max(0.0, math.sin(az + 0.3)) - 0.05         # flequillo de costado
        if picos and a < 2.2:
            fase = (az / (2 * math.pi)) * picos * 2.6 + 0.5
            tri = abs((fase % 1.0) - 0.5) * 2                        # 0 en la punta, 1 en el hueco
            tri = tri ** 0.7
            prof = 0.34 if a < 1.3 else 0.22
            b += prof * tri - prof * 0.55
        return b
    verts, caras = [], []
    for j in range(NV + 1):
        s = j / NV
        for i in range(NU):
            az = -math.pi + 2 * math.pi * i / NU
            b = nacimiento(az)
            v = b + (math.pi / 2 - b) * (s ** 0.9)
            v = min(v, math.pi / 2 - 1e-3)
            esp = 0.05 + 0.02 * (1 - s)
            if estilo == "kingsman":
                # volumen peinado hacia la derecha del personaje (lejos de la raya) y jopo adelante
                vol = min(1.0, max(0.0, (0.85 - az) / 1.9))
                vol = vol * vol * (3 - 2 * vol)
                jopo = max(0.0, 1 - abs(az) / 0.75) * max(0.0, 1 - s / 0.45)
                esp = 0.035 + 0.11 * vol * math.sin(math.pi * min(1.0, s * 1.15) ** 0.8) + 0.12 * jopo
            if estilo == "puntas":
                esp += 0.03 * max(0.0, math.sin(4 * az + 1.0) * math.sin(5 * v)) ** 2 + 0.006 * rnd.random()
            if j == 0:
                esp = 0.02
            verts.append(M @ cab.punto(az, v, esp))
    for j in range(NV):
        for i in range(NU):
            a, b = j * NU + i, j * NU + (i + 1) % NU
            caras.append((a, b, b + NU, a + NU))
    tope = len(verts)
    verts.append(M @ cab.punto(0.0, math.pi / 2, 0.11))
    for i in range(NU):
        caras.append((NV * NU + i, NV * NU + (i + 1) % NU, tope))
    me = bpy.data.meshes.new(nombre)
    me.from_pydata([tuple(p) for p in verts], [], caras)
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(mat)
    ob = bpy.data.objects.new(nombre, me)
    col.objects.link(ob)
    so = ob.modifiers.new("grosor", "SOLIDIFY")
    so.thickness = cab.r * 0.05 * M.to_scale()[0]
    so.offset = -1
    sub = ob.modifiers.new("suave", "SUBSURF")
    sub.levels = sub.render_levels = 1
    _a_hueso(ob, pj)
    return ob


def _nacimiento_kingsman(az: float) -> float:
    """Línea de nacimiento del peinado al costado: la raya va del lado izquierdo del personaje (az > 0)."""
    if az >= 0:
        tabla = [(0.0, 0.50), (0.55, 0.58), (0.85, 0.66), (1.6, 0.68), (2.4, 0.62), (math.pi, 0.55)]
    else:
        tabla = [(0.0, 0.50), (0.9, 0.42), (1.6, 0.40), (2.4, 0.45), (math.pi, 0.55)]
    a = abs(az)
    for (a0, b0), (a1, b1) in zip(tabla, tabla[1:]):
        if a <= a1:
            k = (a - a0) / (a1 - a0)
            return b0 + (b1 - b0) * (k * k * (3 - 2 * k))
    return tabla[-1][1]


def _degrade(nombre, pj, cab: Cabeza, col, color, estilo: str):
    """Degradé de costados y nuca: pelo cortísimo que se aclara hacia abajo hasta la piel (vértices con «fade» 0→1 y
    textura de pelo al ras); en el «kingsman», una línea afeitada debajo de la raya."""
    M = _modelo_a_armadura(pj)
    NU, NV = 144, 26
    frente = 0.92

    def bajo(u):
        a = abs(u)
        if a < 1.57:
            k = (a - frente) / (1.57 - frente)
            return 0.15 + (-0.12 - 0.15) * k
        k = (a - 1.57) / (math.pi - 1.57)
        return -0.12 + (-0.42 + 0.12) * k

    def alto(u):
        if estilo == "kingsman":
            return _nacimiento_kingsman(u) + 0.05
        return 1.25 if estilo == "mohicano" else 1.05
    pico = {"kingsman": 1.0, "mohicano": 0.85, "cresta": 0.95}.get(estilo, 0.9)
    verts, alfas, caras = [], [], []
    us = [-math.pi + 2 * math.pi * i / NU for i in range(NU)]
    for j in range(NV + 1):
        t = j / NV
        for u in us:
            v0, v1 = bajo(u) if abs(u) >= frente else 0.15, alto(u)
            v = v0 + (v1 - v0) * t
            a = min(1.0, t * 2.3) ** 0.7 * pico
            if estilo == "kingsman" and 0.55 < u < 2.6 and abs(v - (_nacimiento_kingsman(u) - 0.04)) < 0.03:
                a = 0.0                                     # la línea afeitada (estilo Kingsman)
            verts.append(M @ cab.punto(u, v, 0.006))
            alfas.append(a)
    for j in range(NV):
        for i in range(NU):
            u = us[i]
            u2 = us[(i + 1) % NU]
            if abs(u) < frente or abs(u2) < frente or (i == NU - 1):
                continue
            a_, b_ = j * NU + i, j * NU + (i + 1) % NU
            caras.append((a_, b_, b_ + NU, a_ + NU))
    me = bpy.data.meshes.new(nombre)
    me.from_pydata([tuple(p) for p in verts], [], caras)
    for p in me.polygons:
        p.use_smooth = True
    at = me.color_attributes.new("fade", "FLOAT_COLOR", "POINT")
    at.data.foreach_set("color", [c for a in alfas for c in (a, a, a, 1.0)])
    mat = bpy.data.materials.new(f"degrade_{pj['id']}")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.75
    vc = nt.nodes.new("ShaderNodeVertexColor")
    vc.layer_name = "fade"
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(vc.outputs["Color"], sep.inputs["Color"])
    tc = nt.nodes.new("ShaderNodeTexCoord")
    ruido = nt.nodes.new("ShaderNodeTexNoise")
    ruido.inputs["Scale"].default_value = 900.0
    ruido.inputs["Detail"].default_value = 2.0
    nt.links.new(tc.outputs["Object"], ruido.inputs["Vector"])
    rr = nt.nodes.new("ShaderNodeMapRange")
    rr.inputs["From Min"].default_value = 0.35
    rr.inputs["From Max"].default_value = 0.65
    rr.inputs["To Min"].default_value = 0.72
    nt.links.new(ruido.outputs["Fac"], rr.inputs["Value"])
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    nt.links.new(sep.outputs[0], mul.inputs[0])
    nt.links.new(rr.outputs["Result"], mul.inputs[1])
    nt.links.new(mul.outputs[0], bsdf.inputs["Alpha"])
    try:
        mat.surface_render_method = "DITHERED"
    except Exception:
        pass
    mat.diffuse_color = (*color, 1.0)
    me.materials.append(mat)
    ob = bpy.data.objects.new(nombre, me)
    col.objects.link(ob)
    ob.visible_shadow = False
    _a_hueso(ob, pj)
    return ob


MECHONES = {
    # (az raíz, v raíz, az punta, v punta, salida de la punta, grosor) en radianes y fracciones del radio
    "puntas": ([(a, 0.95, a * 1.08, 0.30 + 0.06 * abs(a), 0.10, 0.20) for a in (-0.9, -0.6, -0.3, 0.0, 0.3, 0.6, 0.9)]
               + [(sg * a, 0.75, sg * (a + 0.12), 0.0, 0.16, 0.22) for sg in (1, -1) for a in (1.3, 1.65)]
               + [(sg * a, 0.65, sg * (a + 0.1), -0.22, 0.17, 0.24) for sg in (1, -1) for a in (2.1, 2.55)]
               + [(math.pi, 0.6, math.pi, -0.30, 0.17, 0.24)]
               + [(sg * a, 1.15, sg * a * 1.15, 0.85, 0.42, 0.22) for sg in (1, -1) for a in (0.5, 1.5, 2.5)]
               + [(math.pi, 1.1, math.pi, 0.75, 0.42, 0.22)]),
    "luna": ([(-0.9 + 0.3 * i, 1.0, -0.6 + 0.36 * i, 0.32 - 0.07 * i, 0.09, 0.22) for i in range(6)]
             + [(sg * a, 0.7, sg * (a + 0.05), -0.42, 0.12, 0.26) for sg in (1, -1) for a in (1.35, 1.75)]),
    "peinado": [],
    # peinado al costado tipo Kingsman: mechones peinados desde la raya (izquierda) hacia el otro lado + jopo
    "kingsman": ([(0.80, v, -1.15, 0.36 + 0.42 * (v - 0.62), 0.16, 0.10) for v in (0.64, 0.80, 0.96, 1.12, 1.28, 1.42)]
                 + [(0.55, 0.56, -0.55, 0.70, 0.24, 0.13), (0.62, 0.60, -0.85, 0.62, 0.21, 0.11)]),
    # mohicano: tira central de puntas altas de la frente a la nuca, sobre una base gruesa
    "mohicano": ([(0.0, 0.55, 0.0, 1.55, 0.10, 0.30), (math.pi, 1.55, math.pi, 0.25, 0.10, 0.30)]
                 + [(0.0, v, 0.0, v + 0.10, 0.48 + 0.25 * min(1.0, v - 0.5), 0.24) for v in (0.6, 0.8, 1.0, 1.2, 1.4)]
                 + [(math.pi, v, math.pi, v - 0.06, 0.30 + 0.3 * (v - 0.3), 0.22) for v in (1.35, 1.1, 0.85, 0.6, 0.38)]),
    # cresta (faux hawk): puntas que convergen al centro, más altas adelante
    "cresta": ([(sg * 0.34, v, sg * 0.05, v + 0.22, 0.52 - 0.1 * (v - 0.6), 0.13) for v in (0.6, 0.8, 1.0, 1.2, 1.4)
                for sg in (1, -1)]
               + [(0.0, v, 0.0, v + 0.24, 0.62 - 0.12 * (v - 0.6), 0.15) for v in (0.6, 0.85, 1.1, 1.35)]
               + [(0.0, 0.55, 0.0, 1.5, 0.10, 0.28), (math.pi, 1.5, math.pi, 0.9, 0.09, 0.26)]),
}


def _mechones(nombre, pj, cab: Cabeza, estilo: str, col, mat):
    """Mechones afinados (curvas con grosor): flequillo en punta, costados, nuca y copetes de la coronilla."""
    lista = MECHONES.get(estilo) or []
    if not lista:
        return None
    M = _modelo_a_armadura(pj)
    esc = M.to_scale()[0]
    cu = bpy.data.curves.new(nombre, "CURVE")
    cu.dimensions = "3D"
    for (a0, v0, a1, v1, sale, gro) in lista:
        p0 = cab.punto(a0, v0, 0.03)
        p1 = cab.punto(a1, v1, sale)
        am, vm = (a0 + a1) / 2, (v0 + v1) / 2
        pm = cab.punto(am, vm, 0.09 + sale * 0.5)
        sp = cu.splines.new("BEZIER")
        sp.bezier_points.add(2)
        for bp, q, rad in zip(sp.bezier_points, (p0, pm, p1), (gro / 0.21, gro / 0.21 * 0.72, 0.0)):
            bp.co = M @ q
            bp.handle_left_type = bp.handle_right_type = "AUTO"
            bp.radius = rad
        sp.use_smooth = True
    cu.bevel_depth = cab.r * 0.21 * esc
    cu.bevel_resolution = 3
    cu.resolution_u = 8
    cu.use_fill_caps = True
    cu.materials.append(mat)
    ob = bpy.data.objects.new(nombre, cu)
    col.objects.link(ob)
    _a_hueso(ob, pj)
    return ob


def _cola(nombre, pj, cab: Cabeza, col, mat, mat_gomita):
    """Cola de caballo de Luna: tubo que sale de atrás de la cabeza, cae hacia la espalda y se afina."""
    M = _modelo_a_armadura(pj)
    r = cab.r
    raiz = cab.punto(math.pi, 0.15, 0.06)
    ctrl = [raiz, raiz + Vector((0, 0.5 * r, -0.17 * r)), raiz + Vector((0, 0.76 * r, -0.85 * r)),
            raiz + Vector((0, 0.72 * r, -1.6 * r)), raiz + Vector((0, 0.6 * r, -2.1 * r))]
    curva = bpy.data.curves.new(nombre, "CURVE")
    curva.dimensions = "3D"
    sp = curva.splines.new("BEZIER")
    sp.bezier_points.add(len(ctrl) - 1)
    for i, p in enumerate(ctrl):
        bp = sp.bezier_points[i]
        bp.co = M @ p
        bp.handle_left_type = bp.handle_right_type = "AUTO"
        bp.radius = max(0.12, 1.0 - 0.85 * (i / (len(ctrl) - 1)) ** 1.2)
    curva.bevel_depth = r * 0.33 * M.to_scale()[0]
    curva.bevel_resolution = 4
    curva.resolution_u = 10
    curva.use_fill_caps = True
    curva.materials.append(mat)
    ob = bpy.data.objects.new(nombre, curva)
    col.objects.link(ob)
    _a_hueso(ob, pj)
    # gomita
    gm = bpy.data.meshes.new(nombre + "_gomita")
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=r * 0.30 * M.to_scale()[0],
                          radius2=r * 0.30 * M.to_scale()[0], depth=r * 0.12 * M.to_scale()[0])
    bm.to_mesh(gm)
    bm.free()
    gm.materials.append(mat_gomita)
    g = bpy.data.objects.new(nombre + "_gomita", gm)
    col.objects.link(g)
    eje = (ctrl[1] - ctrl[0]).normalized()
    pos = M @ (ctrl[0] + (ctrl[1] - ctrl[0]) * 0.55)
    rot = (M.to_3x3() @ eje).to_track_quat("Z", "Y").to_matrix().to_4x4()
    g.data.transform(rot)
    g.data.transform(Matrix.Translation(pos))
    _a_hueso(g, pj)
    return [ob, g]


def peinar(pj: dict, cab: Cabeza, estilo: str, color, col=None) -> list:
    col = col or pj["raiz"].users_collection[0]
    mat = K.material(f"pelo_{pj['id']}", tuple(color), 0.42)
    b = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if b is not None and "Coat Weight" in b.inputs:
        b.inputs["Coat Weight"].default_value = 0.25
    obs = []
    if estilo not in ("mohicano", "cresta"):
        obs.append(_pelo_malla(f"PELO_{pj['id']}", pj, cab, estilo, col, mat))
    if estilo in ("kingsman", "mohicano", "cresta"):
        obs.append(_degrade(f"PELO_{pj['id']}_degrade", pj, cab, col, tuple(color), estilo))
    mech = _mechones(f"PELO_{pj['id']}_mechones", pj, cab, estilo, col, mat)
    if mech is not None:
        obs.append(mech)
    if estilo == "luna":
        obs += _cola(f"PELO_{pj['id']}_cola", pj, cab, col, mat, K.material(f"gomita_{pj['id']}", (0.02, 0.02, 0.02), 0.5))
    return obs


# ------------------------------------------------------------------------------------------------- actuación facial
EXPRESIONES = {
    "neutral": {},
    "sonrisa": {"boca:sonrisa": 1.0, "ojos:feliz": 0.15},
    "sonrisa_suave": {"boca:sonrisa": 0.55},
    "picara": {"boca:picara": 1.0, "ceja_izq:arriba": 0.9, "ceja_der:enojo": 0.25, "ojos:entrecerrado": 0.3},
    "confiado": {"boca:picara": 0.7, "cejas:arriba": 0.25, "ojos:entrecerrado": 0.2},
    "ironica": {"boca:picara": 0.55, "ceja_der:arriba": 1.0, "ceja_izq:plana": 0.6, "ojos:entrecerrado": 0.45},
    "incredula": {"ceja_der:arriba": 1.0, "ceja_izq:enojo": 0.45, "ojos:entrecerrado": 0.35, "boca:M": 0.8},
    "seria": {"cejas:enojo": 0.3, "boca:M": 0.6},
    "concentrada": {"cejas:enojo": 0.4, "ojos:entrecerrado": 0.2, "boca:M": 0.4},
    "enojo": {"cejas:enojo": 1.0, "boca:triste": 0.4, "ojos:entrecerrado": 0.2},
    "sorpresa": {"cejas:arriba": 1.0, "ojos:grande": 1.0, "boca:O": 0.7},
    "preocupada": {"cejas:preocupado": 1.0, "boca:triste": 0.55, "ojos:abajo_parpado": 0.2},
    "avergonzada": {"rubor": 1.0, "boca:sonrisa": 0.6, "cejas:preocupado": 0.35, "ojos:mirar_abajo": 0.6},
    "carinosa": {"rubor": 0.45, "boca:sonrisa": 0.7, "ojos:feliz": 0.35, "cejas:arriba": 0.2},
    "risa": {"ojos:feliz": 1.0, "boca:sonrisa_abierta": 1.0, "cejas:arriba": 0.45},
    "decidido": {"cejas:enojo": 0.55, "boca:picara": 0.35, "ojos:entrecerrado": 0.15},
    "grito": {"cejas:enojo": 0.8, "boca:A": 1.0, "ojos:grande": 0.3},
    "dolor": {"cejas:preocupado": 1.0, "ojos:cerrado": 0.85, "boca:A": 0.6},
}


def _destinos(partes: dict, clave: str):
    """«ojos:feliz» → [(objeto, "feliz")…]; «cejas:enojo» → las dos cejas; «rubor» → los dos."""
    if clave == "rubor":
        return [(partes["rubor_izq"], "visible"), (partes["rubor_der"], "visible")]
    grupo, forma = clave.split(":")
    if grupo == "ojos":
        return [(partes["ojo_izq"], forma), (partes["ojo_der"], forma)]
    if grupo == "cejas":
        return [(partes["ceja_izq"], forma), (partes["ceja_der"], forma)]
    return [(partes[grupo], forma)]


def _envolvente_audio(ruta: Path, fps: int) -> np.ndarray:
    from estudio.audio.procedural import _decodificar
    x = _decodificar(ruta)
    if x.ndim > 1:
        x = x.mean(1)
    sr = 48000
    hop = sr // fps
    n = len(x) // hop
    if n == 0:
        return np.zeros(0)
    fr = x[: n * hop].reshape(n, hop)
    rms = np.sqrt((fr ** 2).mean(1))
    rms = rms / max(1e-6, np.percentile(rms, 95))
    zc = (np.abs(np.diff(np.sign(fr), axis=1)) > 0).mean(1)       # cruces por cero: «s», «e» → más altos
    return np.stack([np.clip(rms, 0, 1.3), zc], 1)


def _envolvente_texto(texto: str, fps: int, ritmo=13.5) -> np.ndarray:
    """Sin audio todavía: sílabas sintéticas a partir del texto (para las fijas antes de generar las voces)."""
    vocales = "aeiouáéíóú"
    dur = max(0.4, len(texto) / ritmo)
    n = int(dur * fps)
    env = np.zeros((n, 2))
    letras = [c for c in texto.lower() if c.isalpha() or c in " ,.!?¿¡"]
    for i in range(n):
        c = letras[min(len(letras) - 1, int(i / n * len(letras)))] if letras else " "
        abierto = 1.0 if c in vocales else (0.15 if c in " ,.!?¿¡" else 0.45)
        env[i] = (abierto * (0.75 + 0.25 * math.sin(i * 1.9)), 0.08 if c in "eéií" else 0.03)
    return env


def actuar(partes: dict, cara: dict, fps: int, nf: int, semilla: int = 1):
    """Anima la cara cuadro a cuadro: expresiones (con transición), miradas, parpadeos y la boca al hablar."""
    rnd = random.Random(semilla)
    claves = {}                                            # (objeto, forma) -> np.array por cuadro
    for nombre, ob in partes.items():
        for kb in ob.data.shape_keys.key_blocks[1:]:
            claves[(ob.name, kb.name)] = np.zeros(nf)
    obs = {ob.name: ob for ob in partes.values()}

    def sumar(clave, arr):
        for ob, forma in _destinos(partes, clave):
            k = (ob.name, forma)
            if k in claves:
                claves[k] += arr
    # expresiones: escalones suavizados (transición ~0,25 s)
    exprs = sorted(cara.get("expresiones", [{"t": 0, "expr": "neutral"}]), key=lambda e: e["t"])
    t = np.arange(nf) / fps
    pesos_expr = {}
    for i, e in enumerate(exprs):
        t0 = e["t"]
        t1 = exprs[i + 1]["t"] if i + 1 < len(exprs) else 1e9
        tr = e.get("transicion", 0.25)
        tr1 = exprs[i + 1].get("transicion", 0.25) if i + 1 < len(exprs) else 0.25
        sube = np.clip((t - t0) / tr + 0.5, 0, 1)
        baja = np.clip((t1 - t) / tr1 + 0.5, 0, 1)
        w = sube * baja
        w = w * w * (3 - 2 * w)
        inten = e.get("intensidad", 1.0)
        for clave, val in EXPRESIONES[e["expr"]].items():
            pesos_expr.setdefault(clave, np.zeros(nf))
            pesos_expr[clave] += w * val * inten
    # boca al hablar: la expresión de la boca se atenúa mientras habla y las vocales mandan
    abierta = np.zeros(nf)
    agudo = np.zeros(nf)
    for h in cara.get("habla", []):
        env = None
        if h.get("audio") and Path(h["audio"]).exists():
            env = _envolvente_audio(Path(h["audio"]), fps)
            if h.get("recorte_s"):
                r0, r1 = h["recorte_s"]
                env = env[int(r0 * fps): int(r1 * fps) + 1]
        if env is None or len(env) == 0:
            env = _envolvente_texto(h.get("texto", ""), fps)
        f0 = int(round(h["inicio_s"] * fps))
        n = min(len(env), nf - f0)
        if n <= 0:
            continue
        abierta[f0:f0 + n] = np.maximum(abierta[f0:f0 + n], env[:n, 0] * h.get("intensidad", 1.0))
        agudo[f0:f0 + n] = np.maximum(agudo[f0:f0 + n], env[:n, 1])
    k = np.ones(3) / 3
    abierta = np.convolve(abierta, k, mode="same")
    habla = np.clip(abierta * 3, 0, 1)
    for clave, arr in pesos_expr.items():
        if clave.startswith("boca:"):
            arr = arr * (1 - 0.65 * habla)
        sumar(clave, arr)
    zc = np.clip((agudo - 0.05) / 0.08, 0, 1)
    a = np.clip(abierta, 0, 1.2)
    sumar("boca:A", a * (1 - zc) * 0.95)
    sumar("boca:E", a * zc * 0.9)
    o = np.clip(np.convolve(np.diff(np.r_[0, abierta]) < -0.06, np.ones(4) / 4, "same"), 0, 1) * a * 0.6
    sumar("boca:O", o)
    # miradas
    for m in cara.get("miradas", []):
        f0 = int(round(m["t"] * fps))
        f1 = int(round(m.get("hasta", m["t"] + 1.5) * fps))
        u, v = m.get("u", 0.0), m.get("v", 0.0)
        ramp = np.zeros(nf)
        tr = max(1, int(0.12 * fps))
        for f in range(max(0, f0), min(nf, f1)):
            ramp[f] = min(1.0, (f - f0 + 1) / tr, (f1 - f) / tr)
        if u > 0:
            sumar("ojos:mirar_der", ramp * u)
        elif u < 0:
            sumar("ojos:mirar_izq", ramp * -u)
        if v > 0:
            sumar("ojos:mirar_arriba", ramp * v)
        elif v < 0:
            sumar("ojos:mirar_abajo", ramp * -v)
    # parpadeos naturales (cada 2,5–5 s, algunos dobles) + los pedidos
    if cara.get("parpadeo", True):
        ts_ = []
        tt = rnd.uniform(0.6, 2.0)
        while tt < nf / fps:
            ts_.append(tt)
            if rnd.random() < 0.15:
                ts_.append(tt + 0.32)
            tt += rnd.uniform(2.4, 5.2)
        ts_ += cara.get("parpadeos", [])
        parp = np.zeros(nf)
        perfil = [0.35, 0.85, 1.0, 0.7, 0.3]
        for t0 in ts_:
            f0 = int(round(t0 * fps))
            for j, val in enumerate(perfil):
                if 0 <= f0 + j < nf:
                    parp[f0 + j] = max(parp[f0 + j], val)
        sumar("ojos:cerrado", parp)
    frames = np.arange(1, nf + 1, dtype=float)
    for (oname, forma), arr in claves.items():
        ob = obs[oname]
        kb = ob.data.shape_keys.key_blocks[forma]
        kb.slider_max = 2.0
        arr = np.clip(arr, 0, 1.5)
        sk = ob.data.shape_keys
        sk.animation_data_create()
        if sk.animation_data.action is None:
            sk.animation_data.action = bpy.data.actions.new(f"cara_{oname}")
        fc = sk.animation_data.action.fcurve_ensure_for_datablock(sk, f'key_blocks["{forma}"].value')
        if not np.any(arr > 1e-4):
            kb.value = 0.0
            continue
        cambia = np.r_[True, np.abs(np.diff(arr)) > 1e-4] | np.r_[np.abs(np.diff(arr)) > 1e-4, True]
        idx = np.nonzero(cambia)[0]
        fc.keyframe_points.add(len(idx))
        co = np.empty(len(idx) * 2)
        co[0::2] = frames[idx]
        co[1::2] = arr[idx]
        fc.keyframe_points.foreach_set("co", co)
        fc.keyframe_points.foreach_set("interpolation", [1] * len(idx))   # LINEAR
        fc.update()


# ------------------------------------------------------------------------------------------------- todo junto
def preparar(pj: dict, spec: dict, fps: int, nf: int):
    """Vestuario, pelo y cara de un Stickman recién creado por personajes._crear_mixamo."""
    modelo = spec["modelo"]
    vest = spec.get("vestuario", {})
    vestir(pj, modelo, vest)
    datos = datos_reposo(pj["malla"], pj["raiz"])
    c, r = esfera_cabeza(datos)
    cab = Cabeza(c, r, bvh_cabeza(pj["malla"], datos))
    pelo = vest.get("pelo")
    color_pelo = vest.get("color_pelo", (0.02, 0.02, 0.02))
    pj["pelo"] = peinar(pj, cab, pelo, color_pelo) if pelo else []
    tipo = spec.get("cara", {}).get("tipo", "luna" if modelo.endswith("femenino") else "nico")
    partes = armar_cara(pj, cab, tipo, color_cejas=tuple(c * 0.7 for c in color_pelo))
    actuar(partes, spec.get("cara", {}), fps, nf, semilla=sum(map(ord, spec["id"])))
    pj["cara"] = partes
    pj["cabeza"] = cab
    if spec.get("arma_stickman"):
        armar(pj, spec["arma_stickman"], fps, nf)
    if spec.get("mochila"):
        mochila(pj, spec["mochila"], fps, nf)
    for d in (spec["en_mano"] if isinstance(spec.get("en_mano"), list) else [spec["en_mano"]] if spec.get("en_mano") else []):
        en_mano(pj, d, fps, nf)
    return pj


def _tableta(pj: dict, d: dict, fps: int, nf: int):
    """Tableta frente a la panza, inclinada hacia la cara (cuelga del torso; coincide con la pose «tableta»). La
    pantalla usa el material «pantalla_tableta_<id>»: el escenario le pone la imagen (p. ej. el mapa de la misión)."""
    import bmesh
    M = _modelo_a_armadura(pj)
    marco = K.material(f"tableta_marco_{pj['id']}", (0.015, 0.015, 0.018), 0.4)
    pant = bpy.data.materials.new(f"pantalla_tableta_{pj['id']}")
    pant.use_nodes = True
    b_ = next(n for n in pant.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b_.inputs["Base Color"].default_value = (0.02, 0.05, 0.08, 1)
    b_.inputs["Emission Color"].default_value = (0.2, 0.6, 0.8, 1)
    b_.inputs["Emission Strength"].default_value = 1.5
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= 0.11
        v.co.y *= 0.006
        v.co.z *= 0.072
    me = bpy.data.meshes.new(f"TABLETA_{pj['id']}")
    bm.to_mesh(me)
    bm.free()
    # pantalla: un plano apenas delante de la cara frontal (−Y), con coordenadas UV para la imagen
    me2 = bpy.data.meshes.new("tmp_pantalla")
    me2.from_pydata([(-0.051, -0.0032, -0.033), (0.051, -0.0032, -0.033), (0.051, -0.0032, 0.033),
                     (-0.051, -0.0032, 0.033)], [], [(0, 1, 2, 3)])
    uv = me2.uv_layers.new()
    for i, c in enumerate(((0, 0), (1, 0), (1, 1), (0, 1))):
        uv.data[i].uv = c
    bm = bmesh.new()
    bm.from_mesh(me)
    n0 = len(bm.faces)
    bm.from_mesh(me2)
    bm.to_mesh(me)
    bm.free()
    bpy.data.meshes.remove(me2)
    me.materials.append(marco)
    me.materials.append(pant)
    for i, f in enumerate(me.polygons):
        f.material_index = 1 if i >= n0 else 0
    rot = Matrix.Rotation(math.radians(-55), 4, "X")                # la pantalla mira arriba, hacia la cara
    me.transform(rot)
    me.transform(Matrix.Translation((0.0, -0.135, 0.505)))
    me.transform(M)
    ob = bpy.data.objects.new(f"TABLETA_{pj['id']}", me)
    pj["raiz"].users_collection[0].objects.link(ob)
    _a_hueso(ob, pj, "mixamorig:Spine")
    return ob


def en_mano(pj: dict, d: dict, fps: int, nf: int):
    """Un objeto chico en la mano (la radio portátil o la tableta), visible en los tramos [[t0, t1], …]."""
    if d.get("objeto") == "tableta":
        ob = _tableta(pj, d, fps, nf)
        _visible_tramos(ob, d.get("visible", [[0.0, nf / fps]]), fps)
        return ob
    M = _modelo_a_armadura(pj)
    negro = K.material(f"radio_mano_{pj['id']}", (0.02, 0.02, 0.022), 0.45)
    led = K.material("led_verde_radio", (0.1, 1.0, 0.2), 0.3, emision=(0.1, 1.0, 0.2), fuerza=8.0)
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:                       # cuerpo de la radio (unidades del modelo de 0,9 m)
        v.co.x *= 0.022
        v.co.y *= 0.014
        v.co.z *= 0.048
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=0.003, segments=2, affect="EDGES")
    ant = bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.0025, radius2=0.002, depth=0.04)
    for v in ant["verts"]:
        v.co += Vector((0.008, 0.0, 0.044))
    bm2 = bmesh.new()
    bmesh.ops.create_cube(bm2, size=1.0)
    me_led = bpy.data.meshes.new("tmp_led")
    me = bpy.data.meshes.new(f"RADIO_{pj['id']}")
    bm.to_mesh(me)
    bm.free()
    bm2.free()
    bpy.data.meshes.remove(me_led)
    lado = -1.0                             # mano derecha: −X del modelo
    me.transform(Matrix.Translation((lado * 0.395, -0.012, 0.60)))
    me.transform(M)
    me.materials.append(negro)
    me.materials.append(led)
    ob = bpy.data.objects.new(f"RADIO_{pj['id']}", me)
    pj["raiz"].users_collection[0].objects.link(ob)
    _a_hueso(ob, pj, "mixamorig:RightHand")
    _visible_tramos(ob, d.get("visible", [[0.0, nf / fps]]), fps)
    return ob


def _visible_tramos(ob, tramos, fps):
    claves = [(0, True)]
    for t0, t1 in tramos:
        claves += [(int(round(t0 * fps)) + 1, False), (int(round(t1 * fps)) + 1, True)]
    for f, oculto in claves:
        ob.hide_render = ob.hide_viewport = oculto
        ob.keyframe_insert("hide_render", frame=f)
        ob.keyframe_insert("hide_viewport", frame=f)
    for fc in K._fcurves(ob.animation_data.action):
        for kp in fc.keyframe_points:
            kp.interpolation = "CONSTANT"


def armar(pj: dict, a: dict, fps: int, nf: int):
    """Arma del pack en la mano derecha («tipo»: fusil, subfusil, ak, escopeta, pistola), visible en los tramos
    [[t0, t1], …] (por defecto toda la escena) y con fogonazos en cada «disparos» (segundos)."""
    from estudio.blender import armas_stickman as AS, personajes as P
    info = pj["info"]
    ref = a.get("pose_ref", info["clip_arma"])
    acc = P._rt(pj.get("modelo", ""), ref, pj["armadura"], pj["raiz"], info, pj["id"])
    sop = AS.acoplar(pj, a["tipo"], acc, a.get("frame_ref", info.get("frame_arma", 20)))
    tramos = [(int(round(t0 * fps)) + 1, int(round(t1 * fps)) + 1) for t0, t1 in a.get("visible", [[0, nf / fps]])]
    AS.visible(sop, tramos)
    if a.get("disparos"):
        from estudio.blender import efectos as EF
        EF.fogonazos(sop, [int(round(t * fps)) + 1 for t in a["disparos"]], energia=a.get("energia_fogonazo", 900.0))
    pj["arma"] = sop
    return sop


def mochila(pj: dict, m: dict, fps: int, nf: int):
    """Mochila táctica a la espalda (colgada del hueso Spine2), visible desde «desde_s»."""
    M = _modelo_a_armadura(pj)
    mat = K.material(f"mochila_{pj['id']}", (0.11, 0.13, 0.06), 0.85, ruido=0.2, escala_ruido=20)
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= 0.095
        v.co.y *= 0.05
        v.co.z *= 0.12
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=0.018, segments=3, affect="EDGES")
    me = bpy.data.meshes.new(f"MOCHILA_{pj['id']}")
    bm.to_mesh(me)
    bm.free()
    me.transform(Matrix.Translation((0.0, 0.085, 0.555)))          # en la espalda (+Y del modelo), a la altura del pecho
    me.transform(M)
    for p_ in me.polygons:
        p_.use_smooth = True
    me.materials.append(mat)
    ob = bpy.data.objects.new(f"MOCHILA_{pj['id']}", me)
    pj["raiz"].users_collection[0].objects.link(ob)
    _a_hueso(ob, pj, "mixamorig:Spine2")
    f0 = int(round(m.get("desde_s", 0.0) * fps)) + 1
    for f, oculto in ((0, True), (f0, False)):
        ob.hide_render = ob.hide_viewport = oculto
        ob.keyframe_insert("hide_render", frame=f)
        ob.keyframe_insert("hide_viewport", frame=f)
    return ob
