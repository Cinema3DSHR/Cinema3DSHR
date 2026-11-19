"""Modalidad 2 del pipeline: incorporar un .blend autónomo YA PREPARADO Y APROBADO (sin Godot ni AutoFinisher).

Regla: lo que el dueño aprueba visualmente en Blender es EXACTAMENTE lo que se renderiza. El archivo aprobado se
identifica por su SHA-256 y su tamaño; nada de esta modalidad abre el .blend para escribirlo (sólo lectura: nunca
`save`, nunca `pack_all`). Si el archivo no es autónomo o su configuración de render no es la de producción, se rechaza
y se informa el motivo: no se «arregla» porque eso cambiaría lo aprobado.

Pasos (docs/CONSTRUIR_Y_RENDERIZAR.md → «Modalidad 2»):
  1. `aprobar-blend` (en la sesión, cuando el dueño dijo «aprobada»): inspecciona el .blend, comprueba el perfil de
     render y escribe el REGISTRO DE APROBACIÓN en el repo (`producciones/<p>/versiones/v<NNN>.aprobacion.json`):
     SHA-256, bytes, perfil, inspección y la frase del dueño. Un registro no se sobrescribe.
  2. `incorporar_blend.yml` (nube): baja el .blend desde donde esté (Release de entrada o URL), comprueba que su
     SHA-256 sea el del registro, lo inspecciona de nuevo, arma la versión (copia byte a byte + manifest.json con
     origen «blend_externo» + informe), la valida con `validar`, la publica en `blend-<p>-v<NNN>` y llama al render.
  3. `render_desde_blend.yml`: igual que siempre (hash antes de abrir en cada trabajo). Con origen «blend_externo»
     NO acepta cambiar resolución ni muestras: se renderiza con lo aprobado.
"""
from __future__ import annotations

import datetime
import json
import shutil
from pathlib import Path

from estudio.autofinisher import manifiesto as MF, medicion as MD

FORMATO_APROBACION = "estudio.aprobacion_blend/1"

# Perfil de render obligatorio de producción (pedido del dueño, 19/11/2026): 720p 16:9, 30 fps, Cycles CPU, 6 muestras,
# muestreo adaptativo 0,05, OpenImageDenoise, 6 rebotes, Light Tree y semilla fija.
PERFIL_720P = {
    "motor": "CYCLES",
    "dispositivo": "CPU",
    "resolucion": [1280, 720],
    "porcentaje": 100,
    "fps": 30,
    "fps_base": 1.0,
    "muestras": 6,
    "muestreo_adaptativo": True,
    "umbral_adaptativo": 0.05,
    "denoise": True,
    "denoiser": "OPENIMAGEDENOISE",
    "rebotes": 6,
    "arbol_de_luces": True,
    "semilla_animada": False,
}
# Variante vertical 9:16 (Reels/Shorts), autorizada por el dueño el 19/11/2026 para p013: misma cantidad de píxeles que
# 1280×720 (720×1280) y todo lo demás idéntico. Sólo se elige si la producción declara «720x1280» en su formato.
PERFIL_VERTICAL = {**PERFIL_720P, "resolucion": [720, 1280]}


def perfil_de(formato: dict | None) -> dict:
    """Perfil de producción que corresponde al formato declarado (por defecto, el 720p horizontal obligatorio)."""
    res = str((formato or {}).get("resolucion", "")).lower().replace(" ", "")
    return PERFIL_VERTICAL if res == "720x1280" else PERFIL_720P


# ── inspección de sólo lectura (bpy) ─────────────────────────────────────────────────────────────────────────────

