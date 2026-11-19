"""Versión aprobada → BLEND autónomo + controles para el WAV y el render (bpy). Ver estudio/version_escena.py.

Tres pasos (el flujo «Publicar escena aprobada» los corre en este orden):
  preparar  construye la escena UNA vez con el camino de siempre (director.construir: personajes, cámaras, labios
            desde las alineaciones de ElevenLabs), anota muestras de control (cámara, bocas, caderas), empaqueta y
            guarda el BLEND; con las pistas de ESA construcción genera un WAV de control (procedural.generar, lo
            mismo que hace audio_escena.py) que no se publica: sólo sirve para comprobar el WAV definitivo.
  validar   abre el BLEND guardado en un Blender limpio y comprueba que reproduce la escena sin el Python del
            estudio: cámara de cada cuadro (marcadores), muestras de control, rango, fps, resolución, autonomía.
  cerrar    (sin bpy, en version_escena_cerrar) suma el WAV de audio_escena.py: tiene que ser idéntico al de control.
"""
from __future__ import annotations

import json
import shutil
import time
import zipfile
from pathlib import Path

import bpy

from estudio import config, manifiesto as ME, version_escena as VE
from estudio.autofinisher import auto_pack as AP, medicion as MD

TOL = 1e-4


def _toma_de(tomas: list, f: int):
    """Igual que pruebas/video_30s/render_rango.py: entre dos tomas sigue la de la anterior."""
    for t in tomas:
        if t["frame_inicio"] <= f <= t["frame_fin"]:
            return t
    previas = [t for t in tomas if t["frame_inicio"] <= f]
    if previas:
        return max(previas, key=lambda t: t["frame_inicio"])
    raise SystemExit(f"cuadro {f} sin toma")


def _tramos_camara(res: dict, total: int) -> list[dict]:
    out = []
    for f in range(1, total + 1):
        t = _toma_de(res["tomas"], f)
        if out and out[-1]["camara"] == t["camara"].name and out[-1]["toma"] == t["spec"]["id"]:
            out[-1]["hasta"] = f
        else:
            out.append({"desde": f, "hasta": f, "toma": t["spec"]["id"], "camara": t["camara"].name})
    return out


def _commit() -> str | None:
    import os
    import subprocess
    if os.environ.get("GITHUB_SHA"):
        return os.environ["GITHUB_SHA"]
    r = subprocess.run(["git", "-C", str(config.RAIZ), "rev-parse", "HEAD"], capture_output=True, text=True)
    return r.stdout.strip() or None


def _cuadros_control(total: int) -> list[int]:
    return sorted({1, 2, total - 1, total, *range(30, total, 150)} & set(range(1, total + 1)))


def _medir(s, objetos_forma: list[str], caderas: dict) -> dict:
    """Estado del cuadro actual: cámara activa, valores de las formas animadas (bocas, cejas…), caderas."""
    cam = s.camera
    d = {"camara": cam.name if cam else None,
         "camara_pos": [round(v, 5) for v in cam.matrix_world.translation] if cam else None, "formas": {}, "caderas": {}}
    for n in objetos_forma:
        o = bpy.data.objects.get(n)
        if o is None:
            continue
        ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get())
        kb = (ev.data.shape_keys or o.data.shape_keys).key_blocks
        d["formas"][n] = {k.name: round(k.value, 5) for k in kb if k.name != "Basis"}
    for pid, (arm, hueso) in caderas.items():
        o = bpy.data.objects.get(arm)
        if o is not None and hueso in o.pose.bones:
            d["caderas"][pid] = [round(v, 5) for v in (o.matrix_world @ o.pose.bones[hueso].head)]
    return d


def _objetos_con_formas_animadas() -> list[str]:
    out = []
    for o in bpy.data.objects:
        if o.type == "MESH" and o.data.shape_keys and o.data.shape_keys.animation_data \
                and o.data.shape_keys.animation_data.action and not o.hide_render:
            out.append(o.name)
    return sorted(out)


