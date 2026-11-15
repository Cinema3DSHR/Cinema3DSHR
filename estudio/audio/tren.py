"""Sonido procedural del Tren Fantasma (propio del estudio, sin servicios pagos), sincronizado con la escena.

- `ambiente_llanura`: viento de llanura con ráfagas, pasto, teros (el «tero-tero» de dos notas agudas), chimangos
  lejanos y grillos suaves.
- `tren`: la locomotora diésel (dos tiempos, armónicos del cigüeñal + turbo + escape) y, por cada eje de cada vagón,
  el golpe doble de la rueda al pasar una junta del riel (cada 18 m, como las eclisas de la vía), más la rodadura de
  acero y el crujido de los enganches; todo ubicado respecto de la cámara activa (volumen y paneo por fotograma).
- `motor_rpm`: motor de vehículo con su régimen real (la física de Dream Rally graba las rpm) o, si no hay, por la
  velocidad; clase «diesel» (blindados, camión) o «moto» (tetracilíndrico de alta).
"""
from __future__ import annotations
import numpy as np
from estudio.audio.procedural import SR, _ruido_color, _ruido_banda, _interp_por_frame, _espacial, _a_estereo, _barrido

JUNTA_M = 18.0
# ejes de cada tipo de vagón respecto del centro (m): bogies ± distancia y ejes ± media distancia entre ejes (tren.TIPOS)
EJES = {"loco": (5.9, 2.6), "plano": (5.2, 1.8), "cerrado": (5.0, 1.8)}


def ambiente_llanura(n, rng):
    t = np.arange(n) / SR
    rafaga = 0.55 + 0.3 * np.sin(2 * np.pi * 0.07 * t + rng.uniform(0, 6)) + 0.15 * np.sin(2 * np.pi * 0.23 * t + 1.3)
    viento = _ruido_color(n, rng, -6, 25, 1200) * 0.32 * rafaga
    pasto = _ruido_banda(n, rng, 2500, 9000) * 0.025 * rafaga ** 2
    grillos = np.zeros(n)
    for f in (4300.0, 4650.0):
        env = (np.sin(2 * np.pi * 18 * t) > 0.6) * (np.sin(2 * np.pi * 0.4 * t + f) > -0.2)
        grillos += np.sin(2 * np.pi * f * t) * env * 0.006
    aves = np.zeros(n)
    tt = rng.uniform(1.0, 4.0)
    while tt < n / SR - 1.0:
        # tero: dos notas agudas repetidas, ásperas
        for k in range(int(rng.integers(2, 5))):
            for f0, d in ((2900.0, 0.09), (2500.0, 0.11)):
                ini = int((tt + k * 0.32 + (0.0 if f0 > 2600 else 0.12)) * SR)
                m = int(d * SR)
                if ini + m >= n:
                    break
                x = np.arange(m) / SR
                s = np.sin(2 * np.pi * np.cumsum(f0 * (1 + 0.04 * np.sin(2 * np.pi * 60 * x))) / SR)
                aves[ini:ini + m] += np.sign(s) * np.abs(s) ** 0.6 * np.hanning(m) * rng.uniform(0.02, 0.045)
        tt += rng.uniform(5.0, 11.0)
    base = viento + pasto + grillos
    return np.stack([base + aves, np.roll(base, 900) + np.roll(aves, 3000) * 0.7], axis=1)


def _golpe_junta(rng):
    n = int(0.16 * SR)
    t = np.arange(n) / SR
    y = _barrido(n, 140, 70, 0.02, 0.05) * 0.9 + _ruido_banda(n, rng, 900, 6000) * np.exp(-t / 0.012) * 0.5
    y += np.sin(2 * np.pi * 1850 * t) * np.exp(-t / 0.03) * 0.08          # «ting» metálico del riel
    return y


def _diesel(v, n, rng):
    """Locomotora diésel de dos tiempos: ralentí ~300 rpm, a plena carga ~900 rpm (armónicos del encendido)."""
    rpm = 300 + np.clip(v / 22.0, 0, 1) * 600
    f = rpm / 60 * 8                                     # 16 cilindros en dos tiempos: 16 encendidos por vuelta / 2
    fase = np.cumsum(2 * np.pi * f / SR)
    tono = sum(np.sin(k * fase + k * 0.7) / k ** 0.8 for k in range(1, 9))
    tono *= 1.0 + 0.25 * np.sin(fase / 8)                # golpeteo del cigüeñal
    turbo = np.sin(np.cumsum(2 * np.pi * (1300 + 9 * rpm) / SR)) * 0.025
    escape = _ruido_color(n, rng, -4.5, 40, 900) * 0.35
    return tono * 0.22 + turbo + escape


