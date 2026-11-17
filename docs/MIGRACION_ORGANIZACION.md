# Migración de Cinema3DSHR a la organización «Cinema3DSHR» (GitHub Team)

Objetivo: que los flujos de GitHub Actions corran con el límite de la organización Team (60 trabajos simultáneos; hoy,
en la cuenta personal, se midieron 20: corrida 44076765471, 17/11/2026). Estado: **AUDITADO, SIN TRANSFERIR.**

## 1. Qué hay hoy (auditado el 17/11/2026)

- Repositorio: `webmaletin-art/Cinema3DSHR`, **público**. Una sola rama: `ccr-6d21fe8a-76t9c3` (es la rama por defecto).
  7 releases: `catalogo`, `escenarios`, `p000_prueba_mansion`, `p005_mansion_cqb_30s_720p_30fps`,
  `p006_operacion_tren_fantasma`, `p007_al_vacio`, `p008_drift_sunset`. (No hay release `firma` ni `app`: la APK
  firmada todavía no se armó con la clave definitiva.)
- Flujos (11): apk, catalogo, direccion, episodio, limpieza, pelicula, previa, render, revisiones, verificar-acceso,
  video30. Disparadores: push (apk, render), issues (direccion, revisiones), schedule (catalogo, limpieza), el resto a
  mano. Todos declaran sus `permissions:` explícitos (no dependen del permiso por defecto de la organización).
- Secretos que usan los flujos (sólo nombres): `ASSETS_TOKEN` (20 usos), `ANDROID_KEYSTORE_PASSWORD` (2).
- Variables: `MIXAMO_REF`, `NEXUS_REF`, `EXTRACTION_REF`, `RALLY_REF`, `DIRECCION_RAMA` (si no existen, los flujos
  usan valores por defecto).
- Recursos externos (se quedan donde están, NO se tocan): `webmaletin-art/mixamo-respaldo` (privado),
  `webmaletin-art/Operaci-n-Nexus-1`, `webmaletin-art/Extraction-tactical`, `webmaletin-art/Rally-Sim-movile`. Se leen
  con `ASSETS_TOKEN` (token del dueño); los flujos los nombran con la ruta completa, así que siguen igual.
- Acciones usadas: sólo las de GitHub (`actions/checkout`, `setup-python`, `cache`, `upload-artifact`,
  `download-artifact`).
- Código con el nombre del repositorio: `estudio/config.py` (`REPO`, se puede pisar con `CINE_REPO`),
  `app/boot/boot.gd` y `app/main/api.gd` (la app del teléfono). En `api.gd` el nombre del repositorio también forma
  parte de la clave con la que el teléfono guarda cifrado tu token: si se cambia, la app pide el token de nuevo una vez.
- La organización `Cinema3DSHR` existe (tipo Organization). **No pude verificar desde acá su plan (Team) ni tu rol**:
  la app de Claude para GitHub no está instalada en la organización.

## 2. Qué se mueve con la transferencia (según la documentación de GitHub)

Se mueve todo el repositorio: código, ramas, historial, issues (con sus etiquetas `correccion`, `direccion`, `revision`),
releases y sus archivos, historial de Actions. Los secretos, webhooks y llaves de despliegue del repositorio quedan
asociados después de la transferencia. GitHub redirige las direcciones viejas (web, `git` y API) al nuevo lugar
mientras no se cree otro repositorio con el nombre viejo.

Puede verse afectado (y se verifica uno por uno después):

| tema | riesgo | medida |
|---|---|---|
| `ASSETS_TOKEN` y `ANDROID_KEYSTORE_PASSWORD` | si no viajaran, habría que volver a cargarlos (sus valores sólo los tenés vos) | verificarlos con «Verificar acceso» antes de cualquier otra cosa; NO se regeneran |
| variables `*_REF` | podrían no viajar | anotar sus valores ANTES (Settings → Secrets and variables → Actions → Variables) |
| políticas de Actions de la organización | si la organización sólo permite ciertas acciones o desactiva Actions, los flujos no arrancan | en la organización: Settings → Actions → General → «Allow all actions» (o al menos las de GitHub) |
| app del teléfono | usa `webmaletin-art/Cinema3DSHR`: funciona por la redirección; las escrituras (issues) también, pero conviene actualizar | cambiar `REPO` en la app y armar una APK nueva **después** de verificar todo (pide el token una vez) |
| nombre viejo | si alguien crea otro `webmaletin-art/Cinema3DSHR`, se cortan las redirecciones | no crear ni bifurcar con ese nombre |
| acceso de Claude | esta sesión trabaja sobre `webmaletin-art/Cinema3DSHR` | instalar la app de Claude en la organización con acceso a `Cinema3DSHR`; después agrego el repositorio movido a la sesión |
| reglas de la organización | reglas/rulesets de la organización podrían bloquear pushes a la rama | revisar Settings → Repository → Rulesets de la organización |

