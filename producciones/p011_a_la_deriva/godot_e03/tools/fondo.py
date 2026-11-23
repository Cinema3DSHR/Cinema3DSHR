"""Texturas de fondo: nebulosa (azules/violetas/verdeazulados) y Tierra con nubes. Uso: python tools/fondo.py assets/fondo"""
import random, sys, math
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(3)
def ruido(w, h, escalas, pesos):
    a = np.zeros((h, w), np.float32)
    for e, p in zip(escalas, pesos):
        r = rng.random((max(2, h // e), max(2, w // e))).astype(np.float32)
        im = Image.fromarray((r * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        a += np.asarray(im, np.float32) / 255 * p
    return a / sum(pesos)
W, H = 2048, 1024
n1, n2, n3 = ruido(W, H, [256, 128, 64, 32], [1, .6, .4, .2]), ruido(W, H, [200, 100, 50], [1, .5, .3]), ruido(W, H, [300, 150], [1, .5])
masa = np.clip((n1 - 0.45) * 2.4, 0, 1)
rgb = np.zeros((H, W, 3), np.float32)
rgb[..., 0] = masa * (0.30 + 0.35 * n2); rgb[..., 1] = masa * (0.25 + 0.30 * n3); rgb[..., 2] = masa * (0.55 + 0.35 * n1)
rgb += np.clip((n2 - 0.6) * 1.6, 0, 1)[..., None] * np.array([0.05, 0.35, 0.40], np.float32)
est = (rng.random((H, W)) > 0.9985).astype(np.float32)
rgb += est[..., None] * rng.random((H, W, 1)).astype(np.float32)
im = Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0)); im.save(OUT / "nebulosa.png")
# Tierra
W, H = 2048, 1024
t = ruido(W, H, [256, 128, 64, 32, 16], [1, .7, .5, .3, .15])
tierra = t > 0.54
col = np.zeros((H, W, 3), np.float32)
oc = np.array([0.02, 0.10, 0.34], np.float32) + (t[..., None] * 0.12)
ti = np.array([0.12, 0.32, 0.12], np.float32) + (ruido(W, H, [64, 16], [1, .5])[..., None] * 0.25)
col = np.where(tierra[..., None], ti, oc)
nb = np.clip((ruido(W, H, [200, 90, 40], [1, .6, .3]) - 0.5) * 3.2, 0, 1)
col = col * (1 - nb[..., None]) + np.array([0.95, 0.97, 1.0], np.float32) * nb[..., None]
Image.fromarray((np.clip(col, 0, 1) * 255).astype(np.uint8)).save(OUT / "tierra.png")
print("OK")
