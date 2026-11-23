"""Paquete de un personaje para cambiar la ropa: .blend limpio (sin animaciones, pose de reposo, cuerpo COMPLETO, ropa en piezas aparte
dentro de la colección «Ropa», texturas empaquetadas) + GLB estático. Uso: python entrega_personaje.py -- nombre Nombre Visible"""
import bpy, sys, os
sys.path.insert(0,'/home/user/cap3')
import traje_futurista as TF
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:]
nombre=a[0]; titulo=a[1] if len(a)>1 else nombre
pelo_nat=tuple(float(x) for x in a[2].split(',')) if len(a)>2 else None
OUT='/home/user/cap3/entrega'; os.makedirs(OUT,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=f'/home/user/cap3/pers/{nombre}.blend')
# 1) sin animaciones
for ac in list(bpy.data.actions): bpy.data.actions.remove(ac)
dst=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
if dst.animation_data: dst.animation_data_clear()
for o in bpy.data.objects:
    if o.type=='MESH' and o.data.shape_keys and o.data.shape_keys.animation_data: o.data.shape_keys.animation_data_clear()
for pb in dst.pose.bones:
    pb.rotation_mode='QUATERNION'; pb.location=(0,0,0); pb.rotation_quaternion=(1,0,0,0); pb.scale=(1,1,1)
bpy.context.view_layer.update()
# 2) ropa vieja fuera
for o in list(bpy.data.objects):
    if o.name.startswith(('TRAJE_','SUELA_','BOTA_LUZ_','VIVO_','EMBLEMA','COLLAR')): bpy.data.objects.remove(o)
for m in list(bpy.data.materials):
    if m.name.startswith('traje_') and m.users==0: bpy.data.materials.remove(m)
if pelo_nat:      # persona normal: color de pelo y cejas natural (sin el plateado de EVA)
    for m in bpy.data.materials:
        if not m.use_nodes: continue
        p=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
        if p is None: continue
        if m.name.startswith(('Hair','Slicked')): col_n=pelo_nat
        elif m.name.startswith(('Eyebrows','Female_Flat')): col_n=tuple(c*0.7 for c in pelo_nat)
        else: continue
        bc=p.inputs['Base Color']
        if bc.is_linked and bc.links[0].from_node.type=='MIX':
            bc.links[0].from_node.inputs[7].default_value=(*col_n,1)
        elif not bc.is_linked:
            bc.default_value=(*col_n,1)
body=next(o for o in bpy.data.objects if o.name.endswith('Base_Body'))
meshes=[o for o in bpy.data.objects if o.type=='MESH']
pts=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box]
H=max(p.z for p in pts)-min(p.z for p in pts)
antes=set(bpy.data.objects)
TF.construir(dst,body,'EM3D_Base_',H,ocultar_pies=False)          # el cuerpo queda COMPLETO
ropa=[o for o in bpy.data.objects if o not in antes]
# 2 bis) ropa interior original del modelo (para que al sacar el traje no quede desnudo)
FBX={'aiden':'/home/user/personajes_c3/modelos/fbx_a/fbx.fbx','kate':'/home/user/chica_nueva/m/fbx/fbx.fbx','eva':'/home/user/personajes_c3/modelos/fbx_b/fbx.fbx'}[nombre]
antes_i=set(bpy.data.objects)
bpy.ops.import_scene.fbx(filepath=FBX)
nuevos_i=[o for o in bpy.data.objects if o not in antes_i]
interior=[o for o in nuevos_i if o.type=='MESH' and o.name in ('Bra','Underwear_Bottoms','Boxers')]
for o in interior:
    mw=o.matrix_world.copy()
    for md in o.modifiers:
        if md.type=='ARMATURE': md.object=dst
    o.parent=dst; o.matrix_parent_inverse=dst.matrix_world.inverted(); o.matrix_world=mw
    o.name='INTERIOR_'+o.name
for o in nuevos_i:
    if o not in interior and o.name in bpy.data.objects: bpy.data.objects.remove(o)
for ac in list(bpy.data.actions): bpy.data.actions.remove(ac)
# 3) colecciones ordenadas
sc=bpy.context.scene
def col(n):
    c=bpy.data.collections.get(n) or bpy.data.collections.new(n)
    if c.name not in [x.name for x in sc.collection.children]: sc.collection.children.link(c)
    return c
cE,cC,cP,cR,cI=col('Esqueleto'),col('Cuerpo'),col('Pelo y cejas'),col('Ropa'),col('Ropa interior')
def mover(o,c):
    for x in list(o.users_collection): x.objects.unlink(o)
    c.objects.link(o)
mover(dst,cE)
for o in ropa: mover(o,cR)
for o in interior: mover(o,cI)
for o in bpy.data.objects:
    if o in ropa or o in interior or o is dst or o.type!='MESH': continue
    n=o.name
    if n.startswith(('Hair','Slicked','Female_Flat','Eyebrows','Scalp')) or 'Hair' in n: mover(o,cP)
    else: mover(o,cC)
for c in list(bpy.data.collections):
    if c.name not in ('Esqueleto','Cuerpo','Pelo y cejas','Ropa','Ropa interior') and not c.objects and not c.children: bpy.data.collections.remove(c)
# la ropa interior queda OCULTA (debajo del traje se asoma): se muestra al sacar el traje
cI.hide_render=True
for lc in bpy.context.view_layer.layer_collection.children:
    if lc.name=='Ropa interior': lc.hide_viewport=True
# 4) texturas empaquetadas y guardado
try: bpy.ops.file.pack_all()
except Exception as e: print('PACK',e)
sc.frame_start=sc.frame_end=1
bpy.ops.wm.save_as_mainfile(filepath=f'{OUT}/{titulo}.blend', compress=True)
# 5) GLB estático (sin animaciones)
bpy.ops.export_scene.gltf(filepath=f'{OUT}/{titulo}.glb',export_format='GLB',export_morph=True,export_animations=False,use_visible=True,export_skins=True,export_apply=False,export_yup=True,export_image_format='AUTO')
print('ENTREGA',titulo,os.path.getsize(f'{OUT}/{titulo}.blend'),os.path.getsize(f'{OUT}/{titulo}.glb'),'ropa',[o.name for o in ropa])
