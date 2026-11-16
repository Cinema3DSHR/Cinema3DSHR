"""Director: arma una escena completa en Blender a partir de su manifiesto JSON y la renderiza por tomas.

El manifiesto es la "receta" editable de la escena (ver docs/MANIFIESTOS.md). Con él y los recursos referenciados
la escena se reconstruye siempre igual: el .blend que se guarda es una comodidad para editar a mano, no la fuente.
"""
from __future__ import annotations
import importlib
import json
import math
import time
from pathlib import Path

import bpy
from estudio import config
from estudio.blender import kit as K
from estudio.blender import camaras as C
from estudio.blender import vehiculos as V
from estudio.blender import personajes as P
from estudio.blender import pelota as B


def _modulo_escenario(gen: str):
    return importlib.import_module(f"estudio.escenarios.{gen}")


def construir(manifiesto: dict, calidad: str = "revision") -> dict:
    fps = manifiesto.get("render", {}).get("fps", 30)
    K.reiniciar_materiales()
    P.reiniciar()
    s = K.escena_vacia(manifiesto["id"])
    s.render.fps = fps  # antes de importar: los clips glTF se convierten a cuadros con este valor
    esc = manifiesto["escenario"]
    mod = _modulo_escenario(esc["generador"])
    info = mod.construir(esc.get("parametros", {}))
    ctx = C.Contexto(info["anclas"], fps)
    ctx.mapa = manifiesto.get("mapa_tiempo")          # cámara lenta: la película recorre la escena más despacio
    ctx.moviles.update(info.get("moviles", {}))      # vehículos y vagones animados por el propio escenario

    # eventos del escenario (abrir portón, encender luces…)
    for ev in manifiesto.get("eventos", []):
        fn = getattr(mod, ev["accion"], None)
        if fn is None:
            raise ValueError(f"El escenario {esc['generador']} no sabe hacer {ev['accion']!r}")
        fn(info["animables"], frame_inicio=int(ev["inicio_s"] * fps) + 1,
           **{k: v for k, v in ev.items() if k not in ("accion", "inicio_s")})

    # vehículos
    for vh in manifiesto.get("vehiculos", []):
        modelo = vh.get("modelo", "procedural:sedan")
        if modelo == "procedural:sedan":
            veh = V.sedan_procedural(vh["id"], tuple(vh.get("color", (0.02, 0.02, 0.025))))
        else:
            raise NotImplementedError(f"Modelo de vehículo {modelo} todavía no soportado (ver docs/VEHICULOS.md)")
        puntos = [ctx.punto(p, 0) for p in vh["recorrido"]]
        tray = V.animar_por_recorrido(veh, puntos, int(vh.get("inicio_s", 0) * fps) + 1,
                                      [tuple(x) for x in vh["tiempos"]], fps,
                                      duracion_s=manifiesto.get("duracion_s"))
        ctx.moviles[vh["id"]] = {"tray": tray, "anclas": veh["anclas"]}

    # personajes animados (bancos de clips)
    pjs = {}
    seguidos = {t.get("movil") for t in manifiesto["tomas"]} | {
        (t.get(k) or {}).get("movil") for t in manifiesto["tomas"] for k in ("objetivo", "desde", "hasta", "centro", "foco")
        if isinstance(t.get(k), dict)}
    # el retarget evalúa la escena hueso por hueso y cuadro por cuadro: con el escenario afuera de la capa de vista
    # (miles de objetos: árboles, vía, tren) no se re-evalúa todo en cada paso
    excluidas = []
    for lc in s.view_layers[0].layer_collection.children:
        if not lc.exclude:
            lc.exclude = True
            excluidas.append(lc)
    try:
        # personajes de la receta + los que calcula el escenario (p. ej. Mateo bajándose donde frenó el auto)
        for spec in manifiesto.get("personajes", []) + info.get("personajes", []):
            pjs[spec["id"]] = P.crear(spec, fps)
    finally:
        for lc in excluidas:
            lc.exclude = False
    duracion_f = int(round(manifiesto["duracion_s"] * fps))
    for pid, pj in pjs.items():
        if pid in seguidos:
            ctx.moviles[pid] = {"tray": _muestrear_personaje(pj, duracion_f), "anclas": ANCLAS_PERSONAJE}

    # pelota con física (sale de una patada)
    if manifiesto.get("pelota"):
        _pelota(manifiesto["pelota"], pjs, ctx, fps, duracion_f)

    # tomas
    tomas = [C.crear_toma(t, ctx) for t in manifiesto["tomas"]]
    duracion_f = max(t["frame_fin"] for t in tomas)
    s.frame_start, s.frame_end = 1, int(math.ceil(ctx.cuadro(duracion_f)))     # la escena dura menos si hay cámara lenta
    s.render.fps = fps
    s.camera = tomas[0]["camara"]
    _cabinas_por_toma(tomas, ctx)
    ajustes_render(s, calidad, manifiesto.get("render", {}))
    return {"escena": s, "tomas": tomas, "contexto": ctx, "info": info, "personajes": pjs, "frames_pelicula": duracion_f}


