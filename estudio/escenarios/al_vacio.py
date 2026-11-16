"""AL VACÍO — el minijuego «Botón de caída» de Free Kick Swipe (s4muy3ni-lang/Free-Kick-Swipe,
scripts/minigames/boton_caida.gd), recreado y mejorado para video vertical.

Reglas del juego (iguales): dos plataformas enfrentadas sobre un vacío, separadas por un hueco; cada una tiene al fondo
un tablero blanco con un BOTÓN (aro dorado; en el video verde, rojo al apretarlo). Por turnos, cada jugador patea su pelota (física real: vuelo, efecto,
rebotes); si la pelota GOLPEA el botón rival con fuerza (impacto contra la cara ≥ 2,5 m/s: un roce no alcanza), el botón
se hunde y se pone verde, se abre la trampilla de dos hojas bajo los pies del rival y cae al vacío. Gana el primero que
hace caer al otro las veces pedidas.

Escenario (del juego): plataformas rosadas con un toque del color de cada equipo (azul / rojo), barandas doradas con
postes de luz, borde amarillo contra el vacío, flechas en el piso, trampilla amarilla, torres de vigas de hierro que
bajan y se pierden en una niebla oscura con balizas rojas, fondo del abismo, estadio nocturno con tribunas y el público
2D del juego (assets/arcade/crowd_atlas.png).

Mejoras para el video: ascensor que devuelve al que cayó (sube por la trampilla), llamaradas en las esquinas cuando
alguien cae, luces de estadio con haces, LED de color bajo cada plataforma, niebla volumétrica en el vacío y papelitos
al final.

Ejes (Blender): X = de una plataforma a la otra (azul en x < 0 mira a +X; roja en x > 0 mira a −X), Y = ancho, Z arriba.
"""
from __future__ import annotations
import math
import random
import bmesh
import bpy
from mathutils import Vector
from estudio import config
from estudio.blender import kit as K, pelota as B

GAP = 12.0          # hueco entre plataformas (nivel 1 «A la vista»)
DEPTH = 10.5        # (el juego: 7,5) más larga para la carrera de 5 m de los tiros libres de Messi y Cristiano
WIDTH = 9.0
HOLE = 2.3
BUTTON_X = 9.4      # del borde al botón, al fondo (el juego: 6,2)
BUTTON_Z = 1.2
BUTTON_R = 0.55
CAP = 0.14
BALL_BACK = 2.2     # la pelota a 2,2 m del borde
HOLE_BACK = 3.2     # el jugador espera sobre la trampilla, un metro detrás de la pelota
PRESS_SPEED = 2.5
DOOR_OPEN_T = 0.35
TOWER_DEPTH = 30.0
COLOR_EQUIPO = [(0.2, 0.45, 0.95), (0.9, 0.25, 0.25)]
DECK_PINK = (0.93, 0.55, 0.7)
ORO = (1.0, 0.72, 0.25)

PARAMETROS = {"semilla": 7, "publico": 1.0, "animo": [[0, "tension"]], "llamaradas": [], "papelitos_s": None,
              "duracion_s": 60.0}
REF_ATLAS = "mixamo:futbol_free_kick_swipe/03_estadio_publico/assets/arcade/crowd_atlas.png"


def signo(s: int) -> float:
    """azul (0) en x < 0, rojo (1) en x > 0."""
    return -1.0 if s == 0 else 1.0


def borde_x(s: int) -> float:
    return signo(s) * GAP / 2


def hacia_rival(s: int) -> float:
    """+1: la plataforma azul mira a +X."""
    return -signo(s)


def local(s: int, adentro: float, y: float = 0.0, z: float = 0.0) -> Vector:
    """Punto de la plataforma s a `adentro` m del borde hacia el fondo."""
    return Vector((borde_x(s) + signo(s) * adentro, y, z))


def centro_boton(s: int) -> Vector:
    """Centro de la cara del botón (la que mira al rival)."""
    return local(s, BUTTON_X, 0.0, BUTTON_Z) + Vector((hacia_rival(s) * CAP, 0, 0))


def lugar_pelota(s: int) -> Vector:
    return local(s, BALL_BACK, 0.0, B.RADIO)


STANCE = (2.4, 2.3)          # el juego: el que patea espera 2,4 m detrás de la pelota y 2,3 m al costado
PIE = {0: 1, 1: 1}           # 1 diestro (espera a la izquierda de la pelota), −1 zurdo (a la derecha); lo fija la receta


def trampilla(s: int) -> Vector:
    """Donde espera cada jugador (y su trampilla): como Minigame.stance_point del juego, al costado de la línea de la
    pelota al botón, así nunca queda delante del botón."""
    izquierda = 1.0 if s == 0 else -1.0                    # mirando al rival: +Y es la izquierda de la plataforma azul
    return local(s, BALL_BACK + STANCE[0], izquierda * STANCE[1] * PIE[s], 0.0)


# ------------------------------------------------------------------------------------------------ física de la pelota

