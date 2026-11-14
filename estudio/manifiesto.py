"""Manifiestos de producción: carga, validación, versiones, huella de render y bloqueo de escenas aprobadas.

Estructura en disco (todo texto, versionado en Git):
  producciones/<prod>/produccion.json
  producciones/<prod>/escenas/<eNN>/v<k>/escena.json     ← receta editable de la versión k
  escenarios/<id>/escenario.json                          ← escenarios reutilizables (receta + generador)

Reglas:
- Una versión publicada no se edita: los cambios van en una versión nueva (`nueva_version`).
- Una versión APROBADA queda bloqueada ("bloqueada": true) y el render la rechaza salvo --forzar explícito.
- La huella (sha256 de la receta + versión del código de los generadores) decide si hace falta volver a renderizar.
"""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
from estudio import config

TIPOS_TOMA = {"estatica", "general", "dolly", "paneo", "grua", "orbita", "seguimiento", "detalle", "vigilancia",
              "subjetiva"}
ESTADOS = ["borrador", "renderizando", "en_revision", "aprobada", "rechazada", "correcciones", "reemplazada"]


def leer(ruta: Path) -> dict:
    return json.loads(Path(ruta).read_text(encoding="utf-8"))


def escribir(ruta: Path, datos: dict):
    Path(ruta).parent.mkdir(parents=True, exist_ok=True)
    Path(ruta).write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ruta_escena(prod: str, escena: str, version: int) -> Path:
    return config.PRODUCCIONES / prod / "escenas" / escena / f"v{version}" / "escena.json"


def versiones(prod: str, escena: str) -> list[int]:
    d = config.PRODUCCIONES / prod / "escenas" / escena
    return sorted(int(p.name[1:]) for p in d.glob("v*") if p.name[1:].isdigit() and (p / "escena.json").exists())


def validar(m: dict) -> list[str]:
    """Devuelve la lista de errores (vacía = válido)."""
    err = []
    for k in ("id", "produccion", "version", "titulo", "duracion_s", "escenario", "tomas"):
        if k not in m:
            err.append(f"falta '{k}'")
    if err:
        return err
    fin = 0.0
    ids = set()
    for t in sorted(m["tomas"], key=lambda t: t["inicio_s"]):
        if t["id"] in ids:
            err.append(f"toma repetida {t['id']}")
        ids.add(t["id"])
        if t.get("tipo") not in TIPOS_TOMA:
            err.append(f"{t['id']}: tipo '{t.get('tipo')}' desconocido ({sorted(TIPOS_TOMA)})")
        if abs(t["inicio_s"] - fin) > 1e-6:
            err.append(f"{t['id']}: empieza en {t['inicio_s']} s pero la toma anterior termina en {fin} s")
        fin = t["inicio_s"] + t["duracion_s"]
        if t.get("tipo") in ("seguimiento", "detalle", "subjetiva") and not t.get("movil"):
            err.append(f"{t['id']}: las tomas de {t['tipo']} necesitan 'movil'")
    if abs(fin - m["duracion_s"]) > 1e-6:
        err.append(f"las tomas suman {fin} s y la escena dura {m['duracion_s']} s")
    gen = m["escenario"].get("generador")
    if not gen or not (config.RAIZ / "estudio" / "escenarios" / f"{gen}.py").exists():
        err.append(f"generador de escenario '{gen}' inexistente")
    movs = {v["id"] for v in m.get("vehiculos", [])} | {p["id"] for p in m.get("personajes", [])}
    if m.get("pelota"):
        movs.add("pelota")
    for t in m["tomas"]:
        if t.get("movil") and t["movil"] not in movs:
            err.append(f"{t['id']}: móvil '{t['movil']}' no definido")
    return err


def huella(m: dict) -> str:
    """sha256 de lo que define la imagen: receta sin metadatos de estado + código de los generadores usados."""
    receta = {k: v for k, v in m.items() if k not in ("estado", "bloqueada", "salidas", "historial", "notas")}
    h = hashlib.sha256(json.dumps(receta, sort_keys=True, ensure_ascii=False).encode())
    for rel in ("estudio/blender/kit.py", "estudio/blender/camaras.py", "estudio/blender/vehiculos.py",
                "estudio/blender/director.py", f"estudio/escenarios/{m['escenario']['generador']}.py"):
        p = config.RAIZ / rel
        if p.exists():
            h.update(p.read_bytes())
    return h.hexdigest()[:16]


def nueva_version(prod: str, escena: str, motivo: str = "") -> Path:
    """Copia la última versión a v<k+1> (estado borrador) para aplicar correcciones sin tocar la anterior."""
    vs = versiones(prod, escena)
    if not vs:
        raise FileNotFoundError(f"No hay versiones de {prod}/{escena}")
    actual = leer(ruta_escena(prod, escena, vs[-1]))
    nueva = copy.deepcopy(actual)
    nueva["version"] = vs[-1] + 1
    nueva["estado"] = "borrador"
    nueva["bloqueada"] = False
    nueva.pop("salidas", None)
    nueva.setdefault("historial", []).append({"desde_version": vs[-1], "motivo": motivo})
    destino = ruta_escena(prod, escena, nueva["version"])
    escribir(destino, nueva)
    return destino


def puede_renderizar(m: dict, forzar: bool = False) -> tuple[bool, str]:
    if m.get("bloqueada") and not forzar:
        return False, f"{m['id']} v{m['version']} está APROBADA y bloqueada: crear una versión nueva para cambiarla"
    return True, ""


def dependencias(m: dict) -> list[str]:
    """Recursos externos ("fuente:ruta") que necesita la escena: sirven para bajar SÓLO eso en Actions.
    Lee la lista DEPENDENCIAS del generador sin importarlo (el planificador no tiene Blender)."""
    import ast
    from estudio.blender_deps import MODELOS_DEPS
    deps = set()
    src = (config.RAIZ / "estudio" / "escenarios" / f"{m['escenario']['generador']}.py").read_text(encoding="utf-8")
    for nodo in ast.parse(src).body:
        if isinstance(nodo, ast.Assign) and any(getattr(t, "id", "") == "DEPENDENCIAS" for t in nodo.targets):
            deps.update(ast.literal_eval(nodo.value))
    for pj in m.get("personajes", []):
        deps.update(MODELOS_DEPS.get(pj.get("modelo", "futbol:jugador"), []))
        deps.update(a["clip"] for a in pj.get("acciones", []) if str(a.get("clip", "")).startswith("mixamo:"))
    return sorted(deps)
