import sys, os, math, random
import bpy
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib, interiores
from lib import *
bpy.ops.wm.read_factory_settings(use_empty=True)
s=bpy.context.scene
col=coleccion("T")
rng=random.Random(4)
for k,fn in enumerate(interiores.TIPOS):
    fn(col, k*30.0, 1, 30.0, rng)
s.render.engine="CYCLES"; s.cycles.samples=32; s.cycles.device="CPU"; s.cycles.use_denoising=True
w=bpy.data.worlds.new("w"); s.world=w; w.use_nodes=True; w.node_tree.nodes["Background"].inputs["Color"].default_value=(0.02,0.03,0.05,1)
def cam(nombre,loc,tgt,lens=24,ortho=None,res=(720,1280)):
    cd=bpy.data.cameras.new("c"); cd.lens=lens; cd.sensor_fit="VERTICAL"; cd.sensor_height=24
    if ortho: cd.type="ORTHO"; cd.ortho_scale=ortho
    c=bpy.data.objects.new("c",cd); s.collection.objects.link(c); c.location=loc
    c.rotation_euler=(Vector(tgt)-Vector(loc)).to_track_quat("-Z","Y").to_euler(); s.camera=c
    s.render.resolution_x,s.render.resolution_y=res
    s.render.filepath=f"/home/user/mclaren/int_{nombre}.png"; bpy.ops.render.render(write_still=True)
for k,nombre in enumerate(("rest","super","mueb")):
    cam("planta_"+nombre,(24,k*30+15,7.9),(24,k*30+15,0.0),ortho=32,res=(700,1200))
cam("mesa1",(16.9,0.3,2.0),(19.9,2.7,0.5),lens=30,res=(900,700))
cam("mesa2",(23.0,6.9,2.2),(25.9,8.3,0.5),lens=30,res=(900,700))
cam("sofa",(24.6,5.0,1.8),(30.0,5.0,0.6),lens=26,res=(900,700))
for k,nombre in enumerate(()):
    cam("calle_"+nombre,(8,k*30+15,1.6),(24,k*30+15,1.5),lens=18,res=(720,1000))
