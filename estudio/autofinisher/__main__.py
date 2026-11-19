"""Línea de comandos del AutoFinisher (docs/AUTOFINISHER.md).

Con el Python de Blender (bpy):
  construir         --receta R.json --glb X.glb --version N --salida DIR [--godot 4.7.2]
  validar           --blend X.blend --manifiesto manifest.json
  render-trozo      --blend --manifiesto (--desde A --hasta B | --cuadros LISTA) --ancho --alto --muestras --salida
                    [--reintentos 1] [--sin-render]
  aprobar-blend     --blend X.blend --produccion DIR --version N --nota "frase del dueño"
                    MODALIDAD 2: registra la aprobación de un .blend ya preparado (SHA-256, perfil 720p); no lo toca
  incorporar        --blend X.blend --aprobacion REG.json --salida DIR
                    MODALIDAD 2: comprueba hash y perfil, arma la versión (copia byte a byte + manifiesto) sin Godot
Con Python común (sin bpy):
  receta            --receta R.json                         valida la receta y muestra los valores completos
  verificar-blend   --manifiesto M --blend X.blend          tamaño y SHA-256 contra el manifiesto
  reparto           --total N --trabajos K [--cuadros LISTA] tramos de cuadros por trabajo (JSON)
  verificar-cuadros --carpeta DIR --total N                 faltantes / sobrantes / vacíos (no rellena nada)
  verificar-video   --mp4 X.mp4 --ancho --alto --fps --cuadros
  descargar         --url URL --destino ARCHIVO [--sha256 H] descarga midiendo tiempo y velocidad
  informe-render    --informes DIR --solicitados K --total N --verificacion V.json [--jobs J.json] --salida S.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path


def _imprimir(d):
    print(json.dumps(d, ensure_ascii=False, indent=1, default=str))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m estudio.autofinisher")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("construir"); p.add_argument("--receta", required=True); p.add_argument("--glb", required=True)
    p.add_argument("--version", type=int, required=True); p.add_argument("--salida", required=True); p.add_argument("--godot")
    p = sub.add_parser("validar"); p.add_argument("--blend", required=True); p.add_argument("--manifiesto", required=True)
    p = sub.add_parser("render-trozo")
    for a in ("--blend", "--manifiesto", "--salida"):
        p.add_argument(a, required=True)
    p.add_argument("--desde", type=int); p.add_argument("--hasta", type=int); p.add_argument("--cuadros")
    for a in ("--ancho", "--alto", "--muestras"):
        p.add_argument(a, type=int, required=True)
    p.add_argument("--reintentos", type=int, default=1); p.add_argument("--sin-render", action="store_true")
    p = sub.add_parser("aprobar-blend"); p.add_argument("--blend", required=True); p.add_argument("--produccion", required=True)
    p.add_argument("--version", type=int, required=True); p.add_argument("--nota", required=True)
    p = sub.add_parser("incorporar"); p.add_argument("--blend", required=True); p.add_argument("--aprobacion", required=True)
    p.add_argument("--salida", required=True)
    p = sub.add_parser("receta"); p.add_argument("--receta", required=True)
    p = sub.add_parser("verificar-blend"); p.add_argument("--manifiesto", required=True); p.add_argument("--blend", required=True)
    p = sub.add_parser("reparto"); p.add_argument("--total", type=int, required=True); p.add_argument("--trabajos", type=int, required=True)
    p.add_argument("--cuadros", default="")
    p = sub.add_parser("verificar-cuadros"); p.add_argument("--carpeta", required=True); p.add_argument("--total", type=int, required=True)
    p = sub.add_parser("verificar-video"); p.add_argument("--mp4", required=True)
    for a in ("--ancho", "--alto", "--fps", "--cuadros"):
        p.add_argument(a, type=int, required=True)
    p = sub.add_parser("descargar"); p.add_argument("--url", required=True); p.add_argument("--destino", required=True)
    p.add_argument("--sha256")
    p = sub.add_parser("informe-render")
    for a in ("--informes", "--verificacion", "--salida"):
        p.add_argument(a, required=True)
    p.add_argument("--solicitados", type=int, required=True); p.add_argument("--total", type=int, required=True)
    p.add_argument("--jobs")
    a = ap.parse_args(argv)

    if a.cmd == "construir":
        from estudio.autofinisher.construir import construir
        r = construir(a.receta, a.glb, a.version, a.salida, a.godot)
        _imprimir({"salida": r["salida"], "id": r["manifiesto"]["id"], "blend": r["manifiesto"]["archivos"]["blend"],
                   "segundos": r["segundos"], "ram_max_mb": r["ram_max_mb"]})
    elif a.cmd == "validar":
        from estudio.autofinisher.validar import validar
        r = validar(a.blend, a.manifiesto)
        _imprimir(r)
        return 0 if r["ok"] else 1
    elif a.cmd == "render-trozo":
        from estudio.autofinisher import reparto as RP
        from estudio.autofinisher.render_trozo import renderizar
        from estudio.autofinisher import manifiesto as MF
        total = MF.leer(a.manifiesto)["render"]["cuadros"]
        cuadros = RP.parse_lista(a.cuadros, total) if a.cuadros else list(range(a.desde, a.hasta + 1))
        r = renderizar(a.blend, a.manifiesto, cuadros, a.ancho, a.alto, a.muestras, a.salida, a.reintentos, a.sin_render)
        _imprimir({k: r[k] for k in ("version", "cantidad", "procesados", "renderizados", "fallos", "reintentos", "media_s", "total_s", "ram_max_mb")})
        return 1 if r["fallos"] else 0
    elif a.cmd == "aprobar-blend":
        from estudio.autofinisher.blend_externo import aprobar
        _imprimir(aprobar(a.blend, a.produccion, a.version, a.nota))
    elif a.cmd == "incorporar":
        from estudio.autofinisher.blend_externo import incorporar
        _imprimir(incorporar(a.blend, a.aprobacion, a.salida))
    elif a.cmd == "receta":
        from estudio.autofinisher import receta as RC
        _imprimir(RC.leer(a.receta))
    elif a.cmd == "verificar-blend":
        from estudio.autofinisher import manifiesto as MF
        ok, motivo = MF.verificar_blend(MF.leer(a.manifiesto), a.blend)
        print(("OK " if ok else "ERROR ") + motivo)
        return 0 if ok else 1
    elif a.cmd == "reparto":
        from estudio.autofinisher import reparto as RP
        _imprimir(RP.repartir_lista(RP.parse_lista(a.cuadros, a.total), a.trabajos) if a.cuadros
                  else RP.repartir(a.total, a.trabajos))
    elif a.cmd == "verificar-cuadros":
        from estudio.autofinisher import reparto as RP
        r = RP.verificar(a.carpeta, a.total)
        _imprimir(r)
        return 0 if r["completo"] else 1
    elif a.cmd == "verificar-video":
        from estudio.autofinisher import video as VI
        r = VI.verificar(a.mp4, a.ancho, a.alto, a.fps, a.cuadros)
        _imprimir(r)
        return 0 if r["ok"] else 1
    elif a.cmd == "descargar":
        from estudio.autofinisher import medicion as MD
        t = time.time()
        Path(a.destino).parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(a.url, timeout=120) as r, open(a.destino, "wb") as f:
            while True:
                b = r.read(1 << 20)
                if not b:
                    break
                f.write(b)
        seg = time.time() - t
        info = MD.archivo(a.destino)
        info.update({"segundos": round(seg, 2), "mb_por_s": round(info["bytes"] / 1e6 / max(seg, 1e-6), 2)})
        if a.sha256:
            info["sha256_esperado"] = a.sha256
            info["ok"] = info["sha256"] == a.sha256
        _imprimir(info)
        return 0 if info.get("ok", True) else 1
    elif a.cmd == "informe-render":
        from estudio.autofinisher import informe_render as IR
        r = IR.armar(a.informes, a.solicitados, a.total, json.loads(Path(a.verificacion).read_text()), a.jobs)
        Path(a.salida).write_text(json.dumps(r, ensure_ascii=False, indent=1))
        _imprimir(r)
    return 0


if __name__ == "__main__":
    sys.exit(main())
