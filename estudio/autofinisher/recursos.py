"""Baja los recursos externos que necesita el proyecto de Godot de una receta (godot.recursos[]), sin bpy.

Cada recurso: {"repo": "dueño/nombre", "ref": "rama o commit", "archivos": [rutas dentro del repo], "destino": carpeta}.
Usa un clon superficial y disperso (sólo esos archivos). Para repositorios privados toma el token de ASSETS_TOKEN
(nunca se imprime). Mide tiempo y tamaño de cada descarga.

    python -m estudio.autofinisher.recursos --receta R.json [--raiz .]
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from estudio.autofinisher import receta as RC


def bajar(recurso: dict, raiz: Path) -> dict:
    t = time.time()
    token = os.environ.get("ASSETS_TOKEN", "")
    url = f"https://github.com/{recurso['repo']}.git"
    if token:
        url = f"https://x-access-token:{token}@github.com/{recurso['repo']}.git"
    destino = raiz / recurso["destino"]
    destino.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as d:
        def git(*a):
            r = subprocess.run(["git", *a], cwd=d, capture_output=True, text=True)
            if r.returncode:
                raise RuntimeError(f"git {a[0]} falló para {recurso['repo']}: {r.stderr.replace(token, '***')[-400:]}")
        git("clone", "--depth", "1", "--filter=blob:none", "--sparse", "--branch", recurso.get("ref", "main"), url, "r")
        subprocess.run(["git", "-C", "r", "sparse-checkout", "set", "--no-cone", *recurso["archivos"]], cwd=d,
                       check=True, capture_output=True)
        total = 0
        for a in recurso["archivos"]:
            src = Path(d) / "r" / a
            if not src.exists():
                raise FileNotFoundError(f"{recurso['repo']}@{recurso.get('ref', 'main')} no tiene {a}")
            shutil.copy2(src, destino / src.name)
            total += src.stat().st_size
    return {"repo": recurso["repo"], "ref": recurso.get("ref", "main"), "archivos": len(recurso["archivos"]),
            "mb": round(total / 1e6, 2), "segundos": round(time.time() - t, 2), "destino": recurso["destino"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--receta", required=True)
    ap.add_argument("--raiz", default=".")
    a = ap.parse_args()
    r = RC.leer(a.receta)
    out = [bajar(x, Path(a.raiz)) for x in r.get("godot", {}).get("recursos", [])]
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
