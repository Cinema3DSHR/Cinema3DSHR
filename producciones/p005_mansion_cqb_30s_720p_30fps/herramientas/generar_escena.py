"""Genera escenas/e01/v1/escena.json de la producción CQB: coreografía de 4 operadores y 1 enemigo, disparos, cámaras y sonido.

Los recorridos usan ciclos enteros de clip (la cadera avanza lo que avanzó el ciclo, sin deslizar los pies): para cada
tramo se elige la cantidad de ciclos que mejor llega al punto y se ajusta la velocidad del clip para que dure lo previsto.
Todo está en segundos de la película; los disparos se sincronizan con el retroceso de cada clip (fotograma 3 del ciclo).
"""
import itertools
import json
import math
from pathlib import Path

FPS, DUR = 30, 30.0
P = "mixamo:packs/"
# clave: (clip, segundos por ciclo, metros por ciclo)
CLIPS = {
    "idle": (P + "Pro_Rifle_Pack/idle_aiming.fbx", 63 / FPS, 0.0),
    "agachado": (P + "Pro_Rifle_Pack/idle_crouching_aiming.fbx", 63 / FPS, 0.0),
    "baja": (P + "Pro_Rifle_Pack/idle.fbx", 63 / FPS, 0.0),
    "caminar": (P + "Pro_Rifle_Pack/walk_forward.fbx", 1.0, 1.81),
    "caminar_ag": (P + "Pro_Rifle_Pack/walk_crouching_forward.fbx", 1.0, 1.92),
    "fuego": (P + "Basic_Shooter_Pack/firing_rifle.fbx", 8 / FPS, 0.0),          # un disparo por ciclo (retroceso en el cuadro 3)
    "fuego_lento": (P + "Shooter_Pack/firing_rifle.fbx", 35 / FPS, 0.0),         # un disparo por ciclo, retroceso marcado
    "golpe": (P + "Basic_Shooter_Pack/hit_reaction.fbx", 13 / FPS, 0.0),
    "muerte": (P + "Pro_Rifle_Pack/death_from_the_front.fbx", 103 / FPS, 0.0),
}
DISPARO_CUADRO = 3


def rumbo(a, b):
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


class Actor:
    def __init__(self, pid, modelo, arma, pos, head):
        self.pid, self.modelo, self.arma = pid, modelo, arma
        self.pos, self.head, self.t = tuple(pos), head, 0.0
        self.acc, self.disparos, self.pasos, self.primero = [], [], [], True

    def _add(self, clave, dur, repetir, head=None, giro=0.0, vel=1.0, pos_fin=None, **extra):
        clip, _, _ = CLIPS[clave]
        a = {"clip": clip, "inicio_s": round(self.t, 4), "repetir": int(repetir)}
        if self.primero:
            a["pos"] = [round(self.pos[0], 3), round(self.pos[1], 3)]
            a["mirando_deg"] = round(head if head is not None else self.head, 3)
            self.primero = False
        else:
            a["encadenar"] = True
            if head is not None:
                a["mirando_deg"] = round(head, 3)
                if giro:
                    a["giro_s"] = giro
        if abs(vel - 1.0) > 1e-3:
            a["velocidad"] = round(vel, 4)
        a.update(extra)
        self.acc.append(a)
        if head is not None:
            self.head = head
        if pos_fin is not None:
            self.pos = pos_fin
        self.t += dur

    def pose(self, clave, hasta, apunta=None, head=None, giro=0.35):
        """Mantiene una pose (idle/agachado/...) hasta el instante absoluto `hasta`, mirando a `apunta` (punto) o `head`."""
        dur = hasta - self.t
        assert dur > 0.05, (self.pid, clave, self.t, hasta)
        h = rumbo(self.pos, apunta) if apunta else (head if head is not None else None)
        _, cic, _ = CLIPS[clave]
        n = max(1, round(dur / cic))
        self._add(clave, dur, n, head=h, giro=giro, vel=n * cic / dur)

    def ir(self, clave, tramos, v=1.35):
        """Camina por una lista de puntos. Elige ciclos enteros por tramo (el que deje más cerca del punto) y simula dónde
        queda; la velocidad del clip es `v` (la duración sale de los ciclos)."""
        clip, cic, d = CLIPS[clave]
        mejor = None
        for deltas in itertools.product((-1, 0, 1), repeat=len(tramos)):
            pos, plan, err = self.pos, [], 0.0
            for wp, dl in zip(tramos, deltas):
                dist = math.hypot(wp[0] - pos[0], wp[1] - pos[1])
                n = max(1, round(dist / d) + dl)
                h = rumbo(pos, wp)
                pf = (pos[0] + math.cos(math.radians(h)) * d * n, pos[1] + math.sin(math.radians(h)) * d * n)
                err += math.hypot(pf[0] - wp[0], pf[1] - wp[1])
                plan.append((n, h, pf, n * cic / v))
                pos = pf
            if mejor is None or err < mejor[0]:
                mejor = (err, plan)
        for n, h, pf, dur in mejor[1]:
            t0 = self.t
            self._add(clave, dur, n, head=h, giro=0.35, vel=v, pos_fin=pf)
            for k in range(2 * n):          # pasos: uno cada medio ciclo
                self.pasos.append(round(t0 + (k + 0.5) * dur / (2 * n), 3))

    def rafaga(self, clave, t0, n):
        """`n` disparos seguidos desde `t0` con el clip de fuego; registra los instantes de cada disparo."""
        clip, cic, _ = CLIPS[clave]
        assert abs(self.t - t0) < 0.02, (self.pid, self.t, t0)
        self._add(clave, n * cic, n)
        for k in range(n):
            self.disparos.append(round(t0 + (DISPARO_CUADRO + k * cic * FPS) / FPS, 4))

    def spec(self):
        d = {"id": self.pid, "modelo": self.modelo, "arma": self.arma, "acciones": self.acc}
        if self.disparos:
            d["disparos"] = self.disparos
        return d


