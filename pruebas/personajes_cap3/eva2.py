"""Prueba: retarget de un clip de Mixamo sobre el esqueleto estándar de un personaje CC4 (FBX) y fotos de 4 cuadros. Uso: python mix.py -- fbxPersonaje clipMixamo prefijo"""
import bpy, sys, math, os, bmesh
from mathutils import Vector
sys.path.insert(0,'/home/user/cap3'); sys.path.insert(0,'/home/user/personajes_c3')
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

import colores, holo_eva as H
from mathutils import Vector
sc=bpy.context.scene
colores.aplicar(piel=(0.88,0.66,0.55),pelo=(0.55,0.58,0.65),ceja=(0.35,0.37,0.42))
for o in bpy.data.objects:
    if o.name in ('Bra','Underwear_Bottoms','Boxers'): o.hide_render=True
meshes=[o for o in bpy.data.objects if o.type=='MESH' and not o.hide_render]
body=next(o for o in meshes if o.name.endswith('Base_Body'))
# uniforme real (se construye del cuerpo, igual que el holograma lo envuelve)
vg=[g.name for g in body.vertex_groups]
def conservar(n):
    n=n.replace('EM3D_Base_','')
    if n.startswith(('Head','Neck','L_Hand','R_Hand','L_Foot','R_Foot','L_Toe','R_Toe','FacialBone','Jaw','Eye','L_Eye','R_Eye','Tongue','Teeth','UpperJaw')): return False
    return n.startswith(('Hip','Pelvis','Waist','Spine','L_Thigh','R_Thigh','L_Calf','R_Calf','L_Knee','R_Knee','L_Upperarm','R_Upperarm','L_Forearm','R_Forearm','L_Clavicle','R_Clavicle','L_Elbow','R_Elbow','L_Ribs','R_Ribs','L_Breast','R_Breast'))
keep={i for i,g in enumerate(vg) if conservar(g)}
dup=body.copy(); dup.data=body.data.copy(); dup.name='UNIFORME_EVA'; sc.collection.objects.link(dup); dup.shape_key_clear()
bm=bmesh.new(); bm.from_mesh(dup.data); dl=bm.verts.layers.deform.active
borrar=[v for v in bm.verts if (not v[dl]) or max(v[dl].items(), key=lambda kv: kv[1])[0] not in keep]
bmesh.ops.delete(bm,geom=borrar,context='VERTS'); bm.normal_update()
for v in bm.verts: v.co+=v.normal*0.010
bm.to_mesh(dup.data); bm.free()
dup.data.materials.clear(); t=bpy.data.materials.new('uniforme_eva'); t.use_nodes=True
p=t.node_tree.nodes['Principled BSDF']; p.inputs['Base Color'].default_value=(0.82,0.86,0.92,1); p.inputs['Roughness'].default_value=0.35
dup.data.materials.append(t)
for pol in dup.data.polygons: pol.use_smooth=True
meshes=[o for o in bpy.data.objects if o.type=='MESH' and not o.hide_render]
H.preparar(meshes)
# línea de tiempo del holograma
alt=1.9
H.clave('reveal',[(f0,0.0),(f0+26,alt),(f1-22,alt),(f1,0.0)])
H.clave('real',[(f0,-1.0),(f0+34,-1.0),(f0+58,alt),(f1-26,alt),(f1-22,-1.0)])
fl=[(f0+28,1),(f0+30,0.35),(f0+32,1),(f0+34,0.5),(f0+36,1),(f0+60,1),(f0+61,0.25),(f0+63,1),(f0+64,0.6),(f0+66,1),(f1-30,1),(f1-28,0.3),(f1-26,1),(f1-24,0.4),(f1-22,1)]
H.clave('flick',[(f0,1)]+fl+[(f1,1)])
# habla (visemas) y parpadeo
mesh_sk=[o for o in meshes if o.data.shape_keys]
def clave_sk(nombre,vals):
    for ob in mesh_sk:
        k=ob.data.shape_keys
        if k.animation_data and k.animation_data.action and 'Calibration' in k.animation_data.action.name: k.animation_data.action=None
        if nombre in k.key_blocks:
            for fr,v in vals:
                k.key_blocks[nombre].value=v; k.key_blocks[nombre].keyframe_insert('value',frame=fr)
for t_ in range(f0+60,f1-30,9): clave_sk('V_Open',[(t_,0),(t_+3,0.8),(t_+6,0.1)])
clave_sk('Eyes_Blink',[(f0+70,0),(f0+72,1),(f0+75,0)])
sc.frame_start=f0; sc.frame_end=f1
sc.render.engine='CYCLES'; sc.cycles.device='CPU'; sc.cycles.samples=24; sc.cycles.use_denoising=True; sc.cycles.transparent_max_bounces=24
sc.view_settings.view_transform='Khronos PBR Neutral'; sc.render.resolution_x=300; sc.render.resolution_y=420
w=bpy.data.worlds.new('w'); w.use_nodes=True; w.node_tree.nodes['Background'].inputs[0].default_value=(0.02,0.03,0.05,1); sc.world=w
def luz(nm,loc,e,col):
    l=bpy.data.lights.new(nm,'AREA'); l.energy=e; l.size=2.0; l.color=col
    o=bpy.data.objects.new(nm,l); sc.collection.objects.link(o); o.location=loc
    o.rotation_euler=(Vector((0,0,1.0))-Vector(loc)).to_track_quat('-Z','Y').to_euler()
luz('k',(-1.4,-2.5,2.0),90,(1,0.95,0.9)); luz('f',(1.8,-2.0,1.0),40,(0.6,0.8,1)); luz('r',(0,2.0,2.2),70,(0.5,0.8,1))
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera=cam
import os; os.makedirs('/home/user/cap3/fotos',exist_ok=True)
mostrar=[f0+11,f0+23,f0+36,f0+48,f0+62,f0+70,f1-28,f1-10]
for k,fr in enumerate(mostrar):
    sc.frame_set(fr)
    cad=dst.matrix_world@dst.pose.bones[pref_d+'Hip'].head
    cam.data.sensor_fit='VERTICAL'; cam.data.sensor_height=24; cam.data.lens=34
    cam.location=(cad.x,cad.y-3.6,0.95); cam.rotation_euler=(math.radians(90),0,0)
    sc.render.filepath=f'/home/user/cap3/fotos/{pref}_{k}.png'; bpy.ops.render.render(write_still=True); print('RENDER',fr,flush=True)
