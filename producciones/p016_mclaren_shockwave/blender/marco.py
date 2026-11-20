"""p015 «FRACTURA» · marco: Cycles, mundo, compositor, cámaras con cortes, velos de transición y Aiden por NLA (tiempo animado)."""
import math
import bpy
from mathutils import Vector
import lib
from lib import *
import guion

RES = (720, 1280)


def cycles(s, res=RES, muestras=6):
    s.render.engine = "CYCLES"
    s.render.resolution_x, s.render.resolution_y = res
    s.render.resolution_percentage = 100
    s.render.fps = FPS
    s.render.fps_base = 1.0
    s.frame_start, s.frame_end = 0, guion.TOTAL - 1
    s.render.image_settings.file_format = "PNG"
    s.render.use_motion_blur = True
    s.render.motion_blur_shutter = 0.35
    s.render.motion_blur_position = "START"
    s.render.use_persistent_data = True
    s.render.compositor_device = "CPU"
    s.render.use_compositing = True
    s.view_settings.view_transform = "AgX"
    s.view_settings.look = "AgX - Medium High Contrast"
    s.view_settings.exposure = 0.0
    c = s.cycles
    c.device = "CPU"
    c.samples = muestras
    c.use_adaptive_sampling = True
    c.adaptive_threshold = 0.05
    c.use_denoising = True
    c.denoiser = "OPENIMAGEDENOISE"
    c.denoising_input_passes = "RGB_ALBEDO_NORMAL"
    c.max_bounces = 6
    c.diffuse_bounces = 3
    c.glossy_bounces = 4
    c.transmission_bounces = 6
    c.transparent_max_bounces = 12
    c.volume_bounces = 1
    c.use_light_tree = True
    c.use_animated_seed = False
    c.seed = 2026
    c.caustics_reflective = False
    c.caustics_refractive = False
    c.sample_clamp_indirect = 8.0
    c.volume_step_rate = 1.0
    c.volume_max_steps = 20


def mundo(s):
    w = bpy.data.worlds.new("Vacio")
    s.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes["Background"]
    bg.inputs["Color"].default_value = (0.004, 0.005, 0.008, 1)
    bg.inputs["Strength"].default_value = 1.0
    return bg


def ambiente(bg, claves):
    """claves = [(cuadro, (r,g,b), fuerza)] → color y fuerza del fondo por escena."""
    for f, c, k in claves:
        bg.inputs["Color"].default_value = (*c, 1)
        bg.inputs["Strength"].default_value = k
        bg.inputs["Color"].keyframe_insert("default_value", frame=f)
        bg.inputs["Strength"].keyframe_insert("default_value", frame=f)
    nt = bg.id_data
    ad = nt.animation_data
    if ad and ad.action:
        lib._interp_id(nt, "CONSTANT")       # el color del fondo cambia de golpe al empezar cada escena


