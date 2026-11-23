"""Prueba: retarget de un clip de Mixamo sobre el esqueleto estándar de un personaje CC4 (FBX) y fotos de 4 cuadros. Uso: python mix.py -- fbxPersonaje clipMixamo prefijo"""
import bpy, sys, math, os, bmesh
from mathutils import Vector
sys.path.insert(0,'/home/user/personajes_c3')
import retarget_dir as RT
a=sys.argv[sys.argv.index('--')+1:]
fbx,clip,pref=a[0],a[1],a[2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx)
dst=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
nuevos_d=set(bpy.data.objects)
antes=set(bpy.data.objects); acc0=set(bpy.data.actions)
bpy.ops.import_scene.fbx(filepath=clip, automatic_bone_orientation=False)
src=[o for o in bpy.data.objects if o not in antes and o.type=='ARMATURE'][0]
acc=[x for x in bpy.data.actions if x not in acc0][0]
M={'Hips':'Hip','Spine':'Waist','Spine1':'Spine01','Spine2':'Spine02','Neck':'NeckTwist01','Head':'Head','LeftShoulder':'L_Clavicle','LeftArm':'L_Upperarm','LeftForeArm':'L_Forearm','LeftHand':'L_Hand',
   'RightShoulder':'R_Clavicle','RightArm':'R_Upperarm','RightForeArm':'R_Forearm','RightHand':'R_Hand','LeftUpLeg':'L_Thigh','LeftLeg':'L_Calf','LeftFoot':'L_Foot','LeftToeBase':'L_ToeBase',
   'RightUpLeg':'R_Thigh','RightLeg':'R_Calf','RightFoot':'R_Foot','RightToeBase':'R_ToeBase'}
for lado,l in (('Left','L'),('Right','R')):
    for d,n in (('Thumb','Thumb'),('Index','Index'),('Middle','Mid'),('Ring','Ring'),('Pinky','Pinky')):
        for i in (1,2,3): M[f'{lado}Hand{d}{i}']=f'{l}_{n}{i}'
pref_d='EM3D_Base_'
nombres={pref_d+v:'mixamorig:'+k for k,v in M.items() if ('mixamorig:'+k) in src.pose.bones and (pref_d+v) in dst.pose.bones}
print('MAPEADOS',len(nombres),'de',len(M))
# orientación: hacia dónde miran los pies en reposo (mundo)
def frente(arm,b,t):
    return (arm.matrix_world@arm.pose.bones[b].tail - arm.matrix_world@arm.pose.bones[t].head)
bpy.context.view_layer.update()
fd=(dst.matrix_world@dst.data.bones[pref_d+'L_ToeBase'].head_local)-(dst.matrix_world@dst.data.bones[pref_d+'L_Foot'].head_local)
fs=(src.matrix_world@src.data.bones['mixamorig:LeftToeBase'].head_local)-(src.matrix_world@src.data.bones['mixamorig:LeftFoot'].head_local)
ang=math.atan2(fd.y,fd.x)-math.atan2(fs.y,fs.x)
print('GIRO_Z',round(math.degrees(ang),1),[round(x,2) for x in fd],[round(x,2) for x in fs])
f0,f1=int(acc.frame_range[0]),min(int(acc.frame_range[1]),int(acc.frame_range[0])+int(a[3]) if len(a)>3 else int(acc.frame_range[1]))
nueva=RT.retarget(src,acc,dst,'clip',hueso_cadera=pref_d+'Hip',cadera_origen='mixamorig:Hips',nombres=nombres,fotogramas=(f0,f1),giro_z=ang)
dst.animation_data.action=nueva
for o in list(bpy.data.objects):
    if o.type=='ARMATURE' and o is src: bpy.data.objects.remove(o)