def _voces(m: dict) -> tuple[list[dict], list[Path]]:
    """Voces de la mezcla y de las caras (mp3 + alineación) que usó esta construcción, con sus huellas."""
    from estudio.audio import elevenlabs as EL
    voces, archivos = [], []
    for ev in (m.get("sonido") or {}).get("eventos", []):
        if ev.get("tipo") != "voz":
            continue
        mp3 = EL.ruta_en_biblioteca(ev)
        alin = EL.ruta_alineacion(ev)
        v = {"origen": "sonido", "rol": ev.get("rol"), "texto": ev.get("texto"), "inicio_s": ev.get("inicio_s"),
             "recorte_s": ev.get("recorte_s"), "volumen": ev.get("volumen", 1.0),
             "audio": str(mp3.relative_to(config.RAIZ)), "audio_sha256": MD.sha256(mp3)}
        archivos.append(mp3)
        if alin.exists():
            v["alineacion"] = str(alin.relative_to(config.RAIZ))
            v["alineacion_sha256"] = MD.sha256(alin)
            archivos.append(alin)
        voces.append(v)
    for pj in m.get("personajes", []):
        for h in (pj.get("cara") or {}).get("habla", []):
            v = {"origen": f"cara:{pj['id']}", "texto": h.get("texto"), "inicio_s": h.get("inicio_s"),
                 "recorte_s": h.get("recorte_s")}
            for k in ("audio", "alineacion"):
                if isinstance(h.get(k), str):
                    p = config.ruta_recurso(h[k])
                    v[k] = h[k]
                    v[k + "_sha256"] = MD.sha256(p)
                    archivos.append(p)
            voces.append(v)
    unicos = sorted({p.resolve() for p in archivos})
    return voces, unicos


