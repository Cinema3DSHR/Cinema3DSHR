"""Etapa 2 (rápida): abre <nombre>.blend (con los clips ya retargeteados), rehace el traje y las botas con piezas skinneadas y exporta el GLB.
Uso: python traje2.py -- nombre"""
import bpy, sys, os
sys.path.insert(0,'/home/user/cap3')
import traje_futurista as TF
from mathutils import Vector
nombre=sys.argv[sys.argv.index('--')+1]
bpy.ops.wm.open_mainfile(filepath=f'/home/user/cap3/pers/{nombre}.blend')
for o in list(bpy.data.objects):
    if o.name.startswith(('TRAJE_','SUELA_','BOTA_LUZ_','VIVO_','EMBLEMA')): bpy.data.objects.remove(o)
for m in list(bpy.data.materials):
    if m.name.startswith('traje_') and m.users==0: bpy.data.materials.remove(m)
dst=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
body=next(o for o in bpy.data.objects if o.name.endswith('Base_Body'))
meshes=[o for o in bpy.data.objects if o.type=='MESH']
pts=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box]
H=max(p.z for p in pts)-min(p.z for p in pts)
dst.animation_data_create(); dst.animation_data.action=None
for pb in dst.pose.bones:
    pb.rotation_mode='QUATERNION'; pb.location=(0,0,0); pb.rotation_quaternion=(1,0,0,0); pb.scale=(1,1,1)
bpy.context.view_layer.update()
piezas=TF.construir(dst,body,'EM3D_Base_',H); print('TRAJE',len(piezas))
KEEP={'V_Open','V_Explosive','V_Dental_Lip','V_Tight_O','V_Tight','V_Wide','V_Affricate','Brow_Raise_Inner_Left','Brow_Raise_Inner_Right','Brow_Drop_Left','Brow_Drop_Right','Brow_Raise_Left','Brow_Raise_Right','Eye_Wide_L','Eye_Wide_R','Mouth_Lips_Part','Mouth_Lips_Tight','Mouth_Frown','Mouth_Smile','Cheek_Raise_L','Cheek_Raise_R','Eye_Squint_L','Eye_Squint_R','Eye_Blink_L','Eye_Blink_R'}
for ob in bpy.data.objects:
    if ob.type=='MESH' and ob.data.shape_keys:
        for kb in list(ob.data.shape_keys.key_blocks)[1:]:
            if kb.name not in KEEP: ob.shape_key_remove(kb)
bpy.ops.export_scene.gltf(filepath=f'/home/user/cap3/pers/{nombre}.glb',export_format='GLB',export_morph=True,export_animations=True,export_animation_mode='ACTIONS',export_skins=True,export_apply=False,export_yup=True,export_image_format='AUTO')
print('EXPORTADO',nombre,os.path.getsize(f'/home/user/cap3/pers/{nombre}.glb'))