def _cabinas_por_toma(tomas: list, ctx):
    """La cabina de Dream Rally (habitáculo y pilotos) se ve SÓLO en las tomas «interior» de su auto; desde afuera no."""
    def descendientes(o):
        for h in o.children:
            yield h
            yield from descendientes(h)
    for mid, m in ctx.moviles.items():
        raiz = m.get("objeto")
        if raiz is None:
            continue
        partes = [o for o in descendientes(raiz) if o.get("cabina_dr") and not o.hide_render]
        if not partes:
            continue
        tramos = []
        for t in tomas:
            sp = t["spec"]
            if sp.get("movil") == mid and sp.get("punto_base") == "interior":
                a, b = ctx.cuadro(t["frame_inicio"]), ctx.cuadro(t["frame_fin"])
                tramos.append((a - 1e-3, b + (ctx.cuadro(t["frame_fin"] + 1) - b) * 0.5))
        for o in partes:
            hasta = float(o.get("oculto_desde", 1e9))      # p. ej. Mateo se baja del auto: desde ahí no está más
            claves = [(-10.0, True)] + [k for a, b in tramos if a < hasta for k in ((a, False), (min(b, hasta), True))]
            for fr, oculto in claves:
                o.hide_render = oculto
                o.hide_viewport = oculto
                o.keyframe_insert("hide_render", frame=fr)
                o.keyframe_insert("hide_viewport", frame=fr)
            for ruta in ("hide_render", "hide_viewport"):
                fc = o.animation_data.action.fcurve_ensure_for_datablock(o, ruta)
                for kp in fc.keyframe_points:
                    kp.interpolation = "CONSTANT"


def ir_a(res: dict, f_pelicula: int):
    """Pone la escena en el instante que se ve en el cuadro f de la PELÍCULA (con cámara lenta, un sub-cuadro)."""
    fe = res["contexto"].cuadro(f_pelicula)
    entero = int(math.floor(fe))
    res["escena"].frame_set(entero, subframe=fe - entero)


ANCLAS_PERSONAJE = {"cadera": (0, 0, 0), "cabeza": (0, 0, 0.62), "pecho": (0, 0, 0.35), "pies": (0, 0, -0.9),
                    "": (0, 0, 0)}


def _muestrear_personaje(pj: dict, duracion_f: int) -> dict:
    """Trayectoria de la cadera por cuadro (para que las cámaras sigan a un personaje)."""
    sc = bpy.context.scene
    arm = pj["armadura"]
    hueso = arm.pose.bones[pj["info"]["cadera"]]
    tray = {}
    prev = None
    for f in range(1, duracion_f + 1):
        sc.frame_set(f)
        pos = (arm.matrix_world @ hueso.head).copy()
        # rumbo de la convención de móviles (0 = mirando a +Y): dirección en que mira el modelo menos 90°
        rumbo = (pj["raiz"].matrix_world.to_euler().z + math.radians(pj["info"].get("adelante_deg", 0))
                 - math.pi / 2)
        v = 0.0 if prev is None else (pos - prev).length * sc.render.fps
        tray[f] = (pos, rumbo, v)
        prev = pos
    return tray


