"""s0 «Dormitorio y teléfono» (0–285): amanecer en un dormitorio de Sweet Home; Aiden mira su celular: llega un aviso del banco, abre la app y el saldo rueda
hasta USD 1.000.000; cara de sorpresa; el zoom al número abre la transición hacia el mundo de posibilidades (lluvia de billetes y destello)."""
import math
import random
import bpy
from mathutils import Vector, Euler
import lib
from lib import *
import marco
import sh3d
import saldo as SAL
import personas as P
import guion

W, L, H = 5.0, 4.4, 2.7          # x, y, z (m): habitación centrada en x, y de 0 a L


def pantalla_png(ruta, modo):
    from PIL import Image, ImageDraw, ImageFont
    B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    im = Image.new("RGBA", (540, 1170), (10, 14, 22, 255))
    d = ImageDraw.Draw(im)
    if modo == "bloqueo":
        d.text((270, 170), "07:12", font=ImageFont.truetype(B, 150), fill=(255, 255, 255, 255), anchor="mm")
        d.text((270, 270), "sábado 21 de noviembre", font=ImageFont.truetype(R, 34), fill=(190, 200, 215, 255), anchor="mm")
        d.rounded_rectangle((30, 400, 510, 600), radius=34, fill=(235, 240, 248, 255))
        d.rounded_rectangle((52, 424, 124, 496), radius=16, fill=(18, 120, 90, 255))
        d.text((88, 460), "$", font=ImageFont.truetype(B, 52), fill=(255, 255, 255, 255), anchor="mm")
        d.text((146, 436), "BANCO DEL SUR", font=ImageFont.truetype(B, 30), fill=(30, 40, 55, 255))
        d.text((146, 480), "Depósito recibido", font=ImageFont.truetype(R, 30), fill=(70, 80, 95, 255))
        d.text((52, 540), "+ USD 1.000.000,00 acreditados", font=ImageFont.truetype(B, 34), fill=(18, 120, 90, 255))
    else:
        d.rectangle((0, 0, 540, 150), fill=(18, 120, 90, 255))
        d.text((40, 76), "BANCO DEL SUR", font=ImageFont.truetype(B, 44), fill=(255, 255, 255, 255), anchor="lm")
        d.text((270, 300), "Saldo disponible", font=ImageFont.truetype(R, 40), fill=(170, 185, 205, 255), anchor="mm")
        d.text((60, 470), "USD", font=ImageFont.truetype(B, 56), fill=(120, 230, 180, 255), anchor="lm")
        d.rounded_rectangle((40, 760, 500, 860), radius=22, outline=(120, 230, 180, 255), width=4)
        d.text((270, 810), "Cuenta de ahorro  ·  **** 4821", font=ImageFont.truetype(R, 32), fill=(190, 200, 215, 255), anchor="mm")
    im.save(ruta)
    return ruta


def telefono(col):
    """Celular de 7×15 cm: cuerpo oscuro y dos pantallas (bloqueo y app) que se alternan; el saldo es un odómetro de dígitos."""
    raiz = bpy.data.objects.new("telefono", None)
    col.objects.link(raiz)
    cuerpo = mat("cel_cuerpo", (0.02, 0.022, 0.03), metal=0.8, rug=0.25)
    c = caja("cel_cuerpo", (0, 0, 0), (0.072, 0.0085, 0.152), col, cuerpo)
    c.parent = raiz
    # frente del celular = −Y local (la pantalla mira hacia −Y)
    p1 = pantalla_png("/tmp/pant_bloqueo.png", "bloqueo")
    p2 = pantalla_png("/tmp/pant_app.png", "app")
    pantallas = []
    for nombre, ruta in (("bloqueo", p1), ("app", p2)):
        m = SAL.mat_imagen_emisivo("cel_pant_" + nombre, ruta, 1.1)
        o = SAL.plano_xy("cel_pant_" + nombre, (0, 0, 0), 0.066, 0.143, col, m)
        col.objects.link(o)
        o.parent = raiz
        o.location = (0, -0.0044, 0)
        o.visible_shadow = False
        # sombra de la pantalla: el material emite; para que se vea bien se agrega un fondo oscuro detrás
        pantallas.append(o)
    # odómetro del saldo sobre la pantalla de la app (dígitos de 8 × 12 mm)
    od = SAL.Odometro(col, "saldo_cel", 7, 0.0072, 0.0118, color=(1.0, 1.0, 1.0), fuerza=3.0)
    od.raiz.parent = raiz
    od.raiz.location = (0.0075, -0.0046, -0.0105)
    return raiz, pantallas, od