def simular_pelota(p0, v0, w0=(0, 0, 0), duracion=5.0, dt=1 / 240, presionados=()):
    """Vuelo con arrastre y Magnus (las constantes de estudio/blender/pelota.py) contra las cubiertas, los tableros y los
    botones. Devuelve (trayectoria [(t, pos, vel, w)], eventos [{tipo, t, lado, impacto}]). Sin piso abajo: el vacío."""
    p, v, w = Vector(p0), Vector(v0), Vector(w0)
    R = B.RADIO
    area = math.pi * R * R
    out, ev = [], []
    t = 0.0
    while t <= duracion and p.z > -45.0:
        out.append((t, p.copy(), v.copy(), w.copy()))
        sp = v.length
        if sp > 0:
            f = 0.5 * B.RHO * B.CD * area * sp * sp
            v -= v.normalized() * min(sp, f / B.MASA * dt)
        if sp > 1.0:
            v += w.cross(v) * (B.MAGNUS_K / B.MASA) * dt
        v.z -= B.G * dt
        prev = p.copy()
        p += v * dt
        for s in (0, 1):
            x_b, x_f = sorted((borde_x(s), borde_x(s) + signo(s) * DEPTH))
            # cubierta (arriba en z = 0)
            if x_b <= p.x <= x_f and abs(p.y) <= WIDTH / 2 and p.z < R and prev.z >= R - 0.02:
                p.z = R
                if v.z < -0.6:
                    v.z = -v.z * B.REBOTE
                    w *= 0.8
                    ev.append({"tipo": "pique", "t": t, "lado": s, "impacto": abs(v.z)})
                else:
                    v.z = 0.0
                    hs = math.hypot(v.x, v.y)
                    if hs > 0:
                        k = max(0.0, hs - (B.ROD_A + B.ROD_C * min(hs, B.ROD_VK)) * dt) / hs
                        v.x *= k
                        v.y *= k
            # tablero del botón (frente hacia el rival)
            n = hacia_rival(s)
            frente = borde_x(s) + signo(s) * BUTTON_X
            cara_cap = frente + n * CAP
            if abs(p.y) <= 1.2 + R and 0.0 <= p.z <= 2.2 + R:
                for plano, es_cap in ((cara_cap, True), (frente, False)):
                    if (prev.x - plano) * n >= R - 1e-4 and (p.x - plano) * n < R:
                        d_cap = math.hypot(p.y, p.z - BUTTON_Z)
                        if es_cap and d_cap > BUTTON_R + R * 0.5:
                            continue
                        impacto = -v.x * n
                        if impacto <= 0:
                            continue
                        p.x = plano + n * R
                        rest = 0.35 if es_cap else 0.5
                        v.x = n * impacto * rest
                        v.y *= 0.8
                        v.z *= 0.8
                        w *= 0.6
                        tipo = "boton" if es_cap else "tablero"
                        if es_cap and (impacto < PRESS_SPEED or s in presionados):
                            tipo = "roce"
                        ev.append({"tipo": tipo, "t": t, "lado": s, "impacto": round(impacto, 2)})
                        break
        t += dt
    return out, ev


def resolver(p0, destino, velocidad, efecto=(0, 0, 0), iteraciones=50):
    """Dirección de salida para pasar por `destino` (en el plano del destino) a `velocidad`."""
    p0, destino = Vector(p0), Vector(destino)
    d = destino - p0
    horiz = Vector((d.x, d.y, 0))
    yaw = math.atan2(d.y, d.x)
    pitch = math.atan2(d.z, horiz.length) + 0.1
    eje = horiz.normalized()
    for _ in range(iteraciones):
        v0 = Vector((math.cos(pitch) * math.cos(yaw), math.cos(pitch) * math.sin(yaw), math.sin(pitch))) * velocidad
        tray, _e = simular_pelota(p0, v0, efecto, duracion=2.5, presionados=(0, 1))   # sin rebotes en botones
        cerca = min(tray, key=lambda q: abs((q[1] - p0).dot(eje) - horiz.length))
        err = destino - cerca[1]
        lat = Vector((-eje.y, eje.x, 0))
        yaw += err.dot(lat) / max(1.0, horiz.length) * 0.9
        pitch += err.z / max(1.0, horiz.length) * 0.9
        if err.length < 0.015:
            break
    return Vector((math.cos(pitch) * math.cos(yaw), math.cos(pitch) * math.sin(yaw), math.sin(pitch))) * velocidad


# ------------------------------------------------------------------------------------------------ escenario

