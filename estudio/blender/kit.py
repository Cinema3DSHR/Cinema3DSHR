"""Kit de construcción procedural para Blender (bpy 5.x).

Piezas básicas reutilizables por todos los escenarios: materiales PBR procedurales, cajas con bisel,
cilindros, vidrio, luces, instancias, cielo nocturno, niebla y utilidades de animación.

Reglas:
- Todo se crea por datos (bmesh / bpy.data), sin depender de la ventana ni del contexto de la interfaz.
- Las medidas están en metros. Ejes de Blender: X/Y suelo, Z arriba.
- Las texturas son procedurales (ruido, ladrillo, voronoi) en coordenadas de mundo: no se descarga ninguna imagen
  y la escala es la misma en todos los objetos. Para el visor Android se exportan colores planos equivalentes.
"""
from __future__ import annotations
import math
import bmesh
import bpy
from mathutils import Vector, Euler

# ----------------------------------------------------------------------------------------------- escena

def escena_vacia(nombre: str = "Escena") -> bpy.types.Scene:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.name = nombre
    s.unit_settings.system = "METRIC"
    return s


def coleccion(nombre: str, padre: bpy.types.Collection | None = None) -> bpy.types.Collection:
    c = bpy.data.collections.get(nombre)
    if c is None:
        c = bpy.data.collections.new(nombre)
        (padre or bpy.context.scene.collection).children.link(c)
    return c


def _enlazar(obj, col):
    (col or bpy.context.scene.collection).objects.link(obj)
    return obj

# ------------------------------------------------------------------------------------------- materiales

_MATS: dict[str, bpy.types.Material] = {}


def _nodos(mat):
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return nt, bsdf, out


def _set(bsdf, nombre, valor):
    if nombre in bsdf.inputs:
        bsdf.inputs[nombre].default_value = valor


