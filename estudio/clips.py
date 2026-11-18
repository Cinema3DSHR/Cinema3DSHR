"""Biblioteca de clips de animación (catalogo/animaciones.json, 6.515 clips): buscar con la DESCRIPCIÓN de cada uno y
avisar cuando una receta usa un clip con estilo marcado. Sin bpy.

La descripción manda: dos clips con el mismo nombre («Walking») pueden ser una caminata normal o la de un borracho
(«Walking_2» = «Male Drunk Walk»; pasó en «A la deriva» E02 v1). Antes de elegir un clip: `python -m estudio clips
buscar caminar` y mirar su ficha (`clips ficha`, estudio/blender/ficha_clip.py).
"""
from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache

from estudio import config

# estilos que cambian el carácter del personaje: se usan sólo si la escena lo pide
ESTILOS_MARCADOS = ["drunk", "borracho", "injured", "herido", "brutal", "sexy", "boxing", "boxeo", "zombie", "orc",
                    "dwarf", "enano", "clown", "payaso", "old man", "anciano", "sneak", "sigil", "crouch", "agach",
                    "carrying", "lleva a alguien", "rifle", "torch", "antorcha", "drunk", "dizzy", "mareado", "strut",
                    "swagger", "catwalk", "walker", "iv pole", "happy", "feliz", "careful", "cuidado", "hurried",
                    "apurad", "tough", "pistol", "sword", "espada", "vegas"]


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", s)


@lru_cache(maxsize=1)
def catalogo() -> dict:
    d = json.loads((config.CATALOGO / "animaciones.json").read_text())
    return {c["ref"]: c for c in d["clips"]}


@lru_cache(maxsize=1)
def _analisis() -> dict:
    p = config.CATALOGO / "analisis_animaciones.json"
    return {a["id"]: a for a in json.loads(p.read_text())} if p.exists() else {}


def ficha(ref: str) -> dict | None:
    c = catalogo().get(ref)
    if not c:
        return None
    a = _analisis().get(c["id"], {})
    out = dict(c)
    if a.get("desplazamiento_cadera_m") is not None:
        out["desplazamiento_cadera_m"] = a["desplazamiento_cadera_m"]
    out["estilo_marcado"] = estilo(c)
    return out


def estilo(c: dict) -> list[str]:
    """Palabras de estilo marcado que aparecen en la descripción (vacío = neutro)."""
    txt = _norm(" ".join(str(c.get(k, "")) for k in ("descripcion", "descripcion_en", "nombre")))
    return sorted({e for e in ESTILOS_MARCADOS if re.search(r"\b" + re.escape(e), txt)})   # al comienzo de palabra


def buscar(texto: str = "", funcion: str = "", sin_estilo: bool = False, limite: int = 40) -> list[dict]:
    q = _norm(texto)
    out = []
    for c in catalogo().values():
        if funcion and funcion not in (c.get("funciones") or []):
            continue
        campo = _norm(" ".join(str(c.get(k, "")) for k in ("ref", "nombre", "descripcion", "descripcion_en", "grupo")))
        if q and not all(p in campo for p in q.split()):
            continue
        e = estilo(c)
        if sin_estilo and e:
            continue
        out.append({"ref": c["ref"], "descripcion": c.get("descripcion"), "en": c.get("descripcion_en"),
                    "duracion_s": c.get("duracion_s"), "en_el_lugar": c.get("en_el_lugar"), "estilo": e,
                    "postura": c.get("postura"), "arma": c.get("arma")})
    out.sort(key=lambda x: (bool(x["estilo"]), x["ref"]))
    return out[:limite]


def avisos_receta(m: dict) -> list[str]:
    """Clips de la receta con estilo marcado (para que alguien lo confirme a propósito)."""
    out, vistos = [], set()
    for pj in m.get("personajes", []):
        for ac in pj.get("acciones", []):
            ref = ac.get("clip", "")
            if ref in vistos:
                continue
            vistos.add(ref)
            c = catalogo().get(ref)
            if c and estilo(c) and not ac.get("estilo_confirmado"):
                out.append(f"{pj['id']}: el clip {ref.split('/')[-1]} es «{c.get('descripcion_en') or c.get('descripcion')}» "
                           f"(estilo: {', '.join(estilo(c))}); si es a propósito, poné \"estilo_confirmado\": true")
    return out