def _mat_publico(atlas_ruta, animo):
    """Hinchas 2D del juego: fila del atlas por hincha (atributo «fila»), columna (pose) según el ánimo, alternando."""
    mat = bpy.data.materials.new("publico_vacio")
    mat.use_nodes = True
    nt = mat.node_tree
    N, L = nt.nodes, nt.links
    N.clear()
    out = N.new("ShaderNodeOutputMaterial")
    emi = N.new("ShaderNodeEmission")
    emi.inputs["Strength"].default_value = 0.55
    tr = N.new("ShaderNodeBsdfTransparent")
    mixs = N.new("ShaderNodeMixShader")
    uv = N.new("ShaderNodeUVMap")
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(uv.outputs["UV"], sep.inputs[0])
    at_fila = N.new("ShaderNodeAttribute")
    at_fila.attribute_name = "fila"
    at_fase = N.new("ShaderNodeAttribute")
    at_fase.attribute_name = "fase"
    cols = {"calma": 0, "aplauso": 1, "festejo": 2, "salta": 3, "tension": 4, "bronca": 5}
    fps = bpy.context.scene.render.fps
    # ánimo en el tiempo con claves constantes (una expresión anidada larga no entra en un controlador de Blender)
    base = N.new("ShaderNodeValue")
    ritmo = N.new("ShaderNodeValue")
    for seg, a in sorted(animo, key=lambda x: x[0]):
        f = int(seg * fps) + 1
        base.outputs[0].default_value = cols.get(a, 0)
        base.outputs[0].keyframe_insert("default_value", frame=f)
        ritmo.outputs[0].default_value = 30 if a in ("calma", "tension") else 4
        ritmo.outputs[0].keyframe_insert("default_value", frame=f)
    if nt.animation_data and nt.animation_data.action:
        for fc in K._fcurves(nt.animation_data.action):
            for kp in fc.keyframe_points:
                kp.interpolation = "CONSTANT"
    cuadro = N.new("ShaderNodeValue")
    cuadro.outputs[0].driver_add("default_value").driver.expression = "frame"

    def op(tipo, a, b=None):
        n = N.new("ShaderNodeMath")
        n.operation = tipo
        for i, x in enumerate((a, b)):
            if x is None:
                continue
            if isinstance(x, (int, float)):
                n.inputs[i].default_value = x
            else:
                L.new(x, n.inputs[i])
        return n.outputs[0]
    # alterna entre la columna base y la siguiente (aplauso ↔ festejo…) con una fase por hincha
    paso = op("FLOOR", op("DIVIDE", op("ADD", cuadro.outputs[0], op("MULTIPLY", at_fase.outputs["Fac"], 40.0)), ritmo.outputs[0]))
    alterna = op("MODULO", paso, 2.0)
    col = op("MINIMUM", op("ADD", base.outputs[0], alterna), 5.0)
    fila = op("FLOOR", op("MULTIPLY", at_fila.outputs["Fac"], 12.0))
    u = op("DIVIDE", op("ADD", col, sep.outputs["X"]), 6.0)
    v = op("SUBTRACT", 1.0, op("DIVIDE", op("SUBTRACT", op("ADD", fila, 1.0), sep.outputs["Y"]), 12.0))
    comb = N.new("ShaderNodeCombineXYZ")
    L.new(u, comb.inputs[0])
    L.new(v, comb.inputs[1])
    tex = N.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(atlas_ruta), check_existing=True)
    tex.interpolation = "Closest"
    tex.extension = "CLIP"
    L.new(comb.outputs[0], tex.inputs["Vector"])
    L.new(tex.outputs["Color"], emi.inputs["Color"])
    L.new(tex.outputs["Alpha"], mixs.inputs["Fac"])
    L.new(tr.outputs[0], mixs.inputs[1])
    L.new(emi.outputs[0], mixs.inputs[2])
    L.new(mixs.outputs[0], out.inputs["Surface"])
    return mat


def _tribuna(nombre, lado_y: float, x0: float, x1: float, filas: int, col, mat_grada, mat_pub, rnd, densidad=1.0):
    """Tribuna escalonada a lo largo de X del lado lado_y (±1), mirando al centro, con un hincha 2D por butaca."""
    bm = bmesh.new()
    pub = bmesh.new()
    lay_uv = pub.loops.layers.uv.new("UVMap")
    a_fila = pub.faces.layers.float.new("fila")
    a_fase = pub.faces.layers.float.new("fase")
    y0, z0 = 15.0, -7.0
    paso_y, paso_z = 1.0, 0.55
    for i in range(filas):
        y_a, y_b = y0 + i * paso_y, y0 + (i + 1) * paso_y
        z = z0 + i * paso_z
        for (ya, yb, za, zb) in ((y_a, y_b, z, z), ):
            vs = [bm.verts.new((x0, lado_y * ya, za)), bm.verts.new((x1, lado_y * ya, za)),
                  bm.verts.new((x1, lado_y * yb, zb)), bm.verts.new((x0, lado_y * yb, zb))]
            bm.faces.new(vs)
        # contrahuella
        vs = [bm.verts.new((x0, lado_y * y_b, z)), bm.verts.new((x1, lado_y * y_b, z)),
              bm.verts.new((x1, lado_y * y_b, z + paso_z)), bm.verts.new((x0, lado_y * y_b, z + paso_z))]
        bm.faces.new(vs)
        x = x0 + 0.4
        while x < x1 - 0.4:
            if rnd.random() < densidad:
                w, h = 0.62, 0.84
                yc = lado_y * (y_a + 0.45)
                cx = x + rnd.uniform(-0.08, 0.08)
                vs = [pub.verts.new((cx - w / 2, yc, z)), pub.verts.new((cx + w / 2, yc, z)),
                      pub.verts.new((cx + w / 2, yc, z + h)), pub.verts.new((cx - w / 2, yc, z + h))]
                f = pub.faces.new(vs)
                for lp, uvv in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
                    lp[lay_uv].uv = uvv
                f[a_fila] = rnd.random() * 0.999
                f[a_fase] = rnd.random()
            x += 0.66
    # techo/viga de la tribuna y pared del fondo
    yb = y0 + filas * paso_y
    zt = z0 + filas * paso_z
    for vs in (((x0, lado_y * yb, z0), (x1, lado_y * yb, z0), (x1, lado_y * yb, zt + 6), (x0, lado_y * yb, zt + 6)),):
        bm.faces.new([bm.verts.new(q) for q in vs])
    me = bpy.data.meshes.new(nombre)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat_grada)
    ob = bpy.data.objects.new(nombre, me)
    col.objects.link(ob)
    mp = bpy.data.meshes.new(nombre + "_publico")
    pub.to_mesh(mp)
    pub.free()
    mp.materials.append(mat_pub)
    op = bpy.data.objects.new(nombre + "_publico", mp)
    col.objects.link(op)
    op["visor_lod"] = "bajo"
    return ob


def _viga(bm, a: Vector, b: Vector, t: float):
    """Viga cuadrada de a a b (sección t)."""
    d = (b - a)
    if d.length < 1e-4:
        return
    eje = d.normalized()
    ref = Vector((0, 0, 1)) if abs(eje.z) < 0.9 else Vector((1, 0, 0))
    u = eje.cross(ref).normalized() * t / 2
    v = eje.cross(u).normalized() * t / 2
    ca = [a + u + v, a - u + v, a - u - v, a + u - v]
    cb = [b + u + v, b - u + v, b - u - v, b + u - v]
    va = [bm.verts.new(q) for q in ca]
    vb = [bm.verts.new(q) for q in cb]
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new([va[i], va[j], vb[j], vb[i]])


