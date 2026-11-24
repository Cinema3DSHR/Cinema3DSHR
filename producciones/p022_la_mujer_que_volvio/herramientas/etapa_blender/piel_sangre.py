# Sangre en la piel (rostro: heridita y manchas de roce; manos). Se ejecuta con exec() dentro de efectos_*.py (comparte bpy, Vector, math y f_imp).
def _rgba(nodo, nombre):
    return [x for x in nodo.inputs if x.name == nombre and x.type == 'RGBA'][0]
def sangre_en(material, mascara_fn, factor_max=1.0):
    nt = material.node_tree; bs = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    ent = bs.inputs['Base Color']
    origen = ent.links[0].from_socket if ent.links else None; val = tuple(ent.default_value)
    tc = nt.nodes.new('ShaderNodeTexCoord'); sx = nt.nodes.new('ShaderNodeSeparateXYZ')
    caja = None
    if material.name == 'EM3D_Skin_Head':                       # caja real de la piel de la cabeza (en reposo) para normalizar las coordenadas
        for ob in bpy.data.objects:
            if ob.type == 'MESH' and any(sl.material == material for sl in ob.material_slots):
                idx = [i for i, sl in enumerate(ob.material_slots) if sl.material == material][0]
                vs = {v for pl in ob.data.polygons if pl.material_index == idx for v in pl.vertices}
                if vs:
                    cs = [ob.data.vertices[v].co for v in vs]
                    lo = Vector((min(c.x for c in cs), min(c.y for c in cs), min(c.z for c in cs))); hi = Vector((max(c.x for c in cs), max(c.y for c in cs), max(c.z for c in cs)))
                    caja = (lo, hi); break
    if caja:
        mpn = nt.nodes.new('ShaderNodeMapping'); lo, hi = caja; sz = hi - lo
        mpn.inputs['Location'].default_value = (-lo.x / sz.x, -lo.y / sz.y, -lo.z / sz.z); mpn.inputs['Scale'].default_value = (1 / sz.x, 1 / sz.y, 1 / sz.z)
        nt.links.new(tc.outputs['Object'], mpn.inputs[0]); nt.links.new(mpn.outputs[0], sx.inputs[0]); fuente = mpn.outputs[0]
        print('caja de la cabeza', [round(v, 3) for v in lo], [round(v, 3) for v in hi])
    else:
        nt.links.new(tc.outputs['Generated'], sx.inputs[0]); fuente = tc.outputs['Generated']
    ru = nt.nodes.new('ShaderNodeTexNoise'); ru.inputs['Scale'].default_value = 22.0; ru.inputs['Detail'].default_value = 7.0; nt.links.new(fuente, ru.inputs['Vector'])
    m_ = mascara_fn(nt, sx, ru)
    cant = nt.nodes.new('ShaderNodeValue'); cant.outputs[0].default_value = 0.0
    d_ = cant.outputs[0].driver_add('default_value') if False else None
    drv = cant.driver_add('outputs[0].default_value') if False else None
    mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; nt.links.new(m_, mul.inputs[0]); mul.inputs[1].default_value = 1.0
    d2 = mul.inputs[1].driver_add('default_value'); d2.driver.type = 'SCRIPTED'; d2.driver.expression = f'min(max((frame - {f_imp}) / 40.0, 0.0), 1.0) * {factor_max}'
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; _rgba(mx, 'B').default_value = (0.20, 0.004, 0.006, 1)
    if origen: nt.links.new(origen, _rgba(mx, 'A'))
    else: _rgba(mx, 'A').default_value = val
    cl = nt.nodes.new('ShaderNodeClamp'); nt.links.new(mul.outputs[0], cl.inputs['Value']); nt.links.new(cl.outputs[0], mx.inputs['Factor'])
    nt.links.new(mx.outputs['Result'], ent)
    # brillo húmedo donde hay sangre
    rg = nt.nodes.new('ShaderNodeMix'); rg.data_type = 'FLOAT'; rg.inputs['A'].default_value = bs.inputs['Roughness'].default_value; rg.inputs['B'].default_value = 0.08
    nt.links.new(cl.outputs[0], rg.inputs['Factor']); nt.links.new(rg.outputs['Result'], bs.inputs['Roughness'])
