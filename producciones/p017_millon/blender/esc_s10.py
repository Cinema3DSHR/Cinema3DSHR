"""s10 «Los tres en paralelo» (1662–2000): placa de fondo (degradé con partículas de luz) sobre la que el montaje (ffmpeg) apila los tres finales y pone la frase y la pregunta."""
import math
from mathutils import Vector
import lib
from lib import *
import guion


def construir(ctx, i, f0, f1):
    col = coleccion("S10_Placa")
    O = Vector(ctx.desp(i))
    fondo = mat_emisivo("placa_fondo", (0.04, 0.06, 0.16), 1.0)
    caja("placa", O + Vector((0, 3.0, 0)), (20, 0.1, 30), col, fondo)
    cam = Camara("cam_s10", col, 30.0)
    cam.claves(f0, f1 - 1, lambda f: O + Vector((0, -6.0, 0)), lambda f: O + Vector((0, 3.0, 0)), paso=20)
    ctx.dir.corte(f0, cam)
    ctx.amb.append((f0 - 1, (0.02, 0.03, 0.08), 0.4))
    ctx.escena_activa(col, f0, f1)
