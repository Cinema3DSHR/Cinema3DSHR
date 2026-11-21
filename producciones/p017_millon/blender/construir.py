"""p017 «¿Qué harías con un millón de dólares?» · construye el BLEND (o sólo las escenas pedidas, para validar).
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


REGISTRO = {"s0": "esc_s0", "s1": "esc_s1", "s2": "esc_finca", "s8": "esc_s8", "s9": "esc_s9"}


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    salida = args[0] if args else os.path.join(AQUI, "millon.blend")
    sel = args[1].split(",") if len(args) > 1 and args[1] != "todas" else None
    esc = float(args[2]) if len(args) > 2 else 1.0
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    marco.cycles(s, (int(guion.W * esc), int(guion.H * esc)))
    s.frame_end = guion.rango(9)[1] - 1          # el cierre (s10) se arma en el montaje con ffmpeg a partir de las tomas renderizadas
    s.view_settings.exposure = -0.2
    ctx = Ctx(s)
    ctx.bg = marco.mundo(s)
    ctx.comp = marco.compositor(s)
    ctx.dir = marco.Direccion(s, lib.coleccion("Direccion"))
    import personas as P
    ctx.aiden = P.cargar("aiden", lib.coleccion("PERSONAS"))
    ctx.kate = P.cargar("kate", lib.coleccion("PERSONAS"))
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
