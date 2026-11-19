"""Informe final de un render distribuido (sin bpy): junta los informes de cada trabajo y, si está, la lista de trabajos
de la corrida que da la API de GitHub (para medir esperas en cola y simultaneidad real)."""
from __future__ import annotations

import datetime
import json
from pathlib import Path


def _t(s: str | None):
    return datetime.datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


def simultaneidad(trabajos: list[dict]) -> int:
    ev = []
    for j in trabajos:
        a, b = _t(j.get("started_at")), _t(j.get("completed_at"))
        if a and b:
            ev += [(a, 1), (b, -1)]
    cur = pico = 0
    for _, d in sorted(ev, key=lambda e: (e[0], e[1])):
        cur += d
        pico = max(pico, cur)
    return pico


def armar(carpeta_informes: str | Path, solicitados: int, cuadros_total: int, verificacion: dict,
          jobs_api: str | Path | None = None, prefijo_trabajo: str = "render") -> dict:
    infs = [json.loads(p.read_text()) for p in sorted(Path(carpeta_informes).rglob("informe_*.json"))]
    tiempos = [v["s"] for i in infs for v in i.get("por_cuadro", {}).values()]
    out = {
        "formato": "estudio.informe_render/1",
        "trabajos_solicitados": solicitados,
        "trabajos_con_informe": len(infs),
        "cuadros_esperados": cuadros_total,
        "cuadros_renderizados": sum(i.get("renderizados", 0) for i in infs),
        "fallos": [f for i in infs for f in i.get("fallos", [])],
        "reintentos": sum(i.get("reintentos", 0) for i in infs),
        "segundos_por_cuadro": {"media": round(sum(tiempos) / len(tiempos), 2) if tiempos else None,
                                "min": min(tiempos) if tiempos else None, "max": max(tiempos) if tiempos else None},
        "cpu_total_h": round(sum(tiempos) / 3600, 2),
        "preparacion_por_trabajo_s": {"verificar_hash_max": max((i.get("verificar_hash_s", 0) for i in infs), default=None),
                                      "abrir_blend_max": max((i.get("abrir_blend_s", 0) for i in infs), default=None)},
        "ram_max_mb": max((i.get("ram_max_mb", 0) for i in infs), default=None),
        "verificacion_cuadros": verificacion,
    }
    if jobs_api and Path(jobs_api).exists():
        js = json.loads(Path(jobs_api).read_text())
        js = js.get("jobs", js) if isinstance(js, dict) else js
        rend = [j for j in js if str(j.get("name", "")).startswith(prefijo_trabajo)]
        esperas = [(_t(j["started_at"]) - _t(j["created_at"])).total_seconds() for j in rend
                   if j.get("started_at") and j.get("created_at")]
        dur = [(_t(j["completed_at"]) - _t(j["started_at"])).total_seconds() for j in rend
               if j.get("started_at") and j.get("completed_at")]
        ini = [_t(j["started_at"]) for j in rend if j.get("started_at")]
        fin = [_t(j["completed_at"]) for j in rend if j.get("completed_at")]
        out["github"] = {
            "trabajos_ejecutados": sum(1 for j in rend if j.get("conclusion") == "success"),
            "trabajos_fallidos": sum(1 for j in rend if j.get("conclusion") not in (None, "success")),
            "simultaneos_max": simultaneidad(rend),
            "espera_en_cola_s": {"media": round(sum(esperas) / len(esperas), 1) if esperas else None,
                                 "max": round(max(esperas), 1) if esperas else None},
            "duracion_trabajo_s": {"media": round(sum(dur) / len(dur), 1) if dur else None,
                                   "max": round(max(dur), 1) if dur else None},
            "reloj_render_s": round((max(fin) - min(ini)).total_seconds(), 1) if ini and fin else None,
        }
    return out
