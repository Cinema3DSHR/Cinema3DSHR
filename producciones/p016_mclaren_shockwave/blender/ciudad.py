"""p016 · avenida futurista (eje Y), edificios con grandes vidrieras (hero), fachadas con ventanas cálidas reactivas a la onda, árboles, canteros y asfalto mojado."""
import math
import random
import bpy
from mathutils import Vector
import lib
from lib import *
import guion
import sh3d
import interiores

ANCHO_CALZADA = 24.0       # x ∈ [−12, 12]
X_VIDRIO = 17.0            # plano de las vidrieras (±)
H_PLANTA = 8.5             # alto del zócalo vidriado
HERO_Y0, HERO_Y1 = -540.0, 40.0     # zona donde los vidrios se rompen
CIUDAD_Y0, CIUDAD_Y1 = -700.0, 900.0


def _n(nt, tipo, **kw):
    n = nt.nodes.new(tipo)
    for k, v in kw.items():
        setattr(n, k, v)
    return n


def mat_asfalto():
    m = bpy.data.materials.new("asfalto_mojado")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = _n(nt, "ShaderNodeTexCoord")
    r1 = _n(nt, "ShaderNodeTexNoise")
    r1.inputs["Scale"].default_value = 0.35
    r1.inputs["Detail"].default_value = 6.0
    nt.links.new(tc.outputs["Object"], r1.inputs["Vector"])
    r2 = _n(nt, "ShaderNodeTexNoise")
    r2.inputs["Scale"].default_value = 14.0
    r2.inputs["Detail"].default_value = 9.0
    nt.links.new(tc.outputs["Object"], r2.inputs["Vector"])
    cr = _n(nt, "ShaderNodeValToRGB")
    cr.color_ramp.elements[0].color = (0.012, 0.012, 0.014, 1)
    cr.color_ramp.elements[1].color = (0.06, 0.058, 0.055, 1)
    nt.links.new(r2.outputs["Fac"], cr.inputs["Fac"])
    nt.links.new(cr.outputs["Color"], b.inputs["Base Color"])
    # charcos: donde el ruido grande es bajo, el asfalto es casi un espejo
    rr = _n(nt, "ShaderNodeMapRange")
    rr.inputs["From Min"].default_value = 0.40
    rr.inputs["From Max"].default_value = 0.58
    rr.inputs["To Min"].default_value = 0.04
    rr.inputs["To Max"].default_value = 0.45
    rr.clamp = True
    nt.links.new(r1.outputs["Fac"], rr.inputs["Value"])
    nt.links.new(rr.outputs["Result"], b.inputs["Roughness"])
    b.inputs["Specular IOR Level"].default_value = 0.8
    bu = _n(nt, "ShaderNodeBump")
    bu.inputs["Strength"].default_value = 0.15
    nt.links.new(r2.outputs["Fac"], bu.inputs["Height"])
    nt.links.new(bu.outputs["Normal"], b.inputs["Normal"])
    return m


