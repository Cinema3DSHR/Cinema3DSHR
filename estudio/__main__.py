"""Línea de comandos del estudio:  python -m estudio <comando> …   (ver docs/FLUJO_DE_PRODUCCION.md)

Comandos principales
  validar <escena.json>                         revisa la receta (tomas contiguas, anclas, móviles…)
  fijas <escena.json> [--calidad previa]        un fotograma por toma (revisión rápida de encuadres)
  matriz <escena.json>                          lista de tomas en JSON (para repartir el render en paralelo)
  render <escena.json> --toma ID [--calidad revision] [--cada N]   fotogramas de una toma + su video intermedio
  cerrar <escena.json> --tomas DIR              audio, montaje, MP4/OGV, portada, GLB del visor, .blend, info.json
  escenario <escenario.json>                    publica un escenario suelto: GLB del visor + portada
  nueva-version <produccion> <escena> [--motivo TEXTO]
  previa <escena.json> [--salida DIR]           GLB + línea de tiempo para el EDITOR 3D (misma escena que el render)
  direccion <produccion>                        resumen de cámaras, marcadores y notas que mandó el director
  aplicar-direccion <produccion> <escena> --camaras camera_001,…   versión nueva con esas cámaras del director
  catalogo --releases R.json --issues I.json [--infos DIR] --salida catalogo.json
  limpieza --catalogo catalogo.json             lista los temporales que la política permite borrar
  animaciones [--limite N]                      inventario de animaciones → catalogo/animaciones.json
  voces <escena.json> [--gastar]                voces y efectos de ElevenLabs que faltan (sin --gastar: sólo estima)
  audio-estado                                  plan y créditos de ElevenLabs (consulta gratuita)
  voces-lista                                   voces de la cuenta (consulta gratuita)
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import sys
import time
from pathlib import Path

from estudio import config
from estudio import manifiesto as MF


def _cargar(ruta) -> dict:
    m = MF.leer(Path(ruta))
    errs = MF.validar(m)
    if errs:
        sys.exit("Manifiesto inválido:\n  - " + "\n  - ".join(errs))
    return m


def cmd_validar(a):
    m = MF.leer(Path(a.escena))
    errs = MF.validar(m)
    print("OK" if not errs else "\n".join(errs))
    print("huella:", MF.huella(m))
    return 1 if errs else 0


def cmd_matriz(a):
    m = _cargar(a.escena)
    print(json.dumps([t["id"] for t in m["tomas"]]))


def cmd_fijas(a):
    from estudio.blender import director as D
    import bpy
    m = _cargar(a.escena)
    res = D.construir(m, a.calidad)
    out = Path(a.salida)
    out.mkdir(parents=True, exist_ok=True)
    s = res["escena"]
    for t in res["tomas"]:
        s.camera = t["camara"]
        D.ir_a(res, (t["frame_inicio"] + t["frame_fin"]) // 2)
        s.render.filepath = str(out / f"{t['spec']['id']}.jpg")
        bpy.ops.render.render(write_still=True)
        print("fija", t["spec"]["id"])


def cmd_render(a):
    from estudio.blender import director as D
    from estudio import montaje
    m = _cargar(a.escena)
    ok, motivo = MF.puede_renderizar(m, a.forzar)
    if not ok:
        sys.exit(motivo)
    res = D.construir(m, a.calidad)
    carpeta = Path(a.salida)
    inf = D.render_tomas(res, carpeta, solo=[a.toma] if a.toma else None, cada=a.cada)
    for t in res["tomas"]:
        tid = t["spec"]["id"]
        if a.toma and tid != a.toma:
            continue
        if a.cada == 1:
            montaje.montar_toma(carpeta / tid, carpeta / f"{tid}.mp4", m["render"].get("fps", 30),
                                t["spec"].get("montaje"))
    (carpeta / f"informe_{a.toma or 'todas'}.json").write_text(json.dumps(inf))


def cmd_cerrar(a):
    """Une las tomas ya renderizadas y produce todos los entregables de la versión."""
    from estudio.blender import director as D
    from estudio.audio import procedural
    from estudio import montaje
    from estudio import publicacion as P
    m = _cargar(a.escena)
    t0 = time.time()
    calidad = a.calidad
    q = config.CALIDADES[calidad]
    res = D.construir(m, calidad)
    out = Path(a.salida)
    out.mkdir(parents=True, exist_ok=True)
    pistas = D.exportar_pistas(res, out / "pistas.json")
    eid = m["id"].split("-")[-1]
    base = f"{eid}_v{m['version']}"
    wav = None
    if m.get("sonido", {}).get("generador") == "procedural":
        wav = procedural.generar(m, pistas, out / f"{base}_audio.wav")
    tomas = [Path(a.tomas) / f"{t['id']}.mp4" for t in m["tomas"]]
    faltan = [str(p) for p in tomas if not p.exists()]
    if faltan:
        sys.exit("Faltan tomas renderizadas: " + ", ".join(faltan))
    r = montaje.unir_escena(tomas, wav, out, f"{base}_revision", crf=q["crf"])
    r["portada"].rename(out / f"{base}_portada.jpg")
    r["miniatura"].rename(out / f"{base}_miniatura.jpg")
    D.guardar_blend(out / f"{base}_proyecto.blend")
    tam_glb = D.exportar_visor(out / f"{base}_visor.glb")
    segs = sum(v.get("segundos", 0) for f in Path(a.tomas).glob("informe_*.json")
               for v in json.loads(f.read_text()).values())
    info = {"escena": m["id"], "version": m["version"], "huella": MF.huella(m), "calidad": calidad,
            "resolucion": f"{q['ancho']}x{q['alto']}", "fps": q["fps"], "motor": q["motor"],
            "duracion_s": r["duracion_s"], "segundos_render": round(segs, 1),
            "fecha": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "visor_bytes": tam_glb, "archivos": {}}
    for f in sorted(out.glob(f"{base}_*")):
        if f.suffix in (".mp4", ".ogv", ".jpg", ".glb", ".blend", ".wav"):
            info["archivos"][f.name] = {"bytes": f.stat().st_size, "sha256": P.sha256(f)}
    MF.escribir(out / f"{base}_info.json", info)
    print(json.dumps(info, indent=1, ensure_ascii=False))
    print(f"cerrado en {time.time() - t0:.0f} s")


def cmd_escenario(a):
    """Construye un escenario suelto y publica su GLB para el visor + una portada."""
    from estudio.blender import director as D
    from estudio.blender import kit as K
    import importlib
    import bpy
    e = MF.leer(Path(a.escenario))
    K.reiniciar_materiales()
    s = K.escena_vacia(e["id"])
    mod = importlib.import_module(f"estudio.escenarios.{e['generador']}")
    info = mod.construir(e.get("parametros", {}))
    out = Path(a.salida)
    # portada: cámara aérea fija
    from estudio.blender import camaras as C
    ctx = C.Contexto(info["anclas"])
    centro = next(iter(info["anclas"].values()))
    toma = C.crear_toma({"id": "portada", "tipo": "orbita", "inicio_s": 0, "duracion_s": 1 / 30,
                         "centro": {"ancla": e.get("ancla_portada", "centro_casa")} if "centro_casa" in info["anclas"]
                         else list(centro), "radio": 42, "altura": 20, "angulo_inicial": -115,
                         "angulo_final": -115, "lente_mm": 26}, ctx)
    s.camera = toma["camara"]
    s.frame_start = s.frame_end = 1
    D.ajustes_render(s, "revision", {"exposicion": 0.8})
    s.render.filepath = str(out / f"{e['id']}_portada.jpg")
    bpy.ops.render.render(write_still=True)
    tam = D.exportar_visor(out / f"{e['id']}_visor.glb")
    MF.escribir(out / f"{e['id']}_info.json", {"escenario": e["id"], "visor_bytes": tam,
                                                "anclas": {k: list(v) for k, v in info["anclas"].items()}})
    print("escenario publicado en", out, tam, "bytes")


def cmd_nueva_version(a):
    print(MF.nueva_version(a.produccion, a.escena, a.motivo))


def cmd_previa(a):
    """Previsualización 3D interactiva (EDITOR 3D de la app) desde la MISMA escena que se renderiza."""
    from estudio.blender import director as D, previa as PV
    m = MF.leer(a.escena)
    err = MF.validar(m)
    if err:
        print("\n".join(err))
        return 1
    res = D.construir(m, "revision")
    eid = m["id"].split("-")[-1]
    out = Path(a.salida)
    tam = PV.exportar(res, m, out / f"{eid}_v{m['version']}_previa.glb", out / f"{eid}_v{m['version']}_previa.json")
    print("PREVIA", json.dumps(tam))


def cmd_direccion(a):
    from estudio import direccion as DR
    print(DR.resumen(a.produccion))


def cmd_aplicar_direccion(a):
    from estudio import direccion as DR
    ruta = DR.nueva_version_con_camaras(a.produccion, a.escena, [c.strip() for c in a.camaras.split(",") if c.strip()], a.motivo)
    print("versión nueva:", ruta)


def cmd_catalogo(a):
    from estudio import publicacion as P
    rel = json.loads(Path(a.releases).read_text()) if a.releases else []
    iss = json.loads(Path(a.issues).read_text()) if a.issues else []
    infos = {}
    if a.infos:
        for f in Path(a.infos).rglob("*_info.json"):
            infos[f"{f.parent.name}/{f.name}"] = json.loads(f.read_text())
    cat = P.construir_catalogo(rel, iss, infos)
    Path(a.salida).write_text(json.dumps(cat, ensure_ascii=False, indent=1))
    print(f"catálogo: {cat['resumen']}")


def cmd_limpieza(a):
    from estudio import publicacion as P
    cat = json.loads(Path(a.catalogo).read_text())
    pol = json.loads((config.RAIZ / "config" / "retencion.json").read_text())
    print(json.dumps(P.plan_limpieza(cat, pol), indent=1))


def cmd_voces(a):
    """Genera (o sólo estima, sin --gastar) las voces y efectos de ElevenLabs que faltan en la biblioteca."""
    from estudio.audio import elevenlabs as EL
    m = _cargar(a.escena)
    inf = EL.asegurar_escena(m, gastar=a.gastar)
    print(json.dumps(inf, ensure_ascii=False, indent=1))


def cmd_audio_estado(a):
    from estudio.audio import elevenlabs as EL
    print(json.dumps(EL.suscripcion(), ensure_ascii=False, indent=1))


def cmd_voces_lista(a):
    from estudio.audio import elevenlabs as EL
    for v in EL.voces():
        print(f"{v['voice_id']}  {v['nombre'][:42]:42} {str(v['categoria']):12} {str(v['genero']):7} {str(v['acento']):14} {','.join(v['idiomas'])}")


def cmd_animaciones(a):
    from estudio.catalogo import animaciones
    animaciones.construir(limite=a.limite, analizar=a.analizar)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="estudio", description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("validar"); p.add_argument("escena"); p.set_defaults(f=cmd_validar)
    p = sub.add_parser("matriz"); p.add_argument("escena"); p.set_defaults(f=cmd_matriz)
    p = sub.add_parser("fijas"); p.add_argument("escena"); p.add_argument("--calidad", default="previa")
    p.add_argument("--salida", default=str(config.SALIDA / "fijas")); p.set_defaults(f=cmd_fijas)
    p = sub.add_parser("render"); p.add_argument("escena"); p.add_argument("--toma")
    p.add_argument("--calidad", default="revision"); p.add_argument("--cada", type=int, default=1)
    p.add_argument("--salida", default=str(config.SALIDA / "tomas")); p.add_argument("--forzar", action="store_true")
    p.set_defaults(f=cmd_render)
    p = sub.add_parser("cerrar"); p.add_argument("escena"); p.add_argument("--tomas", required=True)
    p.add_argument("--calidad", default="revision"); p.add_argument("--salida", default=str(config.SALIDA / "entrega"))
    p.set_defaults(f=cmd_cerrar)
    p = sub.add_parser("escenario"); p.add_argument("escenario")
    p.add_argument("--salida", default=str(config.SALIDA / "escenarios")); p.set_defaults(f=cmd_escenario)
    p = sub.add_parser("nueva-version"); p.add_argument("produccion"); p.add_argument("escena")
    p.add_argument("--motivo", default=""); p.set_defaults(f=cmd_nueva_version)
    p = sub.add_parser("previa"); p.add_argument("escena"); p.add_argument("--salida", default="salida/previa")
    p.set_defaults(f=cmd_previa)
    p = sub.add_parser("direccion"); p.add_argument("produccion"); p.set_defaults(f=cmd_direccion)
    p = sub.add_parser("aplicar-direccion"); p.add_argument("produccion"); p.add_argument("escena")
    p.add_argument("--camaras", required=True, help="ids separados por comas: camera_001,camera_002")
    p.add_argument("--motivo", default=""); p.set_defaults(f=cmd_aplicar_direccion)
    p = sub.add_parser("catalogo"); p.add_argument("--releases"); p.add_argument("--issues")
    p.add_argument("--infos"); p.add_argument("--salida", default="catalogo.json"); p.set_defaults(f=cmd_catalogo)
    p = sub.add_parser("limpieza"); p.add_argument("--catalogo", required=True); p.set_defaults(f=cmd_limpieza)
    p = sub.add_parser("voces"); p.add_argument("escena"); p.add_argument("--gastar", action="store_true")
    p.set_defaults(f=cmd_voces)
    p = sub.add_parser("audio-estado"); p.set_defaults(f=cmd_audio_estado)
    p = sub.add_parser("voces-lista"); p.set_defaults(f=cmd_voces_lista)
    p = sub.add_parser("animaciones"); p.add_argument("--limite", type=int, default=0)
    p.add_argument("--analizar", action="store_true"); p.set_defaults(f=cmd_animaciones)
    a = ap.parse_args(argv)
    return a.f(a) or 0


if __name__ == "__main__":
    sys.exit(main())
