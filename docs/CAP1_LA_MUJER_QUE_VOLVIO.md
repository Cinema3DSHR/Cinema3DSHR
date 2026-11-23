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
- **Disparo (casa, recuerdo del ataque):** fogonazo con luz puntual de 2–3 cuadros, humo de pólvora, casquillo que sale, golpe en el hombro de Gabriel con la camisa que se desgarra y salpicadura (partículas/líquido Mantaflow), mancha que se extiende en la tela y gotas en el suelo; cámara casi en una toma lenta rápida (30 fps, fotograma a fotograma). Violencia moderada y de tono dramático, sin recrearse.
