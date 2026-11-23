"""Genera las imágenes de las pantallas de la nave (1280×720, estilo propio: cian/ámbar sobre azul noche). Uso: python tools/pantallas.py assets/pantallas"""
import math, random, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
F = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"; FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"; FM = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
def f(sz, b=False, m=False): return ImageFont.truetype(FM if m else (FB if b else F), sz)
BG = (4, 10, 22); CY = (60, 220, 255); CY2 = (20, 120, 170); AM = (255, 176, 60); RD = (255, 80, 80); GR = (90, 255, 160); WH = (220, 235, 245)
W, H = 1280, 720

def base(titulo, sub=""):
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    for x in range(0, W, 40): d.line([(x, 0), (x, H)], fill=(8, 20, 38))
    for y in range(0, H, 40): d.line([(0, y), (W, y)], fill=(8, 20, 38))
    d.rectangle([0, 0, W, 64], fill=(6, 22, 42)); d.line([(0, 64), (W, 64)], fill=CY2, width=2)
    d.text((28, 14), titulo, font=f(34, True), fill=CY); d.text((W - 420, 22), sub, font=f(22, m=True), fill=AM)
    d.rectangle([0, H - 36, W, H], fill=(6, 22, 42)); d.line([(0, H - 36), (W, H - 36)], fill=CY2, width=1)
    d.text((28, H - 30), "A LA DERIVA · SISTEMA CENTRAL", font=f(16, m=True), fill=CY2)
    return im, d

def barras(d, x, y, w, h, vals, col):
    n = len(vals); bw = w / n
    for i, v in enumerate(vals):
        d.rectangle([x + i * bw + 2, y + h - v * h, x + (i + 1) * bw - 2, y + h], fill=col)
    d.rectangle([x, y, x + w, y + h], outline=CY2)

def linea(d, x, y, w, h, vals, col):
    pts = [(x + i * w / (len(vals) - 1), y + h - v * h) for i, v in enumerate(vals)]
    d.line(pts, fill=col, width=3); d.rectangle([x, y, x + w, y + h], outline=CY2)

def anillo(d, cx, cy, r, v, col, txt):
    d.arc([cx - r, cy - r, cx + r, cy + r], 135, 405, fill=(20, 50, 80), width=14)
    d.arc([cx - r, cy - r, cx + r, cy + r], 135, 135 + 270 * v, fill=col, width=14)
    d.text((cx, cy - 6), f"{int(v*100)}%", font=f(34, True), fill=WH, anchor="mm"); d.text((cx, cy + r + 24), txt, font=f(20), fill=CY2, anchor="mm")

rnd = random.Random(7)
# 1 · mapa estelar
im, d = base("MAPA ESTELAR · DERIVA", "ESTADO: SIN RUMBO")
for _ in range(260):
    x, y = rnd.randint(30, W - 30), rnd.randint(80, H - 50); r = rnd.choice([1, 1, 2, 3]); d.ellipse([x - r, y - r, x + r, y + r], fill=rnd.choice([WH, CY, (150, 170, 255)]))