ENEMIGO_POS = (1.2, 6.9)
CUERPO = (1.15, 5.9)          # donde queda tendido (la caída lo desplaza ~1 m hacia los operadores)

# ----------------------------------------------------------------------------- operadores
o1 = Actor("o1", "soldado:ch35", "M4A1", (0.35, -1.3), 90)
o1.pose("idle", 1.6, head=90)
o1.ir("caminar", [(0.4, 0.5), (3.4, 1.7), (3.7, 3.8)])
o1.pose("idle", 12.2, apunta=ENEMIGO_POS, giro=0.5)
for t0, n in ((12.2, 4), (14.5, 5), (16.6, 5)):
    o1.rafaga("fuego", t0, n)
    if t0 == 12.2:
        o1.pose("idle", 14.5)
    elif t0 == 14.5:
        o1.pose("idle", 16.6)
o1.pose("idle", 18.9)
o1.ir("caminar_ag", [(2.9, 5.5)], v=1.0)
o1.pose("idle", 30.0, apunta=CUERPO, giro=0.6)

o2 = Actor("o2", "soldado:ch15", "M4A1", (-0.3, -2.4), 90)
o2.pose("idle", 2.05, head=90)
o2.ir("caminar", [(-0.35, 1.0), (-1.3, 3.0)])
o2.pose("idle", 12.6, apunta=ENEMIGO_POS, giro=0.5)
for t0, n, sig in ((12.6, 4, 15.0), (15.0, 4, 17.0), (17.0, 5, 18.9)):
    o2.rafaga("fuego", t0, n)
    o2.pose("idle", sig)
o2.ir("caminar_ag", [(-0.2, 4.9)], v=1.0)
o2.pose("idle", 30.0, apunta=CUERPO, giro=0.6)

o3 = Actor("o3", "soldado:operador", "M4A1", (0.35, -3.5), 90)
o3.pose("idle", 2.5, head=90)
o3.ir("caminar", [(0.3, 1.1), (1.1, 3.3)])
o3.pose("idle", 11.6, apunta=ENEMIGO_POS, giro=0.5)
for t0, n, sig in ((11.6, 5, 13.8), (13.8, 4, 16.0), (16.0, 6, 18.0), (18.0, 4, 19.2)):
    o3.rafaga("fuego", t0, n)
    o3.pose("idle", sig)
o3.ir("caminar_ag", [(1.1, 4.9)], v=1.0)
o3.pose("idle", 24.0, apunta=CUERPO, giro=0.5)
o3.pose("idle", 30.0, apunta=(-3.8, 7.6), giro=0.9)

o4 = Actor("o4", "soldado:ch35", "M4A1", (-0.35, -4.6), 90)
o4.pose("idle", 3.0, head=90)
o4.ir("caminar", [(-0.45, 2.4)])
o4.pose("idle", 13.0, apunta=ENEMIGO_POS, giro=0.5)
for t0, n, sig in ((13.0, 3, 15.4), (15.4, 4, 17.4), (17.4, 3, 19.6)):
    o4.rafaga("fuego", t0, n)
    o4.pose("idle", sig)
o4.pose("idle", 24.0, apunta=(-4.0, 4.5), giro=0.8)
o4.pose("idle", 27.0, apunta=(-4.2, 7.4), giro=0.9)
o4.pose("baja", 30.0, apunta=(-1.0, 6.0), giro=0.6)

