"""Manifiesto de una versión de producción (SALIDA del AutoFinisher, formato «estudio.version_blend/1»), sin bpy.

Cada versión es INMUTABLE: se identifica por `produccion` + `version` (entero), su Release propia
(`blend-<produccion>-v<NNN>`) y los SHA-256 de sus archivos. Cualquier cambio (receta, GLB, scripts) es una versión
nueva; los flujos se niegan a publicar sobre una Release que ya existe y el render verifica el hash del .blend antes
de abrirlo.

Archivos de una versión (todos en su Release):
  <produccion>_v<NNN>.blend            proyecto Blender autónomo (texturas empaquetadas)
  <produccion>_v<NNN>.glb              lo que exportó Godot (para auditar o reconstruir)
  manifest.json                         este manifiesto
  informe_preparacion.json              tiempos, RAM, inspección y correcciones del AutoFinisher
"""
from __future__ import annotations

import datetime
import json
from pathlib import Path

from estudio.autofinisher import medicion as MD

FORMATO = "estudio.version_blend/1"
ESTADOS_REVISION = ("sin revisar", "en revisión", "aprobada", "rechazada")


def id_version(produccion: str, version: int) -> str:
    return f"{produccion}_v{int(version):03d}"


def tag_release(produccion: str, version: int) -> str:
    return f"blend-{produccion}-v{int(version):03d}"


def nombres(produccion: str, version: int) -> dict:
    b = id_version(produccion, version)
    return {"blend": f"{b}.blend", "glb": f"{b}.glb", "manifiesto": "manifest.json", "informe": "informe_preparacion.json"}


def construir(receta: dict, version: int, blend: Path, glb: Path, informe: Path | None, empaque: dict,
              versiones: dict, receta_sha256: str) -> dict:
    es, rd = receta["escena"], receta["render"]
    m = {
        "formato": FORMATO,
        "produccion": receta["produccion"],
        "version": int(version),
        "id": id_version(receta["produccion"], version),
        "release": tag_release(receta["produccion"], version),
        "titulo": receta.get("titulo", ""),
        "construido": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "archivos": {"blend": MD.archivo(blend), "glb": MD.archivo(glb)},
        "render": {
            "motor": rd["motor"], "dispositivo": rd["dispositivo"], "resolucion": rd["resolucion"],
            "fps": es["fps"], "cuadro_inicial": es["cuadro_inicial"], "cuadro_final": es["cuadro_final"],
            "cuadros": es["cuadro_final"] - es["cuadro_inicial"] + 1, "numeracion_archivos": "1..N (f_0001.png)",
            "muestras": rd["muestras"], "muestreo_adaptativo": rd["muestreo_adaptativo"], "denoiser": rd["denoiser"],
            "rebotes": rd["rebotes"], "arbol_de_luces": rd["arbol_de_luces"], "camara": es.get("camara"),
        },
        "dependencias": {"empaquetadas": empaque.get("empaquetados", []), "externas": empaque.get("externos", [])},
        "versiones": {**versiones, "receta_sha256": receta_sha256},
        "revision": {"estado": "sin revisar"},
    }
    if informe is not None and Path(informe).exists():
        m["archivos"]["informe"] = {"nombre": Path(informe).name, "bytes": Path(informe).stat().st_size}
    return m


def errores(m: dict) -> list[str]:
    e = []
    if m.get("formato") != FORMATO:
        e.append(f"formato: se esperaba «{FORMATO}»")
    for k in ("produccion", "version", "id", "release", "archivos", "render", "dependencias", "versiones"):
        if k not in m:
            e.append(f"falta «{k}»")
    if e:
        return e
    if m["id"] != id_version(m["produccion"], m["version"]) or m["release"] != tag_release(m["produccion"], m["version"]):
        e.append("id o release no corresponden a produccion + version")
    b = m["archivos"].get("blend", {})
    if len(str(b.get("sha256", ""))) != 64:
        e.append("archivos.blend.sha256 falta o no es un SHA-256")
    if m["dependencias"].get("externas"):
        e.append(f"hay recursos externos sin empaquetar: {m['dependencias']['externas']}")
    r = m["render"]
    if r.get("cuadros") != r.get("cuadro_final", 0) - r.get("cuadro_inicial", 0) + 1:
        e.append("render.cuadros no coincide con el rango")
    if m.get("revision", {}).get("estado") not in ESTADOS_REVISION:
        e.append(f"revision.estado debe ser uno de {ESTADOS_REVISION}")
    return e


def verificar_blend(m: dict, ruta_blend: str | Path) -> tuple[bool, str]:
    """¿El .blend descargado es exactamente el de esta versión? (tamaño y SHA-256)."""
    b = m["archivos"]["blend"]
    p = Path(ruta_blend)
    if not p.exists():
        return False, f"no está {p}"
    if p.stat().st_size != b["bytes"]:
        return False, f"tamaño {p.stat().st_size} ≠ {b['bytes']} del manifiesto"
    h = MD.sha256(p)
    if h != b["sha256"]:
        return False, f"SHA-256 {h} ≠ {b['sha256']} del manifiesto"
    return True, f"{p.name}: {b['bytes']} bytes, SHA-256 {h} (= manifiesto {m['id']})"


def leer(ruta: str | Path) -> dict:
    """Manifiesto de una versión: el del AutoFinisher o el de una escena aprobada del estudio
    (`estudio.version_escena/1`, estudio/version_escena.py). Los dos traen archivos.blend y render con el mismo
    significado, así que el render por trozos y la verificación del BLEND sirven para ambos."""
    m = json.loads(Path(ruta).read_text())
    if m.get("formato") == "estudio.version_escena/1":
        from estudio import version_escena as VE
        return VE.leer(ruta)
    e = errores(m)
    if e:
        raise ValueError(f"manifiesto {ruta} inválido: " + "; ".join(e))
    return m
