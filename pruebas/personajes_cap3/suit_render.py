import bpy, sys, math, os
sys.path.insert(0,'/home/user/cap3'); sys.path.insert(0,'/home/user/personajes_c3')
import colores, traje_futurista as TF
import retarget_dir as RT
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:]
fbx,pref=a[0],a[1]; piel=tuple(float(x) for x in a[2].split(',')); pelo=tuple(float(x) for x in a[3].split(','))
clip=a[4] if len(a)>4 else None
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx)
dst=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
P='EM3D_Base_'
sc=bpy.context.scene
colores.aplicar(piel,pelo)
for o in bpy.data.objects:
    if o.name in ('Bra','Underwear_Bottoms','Boxers'): o.hide_render=True
body=next(o for o in bpy.data.objects if o.name.endswith('Base_Body'))
meshes=[o for o in bpy.data.objects if o.type=='MESH' and not o.hide_render]
pts=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box]
H=max(p.z for p in pts)-min(p.z for p in pts); zmin=min(p.z for p in pts)
piezas=TF.construir(dst,body,P,H)
print('PIEZAS',len(piezas),'H',round(H,3))
# render
sc.render.engine='CYCLES'; sc.cycles.device='CPU'; sc.cycles.samples=32; sc.cycles.use_denoising=True; sc.view_settings.view_transform='Khronos PBR Neutral'
sc.render.resolution_x=360; sc.render.resolution_y=560
w=bpy.data.worlds.new('w'); w.use_nodes=True; w.node_tree.nodes['Background'].inputs[0].default_value=(0.05,0.06,0.09,1); sc.world=w
S=H/1.7
def luz(nm,loc,e,col=(1,1,1),size=3):
    l=bpy.data.lights.new(nm,'AREA'); l.energy=e; l.size=size; l.color=col
    o=bpy.data.objects.new(nm,l); sc.collection.objects.link(o); o.location=loc
    o.rotation_euler=(Vector((0,0,zmin+H*0.55))-Vector(loc)).to_track_quat('-Z','Y').to_euler()
luz('k',(-1.6*S,-2.6*S,zmin+H*1.0),60*S*S,(1,0.95,0.9),2.5*S); luz('f',(2.2*S,-2.0*S,zmin+H*0.6),22*S*S,(0.7,0.85,1),3*S); luz('r',(0.6*S,2.4*S,zmin+H*1.1),60*S*S,(0.6,0.85,1),2*S)
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera=cam
cam.data.sensor_fit='VERTICAL'; cam.data.sensor_height=24
def shot(nm,cx,cy,cz,dist,lens,az=0):
    cam.data.lens=lens
    cam.location=(cx+dist*math.sin(math.radians(az)),cy-dist*math.cos(math.radians(az)),cz)
    d=Vector((cx,cy,cz))-cam.location
    cam.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=f'/home/user/cap3/fotos/{pref}_{nm}.png'; bpy.ops.render.render(write_still=True)
os.makedirs('/home/user/cap3/fotos',exist_ok=True)
# brazos hacia abajo: pose A suave (los brazos de CC4 vienen en T)
for lado,sg in (('L',1),('R',-1)):
    pb=dst.pose.bones[P+f'{lado}_Upperarm']; pb.rotation_mode='XYZ'
bpy.context.view_layer.update()
shot('frente',0,0,zmin+H*0.52,H*1.6,45)
shot('tres_cuartos',0,0,zmin+H*0.52,H*1.6,45,az=40)
shot('espalda',0,0,zmin+H*0.52,H*1.6,45,az=180)
shot('busto',0,0,zmin+H*0.80,H*0.62,55,az=20)
shot('botas',0,0,zmin+H*0.13,H*0.55,50,az=30)
print('LISTO',flush=True)