d.ellipse([880, 190, 1060, 370], outline=CY2, width=3); d.ellipse([930, 240, 1010, 320], fill=(40, 120, 200))
d.text((970, 392), "TIERRA", font=f(22, True), fill=CY, anchor="mm"); d.text((970, 416), "412 000 km", font=f(18, m=True), fill=AM, anchor="mm")
pts = [(140, 560), (280, 500), (430, 470), (560, 400), (700, 360), (860, 290)]
d.line(pts, fill=AM, width=3)
for p in pts: d.ellipse([p[0] - 6, p[1] - 6, p[0] + 6, p[1] + 6], outline=AM, width=3)
d.polygon([(130, 560), (150, 548), (150, 572)], fill=GR); d.text((100, 592), "NAVE", font=f(20, True), fill=GR)
d.text((60, 100), "TRAYECTORIA DE DERIVA", font=f(22, True), fill=WH); d.text((60, 130), "VEL.  0,42 km/s   ·   DESVÍO  +3,1°", font=f(20, m=True), fill=CY)
im.save(OUT / "mapa_estelar.png")
# 2 · estado de la nave
im, d = base("ESTADO DE LA NAVE", "TODOS LOS SISTEMAS")
anillo(d, 220, 260, 90, 0.72, CY, "ENERGÍA"); anillo(d, 520, 260, 90, 0.64, AM, "COMBUSTIBLE"); anillo(d, 820, 260, 90, 0.91, GR, "OXÍGENO"); anillo(d, 1090, 260, 90, 0.38, RD, "REFRIGERACIÓN")
linea(d, 60, 440, 560, 200, [0.5 + 0.3 * math.sin(i / 3) + rnd.uniform(-.05, .05) for i in range(40)], CY); d.text((60, 410), "CONSUMO ENERGÉTICO · 24 h", font=f(20), fill=WH)
barras(d, 680, 440, 540, 200, [rnd.uniform(.3, .95) for _ in range(18)], CY2); d.text((680, 410), "CARGA POR MÓDULO", font=f(20), fill=WH)
im.save(OUT / "estado_nave.png")
# 3 · módulo botánico
im, d = base("MÓDULO BOTÁNICO · INCUBADORAS", "CICLO DE CULTIVO 214")
for i in range(9):
    x = 60 + (i % 3) * 400; y = 100 + (i // 3) * 170
    ok = i not in (2, 5)
    d.rounded_rectangle([x, y, x + 370, y + 150], 10, outline=(GR if ok else AM), width=3)
    d.text((x + 16, y + 10), f"INCUBADORA {i+1:02d}", font=f(22, True), fill=WH)
    d.text((x + 16, y + 48), f"T {22 + i%3:.1f} °C   HUM {61 + i}%", font=f(20, m=True), fill=CY)
    d.text((x + 16, y + 82), "ESTABLE" if ok else "INESTABLE", font=f(22, True), fill=GR if ok else AM)
    linea(d, x + 180, y + 88, 170, 44, [0.5 + 0.2 * math.sin(j / 2 + i) for j in range(20)], GR if ok else AM)
im.save(OUT / "botanico.png")
# 4 · comunicaciones
im, d = base("COMUNICACIONES · ESPECTRO", "SEÑAL: NINGUNA")
for k in range(3):
    pts = [(60 + i * 12, 220 + k * 150 + 40 * math.sin(i / (3 + k) + k) * (0.2 if i > 60 else 1)) for i in range(100)]
    d.line(pts, fill=[CY, AM, GR][k], width=2)
d.text((60, 90), "FRECUENCIA 8 421 MHz · BARRIDO", font=f(22), fill=WH)
d.text((60, 640), "ÚLTIMO CONTACTO: HACE 41 DÍAS", font=f(24, True), fill=RD)
im.save(OUT / "comunicaciones.png")
# 5 · navegación (Aiden)
im, d = base("NAVEGACIÓN · PUESTO DE MANDO", "MODO MANUAL")
d.ellipse([340, 110, 940, 650], outline=CY2, width=2)
for r in (60, 140, 220, 270): d.ellipse([640 - r, 380 - r, 640 + r, 380 + r], outline=(14, 60, 90))
d.line([(640, 110), (640, 650)], fill=(14, 60, 90)); d.line([(340, 380), (940, 380)], fill=(14, 60, 90))
d.polygon([(640, 340), (622, 392), (658, 392)], fill=GR)
for _ in range(7): d.ellipse([(x := rnd.randint(400, 880)) - 5, (y := rnd.randint(170, 590)) - 5, x + 5, y + 5], outline=AM, width=2)
d.text((60, 100), "RUMBO 214°", font=f(28, True), fill=CY); d.text((60, 150), "ALT  412 km", font=f(22, m=True), fill=WH); d.text((60, 186), "VEL  0,42 km/s", font=f(22, m=True), fill=WH)
d.text((1000, 100), "ALERTAS", font=f(26, True), fill=AM); d.text((1000, 146), "· Deriva constante", font=f(20), fill=WH); d.text((1000, 176), "· Sin guía de Tierra", font=f(20), fill=WH)
im.save(OUT / "navegacion.png")
# 6 · núcleo de EVA (ojo)
im = Image.new("RGB", (W, H), (2, 6, 14)); d = ImageDraw.Draw(im)
for r in range(300, 20, -12):
    c = int(255 * (1 - r / 300)); d.ellipse([640 - r, 360 - r, 640 + r, 360 + r], outline=(0, int(c * .6), c))
d.ellipse([590, 310, 690, 410], fill=(120, 230, 255)); d.ellipse([620, 340, 660, 380], fill=(255, 255, 255))
im = im.filter(ImageFilter.GaussianBlur(1.2)); im.save(OUT / "eva_nucleo.png")
# 7 · registros
im, d = base("REGISTROS · ACCESO RESTRINGIDO", "NIVEL 2")
lin = ["06:38:11  Ciclo de cultivo 214 · parámetros nominales", "06:41:52  Presión de módulo botánico · estable", "06:42:07  Secuencia de CIERRE iniciada · origen: CENTRAL", "06:42:09  Compuertas B-3, B-4 · cierre confirmado",
       "06:49:58  Humedad incubadora 03 · fuera de rango", "06:50:00  ALARMA · anomalía en módulo botánico", "06:50:03  Compuertas B-1, B-2 · cierre automático", "06:50:41  Incubadora 06 · pérdida de estabilidad"]
for i, t in enumerate(lin):
    col = AM if "CIERRE" in t else (RD if "ALARMA" in t else WH); d.text((50, 110 + i * 56), t, font=f(24, m=True), fill=col)
im.save(OUT / "registros.png")
# 8 · tablet / chat
im = Image.new("RGB", (W, H), (10, 18, 34)); d = ImageDraw.Draw(im)
d.rounded_rectangle([420, 70, 860, 160], 22, fill=(24, 60, 100)); d.text((450, 98), "Perdón por todo esto.", font=f(30), fill=WH)
d.rounded_rectangle([140, 190, 640, 280], 22, fill=(32, 36, 56)); d.text((170, 218), "Gracias por la flor.", font=f(30), fill=WH)
d.rounded_rectangle([60, H - 130, W - 60, H - 50], 40, outline=CY2, width=3); d.text((110, H - 106), "Escribí un mensaje…", font=f(28), fill=CY2)
im.save(OUT / "chat_tablet.png")
# 9 · ventana de enfermería / vitales
im, d = base("ENFERMERÍA · SIGNOS VITALES", "PUESTO LIBRE")
linea(d, 60, 110, 1160, 150, [0.5 + 0.4 * math.sin(i * 0.9) * (1 if i % 14 < 3 else .15) for i in range(140)], GR)
linea(d, 60, 290, 1160, 150, [0.5 + 0.3 * math.sin(i * 0.3) for i in range(140)], CY)
d.text((60, 470), "FC  64   ·   SpO2  98%   ·   TEMP 36,6 °C", font=f(34, m=True), fill=WH)
d.text((60, 540), "KIT MÉDICO: COMPLETO", font=f(26, True), fill=GR)
im.save(OUT / "signos_vitales.png")
print("OK", len(list(OUT.glob("*.png"))))
# 10 · botonera (panel de botones luminosos para consolas)
im = Image.new("RGB", (512, 256), (6, 10, 18)); d = ImageDraw.Draw(im)
for r in range(6):
    for c in range(14):
        x, y = 14 + c * 35, 14 + r * 38
        col = rnd.choice([CY, CY, CY2, AM, GR, (40, 60, 90), (40, 60, 90)])
        d.rounded_rectangle([x, y, x + 28, y + 28], 5, fill=col if col not in ((40, 60, 90),) else (14, 24, 40), outline=(20, 50, 80))
im.save(OUT / "botonera.png")
# 11 · paneles hexagonales para muros
im = Image.new("RGB", (512, 512), (176, 184, 194)); d = ImageDraw.Draw(im)
for y in range(0, 512, 64):
    for x in range(0, 512, 64):
        d.rectangle([x + 3, y + 3, x + 61, y + 61], outline=(128, 138, 152), width=2)
        if (x // 64 + y // 64) % 5 == 0: d.line([(x + 10, y + 32), (x + 54, y + 32)], fill=(40, 150, 200), width=2)
im.save(OUT / "panel_muro.png")
# 12 · estrellas sobre mapa en tablet de Kate (microscopio / muestras)
im, d = base("ANÁLISIS DE MUESTRAS · BOTÁNICA", "ESPÉCIMEN 12")
for i in range(4):
    cx = 220 + i * 280; d.ellipse([cx - 110, 200, cx + 110, 420], outline=CY2, width=3); 
    for _ in range(40): x, y = cx + rnd.randint(-90, 90), 310 + rnd.randint(-90, 90); d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=GR)
    d.text((cx, 450), f"MUESTRA {i+1:02d}", font=f(22, True), fill=WH, anchor="mm")
im.save(OUT / "muestras.png")
# 13 · muro con zócalo oscuro (la textura cubre 3,2 m de alto: zócalo abajo, línea de luz a 0,95 m, paneles de 0,4 m)
im = Image.new("RGB", (512, 512), (186, 194, 204)); d = ImageDraw.Draw(im)
for y in range(0, 512, 64):
    for x in range(0, 512, 64):
        d.rectangle([x + 3, y + 3, x + 61, y + 61], outline=(136, 146, 160), width=2)
d.rectangle([0, 362, 512, 512], fill=(96, 108, 124))
for y in range(362, 512, 64):
    for x in range(0, 512, 64): d.rectangle([x + 3, y + 3, x + 61, y + min(61, 510 - y)], outline=(70, 82, 98), width=2)
d.rectangle([0, 356, 512, 364], fill=(30, 36, 46)); d.rectangle([0, 359, 512, 361], fill=(70, 220, 255))
d.rectangle([0, 150, 512, 154], fill=(150, 160, 175))
im.save(OUT / "muro_alto.png")
# 14 · suelo de placas
im = Image.new("RGB", (512, 512), (64, 70, 80)); d = ImageDraw.Draw(im)
for y in range(0, 512, 128):
    for x in range(0, 512, 128):
        c = 64 + ((x // 128 + y // 128) % 2) * 8
        d.rectangle([x + 2, y + 2, x + 126, y + 126], fill=(c, c + 6, c + 16)); d.rectangle([x, y, x + 127, y + 127], outline=(40, 46, 56), width=3)
        d.line([(x + 14, y + 14), (x + 40, y + 14)], fill=(40, 150, 190), width=2)
im.save(OUT / "suelo.png")
# 15 · rótulos de puertas
def rot(nombre, texto, col):
    im = Image.new("RGB", (512, 128), (6, 12, 22)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 511, 127], outline=col, width=4); d.rectangle([0, 0, 22, 127], fill=col)
    d.text((270, 64), texto, font=f(40, True), fill=WH, anchor="mm"); im.save(OUT / f"rot_{nombre}.png")
rot("aiden", "CUARTO DE AIDEN", AM); rot("kate", "CUARTO DE KATE", GR); rot("comedor", "COMEDOR", CY); rot("comunicaciones", "COMUNICACIONES", CY)
rot("botanico", "MÓDULO BOTÁNICO", GR); rot("enfermeria", "ENFERMERÍA", (255, 255, 255)); rot("operaciones", "CENTRO DE OPERACIONES", CY)
# 16 · muro de nave (acero oscuro con paneles biselados, remaches y vetas de luz) — tile de 3,2 m
im = Image.new("RGB", (512, 512), (52, 60, 72)); d = ImageDraw.Draw(im)
for y in range(0, 512, 128):
    for x in range(0, 512, 128):
        c = 54 + ((x // 128 + y // 128) % 2) * 6
        d.rectangle([x + 2, y + 2, x + 126, y + 126], fill=(c, c + 8, c + 20))
        d.line([(x + 2, y + 2), (x + 126, y + 2)], fill=(96, 108, 124), width=3); d.line([(x + 2, y + 2), (x + 2, y + 126)], fill=(88, 100, 116), width=3)
        d.line([(x + 2, y + 126), (x + 126, y + 126)], fill=(24, 28, 36), width=3); d.line([(x + 126, y + 2), (x + 126, y + 126)], fill=(24, 28, 36), width=3)
        for (rx, ry) in ((12, 12), (114, 12), (12, 114), (114, 114)): d.ellipse([x + rx - 3, y + ry - 3, x + rx + 3, y + ry + 3], fill=(120, 132, 148), outline=(30, 34, 42))
        if (x // 128 + y // 128) % 3 == 0: d.rectangle([x + 20, y + 60, x + 108, y + 66], fill=(30, 150, 200))
d.rectangle([0, 470, 512, 512], fill=(30, 34, 42)); d.rectangle([0, 466, 512, 470], fill=(60, 200, 240))
im.save(OUT / "muro_nave.png")
# 17 · suelo de chapa antideslizante (rombos), juntas y tornillos
im = Image.new("RGB", (512, 512), (46, 50, 58)); d = ImageDraw.Draw(im)
for y in range(0, 512, 16):
    for x in range(0, 512, 16):
        o = 8 if (y // 16) % 2 else 0
        cx, cy = x + o, y + 8
        d.polygon([(cx, cy - 6), (cx + 5, cy), (cx, cy + 6), (cx - 5, cy)], fill=(70, 76, 86), outline=(30, 34, 40))
for k in (0, 255):
    d.rectangle([k, 0, k + 2, 512], fill=(20, 22, 28)); d.rectangle([0, k, 512, k + 2], fill=(20, 22, 28))
for (x, y) in ((8, 8), (500, 8), (8, 500), (500, 500), (263, 8), (263, 500), (8, 263), (500, 263)): d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(120, 130, 144), outline=(20, 22, 28))
im.save(OUT / "suelo_nave.png")
# 18 · franja de peligro
im = Image.new("RGB", (256, 64), (20, 20, 20)); d = ImageDraw.Draw(im)
for i in range(-4, 12): d.polygon([(i * 40, 64), (i * 40 + 20, 64), (i * 40 + 52, 0), (i * 40 + 32, 0)], fill=(240, 190, 20))
im.save(OUT / "franja_peligro.png")
# 19 · expendedora (frente de vidrio con productos y teclado)
im = Image.new("RGB", (512, 768), (14, 18, 26)); d = ImageDraw.Draw(im)
d.rectangle([0, 0, 511, 60], fill=(10, 60, 90)); d.text((256, 30), "ALIMENTOS", font=f(32, True), fill=WH, anchor="mm")
cols = [(230, 70, 60), (240, 190, 50), (80, 190, 110), (70, 150, 230), (230, 130, 50), (200, 200, 210), (150, 90, 200)]
for r in range(6):
    d.rectangle([20, 80 + r * 92 + 78, 380, 80 + r * 92 + 84], fill=(80, 90, 104))
    for c in range(6):
        col = rnd.choice(cols); x = 30 + c * 58
        d.rounded_rectangle([x, 80 + r * 92 + 10, x + 44, 80 + r * 92 + 76], 6, fill=col, outline=(20, 20, 24))
        d.rectangle([x + 6, 80 + r * 92 + 30, x + 38, 80 + r * 92 + 50], fill=(240, 240, 240))
d.rectangle([400, 80, 500, 640], fill=(24, 30, 44), outline=(60, 80, 110))
for r in range(4):
    for c in range(3): d.rectangle([408 + c * 30, 110 + r * 40, 430 + c * 30, 130 + r * 40], fill=(60, 200, 240))
d.rectangle([408, 300, 492, 340], fill=(10, 20, 30), outline=(60, 200, 240)); d.text((450, 320), "0,00", font=f(20, m=True), fill=GR, anchor="mm")
d.rectangle([408, 560, 492, 620], fill=(0, 0, 0), outline=(120, 120, 130))
d.rectangle([0, 660, 511, 767], fill=(8, 12, 18)); d.rectangle([40, 690, 380, 740], fill=(2, 4, 8), outline=(60, 80, 110))
im.save(OUT / "expendedora.png")
