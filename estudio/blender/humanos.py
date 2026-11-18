"""Personajes humanos (serie espacial) sobre los maniquíes del dueño.

Los FBX de Tripo3D (esqueleto mixamorig de 65 huesos, ~0,95 m al importar, miran a −Y) aportan el cuerpo y el
esqueleto (las animaciones de Mixamo andan igual). El estudio les pone:
  · CABEZA de MakeHuman TAL CUAL (hombre o mujer por defecto, sin retoques), del tamaño que corresponde a la
    altura del cuerpo, fundida en el cuello (estudio/blender/cabeza_mh.py), con ojos, dientes, lengua, pestañas,
    cejas de pelitos y piel con dispersión subsuperficial.
  · ROSTRO 3D: las 59 unidades de expresión de MakeHuman + parpadeo completo; expresiones, microexpresiones,
    mirada con sacádicos y labios con la voz (estudio/blender/expresiones_3d.py).
  · PELO realista: hebras guía + hijas para Cycles y tarjetas con transparencia para el teléfono
    (estudio/blender/pelo_realista.py). Él: degradé militar peinado hacia atrás. Ella: largo, suelto y peinado.
  · TRAJE DE PRIMERA PIEL (va debajo del traje espacial, que viene después) (estudio/blender/ropa_humana.py).

Manifiesto: {"id": "el", "modelo": "humano:chico", "alto_m": 1.80,
             "cara": {"expresiones": [...], "miradas": [...], "habla": [{"inicio_s": …,
                      "audio": "audio/biblioteca/voz_….mp3", "texto": "…"}]}, "acciones": [...]}
Las rutas de audio van RELATIVAS al repositorio (en GitHub Actions la carpeta del repo tiene otro nombre).
"""
from __future__ import annotations

BASE_SUBIDAS = "subidas:un_sueno_de_a_dos"
MODELOS = {
    "humano:chico": {"ref": f"{BASE_SUBIDAS}/chico/tripo_convert_149bc4a7-9bf8-493a-b51e-14da191a88e2.fbx",
                     "alto_modelo": 0.93},
    "humano:chica": {"ref": f"{BASE_SUBIDAS}/chica/tripo_convert_31e45afb-e5aa-4aab-9cc4-3e59349d0581.fbx",
                     "alto_modelo": 0.98},
}

TRAJE = {"prenda": "traje_primera_piel", "color": [0.13, 0.14, 0.16], "acento": [0.15, 0.62, 0.78],
         "paneles": [0.20, 0.21, 0.24]}

PERFILES = {
    "humano:chico": {
        "genero": 1.0, "piel": (0.80, 0.62, 0.50), "labios": (0.70, 0.47, 0.44), "barba": 0.22,
        "iris": (0.30, 0.20, 0.12), "cejas": (0.07, 0.05, 0.035),
        "pelo_modelo": "hair02", "peinado": "degrade_militar", "pelo": (0.07, 0.05, 0.035), "melanina": 0.86,
        "rojizo": 0.3,
        "vestuario": [TRAJE],
    },
    "humano:chica": {
        "genero": 0.0, "piel": (0.86, 0.68, 0.57), "labios": (0.78, 0.46, 0.47), "barba": 0.0,
        "iris": (0.34, 0.21, 0.11), "cejas": (0.15, 0.09, 0.06),
        "pelo_modelo": "summer_girl", "peinado": "largo_suelto", "pelo": (0.16, 0.09, 0.05), "melanina": 0.72,
        "rojizo": 0.45,
        "vestuario": [TRAJE],
    },
}


def preparar(pj: dict, spec: dict, fps: int, nf: int, otros: dict | None = None):
    """Cabeza, rostro, pelo y traje de un humano recién creado por personajes._crear_mixamo."""
    from estudio.blender import cabeza_mh as CM, expresiones_3d as E3, pelo_realista as PR, ropa_humana as RH
    perfil = {**PERFILES[spec["modelo"]], **spec.get("perfil", {})}
    pj["coleccion"] = pj["malla"].users_collection[0]
    pj["u"] = 1.0 / pj["raiz"].scale.x                      # 1 metro real en unidades del modelo
    pj["escala_cabeza"] = perfil.get("escala_cabeza", 1.0)
    pj["perfil"] = perfil
    CM.armar(pj, perfil)
    E3.actuar(pj, spec.get("cara", {}), fps, nf, otros)
    if perfil.get("pelo_modelo"):                          # pelo ya modelado (los que sube el dueño)
        from estudio.blender import pelo_modelo as PM
        PM.poner(pj, perfil["pelo_modelo"], perfil["pelo"], perfil.get("pelo_holgura", 1.12))
    elif perfil.get("peinado"):
        PR.construir(pj, perfil["peinado"], perfil["pelo"], perfil["melanina"], perfil["rojizo"],
                     sum(map(ord, pj["id"])))
    RH.vestir(pj, perfil.get("vestuario", []))
    return pj
