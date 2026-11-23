"""Traje espacial futurista con botas para los personajes CC4 (esqueleto FBX de 101 huesos): mono ajustado de tela técnica + placas, hombreras, brazales, cinturón,
rodilleras, cuello y botas altas con suela; vivos celestes emisivos. Todo lo rígido va parentado a huesos (se mueve con las animaciones); mono y botas se
generan del propio cuerpo (heredan pesos, se deforman). Frente del personaje = −Y mundo en reposo."""
import bpy, bmesh, math
from mathutils import Vector, Matrix

NAVY=(0.035,0.055,0.095)
PLACA=(0.62,0.66,0.72)
CYAN=(0.1,0.75,1.0)

def mat_tela():
    m=bpy.data.materials.new('traje_tela'); m.use_nodes=True; nt=m.node_tree
    p=nt.nodes['Principled BSDF']; p.inputs['Base Color'].default_value=(*NAVY,1); p.inputs['Roughness'].default_value=0.5
    try: p.inputs['Sheen Weight'].default_value=0.4
    except Exception: pass
    br=nt.nodes.new('ShaderNodeTexBrick'); br.inputs['Scale'].default_value=7.0; br.inputs['Mortar Size'].default_value=0.012; br.inputs['Mortar Smooth'].default_value=0.3; br.inputs['Bias'].default_value=0.0
    br.inputs['Color1'].default_value=(0.045,0.07,0.115,1); br.inputs['Color2'].default_value=(0.04,0.062,0.105,1); br.inputs['Mortar'].default_value=(0.01,0.015,0.03,1)
    nt.links.new(br.outputs['Color'],p.inputs['Base Color'])
    ns=nt.nodes.new('ShaderNodeTexNoise'); ns.inputs['Scale'].default_value=900.0; ns.inputs['Detail'].default_value=1.0
    nt.links.new(nt.nodes['Texture Coordinate'].outputs['Object'] if 'Texture Coordinate' in nt.nodes else nt.nodes.new('ShaderNodeTexCoord').outputs['Object'],br.inputs['Vector'])
    bp=nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value=0.12
    tc=nt.nodes.new('ShaderNodeTexCoord')
    nt.links.new(tc.outputs['Object'],ns.inputs['Vector']); nt.links.new(ns.outputs['Fac'],bp.inputs['Height']); nt.links.new(bp.outputs['Normal'],p.inputs['Normal'])
    return m
def mat_placa():
    m=bpy.data.materials.new('traje_placa'); m.use_nodes=True; p=m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value=(*PLACA,1); p.inputs['Metallic'].default_value=0.75; p.inputs['Roughness'].default_value=0.32
    return m
def mat_bota():
    m=bpy.data.materials.new('traje_bota'); m.use_nodes=True; p=m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value=(0.03,0.032,0.04,1); p.inputs['Roughness'].default_value=0.38
    try: p.inputs['Coat Weight'].default_value=0.3
    except Exception: pass
    return m
def mat_suela():
    m=bpy.data.materials.new('traje_suela'); m.use_nodes=True; p=m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value=(0.16,0.17,0.19,1); p.inputs['Roughness'].default_value=0.8
    return m
def mat_luz():
    m=bpy.data.materials.new('traje_luz'); m.use_nodes=True; nt=m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out=nt.nodes.new('ShaderNodeOutputMaterial'); em=nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value=(*CYAN,1); em.inputs['Strength'].default_value=4.0
    nt.links.new(em.outputs[0],out.inputs['Surface']); return m

def _region(sc, body, keep, off, nombre, mat, zmin=None, zmax=None):
    vg=[g.name for g in body.vertex_groups]
    k={i for i,g in enumerate(vg) if keep(g.replace('EM3D_Base_',''))}
    dup=body.copy(); dup.data=body.data.copy(); dup.name=nombre; sc.collection.objects.link(dup); dup.shape_key_clear()
    bm=bmesh.new(); bm.from_mesh(dup.data); dl=bm.verts.layers.deform.active
    mw=dup.matrix_world
    borrar=[]
    for v in bm.verts:
        d=v[dl]
        if not d: borrar.append(v); continue
        mejor=max(d.items(), key=lambda kv: kv[1])[0]
        z=(mw@v.co).z
        if mejor not in k or (zmin is not None and z<zmin) or (zmax is not None and z>zmax): borrar.append(v)
    bmesh.ops.delete(bm,geom=borrar,context='VERTS'); bm.normal_update()
    for v in bm.verts: v.co+=v.normal*off
    bm.to_mesh(dup.data); bm.free()
    dup.data.materials.clear(); dup.data.materials.append(mat)
    for p in dup.data.polygons: p.use_smooth=True
    return dup

