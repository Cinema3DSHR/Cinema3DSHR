"""Inventario y búsqueda de animaciones (catalogo/animaciones.json).

Fuentes (sólo lectura; los originales nunca se tocan):
- mixamo-respaldo/indice.json            3099 FBX de Mixamo (Y Bot, 30 fps, esqueleto mixamorig de 65 huesos)
- mixamo-respaldo/packs_extra_glb/extras.json   clips dentro de GLB (personas: mixamorig 66 huesos; perro)

Para cada clip se derivan FUNCIONES (qué hace realmente: caminar, recargar, morir…), ARMA, POSTURA, si es
EN EL LUGAR o con desplazamiento, si probablemente es un BUCLE y un GRUPO de similares (variantes del mismo
movimiento). La selección (`buscar`) puntúa por texto (nombre + descripción en inglés y español) y filtra por
contexto (arma, postura, en el lugar, duración), así no se elige sólo por el nombre del archivo.

`--analizar` abre una muestra con Blender y verifica esqueleto (huesos y nombres) y desplazamiento de la cadera
(root motion), y lo guarda en catalogo/analisis_animaciones.json.
"""
from __future__ import annotations
import json
import re
import unicodedata
from pathlib import Path
from estudio import config

# función → palabras clave (inglés de Mixamo y español de las descripciones traducidas)
FUNCIONES = {
    "idle": ["idle", "standing", "breathing", "parado", "ocioso", "inactivo", "esperando", "waiting"],
    "caminar": ["walk", "walking", "camin", "strut", "stroll"],
    "correr": ["run", "running", "jog", "corr", "trot"],
    "sprint": ["sprint", "fast run", "esprint"],
    "agacharse": ["crouch", "crouching", "agach", "kneel", "duck", "cuclillas", "arrodill"],
    "arrastrarse": ["crawl", "prone", "arrastr", "gatear", "cuerpo a tierra"],
    "saltar": ["jump", "hop", "leap", "vault", "salt", "parkour", "flip"],
    "caer": ["fall", "falling", "trip", "stumble", "caer", "caida", "tropez"],
    "levantarse": ["get up", "getting up", "stand up", "standing up", "rise", "levant", "incorpor"],
    "girar": ["turn", "pivot", "gir", "180", "90"],
    "mirar": ["look", "looking", "search", "scan", "mir", "observ", "buscar"],
    "apuntar": ["aim", "aiming", "apunt"],
    "disparar": ["shoot", "shooting", "fire", "firing", "dispar", "gunplay", "shot"],
    "recargar": ["reload", "recarg"],
    "cambiar_arma": ["equip", "unequip", "draw", "holster", "sheath", "unsheath", "desenfund", "enfund", "switch"],
    "pelear": ["fight", "fighting", "boxing", "brawl", "martial", "capoeira", "pelea", "lucha", "combat"],
    "golpear": ["punch", "kick", "hit", "strike", "slash", "attack", "jab", "hook", "elbow", "knee", "golpe",
                "patad", "ataque", "puñet"],
    "esquivar": ["dodge", "evade", "block", "parry", "roll", "esquiv", "bloque"],
    "recibir_impacto": ["hit reaction", "react", "impact", "stagger", "knocked", "recib", "impacto", "reaccion al golpe"],
    "morir": ["death", "dying", "die", "dead", "killed", "muert", "morir", "muere"],
    "conducir": ["driving", "drive", "steering", "conduc", "manej"],
    "subir_vehiculo": ["enter car", "get in", "entering", "subir", "entrar al auto"],
    "bajar_vehiculo": ["exit car", "get out", "exiting", "bajar", "salir del auto"],
    "sentarse": ["sit", "sitting", "seated", "sent"],
    "interactuar": ["open", "close", "push", "pull", "pick", "grab", "press", "button", "door", "lever", "carry",
                    "lift", "abrir", "cerrar", "empuj", "tirar", "agarr", "levantar objeto", "puerta", "cargar"],
    "gesto": ["gesture", "wave", "point", "salute", "clap", "nod", "shrug", "thumbs", "saluda", "señal", "aplau",
              "asent", "gesto"],
    "hablar": ["talk", "talking", "conversation", "phone", "argue", "habl", "convers", "telefono", "discut"],
    "reaccion": ["surprise", "scared", "afraid", "shock", "terrified", "cheer", "angry", "sad", "laugh", "cry",
                 "sorpr", "miedo", "asust", "enoj", "triste", "rie", "llor", "celebr"],
    "nadar": ["swim", "nad"],
    "trepar": ["climb", "ladder", "trep", "escal"],
    "bailar": ["dance", "dancing", "bail", "breakdance", "hip hop", "salsa", "samba"],
    "lanzar": ["throw", "toss", "grenade", "lanz", "arroj", "granada"],
    "herido": ["injured", "wounded", "limp", "herid", "cojear", "lastim"],
    "sigilo": ["sneak", "stealth", "sigil", "agazap"],
    "magia": ["spell", "magic", "cast", "hechiz", "magia"],
}
ARMAS = {
    "rifle": ["rifle", "gun", "ak", "m4", "assault"], "pistola": ["pistol", "handgun", "pistola"],
    "escopeta": ["shotgun", "escopeta"], "espada": ["sword", "great sword", "espada", "katana"],
    "escudo": ["shield", "escudo"], "arco": ["bow", "longbow", "arco"], "hacha": ["axe", "hacha"],
    "cuchillo": ["knife", "cuchillo", "dagger"],
}
POSTURAS = {"agachado": ["crouch", "agach", "kneel", "arrodill"], "sentado": ["sit", "sent", "driving", "manej"],
            "suelo": ["prone", "crawl", "lying", "laying", "arrastr", "acostad", "tirado"]}
