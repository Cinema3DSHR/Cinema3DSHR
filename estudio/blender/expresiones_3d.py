"""Actuación facial 3D (cabeza de MakeHuman, estudio/blender/cabeza_mh.py), cuadro a cuadro sobre las formas clave:
  · EXPRESIONES con fundidos (mismos nombres que las de los Stickman, así sirven las recetas de escena).
  · MICROEXPRESIONES: cejas, párpados, mejillas y comisuras con un movimiento chico y lento (la cara nunca congelada).
  · PARPADEO cada 2,5–5,5 s (más seguido al hablar), a veces doble.
  · MIRADA: los ojos giran hacia un objeto, un punto o el otro personaje, con sacádicos; los párpados acompañan.
  · LABIOS: visemas del español (A, E, I, O, U, M/B/P, F/V, consonantes) sobre la voz real (envolvente del audio) o
    con la alineación por letra de ElevenLabs; la mandíbula abre con el volumen.
"cara": {"expresiones": [{"t": 0, "expr": "neutral"}, {"t": 4, "expr": "triste_sutil", "intensidad": 0.6}],
         "miradas": [{"t": 0, "objetivo": "pj:ella"}, {"t": 6, "objetivo": [x, y, z]}],
         "habla": [{"inicio_s": 2.0, "audio": "audio/biblioteca/voz_….mp3", "texto": "…"}]}
"""
from __future__ import annotations
import json
import math
import random
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

from estudio import config

EXPRESIONES = {
    "neutral": {},
    "seria": {"LeftBrowDown": 0.15, "RightBrowDown": 0.15, "lowerLipUp": 0.1},
    "sonrisa_suave": {"MouthLeftPullUp": 0.32, "MouthRightPullUp": 0.32, "LeftCheekUp": 0.2, "RightCheekUp": 0.2,
                      "lowerLipUp": 0.1},
    "sonrisa": {"MouthLeftPullUp": 0.55, "MouthRightPullUp": 0.55, "LeftCheekUp": 0.45, "RightCheekUp": 0.45,
                "LeftLowerLidUp": 0.25, "RightLowerLidUp": 0.25, "lowerLipUp": 0.22},
    "risa": {"MouthLeftPullUp": 0.75, "MouthRightPullUp": 0.75, "LeftCheekUp": 0.7, "RightCheekUp": 0.7,
             "LeftLowerLidUp": 0.45, "RightLowerLidUp": 0.45, "JawDrop": 0.2, "UpperLipUp": 0.2},
    "carinosa": {"MouthLeftPullUp": 0.3, "MouthRightPullUp": 0.3, "LeftInnerBrowUp": 0.3, "RightInnerBrowUp": 0.3,
                 "LeftCheekUp": 0.2, "RightCheekUp": 0.2, "LeftUpperLidClosed": 0.12, "RightUpperLidClosed": 0.12},
    "triste_sutil": {"LeftInnerBrowUp": 0.45, "RightInnerBrowUp": 0.45, "MouthLeftPullDown": 0.25,
                     "MouthRightPullDown": 0.25, "LeftUpperLidClosed": 0.2, "RightUpperLidClosed": 0.2,
                     "lowerLipUp": 0.12},
    "triste": {"LeftInnerBrowUp": 0.8, "RightInnerBrowUp": 0.8, "MouthLeftPullDown": 0.5, "MouthRightPullDown": 0.5,
               "LeftUpperLidClosed": 0.3, "RightUpperLidClosed": 0.3, "lowerLipUp": 0.25},
    "preocupada": {"LeftInnerBrowUp": 0.55, "RightInnerBrowUp": 0.55, "LeftBrowDown": 0.15, "RightBrowDown": 0.15,
                   "MouthLeftPullSide": 0.12, "MouthRightPullSide": 0.12, "lowerLipBackward": 0.15},
    "admiracion": {"LeftOuterBrowUp": 0.35, "RightOuterBrowUp": 0.35, "LeftInnerBrowUp": 0.3, "RightInnerBrowUp": 0.3,
                   "LeftUpperLidOpen": 0.3, "RightUpperLidOpen": 0.3, "JawDrop": 0.06},
    "sorpresa": {"LeftOuterBrowUp": 0.85, "RightOuterBrowUp": 0.85, "LeftInnerBrowUp": 0.75, "RightInnerBrowUp": 0.75,
                 "LeftUpperLidOpen": 0.7, "RightUpperLidOpen": 0.7, "JawDrop": 0.28},
    "miedo": {"LeftInnerBrowUp": 0.9, "RightInnerBrowUp": 0.9, "LeftOuterBrowUp": 0.4, "RightOuterBrowUp": 0.4,
              "LeftUpperLidOpen": 0.6, "RightUpperLidOpen": 0.6, "MouthLeftPullSide": 0.35,
              "MouthRightPullSide": 0.35, "JawDrop": 0.12},
    "enojo": {"LeftBrowDown": 0.7, "RightBrowDown": 0.7, "NoseWrinkler": 0.3, "MouthLeftPullDown": 0.2,
              "MouthRightPullDown": 0.2, "LeftLowerLidUp": 0.3, "RightLowerLidUp": 0.3, "LipsKiss": 0.1},
    "cansado": {"LeftUpperLidClosed": 0.45, "RightUpperLidClosed": 0.45, "LeftInnerBrowUp": 0.2,
                "RightInnerBrowUp": 0.2, "MouthLeftPullDown": 0.15, "MouthRightPullDown": 0.15},
}
EXPRESIONES["preocupado"] = EXPRESIONES["preocupada"]
EXPRESIONES["ternura"] = EXPRESIONES["carinosa"]

