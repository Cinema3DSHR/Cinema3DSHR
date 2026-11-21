"""s8 «Saldo cero» (1317–1440): de vuelta en el dormitorio, el saldo del celular rueda hasta 0 y la persona se queda helada."""
import math
from mathutils import Vector
import lib
from lib import *
import personas as P
import guion


def construir(ctx, i, f0, f1):
    s0 = ctx.s0
    O, ai, od, col = s0["O"], s0["ai"], s0["od"], s0["col"]
    pos = O + Vector((0.5, 2.1, 0.0))
    # Aiden regresa al dormitorio (mismo lugar, mirando hacia +Y como en s0)
    P.colocar(ai, [(f0 - 1, (0, 0, -800), ai.mirar(0, 1)), (f0, pos, ai.mirar(0, 1)), (f1 - 1, pos, ai.mirar(0, 1))])
    P.clip(ai, "mensajear", f0, f0 + 58, mapa=lambda f: min((f - f0) * 0.6 + 8, 130.0))
    P.clip(ai, "sorpresa", f0 + 51, f1, mapa=lambda f: (f - f0 - 51) * 0.55 + 6, mezcla=8)
    od.contar(1000000, 0, f0 + 20, f0 + 64)
    od.fin()
    cab = s0["cabeza"]
    mano = s0["mano"]
    c1 = Camara("cam_s8_a", col, 32.0)
    c1.seguir(cab)
    c1.claves(f0, f0 + 60, lambda f: O + Vector((1.40 - 0.05 * (f - f0) / 60.0, 0.30, 1.62)), None, fdof=lambda f: (1.9, 2.8), paso=1)
    c2 = Camara("cam_s8_b", col, 28.0)
    c2.seguir(s0['pecho'])
    c2.claves(f0 + 60, f1, lambda f: O + Vector((lerp(0.9, 0.55, suave((f - f0 - 60) / (f1 - f0 - 60))), lerp(3.9, 3.7, suave((f - f0 - 60) / (f1 - f0 - 60))), 1.45)), None, fdof=lambda f: (1.4, 2.4), paso=1)
    for f_, c_ in ((f0, c1), (f0 + 60, c2)):
        v = ctx.dir.corte(f_, c_)
        if f_ == f0:
            v.rampa(f0, f0 + 8, 1.0, 0.0, (0, 0, 0))
    v2 = ctx.dir.velos["cam_s8_b"]
    v2.rampa(f1 - 10, f1 - 1, 0.0, 1.0, (0, 0, 0))
    ctx.escena_activa(col, f0, f1)
