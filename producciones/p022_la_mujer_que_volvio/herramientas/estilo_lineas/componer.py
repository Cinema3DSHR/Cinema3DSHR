"""Junta las capas de render_estilo.py (beauty, plano, lineas_c, clases) en la imagen final de un estilo: gris/niveles, rojo selectivo y contornos.
Uso: python componer.py ESTILO PREFIJO SALIDA.png"""
import sys, os, numpy as np
from PIL import Image, ImageFilter
ESTILO, PRE, SAL = sys.argv[1], sys.argv[2], sys.argv[3]
L = lambda n: np.asarray(Image.open(f'{PRE}_{n}.png').convert('RGB'), dtype=np.float32) / 255.0
PASADAS = os.path.exists(f'{PRE}_normales.png')
beauty, cla = L('beauty'), L('clases')
lin = L('lineas_c') if not PASADAS else None; plano = np.ones_like(beauty)               # fondo de las líneas = blanco emisivo (constante: no hace falta renderizarlo)
lum = lambda x: x[..., 0] * 0.2126 + x[..., 1] * 0.7152 + x[..., 2] * 0.0722
def es(c, tol=0.30): return np.all(np.abs(cla - np.array(c, dtype=np.float32)) < tol, axis=-1)
def grad(x):                                                                              # magnitud del gradiente (diferencias finitas) de una imagen HxW o HxWxC
    gx = np.abs(np.roll(x, -1, axis=1) - x); gy = np.abs(np.roll(x, -1, axis=0) - x)
    g = np.maximum(gx, gy); g[-1, :] = 0; g[:, -1] = 0; g[0, :] = 0; g[:, 0] = 0
    return g.max(axis=-1) if g.ndim == 3 else g
if PASADAS:                                                                              # líneas en espacio de imagen: normales (aristas) + profundidad (planos) + clases (siluetas)
    nor = np.asarray(Image.open(f'{PRE}_normales.png').convert('RGB'), dtype=np.float32) / 255.0
    pro = np.asarray(Image.open(f'{PRE}_prof.png').convert('L'), dtype=np.float32) / 255.0
    e_n = grad(nor) > 0.28; e_d = grad(pro) > 0.020; e_c = grad(cla) > 0.30
    borde = ((e_n | e_d | e_c) & ~es((1, 1, 1), 0.25)).astype(np.float32)        # el láser (rojo) no lleva contorno
    trazo = np.clip(borde + 0.6 * np.maximum(np.roll(borde, 1, 0), np.roll(borde, 1, 1)), 0, 1)       # ~1,5 px
    trazo = np.asarray(Image.fromarray((trazo * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6)), dtype=np.float32) / 255.0
else:
    trazo = np.clip(lum(plano) - lum(lin), 0, 1)                                          # 0…1: dónde hay línea (Freestyle, ya con suavizado)
    trazo = np.asarray(Image.fromarray((trazo * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.45)), dtype=np.float32) / 255.0
trazo = np.clip(trazo * 1.25, 0, 1)
m_rojo = es((1, 1, 1), 0.25); m_pj = es((1, 0, 0)); m_arma = es((0, 1, 0)); m_arq = es((0, 0, 1)); m_veg = es((1, 1, 0)); m_obj = es((1, 0, 1)); m_auto = es((0, 1, 1))
m_fondo = np.all(cla < 0.12, axis=-1)
def niveles(v, cortes, tonos):
    out = np.full_like(v, tonos[-1])
    for c, t in reversed(list(zip(cortes, tonos[:-1]))): out = np.where(v < c, t, out)
    return out
def suave(m, r=0.8): return np.asarray(Image.fromarray((m.astype(np.float32) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r)), dtype=np.float32)[..., None] / 255.0
v = lum(beauty)
v = np.asarray(Image.fromarray((np.clip(v, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.9)), dtype=np.float32) / 255.0       # quita el grano de las 6 muestras antes de cuantizar
yy, xx = np.mgrid[0:v.shape[0], 0:v.shape[1]]
rayado = (((xx + yy) % 7) < 1.2).astype(np.float32)                                        # trama diagonal de tinta para las sombras
if ESTILO == 'A':                                                                       # INK FILTER: escala de grises con contraste de ilustración + contornos + rojo selectivo
    g = np.clip((v - 0.5) * 1.35 + 0.52, 0, 1)
    base = np.repeat(g[..., None], 3, axis=2)
    sombra = np.clip((0.55 - v) / 0.25, 0, 1) * (1 - m_fondo)
    base = base * (1 - 0.55 * (rayado * sombra)[..., None])
elif ESTILO == 'B':                                                                     # TECHNICAL MATERIALS: maqueta blanca/gris, 3 niveles de sombra
    g = niveles(v, (0.46, 0.74), (0.60, 0.80, 0.96)); base = np.repeat(g[..., None], 3, axis=2)
elif ESTILO == 'C':                                                                     # HYBRID: arquitectura técnica + personajes originales (volumen y color contenidos)
    g = niveles(v, (0.46, 0.74), (0.60, 0.80, 0.96)); tec = np.repeat(g[..., None], 3, axis=2)
    gris = np.repeat(v[..., None], 3, axis=2); pj = 0.45 * beauty + 0.55 * gris; pj = np.round(pj * 7) / 7.0                     # 7 niveles: conserva el volumen
    base = np.where(m_pj[..., None], suave(m_pj, 0.6) * pj + (1 - suave(m_pj, 0.6)) * tec, tec)
else:                                                                                   # D: PLANO DIBUJADO: tonos planos por clase, 3 niveles, fondo gris medio
    vd = np.asarray(Image.fromarray((np.clip(v, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.6)), dtype=np.float32) / 255.0; g = np.round(vd * 4) / 4.0
    base = np.repeat(g[..., None], 3, axis=2)
fondo_tono = {'A': None, 'B': 0.95, 'C': 0.95, 'D': 0.62}[ESTILO]
if fondo_tono is not None:
    mf = suave(m_fondo, 0.7); base = base * (1 - mf) + fondo_tono * mf
# rojo selectivo: sangre, tubo, extintor y láser mantienen su color (con sus 3 niveles)
rojo_col = np.stack([np.clip(beauty[..., 0] * 1.15, 0, 1), beauty[..., 1] * 0.6, beauty[..., 2] * 0.6], axis=-1)
mr = suave(m_rojo, 0.6)
img = base * (1 - mr) + rojo_col * mr
img = img * (1 - trazo[..., None]) + np.array([0.04, 0.04, 0.05], dtype=np.float32) * trazo[..., None]
Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)).save(SAL)
print('OK', SAL)