def _pelota(spec: dict, pjs: dict, ctx, fps: int, duracion_f: int):
    """Arma la pelota: reposo hasta la patada; después, física pura (FISICA_E_IA.md)."""
    from mathutils import Vector
    ob = B.crear("pelota", K.coleccion("objetos"))
    pat = spec.get("patada")
    reposo = Vector(ctx.punto(spec["inicio"], 1)) if spec.get("inicio") else None
    if not pat:
        ob.location = reposo or (0, 0, B.RADIO)
        return
    t_contacto = pat.get("tiempo_s")
    pj = pjs.get(pat.get("personaje", ""))
    if t_contacto is None and pj:
        clip = pat.get("clip") or pj["tramos"][-1]["accion"].name
        tr = next(t for t in pj["tramos"] if t["accion"].name == clip)
        golpeo = _golpeo(clip)
        tc = (golpeo or {}).get("tc", 0.35)
        t_contacto = (tr["f0"] - 1) / fps + tc / (1.0 / tr["strip"].scale)
    f_contacto = int(round(t_contacto * fps)) + 1
    if reposo is None and pj:
        # la pelota espera donde va a pegar el pie: la punta más adelantada en el cuadro de contacto
        bpy.context.scene.frame_set(f_contacto)
        arm = pj["armadura"]
        pies = [(arm.matrix_world @ arm.pose.bones[h].head) for h in (pj["info"]["pie_der"], pj["info"]["pie_izq"])]
        reposo = min(pies, key=lambda v: v.z).copy()
        reposo.z = B.RADIO
    reposo = reposo or Vector((0, 0, B.RADIO))
    arco_x = {"este": 52.5, "oeste": -52.5}.get(pat.get("arco", "este"))
    destino = ctx.punto(pat["destino"], f_contacto)
    v0 = B.resolver_tiro(reposo, destino, pat.get("velocidad", 25.0), tuple(pat.get("efecto", (0, 0, 0))), arco_x)
    tray = B.simular(reposo, v0, tuple(pat.get("efecto", (0, 0, 0))),
                     duracion=max(0.5, (duracion_f - f_contacto) / fps), arco_x=arco_x)
    B.animar(ob, tray, f_contacto, fps, reposo=reposo)
    t_tray = {}
    for i in range(0, len(tray), int(round(240 / fps))):
        t, p, v, w = tray[i]
        t_tray[f_contacto + int(round(t * fps))] = (p.copy(), math.atan2(-v.x, v.y) if v.length > 0.1 else 0.0, v.length)
    t_tray[1] = (reposo.copy(), 0.0, 0.0)
    for f in range(1, f_contacto):
        t_tray[f] = (reposo.copy(), 0.0, 0.0)
    ctx.moviles["pelota"] = {"tray": t_tray, "anclas": {"": (0, 0, 0)}}
    ctx.eventos.append({"tipo": "patada", "t": t_contacto, "pos": list(reposo)})
    if arco_x is not None:
        for t, p_, v_, w_ in tray:
            if abs(p_.x) > abs(arco_x) and abs(p_.y) < B.ARCO["ancho"] / 2 and p_.z < B.ARCO["alto"]:
                ctx.eventos.append({"tipo": "gol", "t": t_contacto + t, "pos": list(p_)})
                break
    print(f"[pelota] patada en t={t_contacto:.2f} s, salida {v0.length:.1f} m/s hacia {tuple(round(c, 2) for c in destino)}")


def _golpeo(clip: str) -> dict | None:
    ruta = config.CATALOGO / "futbol.json"
    if not ruta.exists():
        return None
    base = clip[2:] if clip[:2] in ("f_", "k_", "s_") else clip
    for c in json.loads(ruta.read_text())["clips"]:
        if c["clip"] == clip and c.get("golpeo"):
            return c["golpeo"]
        if c["clip"].endswith(base.replace("_mirror", "")) and c.get("golpeo"):
            return c["golpeo"]
    return None


