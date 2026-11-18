# Visor de escenas (HTML)

`visor_escena.html`: un solo archivo para revisar una escena en el navegador (también del celular), sin Godot ni la app.
Versión publicada para el teléfono: https://claude.ai/artifact/SEW8AN7eTVhb1t3vaRAvJq (privada del dueño).

- **ABRIR ESCENA**: el `.glb` de la escena (y, si vino, el `.json` de la línea de tiempo: elegir los dos juntos). Hoy sirve
  el par `<escena>_v<k>_previa.glb` + `.json` que ya exporta `python -m estudio previa` / `previa.yml`. Si la línea de
  tiempo viene dentro del GLB (`extras.estudio_previa` de la escena o del archivo), alcanza con el GLB solo.
- **MONTAJE** (cámara de cada toma según la línea de tiempo), **TOMA** (una cámara fija), **LIBRE** (recorrer la escena:
  1 dedo mira, 2 dedos acercan y corren, cruceta ▲▼◀▶⤒⤓ con rapidez 2 / 6 / 0,5 m/s; teclado WASD QE; LENTE en mm;
  «Pegada a»: la cámara viaja con el vagón / auto / personaje). Siempre se ve el cuadro del render (misma proporción).
- **➕ CÁMARA NUEVA**: agrega una cámara donde estás mirando (tramo por defecto: desde ahí hasta el fin de la toma;
  reemplaza esa toma o «toma nueva»). **✏️ EDITAR CÁMARA DE LA TOMA**: arranca en la cámara de rodaje de la toma
  actual (pegada a lo que la lleva) para subirla, correrla, girarla o cambiarle el lente. Mientras dice
  «EDITANDO CÁMARA N», todo lo que se mueve queda en esa orden (en una modificación, además, el cambio en palabras:
  «0,30 m más alta · gira 5° a la izquierda · lente 32 → 45 mm»); ✔ LISTO deja de editar. Cada cámara de la lista
  tiene EDITAR (volver a ajustarla), ✕ y los campos desde/hasta/qué reemplaza/movimiento/nota; en LIBRE se ven como
  conos rojos.
- **📋 COPIAR PARA CLAUDE**: todas las cámaras y notas en un solo texto + bloque JSON `estudio.visor_ordenes/2`
  (por cámara: acción nueva/modificar, toma, tramo en segundos y cuadros, pose respecto del objeto al que va pegada
  — objeto.matrix_world⁻¹ · cámara.matrix_world, Blender — y en el mundo, la original si es una modificación, lente).
- ▶/⏸, cuadro a cuadro, velocidad ×1 ×0,5 ×0,25 ×2, línea de tiempo con los cortes de toma, qué clip hace cada personaje.
- Sin luces del archivo ni sombras: luz pareja; **COLOR PLANO** apaga la luz por completo.
- **📍 NOTA**: un comentario en el momento actual (va en el mismo texto).
- Comprobado con e01 v1: la pose copiada coincide con la cámara de Blender (rotación igual, ≤ 4 mm), y la posición
  respecto del vagón coincide con el `desp_local` de la receta (x −0,30, y −1,35; la z se mide desde el origen del
  vagón, 2,8 m bajo el piso de la receta) y no cambia al avanzar el tiempo.
- Las notas se guardan en el navegador (por escena y huella) hasta borrarlas.

Carga three.js 0.147.0 desde cdn.jsdelivr.net (hace falta internet). También acepta `?glb=URL&json=URL` si se lo sirve
desde un sitio propio.
