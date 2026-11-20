"""p016 «McLaren F1: SHOCKWAVE» · construye el BLEND completo. Uso: python construir.py -- salida.blend [escala_res] [fases]
FRACTURA_STILLS="cuadro,cuadro" renderiza esos cuadros junto al .blend."""
import math
import os
import sys
import bpy
from mathutils import Vector, Euler

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import lib
from lib import *
import guion
import marco
import coche as C
import ciudad
import efectos
import camaras

T = Tiempo(guion.KNOTS_T)


def v_coche(t):
    if t <= 10.0:
        return 12.0 + 2.6 * t
    if t <= 17.667:
        return 38.0 + 3.52 * (t - 10.0)
    if t <= 22.6:
        return 65.0
    return 65.0 + (t - 22.6) * (10.0 / 2.2)


_cache_y = {}


def y_coche_t(t):
    """Posición Y del coche en el instante de simulación t (integral de la velocidad), memoizada cada 1/200 s."""
    k = int(t * 200)
    if k not in _cache_y:
        if not _cache_y:
            _cache_y[0] = guion.Y0
        j = max(x for x in _cache_y if x <= k)
        y = _cache_y[j]
        while j < k:
            y -= v_coche(j / 200.0) / 200.0
            j += 1
            _cache_y[j] = y
    return _cache_y[k]


def y_coche(f):
    return y_coche_t(T(f))


def encender_luces(coche):
    """Faros delanteros y pilotos traseros ENCENDIDOS: se agrega emisión a los materiales de luces del modelo (conserva sus texturas) y luces reales."""
    for nombre, color, fuerza in (("vehiclelights_11", (1.0, 0.95, 0.85), 14.0), ("vehiclelights_13", (1.0, 0.95, 0.85), 14.0),
                                  ("vehiclelights_41", (1.0, 0.04, 0.02), 9.0), ("vehiclelights_42", (1.0, 0.04, 0.02), 9.0),
                                  ("vehiclelights_43", (1.0, 0.04, 0.02), 9.0), ("vehiclelights_44", (1.0, 0.04, 0.02), 9.0),
                                  ("vehiclelights_45", (1.0, 0.04, 0.02), 9.0), ("vehiclelights_30", (1.0, 0.04, 0.02), 9.0)):
        m = bpy.data.materials.get(nombre)
        if not m:
            continue
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Emission Color"].default_value = (*color, 1)
        b.inputs["Emission Strength"].default_value = fuerza
    raiz = coche["raiz"]
    for sx in (-1, 1):
        sp = bpy.data.lights.new(f"faro_{sx}", "SPOT")
        sp.energy = 6000.0
        sp.spot_size = math.radians(70)
        sp.spot_blend = 0.6
        sp.color = (1.0, 0.93, 0.82)
        sp.shadow_soft_size = 0.12
        o = bpy.data.objects.new(f"faro_{sx}", sp)
        bpy.context.scene.collection.objects.link(o)
        o.parent = raiz
        o.location = (sx * 0.62, -2.15, -0.2)
        o.rotation_euler = Euler((math.radians(-84), 0, 0), "XYZ")      # el foco apunta a −Z local: −84° sobre X lo lleva a −Y, un poco hacia abajo
        pl = bpy.data.lights.new(f"piloto_{sx}", "POINT")
        pl.energy = 120.0
        pl.color = (1.0, 0.05, 0.02)
        pl.shadow_soft_size = 0.1
        po = bpy.data.objects.new(f"piloto_{sx}", pl)
        bpy.context.scene.collection.objects.link(po)
        po.parent = raiz
        po.location = (sx * 0.62, 2.4, 0.1)


def pintura_brillante():
    """El modelo trae la pintura mate (rugosidad 0,75 de la importación): se le da barniz y brillo sin tocar sus texturas."""
    for n in ("paint", "colour"):
        m = bpy.data.materials.get(n)
        if m:
            b = m.node_tree.nodes["Principled BSDF"]
            b.inputs["Roughness"].default_value = 0.22
            b.inputs["Coat Weight"].default_value = 0.8
            b.inputs["Coat Roughness"].default_value = 0.05
            b.inputs["Specular IOR Level"].default_value = 0.7
    for n in ("Color_0B1717", "Color_232323", "Color_242424"):
        m = bpy.data.materials.get(n)
        if m:
            b = m.node_tree.nodes["Principled BSDF"]
            b.inputs["Roughness"].default_value = 0.05
            b.inputs["Metallic"].default_value = 0.0
    for n in ("thread", "sidewall"):
        m = bpy.data.materials.get(n)
        if m:
            m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.8
    for n in ("wheels", "wheels_brake", "detail_chassis", "gold"):
        m = bpy.data.materials.get(n)
        if m:
            b = m.node_tree.nodes["Principled BSDF"]
            b.inputs["Metallic"].default_value = 0.8
            b.inputs["Roughness"].default_value = 0.3


