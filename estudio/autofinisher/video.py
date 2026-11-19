"""Verificación del MP4 final con ffprobe (sin bpy): cantidad exacta de cuadros, resolución, fps y duración."""
from __future__ import annotations

import json
import subprocess
from fractions import Fraction
from pathlib import Path


def sondear(mp4: str | Path) -> dict:
    r = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height,r_frame_rate,nb_read_frames,codec_name,pix_fmt:format=duration,size",
                        "-of", "json", str(mp4)], capture_output=True, text=True, check=True)
    d = json.loads(r.stdout)
    s = d["streams"][0]
    return {"ancho": int(s["width"]), "alto": int(s["height"]), "fps": float(Fraction(s["r_frame_rate"])),
            "cuadros": int(s.get("nb_read_frames", 0)), "codec": s.get("codec_name"), "pix_fmt": s.get("pix_fmt"),
            "duracion_s": round(float(d["format"]["duration"]), 3), "bytes": int(d["format"]["size"])}


def verificar(mp4: str | Path, ancho: int, alto: int, fps: int, cuadros: int) -> dict:
    v = sondear(mp4)
    problemas = []
    if (v["ancho"], v["alto"]) != (ancho, alto):
        problemas.append(f"resolución {v['ancho']}x{v['alto']} ≠ {ancho}x{alto}")
    if abs(v["fps"] - fps) > 1e-3:
        problemas.append(f"fps {v['fps']} ≠ {fps}")
    if v["cuadros"] != cuadros:
        problemas.append(f"cuadros {v['cuadros']} ≠ {cuadros}")
    esperada = cuadros / fps
    if abs(v["duracion_s"] - esperada) > 1.5 / fps:
        problemas.append(f"duración {v['duracion_s']} s ≠ {esperada:.3f} s")
    return {**v, "esperado": {"ancho": ancho, "alto": alto, "fps": fps, "cuadros": cuadros,
                              "duracion_s": round(esperada, 3)}, "problemas": problemas, "ok": not problemas}