def _al_hueso(arm, obj, hueso, mundo):
    """Pieza rígida que se deforma con el esqueleto como el resto del cuerpo (pesos 1.0 al hueso + modificador Armature): se exporta bien a GLB/Godot."""
    obj.parent = arm
    obj.matrix_parent_inverse = arm.matrix_world.inverted()
    obj.matrix_world = mundo
    vg = obj.vertex_groups.new(name=hueso)
    vg.add(list(range(len(obj.data.vertices))), 1.0, 'REPLACE')
    md = obj.modifiers.new('Armature', 'ARMATURE'); md.object = arm

def _caja(sc, nombre, dim, mundo, mat, bisel=0.012):
    bm=bmesh.new(); bmesh.ops.create_cube(bm,size=1.0)
    for v in bm.verts: v.co.x*=dim[0]; v.co.y*=dim[1]; v.co.z*=dim[2]
    bmesh.ops.bevel(bm,geom=list(bm.edges),offset=bisel,segments=2,affect='EDGES')
    me=bpy.data.meshes.new(nombre); bm.to_mesh(me); bm.free()
    o=bpy.data.objects.new(nombre,me); sc.collection.objects.link(o)
    for p in me.polygons: p.use_smooth=True
    me.materials.append(mat); return o
def _cil(sc, nombre, radio, largo, mat, seg=24):
    bm=bmesh.new(); bmesh.ops.create_cone(bm,cap_ends=True,segments=seg,radius1=radio,radius2=radio,depth=largo)
    me=bpy.data.meshes.new(nombre); bm.to_mesh(me); bm.free()
    o=bpy.data.objects.new(nombre,me); sc.collection.objects.link(o)
    for p in me.polygons: p.use_smooth=True
    me.materials.append(mat); return o
def _toro(sc, nombre, R, r, mat, esc=(1,1,1)):
    bm=bmesh.new()
    for i in range(48):
        a=2*math.pi*i/48
        for j in range(10):
            b=2*math.pi*j/10
            bm.verts.new(((R+r*math.cos(b))*math.cos(a),(R+r*math.cos(b))*math.sin(a),r*math.sin(b)))
    bm.verts.ensure_lookup_table()
    for i in range(48):
        for j in range(10):
            a1=bm.verts[i*10+j]; a2=bm.verts[((i+1)%48)*10+j]; a3=bm.verts[((i+1)%48)*10+(j+1)%10]; a4=bm.verts[i*10+(j+1)%10]
            bm.faces.new((a1,a2,a3,a4))
    for v in bm.verts: v.co.x*=esc[0]; v.co.y*=esc[1]
    me=bpy.data.meshes.new(nombre); bm.to_mesh(me); bm.free()
    o=bpy.data.objects.new(nombre,me); sc.collection.objects.link(o)
    for p in me.polygons: p.use_smooth=True
    me.materials.append(mat); return o