## 3. Procedimiento

Antes (vos, 5 minutos; nada se modifica):
1. Confirmar el plan: github.com/organizations/Cinema3DSHR/settings/billing → debe decir **Team**.
2. Confirmar tu rol: github.com/orgs/Cinema3DSHR/people → **Owner** (o permiso para crear repositorios).
3. Anotar los valores de las variables `*_REF` y `DIRECCION_RAMA` (si existen) y confirmar que tenés guardados los
   valores de `ASSETS_TOKEN` y `ANDROID_KEYSTORE_PASSWORD` por si hubiera que volver a cargarlos (no se regeneran).
4. En la organización: Actions habilitado y acciones de GitHub permitidas.
5. Que no esté corriendo ningún flujo (hoy no hay ninguno: la prueba de e01 se canceló).

Transferencia (sólo vos podés hacerla; requiere ser administrador del repositorio):
6. github.com/webmaletin-art/Cinema3DSHR/settings → Danger Zone → **Transfer** → organización `Cinema3DSHR`, mismo
   nombre. Queda `Cinema3DSHR/Cinema3DSHR`.
7. Instalar la app de Claude en la organización (github.com/apps/claude → Configure → Cinema3DSHR → acceso a
   `Cinema3DSHR`).

Verificación (yo, sin renders):
8. Agregar `Cinema3DSHR/Cinema3DSHR` a la sesión y cambiar el remoto de la copia local.
9. Comprobar ramas, commits, releases e issues contra la foto de la sección 5.
10. Correr «Verificar acceso» (`verificar-acceso.yml`): comprueba que `ASSETS_TOKEN` lee mixamo-respaldo y los otros
    repositorios de recursos. No renderiza nada.
11. Confirmar que las variables existen (o volver a cargarlas con los valores que anotaste).
12. Comprobar la concurrencia de la organización: sólo con tu autorización, la prueba de 60 trabajos de e01 (punto 4).

Después (con tu OK):
13. Actualizar `REPO` en `estudio/config.py` y en la app, y armar una APK nueva (el teléfono pide el token una vez).

## 4. Prueba de 60 trabajos con e01 (preparada, NO lanzada)

Flujo «Episodio · render distribuido», entradas: `produccion=p009_duo_cero`, `escenas=e01`, `trabajos=60`,
`prueba=0`. Reparte los 979 fotogramas de e01 sin modificar la escena (19 bloques de 17 y 41 de 16), con la
configuración verificada (960×540, Cycles CPU, 6 muestras, adaptativo 0,05, OIDN, 6 rebotes, Light Tree, semilla 0).
El informe dice cuántos trabajos corrieron a la vez: con Team deberían ser 60 (en la cuenta personal fueron 20).
Tiempo esperado con 60 a la vez: ~6–8 min de reloj [E]; con 20, ~20 min (medido en curso antes de cancelar).

## 5. Foto antes de transferir (17/11/2026, sin datos sensibles)

- Rama `ccr-6d21fe8a-76t9c3` (única y por defecto): último commit `11da973946e1`, 66 commits.
- Releases: 7 (las de arriba). Issues: 4, todos cerrados (#1–#4, etiqueta `revision`).
- Flujos: 11 activos (apk, catalogo, direccion, episodio, limpieza, pelicula, previa, render, revisiones,
  verificar-acceso, video30).
- Secretos usados (nombres): `ASSETS_TOKEN`, `ANDROID_KEYSTORE_PASSWORD`. Los valores de los secretos no los puede leer
  nadie (ni GitHub los muestra): no se anotan; si hiciera falta volver a cargarlos, los carga el dueño.
- Variables usadas (nombres): `MIXAMO_REF`, `NEXUS_REF`, `EXTRACTION_REF`, `RALLY_REF`, `DIRECCION_RAMA`.
- Corrida de prueba e01 de 60 trabajos (44076765471): cancelada; ningún flujo en curso.
