# Visor de escenas (HTML)

`visor_escena.html`: un solo archivo para revisar una escena en el navegador (también del celular), sin Godot ni la app.
Versión publicada para el teléfono: https://claude.ai/artifact/SEW8AN7eTVhb1t3vaRAvJq (privada del dueño).

- **ABRIR ESCENA**: el `.glb` de la escena (y, si vino, el `.json` de la línea de tiempo: elegir los dos juntos). Hoy sirve
  el par `<escena>_v<k>_previa.glb` + `.json` que ya exporta `python -m estudio previa` / `previa.yml`. Si la línea de
  tiempo viene dentro del GLB (`extras.estudio_previa` de la escena o del archivo), alcanza con el GLB solo.
- **MONTAJE** (cámara de cada toma según la línea de tiempo), **TOMA** (una cámara fija), **LIBRE** (dar vueltas con el
  dedo; LENTE en mm). Siempre se ve el cuadro del render (misma proporción).
- ▶/⏸, cuadro a cuadro, velocidad ×1 ×0,5 ×0,25 ×2, línea de tiempo con los cortes de toma, qué clip hace cada personaje.
- Sin luces del archivo ni sombras: luz pareja; **COLOR PLANO** apaga la luz por completo.
- **📍 MARCAR** + texto → **COPIAR PARA CLAUDE**: texto para pegar en el chat con cuadro, segundos, toma, cámara y, si
  se marcó en LIBRE, la cámara propuesta en **coordenadas de Blender** (posición, rotación Euler XYZ en grados,
  cuaternión, lente en mm, sensor 36 mm AUTO) más un bloque JSON `estudio.visor_notas/1`. Comprobado con e01 v1: la
  pose copiada coincide con la cámara de Blender (rotación igual, ≤ 4 mm de diferencia).
- Las notas se guardan en el navegador (por escena y huella) hasta borrarlas.

Carga three.js 0.147.0 desde cdn.jsdelivr.net (hace falta internet). También acepta `?glb=URL&json=URL` si se lo sirve
desde un sitio propio.
