"""Etapa Blender del capítulo 3 de «A la deriva»: junta los 5 GLB de Godot en UN .blend (nave única + personajes por escena, línea de tiempo
encadenada, cámaras por marcadores), agrega luces, mundo y efectos y deja el perfil de render obligatorio (960×540, 6 muestras, 30 fps).
Uso: blender -b -P construir_cap3.py -- SALIDA.blend [escenas=s1,s2,s3,s4,s5]"""
import bpy, sys, json, math, os
from mathutils import Vector, Matrix

A = sys.argv[sys.argv.index('--') + 1:]
SALIDA = A[0]
ESC = (A[1] if len(A) > 1 else 's1,s2,s3,s4,s5').split(',')
DIR = '/home/user/cap3/e03/'
FPS = 30

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = FPS; sc.render.fps_base = 1.0
bpy.context.preferences.edit.use_global_undo = False

# ───────────────────────────────────────────────────────────── importar y encadenar
colecciones = {}
camaras_por_toma = []
offset = 0
rangos = {}
def hijos_rec(o):
    out = [o]
    for c in o.children: out += hijos_rec(c)
    return out

for k, clave in enumerate(ESC):
    antes = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=f'{DIR}{clave}.glb')
    nuevos = [o for o in bpy.data.objects if o not in antes]
    js = json.load(open(f'{DIR}{clave}.json'))
    N = int(js['frames'])
    col = bpy.data.collections.new(f'Escena_{clave}'); sc.collection.children.link(col)
    colecciones[clave] = col
    nave = next((o for o in nuevos if o.name.split('.')[0] == 'Nave' and o.type == 'EMPTY'), None)
    n_nave = {o.name for o in hijos_rec(nave)} if nave else set()
    n_extra = {o.name for o in nuevos if o.parent is None and o.type == 'MESH'}
    n_luces = {o.name for o in nuevos if o.type == 'LIGHT'}
    n_nuevos = [o.name for o in nuevos]
    if k == 0:
        colnave = bpy.data.collections.new('Nave'); sc.collection.children.link(colnave)
        for n in n_nave | n_extra:
            o = bpy.data.objects[n]
            for c in list(o.users_collection): c.objects.unlink(o)
            colnave.objects.link(o)
    else:
        for n in n_nave | n_extra:
            if n in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)
    for n in n_luces:
        if n in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)
    propios = [bpy.data.objects[n] for n in n_nuevos if n in bpy.data.objects and n not in n_nave and n not in n_extra and n not in n_luces]
    for o in propios:
        for c in list(o.users_collection): c.objects.unlink(o)
        col.objects.link(o)
    # desplazar la animación (tiras NLA) y repetir los vientos de las plantas
    def desplazar(idb):
        ad = idb.animation_data
        if not ad: return
        for tr in ad.nla_tracks:
            tr.mute = False                               # el importador las deja silenciadas
            for st in tr.strips:
                dur = st.frame_end - st.frame_start
                if st.name.startswith('escena'):
                    st.frame_start_ui = 1 + offset
                else:                                   # viento en bucle de las plantas
                    tot_cap = 5400
                    st.repeat = max(1, math.ceil(tot_cap / max(dur, 1)))
                    st.frame_end_ui = st.frame_start + dur * st.repeat if hasattr(st, 'frame_end_ui') else st.frame_end
    objs_anim = propios + ([bpy.data.objects[n] for n in n_nave if n in bpy.data.objects] if k == 0 else [])
    for o in objs_anim:
        desplazar(o)
        if o.type == 'MESH' and o.data.shape_keys: desplazar(o.data.shape_keys)
    # cámaras: sólo las de las tomas del JSON; lente en mm con sensor vertical 24
    for tm in js['tomas']:
        cam = bpy.data.objects.get(tm['camara'])
        cam.data.sensor_fit = 'VERTICAL'; cam.data.sensor_height = 24.0; cam.data.lens = float(tm['lente_mm'])
        cam.data.clip_start = 0.1; cam.data.clip_end = 200
        camaras_por_toma.append((offset + int(tm['frame_inicio']), cam))
    nombres_toma = {tm['camara'] for tm in js['tomas']}
    for n in n_nuevos:
        if n in bpy.data.objects and bpy.data.objects[n].type == 'CAMERA' and n not in nombres_toma:
            bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)
    rangos[clave] = (1 + offset, offset + N)
    offset += N

TOTAL = offset
sc.frame_start, sc.frame_end = 1, TOTAL
print('TOTAL_CUADROS', TOTAL, 'rangos', rangos)

# marcadores con cámara (los cortes)
for f, cam in sorted(camaras_por_toma, key=lambda x: x[0]):
    m = sc.timeline_markers.new(cam.name, frame=int(f)); m.camera = cam
sc.camera = sorted(camaras_por_toma, key=lambda x: x[0])[0][1]

# visibilidad por escena: cada objeto de la escena se ve sólo en su rango (propiedades booleanas: salto seco, sin interpolar)
for clave, col in colecciones.items():
    a, b = rangos[clave]
    for n_o in [x.name for x in col.all_objects if x is not None]:
        o = bpy.data.objects[n_o]
        for prop in ('hide_render', 'hide_viewport'):
            if a > 1:
                setattr(o, prop, True); o.keyframe_insert(prop, frame=1)
            setattr(o, prop, False); o.keyframe_insert(prop, frame=a)
            if b < TOTAL:
                setattr(o, prop, True); o.keyframe_insert(prop, frame=b + 1)
exec(open(DIR + 'efectos_cap3.py').read())
bpy.ops.wm.save_as_mainfile(filepath=SALIDA, compress=True)
print('GUARDADO', SALIDA, os.path.getsize(SALIDA))
