"""p017 · teléfono y saldo: celular 3D con pantalla emisiva (notificación, app del banco) y un SALDO tipo odómetro (cada dígito rueda en 3D con su propia tira),
más el tablero (HUD) que acompaña las compras: SALDO + etiquetas «−250.000». Los dígitos son planos con una tira de 0–9 cuyo desplazamiento se anima:
el número cambia de verdad en pantalla, no por cortes."""
import math
import os
import bpy
from mathutils import Vector
import lib
from lib import *

TIRA = "/tmp/tira_digitos.png"
FUENTE_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def _tira_digitos(alto_celda=200, ancho=130):
    from PIL import Image, ImageDraw, ImageFont
    f = ImageFont.truetype(FUENTE_B, 150)
    # 11 celdas: 0..9 y otro 0 repetido para rodar de 9 a 0 sin salto
    im = Image.new("RGBA", (ancho, alto_celda * 11), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i in range(11):
        n = str(i % 10)
        bb = d.textbbox((0, 0), n, font=f)
        d.text(((ancho - (bb[2] - bb[0])) / 2 - bb[0], i * alto_celda + (alto_celda - (bb[3] - bb[1])) / 2 - bb[1] - 6), n, font=f, fill=(255, 255, 255, 255))
    im.save(TIRA)
    return TIRA, alto_celda * 11, alto_celda


def texto_png(ruta, texto, tam=120, color=(255, 255, 255, 255), fondo=None, pad=18, negrita=True):
    from PIL import Image, ImageDraw, ImageFont
    f = ImageFont.truetype(FUENTE_B if negrita else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", tam)
    d0 = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    bb = d0.textbbox((0, 0), texto, font=f)
    w, h = bb[2] - bb[0] + 2 * pad, bb[3] - bb[1] + 2 * pad
    im = Image.new("RGBA", (w, h), fondo or (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((pad - bb[0], pad - bb[1]), texto, font=f, fill=color)
    im.save(ruta)
    return ruta, w, h


def mat_imagen_emisivo(nombre, ruta, fuerza=1.0, alfa=True):
    """Material emisivo con una imagen (texto/etiqueta) y transparencia por el canal alfa; no recibe luz: se ve igual en cualquier escena."""
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tx = nt.nodes.new("ShaderNodeTexImage")
    img = bpy.data.images.load(ruta)
    img.pack()
    tx.image = img
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = fuerza
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mz = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(tx.outputs["Color"], em.inputs["Color"])
    nt.links.new(tx.outputs["Alpha"], mz.inputs["Fac"])
    nt.links.new(tr.outputs[0], mz.inputs[1])
    nt.links.new(em.outputs[0], mz.inputs[2])
    nt.links.new(mz.outputs[0], out.inputs["Surface"])
    return m


def plano_xy(nombre, centro, ancho, alto, col, mat, parent=None):
    """Plano vertical que mira hacia −Y (la cámara lo ve de frente desde −Y)."""
    verts = [(-ancho / 2, 0, -alto / 2), (ancho / 2, 0, -alto / 2), (ancho / 2, 0, alto / 2), (-ancho / 2, 0, alto / 2)]
    me = bpy.data.meshes.new(nombre)
    me.from_pydata(verts, [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new(name="UVMap")
    for lp, uvv in zip(me.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        uv.data[lp.index].uv = uvv
    me.materials.append(mat)
    o = bpy.data.objects.new(nombre, me)
    col.objects.link(o) if False else None
    return o


class Odometro:
    """Número de n dígitos con puntos de millar: cada dígito es un plano con la tira 0–9 y una animación de desplazamiento propia."""

    def __init__(self, col, nombre, n_digitos=7, ancho_digito=0.1, alto_digito=0.15, color=(1.0, 1.0, 1.0), fuerza=2.5, con_puntos=True):
        ruta, alto_tira, alto_celda = _tira_digitos()
        self.n = n_digitos
        self.col = col
        self.alto_celda = alto_celda
        self.raiz = bpy.data.objects.new(nombre, None)
        col.objects.link(self.raiz)
        self.mapeos = []
        self.dig = []
        # posiciones de derecha a izquierda (con un punto cada 3 dígitos)
        x = 0.0
        pos = []
        for i in range(n_digitos):
            pos.append(x)
            x -= ancho_digito
            if con_puntos and (i + 1) % 3 == 0 and i + 1 < n_digitos:
                x -= ancho_digito * 0.45
        ancho_total = -x + ancho_digito
        pos = [p + ancho_total / 2 - ancho_digito for p in pos]
        self.ancho_total = ancho_total
        for i in range(n_digitos):
            m = bpy.data.materials.new(f"{nombre}_dig{i}")
            m.use_nodes = True
            nt = m.node_tree
            for nn in list(nt.nodes):
                nt.nodes.remove(nn)
            out = nt.nodes.new("ShaderNodeOutputMaterial")
            tc = nt.nodes.new("ShaderNodeTexCoord")
            mp = nt.nodes.new("ShaderNodeMapping")
            mp.inputs["Scale"].default_value = (1.0, 1.0 / 11.0, 1.0)
            nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])
            tx = nt.nodes.new("ShaderNodeTexImage")
            im = bpy.data.images.load(ruta, check_existing=True)
            im.pack()
            tx.image = im
            tx.extension = "CLIP"
            nt.links.new(mp.outputs["Vector"], tx.inputs["Vector"])
            em = nt.nodes.new("ShaderNodeEmission")
            em.inputs["Color"].default_value = (*color, 1.0)
            em.inputs["Strength"].default_value = fuerza
            tr = nt.nodes.new("ShaderNodeBsdfTransparent")
            mz = nt.nodes.new("ShaderNodeMixShader")
            nt.links.new(tx.outputs["Alpha"], mz.inputs["Fac"])
            nt.links.new(tr.outputs[0], mz.inputs[1])
            nt.links.new(em.outputs[0], mz.inputs[2])
            nt.links.new(mz.outputs[0], out.inputs["Surface"])
            verts = [(-ancho_digito / 2, 0, -alto_digito / 2), (ancho_digito / 2, 0, -alto_digito / 2), (ancho_digito / 2, 0, alto_digito / 2), (-ancho_digito / 2, 0, alto_digito / 2)]
            me = bpy.data.meshes.new(f"{nombre}_d{i}")
            me.from_pydata(verts, [], [(0, 1, 2, 3)])
            uv = me.uv_layers.new(name="UVMap")
            for lp, uvv in zip(me.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
                uv.data[lp.index].uv = uvv
            me.materials.append(m)
            o = bpy.data.objects.new(f"{nombre}_d{i}", me)
            col.objects.link(o)
            o.parent = self.raiz
            o.location = (pos[i], 0, 0)
            o.visible_shadow = False
            self.dig.append(o)
            self.mapeos.append(mp.inputs["Location"])
        if con_puntos:
            from PIL import Image, ImageDraw
            im_p = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
            ImageDraw.Draw(im_p).ellipse((4, 4, 60, 60), fill=(255, 255, 255, 255))
            im_p.save("/tmp/punto_odo.png")
            rp = "/tmp/punto_odo.png"
            mpunto = mat_imagen_emisivo(f"{nombre}_punto", rp, fuerza)
            mpunto.node_tree.nodes["Emission"].inputs["Color"].default_value = (*color, 1.0) if False else (1, 1, 1, 1)
            for i in range(n_digitos):
                if (i + 1) % 3 == 0 and i + 1 < n_digitos:
                    px = pos[i] - ancho_digito * 0.72
                    dz0 = -alto_digito * 0.40
                    dw = ancho_digito * 0.16
                    verts = [(-dw, 0, dz0), (dw, 0, dz0), (dw, 0, dz0 + 2 * dw), (-dw, 0, dz0 + 2 * dw)]
                    me = bpy.data.meshes.new(f"{nombre}_pt{i}")
                    me.from_pydata(verts, [], [(0, 1, 2, 3)])
                    uv = me.uv_layers.new(name="UVMap")
                    for lp, uvv in zip(me.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
                        uv.data[lp.index].uv = uvv
                    me.materials.append(mpunto)
                    o = bpy.data.objects.new(f"{nombre}_pt{i}", me)
                    col.objects.link(o)
                    o.parent = self.raiz
                    o.location = (px, 0, 0)
                    self.dig.append(o)

    def poner(self, valor, f):
        """Fija el número `valor` en el cuadro f (clave de cada dígito; entre claves el dígito rueda de forma lineal)."""
        s = f"{int(valor):0{self.n}d}"[-self.n:]
        for i in range(self.n):
            d = int(s[self.n - 1 - i])          # i = 0 es el dígito de la derecha (unidades)
            v = ((10 - d) % 10) / 11.0          # la imagen se muestrea desde abajo: el dígito d está en la celda (10−d)
            sock = self.mapeos[i]
            sock.default_value = (0.0, v, 0.0)
            sock.keyframe_insert("default_value", frame=int(f))

    def contar(self, desde, hasta, f0, f1, pasos=None):
        """Rueda desde `desde` hasta `hasta` entre los cuadros f0 y f1: cada dígito avanza su propia fracción (el de las unidades gira rapidísimo)."""
        pasos = pasos or max(2, (f1 - f0))
        for k in range(pasos + 1):
            u = k / pasos
            self.poner(desde + (hasta - desde) * u * u * (3 - 2 * u), f0 + (f1 - f0) * u)

    def fin(self):
        for s in self.mapeos:
            nt = s.id_data
            if nt.animation_data and nt.animation_data.action:
                lib._interp_id(nt, "LINEAR")


_n_et = [0]


def etiqueta(col, texto, alto_m=0.2, color=(255, 255, 255, 255), fondo=None, fuerza=1.6, tam=110, pad=22):
    """Cartel 3D con texto (plano emisivo, mira hacia −Y): para rótulos dentro de la escena."""
    _n_et[0] += 1
    ruta, w, h = texto_png(f"/tmp/et_{_n_et[0]}.png", texto, tam=tam, color=color, fondo=fondo, pad=pad)
    ancho_m = alto_m * w / h
    m = mat_imagen_emisivo(f"et_{_n_et[0]}", ruta, fuerza)
    o = plano_xy(f"et_{_n_et[0]}", (0, 0, 0), ancho_m, alto_m, col, m)
    col.objects.link(o)
    o.visible_shadow = False
    return o
