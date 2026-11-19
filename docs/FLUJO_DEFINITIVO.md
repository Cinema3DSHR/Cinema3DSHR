# Flujo definitivo de producción: creo → mirás → corregís → aprobás → la nube entrega el MP4

Desde el 19/11/2026. Una sola aprobación: la que da el dueño en el chat. No hay formularios, entornos protegidos de
GitHub ni pedidos de autorización aparte.

```
 1 CREAR        Claude arma la escena (receta escena.json): escenario, personajes, cámaras, animaciones, expresiones,
                voces (ElevenLabs con alineación), música, ambiente, luces, materiales, efectos.
 2 PREVISUALIZAR  python -m estudio previa <escena.json> --salida <scratchpad>/previa --audio
                → <e>_v<k>_previa.glb + .json + .m4a, mandados por el chat (SendUserFile). Sin render.
 3 CORREGIR     el dueño dice qué cambiar → versión nueva (python -m estudio nueva-version) → otra previsualización.
 4 APROBAR      el dueño dice «aprobada» → python -m estudio aprobar <escena.json> → commit + push →
                Claude lanza «Publicar escena aprobada» (publicar_escena.yml) con esa escena.
 5 RENDER       el mismo flujo, al publicar la Release, llama solo a render_escena.yml: reparte, renderiza desde el
                BLEND, monta con montar.py (audio intacto), verifica y suma el MP4 final a la Release.
```

## Etapa 2 — previsualización (liviana, sin render)

- Comando: `$PY -m estudio previa producciones/<p>/escenas/<e>/v<k>/escena.json --salida <scratchpad>/previa --audio`.
  Sale de la MISMA construcción que se renderiza (`director.construir`):
  - `<e>_v<k>_previa.glb`: geometría liviana para el teléfono, personajes con sus animaciones y **las formas de la
    boca y la cara** (los labios hechos con las alineaciones de ElevenLabs), cámaras de rodaje y luces;
  - `<e>_v<k>_previa.json`: línea de tiempo (tomas, cámaras, personajes);
  - `<e>_v<k>_previa.m4a`: la mezcla de la escena (`procedural.generar`, lo mismo que `audio_escena.py`), AAC 128k,
    con los tiempos y el volumen originales. No gasta créditos.
- Se le pasan los tres por el chat (`SendUserFile`, `display: "attach"`) y se registra la entrega
  (`estudio.proteccion.registrar`, deja `entregado.json`): la aprobación se compara contra ESA huella.