def ajustes_render(s, calidad: str, extra: dict):
    q = {**config.CALIDADES[calidad], **{k: v for k, v in extra.items() if k in ("muestras", "motor")}}
    s.render.engine = q["motor"]
    s.render.resolution_x, s.render.resolution_y = q["ancho"], q["alto"]
    s.render.resolution_percentage = 100
    s.render.image_settings.file_format = "JPEG"
    s.render.image_settings.quality = 92
    s.render.use_motion_blur = extra.get("desenfoque_movimiento", False)
    try:
        s.view_settings.view_transform = "AgX"
        s.view_settings.look = extra.get("look", "AgX - Medium High Contrast")
    except TypeError:
        try:
            s.view_settings.look = "Medium High Contrast"
        except TypeError:
            pass
    s.view_settings.exposure = extra.get("exposicion", 0.0)
    if q["motor"] == "BLENDER_EEVEE":
        e = s.eevee
        e.taa_render_samples = q["muestras"]
        for attr, val in (("use_raytracing", extra.get("trazado_rayos", True)),
                          ("use_shadows", True),
                          ("use_volumetric_shadows", False),
                          ("volumetric_tile_size", "16"),
                          ("use_bloom", True)):
            try:
                setattr(e, attr, val)
            except (AttributeError, TypeError):
                pass
        try:
            e.ray_tracing_options.resolution_scale = "2"
            e.ray_tracing_options.use_denoise = True
            e.fast_gi_method = "GLOBAL_ILLUMINATION"
        except (AttributeError, TypeError):
            pass
    elif q["motor"] == "CYCLES":
        c = s.cycles
        c.device = "CPU"
        c.samples = q["muestras"]
        c.use_adaptive_sampling = True
        c.adaptive_threshold = 0.05
        c.use_denoising = True
        try:
            c.denoiser = "OPENIMAGEDENOISE"
            c.denoising_input_passes = "RGB_ALBEDO_NORMAL"
        except TypeError:
            pass
        c.max_bounces = 6
        c.diffuse_bounces = 2
        c.glossy_bounces = 3
        c.transmission_bounces = 4
        c.transparent_max_bounces = 8
        c.caustics_reflective = False
        c.caustics_refractive = False
        c.sample_clamp_indirect = 8.0
        s.render.use_persistent_data = True  # reutiliza la escena entre fotogramas (mucho más rápido)


def render_tomas(res: dict, carpeta: Path, solo: list[str] | None = None, cada: int = 1) -> dict:
    """Renderiza cada toma a JPG en carpeta/<toma>/f_0001.jpg. Reanuda si ya hay fotogramas.

    cada > 1 renderiza sólo 1 de cada N fotogramas (previsualización rápida tipo "animática").
    """
    s = res["escena"]
    informe = {}
    for t in res["tomas"]:
        tid = t["spec"]["id"]
        if solo and tid not in solo:
            continue
        d = carpeta / tid
        d.mkdir(parents=True, exist_ok=True)
        s.camera = t["camara"]
        t0 = time.time()
        hechos = 0
        for i, f in enumerate(range(t["frame_inicio"], t["frame_fin"] + 1)):
            if i % cada:
                continue
            out = d / f"f_{i + 1:04d}.jpg"
            if out.exists() and out.stat().st_size > 0:
                continue
            ir_a(res, f)
            s.render.filepath = str(out)
            bpy.ops.render.render(write_still=True)
            hechos += 1
        informe[tid] = {"fotogramas": t["frame_fin"] - t["frame_inicio"] + 1, "renderizados": hechos,
                        "segundos": round(time.time() - t0, 1)}
        print(f"[render] {tid}: {informe[tid]}", flush=True)
    return informe


