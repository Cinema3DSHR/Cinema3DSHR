"""Verificación de recursos de una receta ANTES de preparar una escena (sin bpy).

Comprueba que existe y se puede abrir todo lo que la receta nombra:
  - audios de las líneas (personajes → cara → habla[].audio), de los eventos (p. ej. eva_habla) y las marcas de tiempo
    por letra (alineacion): el archivo existe, ffprobe lo abre y dura más de 0 s; el JSON de marcas se lee;
  - audios de la mezcla (sonido.eventos: voz / música / efecto generados con ElevenLabs): están en la biblioteca;
  - recursos externos «fuente:ruta» (clips de Mixamo, modelos, pelos, muebles de Sweet Home…): existen.
Si falta algo obligatorio se informa y la preparación se detiene: NUNCA se reemplaza un audio real por sílabas
inventadas ni un recurso por otro. Las rutas absolutas viejas (recetas de Dúo Cero) se resuelven con
`config.ruta_recurso` y quedan como aviso.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from estudio import config


class RecursoFaltante(RuntimeError):
    pass


def _audios(m: dict) -> list[tuple[str, str, str]]:
    """(dónde, clave, ruta) de cada audio / marca de tiempo nombrado por la receta (fuera de `sonido`)."""
    out = []
    for pj in m.get("personajes", []):
        for i, h in enumerate((pj.get("cara") or {}).get("habla", [])):
            for k in ("audio", "alineacion"):
                if isinstance(h.get(k), str):
                    out.append((f"personaje {pj['id']} · habla[{i}]", k, h[k]))
    for ev in m.get("eventos", []):
        for i, ln in enumerate(ev.get("lineas", []) or []):
            for k in ("audio", "alineacion"):
                if isinstance(ln.get(k), str):
                    out.append((f"evento {ev.get('accion')} · línea {i}", k, ln[k]))
    return out


def _abre_audio(p: Path) -> str | None:
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(p)],
                           capture_output=True, text=True, timeout=30)
        d = float(json.loads(r.stdout or "{}").get("format", {}).get("duration", 0) or 0)
        return None if d > 0 else "no se puede abrir (o dura 0 s)"
    except (subprocess.SubprocessError, ValueError, json.JSONDecodeError) as e:
        return f"no se puede abrir ({e})"


def verificar(m: dict, externos: bool = True, mezcla: bool = True) -> tuple[list[str], list[str]]:
    """(errores, avisos). externos: también los recursos «fuente:ruta»; mezcla: también los audios de `sonido`."""
    errores, avisos = [], []
    vistos = set()
    for donde, k, ruta in _audios(m):
        if config.es_absoluta(ruta):
            avisos.append(f"{donde}: ruta absoluta de otra máquina ({ruta}); se resuelve relativa a la raíz")
        p = config.ruta_recurso(ruta)
        if (p, k) in vistos:
            continue
        vistos.add((p, k))
        if not p.exists():
            errores.append(f"{donde}: falta el {('audio' if k == 'audio' else 'archivo de marcas de tiempo')} {ruta}")
            continue
        if k == "audio":
            mal = _abre_audio(p)
            if mal:
                errores.append(f"{donde}: el audio {ruta} {mal}")
        else:
            try:
                d = json.loads(p.read_text())
                if not d.get("characters"):
                    errores.append(f"{donde}: {ruta} no trae marcas por letra («characters»)")
            except json.JSONDecodeError as e:
                errores.append(f"{donde}: {ruta} no es JSON válido ({e})")
    if mezcla:
        from estudio.audio import elevenlabs as E
        for i, ev in enumerate((m.get("sonido") or {}).get("eventos", [])):
            if ev.get("tipo") not in ("voz", "musica", "efecto"):
                continue
            try:
                p = E.ruta_en_biblioteca(ev)
            except Exception as e:                     # noqa: BLE001 (ErrorAudio: falta generarlo)
                errores.append(f"sonido.eventos[{i}] ({ev['tipo']}): {e}")
                continue
            mal = _abre_audio(p)
            if mal:
                errores.append(f"sonido.eventos[{i}] ({ev['tipo']}): {p.name} {mal}")
    if externos:
        from estudio import manifiesto as MF
        for ref in MF.dependencias(m):
            try:
                config.resolver(ref)
            except (FileNotFoundError, ValueError) as e:
                errores.append(f"recurso externo: {e}")
    return errores, avisos


def exigir(m: dict, **kw):
    errores, avisos = verificar(m, **kw)
    for a in avisos:
        print("[recursos] aviso:", a, flush=True)
    if errores:
        raise RecursoFaltante("Faltan recursos; NO se prepara la escena (no se inventa nada en su lugar):\n  - "
                              + "\n  - ".join(errores))
