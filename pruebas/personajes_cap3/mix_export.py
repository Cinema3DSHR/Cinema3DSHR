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
# animación facial de prueba por shape keys (parpadeo, boca, sonrisa) sobre las mismas mallas
meshes=[o for o in bpy.data.objects if o.type=='MESH' and o.data.shape_keys]
def clave(nombre,vals):
    for ob in meshes:
        k=ob.data.shape_keys
        if nombre in k.key_blocks:
            for fr,v in vals:
                k.key_blocks[nombre].value=v; k.key_blocks[nombre].keyframe_insert('value',frame=fr)
clave('V_Open',[(f0,0),(f0+8,1),(f0+14,0),(f0+22,0.7),(f0+30,0)])
clave('V_Tight_O',[(f0,0),(f0+14,0),(f0+18,1),(f0+22,0)])
clave('Mouth_Smile',[(f0,0),(f0+20,0),(f0+36,1)])
clave('Eyes_Blink',[(f0,0),(f0+10,0),(f0+12,1),(f0+15,0)])
for ob in meshes:
    k=ob.data.shape_keys
    if k.animation_data and k.animation_data.action and 'Calibration' in k.animation_data.action.name: pass
sc=bpy.context.scene; sc.frame_start=f0; sc.frame_end=f1
bpy.ops.export_scene.gltf(filepath=f'/home/user/personajes_c3/{pref}.glb',export_format='GLB',export_morph=True,export_animations=True,export_apply=False,export_skins=True,export_yup=True)
print('EXPORTADO',pref)