def preparar(ruta_escena: str, salida: str, ensayo: bool = False) -> dict:
    from estudio import recursos as R
    from estudio.audio import procedural
    from estudio.blender import director as D
    crono = MD.Cronometro()
    ruta_escena = Path(ruta_escena)
    m = ME.leer(ruta_escena)
    err = ME.validar(m)
    if not ensayo:
        err += VE.errores_aprobacion(m)
    if err:
        raise SystemExit("NO SE PUBLICA:\n  - " + "\n  - ".join(err))
    R.exigir(m)                                   # voces, alineaciones, clips y modelos: si falta algo, se corta
    nb = VE.nombres(m)
    out = Path(salida)
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f"{out} no está vacía: una versión no se arma encima de otra")
    (out / "_control").mkdir(parents=True, exist_ok=True)
    calidad = m.get("render", {}).get("calidad", "revision")
    with crono.etapa("construir"):
        res = D.construir(m, calidad)
    s = res["escena"]
    total = res.get("frames_pelicula", s.frame_end)
    if m.get("mapa_tiempo"):
        raise SystemExit("La escena usa cámara lenta (mapa_tiempo): el BLEND solo no reproduce los sub-cuadros. "
                         "Esta versión no se puede publicar para el render desde BLEND.")
    if (s.frame_start, s.frame_end) != (1, total):
        raise SystemExit(f"rango de la escena {s.frame_start}-{s.frame_end} ≠ 1-{total} cuadros de la película")
    assert s.render.engine == "CYCLES", s.render.engine
    with crono.etapa("audio_de_control"):
        pistas = D.exportar_pistas(res, out / "_control" / "pistas.json")
        wav_control = procedural.generar(m, pistas, out / "_control" / "audio.wav")
    # lo mismo que fijaba render_rango.py en cada trabajo, ahora guardado en el BLEND
    c = s.cycles
    c.seed = 0
    c.use_animated_seed = False
    s.render.image_settings.file_format = "PNG"
    s.render.image_settings.color_mode = "RGB"
    s.render.image_settings.color_depth = "8"
    tramos = _tramos_camara(res, total)
    formas = _objetos_con_formas_animadas()
    caderas = {pid: (pj["armadura"].name, pj["info"]["cadera"]) for pid, pj in res["personajes"].items()
               if pj.get("armadura") is not None and pj.get("info", {}).get("cadera")}
    control = {}
    with crono.etapa("muestras_de_control"):
        for f in _cuadros_control(total):
            t = _toma_de(res["tomas"], f)
            s.camera = t["camara"]                  # como el render de siempre: la cámara de la toma
            D.ir_a(res, f)
            control[str(f)] = _medir(s, formas, caderas)
    s.frame_set(1)
    s.camera = res["tomas"][0]["camara"]
    with crono.etapa("empaquetar"):
        # datos que ninguna cosa de la escena usa (p. ej. los materiales que trae el FBX de un pelo, cuyas mallas se
        # borran al importarlo): no se ven en el render y algunos apuntan a texturas que no existen
        huerfanos = bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
        emp = AP.empaquetar()
    if not emp["autonomo"]:
        usos = {n.split(":", 1)[1]: [u.name for u in bpy.data.user_map(subset=[bpy.data.images[n.split(":", 1)[1]]])
                                     [bpy.data.images[n.split(":", 1)[1]]]]
                for n in emp["externos"] if n.startswith("imagen:") and n.split(":", 1)[1] in bpy.data.images}
        raise SystemExit(f"El BLEND no queda autónomo, hay recursos afuera: {emp['externos'][:10]} (los usan: {usos})")
    with crono.etapa("guardar_blend"):
        D.guardar_blend(out / nb["blend"])
    shutil.copy(ruta_escena, out / nb["escena"])
    voces, archivos = _voces(m)
    with zipfile.ZipFile(out / nb["voces"], "w", zipfile.ZIP_STORED) as z:
        for p in archivos:
            z.write(p, str(p.relative_to(config.RAIZ.resolve())))
    q = config.CALIDADES[calidad]
    man = {
        "formato": VE.FORMATO, "completo": False, "ensayo": ensayo,
        "produccion": m["produccion"], "escena": VE.eid(m), "version": m["version"], "id": f"{m['id']}-v{m['version']}",
        "release": VE.tag_release(m), "titulo": m.get("titulo", ""), "huella": ME.huella(m),
        "huella_aprobada": VE.aprobada(m), "construido": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "archivos": {"blend": MD.archivo(out / nb["blend"]), "escena": MD.archivo(out / nb["escena"]),
                     "voces": MD.archivo(out / nb["voces"])},
        "audio_control": {"sha256": MD.sha256(wav_control), "bytes": wav_control.stat().st_size,
                          "generador": "estudio.audio.procedural.generar (pistas de esta misma construcción)"},
        "render": {"motor": s.render.engine, "dispositivo": c.device, "calidad": calidad,
                   "resolucion": [s.render.resolution_x, s.render.resolution_y], "fps": s.render.fps,
                   "cuadro_inicial": 1, "cuadro_final": total, "cuadros": total,
                   "numeracion_archivos": "1..N (f_0001.png)", "muestras": c.samples,
                   "muestreo_adaptativo": c.use_adaptive_sampling, "umbral_adaptativo": round(c.adaptive_threshold, 4),
                   "denoiser": c.denoiser, "rebotes_max": c.max_bounces, "arbol_de_luces": c.use_light_tree,
                   "semilla": c.seed, "semilla_animada": c.use_animated_seed, "crf": q.get("crf", 22),
                   "duracion_s": m["duracion_s"]},
        "tomas": tramos, "voces": voces,
        "control": {"objetos_con_formas": formas, "caderas": {k: list(v) for k, v in caderas.items()},
                    "cuadros": control},
        "dependencias_externas": emp["externos"], "empaquetados": len(emp["empaquetados"]),
        "datos_sin_uso_eliminados": huerfanos,
        "versiones": {"blender": bpy.app.version_string, "commit": _commit()},
        "tiempos": {"etapas": crono.etapas, "total_s": crono.total(), "ram_max_mb": MD.ram_max_mb()},
    }
    (out / nb["manifiesto"]).write_text(json.dumps(man, indent=1, ensure_ascii=False))
    print(f"PREPARADA {man['release']}: {total} cuadros, BLEND {man['archivos']['blend']['mb']} MB, "
          f"{len(voces)} voces, {len(formas)} mallas con formas animadas, control de audio {man['audio_control']['sha256'][:12]}")
    return man


