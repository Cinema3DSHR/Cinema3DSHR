"""Colores reales para los personajes CC4 en su versión FBX (materiales Principled): piel, pelo, cejas, pestañas, ojos, labios. Se aplica por nombre de material."""
import bpy

def _principled(m):
    return next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'), None)

def _tintar(m, color, fuerza=1.0):
    """Si el Base Color viene de una imagen, se multiplica por el tinte; si no, se fija el color."""
    p=_principled(m)
    if not p: return False
    bc=p.inputs['Base Color']
    if bc.is_linked:
        src=bc.links[0].from_socket
        mix=m.node_tree.nodes.new('ShaderNodeMix'); mix.data_type='RGBA'; mix.blend_type='MULTIPLY'
        mix.inputs[0].default_value=fuerza; mix.inputs[7].default_value=(*color,1.0)
        m.node_tree.links.new(src,mix.inputs[6]); m.node_tree.links.new(mix.outputs[2],bc)
    else:
        bc.default_value=(*color,1.0)
    return True

def aplicar(piel, pelo, ceja=None, pestana=(0.02,0.015,0.012), iris=None, labios=None):
    ceja=ceja or tuple(c*0.7 for c in pelo)
    log=[]
    for m in bpy.data.materials:
        if not m.use_nodes: continue
        n=m.name
        if n.startswith(('EM3D_Skin','EMS_Skin')): ok=_tintar(m,piel)
        elif n.startswith(('Hair','Scalp','Slicked')): ok=_tintar(m,pelo)
        elif n.startswith(('Eyebrows','Female_Flat')): ok=_tintar(m,ceja)
        elif n.startswith(('EM3D_Eyelash','EMS_Eyelash')): ok=_tintar(m,pestana)
        elif n in ('EM3D_Nails','EMS_Nails'): ok=_tintar(m,tuple(min(1,c*1.05) for c in piel))
        else: continue
        log.append((n,ok))
    return log
