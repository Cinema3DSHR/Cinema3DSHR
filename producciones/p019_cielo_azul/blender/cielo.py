"""p019 · mundo con cielo físico (Nishita/dispersión de Rayleigh de Blender) mezclado con un cielo de estrellas; los parámetros se animan por escena."""
import math
import bpy
import lib


def mundo(s):
    w = bpy.data.worlds.new("Cielo")
    s.world = w
    w.use_nodes = True
    nt = w.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputWorld")
    sky = nt.nodes.new("ShaderNodeTexSky")
    ok = False
    for tipo in ("MULTIPLE_SCATTERING", "SINGLE_SCATTERING", "NISHITA"):
        try:
            sky.sky_type = tipo
            ok = True
            break
        except Exception:
            continue
    bg1 = nt.nodes.new("ShaderNodeBackground")
    bg1.inputs["Strength"].default_value = 0.5
    # estrellas procedurales (Voronoi en el mundo)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    vo = nt.nodes.new("ShaderNodeTexVoronoi")
    vo.inputs["Scale"].default_value = 110.0
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.0
    mr.inputs["From Max"].default_value = 0.07
    mr.inputs["To Min"].default_value = 1.0
    mr.inputs["To Max"].default_value = 0.0
    pw = nt.nodes.new("ShaderNodeMath")
    pw.operation = "POWER"
    pw.inputs[1].default_value = 3.0
    mu = nt.nodes.new("ShaderNodeMath")
    mu.operation = "MULTIPLY"
    mu.inputs[1].default_value = 25.0
    bg2 = nt.nodes.new("ShaderNodeBackground")
    bg2.inputs["Color"].default_value = (0.004, 0.005, 0.01, 1)
    ad = nt.nodes.new("ShaderNodeMix")
    ad.data_type = "RGBA"
    ad.blend_type = "ADD"
    ad.inputs[0].default_value = 1.0
    ad.inputs[6].default_value = (0.003, 0.004, 0.01, 1)
    mz = nt.nodes.new("ShaderNodeMixShader")
    L = nt.links.new
    L(sky.outputs[0], bg1.inputs["Color"])
    L(tc.outputs["Generated"], vo.inputs["Vector"])
    L(vo.outputs["Distance"], mr.inputs["Value"])
    L(mr.outputs["Result"], pw.inputs[0])
    L(pw.outputs[0], mu.inputs[0])
    L(mu.outputs[0], ad.inputs[7])
    L(ad.outputs[2], bg2.inputs["Color"])
    L(bg1.outputs[0], mz.inputs[1])
    L(bg2.outputs[0], mz.inputs[2])
    L(mz.outputs[0], out.inputs["Surface"])
    return {"sky": sky, "mix": mz.inputs["Fac"], "nt": nt, "bg1": bg1}


def poner(c, f, estrellas=False, elev=40.0, rot=0.0, aire=1.0):
    """Clave de cielo en el cuadro f: estrellas=True usa el cielo negro con estrellas (escenas de diagrama y espacio)."""
    sky = c["sky"]
    sky.sun_elevation = math.radians(elev)
    sky.sun_rotation = math.radians(rot)
    sky.air_density = aire
    c["mix"].default_value = 1.0 if estrellas else 0.0
    sky.keyframe_insert("sun_elevation", frame=int(f))
    sky.keyframe_insert("sun_rotation", frame=int(f))
    sky.keyframe_insert("air_density", frame=int(f))
    c["mix"].keyframe_insert("default_value", frame=int(f))


def fin(c):
    nt = c["nt"]
    if nt.animation_data and nt.animation_data.action:
        from bpy_extras import anim_utils
        ad = nt.animation_data
        cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
        for fc in (cb.fcurves if cb else []):
            const = "default_value" in fc.data_path          # el selector cielo/estrellas cambia de golpe al empezar cada escena
            for kp in fc.keyframe_points:
                kp.interpolation = "CONSTANT" if const else "BEZIER"