def _torre(s: int, col, m_hierro, m_baliza):
    """Torre de vigas de hierro bajo la plataforma: cuatro patas que se angostan, anillos, cruces y balizas rojas."""
    bm = bmesh.new()
    luces = []
    x_a, x_b = sorted((borde_x(s) + signo(s) * 0.35, borde_x(s) + signo(s) * (DEPTH - 0.35)))
    cx = (x_a + x_b) / 2
    hz = WIDTH / 2 - 0.35
    top, bottom = -1.0, -TOWER_DEPTH

    def esquina(i, z):
        u = min(1.0, max(0.0, (top - z) / (top - bottom)))
        k = 1.0 + (0.45 - 1.0) * u
        lx = x_a if i in (0, 3) else x_b
        ly = -hz if i < 2 else hz
        return Vector((cx + (lx - cx) * k, ly * k, z))
    for i in range(4):
        _viga(bm, esquina(i, top + 0.02), esquina(i, bottom), 0.42)
    bays = int(math.ceil((top - bottom) / 3.4))
    for b in range(bays + 1):
        z = top - b * 3.4
        for i in range(4):
            j = (i + 1) % 4
            _viga(bm, esquina(i, z), esquina(j, z), 0.26)
            if b < bays:
                _viga(bm, esquina(i, z), esquina(j, z - 3.4), 0.14)
                _viga(bm, esquina(j, z), esquina(i, z - 3.4), 0.14)
        if b % 2 == 1:
            for i in range(4):
                luces.append(esquina(i, z))
    me = bpy.data.meshes.new(f"torre_{s}")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(m_hierro)
    ob = bpy.data.objects.new(f"torre_{s}", me)
    col.objects.link(ob)
    for k, q in enumerate(luces):
        K.esfera(f"baliza_{s}_{k}", q + (q - Vector((cx, 0, q.z))).normalized() * 0.3, 0.13, m_baliza, col, subdiv=1)


def _plataforma(s: int, col, mats):
    """Cubierta con el hueco de la trampilla, barandas doradas con postes de luz, borde amarillo, flechas, trampilla de
    dos hojas (con su bisagra animable), tablero y botón."""
    c = tuple(DECK_PINK[i] + (COLOR_EQUIPO[s][i] - DECK_PINK[i]) * 0.25 for i in range(3))
    m_deck = K.material(f"cubierta_{s}", tuple(x * 0.85 for x in c), 0.45, ruido=0.08, escala_ruido=6, relieve=0.05)
    h = trampilla(s)
    hx0, hx1 = h.x - HOLE / 2, h.x + HOLE / 2
    w2 = WIDTH / 2
    xa, xb = sorted((borde_x(s), borde_x(s) + signo(s) * DEPTH))
    hy0, hy1 = h.y - HOLE / 2, h.y + HOLE / 2
    piezas = [((xa, -w2), (hx0, w2)), ((hx1, -w2), (xb, w2)), ((hx0, -w2), (hx1, hy0)), ((hx0, hy1), (hx1, w2))]
    objs = {}
    for k, ((ax, ay), (bx, by)) in enumerate(piezas):
        if bx - ax < 0.01 or by - ay < 0.01:
            continue
        K.caja(f"cubierta_{s}_{k}", ((ax + bx) / 2, (ay + by) / 2, -0.5), (bx - ax, by - ay, 1.0), m_deck, col, bisel=0.02)
    # borde claro contra el vacío
    K.caja(f"borde_{s}", (borde_x(s) - signo(s) * 0.1, 0, 0.02), (0.25, WIDTH, 0.04), mats["borde"], col)
    # LED de color bajo el borde (mejora)
    K.caja(f"led_{s}", (borde_x(s) - signo(s) * 0.02, 0, -0.55), (0.06, WIDTH, 0.12),
           K.emisivo(f"led_equipo_{s}", COLOR_EQUIPO[s], 18.0), col)
    for sy in (-1, 1):
        K.caja(f"led_lado_{s}_{sy}", ((xa + xb) / 2, sy * (WIDTH / 2 + 0.02), -0.55), (DEPTH, 0.06, 0.12),
               K.emisivo(f"led_equipo_{s}", COLOR_EQUIPO[s], 18.0), col)
    # barandas doradas y postes con luz
    for sy in (-1, 1):
        K.caja(f"baranda_{s}_{sy}", ((xa + xb) / 2 - signo(s) * 0.3 * 0, sy * (w2 - 0.1), 0.9), (DEPTH - 1.0, 0.08, 0.08),
               mats["oro"], col)
        for k in range(4):
            x = xa + 0.8 + k * (DEPTH - 1.6) / 3
            K.caja(f"poste_{s}_{sy}_{k}", (x, sy * (w2 - 0.1), 0.45), (0.1, 0.1, 0.9), mats["oro"], col)
            K.esfera(f"foco_{s}_{sy}_{k}", (x, sy * (w2 - 0.1), 0.95), 0.08, mats["foco"], col, subdiv=1)
        for k in range(2):
            for sg in (-1, 1):
                fl = K.caja(f"flecha_{s}_{sy}_{k}_{sg}", (borde_x(s) + signo(s) * (1.4 + k * 0.6), sy * (w2 - 1.2) + sg * 0.25,
                                                          0.008), (0.14, 0.7, 0.012), mats["flecha"], col)
                fl.rotation_euler.z = sg * 0.7 * hacia_rival(s)
    # trampilla: dos hojas que giran hacia abajo sobre sus bordes (en Y)
    hojas = []
    for k, sg in enumerate((-1, 1)):
        bis = K.vacio(f"bisagra_{s}_{k}", (h.x, h.y + sg * HOLE / 2, -0.06), col)
        hoja = K.caja(f"trampa_{s}_{k}", (h.x, h.y + sg * HOLE / 4, -0.06), (HOLE, HOLE / 2 - 0.01, 0.12), mats["trampa"], col)
        hoja.parent = bis
        hoja.location = (0, -sg * HOLE / 4, 0)
        hojas.append(bis)
    # tablero blanco y botón rojo con aro dorado
    frente = borde_x(s) + signo(s) * BUTTON_X
    K.caja(f"tablero_{s}", (frente + signo(s) * 0.15, 0, 1.1), (0.3, 2.4, 2.2), mats["tablero"], col, bisel=0.03)
    boton = K.cilindro(f"boton_{s}", (frente + hacia_rival(s) * CAP / 2, 0, BUTTON_Z), BUTTON_R, CAP, mats["boton"], col,
                       lados=40, eje="X")
    aro = bpy.data.objects.new(f"aro_{s}", bpy.data.meshes.new(f"aro_{s}"))
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=False, segments=48, radius1=BUTTON_R + 0.12, radius2=BUTTON_R + 0.12, depth=0.1)
    bm.to_mesh(aro.data)
    bm.free()
    aro.data.materials.append(mats["oro"])
    col.objects.link(aro)
    aro.location = (frente + hacia_rival(s) * 0.05, 0, BUTTON_Z)
    aro.rotation_euler = (0, math.pi / 2, 0)
    # material verde para cuando se aprieta
    boton["verde"] = mats["boton_verde"].name
    objs.update({"hojas": hojas, "boton": boton})
    return objs


