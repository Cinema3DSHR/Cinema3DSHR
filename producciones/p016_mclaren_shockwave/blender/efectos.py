"""p016 · efectos físicos (simulación por Python con numpy, horneada a claves; sin cachés externos para que el BLEND sea autónomo):
vidrieras que vibran, se fisuran y estallan en cascada cuando llega la onda, hojas, piedras, polvo y las líneas de flujo aerodinámico."""
import math
import random
import bisect
import numpy as np
import bpy
from mathutils import Vector, Quaternion
import lib
from lib import *
import guion
import ciudad

C_ONDA = 110.0           # velocidad de la onda en tiempo de simulación (m/s)


def t_rotura(tcar, y, x):
    """La onda va por delante del coche (18 m) y recorre el lateral hasta la fachada a C_ONDA."""
    return tcar(y + 18.0) + abs(x - guion.X_CARRIL) / C_ONDA

G = 9.8


# ───────────────────────────────────────────── utilidades
def tabla_tiempos(ctx):
    """tcar(y): instante de simulación en que el coche llega a la posición y (monótona decreciente); f_de_t(t): primer cuadro en que el mapa de tiempo alcanza t."""
    ts = np.arange(0.0, 27.0, 0.005)
    ys = np.array([ctx.y_coche_t(float(t)) for t in ts])
    fs = np.arange(0, guion.TOTAL + 1)
    Tf = np.array([ctx.T(int(f)) for f in fs])

    def tcar(y):
        return float(np.interp(-y, -ys, ts))

    def f_de_t(t):
        return float(np.interp(t, Tf, fs))
    return tcar, f_de_t, Tf


def escribir_claves(obj, frames, locs, quats=None, escala=None):
    """Escribe de golpe las claves de posición (y rotación en cuaternión / escala) de un objeto con la API de acciones por capas (rápido, sin keyframe_insert)."""
    from bpy_extras import anim_utils
    ad = obj.animation_data_create()
    act = bpy.data.actions.new("a_" + obj.name)
    slot = act.slots.new("OBJECT", obj.name)
    ad.action = act
    ad.action_slot = slot
    cb = anim_utils.action_ensure_channelbag_for_slot(act, slot)
    n = len(frames)
    fr = np.asarray(frames, dtype=np.float32)

    def curva(path, idx, vals):
        fc = cb.fcurves.new(path, index=idx)
        fc.keyframe_points.add(n)
        co = np.empty(2 * n, dtype=np.float32)
        co[0::2] = fr
        co[1::2] = vals
        fc.keyframe_points.foreach_set("co", co)
        fc.update()
    L = np.asarray(locs, dtype=np.float32)
    for i in range(3):
        curva("location", i, L[:, i])
    if quats is not None:
        obj.rotation_mode = "QUATERNION"
        Q = np.asarray(quats, dtype=np.float32)
        for i in range(4):
            curva("rotation_quaternion", i, Q[:, i])
    if escala is not None:
        S = np.asarray(escala, dtype=np.float32)
        for i in range(3):
            curva("scale", i, S[:, i] if S.ndim == 2 else S)


def q_mul(a, b):
    w1, x1, y1, z1 = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    w2, x2, y2, z2 = b[..., 0], b[..., 1], b[..., 2], b[..., 3]
    return np.stack([w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2, w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2], axis=-1)


def q_from_rv(rv):
    """Cuaternión de una rotación dada como vector eje×ángulo (N,3)."""
    ang = np.linalg.norm(rv, axis=-1, keepdims=True)
    eje = np.where(ang > 1e-9, rv / np.maximum(ang, 1e-9), np.array([1.0, 0, 0]))
    h = ang / 2
    return np.concatenate([np.cos(h), eje * np.sin(h)], axis=-1)