VISEMAS = {
    "a": {"JawDrop": 0.50, "MouthLeftPullSide": 0.10, "MouthRightPullSide": 0.10},
    "e": {"JawDrop": 0.30, "MouthLeftPullSide": 0.32, "MouthRightPullSide": 0.32, "UpperLipUp": 0.10},
    "i": {"JawDrop": 0.16, "MouthLeftPullSide": 0.48, "MouthRightPullSide": 0.48},
    "o": {"JawDrop": 0.38, "LipsKiss": 0.45},
    "u": {"JawDrop": 0.14, "LipsKiss": 0.75},
    "m": {"lowerLipUp": 0.35, "LipsKiss": 0.08},
    "f": {"lowerLipBackward": 0.45, "UpperLipUp": 0.15, "JawDrop": 0.08},
    "c": {"JawDrop": 0.14, "MouthLeftPullSide": 0.14, "MouthRightPullSide": 0.14},
    " ": {},
}
LETRA = {**{c: "a" for c in "aá"}, **{c: "e" for c in "eé"}, **{c: "i" for c in "iíy"}, **{c: "o" for c in "oó"},
         **{c: "u" for c in "uúü"}, **{c: "m" for c in "mbp"}, **{c: "f" for c in "fv"}}


def _llaves(ob, curvas: dict[str, np.ndarray]):
    sk = ob.data.shape_keys
    if sk is None:
        return
    nombres = {kb.name for kb in sk.key_blocks}
    sk.animation_data_create()
    act = sk.animation_data.action or bpy.data.actions.new(f"cara_{ob.name}")
    sk.animation_data.action = act
    for nombre, val in curvas.items():
        if nombre not in nombres or not np.any(np.abs(val) > 1e-4):
            continue
        kb = sk.key_blocks[nombre]
        kb.slider_min, kb.slider_max = -1.0, 1.5
        fc = act.fcurve_ensure_for_datablock(sk, f'key_blocks["{nombre}"].value')
        fc.keyframe_points.clear()
        n = len(val)
        fc.keyframe_points.add(n)
        co = np.empty(n * 2)
        co[0::2] = np.arange(1, n + 1)
        co[1::2] = val
        fc.keyframe_points.foreach_set("co", co)
        fc.keyframe_points.foreach_set("interpolation", [1] * n)
        fc.update()


def _suave(x, sigma):
    r = int(sigma * 3) + 1
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    return np.convolve(np.pad(x, r, mode="edge"), k / k.sum(), mode="valid")


def _ruido(n, fps, rng, hz):
    t = np.arange(n) / fps
    out = np.zeros(n)
    for k in range(3):
        out += 0.55 ** k * np.sin(2 * math.pi * hz * (1 + 0.9 * k) * rng.uniform(0.7, 1.3) * t + rng.uniform(0, 6.3))
    return out / 1.8