def inspeccionar(ruta_blend: str | Path) -> dict:
    """Abre el .blend SIN modificarlo y devuelve lo necesario para decidir si se puede renderizar tal cual."""
    import bpy
    from bpy_extras import anim_utils
    from estudio.autofinisher import auto_pack

    p = Path(ruta_blend).resolve()
    antes = (p.stat().st_size, p.stat().st_mtime_ns)
    bpy.ops.wm.open_mainfile(filepath=str(p))
    s = bpy.context.scene
    c = s.cycles
    cam = s.camera
    cam_anim = False
    if cam is not None and cam.animation_data and cam.animation_data.action:
        cb = anim_utils.action_get_channelbag_for_slot(cam.animation_data.action, cam.animation_data.action_slot)
        cam_anim = bool(cb and len(cb.fcurves))
    animados = sorted(o.name for o in bpy.data.objects if o.animation_data and o.animation_data.action)
    emp = auto_pack.revisar()
    d = {
        "archivo": p.name,
        "blender_guardado": ".".join(str(x) for x in bpy.data.version),
        "blender_lector": bpy.app.version_string,
        "escena": s.name,
        "render": {
            "motor": s.render.engine,
            "dispositivo": getattr(c, "device", None),
            "resolucion": [s.render.resolution_x, s.render.resolution_y],
            "porcentaje": s.render.resolution_percentage,
            "fps": s.render.fps,
            "fps_base": round(s.render.fps_base, 6),
            "muestras": c.samples,
            "muestreo_adaptativo": c.use_adaptive_sampling,
            "umbral_adaptativo": round(c.adaptive_threshold, 6),
            "denoise": c.use_denoising,
            "denoiser": c.denoiser,
            "rebotes": c.max_bounces,
            "arbol_de_luces": c.use_light_tree,
            "semilla": c.seed,
            "semilla_animada": c.use_animated_seed,
            "cuadro_inicial": s.frame_start,
            "cuadro_final": s.frame_end,
        },
        "camara": cam.name if cam else None,
        "camara_animada": cam_anim,
        "objetos": len(bpy.data.objects),
        "objetos_animados": len(animados),
        "acciones": sorted(a.name for a in bpy.data.actions),
        "materiales": len(bpy.data.materials),
        "luces": len([o for o in bpy.data.objects if o.type == "LIGHT"]),
        "empaquetados": emp["empaquetados"],
        "externos": emp["externos"],
        "autonomo": emp["autonomo"],
    }
    despues = (p.stat().st_size, p.stat().st_mtime_ns)
    if despues != antes:      # nunca debería pasar: esta función no guarda nada
        raise RuntimeError(f"el .blend cambió durante la inspección: {antes} → {despues}")
    return d


# ── reglas (sin bpy) ─────────────────────────────────────────────────────────────────────────────────────────────

def problemas(insp: dict, perfil: dict = PERFIL_720P, formato: dict | None = None) -> list[str]:
    """Todo lo que impide renderizar el archivo TAL CUAL. Lista vacía = se puede incorporar."""
    e = []
    r = insp["render"]
    for k, v in perfil.items():
        actual = r.get(k)
        if isinstance(v, float):
            ok = actual is not None and abs(float(actual) - v) < 1e-6
        else:
            ok = actual == v
        if not ok:
            e.append(f"render.{k}: el .blend tiene {actual!r} y producción pide {v!r}")
    if r.get("semilla") is None:
        e.append("render.semilla: no hay semilla")
    if insp.get("camara") is None:
        e.append("la escena no tiene cámara activa")
    if not insp.get("autonomo"):
        e.append(f"recursos externos sin empaquetar: {insp.get('externos')}")
    cuadros = r["cuadro_final"] - r["cuadro_inicial"] + 1
    if cuadros < 1:
        e.append(f"rango de cuadros vacío: {r['cuadro_inicial']}..{r['cuadro_final']}")
    if formato:
        if formato.get("fps") and formato["fps"] != r["fps"]:
            e.append(f"fps {r['fps']} ≠ {formato['fps']} de la producción")
        if formato.get("duracion_s") and formato.get("fps"):
            esperado = round(formato["duracion_s"] * formato["fps"])
            if cuadros != esperado:
                e.append(f"{cuadros} cuadros ≠ {esperado} de la producción ({formato['duracion_s']} s a {formato['fps']} fps)")
        if formato.get("resolucion"):
            res = [int(x) for x in str(formato["resolucion"]).lower().split("x")]
            if res != list(r["resolucion"]):
                e.append(f"resolución {r['resolucion']} ≠ {res} de la producción")
    return e