- **Cómo la abre el dueño en Android**:
  1. bajar los tres archivos del chat al teléfono;
  2. abrir el visor (https://claude.ai/artifact/SEW8AN7eTVhb1t3vaRAvJq, el mismo `visor/visor_escena.html`);
  3. **ABRIR ESCENA** y elegir los tres archivos juntos (mantener apretado para elegir varios);
  4. ▶ reproduce imagen y sonido juntos (el reloj es el del audio); ×1/×0,5/×0,25/×2 cambia la velocidad de los dos;
     🔊 AUDIO lo silencia; **MONTAJE** muestra el corte de cámaras, **TOMA** una cámara, **LIBRE** recorrer;
     **💡 LUCES DE LA ESCENA** cambia la luz pareja por las luces de Blender (aproximadas: el render final es Cycles);
  5. si quiere tocar cámaras: CÁMARA NUEVA / EDITAR, 📍 NOTA y **📋 COPIAR PARA CLAUDE** (docs/VISOR_Y_ORDENES_DE_CAMARA.md).
- También se puede publicar en la Release de la producción con `previa.yml` (sube GLB, JSON y M4A).
- Límite honesto: la luz del visor es una aproximación en tiempo real. La iluminación exacta sólo la da Cycles.

## Etapa 4 — aprobación y publicación

1. El dueño dice expresamente que la versión está aprobada (p. ej. «e02 v3 aprobada, renderizá»).
2. `python -m estudio aprobar producciones/<p>/escenas/<e>/v<k>/escena.json --nota "<frase del dueño>"`:
   - exige la previsualización entregada (`entregado.json`) con **la misma huella**: se aprueba lo que se vio;
   - pone `estado: aprobada`, `bloqueada: true` y en el `historial` la huella aprobada (la huella no cambia: no
     incluye estado, bloqueada ni historial). Desde ahí la receta no se puede editar: cambios = versión nueva.
3. Commit + push en la rama de la sesión, y lanzar **«Publicar escena aprobada»** (`publicar_escena.yml`, entrada
   `escena` = la ruta) sobre esa rama. Esa frase del dueño es la autorización de la publicación y del render.
4. El flujo:
   - se niega si la escena no está aprobada y bloqueada, si la huella no es la aprobada o si la Release ya existe;
   - `publicar-escena preparar`: construye la escena **una vez**, guarda muestras de control (cámara, valores de
     las formas de la cara, caderas), fija la semilla y el PNG del render, empaqueta todo y guarda el BLEND; con las
     pistas de esa construcción genera un WAV de control;
   - `publicar-escena validar`: abre el BLEND en un Blender limpio y comprueba, sin el Python del estudio, la cámara
     de cada cuadro (marcadores), las muestras de control, el rango, los fps, la resolución y que no dependa de
     nada externo;
   - `audio_escena.py` (sin cambios) hace el WAV definitivo y `publicar-escena cerrar` exige que sea **idéntico
     byte a byte** al de control: así BLEND y WAV son de la misma receta;
   - publica la Release `escena-<produccion>-<e>-v<NNN>` (primero borrador; se publica sólo si están todos los
     archivos con su tamaño): `<e>_v<k>.blend`, `<e>_v<k>.wav`, `<e>_v<k>_voces.zip` (mp3 y JSON de alineación que
     usó la cara), `<e>_v<k>_escena.json`, `manifest.json` (`estudio.version_escena/1`, SHA-256 de todo, huella,
     tomas, voces, render, control).

## Etapa 5 — render automático (`render_escena.yml`)

Lo llama `publicar_escena.yml` apenas publica. Sin otra aprobación:

1. **planificar**: baja el manifiesto, exige versión completa (no ensayo), reparte los cuadros en ≤ 60 tramos.
2. **render** (en paralelo): instala sólo Blender, baja el BLEND, **verifica su SHA-256**, renderiza su tramo con
   `render-trozo` (cámaras por los marcadores; cada cuadro se reintenta una vez). No reconstruye ni usa Godot.
3. **montar**: junta los cuadros (si falta alguno se detiene sin rellenar), baja el WAV y la receta de la misma
   versión y **verifica sus SHA-256**, corre `montar.py --audio-intacto` (sin `loudnorm` ni `-shortest`: si el WAV
   no dura lo mismo que el video ±1 cuadro, se detiene; después compara el audio del MP4 con el WAV: duración,
   desfase = 0 muestras y volumen ±0,5 dB), verifica el MP4 (cuadros, resolución, fps, duración) y suma
   `<e>_v<k>_final.mp4` + `<e>_v<k>_final_informe.json` a la Release de la versión (nunca sobrescribe).

Si falta un cuadro: lanzar a mano «Render de escena publicada» con el mismo `tag`, `cuadros` = los que faltaron y
`corrida_previa` = la corrida que falló.

## Reglas

- La previsualización no es el render final ni gasta recursos de producción.
- No se publica una versión sin la aprobación del dueño en el chat (`aprobar` + flujo).
- Una versión aprobada no se reconstruye ni se edita; cualquier cambio es una versión nueva con su propia revisión.
- El sistema de voces, alineaciones y labios (`elevenlabs.py`, `cara_anime.py`, `expresiones_3d.py`,
  `procedural.py`, `audio_escena.py`) no se modificó.
- Si una verificación falla, el flujo se detiene y Claude le cuenta al dueño cuál y por qué.
- Escenas con cámara lenta (`mapa_tiempo`) no se pueden publicar así (el BLEND solo no reproduce sub-cuadros).