def validar(salida: str) -> dict:
    """En un Blender recién abierto: el BLEND guardado da la misma cámara, bocas y caderas que la construcción."""
    out = Path(salida)
    man = json.loads((out / "manifest.json").read_text())
    blend = out / man["archivos"]["blend"]["nombre"]
    ok, motivo = VE.verificar(man, "blend", blend)
    if not ok:
        raise SystemExit("VALIDACIÓN: " + motivo)
    bpy.ops.wm.open_mainfile(filepath=str(blend.resolve()))
    s = bpy.context.scene
    r = man["render"]
    problemas = []
    for k, v in (("cuadro_inicial", s.frame_start), ("cuadro_final", s.frame_end), ("fps", s.render.fps),
                 ("muestras", s.cycles.samples)):
        if r[k] != v:
            problemas.append(f"{k}: BLEND {v} ≠ manifiesto {r[k]}")
    if [s.render.resolution_x, s.render.resolution_y] != r["resolucion"]:
        problemas.append(f"resolución {s.render.resolution_x}x{s.render.resolution_y} ≠ {r['resolucion']}")
    rev = AP.revisar()
    if not rev["autonomo"]:
        problemas.append(f"recursos externos: {rev['externos'][:5]}")
    # cámara de CADA cuadro según los marcadores guardados (lo que usa Blender al renderizar)
    marcas = sorted((mk.frame, mk.camera.name) for mk in s.timeline_markers if mk.camera)
    def cam_marcador(f):
        c = None
        for fr, n in marcas:
            if fr <= f:
                c = n
        return c
    mal_cam = [f for t in man["tomas"] for f in range(t["desde"], t["hasta"] + 1) if cam_marcador(f) != t["camara"]]
    if mal_cam:
        problemas.append(f"{len(mal_cam)} cuadros con otra cámara por los marcadores (p. ej. {mal_cam[:8]})")
    ctl = man["control"]
    caderas = {k: tuple(v) for k, v in ctl["caderas"].items()}
    comparados = 0
    for f, esperado in ctl["cuadros"].items():
        s.frame_set(int(f))                          # sin el Python del estudio: como renderiza Blender
        real = _medir(s, ctl["objetos_con_formas"], caderas)
        if real["camara"] != esperado["camara"]:
            problemas.append(f"cuadro {f}: cámara {real['camara']} ≠ {esperado['camara']}")
        if real["camara_pos"] and esperado["camara_pos"] and \
                max(abs(a - b) for a, b in zip(real["camara_pos"], esperado["camara_pos"])) > TOL * 10:
            problemas.append(f"cuadro {f}: la cámara está en otro lugar {real['camara_pos']} ≠ {esperado['camara_pos']}")
        for n, claves in esperado["formas"].items():
            for k, v in claves.items():
                rv = real["formas"].get(n, {}).get(k)
                if rv is None or abs(rv - v) > TOL * 10:
                    problemas.append(f"cuadro {f}: {n}.{k} = {rv} ≠ {v}")
                comparados += 1
        for pid, v in esperado["caderas"].items():
            rv = real["caderas"].get(pid)
            if rv is None or max(abs(a - b) for a, b in zip(rv, v)) > 1e-3:
                problemas.append(f"cuadro {f}: cadera de {pid} {rv} ≠ {v}")
    inf = {"ok": not problemas, "problemas": problemas[:40], "n_problemas": len(problemas),
           "cuadros_de_control": len(ctl["cuadros"]), "valores_de_formas_comparados": comparados,
           "cuadros_con_camara_verificada": sum(t["hasta"] - t["desde"] + 1 for t in man["tomas"]),
           "marcadores": len(marcas), "blender": bpy.app.version_string}
    (out / "_control" / "validacion_blend.json").write_text(json.dumps(inf, indent=1, ensure_ascii=False))
    print(json.dumps(inf, indent=1, ensure_ascii=False))
    if problemas:
        raise SystemExit("VALIDACIÓN DEL BLEND FALLÓ: " + "; ".join(problemas[:5]))
    return inf
