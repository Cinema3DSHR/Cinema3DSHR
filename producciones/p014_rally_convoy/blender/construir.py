"""p014 «Rally Convoy» · etapa de Blender: importa el GLB que sale de Godot (mundo, siete autos originales completos con su textura, ruedas,
cabinas, pilotos con huesos, peaje y cámara) y hace la terminación artística: cielo y sol, materiales (asfalto, pasto, agua, vidrio, pintura
de los autos), árboles menos facetados, bruma de montaña, humo de gomas en las derrapadas y frenadas, desenfoque de movimiento y Cycles.
Uso: /opt/tools/blendenv/bin/python construir.py -- <rally_convoy_godot.glb> <rally_convoy_godot.json> <salida.blend>
Todo está en código: si cambia el GLB de Godot se vuelve a correr y queda igual."""
import sys
import json
import math
import re
import bpy
import bmesh
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cabinas
import camara_cfg
from mathutils import Vector

GLB, DATOS, SALIDA = sys.argv[sys.argv.index("--") + 1:][:3]
FPS = 30
RES = (480, 854)
SEMILLA = 1414
D = json.load(open(DATOS))


def principled(m):
    return next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)


def nuevo_material(nombre):
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    return m, nt


# ───────────────────────────────────────────── materiales
def vidrio(m, color):
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    vid = nt.nodes.new("ShaderNodeBsdfGlass")
    vid.inputs["Color"].default_value = color
    vid.inputs["Roughness"].default_value = 0.03
    vid.inputs["IOR"].default_value = 1.45
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    lp = nt.nodes.new("ShaderNodeLightPath")
    mez = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Shadow Ray"], mez.inputs["Fac"])
    nt.links.new(vid.outputs[0], mez.inputs[1])
    nt.links.new(tr.outputs[0], mez.inputs[2])
    nt.links.new(mez.outputs[0], out.inputs["Surface"])


def materiales():
    cuenta = {}
    imgs_auto = {f"{a['id']}_0" for a in D["autos"]}
    for m in bpy.data.materials:
        if not m.use_nodes:
            continue
        b = principled(m)
        n = m.name
        if n == "vidrio_auto":
            vidrio(m, (0.06, 0.08, 0.1, 1.0))
            cuenta["vidrio"] = cuenta.get("vidrio", 0) + 1
            continue
        if b is None:
            continue
        # carrocerías: material con la textura original del auto
        if any(nd.type == "TEX_IMAGE" and nd.image and nd.image.name.split(".")[0] in imgs_auto for nd in m.node_tree.nodes):
            b.inputs["Coat Weight"].default_value = 0.8
            b.inputs["Coat Roughness"].default_value = 0.06
            b.inputs["Roughness"].default_value = 0.32
            b.inputs["Metallic"].default_value = 0.25
            cuenta["carroceria"] = cuenta.get("carroceria", 0) + 1
        elif n == "mundo_asphalt":
            b.inputs["Roughness"].default_value = 0.78
            b.inputs["Specular IOR Level"].default_value = 0.35
            cuenta["asfalto"] = 1
        elif n == "mundo_terrain":
            b.inputs["Roughness"].default_value = 0.95
            cuenta["terreno"] = 1
        elif n == "mundo_water":
            b.inputs["Base Color"].default_value = (0.05, 0.16, 0.2, 1.0)
            b.inputs["Roughness"].default_value = 0.03
            b.inputs["Transmission Weight"].default_value = 0.85
            b.inputs["IOR"].default_value = 1.33
            cuenta["agua"] = 1
        elif n == "mundo_rail":
            b.inputs["Metallic"].default_value = 0.85
            b.inputs["Roughness"].default_value = 0.35
        elif n in ("mundo_vc", "mundo_atlas", "mundo_conc"):
            b.inputs["Roughness"].default_value = 0.85
        elif n == "mundo_tree":
            b.inputs["Roughness"].default_value = 0.8
            b.inputs["Subsurface Weight"].default_value = 0.12
        elif n in ("goma", "flanco") or re.match(r"^(goma|flanco)\d*$", n):
            b.inputs["Roughness"].default_value = 0.8
        elif n.startswith(("llanta", "acero_rueda")):
            b.inputs["Metallic"].default_value = 0.9
            b.inputs["Roughness"].default_value = 0.25
    return cuenta


