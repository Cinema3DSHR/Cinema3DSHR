import bpy, sys, math
sys.path.insert(0,'/home/user/cap3')
import colores
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:]
fbx,pref=a[0],a[1]
piel=tuple(float(x) for x in a[2].split(',')); pelo=tuple(float(x) for x in a[3].split(','))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx)
print('LOG',colores.aplicar(piel,pelo))
sc=bpy.context.scene
for o in bpy.data.objects:
    if o.name in ('Bra','Underwear_Bottoms','Boxers'): o.hide_render=True
meshes=[o for o in bpy.data.objects if o.type=='MESH' and not o.hide_render]
body=next(o for o in meshes if o.name.endswith('Base_Body'))
pts=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box]
zmin=min(p.z for p in pts); zmax=max(p.z for p in pts); H=zmax-zmin; cx=sum(p.x for p in pts)/len(pts); cy=sum(p.y for p in pts)/len(pts)
sc.render.engine='CYCLES'; sc.cycles.device='CPU'; sc.cycles.samples=24; sc.cycles.use_denoising=True; sc.view_settings.view_transform='Khronos PBR Neutral'
sc.render.resolution_x=360; sc.render.resolution_y=480
w=bpy.data.worlds.new('w'); w.use_nodes=True; w.node_tree.nodes['Background'].inputs[0].default_value=(0.2,0.22,0.27,1); sc.world=w
S=H/1.7
def luz(nm,loc,e,col=(1,1,1),size=3):
    l=bpy.data.lights.new(nm,'AREA'); l.energy=e; l.size=size; l.color=col
    o=bpy.data.objects.new(nm,l); sc.collection.objects.link(o); o.location=loc
    o.rotation_euler=(Vector((cx,cy,zmin+H*0.8))-Vector(loc)).to_track_quat('-Z','Y').to_euler()
luz('k',(cx-1.2*S,cy-2.0*S,zmin+H*1.0),45*S*S,(1,0.95,0.9),2*S); luz('f',(cx+1.6*S,cy-1.8*S,zmin+H*0.7),16*S*S,(0.8,0.9,1),3*S); luz('r',(cx,cy+2*S,zmin+H*1.1),30*S*S,(1,1,1),2*S)
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera=cam
cam.data.sensor_fit='VERTICAL'; cam.data.sensor_height=24
def shot(nm,cz,dist,lens):
    cam.data.lens=lens; cam.location=(cx,cy-dist,zmin+cz); cam.rotation_euler=(math.radians(90),0,0)
    sc.render.filepath=f'/home/user/cap3/fotos/{pref}_{nm}.png'; bpy.ops.render.render(write_still=True)
import os; os.makedirs('/home/user/cap3/fotos',exist_ok=True)
shot('cuerpo',H*0.52,H*1.5,40)
shot('cara',H*0.89,H*0.5,60)
