"""Los efectos de la guía «Efectos visuales en Godot (Extracción Vertical)» aplicados a las pasadas de render_pdf.py:
A material plano por orientación · B toon con sombra y brillo duro · C contorno de silueta (casco invertido) · D líneas de pantalla (profundidad + 4 tonos) · E combinado.
Uso: python efectos_pdf.py PREFIJO"""
import sys, json, numpy as np
from PIL import Image, ImageFilter, ImageDraw, ImageFont
PRE = sys.argv[1]
def rgb(n): return np.asarray(Image.open(f'{PRE}_{n}.png').convert('RGB'), dtype=np.float32) / 255.0
color, arcilla, nor, cla = rgb('color'), rgb('arcilla'), rgb('normales'), rgb('clases')
pro = np.asarray(Image.open(f'{PRE}_prof.png')).astype(np.float32); pro = pro / (65535.0 if pro.max() > 255 else 255.0)
D = json.load(open(f'{PRE}_datos.json')); Hh, Ww = pro.shape
z = pro * 128.0                                                                            # profundidad en metros (a lo largo del eje de la cámara)
lum = lambda x: x[..., 0] * 0.299 + x[..., 1] * 0.587 + x[..., 2] * 0.114
cielo = z < 0.5
n = nor * 2 - 1
PAPEL = np.array([0.97, 0.965, 0.95], dtype=np.float32); FONDO = 0.84; TINTA = np.array([0.07, 0.07, 0.08], dtype=np.float32)
def sup(m, r=0.7): return np.asarray(Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r)), dtype=np.float32) / 255.0
def es(c, tol=0.3): return np.all(np.abs(cla - np.array(c, dtype=np.float32)) < tol, axis=-1)
# ───── A · material plano por orientación (sin luz): arriba 1,0 · abajo 0,8 · de frente/fondo 0,93 · de costado 0,86 ─────
nz, nx, ny = n[..., 2], n[..., 0], n[..., 1]                                              # Blender: z arriba, y hacia el fondo (en Godot: z hacia la cámara)
t = np.where(nz > 0.6, 1.0, np.where(nz < -0.6, 0.8, np.where(np.abs(ny) > np.abs(nx), 0.93, 0.86)))
lit0 = np.clip(lum(arcilla) / 0.80, 0, 1); alb0 = np.clip(lum(color) / np.maximum(lit0, 0.25), 0, 1); tint0 = 0.50 + 0.50 * np.clip(alb0 * 1.3, 0, 1)
A = PAPEL[None, None, :] * (t * (1 - 0.65 + 0.65 * tint0))[..., None]; A[cielo] = FONDO
# ───── aristas: profundidad (siluetas) + clases + pliegues (normales a más de 25°) ─────
def lin_edges(zz, th=0.04, w=1.5):
    e = np.zeros(zz.shape, dtype=np.float32); k = int(round(w))
    for dx, dy in ((k, 0), (0, k), (-k, 0), (0, -k)):
        zn = np.roll(np.roll(zz, dx, 1), dy, 0); e = np.maximum(e, (np.abs(zn - zz) > th * zz).astype(np.float32))
    return e
def borde_img(x, k=1):
    g = np.maximum(np.abs(np.roll(x, -k, 1) - x), np.abs(np.roll(x, -k, 0) - x)); g = g.max(axis=-1) if g.ndim == 3 else g
    g[-k:, :] = 0; g[:, -k:] = 0; return g
e_prof = lin_edges(np.maximum(z, 0.3), 0.04, 1.5)
e_clase = (borde_img(cla) > 0.3).astype(np.float32)
mismo = np.ones_like(e_prof, dtype=bool)
plieg = np.zeros_like(e_prof)
for dx, dy in ((1, 0), (0, 1)):
    nn = np.roll(np.roll(n, -dx, 1), -dy, 0); zn = np.roll(np.roll(z, -dx, 1), -dy, 0)
    cont = np.abs(zn - z) < 0.03 * np.maximum(z, 0.3)                                      # sólo donde la superficie es continua: ahí un salto de normal es un pliegue real
    plieg = np.maximum(plieg, ((np.abs((n * nn).sum(-1)) < 0.90) & cont).astype(np.float32))
plieg[cielo] = 0
def ensanchar(m, r):
    out = m.copy()
    for dx in range(-r, r + 1):
        for dy in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r + 1: out = np.maximum(out, np.roll(np.roll(m, dx, 1), dy, 0))
    return out
# ───── C · contorno de silueta (casco invertido): ancho = 0,012 · clamp(d·0,35 ; 0,6 ; 3,0) en metros → píxeles según la distancia ─────
sil = np.maximum(e_prof, e_clase)
pix_m = (2 * np.maximum(z, 1.0) * np.tan(D['fov_v'] / 2)) / Hh                              # metros por píxel a esa distancia
ancho_px = np.clip(0.012 * np.clip(z * 0.35, 0.6, 3.0) * 1.1 / pix_m, 1.0, 2.7)
silueta = np.zeros_like(sil)
for rr, (a, b) in ((0, (0, 1.5)), (1, (1.5, 9))):
    sel = sil * ((ancho_px >= a) & (ancho_px < b)); silueta = np.maximum(silueta, ensanchar(sel, rr))
