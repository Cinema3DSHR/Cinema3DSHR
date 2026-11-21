"""p015 «FRACTURA» · biblioteca común del cortometraje: materiales PBR, geometría procedural, mapa de tiempo (cámara lenta, congelado y retroceso),
física balística de fragmentos con trayectoria propia, volúmenes de fuego y humo, ondas de choque, cámaras con recorridos y la composición final.
Todo es código: el BLEND se reconstruye igual. Blender 5.x."""
import math
import random
import bpy
import bmesh
from mathutils import Vector, Quaternion, Euler, Matrix

FPS = 30
RNG = random.Random(2026)


# ───────────────────────────────────────────── colecciones y objetos
def coleccion(nombre, padre=None):
    c = bpy.data.collections.get(nombre)
    if c is None:
        c = bpy.data.collections.new(nombre)
        (padre or bpy.context.scene.collection).children.link(c)
    return c


def enlazar(o, col):
    for c in list(o.users_collection):
        c.objects.unlink(o)
    col.objects.link(o)
    return o


def malla(nombre, verts, caras, col, mat=None, suave=False):
    me = bpy.data.meshes.new(nombre)
    me.from_pydata(verts, [], caras)
    me.update()
    o = bpy.data.objects.new(nombre, me)
    col.objects.link(o)
    if mat is not None:
        me.materials.append(mat)
    if suave:
        for p in me.polygons:
            p.use_smooth = True
    return o


def _bm_obj(nombre, bm, col, mat, loc, rot, suave=False):
    me = bpy.data.meshes.new(nombre)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(nombre, me)
    col.objects.link(o)
    o.location = loc
    o.rotation_euler = rot
    if mat is not None:
        me.materials.append(mat)
    if suave:
        for p in me.polygons:
            p.use_smooth = True
    return o


def caja(nombre, centro, tam, col, mat, rot=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= tam[0]
        v.co.y *= tam[1]
        v.co.z *= tam[2]
    return _bm_obj(nombre, bm, col, mat, centro, rot)


def cilindro(nombre, centro, radio, alto, col, mat, rot=(0, 0, 0), seg=24, suave=True):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=radio, radius2=radio, depth=alto)
    return _bm_obj(nombre, bm, col, mat, centro, rot, suave)


def esfera(nombre, centro, radio, col, mat, seg=32, anillos=20, esc=(1, 1, 1)):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=anillos, radius=radio)
    for v in bm.verts:
        v.co.x *= esc[0]
        v.co.y *= esc[1]
        v.co.z *= esc[2]
    return _bm_obj(nombre, bm, col, mat, centro, (0, 0, 0), True)


def toro(nombre, centro, R, r, col, mat, rot=(0, 0, 0), seg=64, seg_r=12):
    verts, caras = [], []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        for j in range(seg_r):
            b = 2 * math.pi * j / seg_r
            verts.append(((R + r * math.cos(b)) * math.cos(a), (R + r * math.cos(b)) * math.sin(a), r * math.sin(b)))
    for i in range(seg):
        for j in range(seg_r):
            caras.append((i * seg_r + j, i * seg_r + (j + 1) % seg_r, ((i + 1) % seg) * seg_r + (j + 1) % seg_r, ((i + 1) % seg) * seg_r + j))
    o = malla(nombre, verts, caras, col, mat, True)
    o.location = centro
    o.rotation_euler = rot
    return o


def plano(nombre, centro, w, h, col, mat, rot=(0, 0, 0)):
    return caja(nombre, centro, (w, h, 0.01), col, mat, rot)


def esquirla(nombre, tam, semilla, col, mat):
    """Fragmento irregular (prisma de base poligonal deformada): cada uno distinto."""
    r = random.Random(semilla)
    n = r.randint(4, 6)
    base = []
    for i in range(n):
        a = 2 * math.pi * i / n + r.uniform(-0.3, 0.3)
        k = r.uniform(0.45, 1.0)
        base.append((math.cos(a) * k * tam[0], math.sin(a) * k * tam[1]))
    h0, h1 = tam[2] * r.uniform(0.3, 0.5), tam[2] * r.uniform(0.3, 0.5)
    verts = [(x, y, -h0) for x, y in base] + [(x * r.uniform(0.6, 1.0), y * r.uniform(0.6, 1.0), h1) for x, y in base]
    caras = [tuple(range(n))[::-1], tuple(range(n, 2 * n))]
    for i in range(n):
        caras.append((i, (i + 1) % n, n + (i + 1) % n, n + i))
    return malla(nombre, verts, caras, col, mat)


