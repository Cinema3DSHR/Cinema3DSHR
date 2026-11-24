"""Ropa real para los personajes de CC4 (cap. 1 «La mujer que volvió de la muerte»): CAMISA de manga larga con cuello abierto, botonadura y puños, PANTALÓN con cinturón y botamangas, ZAPATOS.
Se generan del propio cuerpo (heredan pesos: se deforman con las animaciones de Mixamo) y se exportan al GLB del personaje. Reemplaza al traje espacial.
Uso: /opt/tools/blendenv/bin/python ropa_noir.py -- nombre(aiden|kate) variante(gabriel|elena)"""
import bpy, bmesh, sys, os, math, random
sys.path.insert(0, '/home/user/cap3')
sys.path.insert(0, '/home/user/Cinema3DSHR/producciones/p011_a_la_deriva/herramientas/personajes_c3')
import traje_futurista as TF
from mathutils import Vector, Matrix
A = sys.argv[sys.argv.index('--') + 1:]; nombre, variante = A[0], A[1]
DIRP = '/home/user/cap3/pers/'
bpy.ops.wm.open_mainfile(filepath=f'{DIRP}{nombre}.blend')
sc = bpy.context.scene
for o in list(bpy.data.objects):
    if o.name.startswith(('TRAJE_', 'SUELA_', 'BOTA_LUZ_', 'VIVO_', 'EMBLEMA', 'COLLAR', 'CAMISA', 'PANTALON', 'CINTURON', 'BOTON', 'PUNO', 'ZAPATO')): bpy.data.objects.remove(o)
for m in list(bpy.data.materials):
    if m.name.startswith(('traje_', 'ropa_')) and m.users == 0: bpy.data.materials.remove(m)
dst = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
body = next(o for o in bpy.data.objects if o.name.endswith('Base_Body'))
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
H = max(p.z for p in pts) - min(p.z for p in pts); S = H / 1.7
dst.animation_data_create(); dst.animation_data.action = None
for pb in dst.pose.bones:
    pb.rotation_mode = 'QUATERNION'; pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.scale = (1, 1, 1)
bpy.context.view_layer.update()
P = 'EM3D_Base_'
K = 1.0 / body.matrix_world.to_scale().x      # el cuerpo está en cm (escala 0.01): los márgenes locales deben multiplicarse
def W(h, punta='head'):
    pb = dst.pose.bones[P + h]; return dst.matrix_world @ (pb.head if punta == 'head' else pb.tail)

# trajes del script original: sólo se aprovechan los PIES (envolvente convexa con pesos); lo demás se borra
piezas = TF.construir(dst, body, P, H)
for o in list(bpy.data.objects):
    if o.name.startswith(('TRAJE_MONO', 'TRAJE_BOTAS', 'COLLAR', 'VIVO_', 'BOTA_LUZ_', 'EMBLEMA')): bpy.data.objects.remove(o)
def mat(nombre_, col, rough, sheen=0.0, coat=0.0):
    m = bpy.data.materials.new(nombre_); m.use_nodes = True; p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*col, 1); p.inputs['Roughness'].default_value = rough
    for k, v in (('Sheen Weight', sheen), ('Coat Weight', coat)):
        try: p.inputs[k].default_value = v
        except Exception: pass
    return m
if variante == 'gabriel':
    c_top, c_bot, c_zap = (0.60, 0.61, 0.64), (0.035, 0.036, 0.042), (0.012, 0.010, 0.010)       # camisa clara (gris azulado), pantalón negro, zapatos negros
else:
    c_top, c_bot, c_zap = (0.30, 0.035, 0.07), (0.025, 0.025, 0.03), (0.012, 0.010, 0.010)         # chaqueta borravino, pantalón oscuro
m_top = mat('ropa_camisa', c_top, 0.82, sheen=0.5); m_bot = mat('ropa_pantalon', c_bot, 0.78, sheen=0.3); m_zap = mat('ropa_zapato', c_zap, 0.22, coat=0.6)
m_cint = mat('ropa_cinturon', (0.02, 0.014, 0.01), 0.35); m_boton = mat('ropa_boton', (0.8, 0.8, 0.78), 0.3)
for o in bpy.data.objects:
    if o.name.startswith('TRAJE_PIE'): o.data.materials.clear(); o.data.materials.append(m_zap); o.name = o.name.replace('TRAJE_PIE', 'ZAPATO')

