"""AutoPack (bpy): empaqueta TODO dentro del .blend y comprueba que no quede nada afuera. Si un recurso no se puede
empaquetar (biblioteca vinculada, caché externa, imagen que no existe), lo informa y la construcción falla antes de
publicar: el .blend tiene que abrirse igual en cualquier máquina de render."""
from __future__ import annotations

import bpy


def empaquetar() -> dict:
    try:
        bpy.ops.file.pack_all()
    except RuntimeError as e:          # pack_all avisa por cada archivo que no encuentra
        aviso = str(e)
    else:
        aviso = ""
    return revisar(aviso)


def revisar(aviso: str = "") -> dict:
    emp, ext = [], []
    for i in bpy.data.images:
        if i.source in ("FILE", "SEQUENCE", "MOVIE", "TILED"):
            (emp if i.packed_file else ext).append(f"imagen:{i.name}")
    for coleccion, etiqueta in ((bpy.data.sounds, "sonido"), (bpy.data.fonts, "fuente"), (bpy.data.volumes, "volumen")):
        for x in coleccion:
            if getattr(x, "filepath", "") and x.filepath != "<builtin>":
                (emp if x.packed_file else ext).append(f"{etiqueta}:{x.name}")
    ext += [f"biblioteca:{lib.filepath}" for lib in bpy.data.libraries]
    ext += [f"cache:{c.filepath}" for c in bpy.data.cache_files]
    ext += [f"clip:{c.filepath}" for c in bpy.data.movieclips]
    return {"empaquetados": sorted(emp), "externos": sorted(ext), "aviso": aviso, "autonomo": not ext}
