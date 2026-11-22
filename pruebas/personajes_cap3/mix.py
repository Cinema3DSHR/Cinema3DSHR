"""Prueba: retarget de un clip de Mixamo sobre el esqueleto estándar de un personaje CC4 (FBX) y fotos de 4 cuadros. Uso: python mix.py -- fbxPersonaje clipMixamo prefijo"""
import bpy, sys, math, os
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
# render
sc=bpy.context.scene
sc.render.engine='CYCLES'; sc.cycles.device='CPU'; sc.cycles.samples=16; sc.cycles.use_denoising=True; sc.view_settings.view_transform='Khronos PBR Neutral'; sc.render.resolution_x=300; sc.render.resolution_y=400
w=bpy.data.worlds.new('w'); w.use_nodes=True; w.node_tree.nodes['Background'].inputs[0].default_value=(0.2,0.22,0.27,1); sc.world=w
l=bpy.data.lights.new('s','SUN'); l.energy=2.5; lo=bpy.data.objects.new('s',l); sc.collection.objects.link(lo); lo.rotation_euler=(math.radians(50),0,math.radians(30))
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera=cam; cam.data.lens=35
cam.location=(0,-4.3,1.0); cam.rotation_euler=(math.radians(90),0,0)
os.makedirs('/home/user/personajes_c3/fotos',exist_ok=True)
for k,fr in enumerate([f0+int((f1-f0)*u) for u in (0,0.25,0.5,0.75)]):
    sc.frame_set(fr)
    # centrar la cámara en la cadera
    cadera=dst.matrix_world@dst.pose.bones[pref_d+'Hip'].head
    cam.location=(cadera.x,cadera.y-4.0,1.0)
    sc.render.filepath=f'/home/user/personajes_c3/fotos/{pref}_{k}.png'; bpy.ops.render.render(write_still=True)
