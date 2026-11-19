"""Mediciones comunes: tiempos por etapa, RAM máxima del proceso y tamaños de archivos (sin bpy)."""
from __future__ import annotations

import contextlib
import hashlib
import os
import resource
import time
from pathlib import Path


def ram_max_mb() -> float:
    """RAM máxima (resident set) del proceso hasta ahora. En Linux ru_maxrss viene en KiB. Cycles corre dentro del
    mismo proceso de Blender, así que incluye la memoria del render."""
    return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0, 1)


def ram_hijos_max_mb() -> float:
    return round(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1024.0, 1)


def sha256(ruta: str | Path, bloque: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for b in iter(lambda: f.read(bloque), b""):
            h.update(b)
    return h.hexdigest()


def archivo(ruta: str | Path) -> dict:
    p = Path(ruta)
    return {"nombre": p.name, "bytes": p.stat().st_size, "mb": round(p.stat().st_size / 1e6, 2), "sha256": sha256(p)}


class Cronometro:
    """Etapas con su duración y la RAM máxima al terminar cada una."""

    def __init__(self):
        self.t0 = time.time()
        self.etapas: dict[str, dict] = {}

    @contextlib.contextmanager
    def etapa(self, nombre: str):
        t = time.time()
        reg = {"inicio_s": round(t - self.t0, 3)}
        self.etapas[nombre] = reg
        try:
            yield reg
            reg["estado"] = "ok"
        except BaseException as e:
            reg["estado"] = "error"
            reg["error"] = f"{type(e).__name__}: {e}"[:500]
            raise
        finally:
            reg["segundos"] = round(time.time() - t, 3)
            reg["ram_max_mb"] = ram_max_mb()

    def total(self) -> float:
        return round(time.time() - self.t0, 3)


def entorno() -> dict:
    """Datos de la máquina (para comparar corridas): CPU, núcleos, RAM total, si es GitHub Actions."""
    d = {"nucleos": os.cpu_count(), "actions": bool(os.environ.get("GITHUB_ACTIONS")),
         "corrida": os.environ.get("GITHUB_RUN_ID"), "intento": os.environ.get("GITHUB_RUN_ATTEMPT"),
         "trabajo": os.environ.get("GITHUB_JOB")}
    try:
        for linea in Path("/proc/meminfo").read_text().splitlines():
            if linea.startswith("MemTotal:"):
                d["ram_total_mb"] = round(int(linea.split()[1]) / 1024)
        for linea in Path("/proc/cpuinfo").read_text().splitlines():
            if linea.startswith("model name"):
                d["cpu"] = linea.split(":", 1)[1].strip()
                break
    except OSError:
        pass
    return d
