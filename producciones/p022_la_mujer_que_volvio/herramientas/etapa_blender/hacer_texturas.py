"""Dibuja las texturas con transparencia de los pinos (ramillete de agujas) con PIL: no se versionan, se regeneran. Uso: python3 hacer_texturas.py SALIDA_DIR"""
import sys, math, random
from PIL import Image, ImageDraw, ImageFilter
out = sys.argv[1]
rng = random.Random(11)
def ramillete(nombre, w=256, h=512, agujas=420, largo=(60, 110), verde=((18, 44, 24), (46, 92, 44))):
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    cx = w // 2
    d.line([(cx, h - 4), (cx, 14)], fill=(70, 52, 34, 255), width=4)                    # rama central
    for i in range(agujas):
        y = rng.uniform(26, h - 20)                                                     # punto de salida sobre la rama
        t = 1.0 - y / h
        lado = rng.choice((-1, 1)); a = math.radians(rng.uniform(18, 62)) * lado
        L = rng.uniform(*largo) * (0.55 + 0.7 * math.sin(math.pi * min(max(y / h, 0.04), 0.96)))
        ex = cx + math.sin(a) * L; ey = y - math.cos(a) * L * 0.7 + rng.uniform(-4, 6)
        k = rng.random()
        col = tuple(int(verde[0][j] + (verde[1][j] - verde[0][j]) * k) for j in range(3))
        d.line([(cx + rng.uniform(-2, 2), y), (ex, ey)], fill=col + (255,), width=2 if rng.random() < 0.6 else 3)
    img = img.filter(ImageFilter.GaussianBlur(0.45))
    img.save(f'{out}/{nombre}.png')
ramillete('agujas_pino_a', agujas=520)
ramillete('agujas_pino_b', agujas=380, largo=(75, 125), verde=((14, 36, 22), (38, 78, 40)))
# corteza: patrón de grietas verticales (relieve) en escala de grises
w, h = 512, 1024
img = Image.new('L', (w, h), 128); d = ImageDraw.Draw(img)
for i in range(260):
    x = rng.uniform(0, w); y = rng.uniform(0, h); L = rng.uniform(80, 320); wd = rng.choice((2, 3, 4, 6))
    xs = [x]; 
    for k in range(10): xs.append(xs[-1] + rng.uniform(-6, 6))
    d.line([(xs[k], y + L * k / 10) for k in range(11)], fill=rng.choice((40, 55, 70, 190, 210)), width=wd)
img = img.filter(ImageFilter.GaussianBlur(1.6)); img.save(f'{out}/corteza_pino.png')
print('texturas listas en', out)
