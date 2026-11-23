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
bpy.ops.export_scene.gltf(filepath=f'/home/user/cap3/pers/{nombre}.glb',export_format='GLB',export_morph=True,export_animations=True,export_animation_mode='ACTIONS',export_skins=True,export_apply=False,export_yup=True,export_image_format='AUTO')
print('EXPORTADO',nombre,os.path.getsize(f'/home/user/cap3/pers/{nombre}.glb'))
