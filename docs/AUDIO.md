# Audio

## Hoy (sin servicios pagos)

`estudio/audio/procedural.py` sintetiza con numpy, sincronizado con la escena:
- **Ambiente** `noche_suburbio`: viento (ruido marrón modulado), rumor de ciudad, grillos.
- **Motor** de cada vehículo: tono que sube con la velocidad real (pistas por fotograma), aspereza, rodado sobre
  asfalto mojado proporcional a la velocidad.
- **Mecanismos**: portón con motor (zumbido + golpe final), portón seccional (traqueteo).
- Espacialización por toma: volumen por distancia a la cámara activa y paneo izquierda/derecha.
- Mezcla normalizada a −16 LUFS en el montaje.

Biblioteca: `catalogo/audio.json` (id, nombre, categoría, procedencia, licencia, etiquetas, variantes, volumen).
Ya existen para importar: disparos OGG de Extraction-tactical y voces ElevenLabs de Operación Nexus.

## ElevenLabs (Etapa 6 — falta autorización)

Para conectarlo hace falta, del dueño:
1. Una **API key** de ElevenLabs con permisos de *Text to Speech*, *Sound Effects* y (si se usa) *Music*.
2. Guardarla como secreto del repositorio `ELEVENLABS_API_KEY` (Actions) y, para usarla desde la sesión de
   Claude, como credencial del entorno (nunca en el chat ni en archivos).
3. Indicar el plan/créditos disponibles para fijar un tope de gasto por producción.

Plan de integración: `estudio/audio/elevenlabs.py` con caché por (texto, voz, ajustes) → hash, de modo que un
diálogo o efecto que ya existe **no se vuelve a generar**; cada archivo generado se registra en
`catalogo/audio.json` con procedencia «ElevenLabs», fecha y licencia de la cuenta. Los efectos se sincronizan con
las animaciones por eventos (p. ej. recarga → sonido en el fotograma del clip marcado en el catálogo).