print('FRAMES',f0,f1,'desp',[round(x,2) for x in nueva.get('desplazamiento_cadera_m',[0,0,0])])
# ── EVA holograma: material transparente/emisivo en TODAS las mallas (cuerpo, pelo, ojos, dientes…), traje holográfico de una pieza
sc=bpy.context.scene
def mat_holo(nombre,color=(0.15,0.75,1.0),fuerza=2.2,alfa=0.55,difw=1.0):
    m=bpy.data.materials.new(nombre); m.use_nodes=True; nt=m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out=nt.nodes.new('ShaderNodeOutputMaterial')
    lw=nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value=0.4
    pw=nt.nodes.new('ShaderNodeMath'); pw.operation='POWER'; pw.inputs[1].default_value=2.2
    geo=nt.nodes.new('ShaderNodeNewGeometry')
    sep=nt.nodes.new('ShaderNodeSeparateXYZ')
    wv=nt.nodes.new('ShaderNodeMath'); wv.operation='MULTIPLY'; wv.inputs[1].default_value=380.0     # líneas de barrido horizontales
    sn=nt.nodes.new('ShaderNodeMath'); sn.operation='SINE'
    lin=nt.nodes.new('ShaderNodeMapRange'); lin.inputs['From Min'].default_value=-1; lin.inputs['From Max'].default_value=1; lin.inputs['To Min'].default_value=0.55; lin.inputs['To Max'].default_value=1.0
    dif=nt.nodes.new('ShaderNodeBsdfDiffuse'); dif.inputs['Color'].default_value=(min(1,color[0]*0.35*difw),min(1,color[1]*0.55*difw),min(1,color[2]*0.7*difw),1)
    em=nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value=(*color,1)
    mul=nt.nodes.new('ShaderNodeMath'); mul.operation='MULTIPLY'
    add=nt.nodes.new('ShaderNodeMath'); add.operation='ADD'; add.inputs[1].default_value=0.35
    emi=nt.nodes.new('ShaderNodeMath'); emi.operation='MULTIPLY'; emi.inputs[1].default_value=fuerza
    em2=nt.nodes.new('ShaderNodeEmission'); em2.inputs['Color'].default_value=(*color,1)
    ad=nt.nodes.new('ShaderNodeAddShader')
    tr=nt.nodes.new('ShaderNodeBsdfTransparent')
    mz=nt.nodes.new('ShaderNodeMixShader')
    L=nt.links.new
    L(lw.outputs['Facing'],pw.inputs[0])
    L(geo.outputs['Position'],sep.inputs[0])
    L(sep.outputs['Z'],wv.inputs[0]); L(wv.outputs[0],sn.inputs[0]); L(sn.outputs[0],lin.inputs['Value'])
    L(pw.outputs[0],add.inputs[0])
    L(add.outputs[0],mul.inputs[0]); L(lin.outputs['Result'],mul.inputs[1])
    L(mul.outputs[0],emi.inputs[0]); L(emi.outputs[0],em2.inputs['Strength'])
    L(em2.outputs[0],ad.inputs[0]); L(dif.outputs[0],ad.inputs[1])
    fa=nt.nodes.new('ShaderNodeMath'); fa.operation='MULTIPLY_ADD'; fa.inputs[1].default_value=0.75; fa.inputs[2].default_value=alfa; fa.use_clamp=True
    L(pw.outputs[0],fa.inputs[0]); L(fa.outputs[0],mz.inputs['Fac'])
    L(tr.outputs[0],mz.inputs[1]); L(ad.outputs[0],mz.inputs[2])
    L(mz.outputs[0],out.inputs['Surface'])
    m.blend_method='BLEND' if hasattr(m,'blend_method') else None
    return m
holo=mat_holo('holograma_EVA',(0.15,0.75,1.0),2.0,0.14)
holo_cara=mat_holo('holograma_EVA_cara',(0.2,0.8,1.0),1.4,0.5,2.2)
holo_ojo=mat_holo('holograma_EVA_ojo',(0.7,0.95,1.0),3.0,0.5)
def mat_ojo(lado):
    m=bpy.data.materials.new('holo_ojo_'+lado); m.use_nodes=True; nt=m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out=nt.nodes.new('ShaderNodeOutputMaterial'); tx=nt.nodes.new('ShaderNodeTexImage')
    img=next((i for i in bpy.data.images if i.name.startswith('EM3D_Eye_'+lado+'_Diffuse') and i.size[0]>200),None) or next((i for i in bpy.data.images if 'Eye_' in i.name and 'Diffuse' in i.name and 'Occl' not in i.name and i.size[0]>200),None)
    print('IMG_OJO',lado,img.name if img else None)
    tx.image=img
    em=nt.nodes.new('ShaderNodeEmission'); em.inputs['Strength'].default_value=2.2
    tint=nt.nodes.new('ShaderNodeMix'); tint.data_type='RGBA'; tint.blend_type='MULTIPLY'; tint.inputs[0].default_value=1.0; tint.inputs[7].default_value=(0.55,0.9,1.0,1)
    nt.links.new(tx.outputs['Color'],tint.inputs[6]); nt.links.new(tint.outputs[2],em.inputs['Color']); nt.links.new(em.outputs[0],out.inputs['Surface'])
    return m
def mat_clara():
    m=bpy.data.materials.new('holo_cornea'); m.use_nodes=True; nt=m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out=nt.nodes.new('ShaderNodeOutputMaterial'); tr=nt.nodes.new('ShaderNodeBsdfTransparent'); nt.links.new(tr.outputs[0],out.inputs['Surface']); return m

meshes=[o for o in bpy.data.objects if o.type=='MESH']
for o in meshes:
    n=o.name
    if n in ('Bra','Underwear_Bottoms') or 'Boxers' in n: o.hide_render=True; continue
    if n.endswith('Eye'):
        for sl in o.material_slots:
            nm=sl.material.name if sl.material else ''
            sl.material=mat_clara() if 'Cornea' in nm else mat_ojo('R' if nm.endswith('_R') else 'L')
        continue
    if 'Teeth' in n or 'Tongue' in n:
        mats=[holo_ojo]
    else:
        mats=[holo]
    for sl in o.material_slots:
        nm=sl.material.name if sl.material else ''
        sl.material=holo_cara if nm.startswith(('EM3D_Skin_Head','EMS_Skin_Head')) else mats[0]
    o.visible_shadow=False if hasattr(o,'visible_shadow') else None
