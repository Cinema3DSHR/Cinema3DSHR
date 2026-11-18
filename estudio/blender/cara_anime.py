"""Rostro dibujado «anime realista» para los personajes humanos de «Un sueño de a dos» (p010).

Es el mismo sistema de las caras de los Stickman (estudio/blender/stickman.py): piezas planas dibujadas en 2D,
proyectadas punto por punto sobre la superficie REAL de la cabeza (rayo desde el centro) y colgadas del hueso de la
cabeza; cada pieza tiene formas clave y la actuación (expresiones, boca con la voz, miradas, parpadeo) es la de los
Stickman (`stickman.actuar`). Lo que cambia es el dibujo, más humano:
  · OJOS en capas: blanco con forma de almendra, iris de color con anillo oscuro, pupila, dos brillos, línea del
    párpado de arriba (más gruesa hacia afuera, con pestañas en ella), línea suave de abajo y pliegue del párpado.
    El iris queda recortado por los párpados en cada forma (no se sale del ojo al mirar a un costado).
  · CEJAS finas y afinadas hacia la cola, del color del pelo.
  · NARIZ sugerida: sombra lateral del tabique y las dos aletas.
  · BOCA con labios: labio de arriba y de abajo rosados, interior oscuro y dientes que asoman al abrirla.
  · RUBOR suave (semitransparente).
Formas clave (los nombres de los Stickman + las de las láminas «Stickman cinematográfico»):
  ojos: cerrado, feliz, entrecerrado, abajo_parpado, grande, triste, mirar_der/izq/arriba/abajo
  cejas: arriba, feliz, enojo, preocupado, triste, plana
  boca: sonrisa, sonrisa_abierta (en D, con dientes y lengua), picara, triste, o_chica, enojo, preocupada,
        y las vocales A, E, O, M · rubor: visible
Las alturas de ojos, cejas, nariz y boca se miden en cada cabeza (`_alturas`).
"""
from __future__ import annotations
import math

import numpy as np

from estudio.blender import kit as K
from estudio.blender import stickman as SM


def _lin(c):
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)


# Medidas en radianes sobre la cabeza (u, v). Se midió el perfil de cada maniquí (v = 0 a la altura del centro;
# mentón en v ≈ −0,9): ojos a media cabeza, cejas arriba, base de la nariz y boca en los tercios de la cara.
PROPORCIONES = {
    "el": {"ojo_sep": 0.37, "ojo_alto": -0.03, "ojo_rx": 0.165, "ojo_ry": 0.098, "iris": 0.98, "mirada": 0.42,
           "ceja_alto": 0.22, "ceja_w": 0.20, "ceja_g": 0.078, "nariz_alto": -0.47, "boca_alto": -0.64,
           "boca_w": 0.21, "labio": 0.030, "pestanas": 0, "sobre": 0.010},
    "ella": {"ojo_sep": 0.35, "ojo_alto": -0.10, "ojo_rx": 0.168, "ojo_ry": 0.11, "iris": 1.0, "mirada": 0.42,
             "ceja_alto": 0.14, "ceja_w": 0.18, "ceja_g": 0.058, "nariz_alto": -0.50, "boca_alto": -0.67,
             "boca_w": 0.19, "labio": 0.038, "pestanas": 5, "sobre": 0.010},
}


# ------------------------------------------------------------------------------------------------ ojos

