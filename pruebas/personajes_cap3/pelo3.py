"""Pelo de Kate: física CONTINUA por gravedad (no sólo en movimientos bruscos). Cabeza que mira abajo / arriba con pausas. Uso: python pelo3.py -- fbx prefijo"""
import bpy, sys, math, os, bmesh
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
a=sys.argv[sys.argv.index('--')+1:]
fbx,pref=a[0],a[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx)
dst=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
P='EM3D_Base_'
sc=bpy.context.scene; sc.render.fps=30
for o in bpy.data.objects:
    if o.type=='MESH' and o.name in ('Bra','Underwear_Bottoms'): o.hide_render=True
# ── colores reales
def _g(m): return next((x for x in m.node_tree.nodes if x.type=='GROUP' and 'shader' in x.name and 'mapping' not in x.name), None)
for m in bpy.data.materials:
    if not m.use_nodes: continue
    g=_g(m)
    if not g: continue
    if m.name.startswith('EM3D_Skin') or m.name.startswith('EMS_Skin'): g.inputs['Diffuse Color'].default_value=(0.86,0.60,0.47,1.0)
    elif m.name.startswith(('Hair','Scalp','Eyebrows','Female_Flat')): g.inputs['Diffuse Color'].default_value=(0.30,0.11,0.05,1.0)
    elif m.name.startswith('EM3D_Eyelash'): g.inputs['Diffuse Color'].default_value=(0.03,0.02,0.02,1.0)
# ── pose de cabeza animada alrededor del pivote
pb=dst.pose.bones[P+'Head']; pb.rotation_mode='QUATERNION'
bpy.context.view_layer.update()
M0=pb.matrix.copy(); piv=M0.translation.copy()
def rot_x(ang):
    R=Matrix.Rotation(ang,4,'X')
    return Matrix.Translation(piv)@R@Matrix.Translation(-piv)@M0
def pose(fr,ang):
    pb.matrix=rot_x(ang)
    bpy.context.view_layer.update()
    pb.keyframe_insert('rotation_quaternion',frame=fr)
f0=1
for fr,deg in ((1,0),(25,0),(60,-42),(100,-42),(140,34),(185,34),(215,0)):
    pose(fr,math.radians(deg))
f1=215
# ── física
body=next(o for o in bpy.data.objects if o.name.endswith('Base_Body'))
bpy.context.view_layer.update()
bm=bmesh.new(); bm.from_mesh(body.data); bm.transform(body.matrix_world); bvh=BVHTree.FromBMesh(bm)
PIEZAS={'Double_high':dict(masa=0.15,flex=0.6,tens=18,aire=1.2,falloff=0.045),
        'Air_bangs':dict(masa=0.08,flex=0.25,tens=12,aire=1.0,falloff=0.03),
        'Space_bun_L':dict(masa=0.3,flex=10.0,tens=60,aire=3.0,falloff=0.10),
        'Space_bun_R':dict(masa=0.3,flex=10.0,tens=60,aire=3.0,falloff=0.10)}
for nombre,p in PIEZAS.items():
    ob=bpy.data.objects[nombre]
    g=ob.vertex_groups.new(name='raiz'); mw=ob.matrix_world
    for v in ob.data.vertices:
        loc,n,i,d=bvh.find_nearest(mw@v.co)
        g.add([v.index],max(0.0,min(1.0,1.0-(d-0.004)/p['falloff'])),'REPLACE')
    cl=ob.modifiers.new('Pelo_fisica','CLOTH'); st=cl.settings
    st.quality=10; st.mass=p['masa']; st.air_damping=p['aire']
    st.tension_stiffness=p['tens']; st.compression_stiffness=p['tens']; st.shear_stiffness=p['tens']*0.6
    st.bending_stiffness=p['flex']; st.bending_damping=0.6
    st.vertex_group_mass='raiz'; st.pin_stiffness=1.0
    cl.collision_settings.use_collision=True; cl.collision_settings.distance_min=0.004; cl.collision_settings.collision_quality=4
    cl.point_cache.frame_start=f0; cl.point_cache.frame_end=f1
body.modifiers.new('col','COLLISION'); body.collision.thickness_outer=0.004
sc.frame_start=f0; sc.frame_end=f1
sc.render.engine='CYCLES'; sc.cycles.device='CPU'; sc.cycles.samples=14; sc.cycles.use_denoising=True; sc.view_settings.view_transform='Khronos PBR Neutral'
sc.render.resolution_x=300; sc.render.resolution_y=400
w=bpy.data.worlds.new('w'); w.use_nodes=True; w.node_tree.nodes['Background'].inputs[0].default_value=(0.25,0.27,0.32,1); sc.world=w
l=bpy.data.lights.new('s','SUN'); l.energy=2.5; lo=bpy.data.objects.new('s',l); sc.collection.objects.link(lo); lo.rotation_euler=(math.radians(50),0,math.radians(30))
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera=cam; cam.data.lens=55
mostrar=[20,58,98,138,182,212]
for fr in range(f0,f1+1):
    sc.frame_set(fr)
    if fr in mostrar:
        cab=dst.matrix_world@dst.pose.bones[P+'Head'].head
        cam.location=(cab.x+1.1,cab.y-0.9,cab.z+0.02)
        cam.rotation_euler=((Vector((cab.x,cab.y,cab.z+0.03))-cam.location).to_track_quat('-Z','Y')).to_euler()
        sc.render.filepath=f'/home/user/chica_nueva/fotos/{pref}_{mostrar.index(fr)}.png'; bpy.ops.render.render(write_still=True); print('RENDER',fr,flush=True)