def simular(P0, V0, Q0, W0, t0, t_fin, g, suelo=0.0, rest=0.25, arrastre=0.02, dt=1 / 120.0, muestreo=1 / 30.0, viento=None, k_viento=0.0, rng=None, friccion=0.8):
    """Integra N cuerpos en bloque. `t0` = instante en que cada uno se libera. Devuelve tiempos y matrices de posición (S,N,3) y cuaternión (S,N,4). `viento(t)` → (N,3) velocidad de aire hacia la que tiende cada cuerpo con coeficiente k_viento."""
    N = len(P0)
    P, V, Q, W = P0.astype(np.float64).copy(), V0.astype(np.float64).copy(), Q0.astype(np.float64).copy(), W0.astype(np.float64).copy()
    reposo = np.zeros(N, dtype=bool)
    t = 0.0
    prox = 0.0
    ts, Ps, Qs = [], [], []
    while t <= t_fin + 1e-9:
        if t >= prox - 1e-9:
            ts.append(t)
            Ps.append(P.astype(np.float32).copy())
            Qs.append(Q.astype(np.float32).copy())
            prox += muestreo
        act = (t >= t0) & (~reposo)
        if act.any():
            if viento is not None and k_viento > 0:
                wv = viento(t)
                V[act] += (wv[act] - V[act]) * k_viento * dt
            V[act, 2] -= g * dt
            V[act] *= (1.0 - arrastre * dt)
            P[act] += V[act] * dt
            rv = W[act] * dt
            Q[act] = q_mul(q_from_rv(rv), Q[act])
            Q[act] /= np.linalg.norm(Q[act], axis=-1, keepdims=True)
            bajo = act & (P[:, 2] < suelo) & (V[:, 2] < 0)
            if bajo.any():
                P[bajo, 2] = suelo
                V[bajo, 2] = -V[bajo, 2] * rest
                V[bajo, 0] *= friccion
                V[bajo, 1] *= friccion
                W[bajo] *= 0.6
                quieto = bajo & (np.abs(V[:, 2]) < 0.5) & (np.linalg.norm(V[:, :2], axis=1) < 0.5)
                reposo |= quieto
                V[quieto] = 0
                W[quieto] = 0
        t += dt
    return np.array(ts), np.stack(Ps), np.stack(Qs)


def hornear(objs, ts, Ps, Qs, t0, ctx, f_de_t, paso=4, escala=None, margen_pre=1):
    """Convierte la trayectoria simulada en claves por cuadro: cada objeto sólo tiene claves desde que se libera hasta que queda quieto o termina la película;
    antes de eso permanece en su sitio con una única clave."""
    Tf = ctx.Tf
    nF = guion.TOTAL
    # cuadro → muestra de simulación
    for i, o in enumerate(objs):
        f_ini = int(max(0, math.floor(f_de_t(float(t0[i])) - margen_pre)))
        if f_ini >= nF - 1:
            escribir_claves(o, [0], [Ps[0, i]], [Qs[0, i]])
            continue
        # cuadros con paso, fin cuando se detiene (variación < 1 mm entre muestras) o termina el video
        mov = np.linalg.norm(np.diff(Ps[:, i], axis=0), axis=1) > 5e-4
        if mov.any():
            ult = np.nonzero(mov)[0].max() + 1
            f_fin = int(min(nF - 1, math.ceil(f_de_t(float(ts[min(ult, len(ts) - 1)])) + 1)))
        else:
            f_fin = f_ini
        fr = list(range(f_ini, max(f_ini + 1, f_fin) + 1, paso))
        if fr[-1] != f_fin:
            fr.append(f_fin)
        if f_ini > 0:
            fr = [0] + fr
        sim_idx = np.clip(np.interp([Tf[min(f, nF)] for f in fr], ts, np.arange(len(ts))), 0, len(ts) - 1)
        i0 = np.floor(sim_idx).astype(int)
        i1 = np.minimum(i0 + 1, len(ts) - 1)
        u = (sim_idx - i0)[:, None]
        pos = Ps[i0, i] * (1 - u) + Ps[i1, i] * u
        q = Qs[i0, i] * (1 - u) + Qs[i1, i] * u
        q /= np.linalg.norm(q, axis=1, keepdims=True)
        escribir_claves(o, fr, pos, q)


