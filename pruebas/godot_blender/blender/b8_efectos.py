"""ETAPA 8 — Efectos rehechos en Blender (las partículas de Godot llegan como vacíos: se usan sus posiciones).
Todo es procedural y depende sólo del cuadro (sin simulación ni horneado): cada trabajo de render puede empezar en
cualquier cuadro y da lo mismo.
- Lluvia: nodos de geometría (gotas que caen en bucle, con viento) que se cortan al tocar la camioneta (copia
  reducida de su carrocería), la vereda/calle y el techo de la casa.
- Fuego: volumen con emisión y ruido 4D que sube. Humo: volumen gris que sube por el fogón. Brasas: puntos que suben.
- Relámpagos: ya llegan animados del GLB (luz, destello del cielo y rayo): sólo se ajusta el material del rayo."""
import math
import bpy
from mathutils import Vector

T = "frame / 30"     # segundos, con un controlador simple (sin Python)


def _tiempo(nodos, x=-1200, y=0):
    v = nodos.new("ShaderNodeValue")
    v.location = (x, y)
    v.label = "segundos"
    d = v.outputs[0].driver_add("default_value").driver
    d.type = "SCRIPTED"
    d.expression = T
    return v.outputs[0]


def _mat(nombre):
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    m.node_tree.nodes.clear()
    return m, m.node_tree.nodes, m.node_tree.links


def _math(nt, op, a=None, b=None, x=0, y=0, valor_b=None):
    n = nt.nodes.new("ShaderNodeMath")
    n.operation = op
    n.location = (x, y)
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = v
        else:
            nt.links.new(v, n.inputs[i])
    return n.outputs[0]


def _caja(nombre, centro, tam, coleccion):
    bpy.ops.mesh.primitive_cube_add(size=1, location=centro)
    o = bpy.context.active_object
    o.name = nombre
    o.scale = tam
    bpy.ops.object.transform_apply(scale=True)
    for c in o.users_collection:
        c.objects.unlink(o)
    coleccion.objects.link(o)
    return o


def _col(nombre, ocultar_render=False):
    c = bpy.data.collections.new(nombre)
    bpy.context.scene.collection.children.link(c)
    c.hide_render = ocultar_render
    return c


def g2b(v):
    """Godot (x, y arriba, z) → Blender (x, −z, y arriba): la misma conversión que hace el importador glTF."""
    return Vector((v[0], -v[2], v[1]))