# ----------------------------------------------------------------------------- enemigo
en = Actor("en", "soldado:ch49", "AK47", ENEMIGO_POS, rumbo(ENEMIGO_POS, (0.5, 3.5)))
en.pose("agachado", 9.2)
en.pose("idle", 11.0, giro=0.2)
for t0, n in ((11.0, 3), (13.6, 3), (15.9, 3)):
    clip, cic, _ = CLIPS["fuego_lento"]
    v = 1.7
    cs = cic / v
    en._add("fuego_lento", n * cs, n, vel=v)
    for k in range(n):
        en.disparos.append(round(t0 + (DISPARO_CUADRO / v + k * cs * FPS) / FPS, 4))
    sig = {11.0: 13.6, 13.6: 15.9, 15.9: 18.7}[t0]
    en.pose("idle", sig)
en._add("golpe", 13 / FPS, 1)
en.t = 19.15
# la muerte: la caída desplaza la cadera ~1 m hacia los operadores y el cuerpo queda tendido hasta el final
en.acc[-1]["inicio_s"] = 18.7
en.acc.append({"clip": CLIPS["muerte"][0], "inicio_s": 19.15, "encadenar": True, "repetir": 1})

ACTORES = [o1, o2, o3, o4, en]

# ----------------------------------------------------------------------------- impactos de bala (destellos en el decorado)
impactos = []
for i, t in enumerate(en.disparos):     # los disparos del enemigo pegan en el muro, la biblioteca y el sofá, cerca de los operadores
    destinos = [(0.9, 0.2, 1.8), (-1.2, 0.2, 1.2), (-4.9, 2.4, 1.5), (-4.5, 4.9, 0.9), (0.0, 0.2, 2.0), (-4.9, 3.6, 1.1), (1.4, 0.2, 1.3),
                (-4.8, 1.9, 1.6), (-4.0, 5.2, 0.7), (-0.6, 0.2, 1.7), (-4.9, 2.8, 1.9)]
    impactos.append({"accion": "chispa", "inicio_s": round(t + 0.1, 3), "pos": list(destinos[i % len(destinos)])})
X_OP = {"o1": 3.7, "o2": -1.2, "o3": 1.1, "o4": -0.45}
ops_x = sorted((t, X_OP[a.pid]) for a in (o1, o2, o3, o4) for t in a.disparos)
ops = [t for t, _ in ops_x]
for t in ops:       # los de los operadores pegan en el escritorio y la pared del fondo; los últimos, en el enemigo
    if t > 17.4 and t < 18.7:
        pos = [ENEMIGO_POS[0] + 0.05 * math.sin(t * 40), ENEMIGO_POS[1] - 0.1, 1.25 + 0.15 * math.cos(t * 30)]
    else:
        k = int(t * 100) % 5
        pos = [(1.0, 5.95, 0.8), (2.5, 5.95, 0.6), (-0.8, 8.5, 1.4), (1.6, 8.5, 1.0), (2.4, 5.95, 0.9)][k]
    impactos.append({"accion": "chispa", "inicio_s": round(t + 0.1, 3), "pos": pos})

# ----------------------------------------------------------------------------- cámaras (tercera persona, planos compuestos)
def toma(i, tipo, plano, t0, t1, **k):
    return {"id": f"t{i:02d}_{tipo}", "tipo": tipo, "plano": plano, "inicio_s": t0, "duracion_s": round(t1 - t0, 3), "luz_relleno": 0, **k}


