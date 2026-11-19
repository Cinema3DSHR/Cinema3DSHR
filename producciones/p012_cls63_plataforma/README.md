# p012 · CLS 63 en plataforma

Flujo: Godot (escena base) → GLB → Blender (preparación artística) → previsualización → aprobación → BLEND autónomo → render final 1280×720.

- `godot/`: proyecto de Godot 4.7.2 con la escena base. El modelo `modelos/cls63.glb` no va a Git: se copia a `godot/modelos/` antes de abrir el proyecto.
- `blender/`: scripts de la etapa de Blender (inspección del GLB y, después, materiales, luces, humo y empaquetado).
- Los archivos generados (GLB, BLEND, video, imágenes) se entregan por chat y van a Releases sólo con la aprobación.