def _llamarada(nombre, pos, col):
    """Chorro de fuego (mejora): cono emisivo con ruido + luz; se dispara animando la escala Z."""
    m = bpy.data.materials.get("fuego") or K.material("fuego", (1.0, 0.45, 0.08), 0.5, emision=(1.0, 0.42, 0.06),
                                                      fuerza=40.0, ruido=0.6, escala_ruido=3, ruido_en_emision=True,
                                                      animar_ruido=2.0)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.35, radius2=0.05, depth=5.0)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, 2.5))
    me = bpy.data.meshes.new(nombre)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(m)
    ob = bpy.data.objects.new(nombre, me)
    col.objects.link(ob)
    ob.location = pos
    ob.scale = (1, 1, 0.001)
    lz = K.luz(nombre + "_luz", "POINT", (pos[0], pos[1], pos[2] + 2.0), 0.0, (1.0, 0.5, 0.15), col)
    return ob, lz


def construir(parametros: dict | None = None) -> dict:
    p = {**PARAMETROS, **(parametros or {})}
    for k, v in (p.get("pie") or {}).items():
        PIE[int(k)] = int(v)
    rnd = random.Random(p["semilla"])
    s = K.bpy.context.scene
    fps = s.render.fps
    col = K.coleccion("ESCENARIO_al_vacio")
    c_pl, c_est, c_fx = (K.coleccion(n, col) for n in ("plataformas", "estadio", "efectos"))
    K.cielo_noche(s, cenit=(0.002, 0.002, 0.008), horizonte=(0.02, 0.014, 0.04), estrellas=True)
    mats = {
        "oro": K.material("oro_baranda", ORO, 0.25, 1.0),
        "foco": K.emisivo("foco_baranda", (1.0, 0.85, 0.45), 12.0),
        "borde": K.material("borde_amarillo", (1, 0.85, 0.3), 0.4, emision=(1, 0.8, 0.25), fuerza=1.5),
        "flecha": K.material("flecha", (1.0, 0.8, 0.1), 0.5),
        "trampa": K.material("trampilla", (0.95, 0.75, 0.15), 0.45, ruido=0.1, relieve=0.1),
        "tablero": K.material("tablero", (0.95, 0.95, 0.98), 0.35),
        # pedido del dueño: el botón está VERDE y se pone ROJO cuando la pelota lo aprieta (alarma: se abre el piso)
        "boton": K.material("boton_verde", (0.2, 0.95, 0.3), 0.25, emision=(0.1, 1.0, 0.2), fuerza=3.0),
        "boton_verde": K.material("boton_rojo", (0.95, 0.12, 0.1), 0.25, emision=(1.0, 0.08, 0.05), fuerza=8.0),
    }
    plats = [_plataforma(k, c_pl, mats) for k in (0, 1)]
    m_hierro = K.material("hierro_torre", (0.5, 0.52, 0.58), 0.45, 0.8, ruido=0.25, escala_ruido=10)
    m_baliza = K.emisivo("baliza_roja", (1.0, 0.15, 0.1), 25.0)
    for k in (0, 1):
        _torre(k, c_pl, m_hierro, m_baliza)
    # el abismo y la niebla del vacío
    K.plano("abismo", (0, 0, -60), (400, 400), K.material("abismo", (0.03, 0.03, 0.08), 0.9), c_est)
    niebla = K.caja("niebla_vacio", (0, 0, -24), (160, 120, 42), None, c_est)
    mv = bpy.data.materials.new("niebla_vacio")
    mv.use_nodes = True
    nt = mv.node_tree
    nt.nodes.remove(nt.nodes.get("Principled BSDF"))
    vol = nt.nodes.new("ShaderNodeVolumePrincipled")
    vol.inputs["Color"].default_value = (0.25, 0.18, 0.55, 1)
    vol.inputs["Density"].default_value = 0.09
    nt.links.new(vol.outputs[0], nt.nodes.get("Material Output").inputs["Volume"])
    niebla.data.materials.clear()
    niebla.data.materials.append(mv)
    niebla["visor_omitir"] = True
    # estadio: tribunas a los dos costados y en las cabeceras, con el público del juego
    m_grada = K.material("grada", (0.16, 0.17, 0.24), 0.8, ruido=0.2, escala_ruido=12)
    animo = p["animo"]
    m_pub = _mat_publico(config.resolver(REF_ATLAS), animo)
    for ly in (-1, 1):
        _tribuna(f"tribuna_{'n' if ly > 0 else 's'}", ly, -34, 34, 22, c_est, m_grada, m_pub, rnd, p["publico"])
    # torres de luz en las esquinas con paneles LED y focos que apuntan a las plataformas
    m_panel = K.emisivo("panel_led", (1.0, 0.97, 0.9), 30.0)
    m_acero = K.material("acero_torre_luz", (0.35, 0.36, 0.4), 0.4, 0.9)
    for ix, sx in enumerate((-1, 1)):
        for iy, sy in enumerate((-1, 1)):
            base = Vector((sx * 30, sy * 32, -8))
            K.caja(f"mastil_{ix}{iy}", (base.x, base.y, 9), (0.8, 0.8, 34), m_acero, c_est)
            panel = K.caja(f"panel_{ix}{iy}", (base.x - sx * 0.6, base.y - sy * 0.6, 26), (4.0, 0.4, 2.6), m_panel, c_est)
            panel.rotation_euler.z = math.atan2(-sy, -sx) + math.pi / 2
            foco = K.luz(f"foco_estadio_{ix}{iy}", "SPOT", (base.x, base.y, 25.5), 90000.0, (1.0, 0.95, 0.88), c_est,
                         tam=1.5)
            foco.data.spot_size = math.radians(38)
            foco.data.spot_blend = 0.5
            K.mirar_a(foco, Vector((sx * 6, 0, 0)))
    # luz de relleno fría desde arriba y contraluz de color por equipo
    K.luz("relleno_cenital", "AREA", (0, 0, 22), 2500.0, (0.75, 0.8, 1.0), c_est, tam=20.0)
    for k in (0, 1):
        c = local(k, DEPTH + 3, 0, 6)
        lz = K.luz(f"contraluz_{k}", "SPOT", tuple(c), 6000.0, COLOR_EQUIPO[k], c_est, tam=1.0)
        lz.data.spot_size = math.radians(55)
        K.mirar_a(lz, trampilla(k) + Vector((0, 0, 1.2)))
    # haz desde el fondo del abismo (atraviesa la niebla): ilumina al que cae y a la trampilla desde abajo
    for k in (0, 1):
        q = trampilla(k)
        hz = K.luz(f"haz_abismo_{k}", "SPOT", (q.x, q.y, -26.0), 60000.0, (0.55, 0.45, 1.0), c_est, tam=0.6)
        hz.data.spot_size = math.radians(16)
        hz.data.spot_blend = 0.6
        K.mirar_a(hz, q)
    # llamaradas en las esquinas exteriores de cada plataforma (se disparan cuando alguien cae)
    llamas = {0: [], 1: []}
    for k in (0, 1):
        for sy in (-1, 1):
            for adentro in (0.3, DEPTH - 0.3):
                q = local(k, adentro, sy * (WIDTH / 2 + 0.6), -0.4)
                llamas[k].append(_llamarada(f"llamarada_{k}_{sy}_{int(adentro)}", tuple(q), c_fx))
    for t, lado in p["llamaradas"]:
        f0 = int(round(t * fps)) + 1
        for ob, lz in llamas[lado]:
            for fr, esc, en in ((f0 - 1, 0.001, 0.0), (f0 + 4, 1.15, 25000.0), (f0 + 26, 0.9, 18000.0), (f0 + 40, 0.001, 0.0)):
                ob.scale = (1, 1, esc)
                ob.keyframe_insert("scale", frame=fr)
                lz.data.energy = en
                lz.data.keyframe_insert("energy", frame=fr)
    if p.get("papelitos_s") is not None:
        _papelitos(c_fx, p["papelitos_s"], fps, rnd)
    # soportes de los jugadores (el personaje va «sobre» su soporte: cae y sube con él)
    soportes = []
    for k in (0, 1):
        so = K.vacio(f"soporte_{k}", tuple(trampilla(k)), c_pl)
        disco = K.cilindro(f"ascensor_{k}", (0, 0, -0.2), 1.05, 0.12, K.material("ascensor", (0.25, 0.26, 0.3), 0.3, 0.9), c_pl,
                           lados=40)
        disco.parent = so
        disco.location = (0, 0, -0.2)
        soportes.append(so)
    anclas = {"centro": (0, 0, 1.0)}
    for k in (0, 1):
        anclas[f"boton_{k}"] = tuple(centro_boton(k))
        anclas[f"pelota_{k}"] = tuple(lugar_pelota(k))
        anclas[f"trampa_{k}"] = tuple(trampilla(k))
        anclas[f"plataforma_{k}"] = tuple(local(k, DEPTH / 2, 0, 0))
        anclas[f"borde_{k}"] = tuple(local(k, 0.0, 0, 0))
    return {"anclas": anclas, "animables": {"plataformas": plats, "soportes": soportes, "llamas": llamas},
            "parametros": p, "moviles": {}}


