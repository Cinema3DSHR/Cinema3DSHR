"""p015 «FRACTURA» · construye el BLEND completo (o sólo las escenas pedidas, para validar).
Uso: blender -b -P construir.py -- salida.blend [escenas coma] [escala_res]   o   python construir.py -- ...
Variables: FRACTURA_STILLS="cuadro,cuadro" renderiza esos cuadros (PNG) junto al .blend."""
import importlib
import os
import sys
import bpy

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import lib
import guion
import marco
import aiden as AID


class Ctx:
    def __init__(self, s):
        self.s = s
        self.escenas = {}
        self.aiden = None
        self.dir = None
        self.comp = None
        self.bg = None
        self.amb = []

    def desp(self, i):
        return guion.desplazamiento(i)

    def escena_activa(self, col, f0, f1):
        # cada escena vive a 1 km de las demás (la visibilidad por colección no se anima): nada que ocultar
        self.escenas[col.name] = (f0, f1)


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    salida = args[0] if args else os.path.join(AQUI, "fractura.blend")
    sel = args[1].split(",") if len(args) > 1 and args[1] != "todas" else None
    esc = float(args[2]) if len(args) > 2 else 1.0
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    marco.cycles(s, (int(720 * esc), int(1280 * esc)))
    ctx = Ctx(s)
    ctx.bg = marco.mundo(s)
    ctx.comp = marco.compositor(s)
    base = lib.coleccion("Direccion")
    ctx.dir = marco.Direccion(s, base)
    if os.path.exists(AID.BIB):
        ctx.aiden = AID.cargar(lib.coleccion("AIDEN"))
        ctx.hips = AID.vacio(lib.coleccion("AIDEN"), ctx.aiden, "mixamorig:Hips", "AIDEN_cadera")
        ctx.head = AID.vacio(lib.coleccion("AIDEN"), ctx.aiden, "mixamorig:Head", "AIDEN_cabeza", frac=0.5)
    from esc_registro import ESCENAS_CONSTRUCTORES
    for i, (sid, nombre, f0, f1) in enumerate(guion.ESCENAS):
        if sel and sid not in sel:
            continue
        mod = ESCENAS_CONSTRUCTORES.get(sid)
        if mod is None:
            continue
        print("ESCENA", sid, nombre, f0, f1, flush=True)
        mod(ctx, i, f0, f1)
    if ctx.aiden is not None:     # Aiden espera lejos, fuera de cuadro, hasta que su primera escena lo necesite
        raiz = bpy.data.objects["PJ_aiden"]
        raiz.rotation_mode = "XYZ"
        for f in (0, 90, 178):
            raiz.location = (0, 0, -600)
            raiz.keyframe_insert("location", frame=f)
        if len(sys.argv) and sel is not None:
            pass
    if ctx.amb:
        marco.ambiente(ctx.bg, sorted(ctx.amb, key=lambda a: a[0]))
    for v in ctx.dir.velos.values():
        v.fin()
    s.render.use_motion_blur = True
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