def material(nombre: str, color=(0.8, 0.8, 0.8), rugosidad=0.5, metal=0.0, *, emision=None, fuerza=0.0,
             ruido: float = 0.0, escala_ruido: float = 4.0, relieve: float = 0.0, alfa: float = 1.0,
             transmision: float = 0.0, ior: float = 1.45, rug_var: float = 0.0, ladrillo: tuple | None = None,
             animar_ruido: float = 0.0, ruido_en_emision: bool = False, mezcla: str = "DITHERED",
             ventanas: tuple | None = None) -> bpy.types.Material:
    """Material PBR con variación procedural opcional.

    ruido: cuánto varía el color (0–1). rug_var: variación de rugosidad (charcos en asfalto mojado).
    relieve: intensidad del bump. ladrillo: (color2, escala) para paredes de ladrillo/baldosa.
    animar_ruido: velocidad de animación del ruido (agua). ruido_en_emision: el ruido modula la emisión (pantallas).
    mezcla: "DITHERED" (barato, granulado con pocas muestras) o "BLENDED" (vidrio suave).
    ventanas: (color, escala) ventanas encendidas al azar sobre fachada oscura (edificios lejanos). Los parámetros quedan guardados en el material
    (propiedad "estudio") para que el exportador del visor pueda reconstruir un color plano.
    """
    if nombre in _MATS:
        return _MATS[nombre]
    mat = bpy.data.materials.new(nombre)
    nt, bsdf, out = _nodos(mat)
    col = (*color[:3], 1.0)
    _set(bsdf, "Base Color", col)
    _set(bsdf, "Roughness", rugosidad)
    _set(bsdf, "Metallic", metal)
    _set(bsdf, "IOR", ior)
    if transmision:
        _set(bsdf, "Transmission Weight", transmision)
    if emision is not None:
        _set(bsdf, "Emission Color", (*emision[:3], 1.0))
        _set(bsdf, "Emission Strength", fuerza)
    if alfa < 1.0:
        _set(bsdf, "Alpha", alfa)
        try:
            mat.surface_render_method = mezcla
        except Exception:
            pass
    mat.diffuse_color = col  # color de la vista sólida y del exportador
    mat.roughness = rugosidad
    mat.metallic = metal
    if ruido or relieve or rug_var or ladrillo:
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        mapeo = nt.nodes.new("ShaderNodeMapping")
        nt.links.new(geo.outputs["Position"], mapeo.inputs["Vector"])
        if animar_ruido:
            # el ruido 4D avanza con el tiempo (driver sobre W)
            tex = nt.nodes.new("ShaderNodeTexNoise")
            tex.noise_dimensions = "4D"
            d = tex.inputs["W"].driver_add("default_value").driver
            d.expression = f"frame*{animar_ruido / 30.0:.5f}"
        else:
            tex = nt.nodes.new("ShaderNodeTexNoise")
        tex.inputs["Scale"].default_value = escala_ruido
        tex.inputs["Detail"].default_value = 6.0
        nt.links.new(mapeo.outputs["Vector"], tex.inputs["Vector"])
        if ladrillo:
            br = nt.nodes.new("ShaderNodeTexBrick")
            br.inputs["Color1"].default_value = col
            br.inputs["Color2"].default_value = (*ladrillo[0][:3], 1.0)
            br.inputs["Mortar"].default_value = (*[c * 0.6 for c in color[:3]], 1.0)
            br.inputs["Scale"].default_value = ladrillo[1]
            br.inputs["Mortar Size"].default_value = 0.01
            nt.links.new(mapeo.outputs["Vector"], br.inputs["Vector"])
            nt.links.new(br.outputs["Color"], bsdf.inputs["Base Color"])
        elif ruido:
            ramp = nt.nodes.new("ShaderNodeValToRGB")
            ramp.color_ramp.elements[0].color = (*[c * (1 - ruido) for c in color[:3]], 1)
            ramp.color_ramp.elements[1].color = (*[min(1.0, c * (1 + ruido)) for c in color[:3]], 1)
            nt.links.new(tex.outputs["Fac"], ramp.inputs["Fac"])
            nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
        if ruido and ruido_en_emision and emision is not None:
            em = nt.nodes.new("ShaderNodeValToRGB")
            em.color_ramp.elements[0].color = (*[c * 0.15 for c in emision[:3]], 1)
            em.color_ramp.elements[1].color = (*emision[:3], 1)
            nt.links.new(tex.outputs["Fac"], em.inputs["Fac"])
            nt.links.new(em.outputs["Color"], bsdf.inputs["Emission Color"])
        if rug_var:
            rr = nt.nodes.new("ShaderNodeMapRange")
            rr.inputs["From Min"].default_value = 0.45
            rr.inputs["From Max"].default_value = 0.6
            rr.inputs["To Min"].default_value = max(0.02, rugosidad - rug_var)
            rr.inputs["To Max"].default_value = min(1.0, rugosidad + rug_var)
            nt.links.new(tex.outputs["Fac"], rr.inputs["Value"])
            nt.links.new(rr.outputs["Result"], bsdf.inputs["Roughness"])
        if relieve:
            bump = nt.nodes.new("ShaderNodeBump")
            bump.inputs["Strength"].default_value = relieve
            bump.inputs["Distance"].default_value = 0.05
            nt.links.new(tex.outputs["Fac"], bump.inputs["Height"])
            nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    if ventanas:
        geo2 = nt.nodes.new("ShaderNodeNewGeometry")
        br2 = nt.nodes.new("ShaderNodeTexBrick")
        br2.inputs["Scale"].default_value = ventanas[1]
        br2.inputs["Mortar Size"].default_value = 0.35
        br2.inputs["Color1"].default_value = (1, 1, 1, 1)
        br2.inputs["Color2"].default_value = (1, 1, 1, 1)
        br2.inputs["Mortar"].default_value = (0, 0, 0, 1)
        nt.links.new(geo2.outputs["Position"], br2.inputs["Vector"])
        azar = nt.nodes.new("ShaderNodeTexWhiteNoise")
        azar.noise_dimensions = "3D"
        snap = nt.nodes.new("ShaderNodeVectorMath")
        snap.operation = "SNAP"
        paso = 1.0 / ventanas[1]
        snap.inputs[1].default_value = (paso, paso, paso * 0.5)
        nt.links.new(geo2.outputs["Position"], snap.inputs[0])
        nt.links.new(snap.outputs["Vector"], azar.inputs["Vector"])
        umbral = nt.nodes.new("ShaderNodeMath")
        umbral.operation = "GREATER_THAN"
        umbral.inputs[1].default_value = 0.82
        nt.links.new(azar.outputs["Value"], umbral.inputs[0])
        mul = nt.nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        nt.links.new(br2.outputs["Fac"], mul.inputs[0])
        nt.links.new(umbral.outputs["Value"], mul.inputs[1])
        mul2 = nt.nodes.new("ShaderNodeMath")
        mul2.operation = "MULTIPLY"
        mul2.inputs[1].default_value = fuerza or 2.0
        nt.links.new(mul.outputs["Value"], mul2.inputs[0])
        _set(bsdf, "Emission Color", (*ventanas[0][:3], 1.0))
        nt.links.new(mul2.outputs["Value"], bsdf.inputs["Emission Strength"])
    mat["estudio"] = {"color": list(color[:3]), "rugosidad": rugosidad, "metal": metal,
                      "emision": list(emision[:3]) if emision else None, "fuerza": fuerza, "alfa": alfa}
    _MATS[nombre] = mat
    return mat