# ───────────────────────────────────────────── vidrieras
def mat_vidriera():
    """Vidrio de las vidrieras: intacto = casi transparente; roto (alfa del color del objeto = 1) = fragmentos translúcidos blanco-azulados con borde brillante."""
    m = bpy.data.materials.new("vidriera_rompible")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    oi = nt.nodes.new("ShaderNodeObjectInfo")
    M = lambda op, a=None, c=None: lib._mm(nt, op, a, c)
    rota = oi.outputs["Alpha"]
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    dif = nt.nodes.new("ShaderNodeBsdfDiffuse")
    dif.inputs["Color"].default_value = (0.22, 0.32, 0.46, 1)
    gl = nt.nodes.new("ShaderNodeBsdfGlossy")
    gl.inputs["Color"].default_value = (0.9, 0.95, 1.0, 1)
    gl.inputs["Roughness"].default_value = 0.08
    fr = nt.nodes.new("ShaderNodeFresnel")
    fr.inputs["IOR"].default_value = 1.45
    mg = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(M("ADD", fr.outputs[0], 0.12), mg.inputs["Fac"])
    nt.links.new(dif.outputs[0], mg.inputs[1])
    nt.links.new(gl.outputs[0], mg.inputs[2])
    mz = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(M("ADD", 0.1, M("MULTIPLY", rota, 0.72)), mz.inputs["Fac"])
    nt.links.new(tr.outputs[0], mz.inputs[1])
    nt.links.new(mg.outputs[0], mz.inputs[2])
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.35
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (0.75, 0.88, 1.0, 1)
    nt.links.new(M("MULTIPLY", M("MULTIPLY", lw.outputs["Facing"], rota), 4.5), em.inputs["Strength"])
    ad = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(mz.outputs[0], ad.inputs[0])
    nt.links.new(em.outputs[0], ad.inputs[1])
    nt.links.new(ad.outputs[0], out.inputs["Surface"])
    return m


def claves_color_constante(o, f_rotura):
    """alfa del color del objeto: 0 hasta la rotura, 1 después (interpolación constante sólo en esa curva)."""
    o.color = (1, 1, 1, 0.0)
    o.keyframe_insert("color", frame=0)
    o.color = (1, 1, 1, 1.0)
    o.keyframe_insert("color", frame=int(max(1, f_rotura)))
    from bpy_extras import anim_utils
    ad = o.animation_data
    cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
    for fc in cb.fcurves:
        if fc.data_path == "color":
            for kp in fc.keyframe_points:
                kp.interpolation = "CONSTANT"


def panel_fragmentos(col, nombre, centro, sx, ancho, alto, nx, nz, r, mat):
    """Panel de vidrio hecho de nx×nz fragmentos irregulares (cuadrícula con vértices desplazados). Devuelve los objetos."""
    xs = [-ancho / 2 + ancho * i / nx for i in range(nx + 1)]
    zs = [-alto / 2 + alto * j / nz for j in range(nz + 1)]
    pts = [[(xs[i] + (r.uniform(-0.25, 0.25) * ancho / nx if 0 < i < nx else 0), zs[j] + (r.uniform(-0.25, 0.25) * alto / nz if 0 < j < nz else 0)) for j in range(nz + 1)] for i in range(nx + 1)]
    objs = []
    for i in range(nx):
        for j in range(nz):
            q = [pts[i][j], pts[i + 1][j], pts[i + 1][j + 1], pts[i][j + 1]]
            cx = sum(p[0] for p in q) / 4
            cz = sum(p[1] for p in q) / 4
            e = 0.012
            verts = []
            for p in q:
                verts.append((0, p[0] - cx, p[1] - cz))
            for p in q:
                verts.append((e, p[0] - cx, p[1] - cz))
            caras = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
            me = bpy.data.meshes.new(f"{nombre}_{i}{j}")
            me.from_pydata(verts, [], caras)
            me.update()
            me.materials.append(mat)
            o = bpy.data.objects.new(f"{nombre}_{i}{j}", me)
            col.objects.link(o)
            # el panel está en el plano YZ: ancho a lo largo de Y
            o.location = Vector((centro[0], centro[1] + cx, centro[2] + cz))
            o.rotation_mode = "QUATERNION"
            objs.append(o)
    return objs


