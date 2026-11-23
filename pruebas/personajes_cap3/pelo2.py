"""Prueba: retarget de un clip de Mixamo sobre el esqueleto estándar de un personaje CC4 (FBX) y fotos de 4 cuadros. Uso: python mix.py -- fbxPersonaje clipMixamo prefijo"""
import bpy, sys, math, os
from mathutils import Vector
sys.path.insert(0,'/home/user/chica_nueva')
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
# ── física del pelo: tela con raíces fijas al cuero cabelludo (grupo «raiz» por distancia al cráneo) y colisión con cuerpo/cabeza
import bmesh
from mathutils.bvhtree import BVHTree
body=next(o for o in bpy.data.objects if o.name.endswith('Base_Body'))
bpy.context.view_layer.update()
bm=bmesh.new(); bm.from_mesh(body.data); bm.transform(body.matrix_world)
bvh=BVHTree.FromBMesh(bm)
PIEZAS={'Double_high':dict(masa=0.2,flex=4.0,tens=40,aire=3.0,falloff=0.07),
        'Air_bangs':dict(masa=0.12,flex=2.0,tens=30,aire=3.0,falloff=0.05),
        'Space_bun_L':dict(masa=0.3,flex=12.0,tens=80,aire=4.0,falloff=0.12),
        'Space_bun_R':dict(masa=0.3,flex=12.0,tens=80,aire=4.0,falloff=0.12)}
for nombre,p in PIEZAS.items():
    pelo=bpy.data.objects.get(nombre)
    if not pelo: print('SIN',nombre); continue
    g=pelo.vertex_groups.new(name='raiz'); mw=pelo.matrix_world
    for v in pelo.data.vertices:
        loc,n,i,d=bvh.find_nearest(mw@v.co)
        w=max(0.0,min(1.0,1.0-(d-0.006)/p['falloff']))
        g.add([v.index],w,'REPLACE')
    cl=pelo.modifiers.new('Pelo_fisica','CLOTH')
    st=cl.settings; st.quality=8; st.mass=p['masa']; st.air_damping=p['aire']
    st.tension_stiffness=p['tens']; st.compression_stiffness=p['tens']; st.shear_stiffness=p['tens']*0.7; st.bending_stiffness=p['flex']; st.bending_damping=1.0
    st.vertex_group_mass='raiz'; st.pin_stiffness=1.0
    cl.collision_settings.use_collision=True; cl.collision_settings.distance_min=0.004; cl.collision_settings.collision_quality=3
    cl.collision_settings.use_self_collision=False
    cl.point_cache.frame_start=f0; cl.point_cache.frame_end=f1
body.modifiers.new('col','COLLISION')
body.collision.thickness_outer=0.004
sc=bpy.context.scene; sc.frame_start=f0; sc.frame_end=f1
sc.render.engine='CYCLES'; sc.cycles.device='CPU'; sc.cycles.samples=16; sc.cycles.use_denoising=True; sc.view_settings.view_transform='Khronos PBR Neutral'
sc.render.resolution_x=300; sc.render.resolution_y=400
w=bpy.data.worlds.new('w'); w.use_nodes=True; w.node_tree.nodes['Background'].inputs[0].default_value=(0.2,0.22,0.27,1); sc.world=w
l=bpy.data.lights.new('s','SUN'); l.energy=2.5; lo=bpy.data.objects.new('s',l); sc.collection.objects.link(lo); lo.rotation_euler=(math.radians(50),0,math.radians(30))
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera=cam; cam.data.lens=60
# simular cuadro a cuadro (el caché de tela necesita avanzar en orden)
paso=max(1,(f1-f0)//6)
mostrar=[f0+k*paso for k in range(7)]
for fr in range(f0,f1+1):
    sc.frame_set(fr)
    if fr in mostrar:
        cabeza=dst.matrix_world@dst.pose.bones[pref_d+'Head'].head
        cam.location=(cabeza.x+0.45,cabeza.y-1.15,cabeza.z+0.05)
        cam.rotation_euler=((cabeza-cam.location).to_track_quat('-Z','Y')).to_euler()
        sc.render.filepath=f'/home/user/chica_nueva/fotos/{pref}_{mostrar.index(fr)}.png'; bpy.ops.render.render(write_still=True)
        print('RENDER',fr,flush=True)
