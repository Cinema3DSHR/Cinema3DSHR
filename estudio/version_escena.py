"""Versión APROBADA de una escena del estudio, lista para el render en la nube (sin bpy).

Flujo (docs/FLUJO_DEFINITIVO.md): Claude crea la escena → previsualización liviana → correcciones → el dueño dice en
el chat que está aprobada → `python -m estudio aprobar` congela la receta → «Publicar escena aprobada»
(publicar_escena.yml) arma el BLEND y el WAV, publica la Release y dispara el render automático.

Release `escena-<produccion>-<escena>-v<NNN>` (inmutable; si existe, no se vuelve a publicar):
  <e>_v<k>.blend                 escena autónoma y empaquetada (cámaras, luces, materiales, personajes, animaciones,
                                 labios horneados desde las alineaciones de ElevenLabs)
  <e>_v<k>.wav                   mezcla completa hecha por pruebas/video_30s/audio_escena.py (48 kHz estéreo)
  <e>_v<k>_voces.zip             las voces (mp3) y sus JSON de alineación que usó la construcción
  <e>_v<k>_escena.json           la receta congelada
  manifest.json                  este manifiesto (formato «estudio.version_escena/1»)
Después del render se suman `<e>_v<k>_final.mp4` y su informe (no se sobrescriben).
"""
from __future__ import annotations

import datetime
import json
from pathlib import Path

from estudio import manifiesto as ME

FORMATO = "estudio.version_escena/1"


def eid(m: dict) -> str:
    return m["id"].split("-")[-1]


def tag_release(m: dict) -> str:
    return f"escena-{m['produccion']}-{eid(m)}-v{int(m['version']):03d}"


def nombres(m: dict) -> dict:
    b = f"{eid(m)}_v{m['version']}"
    return {"blend": f"{b}.blend", "wav": f"{b}.wav", "voces": f"{b}_voces.zip", "escena": f"{b}_escena.json",
            "manifiesto": "manifest.json", "mp4": f"{b}_final.mp4", "informe": f"{b}_final_informe.json"}


# ── aprobación (la da el dueño en el chat; Claude la registra con `python -m estudio aprobar`) ──────────────────────