def vidrieras(ctx, col, tcar, f_de_t):
    r = random.Random(77)
    np_r = np.random.default_rng(77)
    vid = mat_vidriera()
    obj, P0, V0, W0, T0 = [], [], [], [], []
    ancho, alto = 4.5, ciudad.H_PLANTA - 0.4
    y = ciudad.HERO_Y0 + ancho / 2
    n_panel = 0
    while y < ciudad.HERO_Y1:
        for sx in (-1, 1):
            xc = sx * ciudad.X_VIDRIO
            centro = (xc, y, 0.2 + alto / 2)
            frs = panel_fragmentos(col, f"vid_{n_panel}", centro, sx, ancho, alto, 2, 5, r, vid)
            # instante de rotura: el coche pasa por la altura del panel y la onda recorre el lateral hasta la fachada
            tb = t_rotura(tcar, y, xc) + r.uniform(0.0, 0.10)
            for o in frs:
                p = np.array(o.location)
                lateral = -sx
                v = np.array([lateral * r.uniform(2.0, 11.0), r.uniform(-2.0, 7.0), r.uniform(-0.5, 6.0) + 0.5 * (p[2] - 4.0) * 0.3])
                # los fragmentos del centro del panel salen con más fuerza que los de los bordes
                v *= 0.6 + 0.9 * math.exp(-((p[1] - y) / 2.0) ** 2)
                obj.append(o)
                P0.append(p)
                V0.append(v)
                W0.append([r.gauss(0, 3.0), r.gauss(0, 3.0), r.gauss(0, 3.0)])
                T0.append(tb + r.uniform(0.0, 0.08))
            n_panel += 1
        y += ancho
    P0, V0, W0, T0 = np.array(P0), np.array(V0), np.array(W0), np.array(T0)
    Q0 = np.tile(np.array([1.0, 0, 0, 0]), (len(P0), 1))
    ctx.n_paneles = n_panel
    # un evento sonoro por panel: (cuadro de rotura, x, y)
    ctx.roturas_audio = []
    for i in range(0, len(T0), 10):
        ctx.roturas_audio.append([float(f_de_t(float(T0[i]))), float(P0[i][0]), float(P0[i][1])])
    ts, Ps, Qs = simular(P0, V0, Q0, W0, T0, 26.0, G, suelo=0.12, rest=0.28, arrastre=0.05, muestreo=1 / 30.0)
    # vibración previa: pequeños giros en los 0,3 s anteriores a la rotura (el panel «tiembla» y se fisura)
    hornear(obj, ts, Ps, Qs, T0, ctx, f_de_t, paso=5)
    for o, t0 in zip(obj, T0):
        claves_color_constante(o, int(f_de_t(float(t0))))
    return obj, P0, T0


