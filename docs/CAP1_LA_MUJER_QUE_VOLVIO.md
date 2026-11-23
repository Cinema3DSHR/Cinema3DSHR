# «La mujer que volvió de la muerte» — plan de producción (23/11/2026)
**Formato: VERTICAL 540×960 @30 fps** (TikTok/Shorts/Reels; «520p» del pedido = 540p). Carpeta: `producciones/p022_la_mujer_que_volvio`.
Metodología única: Godot arma todo → Blender (luces, lluvia, niebla, humo, relámpagos, Cycles) → GLB de revisión → aprobación → render en la nube.

## Recursos
- **Auto:** `hustler.glb` subido por el dueño (negro; 58 piezas sueltas: capó, paragolpes, puertas, baúl, vidrios, ruedas; 1,8 × 1,48 × 4,59 m, largo en Z). No trae daño: la destrucción se arma deformando/soltando piezas. Copia de trabajo en `/home/user/cap1_noir/auto/` (no va al repo: regla 5). **Origen del modelo sin licencia (parece de un juego de carreras): confirmar antes de publicar.**
- **Gabriel = Aiden, Elena = Kate** (`/home/user/cap3/entrega/*.glb`, ropa nueva: camisa elegante con sangre y herida de hombro para él).
- **Voz:** `gabriel_noir` (5egO01tkUjEzu7xSSE8M), ≈1.475 caracteres ≈ 1.500 créditos; estimar y verificar la voz antes de `--gastar`.

## Plan
1. **Accidente (0:00–1:40):** tormenta, ruta mojada, derrape, choque y auto destruido (balizas, humo). Tomas en 1.ª persona del conductor con respiración y latidos que suben en el derrape y quedan sordos tras el golpe; salida del auto y búsqueda de Elena (sin diálogo, voz en off).
2. **Recuerdos (1:40–2:20):** composiciones oscuras (habitación, whisky, cigarrillo, expedientes, pasillos), sin insignias reales.
3. **La casa (2:20–3:40):** sillón, tormenta, cortinas con tela, humo, camisa con sangre, pistola, monólogo.
4. **Final (3:40–4:00):** cámara que se aleja, relámpago, negro y título.
5. **Sonido:** música original (piano/cuerdas), lluvia, viento, truenos, derrape, impacto, latidos, respiración; voz siempre por encima. Subtítulos discretos.
Capas 2.5D (fondos, niebla, montañas) donde convenga; geometría 3D para auto, personajes y casa.

## Sangre y disparo (pedido del dueño, 23/11/2026)
Se resuelven en la **etapa Blender** (los materiales procedurales no viajan en el GLB; Godot sólo deja los puntos de anclaje y las cámaras).
- **Sangre en el suelo (accidente):** charcos y gotas como decals/mallas finas sobre el asfalto con material propio (rojo oscuro, brillo húmedo, coat transparente, bordes irregulares por ruido), mezclados con la lluvia (la lluvia los diluye y arrastra hilos hacia el borde); gotas sobre piedras y sobre el auto.
- **Rostro y manos:** máscaras de sangre por región (frente, ceja, labio, nariz, nudillos, palmas, uñas) que se mezclan sobre el material de piel de Aiden (ya hay piel real con subsuperficie), con sangre fresca que corre y se oscurece/seca según la toma; aparecen después del choque (continuidad: antes del golpe, limpias).
- **Disparo: NO se muestra en este capítulo** (aclaración del dueño, 23/11/2026). En la casa Gabriel ya tiene la herida de bala en el hombro (camisa manchada, sangre en el suelo, brazo pegado al torso) y sólo la nombra en el monólogo («me disparó»). **Por qué lo hirieron se cuenta en otro capítulo**: ahí va el disparo real hecho con Blender (fogonazo, humo, casquillo, salpicadura con líquido). Guardado como pendiente del cap. 2.
- **Estructura:** el recuerdo del accidente nace en la casa, porque ver a Elena viva le resulta irreal; el orden entre accidente y casa es flexible (se puede abrir con el accidente y luego la casa, o intercalar). Por defecto: accidente → recuerdos → casa → final.

## Dirección del dueño para la casa y el orden (23/11/2026)
- **Orden:** el accidente va AL INICIO (Gabriel ya está pensándolo en su casa) → recuerdos → casa, donde termina de pensar herido de bala, sin mostrar el disparo.
- **Mesa de la casa (inmersiva, con tomas de detalle):** botella y copa con vino real (líquido con refracción y menisco), **otra botella tumbada** con el líquido derramado sobre la mesa (se le cayó; charco que gotea al borde), y **un cigarro real prendido en el cenicero con ceniza real** (brasa que late, ceniza que se curva y cae, hilo de humo). No hace falta que beba en escena: se da a entender.
- En el monólogo se pregunta por qué ella, si ese día murió en el accidente. Nivel de realismo y acabado: producción AAA.
- Voz: muestra enviada; `producciones/p022_la_mujer_que_volvio/herramientas/voces_cap1.py` (42 líneas, 2.354 créditos estimados).

