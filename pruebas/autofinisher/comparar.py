"""Compara dos resúmenes de .blend (resumen_blend.py) y lista cada diferencia (Python común).

    python3 pruebas/autofinisher/comparar.py referencia.json nuevo.json
"""
import json
import sys


def plano(d, pref=""):
    out = {}
    if isinstance(d, dict):
        for k, v in d.items():
            out.update(plano(v, f"{pref}.{k}" if pref else k))
    elif isinstance(d, list) and d and all(isinstance(x, dict) for x in d):
        for i, v in enumerate(d):
            out.update(plano(v, f"{pref}[{i}]"))
    else:
        out[pref] = d
    return out


a, b = (plano(json.load(open(p))) for p in sys.argv[1:3])
iguales = sum(1 for k in a if k in b and a[k] == b[k])
solo_a = sorted(k for k in a if k not in b)
solo_b = sorted(k for k in b if k not in a)
distintos = sorted(k for k in a if k in b and a[k] != b[k])
print(f"campos iguales: {iguales} · distintos: {len(distintos)} · sólo en la referencia: {len(solo_a)} · sólo en la nueva: {len(solo_b)}")
for k in distintos:
    print(f"  ≠ {k}\n      referencia: {json.dumps(a[k], ensure_ascii=False)[:180]}\n      nueva:      {json.dumps(b[k], ensure_ascii=False)[:180]}")
for k in solo_a:
    print(f"  − sólo referencia: {k} = {json.dumps(a[k], ensure_ascii=False)[:150]}")
for k in solo_b:
    print(f"  + sólo nueva:      {k} = {json.dumps(b[k], ensure_ascii=False)[:150]}")