def ruta_registro(raiz_produccion: str | Path, version: int) -> Path:
    return Path(raiz_produccion) / "versiones" / f"v{int(version):03d}.aprobacion.json"


def registro(produccion: str, version: int, blend: str | Path, insp: dict, nota: str, formato: dict | None) -> dict:
    a = MD.archivo(blend)
    return {
        "formato": FORMATO_APROBACION,
        "produccion": produccion,
        "version": int(version),
        "id": MF.id_version(produccion, version),
        "release": MF.tag_release(produccion, version),
        "blend": {"sha256": a["sha256"], "bytes": a["bytes"], "nombre_original": Path(blend).name},
        "aprobacion": {
            "nota_del_dueno": nota,
            "fecha_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "regla": "se renderiza exactamente este archivo (mismo SHA-256), sin reconstruir ni modificar nada",
        },
        "perfil_render": perfil_de(formato),
        "formato_produccion": formato or {},
        "inspeccion": {k: v for k, v in insp.items() if k not in ("empaquetados",)} | {"empaquetados": len(insp["empaquetados"])},
    }


def errores_registro(reg: dict) -> list[str]:
    e = []
    if reg.get("formato") != FORMATO_APROBACION:
        e.append(f"formato: se esperaba «{FORMATO_APROBACION}»")
    for k in ("produccion", "version", "id", "release", "blend", "aprobacion"):
        if k not in reg:
            e.append(f"falta «{k}»")
    if e:
        return e
    if reg["id"] != MF.id_version(reg["produccion"], reg["version"]) or reg["release"] != MF.tag_release(reg["produccion"], reg["version"]):
        e.append("id o release no corresponden a produccion + version")
    if len(str(reg["blend"].get("sha256", ""))) != 64:
        e.append("blend.sha256 falta o no es un SHA-256")
    if not reg["aprobacion"].get("nota_del_dueno"):
        e.append("falta la frase de aprobación del dueño")
    return e


def verificar_contra_registro(reg: dict, ruta_blend: str | Path) -> tuple[bool, str]:
    p = Path(ruta_blend)
    if not p.exists():
        return False, f"no está {p}"
    if p.stat().st_size != reg["blend"]["bytes"]:
        return False, f"tamaño {p.stat().st_size} ≠ {reg['blend']['bytes']} del registro de aprobación"
    h = MD.sha256(p)
    if h != reg["blend"]["sha256"]:
        return False, f"SHA-256 {h} ≠ {reg['blend']['sha256']} aprobado"
    return True, f"{p.name}: {reg['blend']['bytes']} bytes, SHA-256 {h} = el aprobado ({reg['id']})"


def manifiesto_externo(reg: dict, blend: Path, informe: Path, insp: dict) -> dict:
    r = insp["render"]
    m = {
        "formato": MF.FORMATO,
        "origen": "blend_externo",
        "ajustes_bloqueados": True,
        "produccion": reg["produccion"],
        "version": reg["version"],
        "id": reg["id"],
        "release": reg["release"],
        "titulo": reg.get("titulo", ""),
        "construido": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "archivos": {"blend": MD.archivo(blend),
                     "informe": {"nombre": informe.name, "bytes": informe.stat().st_size}},
        "render": {
            "motor": r["motor"], "dispositivo": r["dispositivo"], "resolucion": list(r["resolucion"]),
            "fps": r["fps"], "cuadro_inicial": r["cuadro_inicial"], "cuadro_final": r["cuadro_final"],
            "cuadros": r["cuadro_final"] - r["cuadro_inicial"] + 1, "numeracion_archivos": "1..N (f_0001.png)",
            "muestras": r["muestras"],
            "muestreo_adaptativo": {"activo": r["muestreo_adaptativo"], "umbral": r["umbral_adaptativo"]},
            "denoiser": r["denoiser"], "rebotes": r["rebotes"], "arbol_de_luces": r["arbol_de_luces"],
            "semilla": r["semilla"], "camara": insp["camara"],
        },
        "dependencias": {"empaquetadas": insp["empaquetados"], "externas": insp["externos"]},
        "versiones": {"blender_guardado": insp["blender_guardado"], "blender_validacion": insp["blender_lector"],
                      "receta_sha256": None, "aprobacion_sha256": None},
        "revision": {"estado": "aprobada", "nota": reg["aprobacion"]["nota_del_dueno"],
                     "fecha_utc": reg["aprobacion"]["fecha_utc"]},
    }
    return m