# ───────────────────────────────────────────── materiales
def _principled(m):
    return next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")


def mat(nombre, color, metal=0.0, rug=0.5, emis=None, fuerza=0.0, coat=0.0, alfa=1.0, ior=None, trans=0.0):
    m = bpy.data.materials.get(nombre)
    if m is not None:
        return m
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    b = _principled(m)
    b.inputs["Base Color"].default_value = (*color, 1.0)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rug
    if coat:
        b.inputs["Coat Weight"].default_value = coat
        b.inputs["Coat Roughness"].default_value = 0.05
    if emis is not None:
        b.inputs["Emission Color"].default_value = (*emis, 1.0)
        b.inputs["Emission Strength"].default_value = fuerza
    if trans:
        b.inputs["Transmission Weight"].default_value = trans
    if ior:
        b.inputs["IOR"].default_value = ior
    b.inputs["Alpha"].default_value = alfa
    return m


def mat_emisivo(nombre, color, fuerza):
    m = bpy.data.materials.get(nombre)
    if m is not None:
        return m
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*color, 1.0)
    e.inputs["Strength"].default_value = fuerza
    nt.links.new(e.outputs[0], out.inputs["Surface"])
    return m


def mat_vidrio(nombre, color=(0.8, 0.9, 1.0), rug=0.02, ior=1.45, sombra_transparente=True):
    m = bpy.data.materials.get(nombre)
    if m is not None:
        return m
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    g = nt.nodes.new("ShaderNodeBsdfGlass")
    g.inputs["Color"].default_value = (*color, 1.0)
    g.inputs["Roughness"].default_value = rug
    g.inputs["IOR"].default_value = ior
    if sombra_transparente:
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        lp = nt.nodes.new("ShaderNodeLightPath")
        mz = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(lp.outputs["Is Shadow Ray"], mz.inputs["Fac"])
        nt.links.new(g.outputs[0], mz.inputs[1])
        nt.links.new(tr.outputs[0], mz.inputs[2])
        nt.links.new(mz.outputs[0], out.inputs["Surface"])
    else:
        nt.links.new(g.outputs[0], out.inputs["Surface"])
    return m