tomas = [
    toma(1, "dolly", "por detrás de la fila, avanzando por el pasillo hacia la puerta", 0.0, 2.6,
         desde=[0.0, -7.6, 1.55], hasta=[0.1, -5.6, 1.5], objetivo={"movil": "o1", "punto": "cabeza"}, lente_mm=28, apertura=4.0),
    toma(2, "estatica", "entrada: la fila irrumpe por la puerta, plano bajo desde la habitación", 2.6, 4.8,
         desde=[-3.7, 1.3, 1.05], objetivo={"ancla": "puerta", "desp": [0.2, 0.6, 1.0]}, lente_mm=26, apertura=4.0),
    toma(3, "seguimiento", "seguimiento por encima del hombro del primer operador", 4.8, 7.2, movil="o1", punto_base="cadera",
         desp_local=[-0.8, -2.5, 0.65], objetivo={"movil": "o1", "punto": "cabeza"}, lente_mm=32, retardo=0.15, temblor=0.01),
    toma(4, "estatica", "sobre el hombro del tercer operador: el enemigo asoma tras el escritorio", 7.2, 9.6,
         desde=[0.55, 2.2, 1.55], objetivo={"movil": "en", "punto": "cabeza"}, lente_mm=75, apertura=2.2),
    toma(5, "estatica", "plano general desde la puerta: el enemigo se levanta y dispara", 9.6, 12.0,
         desde=[-0.9, 0.7, 1.45], objetivo={"ancla": "centro_sala", "desp": [0.6, 0.5, 0.9]}, lente_mm=24, apertura=5.6),
    toma(6, "estatica", "contrapicado desde atrás del enemigo: los fogonazos de los operadores", 12.0, 14.5,
         desde=[0.2, 8.1, 0.95], objetivo={"ancla": "centro_sala", "desp": [0.5, -0.8, 1.15]}, lente_mm=30, apertura=4.0),
    toma(7, "estatica", "primer plano de un operador disparando", 14.5, 16.8,
         desde=[1.9, 0.9, 1.45], objetivo={"movil": "o3", "punto": "cabeza"}, lente_mm=50, apertura=2.4),
    toma(8, "estatica", "lateral: el enemigo recibe los impactos y cae", 16.8, 20.0,
         desde=[-1.6, 6.9, 1.25], objetivo={"movil": "en", "punto": "cadera"}, lente_mm=38, apertura=4.0, temblor=0.006),
    toma(9, "grua", "cenital: el enemigo tendido y los operadores avanzando", 20.0, 22.6,
         desde=[-1.0, 3.2, 2.9], hasta=[-0.1, 3.9, 2.6], objetivo={"movil": "en", "punto": "cadera"}, lente_mm=28),
    toma(10, "orbita", "órbita lenta sobre el equipo asegurando la sala", 22.6, 26.2,
         centro=[1.2, 5.0, 1.0], radio=4.2, altura=1.5, angulo_inicial=-140, angulo_final=-60, lente_mm=28),
    toma(11, "grua", "cierre: el equipo y el enemigo neutralizado desde la puerta", 26.2, 30.0,
         desde=[0.1, 0.5, 1.35], hasta=[0.1, -1.0, 2.1], objetivo={"ancla": "centro_sala", "desp": [1.0, 1.3, 0.8]}, lente_mm=24),
]

# ----------------------------------------------------------------------------- sonido (los eventos llevan sus instantes exactos)
son_eventos = [
    {"tipo": "puerta_patada", "inicio_s": 1.75, "ancla": "puerta"},
    {"tipo": "pasos", "t": sorted(t for a in (o1, o2, o3, o4) for t in a.pasos), "movil_ids": [a.pid for a in (o1, o2, o3, o4)]},
    {"tipo": "equipo", "t": [1.3, 1.9, 2.4, 2.9, 5.5, 12.0, 19.0, 21.55, 21.62, 24.0, 27.0]},
    {"tipo": "disparos", "t": [t for t, _ in ops_x], "xs": [x for _, x in ops_x], "arma": "M4A1", "lado": "equipo"},
    {"tipo": "disparos", "t": en.disparos, "xs": [ENEMIGO_POS[0]] * len(en.disparos), "arma": "AK47", "lado": "enemigo"},
    {"tipo": "impactos", "t": [i["inicio_s"] for i in impactos]},
    {"tipo": "caida", "t": [21.1, 20.4, 21.6]},
]
escena = {
    "tipo": "escena", "id": "p005_mansion_cqb_30s_720p_30fps-e01", "produccion": "p005_mansion_cqb_30s_720p_30fps", "numero": 1,
    "version": 1, "titulo": "Entrada táctica",
    "guion": "INT. MANSIÓN — DÍA. Cuatro operadores abren la puerta y entran coordinados a un estudio de lujo; detectan a un enemigo armado tras el escritorio, hay un breve intercambio de disparos, lo neutralizan y aseguran la habitación.",
    "duracion_s": DUR,
    "escenario": {"id": "mansion_cqb", "generador": "mansion_cqb", "parametros": {"semilla": 11}},
    "eventos": [{"accion": "abrir_puerta", "inicio_s": 1.75}] + impactos,
    "vehiculos": [],
    "personajes": [a.spec() for a in ACTORES],
    "tomas": tomas,
    "sonido": {"generador": "procedural", "ambiente": "cqb_interior", "eventos": son_eventos},
    "render": {"calidad": "revision", "fps": FPS, "exposicion": -0.7},
    "estado": "borrador", "bloqueada": False,
}
salida = Path(__file__).resolve().parents[1] / "escenas/e01/v1/escena.json"
salida.write_text(json.dumps(escena, ensure_ascii=False, indent=1))
for a in ACTORES:
    print(a.pid, "termina en t =", round(a.t, 2), "pos", tuple(round(v, 2) for v in a.pos), "disparos", len(a.disparos))
print("impactos:", len(impactos), "escrito", salida)