def _visemas(texto, env, fps, alin):
    n = len(env)
    out = {k: np.zeros(n) for k in VISEMAS}
    if alin:
        for c, a, b in zip(alin.get("characters", []), alin.get("character_start_times_seconds", []),
                           alin.get("character_end_times_seconds", [])):
            vv = LETRA.get(c.lower(), "c" if c.isalpha() else " ")
            out[vv][int(a * fps):min(n, int(b * fps) + 2)] = 1.0
    else:
        voz = np.clip((env - 0.06) / 0.25, 0, 1)
        acum = np.cumsum(voz)
        utiles = [c for c in texto.lower() if c.isalpha() or c in " ,.;:!?¿¡…"]
        if acum[-1] <= 0 or not utiles:
            return out
        pos = acum / acum[-1] * (len(utiles) - 1)
        for f in range(n):
            if voz[f] >= 0.05:
                c = utiles[int(round(pos[f]))]
                out[LETRA.get(c, "c" if c.isalpha() else " ")][f] = 1.0
    return {k: _suave(x, 1.2) for k, x in out.items()}


def _mirada(pj, miradas, fps, nf, rng, otros):
    ojos = pj.get("ojos") or []
    vertical = np.zeros(nf)
    if not ojos or not miradas:
        return vertical
    sc = bpy.context.scene
    marcas = sorted(miradas, key=lambda m: m["t"])

    def objetivo(f):
        t = (f - 1) / fps
        m = ([x for x in marcas if x["t"] <= t + 1e-6] or marcas[:1])[-1]
        o = m["objetivo"]
        if isinstance(o, (list, tuple)):
            return Vector(o)
        if isinstance(o, str) and o.startswith("pj:") and o[3:] in otros:
            arm = otros[o[3:]]["armadura"]
            pb = arm.pose.bones["mixamorig:Head"]
            return arm.matrix_world @ (pb.head + (pb.tail - pb.head) * 0.45)
        ob = bpy.data.objects.get(o) if isinstance(o, str) else None
        return ob.matrix_world.translation.copy() if ob else None
    claves = []
    sac = Vector()
    prox = 0
    f_orig = sc.frame_current
    for f in range(1, nf + 1, 3):
        if f >= prox:
            sac = Vector((rng.gauss(0, 0.01), rng.gauss(0, 0.004), rng.gauss(0, 0.007)))
            prox = f + int(rng.uniform(0.4, 1.5) * fps)
        obj = objetivo(f)
        if obj is None:
            continue
        sc.frame_set(f)
        rot = []
        for ojo in ojos:
            M = ojo.matrix_world
            local = ojo.rotation_euler.to_matrix() @ (M.to_3x3().inverted() @ (obj + sac - M.translation))
            d = local.normalized()
            rot.append((max(-0.45, min(0.45, -math.atan2(d.z, math.hypot(d.x, d.y)))),
                        max(-0.6, min(0.6, math.atan2(d.x, -d.y)))))
        claves.append((f, rot))
        vertical[f - 1:f + 2] = -np.mean([r[0] for r in rot]) / 0.45
    sc.frame_set(f_orig)
    for k, ojo in enumerate(ojos):
        for f, rot in claves:
            ojo.rotation_euler = (rot[k][0], 0.0, rot[k][1])
            ojo.keyframe_insert("rotation_euler", frame=f)
    return np.clip(vertical, -1, 1)