def mat_vidrio_rapido(nombre, tinte=(0.8, 0.92, 1.0)):
    """Vidrio barato: sin refracción (no gasta rebotes de transmisión): mezcla de transparencia y reflejo brillante con Fresnel."""
    m = bpy.data.materials.get(nombre)
    if m is not None:
        return m
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    gl = nt.nodes.new("ShaderNodeBsdfGlossy")
    gl.inputs["Color"].default_value = (*tinte, 1.0)
    gl.inputs["Roughness"].default_value = 0.03
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    tr.inputs["Color"].default_value = (*tinte, 1.0)
    fr = nt.nodes.new("ShaderNodeFresnel")
    fr.inputs["IOR"].default_value = 1.45
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(fr.outputs[0], mx.inputs["Fac"])
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(gl.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    return m


def mat_espejo(nombre, tinte=(0.9, 0.95, 1.0)):
    return mat(nombre, tinte, metal=1.0, rug=0.01)


def mat_ruido(nombre, base, alto, escala=6.0, metal=0.0, rug=0.6, bump=0.4):
    """Material con variación de ruido (desgaste, manchas) entre dos colores."""
    m = bpy.data.materials.get(nombre)
    if m is not None:
        return m
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    nt = m.node_tree
    b = _principled(m)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    r = nt.nodes.new("ShaderNodeTexNoise")
    r.inputs["Scale"].default_value = escala
    r.inputs["Detail"].default_value = 8.0
    nt.links.new(tc.outputs["Object"], r.inputs["Vector"])
    rp = nt.nodes.new("ShaderNodeValToRGB")
    rp.color_ramp.elements[0].color = (*base, 1.0)
    rp.color_ramp.elements[1].color = (*alto, 1.0)
    nt.links.new(r.outputs["Fac"], rp.inputs["Fac"])
    nt.links.new(rp.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rug
    bu = nt.nodes.new("ShaderNodeBump")
    bu.inputs["Strength"].default_value = bump
    nt.links.new(r.outputs["Fac"], bu.inputs["Height"])
    nt.links.new(bu.outputs["Normal"], b.inputs["Normal"])
    return m


# ───────────────────────────────────────────── mapa de tiempo: cámara lenta, congelado y retroceso
class Tiempo:
    """Convierte el cuadro local (0…N) en tiempo de simulación (s). `claves` = [(cuadro, t_sim)]; entre claves la velocidad es la pendiente,
    con transiciones suaves (smoothstep) para que las rampas de cámara lenta no tengan quiebres. Pendiente 0 = congelado, negativa = retroceso."""

    def __init__(self, claves):
        self.k = sorted(claves)

    def __call__(self, f):
        k = self.k
        if f <= k[0][0]:
            return k[0][1] + (f - k[0][0]) / FPS
        if f >= k[-1][0]:
            return k[-1][1] + (f - k[-1][0]) / FPS
        for (f0, t0), (f1, t1) in zip(k, k[1:]):
            if f0 <= f <= f1:
                u = (f - f0) / max(1e-9, f1 - f0)
                s = u * u * (3 - 2 * u)
                return t0 + (t1 - t0) * (0.35 * u + 0.65 * s)
        return k[-1][1]


# ───────────────────────────────────────────── claves de animación (en bloque)
def claves_loc_rot(o, cuadros, locs, rots=None, escalas=None, lineal=False):
    for f, i in zip(cuadros, range(len(cuadros))):
        o.location = locs[i]
        o.keyframe_insert("location", frame=f)
        if rots is not None:
            o.rotation_euler = rots[i]
            o.keyframe_insert("rotation_euler", frame=f)
        if escalas is not None:
            o.scale = escalas[i]
            o.keyframe_insert("scale", frame=f)
    if lineal and o.animation_data and o.animation_data.action:
        _interp(o, "LINEAR")


def _interp(o, tipo):
    from bpy_extras import anim_utils
    ad = o.animation_data
    if not ad or not ad.action:
        return
    cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
    for fc in (cb.fcurves if cb else []):
        for kp in fc.keyframe_points:
            kp.interpolation = tipo


def clave_prop(obj, prop, f, v, indice=-1):
    setattr(obj, prop, v)
    obj.keyframe_insert(prop, frame=f, index=indice)


def visible_en(o, ini, fin, total):
    """Muestra el objeto sólo entre los cuadros ini y fin (sólo en el render: no pesa en los demás cuadros)."""
    o.hide_render = True
    o.hide_viewport = True
    o.keyframe_insert("hide_render", frame=0)
    o.hide_render = False
    o.keyframe_insert("hide_render", frame=max(0, ini - 1) if ini > 0 else 0)
    o.keyframe_insert("hide_render", frame=fin)
    o.hide_render = True
    o.keyframe_insert("hide_render", frame=min(total, fin + 1))
    _interp(o, "CONSTANT")


def colec_visible_en(c, ini, fin, total):
    c.hide_render = True
    c.keyframe_insert("hide_render", frame=0)
    c.hide_render = False
    c.keyframe_insert("hide_render", frame=ini)
    c.keyframe_insert("hide_render", frame=fin)
    c.hide_render = True
    c.keyframe_insert("hide_render", frame=min(total, fin + 1))
    if c.animation_data and c.animation_data.action:
        _interp_id(c, "CONSTANT")


def _interp_id(idb, tipo):
    from bpy_extras import anim_utils
    ad = idb.animation_data
    if not ad or not ad.action:
        return
    cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
    for fc in (cb.fcurves if cb else []):
        for kp in fc.keyframe_points:
            kp.interpolation = tipo


# ───────────────────────────────────────────── física balística de fragmentos
class Fragmento:
    def __init__(self, obj, pos, vel, rot, vrot):
        self.o = obj
        self.p = Vector(pos)
        self.v = Vector(vel)
        self.q = Quaternion(rot)
        self.w = Vector(vrot)       # velocidad angular (rad/s, eje×ángulo)
        self.reposo = False
        self.t0 = 0.0          # no se mueve antes de este instante de la simulación (dominó, retardos)


def simular(fragmentos, t_total, g=(0, 0, -9.8), suelo=None, rest=0.35, arrastre=0.05, dt=1.0 / 120.0, muestreo=1.0 / 60.0, cambios_g=None, esfera_col=None):
    """Integra todos los fragmentos y devuelve {obj: [(t, pos, quat)]} cada `muestreo` s. Cada uno tiene su trayectoria, giro y rebote.
    `cambios_g` = [(t, (gx,gy,gz))] permite invertir la gravedad. `suelo` = altura del piso (rebota y rueda hasta frenarse)."""
    res = {f.o: [] for f in fragmentos}
    t = 0.0
    prox = 0.0
    gv = Vector(g)
    camb = sorted(cambios_g or [])
    while t <= t_total + 1e-9:
        while camb and t >= camb[0][0]:
            gv = Vector(camb[0][1])
            camb.pop(0)
        if t >= prox - 1e-9:
            for f in fragmentos:
                res[f.o].append((t, f.p.copy(), f.q.copy()))
            prox += muestreo
        for f in fragmentos:
            if f.reposo or t < f.t0:
                continue
            f.v += gv * dt
            f.v *= (1.0 - arrastre * dt)
            f.p += f.v * dt
            ang = f.w.length * dt
            if ang > 1e-9:
                f.q = (Quaternion(f.w.normalized(), ang) @ f.q).normalized()
            if suelo is not None and f.p.z < suelo and f.v.z < 0:
                f.p.z = suelo
                f.v.z = -f.v.z * rest
                f.v.x *= 0.82
                f.v.y *= 0.82
                f.w *= 0.7
                if abs(f.v.z) < 0.4 and f.v.xy.length < 0.3:
                    f.reposo = True
                    f.w = Vector((0, 0, 0))
        t += dt
    return res


def animar_trayectorias(tray, tiempo, f0, f1, paso=2):
    """Escribe las claves de posición y rotación de cada fragmento usando el mapa de tiempo (cámara lenta, congelado, retroceso)."""
    for o, muestras in tray.items():
        o.rotation_mode = "QUATERNION"
        ts = [m[0] for m in muestras]
        dt = max(1e-9, ts[1] - ts[0]) if len(ts) > 1 else 1.0
        for f in range(f0, f1 + 1, paso):
            t = max(ts[0], min(ts[-1], tiempo(f)))
            i = min(len(ts) - 2, max(0, int(t / dt)))
            a, b = muestras[i], muestras[i + 1]
            u = (t - a[0]) / max(1e-9, b[0] - a[0])
            o.location = a[1].lerp(b[1], max(0.0, min(1.0, u)))
            o.rotation_quaternion = a[2].slerp(b[2], max(0.0, min(1.0, u)))
            o.keyframe_insert("location", frame=f)
            o.keyframe_insert("rotation_quaternion", frame=f)
    for o in tray:
        _interp(o, "LINEAR")


def nube_fragmentos(nombre, col, mats, n, centro, radio, vel_media, vel_dev, semilla, tam=(0.3, 0.8), gz_up=0.6, w_max=10.0, variantes=8):
    """n fragmentos con malla compartida (pocas variantes) y velocidad radial propia; devuelve la lista de Fragmento."""
    r = random.Random(semilla)
    base = [esquirla(f"{nombre}_v{i}", (r.uniform(*tam), r.uniform(*tam), r.uniform(*tam) * 0.5), semilla * 100 + i, col, r.choice(mats)) for i in range(variantes)]
    for b in base:
        b.hide_render = True
        b.hide_viewport = True
    fr = []
    for i in range(n):
        b = r.choice(base)
        o = bpy.data.objects.new(f"{nombre}_{i}", b.data)
        col.objects.link(o)
        s = r.uniform(0.5, 1.6)
        o.scale = (s, s, s)
        d = Vector((r.gauss(0, 1), r.gauss(0, 1), r.gauss(0, 1) + gz_up)).normalized()
        sp = max(0.5, r.gauss(vel_media, vel_dev))
        pos = Vector(centro) + d * r.uniform(0, radio)
        fr.append(Fragmento(o, pos, d * sp, (1, 0, 0, 0), Vector((r.gauss(0, 1), r.gauss(0, 1), r.gauss(0, 1))).normalized() * r.uniform(0.5, w_max)))
    return fr


# ───────────────────────────────────────────── volúmenes de fuego y humo
def _mm(nt, op, a=None, c=None):
    n = nt.nodes.new("ShaderNodeMath")
    n.operation = op
    for i, v in ((0, a), (1, c)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = float(v)
        else:
            nt.links.new(v, n.inputs[i])
    return n.outputs[0]


def mat_fuego(nombre, semilla=0.0):
    """Volumen de bola de fuego: turbulencia 4D (W = tiempo de simulación) con alto contraste (huecos y vetas), borde que se deshace,
    núcleo blanco-amarillo → naranja → rojo → humo oscuro en la periferia."""
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    pv = nt.nodes.new("ShaderNodeVolumePrincipled")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    r = nt.nodes.new("ShaderNodeTexNoise")
    r.noise_dimensions = "4D"
    r.inputs["Scale"].default_value = 3.2
    r.inputs["Detail"].default_value = 3.0
    r.inputs["Roughness"].default_value = 0.6
    r.inputs["Distortion"].default_value = 0.6
    r.inputs["W"].default_value = semilla
    nt.links.new(tc.outputs["Object"], r.inputs["Vector"])
    ln = nt.nodes.new("ShaderNodeVectorMath")
    ln.operation = "LENGTH"
    nt.links.new(tc.outputs["Object"], ln.inputs[0])
    edge = nt.nodes.new("ShaderNodeMapRange")
    edge.interpolation_type = "SMOOTHSTEP"
    edge.inputs["From Min"].default_value = 0.15
    edge.inputs["From Max"].default_value = 1.0
    edge.inputs["To Min"].default_value = 1.0
    edge.inputs["To Max"].default_value = 0.0
    edge.clamp = True
    nt.links.new(ln.outputs["Value"], edge.inputs["Value"])
    tb = nt.nodes.new("ShaderNodeMapRange")
    tb.inputs["From Min"].default_value = 0.38
    tb.inputs["From Max"].default_value = 0.72
    tb.clamp = True
    nt.links.new(r.outputs["Fac"], tb.inputs["Value"])
    # densidad = turbulencia × borde × multiplicador animable
    d1 = _mm(nt, "MULTIPLY", tb.outputs["Result"], edge.outputs["Result"])
    dd = nt.nodes.new("ShaderNodeMath")
    dd.operation = "MULTIPLY"
    dd.inputs[1].default_value = 6.0
    nt.links.new(d1, dd.inputs[0])
    nt.links.new(dd.outputs[0], pv.inputs["Density"])
    # temperatura: más caliente en el centro y en las vetas densas
    temp = _mm(nt, "MULTIPLY", edge.outputs["Result"], _mm(nt, "ADD", 0.35, _mm(nt, "MULTIPLY", tb.outputs["Result"], 0.65)))
    rp = nt.nodes.new("ShaderNodeValToRGB")
    cr = rp.color_ramp
    cr.elements[0].position = 0.12
    cr.elements[0].color = (0.05, 0.01, 0.0, 1)
    e1 = cr.elements.new(0.35)
    e1.color = (0.9, 0.12, 0.02, 1)
    e2 = cr.elements.new(0.6)
    e2.color = (1.0, 0.5, 0.08, 1)
    cr.elements[-1].position = 0.9
    cr.elements[-1].color = (1.0, 0.92, 0.7, 1)
    nt.links.new(temp, rp.inputs["Fac"])
    nt.links.new(rp.outputs["Color"], pv.inputs["Emission Color"])
    pv.inputs["Color"].default_value = (0.03, 0.025, 0.02, 1.0)
    # la emisión se apaga donde no hay materia (bordes y huecos): sin contorno duro
    em = nt.nodes.new("ShaderNodeMath")
    em.operation = "MULTIPLY"
    em.inputs[1].default_value = 3.0
    nt.links.new(_mm(nt, "MULTIPLY", d1, _mm(nt, "ADD", 0.5, temp)), em.inputs[0])
    nt.links.new(em.outputs[0], pv.inputs["Emission Strength"])
    pv.inputs["Anisotropy"].default_value = 0.3
    nt.links.new(pv.outputs[0], out.inputs["Volume"])
    return m, {"w": r.inputs["W"], "emi": em.inputs[1], "dens": dd.inputs[1], "nodo_ruido": r}


def bola_fuego(nombre, centro, radio_final, col, tiempo, f0, f1, tau=0.45, semilla=0.0, paso=2, duracion_s=3.0, humo=True, emi=5.0, dens=1.0):
    """Esfera volumétrica que se expande (radio = R·(1−e^(−t/τ))) con turbulencia 4D cuyo tiempo es el de simulación y emisión que decae."""
    m, h = mat_fuego(nombre + "_mat", semilla)
    o = esfera(nombre, centro, 1.0, col, m, 24, 16)
    o.visible_shadow = False
    for f in range(f0, f1 + 1, paso):
        t = tiempo(f)
        tt = max(0.0, t)
        r = radio_final * (1.0 - math.exp(-tt / tau)) + 0.02
        o.scale = (r, r, r * 0.92)
        o.keyframe_insert("scale", frame=f)
        h["w"].default_value = semilla + tt * 1.6
        h["w"].keyframe_insert("default_value", frame=f)
        k = max(0.0, 1.0 - tt / duracion_s)
        h["emi"].default_value = emi * k ** 2.2
        h["emi"].keyframe_insert("default_value", frame=f)
        h["dens"].default_value = (14.0 / max(1.0, radio_final)) * dens * (0.6 + 0.4 * min(1.0, tt))
        h["dens"].keyframe_insert("default_value", frame=f)
    return o


def bola_fuego_barata(nombre, centro, radio_final, col, tiempo, f0, f1, tau=0.5, semilla=0.0, paso=2, duracion_s=3.0, emi=6.0):
    """Bola de plasma de superficie (sin volumen): emisión con turbulencia 4D y borde que se desvanece. Mucho más barata que el volumen."""
    m = bpy.data.materials.new(nombre + "_mat")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    r = nt.nodes.new("ShaderNodeTexNoise")
    r.noise_dimensions = "4D"
    r.inputs["Scale"].default_value = 3.5
    r.inputs["Detail"].default_value = 3.0
    r.inputs["W"].default_value = semilla
    nt.links.new(tc.outputs["Object"], r.inputs["Vector"])
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.5
    tb = nt.nodes.new("ShaderNodeMapRange")
    tb.inputs["From Min"].default_value = 0.35
    tb.inputs["From Max"].default_value = 0.7
    tb.clamp = True
    nt.links.new(r.outputs["Fac"], tb.inputs["Value"])
    inv = _mm(nt, "SUBTRACT", 1.0, lw.outputs["Facing"])
    alfa = _mm(nt, "MULTIPLY", _mm(nt, "POWER", inv, 1.6), _mm(nt, "ADD", 0.25, _mm(nt, "MULTIPLY", tb.outputs["Result"], 0.9)))
    rp = nt.nodes.new("ShaderNodeValToRGB")
    cr = rp.color_ramp
    cr.elements[0].position = 0.0
    cr.elements[0].color = (0.8, 0.08, 0.0, 1)
    e1 = cr.elements.new(0.5)
    e1.color = (1.0, 0.45, 0.06, 1)
    cr.elements[-1].position = 1.0
    cr.elements[-1].color = (1.0, 0.9, 0.6, 1)
    nt.links.new(_mm(nt, "MULTIPLY", alfa, 1.2), rp.inputs["Fac"])
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(rp.outputs["Color"], em.inputs["Color"])
    fuerza = nt.nodes.new("ShaderNodeValue")
    fuerza.outputs[0].default_value = emi
    nt.links.new(fuerza.outputs[0], em.inputs["Strength"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mz = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(alfa, mz.inputs["Fac"])
    nt.links.new(tr.outputs[0], mz.inputs[1])
    nt.links.new(em.outputs[0], mz.inputs[2])
    nt.links.new(mz.outputs[0], out.inputs["Surface"])
    o = esfera(nombre, centro, 1.0, col, m, 32, 20)
    o.visible_shadow = False
    for f in range(f0, f1 + 1, paso):
        tt = max(0.0, tiempo(f))
        rr = radio_final * (1.0 - math.exp(-tt / tau)) + 0.02
        o.scale = (rr, rr, rr * 0.92)
        o.keyframe_insert("scale", frame=f)
        r.inputs["W"].default_value = semilla + tt * 1.6
        r.inputs["W"].keyframe_insert("default_value", frame=f)
        fuerza.outputs[0].default_value = emi * max(0.0, 1.0 - tt / duracion_s) ** 2.0
        fuerza.outputs[0].keyframe_insert("default_value", frame=f)
    return o


def onda_choque(nombre, centro, radio_final, col, tiempo, f0, f1, vel=1.0, semilla=0.0, grosor=0.04, color=(1.0, 0.8, 0.5)):
    """Cáscara esférica que se expande: sólo el borde refracta (distorsiona el fondo) y tiene un filo brillante."""
    m = bpy.data.materials.new(nombre + "_mat")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    g = nt.nodes.new("ShaderNodeBsdfGlass")
    g.inputs["IOR"].default_value = 1.12
    g.inputs["Roughness"].default_value = 0.0
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*color, 1.0)
    e.inputs["Strength"].default_value = 3.0
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.55
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mz = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lw.outputs["Facing"], mz.inputs["Fac"])
    nt.links.new(g.outputs[0], mz.inputs[1])
    nt.links.new(tr.outputs[0], mz.inputs[2])
    ad = nt.nodes.new("ShaderNodeAddShader")
    mz2 = nt.nodes.new("ShaderNodeMixShader")
    lw2 = nt.nodes.new("ShaderNodeLayerWeight")
    lw2.inputs["Blend"].default_value = 0.2
    nt.links.new(lw2.outputs["Fresnel"], mz2.inputs["Fac"])
    nt.links.new(tr.outputs[0], mz2.inputs[1])
    nt.links.new(e.outputs[0], mz2.inputs[2])
    nt.links.new(mz.outputs[0], ad.inputs[0])
    nt.links.new(mz2.outputs[0], ad.inputs[1])
    nt.links.new(ad.outputs[0], out.inputs["Surface"])
    o = esfera(nombre, centro, 1.0, col, m, 48, 32)
    o.visible_shadow = False
    for f in range(f0, f1 + 1, 2):
        t = max(0.0, tiempo(f))
        r = max(0.05, vel * t)
        r = min(r, radio_final)
        o.scale = (r, r, r)
        o.keyframe_insert("scale", frame=f)
    return o


# ───────────────────────────────────────────── cámara con recorridos
class Camara:
    """Cámara 9:16 con objetivo propio (Track To a un vacío). Las posiciones y el objetivo se escriben por cuadro desde funciones de t."""

    def __init__(self, nombre, col, lente=28.0):
        cd = bpy.data.cameras.new(nombre)
        cd.lens = lente
        cd.sensor_fit = "VERTICAL"
        cd.sensor_height = 24.0       # 9:16 → vertical: lente 28 mm ≈ 46° de ángulo vertical
        cd.clip_start = 0.02
        cd.clip_end = 600.0          # las escenas están separadas 1000 m: la cámara no ve las vecinas
        self.o = bpy.data.objects.new(nombre, cd)
        col.objects.link(self.o)
        self.t = bpy.data.objects.new(nombre + "_objetivo", None)
        col.objects.link(self.t)
        c = self.o.constraints.new("TRACK_TO")
        c.target = self.t
        c.track_axis = "TRACK_NEGATIVE_Z"
        c.up_axis = "UP_Y"
        self.data = cd

    def seguir(self, objetivo):
        """El objetivo de la cámara pasa a ser otro objeto (p. ej. la cadera de Aiden)."""
        self.o.constraints[0].target = objetivo
        self.sigue = True

    def claves(self, f0, f1, fpos, fobj, flente=None, fdof=None, paso=2, roll=None):
        """fpos(f) y fobj(f) → Vector; flente(f) → mm (opcional); fdof(f) → (distancia_foco, f_stop)."""
        for f in list(range(f0, f1 + 1, paso)) + ([f1] if (f1 - f0) % paso else []):
            self.o.location = fpos(f)
            self.o.keyframe_insert("location", frame=f)
            if fobj is not None:
                self.t.location = fobj(f)
                self.t.keyframe_insert("location", frame=f)
            if flente is not None:
                self.data.lens = flente(f)
                self.data.keyframe_insert("lens", frame=f)
            if fdof is not None:
                d, fs = fdof(f)
                self.data.dof.use_dof = True
                self.data.dof.focus_distance = d
                self.data.dof.aperture_fstop = fs
                self.data.dof.keyframe_insert("focus_distance", frame=f)
                self.data.dof.keyframe_insert("aperture_fstop", frame=f)


def suave(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


def lerp(a, b, u):
    return a + (b - a) * u


def lerpv(a, b, u):
    return Vector(a).lerp(Vector(b), u)


def orbita(centro, radio, ang0, ang1, alto0, alto1, u):
    a = lerp(ang0, ang1, u)
    return Vector(centro) + Vector((math.cos(a) * radio, math.sin(a) * radio, lerp(alto0, alto1, u)))


# ───────────────────────────────────────────── estrellas, polvo y partículas
def campo_estrellas(col, n=700, radio=900.0, semilla=1):
    r = random.Random(semilla)
    m = mat_emisivo("estrella", (1, 1, 1), 18.0)
    base = esfera("estrella_base", (0, 0, -9999), 1.0, col, m, 6, 4)
    out = []
    for i in range(n):
        d = Vector((r.gauss(0, 1), r.gauss(0, 1), r.gauss(0, 1))).normalized()
        o = bpy.data.objects.new(f"estrella_{i}", base.data)
        col.objects.link(o)
        o.location = d * radio
        s = r.uniform(0.25, 1.1) * radio / 900.0
        o.scale = (s, s, s)
        o.visible_shadow = False
        out.append(o)
    base.hide_render = True
    return out


def polvo(col, centro, caja_tam, n, semilla, tiempo=None, f0=0, f1=0, vel=0.05, radio=0.012):
    """Motas flotantes (esferas emisivas pálidas) con deriva lenta; sirven de escala y profundidad."""
    r = random.Random(semilla)
    m = mat_emisivo("mota", (0.9, 0.95, 1.0), 4.0)
    base = esfera("mota_base", (0, 0, -9999), 1.0, col, m, 6, 4)
    base.hide_render = True
    lista = []
    for i in range(n):
        o = bpy.data.objects.new(f"mota_{i}", base.data)
        col.objects.link(o)
        p0 = Vector(centro) + Vector((r.uniform(-1, 1) * caja_tam[0], r.uniform(-1, 1) * caja_tam[1], r.uniform(-1, 1) * caja_tam[2]))
        d = Vector((r.gauss(0, 1), r.gauss(0, 1), r.gauss(0, 1))) * vel
        s = radio * r.uniform(0.4, 1.6)
        o.scale = (s, s, s)
        o.location = p0
        o.visible_shadow = False
        lista.append((o, p0, d))
        if tiempo is not None:
            for f in range(f0, f1 + 1, 6):
                t = tiempo(f)
                o.location = p0 + d * t
                o.keyframe_insert("location", frame=f)
            _interp(o, "LINEAR")
    return lista
