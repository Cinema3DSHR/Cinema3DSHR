# Temporada 01 · inventario de recursos (21/11/2026)

Tres videos verticales 540×960 · 30 fps · MP4 con narración, música, efectos y subtítulos. Se producen de a uno, en este orden: p017 (millón), p018 (diamantes), p019 (cielo azul).

## Personas (siempre revisar la orientación: el frente mira hacia donde camina)
- Aiden y la protagonista de «A la deriva» (`mixamo:personajes_pelicula/a_la_deriva/{chico,chica}`) con pelo propio; Aiden ya tiene 18 clips retargeteados (`producciones/p015_fractura/blender/aiden_clips.py`, variante `retarget_dir.py` que conserva la dirección de los huesos).
- Protagonista masculino y femenina de «Operación Tren Fantasma» (FBX con texturas PBR, esqueleto Mixamo de 65 huesos).
- Stickman masculino/femenino, Y Bot, Operador táctico, MakeHuman (`/home/user/makehuman`).
- Animaciones: packs de Mixamo en `mixamo:packs/` (locomoción, gestos, breakdance para la fiesta, etc.).

## Vehículos
- McLaren F1 del dueño (GLB, `producciones/p016_mclaren_shockwave/modelo/`; `blender/coche.py` ya trae ruedas izquierdas giradas y matrículas). **Regla 10: medir el apoyo de cada rueda.**
- Mercedes CLS 63 (`casa/…/6fc20e71-CLS63.glb`), 28 autos de Dream Racing (`Rally-Sim-movile/godot/game/models/cars/*.glb`: gt, gt3, hyper, hatch, genesis, kl5, kodiak, camo, clasico60, f1…), Falcon clásico, pickup, blindado, etc. (`mixamo:modelos_pelicula`).

## Escenarios y objetos
- Sweet Home 3D (723 piezas): muebles, árboles, puertas, ventanas, estantes, heladeras, cajones. Convención verificada: el FRENTE mira hacia −Y al importar a Blender (`producciones/p016_mclaren_shockwave/blender/sh3d.py`, `interiores.py`: restaurante, supermercado, tienda de muebles).
- Casa: generador de diseño de p013 (`disenio.py` → `layout.json`, casa moderna 18×11 m) y avenida de p016 (`ciudad.py`).
- Árboles reales: sólo `tree_tree` tiene copa densa.

## Herramientas
Blender 5.3 (`/opt/tools/blendenv/bin/python`), Godot 4.7.2, ffmpeg con libass/drawtext, ElevenLabs (voz «Yuli - Warm, Natural» ya agregada; presupuesto en `config/presupuesto_audio.json`), música/efectos sintetizados con numpy (`p015_fractura/blender/musica.py`, `p016_mclaren_shockwave/blender/audio.py`).

## Reglas de calidad que aplican (CLAUDE.md)
9 cámaras de seguimiento continuas y sin tomas tapadas · 10 vehículos apoyados en el suelo · orientación verificada de personas, sillas y mesas · verificación completa del video antes de entregar.
