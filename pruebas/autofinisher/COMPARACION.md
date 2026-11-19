# Reconstrucción de «Casa moderna en tormenta» con el AutoFinisher (prueba técnica local, 19/11/2026)

Sin render y sin Actions. Mismo GLB para las dos construcciones:
- Godot 4.7.2 headless sobre una **copia** del proyecto `pruebas/godot_blender/godot`. El script original reescribe
  el `.tscn` versionado, por eso no se corrió sobre la carpeta original.
- La Kodiak se tomó de Rally-Sim-movile.
- Resultado: 47,0 MB en 15 s.

| | Prueba original (`armar.py` b6–b9, sin cambios) | AutoFinisher (`casa_tormenta.receta.json`) |
|---|---|---|
| Tiempo de máquina | 3,8 s (importar 2,67 · efectos 0,97 · Cycles 0,02 · guardar 0,14) | 3,06 s (importar 2,50 · efectos 0,32 · guardar 0,13 · manifiesto 0,08 · resto < 0,02) |
| RAM máxima | no se medía | 877 MB (importar 823 MB) |
| `.blend` | 37,1 MB | 37,1 MB, autónomo (imagen `kodiak_0` empaquetada) |
| Identidad | — | `casa_tormenta_v001`, manifiesto con SHA-256 del `.blend`, del GLB, de la receta y de los scripts |

## Comparación campo por campo

Herramienta: `resumen_blend.py` + `comparar.py`. Compara la escena, Cycles, los 288 objetos, las 16 luces (energía,
color, radio, ángulo y las 312 claves animadas reescaladas), todos los materiales, el mundo, los nodos de cada efecto
y las imágenes.

Resultado: **721 campos iguales y 6 distintos.**

| Diferencia | Por qué |
|---|---|
| `Chispa`, `Choque_techo_casa`, `Gota_lluvia`: colección `Choque_lluvia_oculto` → `FX_auxiliares_ocultos` | Nombre general de la colección de auxiliares ocultos. Sigue sin renderizarse; no cambia la imagen. |
| Fuego: umbral 0,08 → 0,05 · ganancia 9 → 12 · emisión 22 → 90 | **Corrección pedida**: las llamas salían más tenues que las brasas. Sin verificar con render. |

Iguales: las 16 luces y sus claves, los vidrios, el mundo, la lluvia (9.000 gotas, caja, velocidades, viento,
choques), el humo, las brasas, el relámpago, Cycles (6 muestras, adaptativo 0,05, OIDN, rebotes, árbol de luces, AgX,
pasos de volumen), el rango 0–899, los 30 fps, la cámara, las acciones y el empaquetado.

## Diferencias de comportamiento encontradas (y cómo quedaron)

- **`vidrio_opalino`**: el AutoFinisher reconoce los vidrios por el prefijo `vidrio*`, y la prueba sólo convertía los
  de una lista fija. La primera reconstrucción lo dejó transmisivo; la prueba lo dejaba opaco. Se excluye en la
  receta (`"vidrio_opalino": null`) y queda igual que el original.
- **Formato de cuadros**: b9 dejaba JPEG 92 como salida del `.blend`, pero `render_trozo.py` igual renderizaba PNG. El
  AutoFinisher deja PNG en el `.blend` y el render usa PNG. El resultado no cambia.
- **Árbol de luces**: b9 no lo fijaba (Blender lo trae activo); el AutoFinisher lo fija explícitamente. Mismo valor.
- **Largo del rayo de la lluvia**: 40 m, igual que la prueba (parámetro `largo_rayo`).

## Otras comprobaciones locales

- `validar`: OK. El `.blend` abre en 0,38 s, es autónomo, y su cámara, rango, fps, resolución y muestras coinciden con
  el manifiesto.
- `verificar-blend`: OK. Con un byte cambiado en una copia, rechazado. `render-trozo` también se niega a abrirla.
- `render-trozo --sin-render` con los cuadros 1–15: los recorre en 2,5 s; informe con RAM 899 MB.
- La misma versión no se puede volver a construir encima.
- Descarga real desde la Release `prueba_godot_blender` (`casa_tormenta_540p.mp4`, 10,8 MB, 1,2 s): el SHA-256
  coincide con el que informa GitHub, y el MP4 pasa la verificación de video (900 cuadros, 540×960, 30 fps, 30 s).
- Recursos de la receta: la Kodiak bajó de Rally-Sim-movile por clon disperso (37,2 MB, 2,8 s), idéntica.
- Montaje con 30 PNG sintéticos de ffmpeg (no es un render):
  - con un cuadro faltante, la publicación se detiene y no se crea ningún archivo;
  - completos, sale el MP4 y pasa la verificación.
- `test_autofinisher.py` 32/32 y `test_general.py` 13/13. Este último usa una escena que no es la casa: dos cámaras,
  farola, neón animado, vidrio, emisivo, y sólo el fuego pedido entre dos vacíos FX.