def tren(pistas, n, rng, tipos: list[str], s_inicial: float):
    """tipos: tipo de cada vagón (carro_00 = locomotora). s_inicial: posición sobre la vía de la cabeza al empezar."""
    fps = pistas["fps"]
    out = np.zeros((n, 2))
    golpe = _golpe_junta(rng)
    for i, tipo in enumerate(tipos):
        m = pistas["moviles"].get(f"carro_{i:02d}")
        if not m:
            continue
        pos = np.array([x[:3] for x in m])
        v = np.array([x[3] for x in m])
        d = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(pos[:, :2], axis=0), axis=1))])
        mono = np.zeros(n)
        by, ee = EJES.get(tipo, (5.0, 1.8))
        # distancia del centro del vagón a la cabeza: la da el corrimiento del primer cuadro respecto del carro 0
        d0 = s_inicial - (np.linalg.norm(pos[0, :2] - np.array(pistas["moviles"]["carro_00"][0][:2])) if i else 0.0)
        t_f = np.arange(len(d)) / fps
        for eje in (by + ee / 2, by - ee / 2, -by + ee / 2, -by - ee / 2):
            s_eje = d0 + d + eje
            k0, k1 = np.floor(s_eje[0] / JUNTA_M), np.floor(s_eje[-1] / JUNTA_M)
            for k in np.arange(k0 + 1, k1 + 1):
                tj = float(np.interp(k * JUNTA_M, s_eje, t_f))
                a = int(tj * SR)
                b = min(n, a + len(golpe))
                if b > a:
                    mono[a:b] += golpe[: b - a] * rng.uniform(0.6, 1.0)
        vel = _interp_por_frame(v, n, fps)
        rodado = _ruido_banda(n, rng, 180, 2600) * np.clip(vel / 20.0, 0, 1) * 0.18
        acople = _ruido_banda(n, rng, 300, 1500) * (rng.random(n) < 0.0004) * 0.4   # crujidos de enganches
        mono += rodado + acople
        if tipo == "loco":
            mono += _diesel(vel, n, rng)
        g, pan = _espacial(pistas, pos.tolist(), n)
        out += _a_estereo(mono, g * 1.6, pan)
    return out


def motor_rpm(pistas, movil, n, rng, clase="diesel"):
    fps = pistas["fps"]
    m = pistas["moviles"][movil]
    v = _interp_por_frame(np.abs([x[3] for x in m]), n, fps)
    rpm_f = (pistas.get("rpm") or {}).get(movil)
    if rpm_f:
        rpm = _interp_por_frame(rpm_f, n, fps)
    elif clase == "moto":
        rpm = 4500 + (v % 9.0) / 9.0 * 5000               # sube y cambia: dientes de sierra por marcha
    else:
        rpm = 900 + (v % 7.0) / 7.0 * 1600
    if clase == "moto":
        f = rpm / 60 * 2                                   # cuatro cilindros en cuatro tiempos: 2 encendidos por vuelta
        fase = np.cumsum(2 * np.pi * f / SR)
        tono = np.sin(fase) * 0.5 + np.sin(2 * fase) * 0.35 + np.sin(3 * fase) * 0.2 + np.sin(4 * fase) * 0.12
        mono = np.tanh(tono * 1.8) * 0.35 + _ruido_banda(n, rng, 1500, 7000) * 0.05
    elif clase == "deportivo":
        f = rpm / 60 * 5                                   # V10 atmosférico: 5 encendidos por vuelta, agudo y áspero
        fase = np.cumsum(2 * np.pi * f / SR)
        tono = np.sin(fase) * 0.45 + np.sin(2 * fase) * 0.4 + np.sin(3 * fase) * 0.25 + np.sin(5 * fase) * 0.12
        mono = np.tanh(tono * 2.2) * 0.3 + _ruido_banda(n, rng, 2000, 9000) * 0.04
    else:
        f = rpm / 60 * 4                                   # V8 diésel
        fase = np.cumsum(2 * np.pi * f / SR)
        tono = sum(np.sin(k * fase + k) / k for k in range(1, 7)) * (1 + 0.3 * np.sin(fase / 4))
        mono = tono * 0.25 + _ruido_color(n, rng, -4, 50, 1800) * 0.12
    mono += _ruido_color(n, rng, -2, 250, 5000) * np.clip(v / 15.0, 0, 1) * 0.12   # gomas sobre el asfalto
    g, pan = _espacial(pistas, [x[:3] for x in m], n)
    return _a_estereo(mono, g * 1.5, pan)
