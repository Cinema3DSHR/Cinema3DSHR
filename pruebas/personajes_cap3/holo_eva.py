"""EVA como holograma que se CONSTRUYE: aparece azul de abajo hacia arriba, se vuelve real (piel, pelo y ojos con sus colores y texturas), parpadea
como una proyección y se disuelve. Se aplica sobre los materiales del personaje (envoltorio por material, no se tocan las mallas ni el rig).
Uso desde Blender: import holo_eva as H; H.preparar(objetos, altura); H.clave('reveal', [(f,m),...]); H.clave('real', ...); H.clave('flick', ...)"""
import bpy, math

COLOR=(0.15,0.75,1.0)
_MATS=[]

def _val(nt,nombre):
    n=nt.nodes.new('ShaderNodeValue'); n.name=nombre; n.label=nombre; n.outputs[0].default_value=0.0
    return n

def _holo_shader(nt, alfa=0.55, difw=1.0, fuerza=2.0, tipo='cuerpo', imagen=None):
    """Devuelve el socket de salida del sombreador holográfico (borde brillante + líneas de barrido)."""
    if tipo=='nada':
        tr=nt.nodes.new('ShaderNodeBsdfTransparent'); return tr.outputs[0]
    if tipo=='ojo':
        tx=nt.nodes.new('ShaderNodeTexImage'); tx.image=imagen
        mul=nt.nodes.new('ShaderNodeMix'); mul.data_type='RGBA'; mul.blend_type='MULTIPLY'; mul.inputs[0].default_value=1.0; mul.inputs[7].default_value=(0.55,0.9,1.0,1)
        em=nt.nodes.new('ShaderNodeEmission'); em.inputs['Strength'].default_value=2.4
        nt.links.new(tx.outputs['Color'],mul.inputs[6]); nt.links.new(mul.outputs[2],em.inputs['Color'])
        return em.outputs[0]
    lw=nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value=0.4
    pw=nt.nodes.new('ShaderNodeMath'); pw.operation='POWER'; pw.inputs[1].default_value=2.0
    geo=nt.nodes.new('ShaderNodeNewGeometry'); sep=nt.nodes.new('ShaderNodeSeparateXYZ')
    wv=nt.nodes.new('ShaderNodeMath'); wv.operation='MULTIPLY'; wv.inputs[1].default_value=420.0
    sn=nt.nodes.new('ShaderNodeMath'); sn.operation='SINE'
    lin=nt.nodes.new('ShaderNodeMapRange'); lin.inputs['From Min'].default_value=-1; lin.inputs['From Max'].default_value=1; lin.inputs['To Min'].default_value=0.6; lin.inputs['To Max'].default_value=1.0
    dif=nt.nodes.new('ShaderNodeBsdfDiffuse'); dif.inputs['Color'].default_value=(min(1,COLOR[0]*0.35*difw),min(1,COLOR[1]*0.6*difw),min(1,COLOR[2]*0.75*difw),1)
    add=nt.nodes.new('ShaderNodeMath'); add.operation='ADD'; add.inputs[1].default_value=0.35
    mul=nt.nodes.new('ShaderNodeMath'); mul.operation='MULTIPLY'
    emi=nt.nodes.new('ShaderNodeMath'); emi.operation='MULTIPLY'; emi.inputs[1].default_value=fuerza
    em=nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value=(*COLOR,1)
    ad=nt.nodes.new('ShaderNodeAddShader'); tr=nt.nodes.new('ShaderNodeBsdfTransparent'); mz=nt.nodes.new('ShaderNodeMixShader')
    fa=nt.nodes.new('ShaderNodeMath'); fa.operation='MULTIPLY_ADD'; fa.inputs[1].default_value=0.7; fa.inputs[2].default_value=alfa; fa.use_clamp=True
    L=nt.links.new
    L(lw.outputs['Facing'],pw.inputs[0]); L(geo.outputs['Position'],sep.inputs[0]); L(sep.outputs['Z'],wv.inputs[0]); L(wv.outputs[0],sn.inputs[0]); L(sn.outputs[0],lin.inputs['Value'])
    L(pw.outputs[0],add.inputs[0]); L(add.outputs[0],mul.inputs[0]); L(lin.outputs['Result'],mul.inputs[1]); L(mul.outputs[0],emi.inputs[0]); L(emi.outputs[0],em.inputs['Strength'])
    L(em.outputs[0],ad.inputs[0]); L(dif.outputs[0],ad.inputs[1]); L(pw.outputs[0],fa.inputs[0]); L(fa.outputs[0],mz.inputs['Fac']); L(tr.outputs[0],mz.inputs[1]); L(ad.outputs[0],mz.inputs[2])
    return mz.outputs[0]