def dormitorio(col, O):
    pared = mat("pared_dorm", (0.78, 0.74, 0.68), rug=0.7)
    piso = mat_ruido("piso_dorm", (0.28, 0.17, 0.09), (0.42, 0.27, 0.15), 4.0, rug=0.35, bump=0.1)
    caja("piso", O + Vector((0, L / 2, -0.05)), (W, L, 0.1), col, piso)
    caja("techo", O + Vector((0, L / 2, H + 0.05)), (W, L, 0.1), col, pared)
    caja("pared_fondo", O + Vector((0, L + 0.05, H / 2)), (W + 0.2, 0.1, H), col, pared)
    caja("pared_frente", O + Vector((0, -0.05, H / 2)), (W + 0.2, 0.1, H), col, pared)
    caja("pared_sur", O + Vector((0, -0.55, H_ / 2)), (W_ + 0.3, 0.1, H_), col, pared)
    caja("pared_izq", O + Vector((-W / 2 - 0.05, L / 2, H / 2)), (0.1, L, H), col, pared)
    caja("pared_der", O + Vector((W / 2 + 0.05, L / 2, H / 2)), (0.1, L, H), col, pared)
    # la pared del fondo tiene un ventanal: se recorta con piezas (dintel y antepecho) y se deja pasar el sol
    return col