def _ojo(lado: int, P: dict):
    """Ojo en capas. lado = +1: a la derecha de la imagen (izquierda del personaje). x>0 = hacia afuera."""
    N = 16                                                    # puntos por párpado (de adentro hacia afuera)
    cx, cy, rx, ry = lado * P["ojo_sep"], P["ojo_alto"], P["ojo_rx"], P["ojo_ry"]
    xs = np.linspace(-1, 1, N)

    def parpados(abre=1.0, sube_inf=0.0, escala=1.0, baja_sup=0.0, feliz=0.0, caida=0.0):
        """Curvas del párpado de arriba y de abajo (y relativa al centro), por punto. caida: el de arriba baja más
        hacia afuera (ojos tristes)."""
        sup = ry * escala * (1 - xs ** 2) ** 0.72 * (1 - 0.10 * xs) * abre
        inf = -ry * escala * 0.62 * (1 - xs ** 2) ** 0.9 * (1 - 0.15 * xs)
        inf = inf + (ry * escala * 0.62 * (1 - xs ** 2) ** 0.9) * sube_inf
        sup = sup - (sup - inf) * np.clip(baja_sup + caida * 0.45 * ((xs + 1) / 2) ** 1.2, 0, 1)
        if feliz:
            # «ojos felices»: el de abajo sube en arco y el de arriba baja sobre él
            arco = ry * escala * 0.35 * (1 - xs ** 2) ** 0.8
            inf = inf * (1 - feliz) + (arco - ry * 0.12) * feliz
            sup = np.maximum(inf, sup * (1 - feliz) + (arco + ry * 0.06) * feliz)
        sup = np.maximum(sup, inf)
        return sup, inf

    def islas(abre=1.0, sube_inf=0.0, escala=1.0, baja_sup=0.0, feliz=0.0, gx=0.0, gy=0.0, caida=0.0):
        sup, inf = parpados(abre, sube_inf, escala, baja_sup, feliz, caida)
        X = cx + lado * xs * rx * escala                       # x hacia afuera según el lado
        def dentro(px, py):
            # recorte contra la almendra: interpolar las curvas en la x del punto
            t = np.clip((px - cx) * lado / (rx * escala), -1, 1)
            s_ = np.interp(t, xs, sup)
            i_ = np.interp(t, xs, inf)
            return np.clip(py, cy + i_ + 1e-4, cy + max(1e-4, s_)) if s_ > i_ else cy + i_
        out = {}
        # 1) blanco: abanico desde el centro
        borde = [(X[k], cy + sup[k]) for k in range(N)] + [(X[k], cy + inf[k]) for k in range(N - 2, 0, -1)]
        out["blanco"] = [(cx, cy + (sup[N // 2] + inf[N // 2]) / 2)] + borde
        # 2) iris, anillo y pupila: círculos recortados por los párpados
        ri = ry * escala * P["iris"]
        icx, icy = cx + lado * gx * rx * escala, cy + gy * ry * escala - ry * 0.05
        for nombre, r in (("anillo", ri), ("iris", ri * 0.84), ("pupila", ri * 0.48)):
            pts = [(icx, dentro(icx, icy) if True else icy)]
            for a in np.linspace(0, 2 * math.pi, 20, endpoint=False):
                px = icx + r * math.cos(a) * 0.95
                pts.append((px, dentro(px, icy + r * math.sin(a))))
            out[nombre] = pts
        # 3) brillos (arriba a un costado del iris); se esconden cuando el ojo se cierra
        vis = max(0.0, min(1.0, (sup[N // 2] - inf[N // 2]) / (ry * 0.8)))
        for nombre, (dx, dy, r) in (("brillo1", (0.33, 0.36, 0.34)), ("brillo2", (-0.36, -0.34, 0.15))):
            bx, by = icx + lado * dx * ri, icy + dy * ri
            rr = ri * r * vis
            out[nombre] = [(bx, dentro(bx, by))] + [(bx + rr * math.cos(a), dentro(bx, by) + rr * math.sin(a))
                                                    for a in np.linspace(0, 2 * math.pi, 10, endpoint=False)]
        # 4) línea del párpado de arriba: más gruesa hacia afuera, con una «cola» corta
        g = ry * (0.10 + 0.20 * (xs + 1) / 2)
        top = [(X[k], cy + sup[k] + g[k] * 0.5) for k in range(N)]
        bot = [(X[k], cy + sup[k] - g[k] * 0.25) for k in range(N)]
        cola = (X[-1] + lado * rx * 0.16, cy + sup[-1] + ry * 0.22 * abre - ry * 0.05)
        out["linea_sup"] = top + [cola] + bot[::-1]
        # 5) línea de abajo (suave, sólo la mitad de afuera)
        k0 = N // 3
        out["linea_inf"] = ([(X[k], cy + inf[k] - ry * 0.035) for k in range(k0, N)] +
                            [(X[k], cy + inf[k] + ry * 0.02) for k in range(N - 1, k0 - 1, -1)])
        # 6) pliegue del párpado (arriba de la línea)
        pl = [(X[k], cy + sup[k] + ry * (0.42 + 0.1 * (1 - abre))) for k in range(2, N - 1)]
        out["pliegue"] = pl + [(x, y + ry * 0.05) for x, y in pl[::-1]]
        # 7) pestañas (ella): triangulitos sobre la línea hacia afuera
        for j in range(P["pestanas"]):
            k = N - 2 - 2 * j
            bx, by = X[k], cy + sup[k] + g[k] * 0.4
            d = ry * (0.30 - 0.03 * j) * max(0.15, abre)
            out[f"pest{j}"] = [(bx - lado * rx * 0.02, by), (bx + lado * rx * 0.03, by),
                               (bx + lado * rx * (0.10 + 0.02 * j), by + d)]
        return out

    base = islas()
    g = P["mirada"]
    formas_isl = {
        "base": base,
        "cerrado": islas(abre=0.0, sube_inf=0.25),
        "feliz": islas(feliz=1.0),
        "entrecerrado": islas(baja_sup=0.42),
        "abajo_parpado": islas(sube_inf=0.35),
        "grande": islas(abre=1.12, escala=1.12),
        "triste": islas(baja_sup=0.28, caida=0.8, gy=-0.12),
        "mirar_der": islas(gx=g),
        "mirar_izq": islas(gx=-g),
        "mirar_arriba": islas(gy=0.55 * g),
        "mirar_abajo": islas(gy=-0.6 * g, baja_sup=0.18),
    }
    # mirar a la derecha/izquierda de la IMAGEN: gx va «hacia afuera» según el lado → se invierte en el ojo derecho
    if lado < 0:
        formas_isl["mirar_der"], formas_isl["mirar_izq"] = islas(gx=-g), islas(gx=g)
    capas = [("pliegue", 0.8, 6), ("blanco", 1.0, 0), ("anillo", 1.3, 1), ("iris", 1.45, 2), ("pupila", 1.6, 3),
             ("brillo1", 2.0, 4), ("brillo2", 2.0, 4), ("linea_inf", 1.9, 5), ("linea_sup", 2.1, 5)]
    capas += [(f"pest{j}", 2.1, 5) for j in range(P["pestanas"])]
    formas = {k: [] for k in formas_isl}
    caras, sobre, mat_idx = [], [], []
    for nombre, s, mi in capas:
        ini = len(formas["base"])
        n = len(base[nombre])
        for k in formas_isl:
            formas[k] += formas_isl[k][nombre]
        if nombre in ("blanco", "anillo", "iris", "pupila", "brillo1", "brillo2"):
            for i in range(1, n):
                caras.append((ini, ini + i, ini + (i % (n - 1)) + 1))
        elif nombre.startswith("pest"):
            caras.append((ini, ini + 1, ini + 2))
        else:                                                     # tiras: arriba ida, abajo vuelta
            m = n // 2
            if nombre == "linea_sup":
                m = (n - 1) // 2
                top = list(range(ini, ini + m))
                cola = ini + m
                bot = list(range(ini + n - 1, ini + m, -1))
                for i in range(m - 1):
                    caras.append((top[i], top[i + 1], bot[i + 1], bot[i]))
                caras.append((top[-1], cola, bot[-1]))
                mat_idx += [mi] * m
                sobre += [P["sobre"] * s] * n
                continue
            for i in range(m - 1):
                caras.append((ini + i, ini + i + 1, ini + n - 2 - i, ini + n - 1 - i))
        sobre += [P["sobre"] * s] * n
        nuevas = len(caras) - len(mat_idx)
        mat_idx += [mi] * nuevas
    return formas, caras, sobre, mat_idx


# ------------------------------------------------------------------------------------------------ cejas, nariz

def _ceja(lado: int, P: dict):
    """Ceja fina: más ancha en la cabeza (hacia la nariz) y afinada en la cola."""
    K_ = 11
    cx, cy, w, gro = lado * (P["ojo_sep"] + 0.012), P["ceja_alto"], P["ceja_w"], P["ceja_g"]

    def tira(arco=0.30, dy=0.0, gir=0.0):
        sup, inf = [], []
        for i in range(K_):
            s = -1 + 2 * i / (K_ - 1)
            x = cx + lado * s * w
            pico = 0.35                                            # el arco más alto hacia afuera
            yc = cy + dy + arco * w * 0.35 * (1 - ((s - pico) / (1 + abs(pico))) ** 2) - gir * w * 0.42 * (-s)
            g = gro * (1.0 - 0.45 * (s + 1) / 2) * (0.35 + 0.65 * max(0.0, 1 - s ** 8) ** 0.5)
            sup.append((x, yc + g / 2))
            inf.append((x, yc - g / 2))
        return sup + inf
    formas = {"base": tira(), "arriba": tira(0.5, 0.07), "enojo": tira(0.02, -0.02, 0.9),
              "preocupado": tira(0.15, 0.025, -0.75), "plana": tira(0.05, -0.008),
              "triste": tira(-0.12, -0.004, -0.8), "feliz": tira(0.6, 0.045)}
    caras = [(i, i + 1, K_ + i + 1, K_ + i) for i in range(K_ - 1)]
    return formas, caras, [P["sobre"] * 1.2] * (2 * K_), [0] * len(caras)


def _nariz(P: dict):
    """Nariz sugerida, como en el anime cuidado: sombra suave al costado del tabique y una curva corta debajo."""
    y = P["nariz_alto"]
    pts, caras = [], []
    # sombra del costado (de la mitad de la nariz a la punta), angosta y afinada
    lado = [(-0.020 - 0.004 * t, y + 0.20 - 0.18 * t) for t in np.linspace(0, 1, 6)]
    pts += lado + [(x - 0.010 * (1 - abs(0.5 - t) * 1.2), yy) for (x, yy), t in zip(lado[::-1], np.linspace(1, 0, 6))]
    for i in range(5):
        caras.append((i, i + 1, 10 - i, 11 - i))
    # base de la nariz: curva corta y suave
    b0 = len(pts)
    curva = [(0.045 * math.sin(t), y - 0.010 - 0.012 * math.cos(t)) for t in np.linspace(-1.3, 1.3, 9)]
    pts += curva + [(x, yy + 0.010 * (1 - abs(x) / 0.05)) for x, yy in curva[::-1]]
    for i in range(8):
        caras.append((b0 + i, b0 + i + 1, b0 + 16 - i, b0 + 17 - i))
    return {"base": pts}, caras, [P["sobre"] * 0.8] * len(pts), [0] * len(caras)


# ------------------------------------------------------------------------------------------------ boca

def _boca(P: dict):
    """Labios rosados (arriba y abajo), interior oscuro y dientes. Cada gesto y vocal es una forma clave."""
    N = 15
    y0, W, L = P["boca_alto"], P["boca_w"], P["labio"]
    ts = np.linspace(-1, 1, N)

    def forma(abre=0.0, sonr=0.0, ancho=1.0, dy=0.0, ladeo=0.0, redondo=0.0, dientes=0.6, plano=0.0,
              apretar=1.0, lengua=0.38):
        """abre: separación de los labios; sonr > 0 comisuras arriba (< 0 abajo); redondo: «O»; plano: el labio
        de arriba queda casi recto (sonrisa en D); apretar < 1: labios finos (enojo)."""
        x = ts * W * ancho * (1 - 0.25 * redondo)
        comis = sonr * 0.05 * ts ** 2 + ladeo * 0.02 * ts
        sep = abre * 0.13 * (1 - ts ** 2) ** (0.7 - 0.3 * redondo)
        in_sup = y0 + dy + comis * (1 - plano) + sep * 0.25
        in_inf = y0 + dy + comis - sep * 0.75
        # arco de cupido en el labio de arriba y labio de abajo más lleno
        cup = L * apretar * (0.75 + 0.35 * np.exp(-((np.abs(ts) - 0.28) / 0.2) ** 2) - 0.25 * np.exp(-(ts / 0.1) ** 2))
        out_sup = in_sup + cup * (1 - ts ** 2) ** 0.55 + 0.002
        out_inf = in_inf - L * apretar * 1.15 * (1 - ts ** 2) ** 0.6 - 0.002
        # dientes de arriba: una banda pareja debajo del labio (más baja en el centro, nunca más que la boca)
        dient = np.maximum(in_inf + 0.25 * (in_sup - in_inf),
                           in_sup - dientes * 0.05 * (1 - ts ** 2) ** 0.35 * min(1.0, abre * 3))
        leng = np.minimum(dient, in_inf + (in_sup - in_inf) * lengua * (1 - ts ** 2) ** 0.6)
        pts = []
        for a, b in ((out_sup, in_sup), (in_sup, in_inf), (in_inf, leng), (in_sup, dient), (in_inf, out_inf)):
            pts += [(x[i], a[i]) for i in range(N)] + [(x[i], b[i]) for i in range(N)]
        # línea de la boca (oscura, fina) entre los labios
        pts += [(x[i], (in_sup[i] + in_inf[i]) / 2 + 0.004) for i in range(N)]
        pts += [(x[i], (in_sup[i] + in_inf[i]) / 2 - 0.004) for i in range(N)]
        return pts

    formas = {
        "base": forma(),
        "sonrisa": forma(sonr=1.0, ancho=1.08, dy=0.006),
        "sonrisa_abierta": forma(abre=1.9, sonr=1.6, ancho=1.1, dy=0.02, dientes=0.75, plano=0.8, lengua=0.4),
        "picara": forma(sonr=0.5, ladeo=1.0, ancho=0.95),
        "triste": forma(sonr=-1.6, ancho=0.82, apretar=0.85, dy=0.004),
        "o_chica": forma(abre=1.0, ancho=0.42, redondo=1.0, dientes=0.0, lengua=0.25),
        "enojo": forma(sonr=-0.45, ancho=0.86, apretar=0.55, dy=-0.004),
        "preocupada": forma(sonr=-0.6, ancho=0.76, ladeo=0.35, apretar=0.8),
        "A": forma(abre=1.0, ancho=0.9, dientes=0.5),
        "E": forma(abre=0.45, ancho=1.05, dientes=0.9),
        "O": forma(abre=0.75, ancho=0.62, redondo=1.0, dientes=0.2),
        "M": forma(ancho=0.92, dy=-0.002),
    }
    caras, mat_idx, sobre = [], [], []
    # labio sup, interior, lengua, dientes, labio inf, línea
    capas = [(1.6, 1), (1.0, 2), (1.15, 4), (1.3, 3), (1.6, 1), (1.7, 0)]
    for k, (s, mi) in enumerate(capas):
        ini = k * 2 * N
        for i in range(N - 1):
            caras.append((ini + i, ini + i + 1, ini + N + i + 1, ini + N + i))
            mat_idx.append(mi)
        sobre += [P["sobre"] * s] * (2 * N)
    return formas, caras, sobre, mat_idx


def _rubor(lado: int, P: dict):
    N = 16
    cx, cy = lado * (P["ojo_sep"] + 0.03), P["ojo_alto"] - 0.16
    rx, ry = 0.10, 0.045
    cent = [(cx, cy)] * (N + 1)
    lleno = [(cx, cy)] + [(cx + rx * math.cos(2 * math.pi * i / N), cy + ry * math.sin(2 * math.pi * i / N))
                          for i in range(N)]
    return {"base": cent, "visible": lleno}, SM._abanico(N), [P["sobre"] * 0.6] * (N + 1), [0] * N


# ------------------------------------------------------------------------------------------------ armado

def _alturas(cab, datos) -> dict:
    """Alturas de ojos, cejas, nariz y boca medidas sobre la cabeza real: de la coronilla al mentón (perfil del
    centro de la cara), con las proporciones de una cara humana: ojos a la mitad, base de la nariz a 0,20 y la boca a
    0,31 de la altura de la cabeza por debajo de los ojos; cejas a 0,085 por encima."""
    vs = np.linspace(-1.5, 1.3, 120)
    pts = [cab.punto(0.0, float(v), 0.0) for v in vs]
    z = np.array([p.z for p in pts])
    adelante = np.array([cab.c.y - p.y for p in pts])           # cuánto sobresale hacia el frente
    # el mentón: el punto más bajo que todavía es «cara» (debajo, los rayos ya tocan el cuello y el pecho)
    cara = (vs < 0.0) & (adelante >= 0.85 * adelante.max())
    i_m = int(np.argmin(np.where(cara, z, np.inf)))
    z_m = float(z[i_m])
    reg = datos["reg"] == 0
    top = float(datos["pos"][reg][:, 2].max()) if reg.any() else float(z.max())
    alto = top - z_m
    sel = vs >= vs[i_m]
    zs, vv = z[sel], vs[sel]
    orden = np.argsort(zs)

    def v_de(zz):
        return float(np.interp(zz, zs[orden], vv[orden]))
    ojos = z_m + 0.5 * alto
    return {"ojo_alto": v_de(ojos), "ceja_alto": v_de(ojos + 0.085 * alto),
            "nariz_alto": v_de(ojos - 0.20 * alto), "boca_alto": v_de(ojos - 0.31 * alto)}


# Expresiones de los personajes humanos («Stickman cinematográfico – híbrido realista»): las seis principales de las
# láminas del dueño + las de los Stickman (mismos nombres, así sirven las recetas).
EXPRESIONES = {
    "neutral": {},
    "feliz": {"boca:sonrisa_abierta": 1.0, "ojos:feliz": 0.22, "cejas:feliz": 0.6, "rubor": 0.25},
    "sonrisa": {"boca:sonrisa": 1.0, "ojos:feliz": 0.15, "cejas:arriba": 0.2},
    "sonrisa_suave": {"boca:sonrisa": 0.55},
    "carinosa": {"rubor": 0.45, "boca:sonrisa": 0.7, "ojos:feliz": 0.2, "cejas:arriba": 0.2},
    "sorpresa": {"cejas:arriba": 1.0, "ojos:grande": 0.9, "boca:o_chica": 1.0},
    "preocupado": {"cejas:preocupado": 1.0, "boca:preocupada": 1.0, "ojos:abajo_parpado": 0.15},
    "enojado": {"cejas:enojo": 1.0, "boca:enojo": 1.0, "ojos:entrecerrado": 0.3},
    "triste": {"cejas:triste": 1.0, "ojos:triste": 1.0, "boca:triste": 1.0},
}
EXPRESIONES["preocupada"] = EXPRESIONES["preocupado"]
EXPRESIONES["enojo"] = EXPRESIONES["enojado"]


def actuar(partes: dict, cara: dict, fps: int, nf: int, semilla: int = 1):
    """La actuación de los Stickman (`stickman.actuar`) con la tabla de expresiones de los humanos."""
    vieja = SM.EXPRESIONES
    SM.EXPRESIONES = {**vieja, **EXPRESIONES}
    try:
        SM.actuar(partes, cara, fps, nf, semilla)
    finally:
        SM.EXPRESIONES = vieja


def armar(pj: dict, tipo: str, perfil: dict, col) -> dict:
    """Crea las piezas de la cara sobre la cabeza real del maniquí. Devuelve {nombre: objeto} (como los Stickman)."""
    datos = SM.datos_reposo(pj["malla"], pj["raiz"])
    c, r = SM.esfera_cabeza(datos)
    cab = SM.Cabeza(c, r, SM.bvh_cabeza(pj["malla"], datos))
    pj["cabeza"] = cab
    P = {**PROPORCIONES[tipo], **_alturas(cab, datos), **perfil.get("cara_proporciones", {})}
    pid = pj["id"]
    piel = perfil["piel"]
    m = {
        "linea": K.material(f"cara_linea_{pid}", _lin((0.10, 0.06, 0.05)), 0.5),
        "blanco": K.material(f"cara_blanco_{pid}", _lin((0.94, 0.92, 0.89)), 0.35),
        "anillo": K.material(f"cara_anillo_{pid}", _lin(tuple(x * 0.45 for x in perfil["iris"])), 0.3),
        "iris": K.material(f"cara_iris_{pid}", _lin(tuple(x * 0.75 for x in perfil["iris"])), 0.25),
        "pupila": K.material(f"cara_pupila_{pid}", _lin((0.02, 0.015, 0.015)), 0.2),
        "brillo": K.material(f"cara_brillo_{pid}", (0.95, 0.95, 0.95), 0.2, emision=(1, 1, 1), fuerza=0.8),
        "pliegue": K.material(f"cara_pliegue_{pid}", _lin(tuple(x * 0.72 for x in piel)), 0.5),
        "ceja": K.material(f"cara_ceja_{pid}", _lin(perfil["cejas"]), 0.6),
        "nariz": K.material(f"cara_nariz_{pid}", _lin(tuple(x * 0.66 for x in piel)), 0.55),
        "labios": K.material(f"cara_labios_{pid}", _lin(tuple(0.5 * a + 0.5 * b for a, b in
                                                              zip(perfil["labios"], piel))), 0.35),
        "lengua": K.material(f"cara_lengua_{pid}", _lin((0.80, 0.42, 0.45)), 0.4),
        "boca": K.material(f"cara_boca_{pid}", _lin((0.22, 0.05, 0.06)), 0.5),
        "dientes": K.material(f"cara_dientes_{pid}", _lin((0.95, 0.93, 0.88)), 0.3),
        "linea_boca": K.material(f"cara_linea_boca_{pid}", _lin(tuple(x * 0.55 for x in perfil["labios"])), 0.5),
        "rubor": K.material(f"cara_rubor_{pid}", _lin((0.93, 0.52, 0.52)), 0.6, alfa=0.45, mezcla="BLENDED"),
    }
    partes = {}
    for lado, nom in ((1, "izq"), (-1, "der")):
        f, ca, s, mi = _ojo(lado, P)
        partes[f"ojo_{nom}"] = SM._malla_con_formas(
            f"CARA_{pid}_ojo_{nom}", pj, cab, f, ca, s,
            [m["blanco"], m["anillo"], m["iris"], m["pupila"], m["brillo"], m["linea"], m["pliegue"]], mi, col)
        f, ca, s, mi = _ceja(lado, P)
        partes[f"ceja_{nom}"] = SM._malla_con_formas(f"CARA_{pid}_ceja_{nom}", pj, cab, f, ca, s, [m["ceja"]], mi, col)
        f, ca, s, mi = _rubor(lado, P)
        partes[f"rubor_{nom}"] = SM._malla_con_formas(f"CARA_{pid}_rubor_{nom}", pj, cab, f, ca, s, [m["rubor"]],
                                                      mi, col)
    f, ca, s, mi = _boca(P)
    partes["boca"] = SM._malla_con_formas(f"CARA_{pid}_boca", pj, cab, f, ca, s,
                                          [m["linea_boca"], m["labios"], m["boca"], m["dientes"], m["lengua"]], mi, col)
    f, ca, s, mi = _nariz(P)
    nariz = SM._malla_con_formas(f"CARA_{pid}_nariz", pj, cab, f, ca, s, [m["nariz"]], mi, col)
    for k in list(nariz.data.shape_keys.key_blocks)[::-1]:
        nariz.shape_key_remove(k)
    pj["nariz"] = nariz
    return partes