def vidrio(nombre="vidrio", tinte=(0.55, 0.65, 0.7), alfa=0.22) -> bpy.types.Material:
    return material(nombre, tinte, rugosidad=0.03, metal=0.0, alfa=alfa, ior=1.5, mezcla="BLENDED")


def emisivo(nombre: str, color, fuerza=5.0) -> bpy.types.Material:
    return material(nombre, color, rugosidad=0.5, emision=color, fuerza=fuerza)


def reiniciar_materiales():
    _MATS.clear()

# ------------------------------------------------------------------------------------------- geometría

def _obj_desde_bmesh(nombre, bm, mat, col, ubicacion=(0, 0, 0)):
    me = bpy.data.meshes.new(nombre)
    bm.to_mesh(me)
    bm.free()
    if mat is not None:
        me.materials.append(mat)
    ob = bpy.data.objects.new(nombre, me)
    ob.location = ubicacion
    return _enlazar(ob, col)


def caja(nombre: str, centro, tam, mat=None, col=None, bisel: float = 0.0, rot_z: float = 0.0):
    """Caja de tamaño `tam` (x, y, z) centrada en `centro`. bisel en metros (0 = sin bisel)."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= tam[0]
        v.co.y *= tam[1]
        v.co.z *= tam[2]
    ob = _obj_desde_bmesh(nombre, bm, mat, col, centro)
    ob.rotation_euler.z = rot_z
    if bisel > 0:
        m = ob.modifiers.new("bisel", "BEVEL")
        m.width = bisel
        m.segments = 2
        m.limit_method = "ANGLE"
    return ob


def cilindro(nombre, centro, radio, alto, mat=None, col=None, lados=24, eje="Z"):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=lados, radius1=radio, radius2=radio, depth=alto)
    ob = _obj_desde_bmesh(nombre, bm, mat, col, centro)
    if eje == "X":
        ob.rotation_euler.y = math.pi / 2
    elif eje == "Y":
        ob.rotation_euler.x = math.pi / 2
    for p in ob.data.polygons:
        p.use_smooth = True
    return ob


def esfera(nombre, centro, radio, mat=None, col=None, subdiv=2, escala=(1, 1, 1)):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=radio)
    for v in bm.verts:
        v.co.x *= escala[0]
        v.co.y *= escala[1]
        v.co.z *= escala[2]
    ob = _obj_desde_bmesh(nombre, bm, mat, col, centro)
    for p in ob.data.polygons:
        p.use_smooth = True
    return ob


def plano(nombre, centro, tam, mat=None, col=None, rot=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)
    for v in bm.verts:
        v.co.x *= tam[0]
        v.co.y *= tam[1]
    ob = _obj_desde_bmesh(nombre, bm, mat, col, centro)
    ob.rotation_euler = rot
    return ob


def unir(objs, nombre):
    """Une objetos en uno solo (menos llamadas de dibujo). Mantiene materiales."""
    objs = [o for o in objs if o is not None]
    if not objs:
        return None
    ctx = {"active_object": objs[0], "selected_editable_objects": objs, "selected_objects": objs}
    with bpy.context.temp_override(**ctx):
        bpy.ops.object.join()
    objs[0].name = nombre
    return objs[0]


def padre(hijo, papa):
    mw = hijo.matrix_world.copy()
    hijo.parent = papa
    hijo.matrix_parent_inverse = papa.matrix_world.inverted()
    hijo.matrix_world = mw
    return hijo


def vacio(nombre, ubicacion=(0, 0, 0), col=None, tipo="PLAIN_AXES"):
    e = bpy.data.objects.new(nombre, None)
    e.empty_display_type = tipo
    e.location = ubicacion
    return _enlazar(e, col)


def instancia(nombre, coleccion_fuente: bpy.types.Collection, ubicacion, rot_z=0.0, escala=1.0, col=None):
    """Instancia de una colección (no copia la malla: cuesta casi nada en memoria)."""
    e = bpy.data.objects.new(nombre, None)
    e.instance_type = "COLLECTION"
    e.instance_collection = coleccion_fuente
    e.location = ubicacion
    e.rotation_euler.z = rot_z
    e.scale = (escala, escala, escala)
    return _enlazar(e, col)


def prototipo(nombre: str) -> bpy.types.Collection:
    """Colección fuera de la escena para guardar prototipos instanciables (árbol, arbusto, farola…)."""
    c = bpy.data.collections.get(nombre)
    if c is None:
        c = bpy.data.collections.new(nombre)
    return c

# ----------------------------------------------------------------------------------------------- luces

def luz(nombre, tipo, ubicacion, energia, color=(1, 1, 1), col=None, rot=(0, 0, 0), tam=0.25,
        angulo_spot=None, sombra=True, radio=None):
    ld = bpy.data.lights.new(nombre, tipo)
    ld.energy = energia
    ld.color = color[:3]
    try:
        ld.use_shadow = sombra
    except Exception:
        pass
    if tipo == "AREA":
        ld.size = tam
    if tipo in ("POINT", "SPOT") and radio is not None:
        ld.shadow_soft_size = radio
    if tipo == "SPOT":
        ld.spot_size = angulo_spot or math.radians(60)
        ld.spot_blend = 0.6
    if tipo == "SUN":
        ld.angle = math.radians(1.5)
    ob = bpy.data.objects.new(nombre, ld)
    ob.location = ubicacion
    ob.rotation_euler = rot
    return _enlazar(ob, col)


def mirar_a(ob, objetivo):
    d = Vector(objetivo) - ob.location
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()

# ----------------------------------------------------------------------------------------------- mundo

def cielo_noche(escena, cenit=(0.0008, 0.0012, 0.004), horizonte=(0.009, 0.008, 0.014), estrellas=True,
                fuerza=1.0, niebla: float = 0.0):
    """Cielo nocturno procedural: degradé (resplandor urbano en el horizonte) + estrellas + niebla opcional."""
    w = bpy.data.worlds.new("cielo_noche")
    escena.world = w
    w.use_nodes = True
    nt = w.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = fuerza
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.45
    ramp.color_ramp.elements[0].color = (*horizonte, 1)
    ramp.color_ramp.elements[1].position = 0.75
    ramp.color_ramp.elements[1].color = (*cenit, 1)
    nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
    color_out = ramp.outputs["Color"]
    if estrellas:
        vor = nt.nodes.new("ShaderNodeTexVoronoi")
        vor.feature = "DISTANCE_TO_EDGE" if False else "F1"
        vor.inputs["Scale"].default_value = 420.0
        nt.links.new(tc.outputs["Generated"], vor.inputs["Vector"])
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs["From Min"].default_value = 0.0
        mr.inputs["From Max"].default_value = 0.06
        mr.inputs["To Min"].default_value = 1.2
        mr.inputs["To Max"].default_value = 0.0
        mr.clamp = True
        nt.links.new(vor.outputs["Distance"], mr.inputs["Value"])
        # sólo arriba del horizonte
        alto = nt.nodes.new("ShaderNodeMapRange")
        alto.inputs["From Min"].default_value = 0.52
        alto.inputs["From Max"].default_value = 0.65
        nt.links.new(sep.outputs["Z"], alto.inputs["Value"])
        mul = nt.nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        nt.links.new(mr.outputs["Result"], mul.inputs[0])
        nt.links.new(alto.outputs["Result"], mul.inputs[1])
        add = nt.nodes.new("ShaderNodeMix")
        add.data_type = "RGBA"
        add.blend_type = "ADD"
        add.inputs["Factor"].default_value = 1.0
        nt.links.new(color_out, add.inputs["A"])
        nt.links.new(mul.outputs["Value"], add.inputs["B"])
        color_out = add.outputs["Result"]
    nt.links.new(color_out, bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    if niebla > 0:
        vol = nt.nodes.new("ShaderNodeVolumePrincipled")
        vol.inputs["Density"].default_value = niebla
        vol.inputs["Color"].default_value = (0.6, 0.65, 0.8, 1)
        nt.links.new(vol.outputs["Volume"], out.inputs["Volume"])
    return w

def cielo_dia(escena, cenit=(0.10, 0.28, 0.80), horizonte=(0.50, 0.68, 0.95), fuerza=1.0):
    """Cielo diurno procedural: degradé horizonte→cenit (barato; el sol es una luz SUN aparte)."""
    w = bpy.data.worlds.new("cielo_dia")
    escena.world = w
    w.use_nodes = True
    nt = w.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = fuerza
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.5
    ramp.color_ramp.elements[0].color = (*horizonte, 1)
    ramp.color_ramp.elements[1].position = 0.85
    ramp.color_ramp.elements[1].color = (*cenit, 1)
    nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    return w


def apagar_emisores(materiales, factor=0.0):
    """Baja la emisión de materiales ya creados (modo día)."""
    for m in materiales:
        for n in m.node_tree.nodes:
            if n.type == "BSDF_PRINCIPLED" and "Emission Strength" in n.inputs and not n.inputs["Emission Strength"].is_linked:
                n.inputs["Emission Strength"].default_value *= factor

# ----------------------------------------------------------------------------------------------- animación

def clave(ob, ruta, frame, valor=None, indice=-1):
    if valor is not None:
        if indice >= 0:
            getattr(ob, ruta)[indice] = valor
        else:
            setattr(ob, ruta, valor)
    ob.keyframe_insert(data_path=ruta, frame=frame, index=indice)


def interpolacion_suave(ob, modo="BEZIER"):
    ad = ob.animation_data
    if not ad or not ad.action:
        return
    for fc in _fcurves(ad.action):
        for k in fc.keyframe_points:
            k.interpolation = modo


def _fcurves(action):
    """F-curves de una acción (compatibles con las acciones por capas de Blender 4.4+/5.x)."""
    fcs = list(getattr(action, "fcurves", []) or [])
    if fcs:
        return fcs
    out = []
    for layer in getattr(action, "layers", []):
        for strip in layer.strips:
            for bag in getattr(strip, "channelbags", []):
                out.extend(bag.fcurves)
    return out


def suavizar(t: float) -> float:
    """Curva ease-in-out (0..1)."""
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)