def construir(ctx, i, f0, f1):
    col = coleccion("S0_Dormitorio")
    O = Vector(ctx.desp(i))
    # ─── habitación (Sweet Home): cama, mesa de luz con lámpara, ropero, plantas
    pared = mat("pared_dorm", (0.78, 0.74, 0.68), rug=0.7)
    piso = mat_ruido("piso_dorm", (0.28, 0.17, 0.09), (0.42, 0.27, 0.15), 4.0, rug=0.35, bump=0.1)
    W_, L_, H_ = 5.0, 4.6, 2.7
    caja("piso", O + Vector((0, L_ / 2, -0.05)), (W_, L_, 0.1), col, piso)
    caja("techo", O + Vector((0, L_ / 2, H_ + 0.05)), (W_, L_, 0.1), col, pared)
    caja("pared_izq", O + Vector((-W_ / 2 - 0.05, L_ / 2, H_ / 2)), (0.1, L_, H_), col, pared)
    caja("pared_der", O + Vector((W_ / 2 + 0.05, L_ / 2, H_ / 2)), (0.1, L_, H_), col, pared)
    caja("pared_frente", O + Vector((0, -0.05, H_ / 2)), (W_ + 0.2, 0.1, H_), col, pared)
    # pared del fondo con ventanal de 2,4 × 1,6 m (antepecho a 0,9 m)
    for nom, c, d in (("izq", (-W_ / 2 + 0.7, L_ + 0.05, H_ / 2), (1.4, 0.1, H_)), ("der", (W_ / 2 - 0.7, L_ + 0.05, H_ / 2), (1.4, 0.1, H_)),
                      ("sup", (0, L_ + 0.05, 2.35), (2.2, 0.1, 0.7)), ("inf", (0, L_ + 0.05, 0.45), (2.2, 0.1, 0.9))):
        caja("pared_fondo_" + nom, O + Vector(c), d, col, pared)
    sh3d.poner("shop_window" if False else "triple_window", col, O + Vector((0, L_ + 0.0, 0.9 + 0.0)), frente=(0, -1))
    # cama con el cabecero contra la pared izquierda, mesa de luz y ropero a la derecha
    sh3d.poner("bed_5", col, O + Vector((-W_ / 2 + 1.3, 2.3, 0)), frente=(1, 0))
    sh3d.poner("table_bedside_table", col, O + Vector((-W_ / 2 + 0.4, 0.95, 0)), frente=(1, 0))
    sh3d.poner("table_desk_lamp", col, O + Vector((-W_ / 2 + 0.4, 0.95, 0.54)), frente=(1, 0))
    sh3d.poner("wardrobe_3", col, O + Vector((W_ / 2 - 0.4, 2.2, 0)), frente=(-1, 0))
    sh3d.poner("bush_indoor_plant", col, O + Vector((1.6, L_ - 0.5, 0)), frente=(0, -1))
    alfombra = mat("alfombra_dorm", (0.28, 0.32, 0.42), rug=0.95)
    caja("alfombra", O + Vector((0.3, 2.3, 0.01)), (2.4, 3.0, 0.02), col, alfombra)
    # sol de la mañana entrando por el ventanal y cielo cálido
    sol = bpy.data.lights.new("sol_dorm", "SUN")
    sol.energy = 6.0
    sol.color = (1.0, 0.82, 0.6)
    sol.angle = math.radians(1.5)
    so = bpy.data.objects.new("sol_dorm", sol)
    col.objects.link(so)
    so.rotation_euler = (math.radians(70), 0, math.radians(15))        # entra por el fondo (+Y) hacia −Y
    cielo = mat_emisivo("cielo_ventana", (0.75, 0.88, 1.0), 4.0)
    caja("cielo", O + Vector((0, L_ + 5.0, 1.8)), (14, 0.1, 8), col, cielo)
    # luz de relleno suave en la habitación
    rl = bpy.data.lights.new("relleno_dorm", "AREA")
    rl.energy = 220.0
    rl.size = 3.0
    rl.color = (1.0, 0.9, 0.78)
    ro = bpy.data.objects.new("relleno_dorm", rl)
    col.objects.link(ro)
    ro.location = O + Vector((0.5, 1.2, 2.55))
    ro.rotation_euler = (0, 0, 0)
    caja("panel_techo_dorm", O + Vector((0, 2.3, H_ - 0.03)), (3.6, 2.6, 0.04), col, mat_emisivo("panel_techo_dorm", (1.0, 0.94, 0.84), 6.0))
    lc = bpy.data.lights.new("luz_centro_dorm", "POINT")
    lc.energy = 320.0
    lc.shadow_soft_size = 0.8
    lc.color = (1.0, 0.93, 0.84)
    lco = bpy.data.objects.new("luz_centro_dorm", lc)
    col.objects.link(lco)
    lco.location = O + Vector((-0.8, 2.2, 2.3))
    for k_, (px_, py_) in enumerate(((-1.0, 3.4), (1.2, 0.6), (-1.2, 0.8))):
        rl2 = bpy.data.lights.new(f"relleno_dorm_{k_}", "AREA")
        rl2.energy = 160.0
        rl2.size = 2.5
        rl2.color = (1.0, 0.92, 0.82)
        ro2 = bpy.data.objects.new(f"relleno_dorm_{k_}", rl2)
        col.objects.link(ro2)
        ro2.location = O + Vector((px_, py_, 2.55))
    # ─── Aiden con el celular
    ai = ctx.aiden
    pos = O + Vector((0.5, 2.1, 0.0))
    P.colocar(ai, [(f0, pos, ai.mirar(0, 1)), (f1 - 1, pos, ai.mirar(0, 1))])
    P.clip(ai, "mensajear", f0, 230, mapa=lambda f: min((f - f0) * 0.6 + 8, 130.0))
    P.clip(ai, "sorpresa", 223, f1, mapa=lambda f: (f - 223) * 0.9 + 6, mezcla=8)
    # celular pegado a la mano derecha (vacío con constraints de posición y giro; el celular cuelga de él sin heredar la escala del personaje)
    tel, pantallas, od = telefono(col)
    mano = bpy.data.objects.new("mano_cel", None)
    col.objects.link(mano)
    c1 = mano.constraints.new("COPY_LOCATION")
    c1.target = ai.arm
    c1.subtarget = "mixamorig:RightHand"
    c2 = mano.constraints.new("COPY_ROTATION")
    c2.target = ai.arm
    c2.subtarget = "mixamorig:RightHand"
    tel.parent = mano
    tel.location = (0.0, 0.0, 0.0)
    tel.rotation_euler = (0, 0, 0)
    ctx.tel = (tel, mano)
    # alternar pantallas: bloqueo (0–126) → app (126–f1)
    pantallas[1].hide_render = True
    pantallas[1].keyframe_insert("hide_render", frame=0)
    pantallas[1].hide_render = False
    pantallas[1].keyframe_insert("hide_render", frame=126)
    pantallas[0].hide_render = False
    pantallas[0].keyframe_insert("hide_render", frame=0)
    pantallas[0].hide_render = True
    pantallas[0].keyframe_insert("hide_render", frame=126)
    od.poner(0, 0)
    od.poner(0, 130)
    od.contar(0, 1000000, 134, 190)
    od.poner(1000000, 285)
    od.fin()
    for o_ in (pantallas[0], pantallas[1]):
        lib._interp(o_, "CONSTANT")
    # ─── cámaras
    cabeza = P.vacio(ai, "mixamorig:Head", "cabeza_aiden", col, frac=0.5)
    pecho = P.vacio(ai, "mixamorig:Spine2", "pecho_aiden", col, frac=0.5)
    c1 = Camara("cam_s0_a", col, 24.0)
    c1.seguir(mano)
    c1.claves(f0, 113, lambda f: O + Vector((1.30 - 0.10 * (f / 113.0), 3.95, 1.55)), None, fdof=lambda f: (1.9, 2.8), paso=1)
    c2 = Camara("cam_s0_b", col, 45.0)
    c2.seguir(mano)
    c2.claves(113, 214, lambda f: O + Vector((lerp(1.25, 1.0, suave((f - 113) / 101.0)), lerp(3.7, 3.2, suave((f - 113) / 101.0)), lerp(1.55, 1.45, suave((f - 113) / 101.0)))), None, fdof=lambda f: (lerp(1.5, 1.0, suave((f - 113) / 101.0)), 2.8), paso=1)
    c3 = Camara("cam_s0_c", col, 28.0)
    c3.seguir(pecho)
    c3.claves(214, 264, lambda f: O + Vector((lerp(0.9, 0.7, (f - 214) / 50.0), 3.9, 1.45)), None, fdof=lambda f: (1.5, 2.4), paso=1)
    c4 = Camara("cam_s0_d", col, 40.0)
    c4.seguir(mano)
    c4.claves(264, f1 - 1, lambda f: O + Vector((0.55, 2.55 - 0.25 * suave((f - 264) / 21.0) - 0.0, 1.42)), None, flente=lambda f: lerp(40.0, 70.0, suave((f - 264) / 21.0)), fdof=lambda f: (0.4, 2.0), paso=1)
    for f_, c_ in ((f0, c1), (113, c2), (214, c3), (264, c4)):
        v = ctx.dir.corte(f_, c_)
        if f_ == f0:
            v.rampa(f0, f0 + 10, 1.0, 0.0, (0, 0, 0))
    v4 = ctx.dir.velos["cam_s0_d"]
    v4.rampa(272, f1 - 1, 0.0, 1.0, (1.0, 1.0, 1.0), 6.0)
    ctx.s0 = {"od": od, "ai": ai, "cabeza": cabeza, "pecho": pecho, "mano": mano, "O": O, "col": col, "tel": tel, "pantallas": pantallas}
    ctx.escena_activa(col, f0, f1)