def guardar_blend(ruta: Path):
    """Guarda el proyecto editable. Se descartan los clips de las bibliotecas que la escena no usa (el modelo de
    fútbol trae 3 223): se pueden volver a cargar en cualquier momento desde el recurso original."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    # el prototipo oculto de cada biblioteca guarda TODOS los clips como pistas NLA "estacionadas": se limpian
    for o in bpy.data.objects:
        if any(c.name.startswith("BIBLIOTECA_") for c in o.users_collection) and o.animation_data:
            o.animation_data_clear()
    usadas = set()
    for o in bpy.data.objects:
        ad = o.animation_data
        if ad:
            if ad.action:
                usadas.add(ad.action)
            for tr in ad.nla_tracks:
                for st in tr.strips:
                    if st.action:
                        usadas.add(st.action)
    for a in list(bpy.data.actions):
        if a not in usadas:
            bpy.data.actions.remove(a)
    bpy.ops.wm.save_as_mainfile(filepath=str(ruta), compress=True)


def exportar_visor(ruta: Path, max_tex: int = 512):
    """GLB liviano para el visor Android: colores planos (sin texturas procedurales), luces, cámaras y animación.

    Se omiten fondo lejano de alto costo y la geometría oculta. Las instancias se realizan (el visor no las tiene).
    """
    ruta.parent.mkdir(parents=True, exist_ok=True)
    # en el visor los materiales procedurales se reemplazan por su color base equivalente
    for m in bpy.data.materials:
        meta = m.get("estudio")
        if not meta or not m.use_nodes:
            continue
        bsdf = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if bsdf is None:
            continue
        if bsdf.inputs["Emission Strength"].is_linked:  # ventanas procedurales: en el visor, silueta oscura
            for l in list(bsdf.inputs["Emission Strength"].links):
                m.node_tree.links.remove(l)
            bsdf.inputs["Emission Strength"].default_value = 0.0
        for inp in ("Base Color", "Roughness", "Normal", "Emission Color"):
            for l in list(bsdf.inputs[inp].links):
                m.node_tree.links.remove(l)
        bsdf.inputs["Base Color"].default_value = (*meta["color"], 1)
        if meta.get("emision"):
            bsdf.inputs["Emission Color"].default_value = (*meta["emision"], 1)
        bsdf.inputs["Roughness"].default_value = meta["rugosidad"]
    for o in bpy.data.objects:
        if o.get("visor_omitir"):
            o.hide_set(True)
            o.select_set(False)
    bpy.ops.export_scene.gltf(filepath=str(ruta), use_visible=True, export_format="GLB", export_apply=True,
                              export_lights=True, export_cameras=True, export_animations=True,
                              export_yup=True, export_image_format="WEBP" if max_tex else "AUTO",
                              export_extras=True, export_animation_mode="SCENE", export_bake_animation=False)
    return ruta.stat().st_size


def exportar_pistas(res: dict, ruta: Path) -> dict:
    """Datos de la escena por fotograma para el sonido y la app (no necesitan Blender para leerse).

    camara_activa: [x, y, z, derecha_x, derecha_y] de la cámara de la toma vigente en cada fotograma.
    moviles: {id: [[x, y, z, velocidad_m_s], …]} por fotograma.
    """
    s = res["escena"]
    ctx = res["contexto"]
    cortes = sorted((t["frame_inicio"], t["frame_fin"], t["camara"]) for t in res["tomas"])
    cam_activa = []
    fin = res.get("frames_pelicula", s.frame_end)
    for f in range(1, fin + 1):
        cam = next((c for a, b, c in cortes if a <= f <= b), cortes[-1][2])
        ir_a(res, f)
        mw = cam.matrix_world
        der = mw.to_3x3() @ __import__("mathutils").Vector((1, 0, 0))
        cam_activa.append([round(v, 3) for v in (*mw.translation, der.x, der.y)])
    moviles = {}
    for mid, m in ctx.moviles.items():
        tray = m["tray"]
        f0, f1 = min(tray), max(tray)
        filas = []
        for f in range(1, fin + 1):
            fe = ctx.cuadro(f)
            pos, rumbo, v = ctx.estado(m, fe)
            filas.append([round(pos.x, 3), round(pos.y, 3), round(pos.z, 3), round(v if f0 <= fe <= f1 else 0.0, 3)])
        moviles[mid] = filas
    rpm = {}
    for mid, m in ctx.moviles.items():          # régimen real de los vehículos con física de Dream Rally (sonido del motor)
        if m.get("rpm"):
            r = list(m["rpm"])
            rpm[mid] = [r[min(max(int(ctx.cuadro(f)) - 1, 0), len(r) - 1)] for f in range(1, fin + 1)]
    datos = {"fps": s.render.fps, "frames": fin, "mapa_tiempo": ctx.mapa, "camara_activa": cam_activa, "moviles": moviles, "rpm": rpm,
             "anclas": {k: list(v) for k, v in ctx.anclas.items()}, "eventos": ctx.eventos,
             "tomas": [{"id": t["spec"]["id"], "frame_inicio": t["frame_inicio"], "frame_fin": t["frame_fin"]}
                       for t in res["tomas"]]}
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(datos))
    return datos
