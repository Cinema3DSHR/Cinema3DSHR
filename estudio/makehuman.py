"""Datos de MakeHuman (CC0) para rostros humanos: malla base, macros (género, edad), ojos y unidades de expresión.

La cabeza de los personajes humanos es la de MakeHuman TAL CUAL (el modelo por defecto de MakeHuman, masculino o
femenino según el control de género, sin retoques): cara, párpados, labios, dientes, lengua, ojos y pestañas, con
las 59 unidades de expresión faciales (estilo FACS) de MakeHuman horneadas como formas clave.

Fuente: https://github.com/makehumancommunity/makehuman (commit fijo; sólo `makehuman/data`, datos CC0).
Se descarga sola la primera vez en ../makehuman (o CINE_MAKEHUMAN_DIR); NO se guarda en este repositorio.
Unidades: MakeHuman mide en decímetros, +Y arriba y mira a +Z. `a_blender()` lo pasa a metros, +Z arriba, mirando
a −Y (como los modelos de Tripo del estudio). Todo en numpy: no necesita Blender.
"""
from __future__ import annotations
import functools
import json
import math
import os
import subprocess
from pathlib import Path

import numpy as np

from estudio import config

COMMIT = "a8bc2d54ff0ac92e78ff71431b1023eda42bf482"
REPO = "https://github.com/makehumancommunity/makehuman.git"
CARPETAS = ["3dobjs", "eyes", "poseunits", "rigs", "targets/macrodetails"]


def raiz() -> Path:
    return Path(os.environ.get("CINE_MAKEHUMAN_DIR", config.RAIZ.parent / "makehuman"))


def asegurar() -> Path:
    """Baja (una vez) la parte de MakeHuman que usa el estudio, en el commit fijo."""
    d = raiz() / "makehuman" / "data"
    if (d / "3dobjs" / "base.obj").exists() and (d / "poseunits" / "face-poseunits.bvh").exists():
        return d
    r = raiz()
    if not (r / ".git").exists():
        r.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "-q", "--filter=blob:none", "--no-checkout", REPO, str(r)], check=True)
    subprocess.run(["git", "-C", str(r), "sparse-checkout", "set", *[f"makehuman/data/{c}" for c in CARPETAS]],
                   check=True)
    subprocess.run(["git", "-C", str(r), "checkout", "-q", COMMIT], check=True)
    return d


def _leer_obj(ruta: Path) -> dict:
    v, vt, caras, uvs, grupos = [], [], [], [], []
    grupo = ""
    for linea in ruta.open(encoding="utf-8", errors="ignore"):
        if linea.startswith("v "):
            v.append([float(x) for x in linea.split()[1:4]])
        elif linea.startswith("vt "):
            vt.append([float(x) for x in linea.split()[1:3]])
        elif linea.startswith("g "):
            grupo = linea.split(None, 1)[1].strip()
        elif linea.startswith("f "):
            idx = [p.split("/") for p in linea.split()[1:]]
            caras.append([int(p[0]) - 1 for p in idx])
            uvs.append([int(p[1]) - 1 if len(p) > 1 and p[1] else -1 for p in idx])
            grupos.append(grupo)
    return {"v": np.array(v), "vt": np.array(vt), "caras": caras, "uvs": uvs, "grupos": grupos}


@functools.lru_cache(maxsize=None)
def base() -> dict:
    return _leer_obj(asegurar() / "3dobjs" / "base.obj")


@functools.lru_cache(maxsize=None)
def leer_target(rel: str) -> tuple[np.ndarray, np.ndarray]:
    idx, d = [], []
    for linea in (asegurar() / "targets" / rel).open(encoding="utf-8", errors="ignore"):
        if not linea.strip() or linea.startswith("#"):
            continue
        p = linea.split()
        idx.append(int(p[0]))
        d.append([float(p[1]), float(p[2]), float(p[3])])
    return np.array(idx, dtype=np.int64), np.array(d).reshape(-1, 3)


def _pesos_lineales(valor: float, puntos) -> dict[str, float]:
    if valor <= puntos[0][0]:
        return {puntos[0][1]: 1.0}
    for (a, na), (b, nb) in zip(puntos, puntos[1:]):
        if valor <= b:
            t = (valor - a) / (b - a)
            return {na: 1.0 - t, nb: t}
    return {puntos[-1][1]: 1.0}