silueta = sup(silueta, 0.55)
def tinta(img, m, k=1.0): return img * (1 - (m * k)[..., None]) + TINTA[None, None, :] * (m * k)[..., None]
C = tinta(A, silueta)
# ───── B · toon con sombra proyectada y brillo duro (bandas, shadow_min 0,55, brillo step, borde de luz) ─────
lit = np.clip(lum(arcilla) / 0.80, 0, 1)
band = np.floor(lit * 3.0 + 0.5) / 3.0; sombra = 0.55 + 0.45 * band
albedo = np.clip(lum(color) / np.maximum(lit, 0.25), 0, 1)                                    # el color original, sólo como tono de gris
tint = 0.58 + 0.42 * np.clip(albedo * 1.35, 0, 1)
# vector a la cámara por píxel (posición del punto reconstruida con la profundidad)
yy, xx = np.mgrid[0:Hh, 0:Ww].astype(np.float32); sx = (xx + 0.5) / Ww * 2 - 1; sy = 1 - (yy + 0.5) / Hh * 2
tv = np.tan(D['fov_v'] / 2); th_ = tv * Ww / Hh
fwd = np.array(D['adelante']); rig = np.array(D['derecha']); upv = np.array(D['arriba']); cpos = np.array(D['camara'])
ray = fwd[None, None, :] + rig[None, None, :] * (sx * th_)[..., None] + upv[None, None, :] * (sy * tv)[..., None]
P = cpos[None, None, :] + ray * z[..., None]
V = cpos[None, None, :] - P; V /= np.maximum(np.linalg.norm(V, axis=-1, keepdims=True), 1e-6)
Ld = -np.array(D['sol_dir'])[None, None, :]
Hh_ = Ld + V; Hh_ /= np.maximum(np.linalg.norm(Hh_, axis=-1, keepdims=True), 1e-6)
ndl = np.clip((n * Ld).sum(-1), 0, 1)
espec = (np.power(np.clip((n * Hh_).sum(-1), 0, 1), 24) * (lit > 0.7)) > 0.92
rim = np.power(1 - np.clip((n * V).sum(-1), 0, 1), 3.0) * ndl * 0.18
B = (tint * sombra + rim)[..., None] * PAPEL[None, None, :]; B = np.where(espec[..., None], np.clip(B + 0.18, 0, 1), B); B[cielo] = FONDO
# ───── D · líneas de pantalla: profundidad con umbral 0,04 y la imagen en 4 tonos de papel ─────
g4 = np.floor(lum(color) * 4.0 + 0.5) / 4.0
Dm = (g4 * 0.2 + 0.8)[..., None] * np.ones((1, 1, 3), dtype=np.float32); Dm[cielo] = FONDO
zz = np.maximum(z, 0.3); k2 = 2
segunda = np.maximum(np.abs(np.roll(zz, k2, 1) + np.roll(zz, -k2, 1) - 2 * zz), np.abs(np.roll(zz, k2, 0) + np.roll(zz, -k2, 0) - 2 * zz)) > 0.012 * zz
segunda &= ~cielo
Dm = tinta(Dm, sup(np.maximum(lin_edges(zz, 0.04, 1.5), segunda.astype(np.float32) * 0.8), 0.5))
# ───── E · combinado recomendado: toon con sombra + silueta + pliegues finos ─────
E = tinta(B, sup(plieg, 0.5), 0.75); E = tinta(E, silueta, 0.95)
def guardar(img, nombre): Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)).save(f'{PRE}_{nombre}.png')
for img, nom in ((A, 'A_material_plano'), (B, 'B_toon_sombra_brillo'), (C, 'C_contorno_silueta'), (Dm, 'D_lineas_de_pantalla'), (E, 'E_combinado')): guardar(img, nom)
f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 24)
titulos = ['A · Material plano', 'B · Toon + sombra', 'C · Contorno', 'D · Líneas de pantalla', 'E · Combinado']
t = Image.new('RGB', (Ww * 5 + 60, Hh + 60), (30, 30, 34)); dr = ImageDraw.Draw(t)
for i, nom in enumerate(('A_material_plano', 'B_toon_sombra_brillo', 'C_contorno_silueta', 'D_lineas_de_pantalla', 'E_combinado')):
    t.paste(Image.open(f'{PRE}_{nom}.png'), (10 + i * (Ww + 10), 50)); dr.text((20 + i * (Ww + 10), 12), titulos[i], font=f, fill=(240, 240, 240))
t.save(f'{PRE}_comparativa.png'); print('OK')
