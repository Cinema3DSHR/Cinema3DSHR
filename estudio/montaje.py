"""Montaje con FFmpeg: tomas → escena (MP4 H.264 + OGV para la app), efectos de montaje, audio, portada.

Formatos de entrega (ver docs/RENDER_Y_EXPORTACION.md):
- MP4 H.264 (yuv420p, +faststart) con AAC 192 kb/s: exportar, descargar y compartir.
- OGV (Theora + Vorbis): el reproductor dentro de la app (Godot 4.7 sólo decodifica Theora).
- portada.jpg (1280 px) y miniatura.jpg (480 px).
"""
from __future__ import annotations
import json
import shutil
import subprocess
from pathlib import Path

FUENTE_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
FUENTE_TITULO = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def _ff(*args):
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *map(str, args)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg falló: {' '.join(cmd)}\n{r.stderr[-2000:]}")


def duracion(ruta: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(ruta)],
                       capture_output=True, text=True, check=True)
    return float(json.loads(r.stdout)["format"]["duration"])


def _filtro_efecto(efecto: dict | None, fps: int) -> str:
    if not efecto:
        return "null"
    if efecto.get("efecto") == "vigilancia":
        texto = efecto.get("texto", "CAM 01").replace(":", r"\:").replace("'", "")
        fuente = FUENTE_MONO if Path(FUENTE_MONO).exists() else ""
        ff = f":fontfile={fuente}" if fuente else ""
        return (
            "format=gray,format=yuv420p,eq=contrast=1.15:brightness=0.03,"
            "colorchannelmixer=rr=0.85:gg=1.0:bb=0.85,noise=alls=14:allf=t,"
            f"drawtext=text='{texto}'{ff}:fontcolor=white@0.9:fontsize=h/22:x=w*0.04:y=h*0.05,"
            f"drawtext=text='%{{pts\\:gmtime\\:1794708780\\:%d/%m/%Y %H\\\\\\:%M\\\\\\:%S}}'{ff}"
            ":fontcolor=white@0.9:fontsize=h/24:x=w*0.04:y=h*0.9,"
            f"drawtext=text='● REC'{ff}:fontcolor=red@0.95:fontsize=h/20:x=w*0.84:y=h*0.05:"
            "enable='lt(mod(t,1),0.6)'"
        )
    if efecto.get("efecto") == "titulo":
        # título de cierre: dos líneas centradas que aparecen con un fundido de 1 s desde «desde_s» (relativo a la toma)
        fuente = FUENTE_TITULO if Path(FUENTE_TITULO).exists() else ""
        ff = f":fontfile={fuente}" if fuente else ""
        a = float(efecto.get("desde_s", 0.0))
        alfa = f"if(lt(t\\,{a})\\,0\\,if(lt(t\\,{a + 1.0})\\,t-{a}\\,1))"
        partes = []
        lineas = efecto.get("lineas", ["DÚO CERO"])
        for i, linea in enumerate(lineas):
            txt = linea.replace("\\", "").replace(":", r"\:").replace("'", "")
            tam = "h/9" if i == 0 else "h/26"
            y = "h*0.38" if i == 0 else f"h*{0.38 + 0.16 + 0.05 * (i - 1):.2f}"
            partes.append(f"drawtext=text='{txt}'{ff}:fontcolor=white:fontsize={tam}:x=(w-text_w)/2:y={y}:"
                          f"alpha='{alfa}':shadowcolor=black@0.6:shadowx=3:shadowy=3")
        return ",".join(partes)
    return "null"


def montar_toma(carpeta_fotogramas: Path, salida: Path, fps: int = 30, efecto: dict | None = None,
                crf: int = 14) -> Path:
    """Fotogramas JPG de una toma → video intermedio de alta calidad (se vuelve a comprimir al final)."""
    salida.parent.mkdir(parents=True, exist_ok=True)
    _ff("-framerate", fps, "-i", carpeta_fotogramas / "f_%04d.jpg", "-vf", _filtro_efecto(efecto, fps),
        "-c:v", "libx264", "-preset", "medium", "-crf", crf, "-pix_fmt", "yuv420p", salida)
    return salida


def unir_escena(tomas_mp4: list[Path], audio_wav: Path | None, carpeta: Path, nombre: str, crf: int = 22,
                ancho_ogv: int = 1280) -> dict:
    """Une las tomas, agrega audio normalizado y produce MP4, OGV, portada y miniatura."""
    carpeta.mkdir(parents=True, exist_ok=True)
    lista = carpeta / f"{nombre}_lista.txt"
    lista.write_text("".join(f"file '{p.resolve()}'\n" for p in tomas_mp4))
    video = carpeta / f"{nombre}_video.mp4"
    _ff("-f", "concat", "-safe", 0, "-i", lista, "-c", "copy", video)
    mp4 = carpeta / f"{nombre}.mp4"
    ogv = carpeta / f"{nombre}.ogv"
    if audio_wav and audio_wav.exists():
        _ff("-i", video, "-i", audio_wav, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "slow",
            "-crf", crf, "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-c:a", "aac",
            "-b:a", "192k", "-ar", 48000, "-shortest", "-movflags", "+faststart", mp4)
        _ff("-i", mp4, "-vf", f"scale='min({ancho_ogv},iw)':-2", "-c:v", "libtheora", "-q:v", 7, "-c:a", "libvorbis",
            "-q:a", 4, ogv)
    else:
        _ff("-i", video, "-c:v", "libx264", "-preset", "slow", "-crf", crf, "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", mp4)
        _ff("-i", mp4, "-vf", f"scale='min({ancho_ogv},iw)':-2", "-c:v", "libtheora", "-q:v", 7, ogv)
    portada = carpeta / f"{nombre}_portada.jpg"
    mini = carpeta / f"{nombre}_miniatura.jpg"
    _ff("-ss", min(2.5, duracion(mp4) / 3), "-i", mp4, "-frames:v", 1, "-vf", "scale=1280:-2", "-q:v", 3, portada)
    _ff("-i", portada, "-vf", "scale=480:-2", "-q:v", 4, mini)
    video.unlink(missing_ok=True)
    lista.unlink(missing_ok=True)
    return {"mp4": mp4, "ogv": ogv, "portada": portada, "miniatura": mini, "duracion_s": round(duracion(mp4), 2)}


def unir_pelicula(escenas_mp4: list[Path], salida: Path, crf: int = 20, ancho: int = 1920, fps: int = 30) -> Path:
    """Montaje final de la película (sólo con escenas aprobadas): re-codifica a un formato común."""
    salida.parent.mkdir(parents=True, exist_ok=True)
    entradas = []
    filtros = []
    for i, p in enumerate(escenas_mp4):
        entradas += ["-i", p]
        filtros.append(f"[{i}:v]scale={ancho}:-2,fps={fps},setsar=1[v{i}];")
    concat = "".join(f"[v{i}][{i}:a]" for i in range(len(escenas_mp4)))
    fc = "".join(filtros) + f"{concat}concat=n={len(escenas_mp4)}:v=1:a=1[v][a]"
    _ff(*entradas, "-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", crf,
        "-preset", "slow", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", salida)
    return salida


def hay_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None
