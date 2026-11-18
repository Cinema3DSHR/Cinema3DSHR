# Visor de escenas (HTML)

`visor_escena.html`: un solo archivo para revisar una escena en el navegador (también del celular), sin Godot ni la app.
Versión publicada para el teléfono: https://claude.ai/artifact/SEW8AN7eTVhb1t3vaRAvJq (privada del dueño).

- **ABRIR ESCENA**: el `.glb` de la escena (y, si vino, el `.json` de la línea de tiempo: elegir los dos juntos). Hoy sirve
  el par `<escena>_v<k>_previa.glb` + `.json` que ya exporta `python -m estudio previa` / `previa.yml`. Si la línea de
  tiempo viene dentro del GLB (`extras.estudio_previa` de la escena o del archivo), alcanza con el GLB solo.
- **MONTAJE** (cámara de cada toma según la línea de tiempo), **TOMA** (una cámara fija), **LIBRE** (recorrer la escena:
  1 dedo mira, 2 dedos acercan y corren, cruceta ▲▼◀▶⤒⤓ con rapidez 2 / 6 / 0,5 m/s; teclado WASD QE; LENTE en mm;
  «Pegada a»: la cámara viaja con el vagón / auto / personaje). Siempre se ve el cuadro del render (misma proporción).
- **🎥 COLOCAR CÁMARA**: desde MONTAJE/TOMA pasa a LIBRE en la cámara actual (pegada a lo que la lleva, p. ej. el
  vagón); en LIBRE coloca la cámara y COPIA al instante la orden para Claude: momento (desde/hasta en m:ss y cuadros),
  qué toma reemplaza (o toma nueva), si va fija o con movimiento, posición y rotación RESPECTO del objeto al que va
  pegada (objeto.matrix_world⁻¹ · cámara.matrix_world, Blender) y en el mundo, hacia dónde mira, lente y cuadro.
  Cada orden queda en la lista con VER (vuelve a esa cámara), COPIAR y los campos para ajustarla.
- ▶/⏸, cuadro a cuadro, velocidad ×1 ×0,5 ×0,25 ×2, línea de tiempo con los cortes de toma, qué clip hace cada personaje.
- Sin luces del archivo ni sombras: luz pareja; **COLOR PLANO** apaga la luz por completo.
- **📍 NOTA** + texto y **COPIAR TODO PARA CLAUDE** (órdenes + notas + bloque JSON `estudio.visor_ordenes/1`).
- Comprobado con e01 v1: la pose copiada coincide con la cámara de Blender (rotación igual, ≤ 4 mm), y la posición
  respecto del vagón coincide con el `desp_local` de la receta (x −0,30, y −1,35; la z se mide desde el origen del
  vagón, 2,8 m bajo el piso de la receta) y no cambia al avanzar el tiempo.
- Las notas se guardan en el navegador (por escena y huella) hasta borrarlas.

Carga three.js 0.147.0 desde cdn.jsdelivr.net (hace falta internet). También acepta `?glb=URL&json=URL` si se lo sirve
desde un sitio propio.
