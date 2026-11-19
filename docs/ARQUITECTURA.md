# Arquitectura

## Componentes

| Componente | Dónde | Qué hace |
|---|---|---|
| `estudio/` (Python) | Sesión de Claude y GitHub Actions | Todo el sistema de producción. `python -m estudio …` |
| `estudio/blender/kit.py` | | Piezas procedurales: materiales PBR en coordenadas de mundo, cajas con bisel, instancias, luces, cielo nocturno, niebla, utilidades de animación. |
| `estudio/escenarios/<generador>.py` | | Un generador por tipo de escenario (hoy: `nave_deriva`, `nave_deriva_ampliada` de «A la deriva» y `prueba_minima` de las pruebas). Devuelve **anclas** (puntos de interés) y **animables** (portón, garaje, puerta…). |
| `estudio/blender/vehiculos.py` | | Sedán procedural genérico; recorridos suaves con tiempos y paradas (interpolación monótona: nunca retrocede). |
| `estudio/blender/camaras.py` | | Tipos de toma cinematográfica calculados fotograma a fotograma (dolly, grúa, órbita/aérea, seguimiento, detalle, vigilancia, subjetiva, paneo…), profundidad de campo, cámara en mano, luz de relleno. |
| `estudio/blender/director.py` | | Arma la escena desde su manifiesto, configura el render, renderiza por toma (reanudable), exporta pistas para el sonido, guarda el `.blend`, exporta el GLB del visor. |
| `estudio/audio/procedural.py` | | Ambiente, motor y mecanismos sincronizados con la escena. |
| `estudio/montaje.py` | | FFmpeg: tomas → escena (MP4 + OGV + portada), efectos de montaje, película final. |
| `estudio/manifiesto.py` | | Validación de recetas, versiones, huella de render, bloqueo de aprobadas. |
| `estudio/publicacion.py` | | Catálogo para la app (manifiestos + releases + issues) y plan de limpieza. |
| `estudio/catalogo/animaciones.py` | | Inventario y buscador de animaciones. |
| `catalogo/*.json` | Git | Catálogos de animaciones, armas, vehículos y audio. |
| `escenarios/<id>/escenario.json` | Git | Escenarios reutilizables (receta). |
| `producciones/<id>/…/escena.json` | Git | Recetas versionadas de cada escena. |
| `app/` | Godot 4.7.2 | Cliente Android liviano. |
| `.github/workflows/` | Actions | `render`, `catalogo`, `revisiones`, `pelicula`, `limpieza`, `apk`. |

## Flujo de datos

```
Claude ──escribe──► producciones/P/escenas/E/vK/escena.json ──push──► [render.yml]
   planificar (qué cambió; salta publicadas y aprobadas)
   render ×N (una máquina por toma: Blender bpy + Cycles → JPG → toma.mp4)
   cerrar  (pistas → audio procedural → montaje FFmpeg → MP4 + OGV + portada; .blend; GLB del visor; info.json)
   └─► Release "P": E_vK_revision.mp4/.ogv, _portada.jpg, _miniatura.jpg, _visor.glb, _proyecto.blend, _audio.wav, _info.json
[catalogo.yml] manifiestos + releases + issues ─► Release "catalogo": catalogo.json
App Android ─► lee catalogo.json ─► descarga con caché por SHA-256 ─► reproduce / visor 3D
App ─► (token del dueño) Issue "[REVISIÓN] …" con JSON ─► [revisiones.yml]
   APROBAR/RECHAZAR: registra y cierra · CORREGIR: queda abierto para Claude · RENDERIZAR: render.yml · EXPORTAR: pelicula.yml
```

## Almacenamiento (sección 12 del pedido)

| Clase | Qué | Dónde | Se borra |
|---|---|---|---|
| Permanente | código, scripts, documentación, manifiestos, catálogos, recetas, configuración | Git (este repo) | Nunca |
| Pesado reutilizable | animaciones, armas, personajes, vehículos (originales) | Repos privados de origen (`mixamo-respaldo`, `Operaci-n-Nexus-1`, `Extraction-tactical`), sólo lectura | Nunca |
| Proyecto editable de cada versión | `*_proyecto.blend`, `*_visor.glb`, `*_audio.wav`, portadas, `*_info.json` | Release de la producción | Nunca (automáticamente) |
| Temporal | `*_revision.mp4`, `*_revision.ogv` de versiones reemplazadas o rechazadas | Release de la producción | Sí, según `config/retencion.json` (30 días reemplazadas, 14 rechazadas). Nunca la versión actual ni las aprobadas. |
| Intermedios de render | fotogramas JPG, tomas sueltas | Artifacts de Actions (2 días) / `salida/` local (ignorado por Git) | Solos |

El borrado (`limpieza.yml`) tiene doble seguro: el plan sólo incluye tipos temporales y el script se niega a borrar
cualquier archivo cuyo nombre no termine en `_revision.mp4` / `_revision.ogv`. La receta (escena.json) siempre
permite reconstruir la escena aunque se borre su video.

## Seguridad

- Ninguna clave en el repositorio ni en la APK. Secretos sólo en *GitHub → Settings → Secrets and variables → Actions*.
- Lectura pública; escritura (decisiones, renders, exportaciones) sólo con el token del dueño. `revisiones.yml`
  ignora issues de cualquier otra cuenta y el catálogo sólo cuenta decisiones con `author_association = OWNER`.
- La clave de firma Android se guarda cifrada (AES-256, PBKDF2 600 000 iteraciones) en la release `firma`; la
  contraseña sólo está en el secreto `ANDROID_KEYSTORE_PASSWORD`.
- Valores que vienen de issues se pasan a los scripts por variables de entorno (no se interpolan en el shell).
