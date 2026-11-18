"""Personajes humanos de «Un sueño de a dos» (p010) sobre los maniquíes del dueño.

Los FBX de Tripo3D (esqueleto mixamorig de 65 huesos, ~0,95 m al importar, miran a −Y) vienen blancos y sin rostro.
Se conservan tal cual (cabeza, cuerpo y esqueleto) y el estudio les pone:
  · PIEL: color del personaje con dispersión subsuperficial y poros para Cycles.
  · ROSTRO dibujado estilo anime realista, con el sistema de los Stickman (estudio/blender/cara_anime.py):
    ojos con iris y brillo, párpados, cejas, nariz sugerida, labios y rubor; expresiones, boca con la voz real,
    miradas y parpadeo (`stickman.actuar`).
  · PELO esculpido (una masa bien formada con mechones, como arcilla) con vaivén (estudio/blender/pelo_esculpido.py).
  · ROPA Y ZAPATOS (estudio/blender/ropa_humana.py).

Manifiesto: {"id": "el", "modelo": "humano:chico", "alto_m": 1.78,
             "cara": {"expresiones": [...], "miradas": [...], "habla": [{"inicio_s": …, "audio": "audio/biblioteca/…",
                      "texto": "…"}]}, "acciones": [...]}
Las rutas de audio van RELATIVAS al repositorio (en GitHub Actions la carpeta del repo tiene otro nombre).
"""
from __future__ import annotations
from pathlib import Path

import bpy

from estudio import config

BASE_SUBIDAS = "subidas:un_sueno_de_a_dos"
MODELOS = {
    "humano:chico": {"ref": f"{BASE_SUBIDAS}/chico/tripo_convert_149bc4a7-9bf8-493a-b51e-14da191a88e2.fbx",
                     "alto_modelo": 0.93},
    "humano:chica": {"ref": f"{BASE_SUBIDAS}/chica/tripo_convert_31e45afb-e5aa-4aab-9cc4-3e59349d0581.fbx",
                     "alto_modelo": 0.98},
}

PERFILES = {
    "humano:chico": {
        "cara": "el", "piel": (0.80, 0.60, 0.48), "labios": (0.70, 0.46, 0.43), "iris": (0.36, 0.22, 0.12),
        "cejas": (0.06, 0.04, 0.03), "pelo": (0.05, 0.035, 0.028), "peinado": "corto_texturizado",
        # imagen de referencia: buzo negro con capucha, jean oscuro (y zapatillas y reloj, que no se ven)
        "vestuario": [{"prenda": "jean", "color": [0.07, 0.072, 0.085], "holgura": 0.012},
                      {"prenda": "buzo_capucha", "color": [0.04, 0.04, 0.045]},
                      {"prenda": "zapatillas", "color": [0.10, 0.10, 0.11], "suela": [0.95, 0.94, 0.91],
                       "detalle": [0.92, 0.92, 0.92]},
                      {"prenda": "reloj"}],
    },
    "humano:chica": {
        "cara": "ella", "piel": (0.86, 0.67, 0.56), "labios": (0.80, 0.45, 0.47), "iris": (0.38, 0.22, 0.11),
        "cejas": (0.13, 0.08, 0.05), "pelo": (0.11, 0.065, 0.04), "peinado": "rodete_desprolijo",
        # imagen de referencia: campera de jean sobre remera azul, jean oscuro, cartera de cuero cruzada y aros
        "vestuario": [{"prenda": "remera", "color": [0.07, 0.09, 0.22]},
                      {"prenda": "jean", "color": [0.12, 0.12, 0.14], "holgura": 0.006},
                      {"prenda": "campera_jean", "color": [0.33, 0.43, 0.57]},
                      {"prenda": "zapatillas", "color": [0.95, 0.95, 0.94], "suela": [0.97, 0.96, 0.93],
                       "detalle": [0.85, 0.85, 0.86]},
                      {"prenda": "cartera", "color": [0.36, 0.20, 0.10]},
                      {"prenda": "aros"}],
    },
}


def _lineal(c):
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)


def material_piel(nombre: str, color, rug=0.5):
    """Piel para Cycles: dispersión subsuperficial (rojiza), poros en relieve y un leve brillo."""
    mat = bpy.data.materials.new(nombre)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    lin = _lineal(color)
    bsdf.inputs["Base Color"].default_value = (*lin, 1)
    bsdf.inputs["Roughness"].default_value = rug
    for k, v in (("Subsurface Weight", 0.25), ("Subsurface Scale", 0.012), ("Specular IOR Level", 0.45),
                 ("Coat Weight", 0.05), ("Coat Roughness", 0.35)):
        try:
            bsdf.inputs[k].default_value = v
        except KeyError:
            pass
    try:
        bsdf.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.2)
    except KeyError:
        pass
    vo = nt.nodes.new("ShaderNodeTexVoronoi")
    vo.inputs["Scale"].default_value = 900.0
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 300.0
    mx = nt.nodes.new("ShaderNodeMath")
    mx.operation = "ADD"
    nt.links.new(vo.outputs["Distance"], mx.inputs[0])
    nt.links.new(nz.outputs["Fac"], mx.inputs[1])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.1
    bump.inputs["Distance"].default_value = 0.0004
    nt.links.new(mx.outputs[0], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    mat.diffuse_color = (*lin, 1)
    mat["estudio"] = {"color": list(lin), "rugosidad": rug, "metal": 0.0, "emision": None, "fuerza": 0.0, "alfa": 1.0}
    return mat


def ruta_audio(ruta: str) -> str:
    """Las voces se guardan con la ruta relativa al repositorio; acá se resuelve donde esté el repo."""
    p = Path(ruta)
    return str(p if p.is_absolute() else config.RAIZ / p)


def preparar(pj: dict, spec: dict, fps: int, nf: int):
    """Piel, rostro, pelo, ropa y zapatos de un humano recién creado por personajes._crear_mixamo."""
    from estudio.blender import cara_anime as CA, pelo_esculpido as PE, ropa_humana as RH, stickman as SM
    modelo = spec["modelo"]
    perfil = {**PERFILES[modelo], **spec.get("perfil", {})}
    pj["coleccion"] = pj["malla"].users_collection[0]
    pj["u"] = 1.0 / pj["raiz"].scale.x                      # 1 metro real en unidades del modelo
    pj["perfil"] = perfil
    piel = material_piel(f"piel_{pj['id']}", perfil["piel"])
    pj["malla"].data.materials.clear()
    pj["malla"].data.materials.append(piel)
    partes = CA.armar(pj, perfil["cara"], perfil, pj["coleccion"])
    pj["cara"] = partes
    cara = dict(spec.get("cara", {}))
    cara["habla"] = [{**h, "audio": ruta_audio(h["audio"])} if h.get("audio") else h for h in cara.get("habla", [])]
    SM.actuar(partes, cara, fps, nf, semilla=sum(map(ord, pj["id"])))
    PE.construir(pj, perfil["peinado"], perfil["pelo"])
    PE.mover(pj, fps, nf, spec.get("viento", 1.0))
    RH.vestir(pj, perfil.get("vestuario", []))
    return pj