def pesos_dominantes(k_):
    return lambda n: n.startswith(k_)
zank = 0.115 * S
cadera = (W('L_Thigh').z + W('R_Thigh').z) / 2
cuello_z = W('NeckTwist01').z
def recortar(obj, z, borrar_debajo):
    """Corte limpio por un plano horizontal (nada de bordes dentados)."""
    bm = bmesh.new(); bm.from_mesh(obj.data); mw = obj.matrix_world
    pco = mw.inverted() @ Vector((0, 0, z)); pno = mw.inverted().to_3x3() @ Vector((0, 0, 1))
    geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=pco, plane_no=pno, clear_inner=borrar_debajo, clear_outer=not borrar_debajo)
    bm.to_mesh(obj.data); bm.free()
def arrugas(obj, fuerza, escala, semilla):
    """Arrugas y pliegues: desplazamiento con ruido sobre la forma del cuerpo (se aplica ANTES del armature para que se deforme con el esqueleto)."""
    tex = bpy.data.textures.new('arr_' + obj.name, 'CLOUDS'); tex.noise_scale = escala; tex.noise_depth = 4
    tex.noise_basis = 'ORIGINAL_PERLIN'
    md = obj.modifiers.new('Arrugas', 'DISPLACE'); md.texture = tex; md.strength = fuerza; md.mid_level = 0.0; md.texture_coords = 'OBJECT'
    sub = obj.modifiers.new('Sub', 'SUBSURF'); sub.levels = 1; sub.subdivision_type = 'SIMPLE'
    bpy.context.view_layer.objects.active = obj
    for o_ in bpy.data.objects: o_.select_set(False)
    obj.select_set(True)
    for nm_ in ('Sub', 'Arrugas'):                         # los pliegues van primero (antes del Armature) y se aplican
        try: bpy.ops.object.modifier_move_to_index(modifier=nm_, index=0)
        except Exception as e: print('no se movió', nm_, e)
    for nm_ in ('Arrugas', 'Sub'):
        try: bpy.ops.object.modifier_apply(modifier=nm_)
        except Exception as e: print('no se aplicó', nm_, e)

# ── CAMISA: torso + brazos hasta la muñeca, dos vueltas de holgura, faldón que baja bajo el cinturón, escote abierto
camisa = TF._region(sc, body, lambda n: n.startswith(('Hip', 'Pelvis', 'Waist', 'Spine', 'L_Clavicle', 'R_Clavicle', 'L_Upperarm', 'R_Upperarm', 'L_Forearm', 'R_Forearm', 'L_Elbow', 'R_Elbow', 'L_Breast', 'R_Breast')),
                    0.026 * S * K, 'CAMISA', m_top, zmin=cadera - 0.115 * S, zmax=cuello_z - 0.012 * S)
recortar(camisa, cadera - 0.085 * S, True)                                     # dobladillo recto
# ── PANTALÓN: de la cintura a los tobillos, algo suelto, con botamangas que tapan el borde del zapato
pantalon = TF._region(sc, body, lambda n: n.startswith(('Hip', 'Pelvis', 'L_Thigh', 'R_Thigh', 'L_Calf', 'R_Calf', 'L_Knee', 'R_Knee')) and not n.startswith(('L_Foot', 'R_Foot')),
                      0.030 * S * K, 'PANTALON', m_bot, zmin=zank + 0.01 * S, zmax=cadera + 0.045 * S)
recortar(pantalon, zank + 0.012 * S, True)
arrugas(camisa, 0.0090 * S * K, 0.10 * K, 1); arrugas(pantalon, 0.0075 * S * K, 0.14 * K, 2)
mwb = body.matrix_world
vb = [mwb @ v.co for v in body.data.vertices]
def radio_a_altura(z, tol=0.012):
    pts_ = [p for p in vb if abs(p.z - z) < tol * S]
    cx = sum(p.x for p in pts_) / len(pts_); cy = sum(p.y for p in pts_) / len(pts_)
    return cx, cy, max((Vector((p.x - cx, p.y - cy, 0)).length) for p in pts_), min(p.y for p in pts_)
