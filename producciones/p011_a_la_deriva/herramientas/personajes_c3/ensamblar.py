"""Ensambla un personaje del cap. 3 para Godot: FBX CC4 → colores reales → primera piel futurista + botas → clips de Mixamo retargeteados → GLB.
Uso: python ensamblar.py -- fbx nombre piel(r,g,b) pelo(r,g,b) lista_clips.json [sin_traje]"""
import bpy, sys, math, os, json
sys.path.insert(0,'/home/user/cap3')
import colores, traje_futurista as TF
import retarget_raiz as RT
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:]
fbx,nombre=a[0],a[1]; piel=tuple(float(x) for x in a[2].split(',')); pelo=tuple(float(x) for x in a[3].split(','))
clips=json.load(open(a[4])); con_traje=not (len(a)>5 and a[5]=='sin_traje')
MIX='/home/user/mixamo-respaldo/'
P='EM3D_Base_'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx)
dst=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
colores.aplicar(piel,pelo)
for o in list(bpy.data.objects):
    if o.name in ('Bra','Underwear_Bottoms','Boxers'): bpy.data.objects.remove(o)
for o in bpy.data.objects:
    if o.type=='MESH' and o.data.shape_keys and o.data.shape_keys.animation_data: o.data.shape_keys.animation_data.action=None
for ac in list(bpy.data.actions):
    if 'Calibration' in ac.name or ac.users==0: bpy.data.actions.remove(ac)
body=next(o for o in bpy.data.objects if o.name.endswith('Base_Body'))
meshes=[o for o in bpy.data.objects if o.type=='MESH']
pts=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box]
H=max(p.z for p in pts)-min(p.z for p in pts)
print('ALTURA',round(H,3))
if con_traje:
    piezas=TF.construir(dst,body,P,H); print('TRAJE',len(piezas))
# ── clips
M={'Hips':'Hip','Spine':'Waist','Spine1':'Spine01','Spine2':'Spine02','Neck':'NeckTwist01','Head':'Head','LeftShoulder':'L_Clavicle','LeftArm':'L_Upperarm','LeftForeArm':'L_Forearm','LeftHand':'L_Hand',
   'RightShoulder':'R_Clavicle','RightArm':'R_Upperarm','RightForeArm':'R_Forearm','RightHand':'R_Hand','LeftUpLeg':'L_Thigh','LeftLeg':'L_Calf','LeftFoot':'L_Foot','LeftToeBase':'L_ToeBase',
   'RightUpLeg':'R_Thigh','RightLeg':'R_Calf','RightFoot':'R_Foot','RightToeBase':'R_ToeBase'}
for lado,l in (('Left','L'),('Right','R')):
    for d,n in (('Thumb','Thumb'),('Index','Index'),('Middle','Mid'),('Ring','Ring'),('Pinky','Pinky')):
        for i in (1,2,3): M[f'{lado}Hand{d}{i}']=f'{l}_{n}{i}'
meta={}
fd=(dst.matrix_world@dst.data.bones[P+'L_ToeBase'].head_local)-(dst.matrix_world@dst.data.bones[P+'L_Foot'].head_local)
for nom,ruta in clips.items():
    antes=set(bpy.data.objects); acc0=set(bpy.data.actions)
    bpy.ops.import_scene.fbx(filepath=MIX+ruta, automatic_bone_orientation=False)
    src=[o for o in bpy.data.objects if o not in antes and o.type=='ARMATURE'][0]
    acc=[x for x in bpy.data.actions if x not in acc0][0]
    nombres={P+v:'mixamorig:'+k for k,v in M.items() if ('mixamorig:'+k) in src.pose.bones and (P+v) in dst.pose.bones}
    fs=(src.matrix_world@src.data.bones['mixamorig:LeftToeBase'].head_local)-(src.matrix_world@src.data.bones['mixamorig:LeftFoot'].head_local)
    ang=math.atan2(fd.y,fd.x)-math.atan2(fs.y,fs.x)
    f0,f1=int(acc.frame_range[0]),int(acc.frame_range[1])
    nueva=RT.retarget(src,acc,dst,'c_'+nom,hueso_cadera=P+'Hip',cadera_origen='mixamorig:Hips',nombres=nombres,fotogramas=(f0,f1),giro_z=ang)
    nueva.name='c_'+nom; nueva.use_fake_user=True
    meta[nom]={'frames':[f0,f1],'desp':[round(x,3) for x in nueva.get('desplazamiento_cadera_m',[0,0,0])],'raiz_xy':list(nueva.get('raiz_xy',[])),'mapeados':len(nombres)}
    for o in list(bpy.data.objects):
        if o not in antes and o.type=='ARMATURE': bpy.data.objects.remove(o)
        elif o not in antes: bpy.data.objects.remove(o)
    for x in list(bpy.data.actions):
        if x not in acc0 and x is not nueva: bpy.data.actions.remove(x)
    print('CLIP',nom,meta[nom]['frames'],meta[nom]['desp'],flush=True)
dst.animation_data_create(); dst.animation_data.action=None
json.dump({'altura':H,'clips':meta},open(f'/home/user/cap3/pers/{nombre}_meta.json','w'),indent=1)
bpy.ops.wm.save_as_mainfile(filepath=f'/home/user/cap3/pers/{nombre}.blend')
bpy.ops.export_scene.gltf(filepath=f'/home/user/cap3/pers/{nombre}.glb',export_format='GLB',export_morph=True,export_animations=True,export_animation_mode='ACTIONS',export_skins=True,export_apply=False,export_yup=True,export_image_format='AUTO')
print('EXPORTADO',nombre,os.path.getsize(f'/home/user/cap3/pers/{nombre}.glb'))