# ───────────────────────────────────────────── árboles: las mallas compartidas se redondean (menos facetados)
def arboles():
    """Las mallas de árbol (pocas, compartidas por miles de instancias) se redondean: subdivisión + ruido. Se hace una sola vez por malla."""
    mallas = {}
    for o in bpy.data.objects:
        if o.type == "MESH" and o.data.users >= 12 and len(o.data.polygons) < 4000 and any(m and m.name == "mundo_tree" for m in o.data.materials):
            mallas.setdefault(o.data.name, o.data)
    tex = bpy.data.textures.new("Follaje_ruido", "CLOUDS")
    tex.noise_scale = 0.9
    n = 0
    for nombre, me in mallas.items():
        copia = me.copy()
        tmp = bpy.data.objects.new("tmp_arbol", copia)
        bpy.context.scene.collection.objects.link(tmp)
        sub = tmp.modifiers.new("Redondear", "SUBSURF")
        sub.levels = 1
        sub.render_levels = 1
        dis = tmp.modifiers.new("Ruido", "DISPLACE")
        dis.texture = tex
        dis.strength = 0.22
        dis.mid_level = 0.45
        with bpy.context.temp_override(object=tmp, active_object=tmp, selected_objects=[tmp]):
            bpy.ops.object.modifier_apply(modifier=sub.name)
            bpy.ops.object.modifier_apply(modifier=dis.name)
        for p in copia.polygons:
            p.use_smooth = True
        me.user_remap(copia)          # todas las instancias pasan a la malla redondeada
        bpy.data.objects.remove(tmp)
        n += 1
    return n


# ───────────────────────────────────────────── cielo, sol y bruma
def cielo(s):
    w = bpy.data.worlds.new("Mundo_p014")
    s.world = w
    w.use_nodes = True
    nt = w.node_tree
    for nd in list(nt.nodes):
        nt.nodes.remove(nd)
    out = nt.nodes.new("ShaderNodeOutputWorld")
    fondo = nt.nodes.new("ShaderNodeBackground")
    sky = nt.nodes.new("ShaderNodeTexSky")
    sky.sky_type = "MULTIPLE_SCATTERING"
    sky.sun_disc = False
    sky.sun_elevation = math.radians(38.0)
    sky.sun_rotation = math.radians(200.0)
    sky.aerosol_density = 1.0
    nt.links.new(sky.outputs["Color"], fondo.inputs["Color"])
    fondo.inputs["Strength"].default_value = 0.55
    nt.links.new(fondo.outputs[0], out.inputs["Surface"])
    sol = next((o for o in bpy.data.objects if o.type == "LIGHT" and o.data.type == "SUN"), None)
    if sol is None:
        d = bpy.data.lights.new("Sol", "SUN")
        sol = bpy.data.objects.new("Sol", d)
        s.collection.objects.link(sol)
        sol.rotation_euler = (math.radians(52), 0, math.radians(25))
    sol.parent = None
    sol.data.energy = 3.4
    sol.data.angle = math.radians(1.0)
    sol.data.color = (1.0, 0.95, 0.86)
    return sol.name


def bruma(s, col):
    # volumen acotado alrededor de la ruta (un volumen de mundo infinito tapa el cielo): caja grande y baja, que cubre toda la ruta y la montaña
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 100))
    c = bpy.context.active_object
    c.name = "Bruma_atmosfera"
    c.scale = (12000, 12000, 240)
    for k in list(c.users_collection):
        k.objects.unlink(c)
    col.objects.link(c)
    c.display_type = "WIRE"
    m, nt = nuevo_material("Bruma_atmosfera")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    pv = nt.nodes.new("ShaderNodeVolumeScatter")
    pv.inputs["Density"].default_value = 0.00035
    pv.inputs["Color"].default_value = (0.85, 0.9, 1.0, 1.0)
    pv.inputs["Anisotropy"].default_value = 0.45
    nt.links.new(pv.outputs[0], out.inputs["Volume"])
    c.data.materials.append(m)
    return c.name