def aprobar(ruta: Path, nota: str = "") -> dict:
    """Congela la versión: estado «aprobada», bloqueada, y en el historial la huella aprobada (la huella no incluye
    estado, bloqueada ni historial: aprobar no la cambia). Una versión ya aprobada no se vuelve a aprobar."""
    from estudio import proteccion as PR
    ruta = Path(ruta)
    m = ME.leer(ruta)
    err = ME.validar(m)
    if err:
        raise SystemExit("La escena no es válida, no se aprueba:\n  - " + "\n  - ".join(err))
    if m.get("bloqueada"):
        raise SystemExit(f"{m['id']} v{m['version']} ya está aprobada y bloqueada (huella {aprobada(m)}).")
    h = ME.huella(m)
    reg = PR.registro(ruta)
    # se aprueba LO QUE EL DUEÑO VIO: la huella de la previsualización entregada tiene que ser la de ahora
    if reg is None:
        raise SystemExit("Esta versión no tiene previsualización entregada (entregado.json): primero la previa y la revisión.")
    if reg.get("huella") != h:
        raise SystemExit(f"La receta cambió desde la previsualización entregada (huella {h} ≠ {reg.get('huella')}): "
                         "hace falta una previsualización nueva antes de aprobar.")
    fecha = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    m["estado"] = "aprobada"
    m["bloqueada"] = True
    m.setdefault("historial", []).append({"aprobada": fecha, "huella": h, "por": "dueño (en el chat)", "nota": nota})
    # sólo cambian estado, bloqueada e historial (fuera de la huella); lo entregado sigue protegido y su registro
    # anota la receta aprobada para que `proteccion.verificar` la reconozca
    ruta.write_text(json.dumps(m, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    reg["aprobacion"] = {"fecha": fecha, "huella": h, "receta_sha256": PR.sha256(ruta)}
    (ruta.parent / PR.NOMBRE).write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n")
    return {"escena": m["id"], "version": m["version"], "huella": h, "release": tag_release(m)}


def aprobada(m: dict) -> str | None:
    """Huella que el dueño aprobó (la última aprobación del historial), o None."""
    for h in reversed(m.get("historial", [])):
        if "aprobada" in h:
            return h.get("huella")
    return None


def errores_aprobacion(m: dict) -> list[str]:
    """Lo que impide publicar: no aprobada, no bloqueada o la receta cambió después de aprobar."""
    e = []
    if m.get("estado") != "aprobada" or not m.get("bloqueada"):
        e.append(f"{m['id']} v{m['version']} no está aprobada y bloqueada (estado «{m.get('estado')}»)")
    h_ok = aprobada(m)
    if not h_ok:
        e.append("no hay aprobación registrada en el historial (python -m estudio aprobar)")
    elif h_ok != ME.huella(m):
        e.append(f"la receta o el código cambió después de aprobar (huella {ME.huella(m)} ≠ aprobada {h_ok}): "
                 "hace falta una versión nueva y otra revisión")
    return e


# ── manifiesto ────────────────────────────────────────────────────────────────────────────────────────────────────

def errores(m: dict) -> list[str]:
    e = []
    if m.get("formato") != FORMATO:
        return [f"formato: se esperaba «{FORMATO}»"]
    for k in ("produccion", "escena", "version", "id", "release", "huella", "archivos", "render", "tomas", "voces"):
        if k not in m:
            e.append(f"falta «{k}»")
    if e:
        return e
    for k in ("blend", "escena"):
        if len(str(m["archivos"].get(k, {}).get("sha256", ""))) != 64:
            e.append(f"archivos.{k}.sha256 falta o no es un SHA-256")
    if m.get("completo"):
        for k in ("wav", "voces"):
            if len(str(m["archivos"].get(k, {}).get("sha256", ""))) != 64:
                e.append(f"archivos.{k}.sha256 falta o no es un SHA-256")
    if m.get("dependencias_externas"):
        e.append(f"hay recursos sin empaquetar: {m['dependencias_externas'][:5]}")
    r = m["render"]
    if r.get("cuadros") != r.get("cuadro_final", 0) - r.get("cuadro_inicial", 0) + 1:
        e.append("render.cuadros no coincide con el rango")
    return e


def leer(ruta: str | Path) -> dict:
    m = json.loads(Path(ruta).read_text())
    e = errores(m)
    if e:
        raise ValueError(f"manifiesto {ruta} inválido: " + "; ".join(e))
    return m


def verificar(m: dict, clave: str, ruta: str | Path) -> tuple[bool, str]:
    """¿El archivo descargado es exactamente el de esta versión? (tamaño y SHA-256 del manifiesto)."""
    from estudio.autofinisher import medicion as MD
    a = m["archivos"][clave]
    p = Path(ruta)
    if not p.exists():
        return False, f"no está {p}"
    if p.stat().st_size != a["bytes"]:
        return False, f"{p.name}: tamaño {p.stat().st_size} ≠ {a['bytes']} del manifiesto"
    h = MD.sha256(p)
    if h != a["sha256"]:
        return False, f"{p.name}: SHA-256 {h} ≠ {a['sha256']} del manifiesto"
    return True, f"{p.name}: {a['bytes']} bytes, SHA-256 {h} (= manifiesto {m['id']})"


def cerrar(salida: str | Path, wav: str | Path) -> dict:
    """Suma el WAV definitivo (el de pruebas/video_30s/audio_escena.py) a la versión preparada. Tiene que ser IDÉNTICO,
    byte a byte, al de control que salió de las pistas de la misma construcción del BLEND: así queda probado que BLEND
    y WAV son de la misma receta. Si no coincide, no se publica nada."""
    import shutil
    import wave
    from estudio.autofinisher import medicion as MD
    out = Path(salida)
    man = json.loads((out / "manifest.json").read_text())
    if man.get("completo"):
        raise SystemExit("La versión ya está cerrada")
    wav = Path(wav)
    h = MD.sha256(wav)
    if h != man["audio_control"]["sha256"]:
        raise SystemExit(f"NO SE PUBLICA: el WAV de audio_escena.py ({h[:12]}) no es idéntico al de la construcción del "
                         f"BLEND ({man['audio_control']['sha256'][:12]}): BLEND y WAV no serían de la misma receta.")
    with wave.open(str(wav)) as w:
        sr, canales, n = w.getframerate(), w.getnchannels(), w.getnframes()
    dur = n / sr
    video_s = man["render"]["cuadros"] / man["render"]["fps"]
    if abs(dur - man["render"]["duracion_s"]) > 1 / sr * 2 or abs(dur - video_s) > 1 / man["render"]["fps"]:
        raise SystemExit(f"NO SE PUBLICA: el WAV dura {dur:.4f} s; la receta {man['render']['duracion_s']} s y el video "
                         f"{video_s:.4f} s (más de un cuadro de diferencia)")
    nb = {"wav": f"{man['escena']}_v{man['version']}.wav"}
    shutil.copy(wav, out / nb["wav"])
    man["archivos"]["wav"] = {**MD.archivo(out / nb["wav"]), "muestreo_hz": sr, "canales": canales,
                              "muestras": n, "duracion_s": round(dur, 6),
                              "generador": "pruebas/video_30s/audio_escena.py (sin cambios)"}
    man["completo"] = True
    e = errores(man)
    if e:
        raise SystemExit("manifiesto inválido: " + "; ".join(e))
    (out / "manifest.json").write_text(json.dumps(man, indent=1, ensure_ascii=False))
    print(f"CERRADA {man['release']}: WAV {dur:.3f} s {sr} Hz {canales} canales = control; video {video_s:.3f} s")
    return man