def compositor(s):
    nt = bpy.data.node_groups.new("fractura_comp", "CompositorNodeTree")
    s.compositing_node_group = nt
    nt.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    rl = nt.nodes.new("CompositorNodeRLayers")
    gl = nt.nodes.new("CompositorNodeGlare")
    gl.inputs["Type"].default_value = "Fog Glow"
    gl.inputs["Quality"].default_value = "Medium"
    gl.inputs["Threshold"].default_value = 1.2
    gl.inputs["Strength"].default_value = 0.55
    gl.inputs["Size"].default_value = 0.6
    ld = nt.nodes.new("CompositorNodeLensdist")
    ld.inputs["Dispersion"].default_value = 0.012
    ld.inputs["Distortion"].default_value = 0.0
    cb = nt.nodes.new("CompositorNodeColorBalance")
    cb.inputs["Type"].default_value = "Lift/Gamma/Gain"
    for sk in cb.inputs:
        if sk.type == "RGBA" and sk.name == "Lift":
            sk.default_value = (0.98, 1.0, 1.04, 1.0)
        if sk.type == "RGBA" and sk.name == "Gain":
            sk.default_value = (1.06, 1.0, 0.94, 1.0)
    # viñeta
    el = nt.nodes.new("CompositorNodeEllipseMask")
    el.inputs["Size"].default_value = (0.92, 0.92)
    bl = nt.nodes.new("CompositorNodeBlur")
    bl.inputs["Size"].default_value = (120.0, 120.0)
    ao = nt.nodes.new("CompositorNodeAlphaOver")
    ao.inputs["Foreground"].default_value = (0, 0, 0, 0.55)
    out = nt.nodes.new("NodeGroupOutput")
    L = nt.links.new
    L(rl.outputs["Image"], gl.inputs["Image"])
    L(gl.outputs[0], ld.inputs["Image"])
    L(ld.outputs[0], cb.inputs["Image"])
    L(el.outputs["Mask"], bl.inputs["Image"])
    inv = nt.nodes.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    inv.use_clamp = True
    L(bl.outputs[0], inv.inputs[1])
    L(inv.outputs[0], ao.inputs["Factor"])
    L(cb.outputs[0], ao.inputs["Background"])
    out.is_active_output = True
    L(ao.outputs[0], out.inputs["Image"])
    return {"disp": ld.inputs["Dispersion"], "dist": ld.inputs["Distortion"], "glare": gl.inputs["Strength"], "nt": nt}


class Direccion:
    """Cortes de cámara por marcadores + velo (plano pegado a la lente) para destellos, fundidos y rellenos de transición."""

    def __init__(self, s, col):
        self.s = s
        self.col = col
        self.cuts = []
        self.velos = {}

    def corte(self, f0, cam, velo=True):
        m = self.s.timeline_markers.new(f"{cam.o.name}@{f0}", frame=int(f0))
        m.camera = cam.o
        self.cuts.append((f0, cam))
        if velo and cam.o.name not in self.velos:
            self.velos[cam.o.name] = Velo(cam, self.col)
        return self.velos.get(cam.o.name)


class Velo:
    def __init__(self, cam, col):
        m = bpy.data.materials.new("velo_" + cam.o.name)
        m.use_nodes = True
        nt = m.node_tree
        for n in list(nt.nodes):
            nt.nodes.remove(n)
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        em = nt.nodes.new("ShaderNodeEmission")
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        mz = nt.nodes.new("ShaderNodeMixShader")
        self.fac = mz.inputs["Fac"]
        self.col = em.inputs["Color"]
        self.fue = em.inputs["Strength"]
        nt.links.new(tr.outputs[0], mz.inputs[1])
        nt.links.new(em.outputs[0], mz.inputs[2])
        nt.links.new(mz.outputs[0], out.inputs["Surface"])
        self.fac.default_value = 0.0
        self.fue.default_value = 1.0
        o = plano("velo_" + cam.o.name, (0, 0, -0.35), 2.0, 3.6, col, m)
        o.parent = cam.o
        o.visible_shadow = False
        o.visible_glossy = False
        o.visible_diffuse = False
        o.visible_transmission = False
        o.visible_volume_scatter = False
        self.o = o
        self.mat = m

    def clave(self, f, fac, color=(1, 1, 1), fuerza=1.0):
        self.fac.default_value = fac
        self.col.default_value = (*color, 1)
        self.fue.default_value = fuerza
        for s_ in (self.fac, self.col, self.fue):
            s_.keyframe_insert("default_value", frame=int(f))

    def rampa(self, f0, f1, a, b, color=(1, 1, 1), fuerza=1.0):
        self.clave(f0, a, color, fuerza)
        self.clave(f1, b, color, fuerza)

    def fin(self):
        nt = self.mat.node_tree
        if nt.animation_data and nt.animation_data.action:
            lib._interp_id(nt, "LINEAR")


def pulso(sock, claves):
    """claves = [(cuadro, valor)] para un socket numérico del compositor."""
    for f, v in claves:
        sock.default_value = v
        sock.keyframe_insert("default_value", frame=int(f))
    nt = sock.id_data
    if nt.animation_data and nt.animation_data.action:
        lib._interp_id(nt, "LINEAR")
