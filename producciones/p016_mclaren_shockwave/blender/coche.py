"""p016 · McLaren F1 original (GLB del dueño): importación sin tocar geometría ni texturas, versión F1 (las piezas [LM] y las alternativas «(2)» quedan
ocultas, no borradas), ruedas del lado izquierdo copiadas de las del derecho y GIRADAS 180° (no espejadas), pivotes para rodar, luces y matrículas «3D SHR».
Orientación del modelo importado: frente = −Y, atrás = +Y, derecha = −X, izquierda = +X, suelo de las ruedas en z = −0,64."""
import math
import os
import bpy
from mathutils import Vector, Matrix, Euler

GLB = os.environ.get("MCLAREN_GLB", "/home/user/Cinema3DSHR/producciones/p016_mclaren_shockwave/modelo/mclaren_f1_original.glb")
RADIO = 0.345            # radio del neumático
Z_SUELO = -0.64          # z del punto más bajo de las ruedas en el modelo
OCULTAS = ("[LM]",)
ALTERNATIVAS = ("bonnet_ok (2)", "bump_front_ok (2)", "bump_rear_ok (2)", "door_lr_ok (2)", "door_rr_ok (2)")


def _textura_placa(ruta, texto="3D SHR", ancho=1024, alto=300):
    from PIL import Image, ImageDraw, ImageFont
    im = Image.new("RGB", (ancho, alto), (244, 244, 238))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((6, 6, ancho - 7, alto - 7), radius=26, outline=(20, 20, 20), width=10)
    # banda azul a la izquierda (estilo placa), texto grande centrado
    d.rectangle((16, 16, 120, alto - 17), fill=(20, 60, 160))
    fuente = None
    for f in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"):
        if os.path.exists(f):
            fuente = ImageFont.truetype(f, 190)
            break
    if fuente is None:
        fuente = ImageFont.load_default()
    bb = d.textbbox((0, 0), texto, font=fuente)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    x0 = 120 + (ancho - 120 - tw) / 2 - bb[0]
    d.text((x0, (alto - th) / 2 - bb[1]), texto, font=fuente, fill=(15, 15, 15))
    d.text((34, alto - 80), "UK", font=fuente.font_variant(size=46) if hasattr(fuente, "font_variant") else fuente, fill=(255, 255, 255))
    im.save(ruta)
    return ruta


def cargar(col, ruta_placa="/tmp/placa_3dshr.png"):
    """Importa el GLB dentro de `col` y devuelve un diccionario con la raíz, los pivotes de las ruedas y las luces."""
    antes = set(bpy.data.objects.keys())
    bpy.ops.import_scene.gltf(filepath=GLB)
    nombres = [n for n in bpy.data.objects.keys() if n not in antes]
    nuevos = [bpy.data.objects[n] for n in nombres]
    raiz = bpy.data.objects.new("MCLAREN", None)
    col.objects.link(raiz)
    oc = bpy.data.collections.new("MCLAREN_variantes_no_usadas")
    col.children.link(oc)
    piezas = []
    for o in nuevos:
        if o.type == "EMPTY":
            continue
        for c in list(o.users_collection):
            c.objects.unlink(o)
        col.objects.link(o)
        piezas.append(o)
    for o in nuevos:
        if o.type == "EMPTY":
            bpy.data.objects.remove(o)
    for o in piezas:
        o.parent = raiz
        usar = not (any(t in o.name for t in OCULTAS) or o.name in ALTERNATIVAS)
        if not usar:
            col.objects.unlink(o)
            oc.objects.link(o)
            o.hide_render = True
            o.hide_viewport = True
    # ───── ruedas: las dos que trae el modelo son las del lado derecho (−X)
    res = {"raiz": raiz, "piezas": [o for o in piezas if not o.hide_render], "pivotes": {}, "ruedas": {}}
    der = {"FR": bpy.data.objects["wheel[F1]"], "RR": bpy.data.objects["wheel[F1] (2)"]}
    for k, w in der.items():
        for c in list(w.users_collection):
            c.objects.unlink(w)
        col.objects.link(w)
        w.hide_render = False
        w.hide_viewport = False
        w.parent = None
        bpy.context.view_layer.objects.active = w
        for s in bpy.context.selected_objects:
            s.select_set(False)
        w.select_set(True)
        bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
        centro = w.matrix_world.translation.copy()
        # pivote en el centro de la rueda: el eje del giro es su X local
        pv = bpy.data.objects.new(f"pivote_{k}", None)
        col.objects.link(pv)
        pv.location = centro
        pv.parent = raiz
        w.parent = pv
        w.location = (0, 0, 0)
        res["pivotes"][k] = pv
        res["ruedas"][k] = w
        # copia para el lado izquierdo: misma pieza, GIRADA 180° alrededor de la vertical (no espejada) y puesta a la misma altura y distancia del eje
        izq = "FL" if k == "FR" else "RL"
        w2 = w.copy()
        w2.data = w.data.copy()
        w2.name = f"rueda_{izq}_copia_girada"
        col.objects.link(w2)
        pv2 = bpy.data.objects.new(f"pivote_{izq}", None)
        col.objects.link(pv2)
        pv2.location = (-centro.x, centro.y, centro.z)
        pv2.parent = raiz
        w2.parent = pv2
        w2.location = (0, 0, 0)
        w2.rotation_mode = "XYZ"          # el importador de glTF deja los objetos en cuaterniones
        w2.rotation_euler = Euler((0, 0, math.pi), "XYZ")
        res["pivotes"][izq] = pv2
        res["ruedas"][izq] = w2
    # ───── matrícula trasera: el modelo ya trae el rectángulo con UV 0..1 → se le pone la textura «3D SHR»
    _textura_placa(ruta_placa)
    img = bpy.data.images.load(ruta_placa)
    img.pack()
    mp = bpy.data.materials["carplate"]
    nt = mp.node_tree
    b = nt.nodes["Principled BSDF"]
    tx = nt.nodes.new("ShaderNodeTexImage")
    tx.image = img
    nt.links.new(tx.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.35
    # ───── matrícula delantera: el modelo no trae; se agrega una placa sobre el paragolpes con la misma textura
    mf = bpy.data.materials.new("carplate_frontal")
    mf.use_nodes = True
    bf = mf.node_tree.nodes["Principled BSDF"]
    tf = mf.node_tree.nodes.new("ShaderNodeTexImage")
    tf.image = img
    mf.node_tree.links.new(tf.outputs["Color"], bf.inputs["Base Color"])
    bf.inputs["Roughness"].default_value = 0.35
    verts = [(-0.147, -2.345, -0.455), (0.147, -2.345, -0.455), (0.147, -2.345, -0.37), (-0.147, -2.345, -0.37)]
    me = bpy.data.meshes.new("placa_frontal")
    me.from_pydata(verts, [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new(name="UVMap")
    for lp, (u, v) in zip(me.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        uv.data[lp.index].uv = (u, v)
    me.materials.append(mf)
    pf = bpy.data.objects.new("placa_frontal", me)
    col.objects.link(pf)
    pf.parent = raiz
    res["placa_frontal"] = pf
    raiz.location = (0, 0, -Z_SUELO)
    return res


def girar_ruedas(coche, distancia):
    """Gira las 4 ruedas lo que corresponde a avanzar `distancia` metros hacia el frente (−Y): θ = d/r alrededor del eje X (arriba de la rueda va hacia −Y)."""
    th = distancia / RADIO
    for k, p in coche["pivotes"].items():
        p.rotation_euler = (th, 0, 0)