def animar_coche(ctx, coche):
    raiz = coche["raiz"]
    raiz.rotation_mode = "XYZ"
    raiz.rotation_euler = (0, 0, 0)
    for f in range(0, guion.TOTAL):
        y = y_coche(f)
        # temblor leve de suspensión a velocidad (menor en cámara lenta)
        t = T(f)
        raiz.location = (guion.X_CARRIL, y, -C.Z_SUELO + 0.004 * math.sin(t * 37.0) + 0.002 * math.sin(t * 91.0))
        raiz.keyframe_insert("location", frame=f)
        th = (guion.Y0 - y) / C.RADIO
        for p in coche["pivotes"].values():
            p.rotation_euler = (th, 0, 0)
            p.keyframe_insert("rotation_euler", frame=f)
    lib._interp(raiz, "LINEAR")
    # el vacío que usan las cámaras como objetivo
    ctx.centro = bpy.data.objects.new("coche_centro", None)
    bpy.context.scene.collection.objects.link(ctx.centro)
    ctx.centro.parent = raiz
    ctx.centro.location = (0, 0, 0.1)


class Ctx:
    pass


def mundo_cielo(s):
    w = bpy.data.worlds.new("Atardecer")
    s.world = w
    w.use_nodes = True
    nt = w.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    sky = nt.nodes.new("ShaderNodeTexSky")
    try:
        sky.sky_type = "MULTIPLE_SCATTERING"
    except Exception:
        pass
    sky.sun_elevation = math.radians(2.0)
    sky.sun_rotation = math.radians(200)
    sky.sun_intensity = 0.15
    bg.inputs["Strength"].default_value = 0.7
    nt.links.new(sky.outputs[0], bg.inputs["Color"])
    nt.links.new(bg.outputs[0], out.inputs["Surface"])


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    salida = args[0] if args else os.path.join(AQUI, "mclaren.blend")
    esc = float(args[1]) if len(args) > 1 else 1.0
    fases = args[2] if len(args) > 2 else "todo"
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    marco.cycles(s, (int(720 * esc), int(1280 * esc)))
    s.view_settings.exposure = -0.4
    mundo_cielo(s)
    ctx = Ctx()
    ctx.comp = marco.compositor(s)
    ctx.dir = marco.Direccion(s, lib.coleccion("Direccion"))
    ctx.T = T
    ctx.y_coche = y_coche
    ctx.y_coche_t = y_coche_t
    ciudad.construir(ctx)
    col_c = lib.coleccion("McLaren_F1")
    coche = C.cargar(col_c)
    pintura_brillante()
    encender_luces(coche)
    animar_coche(ctx, coche)
    ctx.coche = coche
    if fases != "base":
        efectos.construir(ctx)
    camaras.construir(ctx)
    import json
    datos = {"fps": guion.FPS, "total": guion.TOTAL,
             "T": [float(T(f)) for f in range(guion.TOTAL)],
             "coche_y": [float(y_coche(f)) for f in range(guion.TOTAL)],
             "oyente": [getattr(ctx, "oyente", {}).get(f, [0, 0, 1.2]) for f in range(guion.TOTAL)],
             "roturas": getattr(ctx, "roturas_audio", []), "x_carril": guion.X_CARRIL}
    json.dump(datos, open(os.path.join(AQUI, "..", "audio_datos.json"), "w"))
    bpy.ops.wm.save_as_mainfile(filepath=salida)
    print("GUARDADO", salida, flush=True)
    st = os.environ.get("FRACTURA_STILLS")
    if st:
        for f in [int(x) for x in st.split(",")]:
            s.frame_set(f)
            s.render.filepath = salida.replace(".blend", f"_f{f:05d}.png")
            bpy.ops.render.render(write_still=True)
            print("STILL", s.render.filepath, flush=True)


main()
