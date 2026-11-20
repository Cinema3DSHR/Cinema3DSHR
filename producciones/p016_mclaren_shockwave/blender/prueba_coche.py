import sys, math, os
import bpy
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import coche
bpy.ops.wm.read_factory_settings(use_empty=True)
s = bpy.context.scene
col = bpy.data.collections.new("C"); s.collection.children.link(col)
c = coche.cargar(col)
s.render.engine = "CYCLES"; s.cycles.samples = 32; s.cycles.device = "CPU"; s.cycles.use_denoising = True
s.render.resolution_x, s.render.resolution_y = 720, 540
w = bpy.data.worlds.new("w"); s.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.55, 0.6, 0.7, 1); w.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.1
sun = bpy.data.lights.new("s", "SUN"); sun.energy = 4; so = bpy.data.objects.new("s", sun); s.collection.objects.link(so); so.rotation_euler = (0.9, 0.2, 0.5)
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
vistas = {"izquierda": (8, 0, 1.0, 0, 0, 0.35), "derecha": (-8, 0, 1.0, 0, 0, 0.35), "frente": (0, -7, 1.1, 0, -2.3, 0.35), "atras": (0, 7, 1.1, 0, 2.3, 0.35),
          "placa_trasera": (0.0, 3.4, 0.9, 0, 2.3, 0.65), "placa_frontal": (0.0, -3.6, 0.8, 0, -2.3, 0.2)}
for nombre, (x, y, z, tx, ty, tz) in vistas.items():
    cd = bpy.data.cameras.new("c"); cd.lens = 55 if "placa" not in nombre else 120
    co = bpy.data.objects.new("c", cd); s.collection.objects.link(co)
    co.location = (x, y, z); co.rotation_euler = (Vector((tx, ty, tz)) - co.location).to_track_quat("-Z", "Y").to_euler()
    s.camera = co
    s.render.filepath = f"/home/user/mclaren/c_{nombre}.png"; bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath="/home/user/mclaren/coche_prueba.blend")
