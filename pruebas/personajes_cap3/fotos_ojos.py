"""Fotos de prueba de un personaje CC4: cuerpo entero, rostro neutro y expresiones por shape keys. Uso: python fotos.py -- archivo prefijo [res]"""
import bpy, sys, math, os
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:]
ruta,pref=a[0],a[1]
res=int(a[2]) if len(a)>2 else 480
if ruta.endswith('.fbx'):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=ruta)
else:
    bpy.ops.wm.open_mainfile(filepath=ruta)
sc=bpy.context.scene
sc.render.engine='CYCLES'; sc.cycles.device='CPU'; sc.cycles.samples=24; sc.cycles.use_denoising=True
sc.render.resolution_x=res; sc.render.resolution_y=int(res*4/3)
sc.render.image_settings.file_format='PNG'
sc.view_settings.view_transform='Khronos PBR Neutral'
# ocultar controles/widgets y luces propias
for o in bpy.data.objects:
    if o.name.startswith('WGT') or o.type=='LIGHT' or o.type=='CAMERA' or o.name=='Lighting': o.hide_render=True; o.hide_viewport=True
# mundo gris suave
w=bpy.data.worlds.new('w'); w.use_nodes=True; w.node_tree.nodes['Background'].inputs[0].default_value=(0.12,0.13,0.16,1); w.node_tree.nodes['Background'].inputs[1].default_value=1.0; sc.world=w
meshes=[o for o in bpy.data.objects if o.type=='MESH' and not o.hide_render]
for ob in meshes:
    k=ob.data.shape_keys
    if k and k.animation_data: k.animation_data.action=None      # la acción «Calibration» pisa los valores en cada evaluación
body=next(o for o in meshes if o.name.endswith('Base_Body'))
arm=next(o for o in bpy.data.objects if o.type=='ARMATURE' and any(m.object==o for ob in meshes for m in ob.modifiers if m.type=='ARMATURE'))
bpy.context.view_layer.update()
# altura total y cabeza
pts=[ob.matrix_world@Vector(c) for ob in meshes for c in ob.bound_box]
zmin=min(p.z for p in pts); zmax=max(p.z for p in pts); cx=sum(p.x for p in pts)/len(pts); cy=sum(p.y for p in pts)/len(pts)
H=zmax-zmin
print('ALTURA',round(H,3),'m  zmin',round(zmin,3))
# luces
def luz(nm,loc,e,col=(1,1,1),size=3):
    l=bpy.data.lights.new(nm,'AREA'); l.energy=e; l.size=size; l.color=col
    o=bpy.data.objects.new(nm,l); sc.collection.objects.link(o); o.location=loc
    d=(Vector((cx,cy,zmin+H*0.55))-Vector(loc)); o.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
S=H/1.7
luz('key',(cx-1.8*S,cy-2.6*S,zmin+H*1.0),110*S*S,(1,0.95,0.9),2.5*S)
luz('fill',(cx+2.2*S,cy-2.2*S,zmin+H*0.6),45*S*S,(0.8,0.9,1),3*S)
luz('rim',(cx+0.5*S,cy+2.4*S,zmin+H*1.1),90*S*S,(1,1,1),2*S)
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera=cam
def shot(nm,centro_z,dist,lens):
    cam.data.lens=lens; cam.data.sensor_fit='VERTICAL'; cam.data.sensor_height=24
    cam.location=(cx,cy-dist,zmin+centro_z)
    cam.rotation_euler=(math.radians(90),0,0)
    sc.render.filepath=f'/home/user/personajes_c3/fotos/{pref}_{nm}.png'; bpy.ops.render.render(write_still=True)
# frente: ¿hacia dónde mira? se prueba con la nariz; asumimos −Y (CC4) y se verifica visualmente
shot('cuerpo',H*0.5,H*1.55*(50/ (24*0 +50)),35)
cabeza_z=H*0.915
def sk_all(valores):
    for ob in meshes:
        sk=ob.data.shape_keys
        if not sk: continue
        for k in sk.key_blocks:
            if k.name!='Basis': k.value=0.0
        for n,v in valores.items():
            if n in sk.key_blocks: sk.key_blocks[n].value=v
EXPR={
 'neutra':{},
 'sonrisa':{'Mouth_Smile':1.0,'Cheek_Raise_L':0.6,'Cheek_Raise_R':0.6,'Eye_Squint_L':0.3,'Eye_Squint_R':0.3,'A38_Mouth_Smile_Left':0.5,'A39_Mouth_Smile_Right':0.5},
 'sorpresa':{'Brow_Raise_Inner_Left':1,'Brow_Raise_Inner_Right':1,'Brow_Raise_Outer_Left':1,'Brow_Raise_Outer_Right':1,'Eye_Wide_L':1,'Eye_Wide_R':1,'A25_Jaw_Open':0.7,'V_Open':0.6},
 'enojo':{'Brow_Drop_Left':1,'Brow_Drop_Right':1,'Eye_Squint_L':0.6,'Eye_Squint_R':0.6,'Mouth_Snarl_Upper_L':0.7,'Mouth_Snarl_Upper_R':0.7,'Mouth_Frown':0.5,'Nose_Scrunch':0.5},
 'tristeza':{'Brow_Raise_Inner_Left':1,'Brow_Raise_Inner_Right':1,'Mouth_Frown':1.0,'Eye_Squint_L':0.2,'Eye_Squint_R':0.2,'Mouth_Bottom_Lip_Down':0.4},
 'ojos_cerrados':{'Eyes_Blink':1.0},
 'fonema_A':{'V_Open':1.0},
 'fonema_O':{'V_Tight_O':1.0},
 'fonema_U':{'Mouth_Pucker':1.0},
 'fonema_M':{'Mouth_Lips_Tight':1.0,'V_Explosive':0.6},
 'fonema_F':{'V_Dental_Lip':1.0},
 'fonema_E':{'V_Wide':1.0},
}
for nm,v in EXPR.items():
    sk_all(v); bpy.context.view_layer.update()
    shot('cara_'+nm,cabeza_z,H*0.45,70)
# boca abierta por hueso de mandíbula (Rigify jaw_master) + visemas
pb=arm.pose.bones.get('jaw_master') or arm.pose.bones.get('jaw')
print('JAW',pb.name if pb else None, pb.rotation_mode if pb else None)
if pb:
    pb.rotation_mode='XYZ'
    for nm,ang,v in (('boca_a',0.45,{'V_Open':0.6}),('boca_o',0.25,{'V_Tight_O':1.0,'Mouth_Pucker':0.5}),('boca_grande',0.7,{'V_Open':1.0,'Mouth_Smile':0.3})):
        pb.rotation_euler=(ang,0,0); sk_all(v); bpy.context.view_layer.update()
        shot('cara_'+nm,cabeza_z,H*0.45,70)
    pb.rotation_euler=(-0.45,0,0); sk_all({}); bpy.context.view_layer.update(); shot('cara_boca_menos',cabeza_z,H*0.45,70)
# mirada: control «eyes» de Rigify (los ojos giran con huesos independientes)
pb=arm.pose.bones.get('eyes')
print('EYES',pb.name if pb else None)
if pb:
    sk_all({}); pb.rotation_mode='XYZ'
    for nm,loc in (('mira_izq',(-0.12,0,0)),('mira_der',(0.12,0,0)),('mira_arriba',(0,0,0.1)),('mira_abajo',(0,0,-0.1))):
        pb.location=loc; bpy.context.view_layer.update(); shot('cara_'+nm,cabeza_z,H*0.45,70)
    pb.location=(0,0,0)
print('LISTO')