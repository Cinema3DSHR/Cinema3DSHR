"""Protección de lo entregado: una versión de escena que ya se le dio al dueño (previsualización GLB + JSON, render)
NO se vuelve a escribir. Se registra con sus huellas (sha256) en `entregado.json`, al lado de su escena.json; desde ahí:

- `exigir_escritura(ruta)` corta cualquier herramienta que quiera sobrescribir esa receta (MF.escribir y los armadores
  de las producciones lo llaman);
- `verificar(ruta)` comprueba que la receta y los archivos entregados que estén a mano siguen intactos.

Una corrección es una versión nueva (`python -m estudio nueva-version`) o una copia de trabajo (escena de trabajo,
`estudio/blender/trabajo.py`), nunca una edición de lo entregado. Sin bpy: lo usan el planificador y las pruebas.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

from estudio import config

NOMBRE = "entregado.json"


def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def _rel(p: Path) -> str:
    p = Path(p).resolve()
    try:
        return str(p.relative_to(config.RAIZ))
    except ValueError:
        return str(p)


def registro(ruta_escena: Path) -> dict | None:
    r = Path(ruta_escena).parent / NOMBRE
    return json.loads(r.read_text()) if r.exists() else None


def motivo_proteccion(ruta_escena: Path) -> str | None:
    """Por qué no se puede escribir esta receta (None = se puede)."""
    ruta_escena = Path(ruta_escena)
    reg = registro(ruta_escena)
    if reg:
        return f"entregada al dueño el {reg.get('fecha', '?')} ({reg.get('nota', '')}); huella {reg.get('huella')}"
    if ruta_escena.exists():
        try:
            m = json.loads(ruta_escena.read_text())
        except json.JSONDecodeError:
            return None
        if m.get("bloqueada"):
            return "versión bloqueada (aprobada)"
    return None


def exigir_escritura(ruta_escena: Path):
    motivo = motivo_proteccion(ruta_escena)
    if motivo:
        raise PermissionError(f"{_rel(ruta_escena)} está protegida: {motivo}. Las correcciones van en una versión nueva "
                              f"(python -m estudio nueva-version) o en una copia de trabajo.")


def registrar(ruta_escena: Path, archivos: list[Path], nota: str = "") -> Path:
    """Registra lo entregado de esta versión (la receta + los derivados que se le dieron al dueño)."""
    from estudio import manifiesto as MF
    ruta_escena = Path(ruta_escena)
    m = MF.leer(ruta_escena)
    reg = {"fecha": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "nota": nota,
           "produccion": m["produccion"], "escena": m["id"].split("-")[-1], "version": m["version"],
           "huella": MF.huella(m),
           "receta": {"ruta": _rel(ruta_escena), "sha256": sha256(ruta_escena)},
           "derivados": [{"nombre": Path(a).name, "bytes": Path(a).stat().st_size, "sha256": sha256(Path(a)),
                          "ruta_al_entregar": _rel(a)} for a in archivos],
           "regla": "No se sobrescribe la receta ni estos archivos. Correcciones = versión nueva o copia de trabajo."}
    out = ruta_escena.parent / NOMBRE
    out.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n")
    return out


def verificar(ruta_escena: Path, buscar_en: list[Path] | None = None) -> list[str]:
    """Problemas encontrados (vacío = intacto). Los derivados se buscan por nombre en `buscar_en` y en su ruta
    original; los que no estén a mano se informan como «no disponible» (no es un error: viven fuera de Git)."""
    ruta_escena = Path(ruta_escena)
    reg = registro(ruta_escena)
    if not reg:
        return [f"{_rel(ruta_escena)}: sin registro de entrega"]
    out = []
    if sha256(ruta_escena) != reg["receta"]["sha256"]:
        out.append(f"LA RECETA CAMBIÓ: {_rel(ruta_escena)} no coincide con lo entregado")
    for d in reg["derivados"]:
        cands = [config.RAIZ / d["ruta_al_entregar"]] + [Path(b) / d["nombre"] for b in (buscar_en or [])]
        hallado = next((c for c in cands if c.exists()), None)
        if hallado is None:
            out.append(f"no disponible acá: {d['nombre']} (no es un error)")
        elif sha256(hallado) != d["sha256"]:
            out.append(f"EL DERIVADO CAMBIÓ: {hallado}")
    return out