def construir(arm, body, P='EM3D_Base_', H=1.7, M=True):
    """PRIMERA PIEL futurista: mono ajustado de tela técnica con costuras de paneles, vivos de luz finos, cuello y botas a juego con suela. Sin placas ni armadura."""
    sc=bpy.context.scene
    bpy.context.view_layer.update()
    S=H/1.7
    def W(h,punta='head'):
        pb=arm.pose.bones[P+h]
        return arm.matrix_world@(pb.head if punta=='head' else pb.tail)
    tela,bota,suela,luz=mat_tela(),mat_bota(),mat_suela(),mat_luz()
    rodilla_z=(W('L_Calf').z+W('R_Calf').z)/2
    z_bota=rodilla_z*0.58                               # botas hasta media pantorrilla
    def mono(n): return n.startswith(('Hip','Pelvis','Waist','Spine','L_Thigh','R_Thigh','L_Calf','R_Calf','L_Knee','R_Knee','L_Upperarm','R_Upperarm','L_Forearm','R_Forearm','L_Clavicle','R_Clavicle','L_Elbow','R_Elbow','L_Ribs','R_Ribs','L_Breast','R_Breast','NeckTwist','Neck','Head','JawRoot','Tongue','L_Eye','R_Eye','UpperJaw'))
    pie=lambda n: n.startswith(('L_Calf','R_Calf','L_Foot','R_Foot','L_Toe','R_Toe','L_BigToe','R_BigToe','L_PinkyToe','R_PinkyToe','L_RingToe','R_RingToe','L_MidToe','R_MidToe','L_IndexToe','R_IndexToe'))
    piezas=[_region(sc,body,lambda n: mono(n) and not n.startswith(('L_Foot','R_Foot','L_Toe','R_Toe')),0.007*S,'TRAJE_MONO',tela,zmin=z_bota-0.03,zmax=W('NeckTwist01').z+0.025*S)]
    zank=0.115*S                                     # sobre el empeine: ahí termina la «zapatilla» y empieza la caña
    caña=_region(sc,body,lambda n: True,0.016*S,'TRAJE_BOTAS',bota,zmin=zank-0.035*S,zmax=z_bota)
    piezas.append(caña)
    # PIE: envolvente convexa de cada pie (dedos juntos en una sola punta redondeada, suela gruesa) con pesos tomados del vértice más cercano del cuerpo
    from mathutils import kdtree
    mw_b=body.matrix_world
    kd=kdtree.KDTree(len(body.data.vertices))
    for i,v in enumerate(body.data.vertices): kd.insert(mw_b@v.co,i)
    kd.balance()
    zbase=min((mw_b@v.co).z for v in body.data.vertices)
    for lado,sg in (('L',1),('R',-1)):
        bmh=bmesh.new()
        pts=[]
        for v in body.data.vertices:
            w=mw_b@v.co
            if w.z<zank+0.045*S and w.x*sg>0.005: pts.append(w.copy())
        for w in pts: bmh.verts.new(w)
        bmesh.ops.convex_hull(bmh,input=list(bmh.verts),use_existing_faces=False)
        bmesh.ops.recalc_face_normals(bmh,faces=list(bmh.faces))
        # engordar: hacia fuera del centro del pie + suela más baja
        c=sum(pts,Vector())/len(pts)
        for v in bmh.verts:
            d=v.co-c; d.z*=0.5
            v.co=v.co+d.normalized()*0.014*S
            if v.co.z<zbase+0.02*S: v.co.z=zbase-0.012*S
        me=bpy.data.meshes.new(f'PIE_{lado}'); bmh.to_mesh(me); bmh.free()
        o=bpy.data.objects.new(f'TRAJE_PIE_{lado}',me); sc.collection.objects.link(o)
        for pl in me.polygons: pl.use_smooth=True
        me.materials.append(bota)
        o.parent=arm; o.matrix_parent_inverse=arm.matrix_world.inverted()
        # pesos
        for v in me.vertices:
            _,idx,_d=kd.find(v.co)
            for g in body.data.vertices[idx].groups:
                nm=body.vertex_groups[g.group].name
                vg=o.vertex_groups.get(nm) or o.vertex_groups.new(name=nm)
                vg.add([v.index],g.weight,'REPLACE')
        md=o.modifiers.new('Armature','ARMATURE'); md.object=arm
        piezas.append(o)
    zf=zbase-0.012*S
    for lado in ('L','R'):
        pie_h=W(f'{lado}_Foot'); toe=W(f'{lado}_ToeBase','tail')
        largo=(Vector((toe.x,toe.y,0))-Vector((pie_h.x,pie_h.y,0))).length+0.09*S
        cen=Vector(((pie_h.x+toe.x)/2,(pie_h.y+toe.y)/2,zf-0.012*S))
        # franja de luz fina al costado de la bota
        sg=1 if lado=='L' else -1
        c2=Vector((pie_h.x+sg*0.043*S,pie_h.y-0.03*S,z_bota*0.55))
        tira=_caja(sc,f'BOTA_LUZ_{lado}',(0.004*S,0.003*S,0.15*S),Matrix.Translation(c2),luz,bisel=0.0008)
        _al_hueso(arm,tira,P+f'{lado}_Calf',Matrix.Translation(c2)); piezas.append(tira)
    # vivos finos del traje: costado del torso y del muslo; emblema plano al pecho
    sp1=W('Spine01'); sp2=W('Spine02')
    for sg in (-1,1):
        c=Vector((sp1.x+sg*0.118*S,sp1.y-0.045*S,sp1.z+0.04*S))
        v=_caja(sc,'VIVO_TORSO',(0.004*S,0.003*S,0.26*S),Matrix.Translation(c),luz,bisel=0.0008)
        _al_hueso(arm,v,P+'Spine01',Matrix.Translation(c)); piezas.append(v)
    for lado,sg in (('L',1),('R',-1)):
        t=W(f'{lado}_Thigh'); c=Vector((t.x+sg*0.062*S,t.y-0.01*S,t.z-0.14*S))
        v=_caja(sc,f'VIVO_PIERNA_{lado}',(0.004*S,0.003*S,0.24*S),Matrix.Translation(c),luz,bisel=0.0008)
        _al_hueso(arm,v,P+f'{lado}_Thigh',Matrix.Translation(c)); piezas.append(v)
    c=Vector((sp2.x,sp2.y-0.098*S,sp2.z+0.02*S))
    em=_caja(sc,'EMBLEMA',(0.038*S,0.004*S,0.038*S),Matrix.Translation(c),luz,bisel=0.004)
    _al_hueso(arm,em,P+'Spine02',Matrix.Translation(c)); piezas.append(em)
    return piezas