def mat_fachada():
    """Torres: cuadrícula de ventanas con luz cálida, apagadas al azar; cuando la onda pasa (y > y_frente) las ventanas se rompen: apagadas, oscuras y con fisuras."""
    m = bpy.data.materials.new("fachada_torre")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = _n(nt, "ShaderNodeOutputMaterial")
    geo = _n(nt, "ShaderNodeNewGeometry")
    sep = _n(nt, "ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Position"], sep.inputs[0])
    M = lambda op, a=None, c=None: lib._mm(nt, op, a, c)
    # celdas de 3,2 m (en Y) × 3,8 m (en Z)
    cu = M("DIVIDE", sep.outputs["Y"], 3.2)
    cv = M("DIVIDE", sep.outputs["Z"], 3.8)
    fu, fv = M("FRACT", cu), M("FRACT", cv)
    ventana = M("MULTIPLY", M("MULTIPLY", M("GREATER_THAN", fu, 0.14), M("LESS_THAN", fu, 0.86)), M("MULTIPLY", M("GREATER_THAN", fv, 0.2), M("LESS_THAN", fv, 0.82)))
    wn = _n(nt, "ShaderNodeTexWhiteNoise")
    wn.noise_dimensions = "2D"
    cv2 = _n(nt, "ShaderNodeCombineXYZ")
    nt.links.new(M("FLOOR", cu), cv2.inputs["X"])
    nt.links.new(M("FLOOR", cv), cv2.inputs["Y"])
    nt.links.new(cv2.outputs[0], wn.inputs["Vector"])
    prendida = M("LESS_THAN", wn.outputs["Value"], 0.68)
    yf = _n(nt, "ShaderNodeValue")
    yf.label = "y_frente"
    yf.outputs[0].default_value = 99999.0
    rota = M("GREATER_THAN", sep.outputs["Y"], yf.outputs[0])
    # fisuras: bordes de Voronoi en la zona rota
    vo = _n(nt, "ShaderNodeTexVoronoi")
    vo.feature = "DISTANCE_TO_EDGE"
    vo.inputs["Scale"].default_value = 2.6
    nt.links.new(geo.outputs["Position"], vo.inputs["Vector"])
    fis = M("LESS_THAN", vo.outputs["Distance"], 0.045)
    # emisión: ventana prendida e intacta → cálida; rota → apagada con fisuras
    calida = _n(nt, "ShaderNodeEmission")
    calida.inputs["Color"].default_value = (1.0, 0.68, 0.30, 1)
    ev = _n(nt, "ShaderNodeVectorMath")
    ev.operation = "SCALE"
    nt.links.new(M("MULTIPLY", M("MULTIPLY", ventana, prendida), M("SUBTRACT", 1.0, rota)), ev.inputs["Scale"])
    ev.inputs[0].default_value = (4.0, 4.0, 4.0)
    nt.links.new(ev.outputs[0], calida.inputs["Strength"]) if False else None
    k = M("MULTIPLY", M("MULTIPLY", ventana, prendida), M("SUBTRACT", 1.0, rota))
    nt.links.new(M("MULTIPLY", k, 5.0), calida.inputs["Strength"])
    # cuerpo de la torre: hormigón oscuro con brillo metálico; vidrio apagado: reflectivo oscuro
    cuerpo = _n(nt, "ShaderNodeBsdfPrincipled")
    cuerpo.inputs["Base Color"].default_value = (0.03, 0.032, 0.038, 1)
    cuerpo.inputs["Metallic"].default_value = 0.6
    cuerpo.inputs["Roughness"].default_value = 0.3
    nt.links.new(M("MULTIPLY", ventana, 1.0), cuerpo.inputs["Metallic"]) if False else None
    mez = _n(nt, "ShaderNodeMixShader")
    nt.links.new(ventana, mez.inputs["Fac"])
    nt.links.new(cuerpo.outputs[0], mez.inputs[1])
    # el vidrio: si está prendida emite, si no refleja
    sumo = _n(nt, "ShaderNodeAddShader")
    vid = _n(nt, "ShaderNodeBsdfGlossy")
    vid.inputs["Color"].default_value = (0.5, 0.6, 0.7, 1)
    vid.inputs["Roughness"].default_value = 0.08
    nt.links.new(vid.outputs[0], sumo.inputs[0])
    nt.links.new(calida.outputs[0], sumo.inputs[1])
    nt.links.new(sumo.outputs[0], mez.inputs[2])
    # fisuras brillantes sobre la zona rota (líneas pálidas)
    fl = _n(nt, "ShaderNodeEmission")
    fl.inputs["Color"].default_value = (0.7, 0.8, 0.9, 1)
    nt.links.new(M("MULTIPLY", M("MULTIPLY", fis, rota), ventana), fl.inputs["Strength"])
    a2 = _n(nt, "ShaderNodeAddShader")
    nt.links.new(mez.outputs[0], a2.inputs[0])
    nt.links.new(fl.outputs[0], a2.inputs[1])
    nt.links.new(a2.outputs[0], out.inputs["Surface"])
    return m, yf.outputs[0]


