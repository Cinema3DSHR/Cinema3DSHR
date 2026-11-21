"""p019 «¿Por qué el cielo es azul?» · construye el BLEND (o sólo las escenas pedidas, para validar).
Uso: python construir.py -- salida.blend [escenas coma|todas] [escala_res]   ·   STILLS="cuadro,cuadro" renderiza esos cuadros."""
import importlib
import os
import sys
import bpy

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import lib
import guion
import marco


class Ctx:
    def __init__(self, s):
        self.s = s
        self.dir = None
        self.comp = None
        self.bg = None
        self.amb = []
        self.escenas = {}

    def desp(self, i):
        return guion.desplazamiento(i)

    def escena_activa(self, col, f0, f1):
        self.escenas[col.name] = (f0, f1)


REGISTRO = {k: "esc" for k in ("s0","s1","s2","s3","s4","s5","s6","s7","s8")}


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    salida = args[0] if args else os.path.join(AQUI, "millon.blend")
    sel = args[1].split(",") if len(args) > 1 and args[1] != "todas" else None
    esc = float(args[2]) if len(args) > 2 else 1.0
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    marco.cycles(s, (int(guion.W * esc), int(guion.H * esc)))
    s.frame_end = guion.TOTAL - 1
    s.view_settings.view_transform = "Khronos PBR Neutral"
    s.view_settings.look = "None"
    s.view_settings.exposure = 0.0
    ctx = Ctx(s)
    ctx.bg = marco.mundo(s)
    ctx.comp = marco.compositor(s)
    ctx.dir = marco.Direccion(s, lib.coleccion("Direccion"))
    import cielo
    ctx.cielo = cielo.mundo(s)
    for i, (sid, nombre, a, b) in enumerate(guion.ESCENAS):
        if sel and sid not in sel:
            continue
        mod = REGISTRO.get(sid)
        if mod is None:
            continue
        f0, f1 = guion.rango(i)
        print("ESCENA", sid, nombre, f0, f1, flush=True)
        importlib.import_module(mod).construir(ctx, i, f0, f1)
    for v in ctx.dir.velos.values():
        v.fin()
    cielo.fin(ctx.cielo)
    if ctx.amb:
        marco.ambiente(ctx.bg, sorted(ctx.amb, key=lambda a: a[0]))
    bpy.ops.wm.save_as_mainfile(filepath=salida)
    print("GUARDADO", salida, flush=True)
    st = os.environ.get("STILLS")
    if st:
        for f in [int(x) for x in st.split(",")]:
            s.frame_set(f)
            s.render.filepath = salida.replace(".blend", f"_f{f:05d}.png")
            bpy.ops.render.render(write_still=True)
            print("STILL", s.render.filepath, flush=True)


main()