def _papelitos(col, t0: float, fps: int, rnd):
    """Papelitos de colores que caen desde arriba al final (partículas con física simple)."""
    m = K.material("papelito", (1, 1, 1), 0.4)
    nt = m.node_tree
    info = nt.nodes.new("ShaderNodeObjectInfo")
    rampa = nt.nodes.new("ShaderNodeValToRGB")
    els = rampa.color_ramp.elements
    els[0].color = (1.0, 0.15, 0.2, 1)
    els[1].color = (0.15, 0.4, 1.0, 1)
    e = els.new(0.33)
    e.color = (1.0, 0.85, 0.1, 1)
    e = els.new(0.66)
    e.color = (0.95, 0.95, 0.95, 1)
    rampa.color_ramp.interpolation = "CONSTANT"
    nt.links.new(info.outputs["Random"], rampa.inputs["Fac"])
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    nt.links.new(rampa.outputs["Color"], bsdf.inputs["Base Color"])
    papel = K.caja("papelito_modelo", (0, 0, -200), (0.05, 0.035, 0.002), m, col)
    emisor = K.plano("papelitos_emisor", (0, 0, 16), (40, 22), None, col)
    emisor.hide_render = True
    ps = emisor.modifiers.new("papelitos", "PARTICLE_SYSTEM").particle_system.settings
    f0 = int(round(t0 * fps)) + 1
    ps.count = 6000
    ps.frame_start = f0
    ps.frame_end = f0 + 90
    ps.lifetime = 400
    ps.render_type = "OBJECT"
    ps.instance_object = papel
    ps.particle_size = 1.0
    ps.size_random = 0.5
    ps.use_rotations = True
    ps.rotation_mode = "NOR"
    ps.angular_velocity_mode = "RAND"
    ps.angular_velocity_factor = 12.0
    ps.normal_factor = -2.0
    ps.factor_random = 1.5
    ps.effector_weights.gravity = 0.12
    ps.drag_factor = 0.4
    ps.brownian_factor = 0.6


