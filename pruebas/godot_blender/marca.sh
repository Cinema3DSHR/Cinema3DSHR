#!/bin/bash
# uso: ./marca.sh <etapa> <inicio|fin|nota> [texto]  → agrega una línea a tiempos.jsonl con la hora UTC
python3 - "$@" <<'PY'
import json, sys, datetime
e, ev = sys.argv[1], sys.argv[2]
t = " ".join(sys.argv[3:])
l = {"etapa": e, "evento": ev, "utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
if t: l["nota"] = t
open("/home/user/Cinema3DSHR/pruebas/godot_blender/tiempos.jsonl", "a").write(json.dumps(l, ensure_ascii=False) + "\n")
print(l)
PY