def envolver(m, tipo, imagen=None, alfa=0.55, difw=1.0):
    """Reemplaza la salida del material por: visible(reveal,flick) ⊗ mezcla(holograma → original según 'real')."""
    nt=m.node_tree
    out=next(n for n in nt.nodes if n.type=='OUTPUT_MATERIAL')
    orig=out.inputs['Surface'].links[0].from_socket
    geo=nt.nodes.new('ShaderNodeNewGeometry'); sep=nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(geo.outputs['Position'],sep.inputs[0])
    vrev=_val(nt,'reveal'); vreal=_val(nt,'real'); vflick=_val(nt,'flick'); vflick.outputs[0].default_value=1.0
    # máscara de aparición: z < reveal  (suavizada 1 cm) ; máscara de «ya es real»: z < real
    def corte(valor_node):
        sub=nt.nodes.new('ShaderNodeMath'); sub.operation='SUBTRACT'
        nt.links.new(valor_node.outputs[0],sub.inputs[0]); nt.links.new(sep.outputs['Z'],sub.inputs[1])
        mp=nt.nodes.new('ShaderNodeMapRange'); mp.clamp=True; mp.inputs['From Min'].default_value=0.0; mp.inputs['From Max'].default_value=0.012
        nt.links.new(sub.outputs[0],mp.inputs['Value'])
        return mp.outputs['Result'], sub
    vis, sub_rev = corte(vrev)
    rl, _ = corte(vreal)
    visf=nt.nodes.new('ShaderNodeMath'); visf.operation='MULTIPLY'; nt.links.new(vis,visf.inputs[0]); nt.links.new(vflick.outputs[0],visf.inputs[1])
    holo=_holo_shader(nt,alfa,difw,2.0,tipo,imagen)
    mix_real=nt.nodes.new('ShaderNodeMixShader'); nt.links.new(rl,mix_real.inputs['Fac']); nt.links.new(holo,mix_real.inputs[1]); nt.links.new(orig,mix_real.inputs[2])
    tr=nt.nodes.new('ShaderNodeBsdfTransparent')
    mix_vis=nt.nodes.new('ShaderNodeMixShader'); nt.links.new(visf.outputs[0],mix_vis.inputs['Fac']); nt.links.new(tr.outputs[0],mix_vis.inputs[1]); nt.links.new(mix_real.outputs[0],mix_vis.inputs[2])
    # línea brillante en el frente de aparición (|z-reveal| < 1,5 cm)
    ab=nt.nodes.new('ShaderNodeMath'); ab.operation='ABSOLUTE'; nt.links.new(sub_rev.outputs[0],ab.inputs[0])
    fr=nt.nodes.new('ShaderNodeMapRange'); fr.clamp=True; fr.inputs['From Min'].default_value=0.0; fr.inputs['From Max'].default_value=0.02; fr.inputs['To Min'].default_value=1.0; fr.inputs['To Max'].default_value=0.0
    nt.links.new(ab.outputs[0],fr.inputs['Value'])
    ge=nt.nodes.new('ShaderNodeMath'); ge.operation='MULTIPLY'; nt.links.new(fr.outputs['Result'],ge.inputs[0]); ge.inputs[1].default_value=9.0
    em=nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value=(0.7,0.95,1.0,1); nt.links.new(ge.outputs[0],em.inputs['Strength'])
    tot=nt.nodes.new('ShaderNodeAddShader'); nt.links.new(mix_vis.outputs[0],tot.inputs[0]); nt.links.new(em.outputs[0],tot.inputs[1])
    nt.links.new(tot.outputs[0],out.inputs['Surface'])
    _MATS.append(m)

def preparar(meshes):
    """Envuelve los materiales de las mallas del personaje según su tipo (cuerpo, ojos, dientes/lengua…)."""
    hechos=set()
    for o in meshes:
        n=o.name
        for sl in o.material_slots:
            m=sl.material
            if not m or m.name in hechos or not m.use_nodes: continue
            nm=m.name
            if n.endswith('Eye') and 'Cornea' in nm: tipo='nada'; img=None
            elif n.endswith('Eye'):
                tipo='ojo'; img=next((i for i in bpy.data.images if i.name.startswith('EM3D_Eye_R_Diffuse') and i.size[0]>200),None)
            elif any(k in n for k in ('Teeth','Tongue','EyeO','TearLine')): tipo='nada'; img=None
            elif nm.startswith(('EM3D_Skin_Head','EMS_Skin_Head')): tipo='cuerpo'; img=None
            else: tipo='cuerpo'; img=None
            envolver(m,tipo,img,alfa=0.62 if nm.startswith(('EM3D_Skin_Head','EMS_Skin_Head')) else 0.5, difw=2.2 if nm.startswith(('EM3D_Skin_Head','EMS_Skin_Head')) else 1.0)
            hechos.add(nm)

def clave(que, puntos):
    """que = 'reveal' | 'real' | 'flick'; puntos = [(cuadro, valor)]. Se anima el mismo valor en todos los materiales."""
    for m in _MATS:
        n=m.node_tree.nodes[que]
        for f,v in puntos:
            n.outputs[0].default_value=v
            n.outputs[0].keyframe_insert('default_value',frame=int(f))
    # interpolación lineal
    for m in _MATS:
        ad=m.node_tree.animation_data
        if ad and ad.action:
            from bpy_extras import anim_utils
            cb=anim_utils.action_get_channelbag_for_slot(ad.action,ad.action_slot)
            for fc in (cb.fcurves if cb else []):
                for kp in fc.keyframe_points: kp.interpolation='LINEAR'
