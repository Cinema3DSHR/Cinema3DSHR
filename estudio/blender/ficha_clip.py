"""Ficha visual de un clip de animación: el esqueleto dibujado como un muñeco de palitos, de costado y de frente, en
8 momentos del clip, con su descripción del catálogo, la duración y cuánto avanza. NO es un render (lo dibuja Pillow
con las posiciones de los huesos): sirve para MIRAR cómo se mueve un clip antes de usarlo en una escena.

Uso: python -m estudio clips ficha mixamo:animaciones/caminar_correr/Standard_Walk.fbx [--salida carpeta]
"""
from __future__ import annotations

from pathlib import Path

import bpy

from estudio import clips as CL
from estudio import config

HUESOS = [("Hips", "Spine"), ("Spine", "Spine1"), ("Spine1", "Spine2"), ("Spine2", "Neck"), ("Neck", "Head"),
          ("Head", "HeadTop_End"),
          ("Spine2", "LeftShoulder"), ("LeftShoulder", "LeftArm"), ("LeftArm", "LeftForeArm"), ("LeftForeArm", "LeftHand"),
          ("Spine2", "RightShoulder"), ("RightShoulder", "RightArm"), ("RightArm", "RightForeArm"),
          ("RightForeArm", "RightHand"),
          ("Hips", "LeftUpLeg"), ("LeftUpLeg", "LeftLeg"), ("LeftLeg", "LeftFoot"), ("LeftFoot", "LeftToeBase"),
          ("Hips", "RightUpLeg"), ("RightUpLeg", "RightLeg"), ("RightLeg", "RightFoot"), ("RightFoot", "RightToeBase")]


def ficha(ref: str, salida: Path, n: int = 8) -> Path:
    from PIL import Image, ImageDraw, ImageFont
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.fps = 30
    bpy.ops.import_scene.fbx(filepath=str(config.resolver(ref)))
    arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
    act = arm.animation_data.action
    f0, f1 = (int(x) for x in act.frame_range)
    sc = bpy.context.scene
    pref = next((b.name.split("Hips")[0] for b in arm.pose.bones if b.name.endswith("Hips")), "mixamorig:")

    def pos(nombre):
        pb = arm.pose.bones.get(pref + nombre)
        return (arm.matrix_world @ pb.head) if pb else None
    cuadros = [round(f0 + (f1 - f0) * i / (n - 1)) for i in range(n)]
    poses = []
    for f in cuadros:
        sc.frame_set(f)
        poses.append({h: pos(h) for par in HUESOS for h in par})
    cad = [p["Hips"] for p in poses]
    W, H, M = 220, 300, 30
    img = Image.new("RGB", (W * n, H * 2 + 90), (18, 20, 24))
    d = ImageDraw.Draw(img)
    try:
        fuente = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
    except OSError:
        fuente = ImageFont.load_default()
    alto = max(p["HeadTop_End"].z for p in poses if p.get("HeadTop_End")) or 1.8
    esc = (H - 2 * M) / max(alto, 1.0)
    for i, (f, p) in enumerate(zip(cuadros, poses)):
        for fila, (eje, nombre) in enumerate((("y", "costado"), ("x", "frente"))):
            ox, oy = W * i + W // 2, H * (fila + 1) - M + 40
            c0 = cad[i]

            def a2d(v):
                h = (getattr(v, eje) - getattr(c0, eje)) * esc
                return (ox + h, oy - v.z * esc)
            d.line([(W * i + 10, oy), (W * (i + 1) - 10, oy)], fill=(60, 64, 70))
            for a, b in HUESOS:
                if p.get(a) is None or p.get(b) is None:
                    continue
                izq = "Left" in a or "Left" in b
                col = (90, 200, 255) if izq else ((255, 170, 70) if ("Right" in a or "Right" in b) else (230, 230, 230))
                d.line([a2d(p[a]), a2d(p[b])], fill=col, width=4)
            if p.get("HeadTop_End") is not None and p.get("Head") is not None:
                hx, hy = a2d(p["Head"])
                d.ellipse([hx - 9, hy - 22, hx + 9, hy - 4], outline=(230, 230, 230), width=3)
            d.text((W * i + 8, H * fila + 44), f"{nombre} · cuadro {f}", font=fuente, fill=(150, 150, 150))
    c = CL.ficha(ref) or {}
    avance = cad[-1] - cad[0]
    dur = (f1 - f0) / 30
    titulo = f"{ref.split('/')[-1]} — «{c.get('descripcion_en') or c.get('descripcion') or '?'}»"
    sub = (f"{dur:.2f} s · avanza {avance.length:.2f} m ({avance.length / max(dur, 1e-3):.2f} m/s) · "
           f"{'ESTILO MARCADO: ' + ', '.join(c.get('estilo_marcado', [])) if c.get('estilo_marcado') else 'estilo neutro'}"
           f" · azul = izquierda, naranja = derecha")
    d.text((10, 8), titulo, font=fuente, fill=(255, 220, 120))
    d.text((10, 26), sub, font=fuente, fill=(200, 200, 200))
    salida.mkdir(parents=True, exist_ok=True)
    out = salida / (ref.split("/")[-1].rsplit(".", 1)[0] + ".png")
    img.save(out)
    return out