# traje holográfico (cuerpo sin cabeza/manos/pies, inflado 1 cm)
body=next(o for o in meshes if o.name.endswith('Base_Body'))
vg=[g.name for g in body.vertex_groups]
def conservar(n):
    n=n.replace('EM3D_Base_','')
    if n.startswith(('Head','Neck','L_Hand','R_Hand','L_Foot','R_Foot','L_Toe','R_Toe','FacialBone','Jaw','Eye','L_Eye','R_Eye','Tongue','Teeth','UpperJaw')): return False
    return n.startswith(('Hip','Pelvis','Waist','Spine','L_Thigh','R_Thigh','L_Calf','R_Calf','L_Knee','R_Knee','L_Upperarm','R_Upperarm','L_Forearm','R_Forearm','L_Clavicle','R_Clavicle','L_Elbow','R_Elbow','L_Ribs','R_Ribs','L_Breast','R_Breast'))
keep={i for i,g in enumerate(vg) if conservar(g)}
dup=body.copy(); dup.data=body.data.copy(); dup.name='TRAJE_HOLO'; sc.collection.objects.link(dup)
dup.shape_key_clear()
bm=bmesh.new(); bm.from_mesh(dup.data); dl=bm.verts.layers.deform.active
borrar=[]
for v in bm.verts:
    d=v[dl]
    if not d: borrar.append(v); continue
    mejor=max(d.items(), key=lambda kv: kv[1])[0]
    if mejor not in keep: borrar.append(v)
bmesh.ops.delete(bm,geom=borrar,context='VERTS'); bm.normal_update()
for v in bm.verts: v.co+=v.normal*0.010
bm.to_mesh(dup.data); bm.free()
dup.data.materials.clear(); dup.data.materials.append(mat_holo('holo_traje',(0.1,0.55,1.0),2.2,0.16))
dup.visible_shadow=False
# expresión facial animada (parpadeo, habla, sonrisa leve) sobre las shape keys
mesh_sk=[o for o in meshes if o.data.shape_keys and o is not dup]
def clave(nombre,vals):
    for ob in mesh_sk:
        k=ob.data.shape_keys
        if nombre in k.key_blocks:
            for fr,v in vals:
                k.key_blocks[nombre].value=v; k.key_blocks[nombre].keyframe_insert('value',frame=fr)
n=f1-f0
for t in range(0,n,10):
    clave('V_Open',[(f0+t,0),(f0+t+4,0.8),(f0+t+8,0.1)])
clave('Mouth_Smile',[(f0,0.3),(f1,0.3)])
clave('Eyes_Blink',[(f0,0),(f0+20,0),(f0+22,1),(f0+25,0),(f0+60,0),(f0+62,1),(f0+65,0)])
# mandíbula acompaña (hueso)
jaw=dst.pose.bones.get('EM3D_Base_JawRoot')
sc.frame_start=f0; sc.frame_end=f1
# render
sc.render.engine='CYCLES'; sc.cycles.device='CPU'; sc.cycles.samples=24; sc.cycles.use_denoising=True; sc.cycles.max_bounces=8; sc.cycles.transparent_max_bounces=16
sc.view_settings.view_transform='Khronos PBR Neutral'; sc.render.resolution_x=360; sc.render.resolution_y=480
w=bpy.data.worlds.new('w'); w.use_nodes=True; w.node_tree.nodes['Background'].inputs[0].default_value=(0.01,0.015,0.03,1); sc.world=w
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera=cam
cam.data.lens=50
mostrar=[f0+int((f1-f0)*u) for u in (0.05,0.3,0.55,0.8)]
for k,fr in enumerate(mostrar):
    sc.frame_set(fr)
    cadera=dst.matrix_world@dst.pose.bones[pref_d+'Hip'].head
    cam.location=(cadera.x,cadera.y-3.7,1.0); cam.rotation_euler=(math.radians(90),0,0); cam.data.lens=35
    sc.render.filepath=f'/home/user/personajes_c3/fotos/{pref}_cuerpo{k}.png'; bpy.ops.render.render(write_still=True)
    cab=dst.matrix_world@dst.pose.bones[pref_d+'Head'].head
    cam.location=(cab.x,cab.y-0.9,cab.z+0.02); cam.rotation_euler=(math.radians(90),0,0); cam.data.lens=60
    sc.render.filepath=f'/home/user/personajes_c3/fotos/{pref}_cara{k}.png'; bpy.ops.render.render(write_still=True)
    print('RENDER',fr,flush=True)
