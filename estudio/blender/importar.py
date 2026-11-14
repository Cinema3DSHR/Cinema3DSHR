"""Importación de modelos (GLB/GLTF/FBX) sin tocar los originales.

Godot exporta GLB con extensiones obligatorias que el importador de Blender no conoce (p. ej.
KHR_node_visibility). En ese caso se arma una COPIA saneada en la caché (salida/cache/gltf) que sólo quita esas
extensiones de "extensionsRequired"; los nodos marcados invisibles se ocultan después de importar.
"""
from __future__ import annotations
import hashlib
import json
import struct
from pathlib import Path

import bpy
from estudio import config

NO_SOPORTADAS = {"KHR_node_visibility"}


def _leer_glb(ruta: Path):
    datos = ruta.read_bytes()
    magic, version, largo = struct.unpack_from("<4sII", datos, 0)
    if magic != b"glTF":
        raise ValueError(f"{ruta} no es GLB")
    off = 12
    chunks = []
    while off < largo:
        n, tipo = struct.unpack_from("<I4s", datos, off)
        chunks.append([tipo, datos[off + 8: off + 8 + n]])
        off += 8 + n
    return version, chunks


def _escribir_glb(ruta: Path, version: int, chunks):
    cuerpo = b""
    for tipo, d in chunks:
        if tipo == b"JSON\x00"[:4] or tipo == b"JSON":
            d = d + b" " * ((4 - len(d) % 4) % 4)
        else:
            d = d + b"\x00" * ((4 - len(d) % 4) % 4)
        cuerpo += struct.pack("<I4s", len(d), tipo) + d
    ruta.write_bytes(struct.pack("<4sII", b"glTF", version, 12 + len(cuerpo)) + cuerpo)


def copia_compatible(ruta: Path) -> tuple[Path, list[str]]:
    """Devuelve (ruta a importar, nombres de nodos invisibles)."""
    version, chunks = _leer_glb(ruta)
    js = json.loads(chunks[0][1].decode("utf-8"))
    req = set(js.get("extensionsRequired", []))
    invisibles = [n.get("name", "") for n in js.get("nodes", [])
                  if n.get("extensions", {}).get("KHR_node_visibility", {}).get("visible") is False]
    if not (req & NO_SOPORTADAS):
        return ruta, invisibles
    js["extensionsRequired"] = [e for e in js["extensionsRequired"] if e not in NO_SOPORTADAS]
    h = hashlib.sha256(ruta.read_bytes()[:1 << 20] + str(ruta.stat().st_size).encode()).hexdigest()[:12]
    destino = config.SALIDA / "cache" / "gltf" / f"{ruta.stem}_{h}.glb"
    if not destino.exists():
        destino.parent.mkdir(parents=True, exist_ok=True)
        chunks[0][1] = json.dumps(js, separators=(",", ":")).encode("utf-8")
        _escribir_glb(destino, version, chunks)
    return destino, invisibles


def importar(ref_o_ruta, coleccion=None) -> list:
    """Importa y devuelve los objetos nuevos (enlazados a `coleccion` si se indica)."""
    ruta = config.resolver(ref_o_ruta) if isinstance(ref_o_ruta, str) and ":" in ref_o_ruta else Path(ref_o_ruta)
    antes = set(bpy.data.objects)
    invisibles = []
    capa_previa = bpy.context.view_layer.active_layer_collection
    if coleccion is not None:
        # importar directamente en la colección destino (mover miles de objetos después es cuadrático)
        def buscar(lc):
            if lc.collection == coleccion:
                return lc
            for h in lc.children:
                r = buscar(h)
                if r:
                    return r
        lc = buscar(bpy.context.view_layer.layer_collection)
        if lc is not None:
            bpy.context.view_layer.active_layer_collection = lc
    if ruta.suffix.lower() in (".glb", ".gltf"):
        if ruta.suffix.lower() == ".glb":
            ruta, invisibles = copia_compatible(ruta)
        bpy.ops.import_scene.gltf(filepath=str(ruta))
    elif ruta.suffix.lower() == ".fbx":
        bpy.ops.import_scene.fbx(filepath=str(ruta), automatic_bone_orientation=False)
    else:
        raise ValueError(f"Formato no soportado: {ruta.suffix}")
    bpy.context.view_layer.active_layer_collection = capa_previa
    nuevos = [o for o in bpy.data.objects if o not in antes]
    invis = set(invisibles)
    for o in nuevos:
        if o.name in invis:
            o.hide_render = True
            o.hide_viewport = True
        if coleccion is not None and coleccion not in o.users_collection:
            for c in list(o.users_collection):
                c.objects.unlink(o)
            coleccion.objects.link(o)
    return nuevos
