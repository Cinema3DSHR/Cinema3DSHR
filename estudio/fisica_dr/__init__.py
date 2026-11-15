"""Física REAL de Dream Rally para las películas.

`simular(plan)` corre `grabar.gd` con Godot (sin cabeza) sobre los archivos de física del juego tal cual están en
Rally-Sim-movile (`godot/game/physics/*.gd`, `godot/game/data/car_build.gd`, `vehicles.json`) y devuelve, por vehículo
y por cuadro, la posición y orientación de la carrocería, la altura de cada rueda (suspensión), su giro, la dirección,
la velocidad, el régimen y el deslizamiento de cada goma.

El resultado se guarda en `datos/fisica_dr/<huella>.json.gz` (texto comprimido, chico) y se versiona: así los flujos de
Actions reproducen exactamente la misma simulación sin instalar Godot. La huella depende del plan y del grabador; el
archivo anota además la huella de los archivos de física del juego que se usaron (procedencia).
"""
from __future__ import annotations
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from estudio import config

AQUI = Path(__file__).resolve().parent
CACHE = config.RAIZ / "datos" / "fisica_dr"
VERSION = 2
ARCHIVOS_JUEGO = ["godot/game/physics/vehicle_physics.gd", "godot/game/physics/vehicle_params.gd",
                  "godot/game/physics/track_base.gd", "godot/game/data/car_build.gd", "godot/game/data/vehicles.json"]


def _huella(plan: dict) -> str:
    h = hashlib.sha256()
    limpio = json.loads(json.dumps(plan))
    for v in limpio.get("vehiculos", []):
        v.get("cabina", {}).pop("glb", None)
        for pil in v.get("cabina", {}).get("pilotos", []):
            pil.pop("glb", None)
    h.update(json.dumps(limpio, sort_keys=True, separators=(",", ":")).encode())
    h.update((AQUI / "grabar.gd").read_bytes())
    h.update(str(VERSION).encode())
    return h.hexdigest()[:20]


def _raiz_rally() -> Path:
    return config.resolver("rally:godot/game/physics/vehicle_physics.gd").parents[3]


