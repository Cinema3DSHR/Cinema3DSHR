"""Reparto de un EPISODIO (varias escenas seguidas) entre N trabajos de GitHub Actions.

Numera los fotogramas de la película de 1 a TOTAL (escena 1, después la 2, …), los parte en N bloques contiguos y
equilibrados (difieren en 1 fotograma como mucho) y dice qué tramo de qué escena le toca a cada trabajo. Comprueba que
no haya huecos ni repetidos. Con --prueba K cada trabajo renderiza sólo K fotogramas repartidos parejo dentro de SU
bloque (ensayo representativo: los 19 trabajan a la vez y se pasa por todas las escenas y tomas).

    python3 pruebas/episodio/plan.py p009_duo_cero --trabajos 19 [--prueba 6] [--escenas e01] [--json salida.json]

Con --escenas se reparten sólo los fotogramas de esas escenas (la numeración sigue siendo la del episodio). El costo
por fotograma medido en GitHub depende más de la máquina que toca (hasta 1,8× en la misma toma) que del contenido
(~10 % entre tomas de una escena), así que dentro de una escena el reparto parejo en fotogramas es el equilibrado.
"""
import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))


def escenas(produccion: str) -> list[dict]:
    """Escenas del episodio en orden, cada una en su versión más nueva, con su largo en fotogramas de película."""
    base = RAIZ / "producciones" / produccion
    p = json.loads((base / "produccion.json").read_text())
    out, desde = [], 1
    for eid in p["escenas"]:
        vs = sorted((base / "escenas" / eid).glob("v*/escena.json"), key=lambda r: int(r.parent.name[1:]))
        ruta = vs[-1]
        m = json.loads(ruta.read_text())
        fps = m.get("render", {}).get("fps", 30)
        n = round(m["duracion_s"] * fps)
        out.append({"escena": eid, "ruta": str(ruta.relative_to(RAIZ)), "desde": desde, "hasta": desde + n - 1,
                    "fotogramas": n})
        desde += n
    return out


def repartir(total: int, trabajos: int) -> list[tuple[int, int]]:
    """Bloques contiguos [desde, hasta] (base 1) de tamaño parejo: los primeros total % trabajos llevan uno más."""
    base, resto = divmod(total, trabajos)
    bloques, d = [], 1
    for i in range(trabajos):
        tam = base + (1 if i < resto else 0)
        bloques.append((d, d + tam - 1))
        d += tam
    return bloques


def plan(produccion: str, trabajos: int, prueba: int = 0, solo: list[str] | None = None) -> dict:
    esc = escenas(produccion)
    elegidas = [e for e in esc if not solo or e["escena"] in solo]
    assert elegidas, f"ninguna escena coincide con {solo}"
    # las escenas elegidas tienen que ser seguidas (un bloque no puede saltar escenas)
    assert all(a["hasta"] + 1 == b["desde"] for a, b in zip(elegidas, elegidas[1:])), "las escenas deben ser consecutivas"
    primero, ultimo = elegidas[0]["desde"], elegidas[-1]["hasta"]
    total = ultimo - primero + 1
    trabajos = min(trabajos, total)
    bloques = [(d + primero - 1, h + primero - 1) for d, h in repartir(total, trabajos)]
    # comprobaciones: cubren primero..ultimo exactamente, sin huecos ni solapes
    assert bloques[0][0] == primero and bloques[-1][1] == ultimo
    assert all(a[1] + 1 == b[0] for a, b in zip(bloques, bloques[1:]))
    assert sum(h - d + 1 for d, h in bloques) == total
    matriz = []
    for i, (d, h) in enumerate(bloques):
        if prueba:
            k = min(prueba, h - d + 1)
            # K fotogramas parejos dentro del bloque (incluye el primero y el último)
            fot = sorted({round(d + (h - d) * j / max(1, k - 1)) for j in range(k)})
        else:
            fot = list(range(d, h + 1))
        tramos = []
        for e in esc:
            loc = [g - e["desde"] + 1 for g in fot if e["desde"] <= g <= e["hasta"]]
            if loc:
                tramos.append({"escena": e["escena"], "ruta": e["ruta"], "offset": e["desde"] - 1,
                               "locales": loc})
        matriz.append({"n": f"{i:02d}", "desde": d, "hasta": h, "cantidad": len(fot),
                       "escenas": " ".join(t["escena"] for t in tramos), "tramos": json.dumps(tramos)})
    return {"total": total, "primero": primero, "ultimo": ultimo, "escenas": elegidas, "matriz": matriz,
            "a_renderizar": sum(x["cantidad"] for x in matriz)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("produccion")
    ap.add_argument("--trabajos", type=int, default=19)
    ap.add_argument("--prueba", type=int, default=0)
    ap.add_argument("--escenas", default="")
    ap.add_argument("--json")
    a = ap.parse_args()
    r = plan(a.produccion, a.trabajos, a.prueba, a.escenas.split() or None)
    if a.json:
        Path(a.json).write_text(json.dumps(r))
    for x in r["matriz"]:
        print(f"trabajo {x['n']}: fotogramas {x['desde']}–{x['hasta']} ({x['hasta'] - x['desde'] + 1}), "
              f"renderiza {x['cantidad']} · escenas {x['escenas']}")
    print(f"total {r['total']} fotogramas; esta corrida renderiza {r['a_renderizar']}")