def mat_interior():
    """Interior de las tiendas detrás de los vidrios: resplandor cálido dorado con estantes (ruido de barras)."""
    m = bpy.data.materials.new("interior_calido")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = _n(nt, "ShaderNodeOutputMaterial")
    tc = _n(nt, "ShaderNodeTexCoord")
    sep = _n(nt, "ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    M = lambda op, a=None, c=None: lib._mm(nt, op, a, c)
    barras = M("ADD", 0.55, M("MULTIPLY", 0.45, M("SINE", M("MULTIPLY", sep.outputs["Z"], 5.5))))
    rn = _n(nt, "ShaderNodeTexNoise")
    rn.inputs["Scale"].default_value = 6.0
    nt.links.new(tc.outputs["Object"], rn.inputs["Vector"])
    em = _n(nt, "ShaderNodeEmission")
    em.inputs["Color"].default_value = (1.0, 0.66, 0.26, 1)
    nt.links.new(M("MULTIPLY", M("MULTIPLY", barras, M("ADD", 0.35, rn.outputs["Fac"])), 2.0), em.inputs["Strength"])
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    return m


def construir(ctx):
    col = coleccion("Ciudad")
    col_int = coleccion("Interiores_SweetHome")
    col_arb = coleccion("Arboles_SweetHome")
    r = random.Random(16)
    asf = mat_asfalto()
    acera = mat("acera", (0.16, 0.155, 0.15), rug=0.45)
    hormigon = mat_ruido("hormigon", (0.06, 0.06, 0.065), (0.2, 0.2, 0.21), 3.0, rug=0.55, bump=0.2)
    metal = mat("metal_marco", (0.03, 0.03, 0.035), metal=0.9, rug=0.25)
    pintura = mat_emisivo("raya_vial", (0.9, 0.9, 0.85), 0.6)
    fach, yf_socket = mat_fachada()
    inter = mat_interior()
    ctx.yf_socket = yf_socket
    L = CIUDAD_Y1 - CIUDAD_Y0
    yc = (CIUDAD_Y0 + CIUDAD_Y1) / 2
    caja("calzada", (0, yc, -0.05), (ANCHO_CALZADA, L, 0.1), col, asf)
    for sx in (-1, 1):
        caja(f"acera_{sx}", (sx * (ANCHO_CALZADA / 2 + 2.5), yc, 0.06), (5.0, L, 0.28), col, acera)
        caja(f"bordillo_{sx}", (sx * (ANCHO_CALZADA / 2 + 0.1), yc, 0.1), (0.25, L, 0.3), col, hormigon)
    # rayas viales
    y = CIUDAD_Y0
    while y < CIUDAD_Y1:
        caja(f"raya_{int(y)}", (0, y, 0.005), (0.18, 3.0, 0.01), col, pintura)
        y += 9.0
    # ───── torres por módulos de 30 m
    paso = 30.0
    y = CIUDAD_Y0
    k = 0
    while y < CIUDAD_Y1:
        for sx in (-1, 1):
            h = r.choice((46, 58, 72, 90, 110, 130)) + r.uniform(-6, 6)
            prof = r.uniform(26, 40)
            xin = sx * (X_VIDRIO + 1.6)
            # zócalo: en la zona cercana lleva un interior real (restaurante, supermercado o tienda de muebles con muebles de Sweet Home 3D); lejos, un resplandor cálido
            if CIUDAD_Y0 + 60 <= y < 150.0:
                rng_i = random.Random(1000 + k * 2 + (1 if sx > 0 else 0))
                interiores.TIPOS[(k + (1 if sx > 0 else 0)) % 3](col_int, y, sx, paso, rng_i)
            else:
                caja(f"zocalo_{k}_{sx}", (sx * (X_VIDRIO + 1.6 + prof / 2), y + paso / 2, H_PLANTA / 2), (prof, paso - 0.4, H_PLANTA), col, inter)
            caja(f"torre_{k}_{sx}", (sx * (X_VIDRIO + 0.2 + (prof + 1.4) / 2), y + paso / 2, H_PLANTA + h / 2), (prof + 1.4, paso - 0.4, h), col, fach)
            caja(f"voladizo_{k}_{sx}", (sx * (X_VIDRIO - 0.6), y + paso / 2, H_PLANTA + 0.25), (2.4, paso, 0.5), col, hormigon)
        y += paso
        k += 1
    # montantes y travesaños de las vidrieras (zona hero)
    yy = HERO_Y0
    while yy <= HERO_Y1:
        for sx in (-1, 1):
            caja(f"montante_{int(yy)}_{sx}", (sx * X_VIDRIO, yy, H_PLANTA / 2), (0.14, 0.18, H_PLANTA), col, metal)
        yy += 3.0
    for sx in (-1, 1):
        caja(f"travesano_b_{sx}", (sx * X_VIDRIO, (HERO_Y0 + HERO_Y1) / 2, 0.1), (0.2, HERO_Y1 - HERO_Y0, 0.2), col, metal)
        caja(f"travesano_a_{sx}", (sx * X_VIDRIO, (HERO_Y0 + HERO_Y1) / 2, H_PLANTA - 0.1), (0.2, HERO_Y1 - HERO_Y0, 0.2), col, metal)
    # ───── árboles REALES de Sweet Home 3D (con copas densas) sobre canteros
    tipos = ["tree_tree"]          # el único árbol de Sweet Home con copa densa y hojas con forma
    for i_, tp in enumerate(tipos):
        sh3d.preparar_arbol(tp, semilla=i_ + 1, copias=6)
    ctx.arboles = []
    for sx in (-1, 1):
        yy = CIUDAD_Y0 + 7.0
        while yy < CIUDAD_Y1:
            c = Vector((sx * 14.3, yy + r.uniform(-1.5, 1.5), 0.28))
            tp = r.choice(tipos)
            esc = r.uniform(1.1, 1.65)
            raiz = sh3d.poner(tp, col_arb, c, frente=(0, -1), escala=esc, nombre=f"arb_{sx}_{int(yy)}")
            hijos = sh3d.ULTIMOS
            alto = sh3d._BIB[tp]["dim"].z * esc
            copa = [o for o in hijos if o.type == "MESH" and any(s_ in o.name.lower() for s_ in ("leav", "foil"))]
            ctx.arboles.append({"pos": c, "sx": sx, "alto": alto, "copa": copa, "raiz": raiz})
            caja(f"cantero_{sx}_{int(yy)}", c + Vector((0, 0, 0.0)), (1.8, 2.4, 0.3), col, hormigon)
            yy += 14.0 if yy < 300 else 28.0
    return col