# ------------------------------------------------------------------------------------------------ el duelo
G = 9.81


def _clave_hide(ob, frame, oculto):
    ob.hide_render = ob.hide_viewport = oculto
    ob.keyframe_insert("hide_render", frame=frame)
    ob.keyframe_insert("hide_viewport", frame=frame)


def _constantes(ob):
    if ob.animation_data and ob.animation_data.action:
        for fc in K._fcurves(ob.animation_data.action):
            if fc.data_path.startswith("hide_"):
                for kp in fc.keyframe_points:
                    kp.interpolation = "CONSTANT"


def despues_personajes(info: dict, pjs: dict, ctx, manifiesto: dict, fps: int) -> None:
    """Juega el duelo de la receta (manifiesto["duelo"]): una pelota por turno puesta en el pie del que patea en el cuadro
    de contacto, el tiro con la física de `simular_pelota`, y si el botón rival se aprieta: botón verde y hundido,
    trampilla abierta, el rival cae (su soporte, con gravedad) y después vuelve con el ascensor."""
    from estudio.blender import director as D, pelota as BP
    duelo = manifiesto.get("duelo", {})
    soportes = info["animables"]["soportes"]
    plats = info["animables"]["plataformas"]
    dur_f = int(round(manifiesto.get("escenario", {}).get("parametros", {}).get("duracion_s", 60) * fps)) + 2
    col = K.coleccion("pelotas")
    # soportes: claves de altura (caídas y subidas) y trampillas (ángulo de las bisagras)
    z_claves = {0: [(1, 0.0)], 1: [(1, 0.0)]}
    puerta = {0: [(1, 0.0)], 1: [(1, 0.0)]}
    verde = {0: [], 1: []}
    turnos = duelo.get("turnos", [])
    informe = []
    for n, tu in enumerate(turnos):
        s = int(tu["tirador"])
        rival = 1 - s
        pj = pjs[tu["personaje"]]
        clip = tu["clip"]
        tr = next(t for t in pj["tramos"] if abs((t["f0"] - 1) / fps - tu["patea_s"]) < 0.05)
        golpeo = D._golpeo(clip.split(":")[-1]) or {}
        tc = golpeo.get("tc", 0.35)
        t_contacto = (tr["f0"] - 1) / fps + (tc - float(tu.get("desde_s", 0.0))) / (1.0 / tr["strip"].scale)
        f_contacto = t_contacto * fps + 1
        sc = bpy.context.scene
        sc.frame_set(int(math.floor(f_contacto)), subframe=f_contacto - math.floor(f_contacto))
        arm = pj["armadura"]
        pies = [(arm.matrix_world @ arm.pose.bones[h].head) for h in (pj["info"]["pie_der"], pj["info"]["pie_izq"])]
        reposo = min(pies, key=lambda v: v.z).copy()
        reposo.z = BP.RADIO
        de = tu.get("destino", {})
        destino = centro_boton(rival) + Vector((0, de.get("dy", 0.0), de.get("dz", 0.0)))
        if "punto" in de:
            destino = Vector(de["punto"])
        efecto = tuple(tu.get("efecto", (0, 0, 0)))
        v0 = resolver(reposo, destino, tu.get("velocidad", 22.0), efecto)
        tray, eventos = simular_pelota(reposo, v0, efecto, duracion=6.0)
        ob = BP.crear(f"pelota_{n}", col)
        f_aparece = int(round(tu.get("aparece_s", tu["patea_s"] - 2.0) * fps)) + 1
        f_fin_vis = int(round(tu.get("desaparece_s", t_contacto + 6.0) * fps)) + 1
        BP.animar(ob, tray, int(round(f_contacto)), fps, reposo=reposo)
        for o in [ob] + list(ob.children):
            _clave_hide(o, 1, True)
            _clave_hide(o, f_aparece, False)
            _clave_hide(o, f_fin_vis, True)
            _constantes(o)
        bt = {}
        for i in range(0, len(tray), int(round(240 / fps))):
            t, p_, v_, w_ = tray[i]
            bt[int(round(f_contacto)) + int(round(t * fps))] = (p_.copy(), math.atan2(-v_.x, v_.y) if v_.length > 0.1 else 0.0, v_.length)
        for f in range(1, int(round(f_contacto))):
            bt[f] = (reposo.copy(), 0.0, 0.0)
        ctx.moviles[f"pelota_{n}"] = {"tray": bt, "anclas": {"": (0, 0, 0)}}
        ctx.eventos.append({"tipo": "patada", "t": t_contacto, "pos": list(reposo), "lado": s})
        apreto = None
        for e in eventos:
            ctx.eventos.append({"tipo": e["tipo"], "t": t_contacto + e["t"], "lado": e["lado"], "impacto": e["impacto"]})
            if e["tipo"] == "boton" and apreto is None:
                apreto = e
        cayo = apreto["lado"] if apreto else None
        informe.append({"turno": n, "tirador": s, "contacto_s": round(t_contacto, 2), "v0": round(v0.length, 1),
                        "cayo": cayo, "esperado": tu.get("resultado"),
                        "eventos": [(e["tipo"], round(t_contacto + e["t"], 2), e["impacto"]) for e in eventos[:4]]})
        if cayo is not None:
            t_p = t_contacto + apreto["t"]
            ctx.eventos.append({"tipo": "caida", "t": t_p, "lado": cayo})
            verde[cayo].append(t_p)
            puerta[cayo].append((t_p * fps + 1, 0.0))
            puerta[cayo].append(((t_p + DOOR_OPEN_T) * fps + 1, 1.0))
            # cae con gravedad desde que se abre el piso
            t0 = t_p + 0.1
            z_claves[cayo].append((t0 * fps + 1, 0.0))
            k = 1
            while True:
                tt = k / fps
                z = -0.5 * G * tt * tt
                z_claves[cayo].append((t0 * fps + 1 + k, max(z, -46.0)))
                if z < -46.0:
                    break
                k += 1
        sube = tu.get("sube_s")          # el que cayó en el turno anterior vuelve en el ascensor al empezar este
        if sube is not None:
            lado = int(tu.get("sube_lado", s))
            f0 = sube * fps + 1
            # lo que quedaba de la caída (sigue hasta −46 m) se corta: el ascensor lo trae desde la niebla
            z_claves[lado] = [k for k in z_claves[lado] if k[0] < f0 - 0.5]
            z_claves[lado].append((f0 - 0.5, -46.0))
            z_claves[lado].append((f0, -9.0))
            dur = float(tu.get("sube_dur", 1.6))
            for k in range(1, int(dur * fps) + 1):
                u = k / (dur * fps)
                z_claves[lado].append((f0 + k, -9.0 * (1 - u) ** 3))
            puerta[lado].append((f0 + dur * fps, 1.0))
            puerta[lado].append((f0 + (dur + 0.3) * fps, 0.0))
            ctx.eventos.append({"tipo": "subida", "t": sube, "lado": lado})
    # el disco del ascensor sólo se ve mientras sube (en la caída no acompaña al jugador)
    for k in (0, 1):
        disco = bpy.data.objects.get(f"ascensor_{k}")
        if disco is None:
            continue
        _clave_hide(disco, 1, True)
        for tu in turnos:
            if tu.get("sube_s") is not None and int(tu.get("sube_lado", tu["tirador"])) == k:
                f_a = tu["sube_s"] * fps + 1
                _clave_hide(disco, f_a, False)
                _clave_hide(disco, f_a + (float(tu.get("sube_dur", 1.6)) + 0.35) * fps, True)
        _constantes(disco)
    for k in (0, 1):
        so = soportes[k]
        base = Vector(so.location)
        for fr, z in sorted(z_claves[k]):
            so.location = (base.x, base.y, z)
            so.keyframe_insert("location", index=2, frame=fr)
        so.location = base
        for kk, bis in enumerate(plats[k]["hojas"]):
            sg = -1 if kk == 0 else 1
            for fr, u in sorted(puerta[k]):
                bis.rotation_euler = (sg * u * math.pi / 2, 0, 0)
                bis.keyframe_insert("rotation_euler", index=0, frame=fr)
        # botón: se hunde y se pone verde al apretarlo; vuelve rojo cuando el que cayó ya subió
        boton = plats[k]["boton"]
        m_rojo, m_verde = boton.data.materials[0], bpy.data.materials[boton["verde"]]
        boton_v = boton.copy()
        boton_v.data = boton.data.copy()
        boton_v.data.materials.clear()
        boton_v.data.materials.append(m_verde)
        boton.users_collection[0].objects.link(boton_v)
        hundido = Vector((hacia_rival(k) * -CAP * 0.6, 0, 0))
        boton_v.location = boton.location + hundido
        _clave_hide(boton_v, 1, True)
        _clave_hide(boton, 1, False)
        subidas = sorted(tu.get("sube_s") for tu in turnos if tu.get("sube_s") is not None
                         and int(tu.get("sube_lado", tu["tirador"])) == k)
        for t_p in verde[k]:
            f = int(round(t_p * fps)) + 1
            _clave_hide(boton_v, f, False)
            _clave_hide(boton, f, True)
            t_r = next((t for t in subidas if t > t_p), None)
            if t_r is not None:
                f2 = int(round((t_r + 1.6) * fps)) + 1
                _clave_hide(boton_v, f2, True)
                _clave_hide(boton, f2, False)
        _constantes(boton)
        _constantes(boton_v)
    print("[al_vacio] duelo:")
    for r in informe:
        print("   ", r)
    info["duelo"] = informe
