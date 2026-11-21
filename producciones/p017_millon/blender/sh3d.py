"""p016 · recursos Sweet Home 3D (muebles, árboles) del respaldo de Nexus: se importan UNA vez y se instancian (mallas compartidas).
Convención verificada con renders: al importar el GLB a Blender el FRENTE del mueble mira hacia −Y (sofá, heladera y estantes se ven de frente desde −Y).
`poner(..., frente=(dx, dy))` gira el objeto para que su frente mire hacia ese vector (en el plano XY)."""
import math
import os
import random
import re
import bpy
from mathutils import Vector, Euler

D = os.environ.get("SH3D_DIR", "/home/user/Operaci-n-Nexus-1/game/assets/sh3d/models/")
_BIB = {}
_COL_BIB = None
ULTIMOS = []          # objetos creados por la última llamada a poner() (para animarlos)


def _col_bib():
    global _COL_BIB
    if _COL_BIB is None:
        _COL_BIB = bpy.data.collections.get("SH3D_biblioteca") or bpy.data.collections.new("SH3D_biblioteca")
        if _COL_BIB.name not in bpy.context.scene.collection.children:
            bpy.context.scene.collection.children.link(_COL_BIB)
    return _COL_BIB


def cargar(id_):
    """Importa el modelo a la biblioteca (oculto), centrado en XY y apoyado en z=0. Devuelve {objs, dim}."""
    if id_ in _BIB:
        return _BIB[id_]
    antes = set(bpy.data.objects.keys())
    ruta = D + id_ + ".glb"
    if not os.path.exists(ruta):
        import glob
        c = sorted(glob.glob(D + "*_" + id_ + ".glb"), key=len)
        if not c:
            raise FileNotFoundError(id_)
        ruta = c[0]
    bpy.ops.import_scene.gltf(filepath=ruta)
    nuevos = [bpy.data.objects[n] for n in bpy.data.objects.keys() if n not in antes]
    cb = _col_bib()
    for o in nuevos:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        cb.objects.link(o)
        o.rotation_mode = "XYZ" if o.parent is None else o.rotation_mode
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in nuevos if o.type == "MESH" for c in o.bound_box]
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    off = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
    for o in nuevos:
        if o.parent is None:
            o.location -= off
    bpy.context.view_layer.update()
    for o in nuevos:
        o.hide_render = True
        o.hide_viewport = True
    _BIB[id_] = {"objs": nuevos, "dim": mx - mn}
    return _BIB[id_]


def poner(id_, col, pos, frente=(0.0, -1.0), escala=1.0, nombre=None, sobre=None):
    """Instancia el modelo (mallas compartidas) en `col` con el frente mirando hacia `frente`. Devuelve la raíz."""
    b = cargar(id_)
    yaw = math.atan2(frente[0], -frente[1])
    mapa = {}
    for o in b["objs"]:
        n = o.copy()
        n.name = (nombre or id_) + "_" + o.name[:18]
        col.objects.link(n)
        n.hide_render = False
        n.hide_viewport = False
        mapa[o] = n
    raiz = None
    raices = [(o, n) for o, n in mapa.items() if o.parent is None]
    for o, n in mapa.items():
        if o.parent is not None and o.parent in mapa:
            n.parent = mapa[o.parent]
    if len(raices) > 1:
        # modelo con varias piezas sueltas (cada una con su propio desplazamiento/escala): se agrupan bajo un vacío que lleva la posición, el giro y la escala
        g = bpy.data.objects.new((nombre or id_) + "_grupo", None)
        col.objects.link(g)
        g.rotation_mode = "XYZ"
        g.location = Vector(pos) + (Vector((0, 0, 0)) if sobre is None else Vector((0, 0, sobre)))
        g.rotation_euler = Euler((0, 0, yaw), "XYZ")
        g.scale = (escala, escala, escala)
        for o, n in raices:
            n.parent = g
            n.matrix_parent_inverse = g.matrix_world.inverted()
            n.matrix_parent_inverse.identity()
        mapa[None] = g
        raiz = g
    else:
        for o, n in raices:
            raiz = n
            n.parent = None
            n.rotation_mode = "XYZ"
            n.location = Vector(pos) + (Vector((0, 0, 0)) if sobre is None else Vector((0, 0, sobre)))
            n.rotation_euler = Euler((0, 0, yaw), "XYZ")
            n.scale = (escala, escala, escala)
    global ULTIMOS
    ULTIMOS = list(mapa.values())
    return raiz