# ───────────────────────────────────────────── hojas, piedras y polvo
def hojas(ctx, col, tcar, f_de_t):
    r = np.random.default_rng(5)
    rp = random.Random(5)
    m1 = mat("hoja_verde", (0.08, 0.3, 0.04), rug=0.5)
    m2 = mat("hoja_seca", (0.45, 0.32, 0.05), rug=0.5)
    # hoja = rombo ligeramente curvo con nervio
    verts = [(0, -0.07, 0), (0.035, 0, 0.004), (0, 0.07, 0), (-0.035, 0, 0.004)]
    me = bpy.data.meshes.new("hoja_malla")
    me.from_pydata(verts, [], [(0, 1, 2, 3)])
    me.update()
    objs, P0, V0, W0, T0 = [], [], [], [], []
    ya = [a for a in ctx.arboles if ciudad.HERO_Y0 + 20 < a["pos"].y < ciudad.HERO_Y1 - 5]
    for a in ya:
        tb = t_rotura(tcar, a["pos"].y, a["pos"].x) + 0.05
        for k in range(9):
            o = bpy.data.objects.new(f"hoja_{len(objs)}", me.copy() if False else me)
            col.objects.link(o)
            o.data.materials.clear() if False else None
            o.active_material = m1 if rp.random() < 0.7 else m2
            s_ = rp.uniform(1.8, 3.2)
            o.scale = (s_, s_, s_)
            o.rotation_mode = "QUATERNION"
            c = a["pos"] + Vector((rp.uniform(-1.6, 1.6), rp.uniform(-1.6, 1.6), rp.uniform(4.2, 6.4)))
            objs.append(o)
            P0.append(np.array(c))
            sx = a["sx"]
            V0.append(np.array([-sx * rp.uniform(3, 11), rp.uniform(0, 8), rp.uniform(0, 5)]))
            W0.append(np.array([rp.gauss(0, 4), rp.gauss(0, 4), rp.gauss(0, 4)]))
            T0.append(tb + rp.uniform(0, 0.25))
    P0, V0, W0, T0 = np.array(P0), np.array(V0), np.array(W0), np.array(T0)
    Q0 = np.tile(np.array([1.0, 0, 0, 0]), (len(P0), 1))
    ph = r.uniform(0, 6.28, size=(len(P0), 3))

    def viento(t):
        # ráfaga que decae después de la onda + remolino suave
        dtb = np.maximum(t - T0, 0)
        base = np.stack([np.zeros(len(P0)), 3.0 * np.exp(-dtb / 1.4), 0.4 * np.sin(2.3 * t + ph[:, 0])], axis=1)
        remol = np.stack([1.5 * np.sin(1.7 * t + ph[:, 1]), 1.2 * np.sin(1.1 * t + ph[:, 2]), 0.8 * np.sin(2.9 * t + ph[:, 0]) - 1.0], axis=1)
        return base + remol
    ts, Ps, Qs = simular(P0, V0, Q0, W0, T0, 26.0, 0.6, suelo=0.05, rest=0.05, arrastre=0.2, muestreo=1 / 30.0, viento=viento, k_viento=1.6)
    hornear(objs, ts, Ps, Qs, T0, ctx, f_de_t, paso=6)
    # los árboles se sacuden: oscilación de las copas tras la onda
    for a in ya:
        tb = t_rotura(tcar, a["pos"].y, a["pos"].x)
        for o in a["copa"]:
            base = o.location.copy()
            frs = list(range(int(f_de_t(tb)), min(guion.TOTAL - 1, int(f_de_t(tb)) + 500), 6))
            if not frs:
                continue
            fr0 = [0] + frs
            L = [np.array(base)]
            for f in frs:
                tt_ = ctx.Tf[f] - tb
                am = 0.6 * math.exp(-tt_ / 1.2) * math.sin(tt_ * 11.0)
                L.append(np.array(base) + np.array([-a["sx"] * am, 0.4 * am, 0.0]))
            escribir_claves(o, fr0, L)
    return objs


def piedras(ctx, col, tcar, f_de_t):
    """Piedras y esquirlas de asfalto que las ruedas lanzan hacia atrás desde el paso del coche (tiempo de simulación 17,7–21 s)."""
    rp = random.Random(9)
    mp = mat("piedra", (0.1, 0.095, 0.09), rug=0.8)
    ma = mat("asfalto_trozo", (0.025, 0.025, 0.027), rug=0.7)
    objs, P0, V0, W0, T0 = [], [], [], [], []
    for k in range(360):
        ts_ = rp.uniform(17.4, 21.6)
        tsp = ctx.y_coche_t(ts_)
        lado = rp.choice((-0.86, 0.86))
        tam = rp.uniform(0.018, 0.07) if rp.random() < 0.7 else rp.uniform(0.07, 0.16)
        o = caja(f"piedra_{k}", (0, 0, 0), (tam, tam * rp.uniform(0.6, 1.3), tam * rp.uniform(0.5, 1.0)), col, mp if rp.random() < 0.6 else ma)
        o.rotation_mode = "QUATERNION"
        objs.append(o)
        P0.append(np.array([guion.X_CARRIL + lado, tsp + rp.uniform(0.8, 1.9), 0.08]))
        V0.append(np.array([rp.gauss(0, 2.0), rp.uniform(4, 20), rp.uniform(2, 9)]))
        W0.append(np.array([rp.gauss(0, 12), rp.gauss(0, 12), rp.gauss(0, 12)]))
        T0.append(ts_)
    P0, V0, W0, T0 = np.array(P0), np.array(V0), np.array(W0), np.array(T0)
    Q0 = np.tile(np.array([1.0, 0, 0, 0]), (len(P0), 1))
    ts, Ps, Qs = simular(P0, V0, Q0, W0, T0, 26.0, G, suelo=0.02, rest=0.4, arrastre=0.05, muestreo=1 / 30.0)
    hornear(objs, ts, Ps, Qs, T0, ctx, f_de_t, paso=4)
    return objs


