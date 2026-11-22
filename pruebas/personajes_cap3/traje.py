"""Prueba: color (piel, pelo, ojos) y traje espacial hecho en Blender sobre el cuerpo del personaje (se deforma con el mismo esqueleto). Uso: python traje.py -- archivo.blend prefijo hex_pelo"""
import bpy, sys, math, bmesh
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:]
ruta,pref=a[0],a[1]
pelo=tuple(float(x) for x in a[2].split(','))
bpy.ops.wm.open_mainfile(filepath=ruta)
sc=bpy.context.scene
sc.render.engine='CYCLES'; sc.cycles.device='CPU'; sc.cycles.samples=32; sc.cycles.use_denoising=True
sc.view_settings.view_transform='Khronos PBR Neutral'
sc.render.resolution_x=420; sc.render.resolution_y=560
for o in bpy.data.objects:
    if o.name.startswith('WGT') or o.type in ('LIGHT','CAMERA') or o.name=='Lighting': o.hide_render=True; o.hide_viewport=True
meshes=[o for o in bpy.data.objects if o.type=='MESH' and not o.hide_render and not o.name.startswith('WGT')]
for ob in meshes:
    k=ob.data.shape_keys
    if k and k.animation_data: k.animation_data.action=None
body=next(o for o in meshes if o.name.endswith('Base_Body'))
arm=next(o for o in bpy.data.objects if o.type=='ARMATURE' and any(m.object==o for ob in meshes for m in ob.modifiers if m.type=='ARMATURE'))
# ── color: piel, pelo, cejas, ojos
def grupo(m):
    return next((x for x in m.node_tree.nodes if x.type=='GROUP' and 'shader' in x.name and 'mapping' not in x.name), None)
PIEL=(0.62,0.38,0.27,1.0)
for m in bpy.data.materials:
    g=grupo(m) if m.use_nodes else None
    if not g: continue
    if m.name.startswith('EMS_Skin'):
        g.inputs['Diffuse Color'].default_value=PIEL
    elif m.name.startswith(('Hair','Slicked')) or m.name.startswith('Eyebrows'):
        g.inputs['Diffuse Color'].default_value=(*pelo,1.0)
    elif m.name in ('EMS_Eye_R','EMS_Eye_L'):
        for n in ('Iris Color','Iris Inner Color'):
            if n in g.inputs: g.inputs[n].default_value=(0.1,0.45,0.9,1.0)
for nm in ('Boxers','Bra','Underwear_Bottoms'):
    o=bpy.data.objects.get(nm)
    if o: o.hide_render=True
# ── traje espacial: copia del cuerpo sin cabeza/manos/pies, inflada 1,2 cm
vg=[g.name for g in body.vertex_groups]
def conservar(n):
    n=n.replace('DEF-','')
    if n.startswith(('spine.00')) and n[-1] in '456': return False
    if n=='spine' or n.startswith(('spine.00','pelvis','thigh','shin','knee_share','shoulder','upper_arm','forearm','breast','elbow')): return True
    return False
keep={i for i,g in enumerate(vg) if conservar(g)}
dup=body.copy(); dup.data=body.data.copy(); dup.name='TRAJE_ESPACIAL'
bpy.context.scene.collection.objects.link(dup)
dup.data.shape_keys and bpy.context.view_layer.objects.active
# quitar shape keys del duplicado para poder editar la malla
dup.shape_key_clear() if hasattr(dup,'shape_key_clear') else None
bm=bmesh.new(); bm.from_mesh(dup.data)
dl=bm.verts.layers.deform.active
borrar=[]
for v in bm.verts:
    d=v[dl]
    if not d: borrar.append(v); continue
    mejor=max(d.items(), key=lambda kv: kv[1])[0]
    if mejor not in keep: borrar.append(v)
bmesh.ops.delete(bm,geom=borrar,context='VERTS')
bm.normal_update()
for v in bm.verts: v.co += v.normal*0.010*(1.0/ max(dup.scale.x,1e-6))
bm.to_mesh(dup.data); bm.free()
dup.data.materials.clear()
t=bpy.data.materials.new('traje_espacial'); t.use_nodes=True
p=t.node_tree.nodes['Principled BSDF']; p.inputs['Base Color'].default_value=(0.05,0.09,0.16,1); p.inputs['Roughness'].default_value=0.45
dup.data.materials.append(t)
for pol in dup.data.polygons: pol.use_smooth=True
sol=dup.modifiers.new('sol','SOLIDIFY'); sol.thickness=0.004/ max(dup.scale.x,1e-6); sol.offset=1
# ── cámara y luces
bpy.context.view_layer.update()
pts=[ob.matrix_world@Vector(c) for ob in meshes for c in ob.bound_box]
zmin=min(p.z for p in pts); zmax=max(p.z for p in pts); cx=sum(p.x for p in pts)/len(pts); cy=sum(p.y for p in pts)/len(pts); H=zmax-zmin; S=H/1.7
w=bpy.data.worlds.new('w'); w.use_nodes=True; w.node_tree.nodes['Background'].inputs[0].default_value=(0.10,0.12,0.18,1); sc.world=w
def luz(nm,loc,e,col=(1,1,1),size=3):
    l=bpy.data.lights.new(nm,'AREA'); l.energy=e; l.size=size; l.color=col
    o=bpy.data.objects.new(nm,l); sc.collection.objects.link(o); o.location=loc
    o.rotation_euler=(Vector((cx,cy,zmin+H*0.55))-Vector(loc)).to_track_quat('-Z','Y').to_euler()
luz('key',(cx-1.8*S,cy-2.6*S,zmin+H*1.0),110*S*S,(1,0.95,0.9),2.5*S); luz('fill',(cx+2.2*S,cy-2.2*S,zmin+H*0.6),45*S*S,(0.8,0.9,1),3*S); luz('rim',(cx+0.5*S,cy+2.4*S,zmin+H*1.1),90*S*S,(0.6,0.8,1),2*S)
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera=cam
cam.data.sensor_fit='VERTICAL'; cam.data.sensor_height=24
def shot(nm,cz,dist,lens):
    cam.data.lens=lens; cam.location=(cx,cy-dist,zmin+cz); cam.rotation_euler=(math.radians(90),0,0)
    sc.render.filepath=f'/home/user/personajes_c3/fotos/{pref}_{nm}.png'; bpy.ops.render.render(write_still=True)
# pose A (brazos hacia abajo) para que el traje se vea natural: bajar brazos rotando los huesos de hombro
for nombre,ang in (('upper_arm_fk.L',-1.0),('upper_arm_fk.R',1.0)):
    pb=arm.pose.bones.get(nombre)
    if pb: pb.rotation_mode='XYZ'; pb.rotation_euler=(0,0,ang) if False else (0,ang*0,0)
shot('traje_cuerpo',H*0.52,H*1.45*1.0,40)
for ob in meshes:
    k=ob.data.shape_keys
    if k:
        for kb in k.key_blocks:
            if kb.name!='Basis': kb.value=0
        for n,v in {'Mouth_Smile':1.0,'Cheek_Raise_L':0.6,'Cheek_Raise_R':0.6,'Eye_Squint_L':0.3,'Eye_Squint_R':0.3}.items():
            if n in k.key_blocks: k.key_blocks[n].value=v
shot('traje_busto',H*0.84,H*0.9,70)
