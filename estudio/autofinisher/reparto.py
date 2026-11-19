"""Reparto de cuadros entre trabajos y verificación de lo renderizado (sin bpy).

Numeración: los ARCHIVOS van de 1 a N (`f_0001.png` …), como en el resto del estudio; el cuadro de Blender es
`cuadro_inicial + n − 1`. El reparto es el mismo que funcionó en la prueba (tramos contiguos de ceil(N / trabajos)).
"""
from __future__ import annotations

import math
import re
from pathlib import Path

PATRON = re.compile(r"^f_(\d{4,})\.(png|jpg|jpeg|exr)$", re.I)


def repartir(total: int, trabajos: int, maximo: int = 60) -> list[dict]:
    """Tramos contiguos que cubren 1..total sin huecos ni repetidos."""
    if total <= 0:
        raise ValueError("no hay cuadros para repartir")
    n = max(1, min(maximo, int(trabajos), total))
    tam = math.ceil(total / n)
    t = [{"n": f"{i:02d}", "desde": d, "hasta": min(total, d + tam - 1)} for i, d in enumerate(range(1, total + 1, tam))]
    for x in t:
        x["cantidad"] = x["hasta"] - x["desde"] + 1
    assert sum(x["cantidad"] for x in t) == total and t[0]["desde"] == 1 and t[-1]["hasta"] == total
    return t


def parse_lista(texto: str, total: int) -> list[int]:
    """«12,40-45,900» → [12, 40, 41, …, 45, 900]. Para recuperar sólo los cuadros que faltaron."""
    out: set[int] = set()
    for parte in re.split(r"[,\s]+", (texto or "").strip()):
        if not parte:
            continue
        if "-" in parte:
            a, b = (int(x) for x in parte.split("-", 1))
            out.update(range(a, b + 1))
        else:
            out.add(int(parte))
    malos = [c for c in out if c < 1 or c > total]
    if malos:
        raise ValueError(f"cuadros fuera de 1..{total}: {sorted(malos)[:10]}")
    return sorted(out)


def repartir_lista(cuadros: list[int], trabajos: int, maximo: int = 60) -> list[dict]:
    """Reparte una lista explícita de cuadros (recuperación): cada trabajo recibe su lista."""
    if not cuadros:
        raise ValueError("lista de cuadros vacía")
    n = max(1, min(maximo, int(trabajos), len(cuadros)))
    tam = math.ceil(len(cuadros) / n)
    t = []
    for i in range(0, len(cuadros), tam):
        parte = cuadros[i:i + tam]
        t.append({"n": f"{len(t):02d}", "desde": parte[0], "hasta": parte[-1], "cantidad": len(parte),
                  "cuadros": ",".join(map(str, parte))})
    return t


def comprimir(cuadros: list[int]) -> str:
    """[1,2,3,7,9,10] → «1-3,7,9-10»."""
    if not cuadros:
        return ""
    cs = sorted(set(cuadros))
    out, a, b = [], cs[0], cs[0]
    for c in cs[1:]:
        if c == b + 1:
            b = c
            continue
        out.append(f"{a}-{b}" if b > a else str(a))
        a = b = c
    out.append(f"{a}-{b}" if b > a else str(a))
    return ",".join(out)


def verificar(carpeta: str | Path, total: int) -> dict:
    """Qué cuadros hay, cuáles faltan, cuáles sobran y si hay archivos vacíos o con nombre raro. NO rellena nada."""
    p = Path(carpeta)
    hay, raros, vacios = set(), [], []
    for f in sorted(p.iterdir()) if p.exists() else []:
        m = PATRON.match(f.name)
        if not m:
            if f.is_file() and not f.name.endswith(".json"):
                raros.append(f.name)
            continue
        if f.stat().st_size == 0:
            vacios.append(f.name)
            continue
        hay.add(int(m.group(1)))
    faltan = sorted(set(range(1, total + 1)) - hay)
    sobran = sorted(c for c in hay if c < 1 or c > total)
    return {"esperados": total, "presentes": len(hay & set(range(1, total + 1))), "faltan": faltan,
            "faltan_texto": comprimir(faltan), "sobran": sobran, "vacios": vacios, "raros": raros,
            "completo": not faltan and not sobran and not vacios}