# ───────────────────────────────────────────── árboles reales con follaje denso (copas de «bolas de hojas» sobre las hojas del modelo)
TINTES = {"sc_acacia": (0.95, 1.05, 0.6), "tree_weeping_willow": (1.1, 1.15, 0.65), "tree_birch": (1.05, 1.1, 0.7), "tree_quaking_aspen": (1.0, 1.1, 0.65),
          "tree_black_tupelo": (0.8, 0.95, 0.55), "tree_sassafras": (0.9, 1.0, 0.55), "tree_tree": (0.85, 1.0, 0.55)}


def _blobs():
    import bmesh
    from mathutils import noise
    mallas = []
    for k in range(3):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
        for v in bm.verts:
            n = noise.noise(v.co * 1.7 + Vector((k * 13.1, k * 7.7, k * 3.3)))
            n2 = noise.noise(v.co * 5.2 + Vector((k * 5.3, 1.0, 9.0)))
            v.co *= 1.0 + 0.22 * n + 0.07 * n2
        me = bpy.data.meshes.new(f"copa_base_{k}")
        bm.to_mesh(me)
        bm.free()
        for p in me.polygons:
            p.use_smooth = True
        mallas.append(me)
    return mallas


def material_hojas():
    m = bpy.data.materials.get("follaje_real")
    if m:
        return m
    m = bpy.data.materials.new("follaje_real")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    r = nt.nodes.new("ShaderNodeTexNoise")
    r.inputs["Scale"].default_value = 3.5
    r.inputs["Detail"].default_value = 6.0
    nt.links.new(tc.outputs["Object"], r.inputs["Vector"])
    rp = nt.nodes.new("ShaderNodeValToRGB")
    rp.color_ramp.elements[0].position = 0.35
    rp.color_ramp.elements[0].color = (0.05, 0.12, 0.03, 1)
    rp.color_ramp.elements[1].position = 0.72
    rp.color_ramp.elements[1].color = (0.22, 0.34, 0.08, 1)
    nt.links.new(r.outputs["Fac"], rp.inputs["Fac"])
    nt.links.new(rp.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.72
    b.inputs["Subsurface Weight"].default_value = 0.2
    return m


def preparar_arbol(id_, semilla=1, copias=4):
    """Árbol REAL de Sweet Home: se conserva su tronco, ramas y hojas con forma; para que la copa sea frondosa se duplica la geometría de hojas
    girada alrededor del eje del tronco (cada copia rota y crece un poco), sin bolas ni esferas."""
    b = cargar(id_)
    if b.get("vestido"):
        return b
    rng = random.Random(semilla)
    cb = _col_bib()
    extra = []
    hojas = [o for o in b["objs"] if o.type == "MESH" and re.match(r"^(leav|foil|stems|branchtw|oldleav)", o.name.lower())]
    raices = [o for o in b["objs"] if o.parent is None]
    raiz = raices[0]
    for c in hojas:
        for k in range(copias):
            n = c.copy()
            n.name = f"{c.name}_d{k}"
            cb.objects.link(n)
            n.hide_render = True
            n.hide_viewport = True
            n.parent = c.parent
            n.matrix_parent_inverse = c.matrix_parent_inverse.copy()
            n.rotation_mode = "XYZ"
            ang = 2 * math.pi * (k + 1) / (copias + 1) + rng.uniform(-0.3, 0.3)
            # giro alrededor de la vertical por el centro del tronco (origen de la raíz)
            n.matrix_world = Euler((0, 0, ang), "XYZ").to_matrix().to_4x4() @ c.matrix_world
            s_ = rng.uniform(1.0, 1.12)
            n.scale = (n.scale[0] * s_, n.scale[1] * s_, n.scale[2] * s_)
            extra.append(n)
    b["objs"] = b["objs"] + extra
    b["vestido"] = True
    return b