## Contexto narrativo (dueño, 23/11/2026) — tenerlo en cuenta en todo el capítulo
Tras el choque Gabriel busca a Elena desesperado; **se le apaga la visión y queda desmayado**: ahí pierde el rastro. **Pasa 1 año** y recién después ocurre lo del disparo y lo demás (se cuenta en otros capítulos). Por eso en el accidente: la búsqueda termina con visión que se cierra (viñeta, desenfoque, latidos que se apagan) y caída, y el corte a negro es ese desmayo. La narración dice «durante años creí que había muerto»; no contradecir con el «1 año» (el capítulo siguiente aclara los tiempos).

## Estado (23/11/2026)
- Voz de Gabriel **generada**: 42 líneas, 111,9 s, 2.354 créditos (`audio_cap1/voces.json`; mp3 en `audio/biblioteca/`, ledger actualizado). Accidente 37 s de voz, recuerdos 36 s, casa 38 s.

## Auto en Godot (23/11/2026)
`godot_cap1/tools/auto.gd` carga `assets/hustler.glb` (no va al repo; copia en `/home/user/cap1_noir/auto/`), lo gira 180° (el original mira a +Z; las piezas del estudio miran a −Z) y repinta la carrocería de NEGRO brillante (el modelo viene claro). Es un cupé clásico de los 70. Pruebas: `tools/prueba_auto.gd`.

## Escena del viaje (dueño, 23/11/2026): los dos dentro del auto, de noche, con lluvia
Gabriel (conduce) y Elena (acompañante) adentro del cupé negro: faros que iluminan la ruta mojada, limpiaparabrisas en movimiento (barrido de 1,5 s, igual que el sonido), gotas en el parabrisas, ambiente de cabina + lluvia, música; vertical 540×960 para TikTok/Shorts/Reels. Va al inicio, con la voz «Hay noches que nunca terminan… Íbamos juntos… no recuerdo qué pasó primero».
- **Sonido hecho:** `herramientas/audio_viaje.py` (procedural, sin créditos): lluvia en el techo, ruta mojada, motor, limpiaparabrisas, 2 truenos, música (cuerdas + piano en La menor) y la voz (líneas 1–5). La voz termina a los ~25 s.
- **Pendiente imagen:** sentados con `sit_idle`/`nervous` + brazos al volante (agarre de manos), limpiaparabrisas animados, faros con cono y lluvia (Blender), ruta que pasa (parallax/terreno que se desplaza), cámaras: interior sobre el hombro, perfil de ambos, faros por delante, exterior bajo.

## Avance de la escena del viaje (23/11/2026)
- Gabriel (al volante, lado +X) y Elena (acompañante, −X) sentados en el cupé con `sit_idle`; manos de Gabriel sobre el volante con cinemática inversa de dos huesos (`godot_cap1/tools/ik.gd`, error 0 mm) y manos de Elena sobre las piernas. Prueba: `tools/prueba_sentados.gd` (corte con la carrocería oculta).
- El auto **ya trae limpiaparabrisas modelados** (brazos blancos en la base del parabrisas): se animan con el mismo período que el sonido (1,5 s).
- **Pendiente:** ropa nueva (hoy llevan el traje espacial como reemplazo: camisa oscura para Gabriel y abrigo para Elena en Blender), animar limpiaparabrisas, faros con cono y luz sobre la ruta mojada, ruta que pasa (suelo y árboles que se desplazan), gotas y lluvia en el parabrisas (Blender), cámaras verticales y exportación GLB para revisión.

## Rig de piloto de Dream Rally portado (23/11/2026)
El dueño indicó usar lo de **Dream Rally** (`Rally-Sim-movile/godot/game/car/rig_pilot.gd`, `cockpit.gd`). Se portó a `godot_cap1/tools/rig_sentado.gd` (clase `RigSentado`): cadera, columna, cabeza, brazos con dedos, piernas con pies en pedales por IK de dos huesos, adaptado a los huesos `EM3D_Base_*` (esqueleto en cm con Z arriba → se convierte al espacio de la cabina con `T`). Se usan los mismos parámetros de Dream Rally para manos en el aro (10 y 2 horas), pies en pedales, limpiaparabrisas (ciclo de 1,4 s, barrido 1,65 rad) y gotas en el parabrisas. Prueba: `tools/prueba_sentados.gd` (Gabriel al volante y Elena de acompañante, cortes de revisión).
**Voz del viaje (ajuste):** estaba 0,9 dB sobre el fondo; ahora el fondo baja y se agacha 85 % mientras habla (voz normalizada a 0,85, fondo ×0,55): **+9 dB** de voz sobre el fondo (`herramientas/audio_viaje.py` lo imprime). Limpiaparabrisas del sonido a 1,4 s para coincidir con la imagen.