# ── puños: anillo al final de cada antebrazo, del ancho real de la muñeca + la holgura de la manga
def anillo_pun(lado):
    mano = W(f'{lado}_Hand'); ante = W(f'{lado}_Forearm')
    dir_ = (mano - ante).normalized(); c = mano - dir_ * 0.022 * S
    cerca = [p for p in vb if (p - c).length < 0.07 * S]
    r_m = max(0.025 * S, sum(((p - c) - dir_ * (p - c).dot(dir_)).length for p in cerca) / max(len(cerca), 1) * 1.3)
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=False, segments=24, radius1=r_m + 0.030 * S, radius2=r_m + 0.030 * S, depth=0.040 * S)
    me = bpy.data.meshes.new(f'PUNO_{lado}'); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(f'PUNO_{lado}', me); sc.collection.objects.link(o); o.data.materials.append(m_top)
    for pl in me.polygons: pl.use_smooth = True
    z_ax = dir_; x_ax = Vector((0, 1, 0)).cross(z_ax).normalized() if abs(z_ax.y) < 0.95 else Vector((1, 0, 0)); y_ax = z_ax.cross(x_ax)
    M = Matrix(((x_ax.x, y_ax.x, z_ax.x, c.x), (x_ax.y, y_ax.y, z_ax.y, c.y), (x_ax.z, y_ax.z, z_ax.z, c.z), (0, 0, 0, 1)))
    TF._al_hueso(dst, o, P + f'{lado}_Forearm', M); return o
anillo_pun('L'); anillo_pun('R')
# ── cinturón: del ancho real de la cadera
zc = cadera + 0.045 * S
cx, cy, Rc, yf = radio_a_altura(zc)
cinto = TF._toro(sc, 'CINTURON', Rc + 0.034 * S, 0.0125 * S, m_cint, esc=(1.0, 1.0, 1.0))
TF._al_hueso(dst, cinto, P + 'Pelvis', Matrix.Translation(Vector((cx, cy, zc))))
hebilla = TF._caja(sc, 'CINTURON_hebilla', (0.034 * S, 0.006 * S, 0.026 * S), Matrix.Translation(Vector((cx, yf - 0.034 * S - 0.003 * S, zc))), m_boton, bisel=0.002)
TF._al_hueso(dst, hebilla, P + 'Pelvis', Matrix.Translation(Vector((cx, yf - 0.034 * S - 0.003 * S, zc))))
# ── cuello abierto: banda de cuello alrededor del escote + botones sobre la tapeta, apoyados en el frente real del torso
zn = cuello_z - 0.012 * S
cxn, cyn, Rn, yfn = radio_a_altura(zn, 0.012)
col = TF._toro(sc, 'COLLAR', Rn + 0.026 * S, 0.011 * S, m_top, esc=(1.0, 1.0, 1.0))
TF._al_hueso(dst, col, P + 'NeckTwist01', Matrix.Translation(Vector((cxn, cyn, zn))))
for i in range(5):
    zb = cuello_z - 0.075 * S - i * ((cuello_z - cadera) * 0.17)
    cxb, cyb, Rb, yfb = radio_a_altura(zb, 0.014)
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.0078 * S)
    me = bpy.data.meshes.new(f'BOTON_{i}'); bm.to_mesh(me); bm.free(); me.materials.append(m_boton)
    o = bpy.data.objects.new(f'BOTON_{i}', me); sc.collection.objects.link(o)
    TF._al_hueso(dst, o, P + ('Spine02' if i < 3 else 'Spine01'), Matrix.Translation(Vector((cxb, yfb - 0.026 * S - 0.002 * S, zb))))
KEEP = {'V_Open', 'V_Explosive', 'V_Dental_Lip', 'V_Tight_O', 'V_Tight', 'V_Wide', 'V_Affricate', 'Brow_Raise_Inner_Left', 'Brow_Raise_Inner_Right', 'Brow_Drop_Left', 'Brow_Drop_Right', 'Brow_Raise_Left', 'Brow_Raise_Right'}
for ob in bpy.data.objects:
    if ob.type == 'MESH' and ob.data.shape_keys:
        for kb in list(ob.data.shape_keys.key_blocks)[1:]:
            if kb.name not in KEEP and not kb.name.startswith(('Eye_', 'Mouth_', 'Cheek_', 'Nose_', 'Jaw_', 'Tongue_')): ob.shape_key_remove(kb)
out = f'{DIRP}{nombre}_noir.glb'
bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', export_morph=True, export_animations=True, export_animation_mode='ACTIONS', export_skins=True, export_apply=False, export_yup=True, export_image_format='AUTO')
print('EXPORTADO', out, os.path.getsize(out))
bpy.ops.wm.save_as_mainfile(filepath=f'{DIRP}{nombre}_noir.blend')
