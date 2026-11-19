"""AutoReport (bpy): versiones de las herramientas y armado del informe de preparación."""
from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import bpy

from estudio import autofinisher as AF
from estudio.autofinisher import medicion as MD

RAIZ = Path(__file__).resolve().parents[2]


def huella_scripts() -> str:
    """SHA-256 del código del AutoFinisher (para saber con qué scripts se armó cada versión)."""
    h = hashlib.sha256()
    for p in sorted((RAIZ / "estudio" / "autofinisher").rglob("*.py")):
        h.update(str(p.relative_to(RAIZ)).encode())
        h.update(p.read_bytes())
    return h.hexdigest()


def commit() -> str | None:
    try:
        r = subprocess.run(["git", "-C", str(RAIZ), "rev-parse", "HEAD"], capture_output=True, text=True, timeout=10)
        return r.stdout.strip() or None
    except Exception:
        return None


def versiones(godot: str | None) -> dict:
    return {"blender": bpy.app.version_string, "godot": godot, "autofinisher": AF.VERSION,
            "scripts_sha256": huella_scripts(), "git_commit": commit()}


def informe(cron: MD.Cronometro, etapas: dict, extra: dict) -> dict:
    return {"formato": "estudio.informe_preparacion/1", "etapas": cron.etapas, "resultados": etapas,
            "segundos_total": cron.total(), "ram_max_mb": MD.ram_max_mb(), "entorno": MD.entorno(), **extra}
