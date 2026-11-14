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

## ElevenLabs (conectado el 14/11/2026)

**Estado probado:** conexión OK (plan **Starter**, 40 000 créditos/mes), 27 voces en la cuenta, voz en español generada
y mezclada en una escena (`p002_la_jefa_llega`), efecto de sonido generado. **Música: no probada** (el endpoint
está escrito pero no se lo llamó: puede requerir otro plan).

**Credencial:** la guardó el dueño con el formulario seguro del entorno; el proxy la inyecta en las llamadas a
`api.elevenlabs.io`. No está en el repo ni en la APK. En otra máquina: variable `ELEVENLABS_API_KEY` (y secreto del
repo si algún flujo de Actions generara audio; hoy **no hace falta**: el audio se genera acá y se guarda en la
biblioteca de Git).

### Cómo se usa (`estudio/audio/elevenlabs.py`)
En `sonido.eventos` de la escena:
```jsonc
{"tipo": "voz", "rol": "jefa", "texto": "Buenas noches. Llegué antes de lo previsto.", "inicio_s": 10.6, "movil": "jefa"},
{"tipo": "efecto", "prompt": "crujido de una puerta de madera pesada abriéndose lentamente", "duracion_s": 2.0, "inicio_s": 12.2}
```
1. `python -m estudio voces <escena.json>` → **sólo estima** (créditos) y lista lo que falta.
2. `python -m estudio voces <escena.json> --gastar` → genera lo que falta y lo guarda en `audio/biblioteca/`.
3. `python -m estudio cerrar …` mezcla desde la biblioteca (nunca gasta). Con `movil`, el volumen y el paneo siguen
   al personaje respecto de la cámara; sin `movil`, va centrado (voz en off, radio, música).
Otros comandos: `audio-estado` (plan y créditos), `voces-lista` (voces de la cuenta).

### Reglas de gasto
- Lo que ya existe **no se regenera** (el nombre del archivo es el hash del pedido completo: texto, voz, modelo, ajustes).
- Tope por escena 4 000 créditos y reserva mensual de 5 000 (`config/presupuesto_audio.json`); pasarse requiere OK del dueño.
- Cada generación queda en `audio/ledger.jsonl` y en `catalogo/audio.json` (id, duración, procedencia, licencia, etiquetas).
- **Costo real:** el panel de ElevenLabs (Usage). La cabecera `character-cost` que devuelve la API no coincidió con el
  costo esperado (17 para 43 caracteres) y el contador de la suscripción tardó en moverse: por eso el registro guarda
  la cifra estimada y la de la cabecera.

### Voces (`config/voces.json`, propuesta: el dueño decide)
`jefa` = «BV Operadora (contrato)» (mujer **argentina**, una de las 6 voces propias en español de Black Veil),
`operador_peninsular`, `mujer_joven`, `hombre_joven`, `hombre_grave`, `narrador`, `narradora`, `radio`.
Modelo por defecto `eleven_multilingual_v2`; la cuenta también ofrece `eleven_v3` y `eleven_v4` (no probados).

### Lecciones de la prueba
- Los efectos salen a niveles muy dispares (el de la puerta: pico −36 dB): la mezcla los normaliza a −6 dB de pico.
- Un prompt de efecto no debe nombrar lo que no querés oír («silencioso»).
- **No pude escuchar** los audios, sólo medirlos: conviene que los escuches vos antes de aprobar.