BUCLE = ["idle", "walk", "run", "jog", "sprint", "crawl", "strafe", "loop", "driving", "swim", "dance", "talking",
         "breathing", "typing", "sitting"]


def _norm(t: str) -> str:
    t = unicodedata.normalize("NFKD", t.lower())
    return "".join(c for c in t if not unicodedata.combining(c))


def _contiene(texto: str, claves) -> bool:
    return any(k in texto for k in claves)


def _grupo(nombre: str) -> str:
    n = _norm(nombre)
    n = re.sub(r"(_inplace|_rm|\(\d+\)|_\d+$|\d+$)", "", n)
    return re.sub(r"[^a-z]+", "_", n).strip("_")


def _derivar(texto_en: str, texto_es: str, nombre: str, pack: str) -> dict:
    t = _norm(" ".join([nombre.replace("_", " "), texto_en, texto_es, pack or ""]))
    funciones = [f for f, ks in FUNCIONES.items() if _contiene(t, ks)]
    arma = next((a for a, ks in ARMAS.items() if _contiene(t, ks)), "ninguna")
    if arma == "ninguna" and pack and _contiene(_norm(pack), ["shooter", "rifle"]):
        arma = "rifle"
    postura = next((p for p, ks in POSTURAS.items() if _contiene(t, ks)), "de_pie")
    return {"funciones": funciones or ["otra"], "arma": arma, "postura": postura,
            "bucle_probable": _contiene(t, BUCLE) and not _contiene(t, ["to ", "start", "stop", "end", "death"])}


def construir(limite: int = 0, analizar: bool = False) -> Path:
    raiz = config.FUENTES["mixamo"]
    salida = config.CATALOGO / "animaciones.json"
    clips = []
    usados = set()
    indice = json.loads((raiz / "indice.json").read_text())
    for a in indice:
        if not a.get("descargada", True) or not a["ruta"].lower().endswith(".fbx"):
            continue  # los clips de los GLB extra se leen de extras.json (con su esqueleto real)
        base = re.sub(r"[^a-z0-9]+", "_", _norm(Path(a["ruta"]).with_suffix("").as_posix()))[-80:].strip("_")
        cid = base
        k = 2
        while cid in usados:
            cid = f"{base}_{k}"
            k += 1
        usados.add(cid)
        d = _derivar(a.get("descripcion_en", ""), a.get("descripcion", ""), a.get("nombre", ""), a.get("pack") or "")
        clips.append({
            "id": cid, "ref": f"mixamo:{a['ruta']}", "formato": "fbx", "clip": None,
            "nombre": a.get("nombre"), "descripcion": a.get("descripcion"), "descripcion_en": a.get("descripcion_en"),
            "categoria_origen": a.get("categoria"), "pack": a.get("pack"), "duracion_s": a.get("duracion_s"),
            "fotogramas": a.get("frames"), "fps": 30, "en_el_lugar": bool(a.get("inplace")),
            "esqueleto": "mixamo_65", "bytes": a.get("bytes"), "id_mixamo": a.get("id_mixamo"),
            "grupo": _grupo(a.get("nombre", "")), **d,
        })
    ext = raiz / "packs_extra_glb" / "extras.json"
    if ext.exists():
        for pack in json.loads(ext.read_text()):
            esq = "mixamo_66_root" if pack.get("huesos") == 66 else f"otro_{pack.get('huesos')}"
            for c in pack.get("animaciones", []):
                cid = "glb_" + re.sub(r"[^a-z0-9]+", "_", _norm(Path(pack["archivo"]).stem + "_" + c["clip"]))
                d = _derivar(c["clip"].replace("_", " "), "", c["clip"], "")
                clips.append({
                    "id": cid, "ref": f"mixamo:{pack['archivo']}", "formato": "glb", "clip": c["clip"],
                    "nombre": c["clip"], "descripcion": "", "descripcion_en": c["clip"].replace("_", " "),
                    "categoria_origen": c.get("categoria"), "pack": pack.get("titulo"), "duracion_s": c.get("duracion_s"),
                    "fotogramas": c.get("keyframes"), "fps": c.get("fps_aprox"), "en_el_lugar": not c.get("root_motion"),
                    "esqueleto": esq if "perro" not in pack["archivo"] else "perro_48", "bytes": None,
                    "grupo": _grupo(c["clip"]), **d,
                })
    if limite:
        clips = clips[:limite]
    grupos: dict[str, int] = {}
    for c in clips:
        grupos[c["grupo"]] = grupos.get(c["grupo"], 0) + 1
    for c in clips:
        c["variantes"] = grupos[c["grupo"]] - 1
    resumen = {"total": len(clips), "por_funcion": {}, "por_arma": {}, "por_esqueleto": {}}
    for c in clips:
        for f in c["funciones"]:
            resumen["por_funcion"][f] = resumen["por_funcion"].get(f, 0) + 1
        resumen["por_arma"][c["arma"]] = resumen["por_arma"].get(c["arma"], 0) + 1
        resumen["por_esqueleto"][c["esqueleto"]] = resumen["por_esqueleto"].get(c["esqueleto"], 0) + 1
    config.CATALOGO.mkdir(exist_ok=True)
    salida.write_text(json.dumps({"formato": 1, "fuente": "mixamo-respaldo", "resumen": resumen, "clips": clips},
                                 ensure_ascii=False, indent=0))
    print(json.dumps(resumen, ensure_ascii=False, indent=1))
    if analizar:
        analizar_muestra(clips)
    return salida