def cuerpo(genero: float, edad: float = 0.5, musculo: float = 0.5, peso: float = 0.5,
           razas: dict | None = None) -> np.ndarray:
    """Malla base con las macros de MakeHuman. Por defecto (como el programa): 25 años, músculo y peso promedio y
    las tres razas por partes iguales; género 0 = mujer, 1 = hombre."""
    v = base()["v"].copy()
    gen = {"female": 1.0 - genero, "male": genero}
    eda = _pesos_lineales(edad, [(0.0, "baby"), (0.1875, "child"), (0.5, "young"), (1.0, "old")])
    mus = _pesos_lineales(musculo, [(0.0, "minmuscle"), (0.5, "averagemuscle"), (1.0, "maxmuscle")])
    pes = _pesos_lineales(peso, [(0.0, "minweight"), (0.5, "averageweight"), (1.0, "maxweight")])
    for g, wg in gen.items():
        for a, wa in eda.items():
            for m, wm in mus.items():
                for p, wp in pes.items():
                    w = wg * wa * wm * wp
                    if w > 1e-4:
                        i, d = leer_target(f"macrodetails/universal-{g}-{a}-{m}-{p}.target")
                        v[i] += w * d
    razas = razas or {"african": 1 / 3, "asian": 1 / 3, "caucasian": 1 / 3}
    tot = sum(razas.values()) or 1.0
    for r, wr in razas.items():
        for g, wg in gen.items():
            for a, wa in eda.items():
                w = wr / tot * wg * wa
                if w > 1e-4:
                    i, d = leer_target(f"macrodetails/{r}-{g}-{a}.target")
                    v[i] += w * d
    return v


def a_blender(v: np.ndarray) -> np.ndarray:
    """dm, +Y arriba, mira a +Z  →  m, +Z arriba, mira a −Y."""
    return np.stack([v[:, 0], -v[:, 2], v[:, 1]], axis=1) * 0.1


@functools.lru_cache(maxsize=None)
def esqueleto() -> dict:
    return json.loads((asegurar() / "rigs" / "default.mhskel").read_text())


def articulacion(v: np.ndarray, nombre: str) -> np.ndarray:
    return v[esqueleto()["joints"][nombre]].mean(axis=0)


# ------------------------------------------------------------------------------------------------ ojos (proxy)

@functools.lru_cache(maxsize=None)
def _ojos_obj() -> dict:
    d = asegurar() / "eyes" / "high-poly"
    o = _leer_obj(d / "high-poly.obj")
    ref, esc, en_verts = [], {}, False
    for linea in (d / "high-poly.mhclo").open(encoding="utf-8", errors="ignore"):
        p = linea.split()
        if not p or p[0].startswith("#"):
            continue
        if p[0] in ("x_scale", "y_scale", "z_scale"):
            esc[p[0][0]] = (int(p[1]), int(p[2]), float(p[3]))
        elif p[0] == "verts":
            en_verts = True
        elif en_verts and len(p) == 9:
            ref.append([float(x) for x in p])
        elif en_verts and len(p) == 1:
            ref.append([float(p[0]), 0, 0, 1.0, 0, 0, 0, 0, 0])
    return {**o, "ref": np.array(ref), "esc": esc, "textura": asegurar() / "eyes" / "materials" / "brown_eye.png"}


def ojos(v_cuerpo: np.ndarray) -> dict:
    """Ojos de alta resolución ajustados a la cara (método mhclo: 3 vértices de la base + desplazamiento escalado)."""
    o = _ojos_obj()
    r = o["ref"]
    i = r[:, :3].astype(np.int64)
    off = r[:, 6:9].copy()
    for k, ax in (("x", 0), ("y", 1), ("z", 2)):
        a, b, den = o["esc"][k]
        off[:, ax] *= abs(v_cuerpo[a, ax] - v_cuerpo[b, ax]) / den
    pos = (v_cuerpo[i] * r[:, 3:6][:, :, None]).sum(axis=1) + off
    return {**o, "v": pos}


