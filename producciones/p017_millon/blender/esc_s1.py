"""s1 «El prudente» (285–549): casa razonable al atardecer, auto sencillo, escritorio con cuentas y tres montones de monedas (casa, inversión, reserva)."""
import math
import random
import bpy
from mathutils import Vector
import lib
from lib import *
import marco
import sh3d
import casa as CASA
import saldo as SAL
import personas as P


def construir(ctx, i, f0, f1):
    col = coleccion("S1_Prudente")
    O = Vector(ctx.desp(i))
    rng = random.Random(11)
    ctx.bg_amb = (f0, (0.30, 0.38, 0.55), 1.0)
    ctx.amb.append((f0 - 1, (0.32, 0.4, 0.6), 1.1))
    # ─── casa razonable (techo a dos aguas), jardín, cerco, auto sencillo y árboles
    info = CASA.casa(col, O, 9.0, 7.0, 2.6, estilo="clasica", rng=rng, color=(0.82, 0.78, 0.68), techo_color=(0.35, 0.12, 0.08))
    CASA.jardin(col, O, 9.0, 7.0, rng, arboles=6)
    auto = sh3d.poner("small_car", col, O + Vector((6.0, -5.0, 0.06)), frente=(0, -1))      # el frente del auto mira hacia la calle (−Y)
    # luz del atardecer
    sol = bpy.data.lights.new("sol_s1", "SUN")
    sol.energy = 4.5
    sol.color = (1.0, 0.72, 0.45)
    sol.angle = math.radians(2.0)
    so = bpy.data.objects.new("sol_s1", sol)
    col.objects.link(so)
    so.rotation_euler = (math.radians(75), 0, math.radians(35))
    # ─── Aiden camina por el camino hasta la puerta (clip de caminata en ciclo; avanza hacia +Y)
    ai = ctx.aiden
    a0, a1 = f0, f0 + 100
    v = 1.25
    pos = lambda f: O + Vector((0.0, -9.0 + v * (f - a0) / 30.0, 0.15))
    P.colocar(ai, [(f, pos(min(f, a1)), ai.mirar(0, 1)) for f in range(a0, a1 + 1, 5)])
    P.clip(ai, "caminar_feliz", a0, a1, mapa=lambda f: (f - a0) * 1.0, ciclo=True)
    # ─── interior-estudio (escritorio con cuentas y barras de ahorro) en el recinto vecino de la escena
    E = O + Vector((60.0, 0, 0))
    piso = mat("piso_estudio", (0.3, 0.2, 0.12), rug=0.3)
    pared = mat("pared_estudio", (0.7, 0.66, 0.6), rug=0.7)
    caja("piso_e", E + Vector((0, 2.5, -0.05)), (6.0, 6.0, 0.1), col, piso)
    caja("pared_e", E + Vector((0, 5.55, 1.4)), (6.0, 0.1, 2.8), col, pared)
    caja("pared_ei", E + Vector((-3.05, 2.5, 1.4)), (0.1, 6.0, 2.8), col, pared)
    caja("pared_ed", E + Vector((3.05, 2.5, 1.4)), (0.1, 6.0, 2.8), col, pared)
    caja("techo_e", E + Vector((0, 2.5, 2.85)), (6.0, 6.0, 0.1), col, pared)
    sh3d.poner("table_desk", col, E + Vector((0.0, 4.5, 0)), frente=(0, -1))
    sh3d.poner("chair_office_chair_2", col, E + Vector((0.0, 5.05, 0)), frente=(0, -1))      # la silla mira al escritorio (−Y)… el escritorio está en −Y de la silla
    sh3d.poner("monitor_lcd", col, E + Vector((0.2, 4.6, 0.74)), frente=(0, -1))
    sh3d.poner("shelf_bookcase_3", col, E + Vector((-1.8, 5.35, 0)), frente=(0, -1))
    sh3d.poner("bush_indoor_plant", col, E + Vector((2.4, 4.9, 0)), frente=(0, -1))
    # tres montones de monedas con carteles: casa (50 %), inversión (30 %), reserva (20 %)
    oro = mat("moneda_oro", (1.0, 0.7, 0.18), metal=1.0, rug=0.25)
    verde = mat_emisivo("barra_verde", (0.2, 0.85, 0.45), 1.5)
    datos = [("CASA", 5, (-1.3, 3.1), (0.9, 0.75, 0.25)), ("INVERSIÓN", 3, (0.0, 3.1), (0.2, 0.7, 1.0)), ("RESERVA", 2, (1.3, 3.1), (0.3, 0.95, 0.5))]
    for nom, n, (x, y), colr in datos:
        h_ = 0.12 * n
        m_ = mat_emisivo("barra_" + nom, colr, 1.2)
        barra = cilindro("barra_" + nom, E + Vector((x, y, h_ / 2)), 0.32, h_, col, m_, seg=36)
        for k in range(n * 3):
            cilindro(f"mon_{nom}_{k}", E + Vector((x + rng.uniform(-0.1, 0.1), y + 0.45 + rng.uniform(-0.05, 0.05), 0.03 + 0.035 * k)), 0.11, 0.03, col, oro, rot=(0, 0, 0), seg=24)
        et = SAL.etiqueta(col, nom, alto_m=0.22)
        et.location = E + Vector((x, y - 0.5, h_ + 0.25))
    # ─── cámaras
    tgt = P.vacio(ai, "mixamorig:Hips", "cadera_aiden", col)
    c1 = Camara("cam_s1_a", col, 28.0)
    c1.claves(f0, f0 + 100, lambda f: O + Vector((lerp(-3.5, 2.5, (f - f0) / 100.0), -13.0, lerp(1.1, 1.8, (f - f0) / 100.0))), lambda f: O + Vector((0, -2.5, 1.2)), fdof=lambda f: (11.5, 3.5), paso=1)
    c2 = Camara("cam_s1_b", col, 24.0)
    c2.claves(f0 + 100, f0 + 160, lambda f: O + Vector((lerp(6.0, 4.4, (f - f0 - 100) / 60.0), -9.0, 1.0)), lambda f: O + Vector((6.0, -5.0, 0.7)), fdof=lambda f: (6.0, 3.0), paso=1)
    c3 = Camara("cam_s1_c", col, 30.0)
    c3.claves(f0 + 160, f0 + 215, lambda f: E + Vector((lerp(-2.4, 2.4, (f - f0 - 160) / 55.0), 0.3, 1.5)), lambda f: E + Vector((0, 4.4, 0.9)), fdof=lambda f: (4.5, 3.0), paso=1)
    c4 = Camara("cam_s1_d", col, 20.0)
    c4.claves(f0 + 215, f1, lambda f: E + Vector((lerp(2.2, -1.8, (f - f0 - 215) / 49.0), 0.4, lerp(1.9, 1.0, (f - f0 - 215) / 49.0))), lambda f: E + Vector((0, 3.1, 0.35)), fdof=lambda f: (3.2, 2.8), paso=1)
    for f_, c_ in ((f0, c1), (f0 + 100, c2), (f0 + 160, c3), (f0 + 215, c4)):
        v_ = ctx.dir.corte(f_, c_)
        if f_ == f0:
            v_.rampa(f0, f0 + 12, 1.0, 0.0, (1.0, 1.0, 1.0), 6.0)
    ctx.escena_activa(col, f0, f1)