def buscar(consulta: str, arma: str | None = None, postura: str | None = None, en_el_lugar: bool | None = None,
           duracion_max: float | None = None, n: int = 10, catalogo: dict | None = None) -> list[dict]:
    """Devuelve los n clips más adecuados. Ej.: buscar("recargar agachado", arma="rifle")."""
    cat = catalogo or json.loads((config.CATALOGO / "animaciones.json").read_text())
    palabras = [p for p in _norm(consulta).split() if len(p) > 2]
    funciones_pedidas = {f for f, ks in FUNCIONES.items() if any(_contiene(p, [k[:5]]) or k.startswith(p[:5]) for p in palabras for k in ks)}
    res = []
    for c in cat["clips"]:
        if arma and c["arma"] != arma:
            continue
        if postura and c["postura"] != postura:
            continue
        if en_el_lugar is not None and c["en_el_lugar"] != en_el_lugar:
            continue
        if duracion_max and (c.get("duracion_s") or 0) > duracion_max:
            continue
        texto = _norm(" ".join(str(c.get(k) or "") for k in ("nombre", "descripcion", "descripcion_en", "pack")))
        p = sum(3 for w in palabras if w in texto) + 4 * len(funciones_pedidas & set(c["funciones"]))
        if p:
            res.append((p - 0.01 * c.get("variantes", 0), c))
    res.sort(key=lambda x: -x[0])
    return [c for _, c in res[:n]]


def analizar_muestra(clips: list[dict], n: int = 40, semilla: int = 3):
    """Abre n clips al azar con Blender: huesos, nombres, rango de fotogramas y desplazamiento de la cadera."""
    import random
    import bpy
    rnd = random.Random(semilla)
    fbx = [c for c in clips if c["formato"] == "fbx" and c["ref"].lower().endswith(".fbx")]
    muestra = rnd.sample(fbx, min(n, len(fbx)))
    out = []
    for c in muestra:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        try:
            bpy.ops.import_scene.fbx(filepath=str(config.resolver(c["ref"])))
        except Exception as e:  # noqa: BLE001
            out.append({"id": c["id"], "error": str(e)})
            continue
        arm = next((o for o in bpy.data.objects if o.type == "ARMATURE"), None)
        act = arm.animation_data.action if arm and arm.animation_data else None
        huesos = [b.name for b in arm.data.bones] if arm else []
        desp = None
        if arm and act:
            pb = arm.pose.bones.get("mixamorig:Hips")
            f0, f1 = act.frame_range
            bpy.context.scene.frame_set(int(f0))
            a = (arm.matrix_world @ pb.head).copy()
            bpy.context.scene.frame_set(int(f1))
            b = (arm.matrix_world @ pb.head).copy()
            desp = [round(v, 3) for v in (b - a)]
        out.append({"id": c["id"], "huesos": len(huesos), "raiz": huesos[0] if huesos else None,
                    "todos_mixamorig": all(h.startswith("mixamorig:") for h in huesos),
                    "rango": list(act.frame_range) if act else None, "desplazamiento_cadera_m": desp,
                    "en_el_lugar_indice": c["en_el_lugar"]})
    (config.CATALOGO / "analisis_animaciones.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    ok = sum(1 for o in out if o.get("huesos") == 65 and o.get("todos_mixamorig"))
    print(f"análisis: {ok}/{len(out)} con el esqueleto mixamorig de 65 huesos")