# ───────────────────────────── lluvia ─────────────────────────────
def lluvia() -> dict:
    fx = bpy.data.objects["FX_lluvia"].matrix_world.translation.copy()
    col_fx = _col("FX_Blender")
    col_choque = _col("Choque_lluvia_oculto", ocultar_render=True)
    # superficies donde se corta la lluvia (las cajas de colisión de Godot llegan sin tamaño: se rehacen con las medidas
    # del script de Godot) + carrocería reducida de la camioneta (más justa que la caja de Godot)
    techo = _caja("Choque_techo_casa", g2b((0.5, 3.4, 0)), (24, 8.6, 1.0), col_choque)
    # la carrocería original (958 mil triángulos): las copias reducidas quedaban con agujeros (8 % de las gotas
    # atravesaba la caja con la reducción al 5 %; 3 % al 10 %); el rayo contra la original agrega ~0,5 s por cuadro
    car = bpy.data.objects["Kodiak_carroceria"]
    red = next(o for o in car.children_recursive if o.type == "MESH")
    caras_red = len(red.data.polygons)
    # gota: cilindro fino y largo (simula el trazo de la caída)
    bpy.ops.mesh.primitive_cylinder_add(vertices=5, radius=0.006, depth=0.55, location=(0, 0, -50))
    gota = bpy.context.active_object
    gota.name = "Gota_lluvia"
    for c in gota.users_collection:
        c.objects.unlink(gota)
    col_choque.objects.link(gota)
    m, n, l = _mat("gota_lluvia")
    out = n.new("ShaderNodeOutputMaterial")
    b = n.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (0.8, 0.85, 0.95, 1)
    b.inputs["Roughness"].default_value = 0.15
    b.inputs["Alpha"].default_value = 0.35
    b.inputs["Emission Color"].default_value = (0.7, 0.78, 0.95, 1)
    b.inputs["Emission Strength"].default_value = 0.25
    l.new(b.outputs[0], out.inputs["Surface"])
    gota.data.materials.append(m)
    # objeto de la lluvia con nodos de geometría
    me = bpy.data.meshes.new("Lluvia")
    o = bpy.data.objects.new("Lluvia", me)
    col_fx.objects.link(o)
    ng = bpy.data.node_groups.new("Lluvia_nodos", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N, L = ng.nodes, ng.links
    salida = N.new("NodeGroupOutput")
    salida.location = (1600, 0)
    CANT = 9000                                 # como en Godot
    X0, X1 = fx.x - 16, fx.x + 16
    Y0, Y1 = fx.y - 11, fx.y + 11
    ARRIBA, ALTO = fx.z, 12.5
    pts = N.new("GeometryNodePoints")
    pts.inputs["Count"].default_value = CANT
    pts.inputs["Radius"].default_value = 0.01
    rnd = N.new("FunctionNodeRandomValue")
    rnd.data_type = "FLOAT_VECTOR"
    rnd.inputs["Seed"].default_value = 3
    rnd.location = (-1200, 0)
    rv = N.new("FunctionNodeRandomValue")
    rv.data_type = "FLOAT"
    rv.inputs["Seed"].default_value = 9
    for sk in rv.inputs:                       # Min/Max del tipo flotante (hay uno por tipo de dato)
        if sk.type == "VALUE" and sk.name in ("Min", "Max"):
            sk.default_value = 11.0 if sk.name == "Min" else 14.0
    rv.location = (-1200, -300)
    sep = N.new("ShaderNodeSeparateXYZ")
    sep.location = (-1000, 0)
    L.new(rnd.outputs["Value"], sep.inputs[0])
    tiempo = N.new("GeometryNodeInputSceneTime")
    tiempo.location = (-1200, -500)

    def gm(op, a, b=None, x=0, y=0):
        return _math(ng, op, a, b, x, y)
    x = gm("MULTIPLY_ADD", sep.outputs[0], X1 - X0, -800, 200)
    N[x.node.name].inputs[2].default_value = X0
    y = gm("MULTIPLY_ADD", sep.outputs[1], Y1 - Y0, -800, 0)
    N[y.node.name].inputs[2].default_value = Y0
    # caída: fract(fase + t·v/ALTO)·ALTO
    vt = gm("MULTIPLY", tiempo.outputs["Seconds"], rv.outputs[0], -900, -400)
    vh = gm("DIVIDE", vt, ALTO, -750, -400)
    fa = gm("ADD", vh, sep.outputs[2], -600, -400)
    fr = gm("FRACT", fa, None, -450, -400)
    caida = gm("MULTIPLY", fr, ALTO, -300, -400)
    z = gm("SUBTRACT", ARRIBA, caida, -150, -400)
    viento = gm("MULTIPLY_ADD", caida, 0.12, -150, 200)       # deriva de 12 cm por metro (como en Godot)
    N[viento.node.name].inputs[2].default_value = 0.0
    xv = gm("ADD", x, viento, 0, 200)
    pos = N.new("ShaderNodeCombineXYZ")
    pos.location = (150, 0)
    L.new(xv, pos.inputs[0]); L.new(y, pos.inputs[1]); L.new(z, pos.inputs[2])
    L.new(pos.outputs[0], pts.inputs["Position"])
    pts.location = (350, 0)
    # rayo hacia abajo desde arriba de la gota: si ya pasó la superficie que encontró, se borra
    origen = N.new("ShaderNodeCombineXYZ")
    origen.location = (150, -250)
    L.new(xv, origen.inputs[0]); L.new(y, origen.inputs[1]); origen.inputs[2].default_value = ARRIBA + 1
    choques = N.new("GeometryNodeJoinGeometry")
    choques.location = (150, -500)
    for ob in (red, techo):
        oi = N.new("GeometryNodeObjectInfo")
        oi.transform_space = "RELATIVE"
        oi.inputs["Object"].default_value = ob
        oi.location = (-100, -600 if ob is red else -750)
        L.new(oi.outputs["Geometry"], choques.inputs[0])
    rc = N.new("GeometryNodeRaycast")
    rc.location = (400, -350)
    L.new(choques.outputs[0], rc.inputs["Target Geometry"])
    L.new(origen.outputs[0], rc.inputs["Source Position"])
    rc.inputs["Ray Direction"].default_value = (0, 0, -1)
    rc.inputs["Ray Length"].default_value = 40
    hz = N.new("ShaderNodeSeparateXYZ")
    hz.location = (600, -350)
    L.new(rc.outputs["Hit Position"], hz.inputs[0])
    debajo = gm("LESS_THAN", z, hz.outputs[2], 750, -300)
    pego = gm("MULTIPLY", debajo, rc.outputs["Is Hit"], 900, -300)
    piso = gm("LESS_THAN", z, -0.07, 750, -500)                  # vereda (−0,07) y calle (−0,25): se apaga al llegar
    borrar = gm("MAXIMUM", pego, piso, 1050, -350)
    dl = N.new("GeometryNodeDeleteGeometry")
    dl.domain = "POINT"
    dl.location = (1100, 0)
    L.new(pts.outputs[0], dl.inputs["Geometry"])
    L.new(borrar, dl.inputs["Selection"])
    gi = N.new("GeometryNodeObjectInfo")
    gi.inputs["Object"].default_value = gota
    gi.location = (1100, -250)
    ip = N.new("GeometryNodeInstanceOnPoints")
    ip.location = (1350, 0)
    L.new(dl.outputs[0], ip.inputs["Points"])
    L.new(gi.outputs["Geometry"], ip.inputs["Instance"])
    ip.inputs["Rotation"].default_value = (0.0, math.atan(0.12), 0.0)   # inclinada con el viento
    L.new(ip.outputs[0], salida.inputs[0])
    mod = o.modifiers.new("Lluvia", "NODES")
    mod.node_group = ng
    return {"gotas": CANT, "caja_x": [round(X0, 2), round(X1, 2)], "caja_y": [round(Y0, 2), round(Y1, 2)],
            "caras_choque_camioneta": caras_red}


# ───────────────────────────── fuego, humo, brasas ─────────────────────────────
def _volumen(nombre, centro, tam, col):
    o = _caja(nombre, centro, tam, col)
    o.visible_shadow = False
    return o


def _ruido_subiendo(nt, t, velocidad, escala, x0=-900, y0=0):
    """Coordenadas generadas (0..1) con el ruido 4D desplazándose hacia arriba: devuelve (factor, z 0..1, dist. xy)."""
    N, L = nt.nodes, nt.links
    tc = N.new("ShaderNodeTexCoord"); tc.location = (x0 - 400, y0)
    sp = N.new("ShaderNodeSeparateXYZ"); sp.location = (x0 - 200, y0 - 200)
    L.new(tc.outputs["Generated"], sp.inputs[0])
    sube = _math(nt, "MULTIPLY", t, -velocidad, x0 - 200, y0 + 200)
    mv = N.new("ShaderNodeVectorMath"); mv.operation = "ADD"; mv.location = (x0, y0)
    cz = N.new("ShaderNodeCombineXYZ"); cz.location = (x0 - 200, y0 + 100)
    L.new(sube, cz.inputs[2])
    L.new(tc.outputs["Generated"], mv.inputs[0]); L.new(cz.outputs[0], mv.inputs[1])
    nz = N.new("ShaderNodeTexNoise"); nz.noise_dimensions = "4D"; nz.location = (x0 + 200, y0)
    nz.inputs["Scale"].default_value = escala
    nz.inputs["Detail"].default_value = 6.0
    nz.inputs["Roughness"].default_value = 0.6
    L.new(mv.outputs[0], nz.inputs["Vector"])
    L.new(_math(nt, "MULTIPLY", t, 0.9, x0, y0 - 350), nz.inputs["W"])
    dx = _math(nt, "SUBTRACT", sp.outputs[0], 0.5, x0, y0 - 500)
    dy = _math(nt, "SUBTRACT", sp.outputs[1], 0.5, x0, y0 - 600)
    cxy = N.new("ShaderNodeCombineXYZ"); cxy.location = (x0 + 200, y0 - 550)
    L.new(dx, cxy.inputs[0]); L.new(dy, cxy.inputs[1])
    ln = N.new("ShaderNodeVectorMath"); ln.operation = "LENGTH"; ln.location = (x0 + 400, y0 - 550)
    L.new(cxy.outputs[0], ln.inputs[0])
    return nz.outputs["Fac"], sp.outputs[2], ln.outputs["Value"]


def fuego() -> dict:
    col = bpy.data.collections["FX_Blender"]
    f = bpy.data.objects["FX_fuego"].matrix_world.translation.copy()
    # base del fuego sobre la parrilla; Blender: x a lo ancho, y hacia la sala (−z de Godot), z arriba
    o = _volumen("Fuego_volumen", f + Vector((0, 0, 0.3)), (0.85, 0.32, 0.75), col)
    m, N, L = _mat("fuego_volumen")
    nt = m.node_tree
    t = _tiempo(N)
    fac, z, r = _ruido_subiendo(nt, t, 1.4, 4.0)
    # forma: más angosto arriba (r < 0,5·(1−z)) y se apaga hacia arriba
    lim = _math(nt, "MULTIPLY", _math(nt, "SUBTRACT", 1.0, z, -100, -700), 0.55, 50, -700)
    forma = _math(nt, "SMOOTH_MIN", _math(nt, "SUBTRACT", lim, r, 200, -650), 1.0, 350, -650)
    N[forma.node.name].inputs[2].default_value = 0.1
    alto = _math(nt, "POWER", _math(nt, "SUBTRACT", 1.0, z, 200, -850), 1.4, 350, -850)
    d = _math(nt, "MULTIPLY", _math(nt, "MULTIPLY", fac, forma, 500, -300), alto, 650, -300)
    d = _math(nt, "MULTIPLY", _math(nt, "SUBTRACT", d, 0.08, 800, -300), 9.0, 950, -300)
    N[d.node.name].use_clamp = True
    rampa = N.new("ShaderNodeValToRGB"); rampa.location = (1100, -100)
    e = rampa.color_ramp.elements
    e[0].position, e[0].color = 0.0, (0.25, 0.02, 0.0, 1)
    e[1].position, e[1].color = 1.0, (1.0, 0.85, 0.45, 1)
    mid = e.new(0.45); mid.color = (1.0, 0.32, 0.03, 1)
    L.new(d, rampa.inputs[0])
    em = N.new("ShaderNodeEmission"); em.location = (1400, 0)
    L.new(rampa.outputs[0], em.inputs["Color"])
    L.new(_math(nt, "MULTIPLY", d, 22.0, 1250, -300), em.inputs["Strength"])
    out = N.new("ShaderNodeOutputMaterial"); out.location = (1600, 0)
    L.new(em.outputs[0], out.inputs["Volume"])
    o.data.materials.append(m)
    # humo: del fuego para arriba hasta el techo del fogón (1,14 m en Godot)
    h = bpy.data.objects["FX_humo"].matrix_world.translation.copy()
    oh = _volumen("Humo_volumen", Vector((h.x, h.y, 0.86)), (1.3, 0.42, 0.56), col)
    m2, N2, L2 = _mat("humo_volumen")
    nt2 = m2.node_tree
    t2 = _tiempo(N2)
    fac2, z2, r2 = _ruido_subiendo(nt2, t2, 0.5, 3.0)
    alto2 = _math(nt2, "MULTIPLY", z2, _math(nt2, "SUBTRACT", 1.0, r2, 200, -900), 350, -850)
    d2 = _math(nt2, "MULTIPLY", _math(nt2, "SUBTRACT", fac2, 0.48, 500, -300), alto2, 650, -300)
    d2 = _math(nt2, "MULTIPLY", d2, 6.0, 800, -300)
    N2[d2.node.name].use_clamp = True
    pv = N2.new("ShaderNodeVolumePrincipled"); pv.location = (1100, 0)
    pv.inputs["Color"].default_value = (0.3, 0.29, 0.28, 1)
    pv.inputs["Anisotropy"].default_value = 0.3
    L2.new(_math(nt2, "MULTIPLY", d2, 1.6, 950, -300), pv.inputs["Density"])
    out2 = N2.new("ShaderNodeOutputMaterial"); out2.location = (1400, 0)
    L2.new(pv.outputs[0], out2.inputs["Volume"])
    oh.data.materials.append(m2)
    return {"fuego": "volumen emisivo con ruido 4D", "humo": "volumen principled", "centro_fuego": [round(v, 2) for v in f]}


def brasas() -> dict:
    col = bpy.data.collections["FX_Blender"]
    b = bpy.data.objects["FX_brasas"].matrix_world.translation.copy()
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1.0, location=(0, 0, -50))
    chispa = bpy.context.active_object
    chispa.name = "Chispa"
    for c in chispa.users_collection:
        c.objects.unlink(chispa)
    bpy.data.collections["Choque_lluvia_oculto"].objects.link(chispa)
    m, N, L = _mat("chispa")
    em = N.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (1.0, 0.45, 0.08, 1)
    em.inputs["Strength"].default_value = 40.0
    out = N.new("ShaderNodeOutputMaterial")
    L.new(em.outputs[0], out.inputs["Surface"])
    chispa.data.materials.append(m)
    me = bpy.data.meshes.new("Brasas")
    o = bpy.data.objects.new("Brasas_chispas", me)
    col.objects.link(o)
    ng = bpy.data.node_groups.new("Brasas_nodos", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N, L = ng.nodes, ng.links
    sal = N.new("NodeGroupOutput")
    pts = N.new("GeometryNodePoints")
    pts.inputs["Count"].default_value = 45            # como en Godot
    rnd = N.new("FunctionNodeRandomValue"); rnd.data_type = "FLOAT_VECTOR"; rnd.inputs["Seed"].default_value = 5
    sp = N.new("ShaderNodeSeparateXYZ")
    L.new(rnd.outputs["Value"], sp.inputs[0])
    tm = N.new("GeometryNodeInputSceneTime")
    VIDA = 2.2
    edad = _math(ng, "FRACT", _math(ng, "ADD", _math(ng, "DIVIDE", tm.outputs["Seconds"], VIDA), sp.outputs[2]))
    # posición: base ± 30 cm de ancho, ± 10 cm de fondo; sube 0,9 m en su vida, con un vaivén
    x = _math(ng, "ADD", _math(ng, "MULTIPLY_ADD", sp.outputs[0], 0.6), _math(ng, "MULTIPLY", _math(ng, "SINE", _math(ng, "MULTIPLY_ADD", tm.outputs["Seconds"], 3.0)), 0.05))
    N[x.node.inputs[0].links[0].from_node.name].inputs[2].default_value = b.x - 0.3
    y = _math(ng, "MULTIPLY_ADD", sp.outputs[1], 0.2)
    N[y.node.name].inputs[2].default_value = b.y - 0.1
    z = _math(ng, "MULTIPLY_ADD", edad, 0.9)
    N[z.node.name].inputs[2].default_value = b.z
    pos = N.new("ShaderNodeCombineXYZ")
    L.new(x, pos.inputs[0]); L.new(y, pos.inputs[1]); L.new(z, pos.inputs[2])
    L.new(pos.outputs[0], pts.inputs["Position"])
    gi = N.new("GeometryNodeObjectInfo"); gi.inputs["Object"].default_value = chispa
    ip = N.new("GeometryNodeInstanceOnPoints")
    L.new(pts.outputs[0], ip.inputs["Points"]); L.new(gi.outputs["Geometry"], ip.inputs["Instance"])
    esc = _math(ng, "MULTIPLY_ADD", _math(ng, "SUBTRACT", 1.0, edad), 0.007)
    N[esc.node.name].inputs[2].default_value = 0.001
    L.new(esc, ip.inputs["Scale"])
    L.new(ip.outputs[0], sal.inputs[0])
    o.modifiers.new("Brasas", "NODES").node_group = ng
    return {"brasas": 45}


def relampago() -> dict:
    # el rayo y el destello llegan animados (escala); sólo se refuerza la emisión del rayo para Cycles
    m = bpy.data.materials["rayo"]
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Emission Strength"].default_value = 60.0
    for o in (bpy.data.objects["Relampago_cielo"], bpy.data.objects["Relampago_rayo"]):
        for h in [o] + list(o.children_recursive):
            h.visible_shadow = False
    return {"relampago": "animación del GLB + emisión del rayo 60, sin sombra"}


def crear() -> dict:
    r = {}
    r.update(lluvia())
    r.update(fuego())
    r.update(brasas())
    r.update(relampago())
    return r