def mascara_cara(nt, sx, ru):          # frente, sienes y mejillas con goteo irregular (simétrica: se ve de cualquier lado)
    zr = nt.nodes.new('ShaderNodeMapRange'); zr.inputs['From Min'].default_value = 0.35; zr.inputs['From Max'].default_value = 0.90; nt.links.new(sx.outputs['Y'], zr.inputs['Value'])      # el eje vertical de esta malla es Y
    mm = nt.nodes.new('ShaderNodeMath'); mm.operation = 'MULTIPLY'; nt.links.new(zr.outputs[0], mm.inputs[0]); nt.links.new(ru.outputs['Fac'], mm.inputs[1])
    ge = nt.nodes.new('ShaderNodeMath'); ge.operation = 'GREATER_THAN'; ge.inputs[1].default_value = 0.20; nt.links.new(mm.outputs[0], ge.inputs[0]); return ge.outputs[0]
def mascara_manos(nt, sx, ru):         # manos y antebrazos (zona baja a los costados del cuerpo)
    zr = nt.nodes.new('ShaderNodeMapRange'); zr.inputs['From Min'].default_value = 0.52; zr.inputs['From Max'].default_value = 0.40; nt.links.new(sx.outputs['Z'], zr.inputs['Value'])
    mm = nt.nodes.new('ShaderNodeMath'); mm.operation = 'MULTIPLY'; nt.links.new(zr.outputs[0], mm.inputs[0]); nt.links.new(ru.outputs['Fac'], mm.inputs[1])
    ge = nt.nodes.new('ShaderNodeMath'); ge.operation = 'GREATER_THAN'; ge.inputs[1].default_value = 0.20; nt.links.new(mm.outputs[0], ge.inputs[0]); return ge.outputs[0]
