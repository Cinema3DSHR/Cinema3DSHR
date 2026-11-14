# Resolución de errores

| Síntoma | Causa | Solución |
|---|---|---|
| `Couldn't open libEGL.so.1` / EEVEE no renderiza | Sin OpenGL en el servidor | `apt-get install libegl1 libgl1-mesa-dri`; o usar Cycles (por defecto). |
| `CUEW initialization failed` | Cycles busca CUDA | Aviso inofensivo: se usa CPU. |
| Render muy lento | EEVEE por software o muchas muestras | Calidad `revision` usa Cycles 10 muestras + denoise; probar encuadres con `fijas` y `humo`. |
| `Manifiesto inválido: tomas…` | Las tomas no son contiguas o no suman la duración | Corregir `inicio_s`/`duracion_s`. |
| `Ancla desconocida` | Nombre de ancla mal escrito | Ver `anclas` en `escenarios/<id>/escenario.json`. |
| La app dice «No se pudo leer el catálogo» | Todavía no corrió `catalogo.yml` o sin internet | Actions → «Catálogo para la app» → Run workflow. |
| La app no aprueba («código 401/403/404») | Token vencido o sin permiso Issues | AJUSTES → crear token fine-grained (Issues RW, sólo Cinema3DSHR). |
| APK de «PRUEBA» | Falta `ANDROID_KEYSTORE_PASSWORD` | Crear el secreto (docs/APP_ANDROID.md) y volver a correr «App Android». |
| «No se pudo descifrar la clave» | El secreto cambió | Volver a poner la contraseña original (no se puede recuperar la clave sin ella). |
| «Falta el secreto ASSETS_TOKEN» en Actions | La escena usa recursos privados (fútbol, Mixamo) | GitHub → Settings → Developer settings → Fine-grained token: repo **mixamo-respaldo**, *Contents: Read*. Guardarlo en Cinema3DSHR → Settings → Secrets → Actions como `ASSETS_TOKEN`. |
| El estadio importa lento o se cuelga | Mover miles de objetos de colección | Ya resuelto: se importa directo en la colección destino y los materiales se asignan por malla. |
| Godot: `Cannot infer the type` | Tipado estricto de GDScript | Declarar el tipo (`var x: float = …`). |