def actuar(pj: dict, cara: dict, fps: int, nf: int, otros: dict | None = None):
    info = pj.get("cabeza_humana")
    if not info:
        return {}
    rng = random.Random(sum(map(ord, pj["id"])) + 11)
    curvas: dict[str, np.ndarray] = {}

    def sumar(u, arr):
        curvas[u] = curvas.get(u, np.zeros(nf)) + arr
    t = np.arange(nf) / fps
    marcas = sorted(cara.get("expresiones", [{"t": 0, "expr": "neutral"}]), key=lambda m: m["t"])
    for i, m in enumerate(marcas):
        fi = m.get("fundido_s", 0.6)
        sig = marcas[i + 1] if i + 1 < len(marcas) else None
        w = np.clip((t - m["t"]) / max(1e-3, fi), 0, 1) if i else np.ones(nf)
        if sig:
            w = w * np.clip((sig["t"] + sig.get("fundido_s", 0.6) - t) / max(1e-3, sig.get("fundido_s", 0.6)), 0, 1)
        w = w * w * (3 - 2 * w)
        for u, val in EXPRESIONES.get(m["expr"], {}).items():
            sumar(u, w * val * m.get("intensidad", 1.0))
    for u, amp, hz in (("LeftInnerBrowUp", 0.07, 0.25), ("RightInnerBrowUp", 0.07, 0.27),
                       ("LeftOuterBrowUp", 0.05, 0.2), ("RightOuterBrowUp", 0.05, 0.22),
                       ("MouthLeftPullUp", 0.04, 0.3), ("MouthRightPullUp", 0.04, 0.33),
                       ("LeftCheekUp", 0.04, 0.2), ("RightCheekUp", 0.04, 0.21),
                       ("LeftLowerLidUp", 0.05, 0.4), ("RightLowerLidUp", 0.05, 0.38), ("NoseWrinkler", 0.02, 0.15)):
        sumar(u, np.clip(_ruido(nf, fps, rng, hz), -1, 1) * amp)
    habla = np.zeros(nf)
    for h in cara.get("habla", []):
        f0 = int(round(h["inicio_s"] * fps))
        env = None
        if h.get("audio"):
            p = Path(h["audio"])
            p = p if p.is_absolute() else config.RAIZ / p
            if p.exists():
                from estudio.blender.stickman import _envolvente_audio
                e = _envolvente_audio(p, fps)
                env = e[:, 0] if len(e) else None
        if env is None:
            from estudio.blender.stickman import _envolvente_texto
            env = _envolvente_texto(h.get("texto", ""), fps)[:, 0]
        alin = h.get("alineacion")
        if isinstance(alin, str):
            q = config.RAIZ / alin
            alin = json.loads(q.read_text()) if q.exists() else None
        vis = _visemas(h.get("texto", ""), env, fps, alin)
        n = len(env)
        a, b = max(0, f0), min(nf, f0 + n)
        if b <= a:
            continue
        abre = np.clip(_suave(env, 1.0) * 1.1, 0, 1.15)
        for vv, w in vis.items():
            for u, x in VISEMAS[vv].items():
                arr = np.zeros(nf)
                seg = w * x * (abre if u == "JawDrop" else np.minimum(1, 0.4 + abre))
                arr[a:b] = seg[a - f0:b - f0]
                sumar(u, arr * h.get("intensidad", 1.0))
        habla[a:b] = 1
        ac = np.zeros(nf)
        ac[a:b] = np.clip(_suave(np.diff(env, prepend=0), 4) * 3, 0, 0.25)[a - f0:b - f0]
        sumar("LeftOuterBrowUp", ac)
        sumar("RightOuterBrowUp", ac)
    vertical = _mirada(pj, cara.get("miradas", []), fps, nf, rng, otros or {})
    for lado in ("Left", "Right"):
        sumar(f"{lado}UpperLidClosed", np.clip(-vertical, 0, 1) * 0.35)
        sumar(f"{lado}UpperLidOpen", np.clip(vertical, 0, 1) * 0.3)
    parp = np.zeros(nf)
    forma = np.array([0.35, 0.8, 1.0, 1.0, 0.7, 0.35, 0.1])
    if cara.get("parpadeo", True):
        f = int(rng.uniform(0.5, 2.0) * fps)
        while f < nf - len(forma):
            parp[f:f + len(forma)] = np.maximum(parp[f:f + len(forma)], forma)
            f2 = f + int(0.3 * fps)
            if rng.random() < 0.12 and f2 < nf - len(forma):
                parp[f2:f2 + len(forma)] = np.maximum(parp[f2:f2 + len(forma)], forma)
            f += int(rng.uniform(0.6, 1.4) * (2.6 if habla[f] else 4.0) * fps)
    sumar("BlinkLeft", parp)
    sumar("BlinkRight", parp)
    curvas = {k: np.clip(v, -0.3, 1.2) for k, v in curvas.items()}
    for ob in [info["obj"]] + list(pj.get("cejas") or []):
        _llaves(ob, curvas)
    return curvas