def mat_polvo():
    m = bpy.data.materials.new("polvo")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    ru = nt.nodes.new("ShaderNodeTexNoise")
    ru.inputs["Scale"].default_value = 2.2
    ru.inputs["Detail"].default_value = 5.0
    nt.links.new(tc.outputs["Object"], ru.inputs["Vector"])
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.4
    inv = lib._mm(nt, "SUBTRACT", 1.0, lw.outputs["Facing"])
    oi = nt.nodes.new("ShaderNodeObjectInfo")
    alfa = lib._mm(nt, "MULTIPLY", lib._mm(nt, "MULTIPLY", inv, lib._mm(nt, "MULTIPLY", ru.outputs["Fac"], 1.7)), lib._mm(nt, "MULTIPLY", oi.outputs["Color"], 0.0)) if False else None
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(oi.outputs["Color"], sep.inputs[0])
    a = lib._mm(nt, "MULTIPLY", lib._mm(nt, "MULTIPLY", inv, lib._mm(nt, "MULTIPLY", ru.outputs["Fac"], 1.6)), oi.outputs["Alpha"])
    dif = nt.nodes.new("ShaderNodeBsdfDiffuse")
    nt.links.new(oi.outputs["Color"], dif.inputs["Color"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mz = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(a, mz.inputs["Fac"])
    nt.links.new(tr.outputs[0], mz.inputs[1])
    nt.links.new(dif.outputs[0], mz.inputs[2])
    nt.links.new(mz.outputs[0], out.inputs["Surface"])
    return m


def polvo(ctx, col, tcar, f_de_t, ctx_vid):
    """Nubes de polvo y humo (superficies con ruido, baratas): a lo largo de las fachadas cuando estallan los vidrios, en el rastro del coche y en el anillo de la onda."""
    rp = random.Random(21)
    m = mat_polvo()
    puffs = []
    base = esfera("polvo_base", (0, 0, -999), 1.0, col, m, 12, 8)
    base.hide_render = True

    def puff(nombre, pos, r0, r1, t_ini, vida, vel, color, alfa):
        o = bpy.data.objects.new(nombre, base.data)
        col.objects.link(o)
        f0 = int(f_de_t(t_ini))
        f1 = int(min(guion.TOTAL - 1, f_de_t(t_ini + vida)))
        if f0 >= guion.TOTAL - 2:
            bpy.data.objects.remove(o)
            return
        fr = list(range(f0, max(f0 + 1, f1) + 1, 6))
        locs, escs, cols = [], [], []
        for f in fr:
            u = max(0.0, min(1.0, (ctx.Tf[f] - t_ini) / vida))
            s_ = r0 + (r1 - r0) * (1 - (1 - u) ** 2)
            locs.append(np.array(pos) + np.array(vel) * (ctx.Tf[f] - t_ini))
            escs.append((s_, s_, s_ * 0.7))
            a = alfa * min(1.0, u * 6) * (1 - u) ** 1.3
            cols.append((color[0], color[1], color[2], a))
        # clave previa invisible
        o.color = (*color, 0.0)
        escribir_claves(o, fr, locs, None, escala=np.array(escs))
        for f, c in zip(fr, cols):
            o.color = c
            o.keyframe_insert("color", frame=f)
        puffs.append(o)
    # a lo largo de las fachadas: un velo de polvo por cada ~14 m de vidriera que estalla
    for y in np.arange(ciudad.HERO_Y0 + 5, ciudad.HERO_Y1, 11.0):
        for sx in (-1, 1):
            tb = t_rotura(tcar, y, sx * ciudad.X_VIDRIO) + 0.1
            puff(f"polvo_f_{int(y)}_{sx}", (sx * (ciudad.X_VIDRIO - 1.5), y, 2.0), 2.0, 8.5, tb, 5.0, (-sx * 1.5, 1.8, 0.5), (0.45, 0.4, 0.34), 0.85)
            if rp.random() < 0.5:
                puff(f"humo_f_{int(y)}_{sx}", (sx * (ciudad.X_VIDRIO - 1.0), y + rp.uniform(-3, 3), 4.0), 1.5, 7.0, tb + 0.1, 6.0, (-sx * 1.0, 1.2, 1.1), (0.12, 0.11, 0.1), 0.7)
    # rastro del coche: polvo levantado detrás de las ruedas y la turbulencia
    for t_ in np.arange(17.3, 24.6, 0.12):
        y_ = ctx.y_coche_t(float(t_))
        puff(f"polvo_r_{t_:.2f}", (guion.X_CARRIL + rp.uniform(-1.0, 1.0), y_ + 2.5, 0.5), 0.7, 3.8, float(t_), 3.5, (rp.uniform(-1, 1), 2.5, 0.8), (0.42, 0.38, 0.32), 0.65)
    return puffs


# ───────────────────────────────────────────── aerodinámica
def flujo(ctx, col):
    """Líneas de corriente del aire alrededor del McLaren (flujo potencial de un cuerpo elipsoidal), como hilos finos con trazos que viajan: parte de lo que ve el espectador del viento."""
    raiz = ctx.coche["raiz"]
    m = bpy.data.materials.new("flujo_aire")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["UV"], sep.inputs[0])
    fase = nt.nodes.new("ShaderNodeValue")
    fase.label = "fase"
    M = lambda op, a=None, c=None: lib._mm(nt, op, a, c)
    traz = M("FRACT", M("SUBTRACT", M("MULTIPLY", sep.outputs["X"], 14.0), fase.outputs[0]))
    pulso = M("MULTIPLY", M("LESS_THAN", traz, 0.35), M("SUBTRACT", 1.0, M("MULTIPLY", M("ABSOLUTE", M("SUBTRACT", M("MULTIPLY", sep.outputs["X"], 2.0), 1.0)), 0.9)))
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (0.75, 0.88, 1.0, 1)
    nivel = nt.nodes.new("ShaderNodeValue")
    nivel.label = "nivel"
    nt.links.new(M("MULTIPLY", M("MULTIPLY", pulso, nivel.outputs[0]), 0.9), em.inputs["Strength"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mz = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(M("MULTIPLY", M("MULTIPLY", pulso, nivel.outputs[0]), 0.55), mz.inputs["Fac"])
    nt.links.new(tr.outputs[0], mz.inputs[1])
    nt.links.new(em.outputs[0], mz.inputs[2])
    nt.links.new(mz.outputs[0], out.inputs["Surface"])
    # animación: fase (trazos que corren por el hilo) y nivel (aparece en la toma aerodinámica y se desvanece)
    for f in range(1260, 1560, 6):
        fase.outputs[0].default_value = ((f - 1260) / 30.0) * 1.6
        fase.outputs[0].keyframe_insert("default_value", frame=f)
    for f, v in ((1260, 0.0), (1300, 0.0), (1335, 1.0), (1440, 1.0), (1500, 0.0), (1799, 0.0)):
        nivel.outputs[0].default_value = v
        nivel.outputs[0].keyframe_insert("default_value", frame=f)
    lib._interp_id(m.node_tree, "LINEAR")
    a, b, c = 1.05, 2.45, 0.62        # semiejes aproximados del cuerpo (ancho, largo, alto); centro local z=−0,03
    rp = random.Random(3)
    nl = 0
    for sx in np.linspace(-1.7, 1.7, 7):
        for sz in (-0.5, -0.2, 0.2, 0.55, 0.95):
            # el hilo parte lejos por delante (y=−9) y se integra con la velocidad del flujo potencial alrededor de una esfera de radio 1 en coordenadas normalizadas
            p = np.array([sx / a, -9.0 / b, (sz + 0.03) / c])
            pts = []
            for i in range(330):
                r2 = float(p @ p)
                rr = math.sqrt(r2)
                if rr < 1.04:
                    p = p / rr * 1.04
                    r2 = float(p @ p)
                    rr = 1.04
                nrm = p / rr
                u = np.array([0.0, 1.0, 0.0])
                vel = u + (1.0 / (2 * rr ** 3)) * (3 * (u @ nrm) * nrm - u)
                p = p + vel * 0.055
                q_ = np.array([p[0] * a, p[1] * b, p[2] * c - 0.03])
                # estela turbulenta detrás del coche: ondulaciones crecientes
                if q_[1] > 2.4:
                    k = (q_[1] - 2.4)
                    q_[0] += 0.09 * k * math.sin(k * 3.1 + sx * 5 + sz * 3)
                    q_[2] += 0.09 * k * math.cos(k * 2.7 + sz * 4 + sx)
                pts.append(q_)
                if q_[1] > 11.5:
                    break
            if len(pts) < 20:
                continue
            tub = _tubo(f"flujo_{nl}", pts, 0.007, col, m)
            tub.parent = raiz
            tub.location = (0, 0, 0)
            nl += 1
    return nl


def _tubo(nombre, pts, radio, col, mat):
    seg = 5
    verts, caras = [], []
    n = len(pts)
    for j, p in enumerate(pts):
        t = Vector(pts[min(j + 1, n - 1)]) - Vector(pts[max(j - 1, 0)])
        t.normalize()
        a_ = t.cross(Vector((0, 0, 1)))
        if a_.length < 1e-4:
            a_ = t.cross(Vector((1, 0, 0)))
        a_.normalize()
        b_ = t.cross(a_)
        for s in range(seg):
            ang = 2 * math.pi * s / seg
            verts.append(Vector(p) + (a_ * math.cos(ang) + b_ * math.sin(ang)) * radio)
    for j in range(n - 1):
        for s in range(seg):
            caras.append((j * seg + s, j * seg + (s + 1) % seg, (j + 1) * seg + (s + 1) % seg, (j + 1) * seg + s))
    me = bpy.data.meshes.new(nombre)
    me.from_pydata([tuple(v) for v in verts], [], caras)
    me.update()
    uv = me.uv_layers.new(name="UVMap")
    for pi, p in enumerate(me.polygons):
        for li in p.loop_indices:
            vi = me.loops[li].vertex_index
            uv.data[li].uv = ((vi // seg) / max(1, n - 1), (vi % seg) / seg)
    me.materials.append(mat)
    o = bpy.data.objects.new(nombre, me)
    col.objects.link(o)
    o.visible_shadow = False
    return o


# ───────────────────────────────────────────── onda de choque
def onda(ctx, col, tcar, f_de_t):
    """Cáscara refractiva que se expande desde el punto de paso (y≈0) a 60 m/s de simulación y se apaga al salir de cuadro."""
    t0 = tcar(0.0)
    C0 = Vector((guion.X_CARRIL, 0.0, 1.2))
    o = onda_choque("onda_paso", C0, 140.0, col, lambda f: max(0.0, ctx.Tf[min(int(f), guion.TOTAL)] - t0) , 520, 760, vel=C_ONDA, color=(1.0, 0.85, 0.6))
    o.visible_shadow = False
    for f_, s_ in ((761, 0.001), (1799, 0.001)):
        o.scale = (s_, s_, s_)
        o.keyframe_insert("scale", frame=f_)
    return o


def construir(ctx):
    col = coleccion("Efectos")
    ctx.Tf = np.array([ctx.T(f) for f in range(guion.TOTAL + 2)])
    tcar, f_de_t, Tf = tabla_tiempos(ctx)
    ctx.tcar = tcar
    ctx.f_de_t = f_de_t
    vidr, P0, T0 = vidrieras(ctx, col, tcar, f_de_t)
    print("EFECTOS vidrios", len(vidr), "paneles", ctx.n_paneles, flush=True)
    h = hojas(ctx, col, tcar, f_de_t)
    print("EFECTOS hojas", len(h), flush=True)
    p = piedras(ctx, col, tcar, f_de_t)
    print("EFECTOS piedras", len(p), flush=True)
    d = polvo(ctx, col, tcar, f_de_t, vidr)
    print("EFECTOS polvo", len(d), flush=True)
    n = flujo(ctx, col)
    print("EFECTOS lineas de flujo", n, flush=True)
    onda(ctx, col, tcar, f_de_t)
    # las ventanas de las torres se rompen siguiendo el frente de la onda (y_frente del material de fachada)
    yf = ctx.yf_socket
    for f in range(0, guion.TOTAL, 6):
        yf.default_value = ctx.y_coche(f) + 12.0 if f >= 534 else 99999.0
        yf.keyframe_insert("default_value", frame=f)
    lib._interp_id(yf.id_data, "CONSTANT")