# ------------------------------------------------------------------------------------------------ expresiones

def _leer_bvh(ruta: Path):
    toks = ruta.read_text().split()
    juntas, pila, k = [], [], 0
    while toks[k] != "MOTION":
        t = toks[k]
        if t in ("ROOT", "JOINT"):
            juntas.append({"nombre": toks[k + 1], "padre": pila[-1] if pila else -1})
            k += 2
        elif t == "End":
            juntas.append({"nombre": None, "padre": pila[-1]})
            k += 2
        elif t == "{":
            pila.append(len(juntas) - 1)
            k += 1
        elif t == "}":
            pila.pop()
            k += 1
        elif t == "OFFSET":
            juntas[-1]["offset"] = np.array([float(x) for x in toks[k + 1:k + 4]])
            k += 4
        elif t == "CHANNELS":
            n = int(toks[k + 1])
            juntas[-1]["canales"] = toks[k + 2:k + 2 + n]
            k += 2 + n
        else:
            k += 1
    nf = int(toks[k + 2])
    return juntas, np.array([float(x) for x in toks[k + 6:]]).reshape(nf, -1)


def _rot(eje: str, grados: float) -> np.ndarray:
    a = math.radians(grados)
    c, s = math.cos(a), math.sin(a)
    if eje == "X":
        return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    if eje == "Y":
        return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


@functools.lru_cache(maxsize=None)
def unidades_expresion() -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """Las unidades de expresión de MakeHuman (face-poseunits.bvh) horneadas sobre la malla base con los pesos del
    esqueleto por defecto: {nombre: (índices, desplazamientos en dm del marco de MakeHuman)}."""
    d = asegurar()
    nombres = json.loads((d / "poseunits" / "face-poseunits.json").read_text())["framemapping"]
    juntas, vals = _leer_bvh(d / "poseunits" / "face-poseunits.bvh")
    v = base()["v"]
    vb = np.stack([v[:, 0], -v[:, 2], v[:, 1]], axis=1)          # malla al marco del BVH (Z arriba)
    rest = []
    for j in juntas:
        rest.append(j["offset"] if j["padre"] < 0 else rest[j["padre"]] + j["offset"])
    rest = np.array(rest)
    pw = json.loads((d / "rigs" / "default_weights.mhw").read_text())["weights"]
    nombre_a_j = {j["nombre"]: i for i, j in enumerate(juntas) if j["nombre"]}
    W = np.zeros((len(vb), len(juntas)))
    for hueso, lista in pw.items():
        if hueso in nombre_a_j:
            a = np.array(lista)
            W[a[:, 0].astype(np.int64), nombre_a_j[hueso]] = a[:, 1]
    tot = W.sum(axis=1)
    W[tot > 0] /= tot[tot > 0, None]
    salida = {}
    for f, nombre in enumerate(nombres):
        if nombre == "Rest":
            continue
        G_R, G_p = [], []
        col = 0
        for j in juntas:
            R = np.eye(3)
            for c in j.get("canales", []):
                if c.endswith("rotation"):
                    R = R @ _rot(c[0], vals[f, col])
                col += 1
            if j["padre"] < 0:
                Rg, pg = R, j["offset"]
            else:
                Rp, pp = G_R[j["padre"]], G_p[j["padre"]]
                Rg, pg = Rp @ R, pp + Rp @ j["offset"]
            G_R.append(Rg)
            G_p.append(pg)
        delta = np.zeros_like(vb)
        for ji, j in enumerate(juntas):
            if not j["nombre"]:
                continue
            dR = G_R[ji] - np.eye(3)
            dp = G_p[ji] - rest[ji]
            if np.abs(dR).max() < 1e-9 and np.abs(dp).max() < 1e-9:
                continue
            m = W[:, ji] > 0
            if m.any():
                delta[m] += W[m, ji, None] * ((vb[m] - rest[ji]) @ dR.T + dp)
        mov = np.linalg.norm(delta, axis=1) > 1e-5
        dd = delta[mov]
        salida[nombre] = (np.nonzero(mov)[0], np.stack([dd[:, 0], dd[:, 2], -dd[:, 1]], axis=1))
    return salida
