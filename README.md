# 3D FILM STUDIO

Estudio cinematográfico 3D automatizado: **Claude Code** dirige, **Blender** (como módulo de Python) construye y
renderiza, **FFmpeg** monta, **GitHub** guarda y publica, y una **app Android en Godot 4.7.2** sirve para mirar,
recorrer en 3D, aprobar, pedir correcciones y exportar.

| Quiero… | Ir a |
|---|---|
| Entender las decisiones y lo que se midió | [`docs/INFORME_ETAPA1.md`](docs/INFORME_ETAPA1.md) |
| Ver la arquitectura y el almacenamiento | [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md) |
| Producir (para Claude) | [`CLAUDE.md`](CLAUDE.md) · [`docs/FLUJO_DE_PRODUCCION.md`](docs/FLUJO_DE_PRODUCCION.md) |
| Instalar la app, firma y token | [`docs/APP_ANDROID.md`](docs/APP_ANDROID.md) |
| Animaciones, personajes, armas, vehículos | [`docs/ANIMACIONES_Y_PERSONAJES.md`](docs/ANIMACIONES_Y_PERSONAJES.md) |
| Películas de fútbol (jugadores, estadio, pelota) | [`docs/FUTBOL.md`](docs/FUTBOL.md) |
| Audio y ElevenLabs | [`docs/AUDIO.md`](docs/AUDIO.md) |
| Algo falla | [`docs/ERRORES.md`](docs/ERRORES.md) |
| Qué se hizo y qué falta | [`docs/REGISTRO.md`](docs/REGISTRO.md) |

```
estudio/        sistema de producción (python -m estudio …)
  blender/      kit procedural, cámaras, vehículos, director (bpy)
  escenarios/   generadores de escenarios (mansion_moderna, …)
  audio/        sonido procedural (ElevenLabs: Etapa 6)
  catalogo/     inventario y buscador de animaciones
catalogo/       animaciones.json (3292 clips), armas.json, vehiculos.json, audio.json
escenarios/     escenarios reutilizables (recetas)
producciones/   películas y escenas: recetas versionadas (escena.json)
app/            cliente Android (Godot 4.7.2)
config/         política de retención de temporales
.github/workflows/  render · catalogo · revisiones · pelicula · limpieza · apk
```

Los videos y archivos pesados **no** van a Git: se publican en las *Releases* de este repositorio.