# ── comandos (bpy) ───────────────────────────────────────────────────────────────────────────────────────────────

def aprobar(blend: str, raiz_produccion: str, version: int, nota: str) -> dict:
    """Registra la aprobación del dueño para ESTE archivo (por su hash). No copia ni toca el .blend."""
    raiz = Path(raiz_produccion)
    prod_json = json.loads((raiz / "produccion.json").read_text())
    produccion = prod_json["id"]
    destino = ruta_registro(raiz, version)
    if destino.exists():
        raise FileExistsError(f"{destino} ya existe: una aprobación no se sobrescribe (otra versión = otro número)")
    insp = inspeccionar(blend)
    err = problemas(insp, perfil_de(prod_json.get("formato")), prod_json.get("formato"))
    if err:
        raise SystemExit("El .blend no se puede aprobar para render tal cual:\n  - " + "\n  - ".join(err))
    reg = registro(produccion, version, blend, insp, nota, prod_json.get("formato"))
    reg["titulo"] = prod_json.get("titulo", "")
    e = errores_registro(reg)
    if e:
        raise SystemExit("registro inválido: " + "; ".join(e))
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(reg, ensure_ascii=False, indent=1))
    return {"registro": str(destino), "id": reg["id"], "sha256": reg["blend"]["sha256"], "bytes": reg["blend"]["bytes"]}


def incorporar(blend: str, ruta_registro_aprobacion: str, salida: str) -> dict:
    """Arma la versión publicable a partir del archivo aprobado: copia byte a byte, manifiesto e informe."""
    reg = json.loads(Path(ruta_registro_aprobacion).read_text())
    e = errores_registro(reg)
    if e:
        raise SystemExit("registro de aprobación inválido: " + "; ".join(e))
    ok, motivo = verificar_contra_registro(reg, blend)
    if not ok:
        raise SystemExit(f"INCORPORACIÓN DETENIDA: el archivo recibido no es el aprobado: {motivo}")
    out = Path(salida)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"{out} ya existe y tiene archivos: una versión no se sobrescribe")
    insp = inspeccionar(blend)
    err = problemas(insp, perfil_de(reg.get("formato_produccion")), reg.get("formato_produccion"))
    if err:
        raise SystemExit("INCORPORACIÓN DETENIDA: " + "; ".join(err))
    out.mkdir(parents=True, exist_ok=True)
    nom = MF.nombres(reg["produccion"], reg["version"])
    dest_blend = out / nom["blend"]
    shutil.copyfile(blend, dest_blend)            # copia de bytes: el archivo publicado ES el aprobado
    ok2, motivo2 = verificar_contra_registro(reg, dest_blend)
    if not ok2:
        shutil.rmtree(out, ignore_errors=True)
        raise SystemExit(f"la copia no coincide con el aprobado: {motivo2}")
    shutil.copyfile(ruta_registro_aprobacion, out / "aprobacion.json")
    informe = out / nom["informe"]
    informe.write_text(json.dumps({"formato": "estudio.informe_incorporacion/1", "origen": "blend_externo",
                                   "verificacion_hash": motivo, "inspeccion": insp}, ensure_ascii=False, indent=1))
    m = manifiesto_externo(reg, dest_blend, informe, insp)
    m["versiones"]["aprobacion_sha256"] = MD.sha256(out / "aprobacion.json")
    em = MF.errores(m)
    if em:
        shutil.rmtree(out, ignore_errors=True)
        raise SystemExit("manifiesto inválido: " + "; ".join(em))
    (out / nom["manifiesto"]).write_text(json.dumps(m, ensure_ascii=False, indent=1))
    return {"salida": str(out), "id": m["id"], "release": m["release"], "blend_sha256": m["archivos"]["blend"]["sha256"],
            "cuadros": m["render"]["cuadros"], "verificacion": motivo}