# ───────────────────────────────────────────── humo de las gomas (derrapes y frenadas)
def humo(s, col):
    m, nt = nuevo_material("Humo_gomas")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    pv = nt.nodes.new("ShaderNodeVolumePrincipled")
    pv.inputs["Color"].default_value = (0.82, 0.82, 0.84, 1.0)
    pv.inputs["Anisotropy"].default_value = 0.2
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    ruido = nt.nodes.new("ShaderNodeTexNoise")
    ruido.noise_dimensions = "4D"
    ruido.inputs["Scale"].default_value = 2.2
    ruido.inputs["Detail"].default_value = 3.0
    nt.links.new(tc.outputs["Object"], ruido.inputs["Vector"])
    dr = ruido.inputs["W"].driver_add("default_value")
    dr.driver.type = "SCRIPTED"
    dr.driver.expression = "frame / 30.0 * 0.5"
    # se desvanece hacia los bordes del volumen (sin cajas visibles)
    r = nt.nodes.new("ShaderNodeMath")
    r.operation = "MULTIPLY"
    r.inputs[1].default_value = 0.9
    nt.links.new(ruido.outputs["Fac"], r.inputs[0])
    dens = nt.nodes.new("ShaderNodeMath")
    dens.operation = "MULTIPLY"
    dens.inputs[1].default_value = 0.0
    nt.links.new(r.outputs[0], dens.inputs[0])
    nt.links.new(dens.outputs[0], pv.inputs["Density"])
    nt.links.new(pv.outputs[0], out.inputs["Volume"])
    creados = 0
    for a in D["autos"]:
        k = a["indice"]
        padre = bpy.data.objects.get(a["nodo"])
        if padre is None:
            continue
        T = D["telemetria"][k]
        slip, fren, vel = T["slip"], T["frenada"], T["v"]
        # intensidad por cuadro: derrape (ángulo de deslizamiento) y frenada fuerte a velocidad
        inten = [min(1.0, max(0.0, (abs(sl) - 5.0) / 14.0) + (0.6 * max(0.0, fr - 0.45) * min(1.0, v / 25.0))) for sl, fr, v in zip(slip, fren, vel)]
        if max(inten) < 0.05:
            continue
        for lado in (-1.0, 1.0):
            bpy.ops.mesh.primitive_cube_add(size=1)
            h = bpy.context.active_object
            h.name = f"Humo_{k}_{'izq' if lado < 0 else 'der'}"
            for kk in list(h.users_collection):
                kk.objects.unlink(h)
            col.objects.link(h)
            h.parent = padre
            h.location = (lado * 0.8, 1.6, 0.35)         # detrás de la rueda trasera (eje local del auto importado: +Y = atrás, +Z = arriba)
            h.scale = (2.4, 3.2, 1.2)
            h.display_type = "WIRE"
            mm = m.copy()
            h.data.materials.append(mm)
            mdens = next(n for n in mm.node_tree.nodes if n.type == "MATH" and n.operation == "MULTIPLY" and n.inputs[1].default_value == 0.0)
            for f, v in enumerate(inten):
                if f % 2 == 0 or v > 0.05:
                    mdens.inputs[1].default_value = v * 2.4
                    mdens.inputs[1].keyframe_insert("default_value", frame=f)
                    h.hide_render = v < 0.03
                    h.keyframe_insert("hide_render", frame=f)
            creados += 1
    return creados


# ───────────────────────────────────────────── tiempo y Cycles
def tiempo(s):
    s.render.fps = FPS
    s.render.fps_base = 1.0
    s.frame_start = 0
    s.frame_end = int(D["cuadros"]) - 1


def cycles(s):
    s.render.engine = "CYCLES"
    s.render.resolution_x, s.render.resolution_y = RES
    s.render.resolution_percentage = 100
    s.render.pixel_aspect_x = s.render.pixel_aspect_y = 1.0
    s.render.image_settings.file_format = "PNG"
    s.render.use_motion_blur = True            # sensación de velocidad
    s.render.motion_blur_shutter = 0.4
    s.render.motion_blur_position = "START"    # sólo hacia adelante: sin barridos en los cortes de cámara
    s.render.use_persistent_data = True
    s.view_settings.view_transform = "AgX"
    s.view_settings.look = "AgX - Medium High Contrast"
    s.view_settings.exposure = -0.4
    c = s.cycles
    c.device = "CPU"
    c.samples = 6
    c.use_adaptive_sampling = True
    c.adaptive_threshold = 0.05
    c.use_denoising = True
    c.denoiser = "OPENIMAGEDENOISE"
    c.denoising_input_passes = "RGB_ALBEDO_NORMAL"
    c.max_bounces = 6
    c.diffuse_bounces = 3
    c.glossy_bounces = 3
    c.transmission_bounces = 6
    c.transparent_max_bounces = 12
    c.volume_bounces = 1
    c.use_light_tree = True
    c.use_animated_seed = False
    c.seed = SEMILLA
    c.caustics_reflective = False
    c.caustics_refractive = False
    c.sample_clamp_indirect = 8.0
    c.volume_step_rate = 2.0
    c.volume_max_steps = 48


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.render.fps = FPS          # el GLB trae la animación en segundos: así quedan a 30 cuadros por segundo
    bpy.ops.import_scene.gltf(filepath=GLB)
    info = {}
    tiempo(s)
    col = bpy.data.collections.new("Efectos_p014")
    s.collection.children.link(col)
    info["camara_curvas"] = camara_cfg.camara(s, D)
    info["materiales"] = materiales()
    info["arboles"] = arboles()
    info["sol"] = cielo(s)
    info["bruma"] = bruma(s, col)
    info["humo"] = humo(s, col)
    info["cabinas"] = cabinas.cabinas(D, s)
    cycles(s)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=SALIDA, compress=True)
    print("INFORME", info)


main()