def sangre_cara(material):
    """Rostro manchado (no chorreado): una heridita en la frente y manchas finas de roce en mejilla, mandíbula, sien y mentón, como de quien se tocó la cara con la mano.
    Cada mancha es una elipse gaussiana definida en el espacio 3D del modelo, centrada en un punto real de la superficie de la cara (se calculan ojos y boca del propio modelo)."""
    ob = next(o for o in bpy.data.objects if o.type == 'MESH' and any(sl.material == material for sl in o.material_slots))
    idx = [i for i, sl in enumerate(ob.material_slots) if sl.material == material][0]
    vs = {v for pl in ob.data.polygons if pl.material_index == idx for v in pl.vertices}
    cs = [ob.data.vertices[v].co for v in vs]
    zmed = sum(c.z for c in cs) / len(cs)
    def verts(prefijo, excluir=None):
        for o in bpy.data.objects:
            if o.type == 'MESH' and o.name.startswith(prefijo) and not (excluir and o.name.startswith(excluir)): return [v.co for v in o.data.vertices]
        return []
    ev = verts('EM3D_Base_Eye', 'EM3D_Base_EyeO'); dv = verts('EM3D_Base_Teeth')
    frente = 1.0 if (sum(c.z for c in ev) / max(len(ev), 1)) > zmed else -1.0
    xs = sorted(c.x for c in ev); xm = xs[len(xs) // 2]
    izq = [c for c in ev if c.x < xm]; der = [c for c in ev if c.x >= xm]
    cm_ = lambda L, ax: sum(getattr(c, ax) for c in L) / max(len(L), 1)
    ojo_i = (cm_(izq, 'x'), cm_(izq, 'y')); ojo_d = (cm_(der, 'x'), cm_(der, 'y')); ojo_y = (ojo_i[1] + ojo_d[1]) / 2
    boca_y = cm_(dv, 'y') if dv else ojo_y - 6.0
    D = max(ojo_y - boca_y, 3.0)
    def sup(x, y):                                                           # punto real de la superficie de la cara (el más al frente cerca de x, y)
        cand = [c for c in cs if abs(c.x - x) < 0.7 and abs(c.y - y) < 0.7]
        if not cand: cand = sorted(cs, key=lambda c: (c.x - x) ** 2 + (c.y - y) ** 2)[:6]
        return max(cand, key=lambda c: c.z * frente)
    todos = [v.co for v in ob.data.vertices]
    LO = Vector((min(c.x for c in todos), min(c.y for c in todos), min(c.z for c in todos))); HI = Vector((max(c.x for c in todos), max(c.y for c in todos), max(c.z for c in todos))); SZ = HI - LO
    nt = material.node_tree; bs = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'); ent = bs.inputs['Base Color']
    origen = ent.links[0].from_socket if ent.links else None; val = tuple(ent.default_value)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    def gauss(cx, cy, ax, ay, ang, estrias=0.0):
        c = sup(cx, cy)
        cn = ((c.x - LO.x) / SZ.x, (c.y - LO.y) / SZ.y, (c.z - LO.z) / SZ.z)                 # centro en coordenadas «generadas» (0–1 del modelo en reposo: no siguen la pose)
        rs = nt.nodes.new('ShaderNodeVectorMath'); rs.operation = 'SUBTRACT'; rs.inputs[1].default_value = cn; nt.links.new(tc.outputs['Generated'], rs.inputs[0])
        a_cm = nt.nodes.new('ShaderNodeVectorMath'); a_cm.operation = 'MULTIPLY'; a_cm.inputs[1].default_value = (SZ.x, SZ.y, SZ.z); nt.links.new(rs.outputs[0], a_cm.inputs[0])
        rot = nt.nodes.new('ShaderNodeVectorRotate'); rot.rotation_type = 'Z_AXIS'; rot.inputs['Angle'].default_value = -ang; nt.links.new(a_cm.outputs[0], rot.inputs['Vector'])
        dv_ = nt.nodes.new('ShaderNodeVectorMath'); dv_.operation = 'DIVIDE'; dv_.inputs[1].default_value = (ax, ay, 1.4); nt.links.new(rot.outputs[0], dv_.inputs[0])
        class _M: pass
        mp = _M(); mp.outputs = [dv_.outputs[0]]
        ln = nt.nodes.new('ShaderNodeVectorMath'); ln.operation = 'LENGTH'; nt.links.new(mp.outputs[0], ln.inputs[0])
        sq = nt.nodes.new('ShaderNodeMath'); sq.operation = 'MULTIPLY'; nt.links.new(ln.outputs['Value'], sq.inputs[0]); nt.links.new(ln.outputs['Value'], sq.inputs[1])
        ng = nt.nodes.new('ShaderNodeMath'); ng.operation = 'MULTIPLY'; ng.inputs[1].default_value = -1.0; nt.links.new(sq.outputs[0], ng.inputs[0])
        ex = nt.nodes.new('ShaderNodeMath'); ex.operation = 'EXPONENT'; nt.links.new(ng.outputs[0], ex.inputs[0])
        g = ex.outputs[0]
        if estrias > 0:                                                      # estrías del roce de los dedos
            wv = nt.nodes.new('ShaderNodeTexWave'); wv.wave_type = 'BANDS'; wv.bands_direction = 'Y'; wv.inputs['Scale'].default_value = 3.2; wv.inputs['Distortion'].default_value = 1.6; wv.inputs['Detail'].default_value = 1.0
            nt.links.new(mp.outputs[0], wv.inputs['Vector'])
            mw = nt.nodes.new('ShaderNodeMath'); mw.operation = 'MULTIPLY_ADD'; mw.inputs[1].default_value = estrias; mw.inputs[2].default_value = 1.0 - estrias
            nt.links.new(wv.outputs['Fac'], mw.inputs[0])
            pr = nt.nodes.new('ShaderNodeMath'); pr.operation = 'MULTIPLY'; nt.links.new(g, pr.inputs[0]); nt.links.new(mw.outputs[0], pr.inputs[1]); g = pr.outputs[0]
        return g
    def suma(lista):
        acc = lista[0]
        for g in lista[1:]:
            n = nt.nodes.new('ShaderNodeMath'); n.operation = 'ADD'; nt.links.new(acc, n.inputs[0]); nt.links.new(g, n.inputs[1]); acc = n.outputs[0]
        cl = nt.nodes.new('ShaderNodeClamp'); nt.links.new(acc, cl.inputs[0]); return cl.outputs[0]
    def esc_(g, k):
        n = nt.nodes.new('ShaderNodeMath'); n.operation = 'MULTIPLY'; n.inputs[1].default_value = k; nt.links.new(g, n.inputs[0]); return n.outputs[0]
    # manchas de roce (cm del modelo; ax/ay = semiejes; ang en rad)
    manchas = [esc_(gauss(ojo_i[0] - 0.6, ojo_y - 0.55 * D, 2.6, 1.0, -0.35, 0.55), 1.0),               # mejilla
               esc_(gauss(ojo_d[0] + 0.4, boca_y + 0.60 * D, 2.0, 0.85, 0.50, 0.55), 1.0),              # mandíbula del otro lado
               esc_(gauss((ojo_i[0] + ojo_d[0]) / 2 + 0.3, boca_y - 0.62 * D, 1.8, 0.75, 0.08, 0.5), 1.0),   # mentón
               esc_(gauss(ojo_i[0] - 1.2, ojo_y + 0.55 * D, 1.6, 0.70, 0.55, 0.5), 0.95),               # sien
               esc_(gauss(ojo_d[0] + 0.9, ojo_y - 0.15 * D, 1.5, 0.65, -0.4, 0.5), 0.95),               # pómulo del otro lado
               esc_(gauss((ojo_i[0] + ojo_d[0]) / 2 + 0.2, ojo_y + 0.05 * D, 0.55, 1.3, 0.1, 0.0), 0.65),   # puente de la nariz (se la tocó)
               esc_(gauss(ojo_d[0] + 0.5, ojo_y + 0.62 * D, 1.4, 0.55, 0.3, 0.5), 0.85)]               # roce en la frente del otro lado
    heridas = [esc_(gauss(ojo_d[0] + 0.7, ojo_y - 0.30 * D, 0.75, 0.16, -0.5), 0.85), gauss(ojo_i[0] + 0.6, ojo_y + 0.60 * D, 1.05, 0.22, 0.35), esc_(gauss(ojo_i[0] + 0.6, ojo_y + 0.60 * D, 1.8, 0.65, 0.35), 0.55),
               esc_(gauss(ojo_i[0] + 0.4, ojo_y + 0.60 * D - 0.95, 0.16, 0.34, 0.1), 0.75)]                # la heridita y una gotita corta (sin chorro)
    M_s = suma(manchas); M_h = suma(heridas)
    M_s.node.name = 'DBG_Ms'; M_h.node.name = 'DBG_Mh'
    amt = nt.nodes.new('ShaderNodeMath'); amt.operation = 'MULTIPLY'; amt.inputs[0].default_value = 1.0; amt.inputs[1].default_value = 1.0; amt.name = 'AmtSangreCara'
    d1 = amt.inputs[0].driver_add('default_value'); d1.driver.type = 'SCRIPTED'; d1.driver.expression = f'min(max((frame - {f_imp}) / 24.0, 0.0), 1.0)'
    def x_amt(g):
        n = nt.nodes.new('ShaderNodeMath'); n.operation = 'MULTIPLY'; nt.links.new(g, n.inputs[0]); nt.links.new(amt.outputs[0], n.inputs[1]); return n.outputs[0]
    m_s2 = x_amt(M_s); m_h2 = x_amt(M_h)
    mx1 = nt.nodes.new('ShaderNodeMix'); mx1.data_type = 'RGBA'; _rgba(mx1, 'B').default_value = (0.12, 0.005, 0.007, 1)
    if origen: nt.links.new(origen, _rgba(mx1, 'A'))
    else: _rgba(mx1, 'A').default_value = val
    nt.links.new(m_s2, mx1.inputs['Factor'])
    mx2 = nt.nodes.new('ShaderNodeMix'); mx2.data_type = 'RGBA'; _rgba(mx2, 'B').default_value = (0.045, 0.0, 0.002, 1)
    nt.links.new(mx1.outputs['Result'], _rgba(mx2, 'A')); nt.links.new(m_h2, mx2.inputs['Factor'])
    nt.links.new(mx2.outputs['Result'], ent)
    rg = nt.nodes.new('ShaderNodeMix'); rg.data_type = 'FLOAT'; rg.inputs['A'].default_value = bs.inputs['Roughness'].default_value; rg.inputs['B'].default_value = 0.20
    mm_ = nt.nodes.new('ShaderNodeMath'); mm_.operation = 'MAXIMUM'; nt.links.new(m_s2, mm_.inputs[0]); nt.links.new(m_h2, mm_.inputs[1])
    nt.links.new(mm_.outputs[0], rg.inputs['Factor']); nt.links.new(rg.outputs['Result'], bs.inputs['Roughness'])
    print('sangre del rostro lista (3D): ojo_y', round(ojo_y, 1), 'boca_y', round(boca_y, 1), 'D', round(D, 1), 'frente', frente)