def _procedencia(rally: Path) -> dict:
    out = {}
    for rel in ARCHIVOS_JUEGO:
        out[rel] = hashlib.sha256((rally / rel).read_bytes()).hexdigest()
    try:
        out["commit"] = subprocess.run(["git", "-C", str(rally), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    except Exception:
        pass
    return out


def _convertir_personaje(ref: str, destino: Path):
    import sys
    r = subprocess.run([os.environ.get("CINE_BPY_PYTHON", sys.executable), "-I", str(AQUI / "convertir_personaje.py"), ref,
                        str(destino)], capture_output=True, text=True, timeout=900)
    if not destino.exists():
        raise RuntimeError("fisica_dr: no se pudo convertir el personaje " + ref + "\n" + (r.stdout + r.stderr)[-2000:])


def _correr_godot(plan: dict) -> dict:
    godot = shutil.which(os.environ.get("CINE_GODOT", "godot"))
    if not godot:
        raise RuntimeError("fisica_dr: falta la simulación en caché y no hay Godot para correrla (simular localmente y subir datos/fisica_dr)")
    rally = _raiz_rally()
    with tempfile.TemporaryDirectory(prefix="fisica_dr_") as tmp:
        t = Path(tmp)
        (t / "project.godot").write_text('config_version=5\n[application]\nconfig/name="fisica_dr"\n')
        (t / "game").mkdir()
        (t / "game" / "physics").symlink_to(rally / "godot/game/physics", target_is_directory=True)
        (t / "game" / "data").symlink_to(rally / "godot/game/data", target_is_directory=True)
        (t / "game" / "car").symlink_to(rally / "godot/game/car", target_is_directory=True)
        shutil.copy(AQUI / "grabar.gd", t / "grabar.gd")
        (t / "plan.json").write_text(json.dumps(plan))
        if any("cabina" in v for v in plan["vehiculos"]):
            # la cabina usa los modelos del piloto, el volante y las medidas de cada auto: sólo eso se importa
            mod = rally / "godot/game/models"
            (t / "game" / "models" / "cars").mkdir(parents=True)
            for n in ("pilot.glb", "pilot_lo.glb", "cabin", "paint"):
                (t / "game" / "models" / n).symlink_to(mod / n, target_is_directory=(mod / n).is_dir())
            tipos = {str(v["cabina"]["tipo"]) for v in plan["vehiculos"] if "cabina" in v}
            for f in (mod / "cars").iterdir():
                # el habitáculo se mide sobre el modelo del auto (CabinCfg exige que exista su GLB)
                if f.suffix in (".json", ".png") or (f.suffix == ".glb" and f.stem.replace("_lo", "") in tipos):
                    (t / "game" / "models" / "cars" / f.name).symlink_to(f)
            # protagonistas sentados en la cabina: el personaje del estudio pasado a GLB (pose de reposo)
            (t / "game" / "models" / "protas").mkdir()
            for v in plan["vehiculos"]:
                for k, pil in enumerate(v.get("cabina", {}).get("pilotos", [])):
                    destino = t / "game" / "models" / "protas" / f"{v['id']}_{k}.glb"
                    _convertir_personaje(pil["ref"], destino)
                    pil["glb"] = f"res://game/models/protas/{destino.name}"
            (t / "plan.json").write_text(json.dumps(plan))
            subprocess.run([godot, "--headless", "--path", str(t), "--import"], capture_output=True, text=True, timeout=1800)
        r = subprocess.run([godot, "--headless", "--path", str(t), "--script", "res://grabar.gd", "--",
                            str(t / "plan.json"), str(t / "salida.json")], capture_output=True, text=True, timeout=1800)
        if r.returncode != 0 or not (t / "salida.json").exists() or "SCRIPT ERROR" in r.stderr + r.stdout:
            raise RuntimeError("fisica_dr: Godot falló\n" + (r.stdout + r.stderr)[-3000:])
        res = json.loads((t / "salida.json").read_text())
    res["procedencia"] = _procedencia(rally)
    return res


def simular(plan: dict) -> dict:
    """Corre (o lee de la caché) la simulación. Los vehículos con "cabina": {"tipo", "pintura", "acento"} además
    exportan su habitáculo con los pilotos animados a un GLB (en config.SALIDA: no va a Git); su ruta queda en
    resultado["vehiculos"][id]["cabina"]."""
    hu = _huella(plan)
    arch = CACHE / f"{hu}.json.gz"
    glbs = {v["id"]: str(config.SALIDA / "fisica_dr" / f"{hu}_{v['id']}.glb") for v in plan["vehiculos"] if "cabina" in v}
    if arch.exists() and all(Path(g).exists() for g in glbs.values()):
        return json.loads(gzip.decompress(arch.read_bytes()))
    if glbs:
        (config.SALIDA / "fisica_dr").mkdir(parents=True, exist_ok=True)
        plan = json.loads(json.dumps(plan))
        for v in plan["vehiculos"]:
            if v["id"] in glbs:
                v["cabina"]["glb"] = glbs[v["id"]]
    res = _correr_godot(plan)
    res["huella"] = hu
    CACHE.mkdir(parents=True, exist_ok=True)
    arch.write_bytes(gzip.compress(json.dumps(res, separators=(",", ":")).encode(), 9, mtime=0))
    return res


def horario_constante(s0: float, v: float, duracion: float, previo: float = 3.0) -> list:
    return [[-previo - 1.0, s0 - v * (previo + 1.0)], [duracion + 1.0, s0 + v * (duracion + 1.0)]]


def horario_por_velocidades(s0: float, tramos: list, previo: float = 3.0) -> list:
    """tramos: [(t, v)] con la velocidad objetivo en cada instante (lineal entre puntos). Integra s(t) cada 0,1 s."""
    out = []
    t0, v0 = tramos[0]
    t, s = t0 - previo - 1.0, s0 - v0 * (previo + 1.0)
    tf = tramos[-1][0] + 1.0
    def vel(tt):
        if tt <= tramos[0][0]:
            return tramos[0][1]
        for (ta, va), (tb, vb) in zip(tramos, tramos[1:]):
            if tt <= tb:
                return va + (vb - va) * (tt - ta) / max(1e-6, tb - ta)
        return tramos[-1][1]
    while t <= tf:
        out.append([round(t, 3), round(s, 4)])
        s += vel(t) * 0.1
        t += 0.1
    return out
