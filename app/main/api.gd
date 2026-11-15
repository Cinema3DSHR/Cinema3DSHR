class_name EstudioApi
extends Node
## Comunicación con el "servidor" del estudio (GitHub):
##  - LECTURA (sin cuenta): catálogo y entregables públicos en GitHub Releases.
##  - ESCRITURA (sólo el dueño): decisiones de revisión como Issues, con un token personal guardado cifrado
##    en el teléfono (nunca dentro de la APK ni del repositorio).
## Todo lo descargado queda en caché (user://cache) indexado por SHA-256: lo que no cambió no se vuelve a bajar
## y se puede ver sin conexión.

signal catalogo_listo(catalogo: Dictionary, desde_red: bool)
signal aviso(texto: String)
signal progreso(clave: String, fraccion: float)

const REPO := "webmaletin-art/Cinema3DSHR"
const URL_CATALOGO := "https://github.com/%s/releases/download/catalogo/catalogo.json"
const API := "https://api.github.com/repos/%s"
const CACHE := "user://cache"
const ARCH_TOKEN := "user://cuenta.dat"
const ARCH_PEND := "user://pendientes.json"
const ARCH_VISTOS := "user://vistos.json"
const ARCH_INDICE := "user://cache/indice.json"

var catalogo: Dictionary = {}
var _indice: Dictionary = {}       # url -> {"ruta", "sha256", "bytes"}
var _descargas: Dictionary = {}    # url -> HTTPRequest en curso
var _esperando: Dictionary = {}    # url -> Array[Callable]

func _ready() -> void:
	DirAccess.make_dir_recursive_absolute(CACHE)
	_indice = _leer(ARCH_INDICE)

# ------------------------------------------------------------------------------------------- archivos

func _leer(ruta: String) -> Dictionary:
	if not FileAccess.file_exists(ruta):
		return {}
	var d = JSON.parse_string(FileAccess.get_file_as_string(ruta))
	return d if d is Dictionary else {}

func _escribir(ruta: String, d) -> void:
	var f := FileAccess.open(ruta, FileAccess.WRITE)
	if f:
		f.store_string(JSON.stringify(d))
		f.close()

# ------------------------------------------------------------------------------------------- catálogo

func cargar_catalogo() -> void:
	var local := _leer(CACHE + "/catalogo.json")
	if not local.is_empty():
		catalogo = local
		catalogo_listo.emit(catalogo, false)
	var h := HTTPRequest.new()
	h.timeout = 15.0
	add_child(h)
	h.request_completed.connect(func(res, cod, _hd, cuerpo):
		h.queue_free()
		if res != HTTPRequest.RESULT_SUCCESS or cod != 200:
			aviso.emit("Sin conexión con el estudio: se muestra lo guardado." if not local.is_empty()
				else "No se pudo leer el catálogo (¿sin internet?).")
			return
		var d = JSON.parse_string(cuerpo.get_string_from_utf8())
		if not (d is Dictionary):
			aviso.emit("El catálogo recibido no es válido.")
			return
		catalogo = d
		_escribir(CACHE + "/catalogo.json", d)
		catalogo_listo.emit(catalogo, true)
		_reintentar_pendientes())
	h.request(URL_CATALOGO % REPO + "?t=%d" % Time.get_unix_time_from_system())

func produccion(pid: String) -> Dictionary:
	for p in catalogo.get("producciones", []):
		if p.get("id") == pid:
			return p
	return {}

# ------------------------------------------------------------------------------------------- descargas

## Devuelve la ruta local si el archivo ya está en caché y coincide su SHA-256; si no, "".
func en_cache(archivo: Dictionary) -> String:
	var url := str(archivo.get("url", ""))
	var e: Dictionary = _indice.get(url, {})
	if e.is_empty() or not FileAccess.file_exists(e.get("ruta", "")):
		return ""
	var sha := str(archivo.get("sha256", ""))
	if sha != "" and sha != str(e.get("sha256", "")):
		return ""
	return e["ruta"]

## Descarga (o toma de la caché) y llama a `listo.call(ruta)` (ruta = "" si falló).
func obtener(archivo: Dictionary, listo: Callable) -> void:
	var url := str(archivo.get("url", ""))
	if url == "":
		listo.call("")
		return
	var ya := en_cache(archivo)
	if ya != "":
		listo.call(ya)
		return
	if _esperando.has(url):
		_esperando[url].append(listo)
		return
	_esperando[url] = [listo]
	var nombre := url.get_file().uri_decode()
	var sub := url.get_base_dir().get_file()
	DirAccess.make_dir_recursive_absolute(CACHE + "/" + sub)
	var destino := CACHE + "/" + sub + "/" + nombre
	var h := HTTPRequest.new()
	h.download_file = destino + ".part"
	h.timeout = 0.0
	h.max_redirects = 10
	add_child(h)
	_descargas[url] = h
	h.request_completed.connect(func(res, cod, _hd, _b):
		_descargas.erase(url)
		h.queue_free()
		var ok: bool = res == HTTPRequest.RESULT_SUCCESS and cod == 200
		var sha_real := ""
		if ok:
			sha_real = FileAccess.get_sha256(destino + ".part")
			var esperado := str(archivo.get("sha256", ""))
			if esperado != "" and esperado != sha_real:
				ok = false
				aviso.emit("Descarga corrupta (SHA-256 distinto): " + nombre)
		if ok:
			DirAccess.remove_absolute(destino)
			DirAccess.rename_absolute(destino + ".part", destino)
			_indice[url] = {"ruta": destino, "sha256": sha_real, "bytes": int(archivo.get("bytes", 0))}
			_escribir(ARCH_INDICE, _indice)
		else:
			DirAccess.remove_absolute(destino + ".part")
			if res != HTTPRequest.RESULT_SUCCESS or cod != 200:
				aviso.emit("No se pudo descargar " + nombre + " (código %d)." % cod)
		for cb in _esperando.get(url, []):
			cb.call(destino if ok else "")
		_esperando.erase(url))
	h.request(url)

func fraccion(url: String) -> float:
	var h: HTTPRequest = _descargas.get(url)
	if h == null or h.get_body_size() <= 0:
		return -1.0
	return float(h.get_downloaded_bytes()) / h.get_body_size()

func bytes_cache() -> int:
	var total := 0
	for url in _indice:
		var r: String = _indice[url].get("ruta", "")
		if FileAccess.file_exists(r):
			var f := FileAccess.open(r, FileAccess.READ)
			if f:
				total += f.get_length()
	return total

func limpiar_cache() -> void:
	for url in _indice:
		DirAccess.remove_absolute(_indice[url].get("ruta", ""))
	_indice.clear()
	_escribir(ARCH_INDICE, _indice)

# ------------------------------------------------------------------------------------------- cuenta (token)

func _clave() -> String:
	return "cine3d|" + OS.get_unique_id() + "|" + REPO

func guardar_token(t: String) -> void:
	var f := FileAccess.open_encrypted_with_pass(ARCH_TOKEN, FileAccess.WRITE, _clave())
	if f:
		f.store_string(t.strip_edges())
		f.close()

func token() -> String:
	if not FileAccess.file_exists(ARCH_TOKEN):
		return ""
	var f := FileAccess.open_encrypted_with_pass(ARCH_TOKEN, FileAccess.READ, _clave())
	if f == null:
		return ""
	var t := f.get_as_text()
	f.close()
	return t

func borrar_token() -> void:
	DirAccess.remove_absolute(ARCH_TOKEN)

func tiene_token() -> bool:
	return token() != ""

func _cabeceras() -> PackedStringArray:
	return PackedStringArray(["Authorization: Bearer " + token(), "Accept: application/vnd.github+json",
		"X-GitHub-Api-Version: 2022-11-28", "User-Agent: 3DFilmStudio-Android", "Content-Type: application/json"])

## Comprueba que el token puede escribir Issues en el repositorio. listo.call(ok: bool, texto: String)
func probar_token(listo: Callable) -> void:
	var h := HTTPRequest.new()
	add_child(h)
	h.request_completed.connect(func(res, cod, _hd, cuerpo):
		h.queue_free()
		if res != HTTPRequest.RESULT_SUCCESS:
			listo.call(false, "Sin conexión.")
			return
		var d = JSON.parse_string(cuerpo.get_string_from_utf8())
		if cod == 200 and d is Dictionary:
			var p: Dictionary = d.get("permissions", {})
			listo.call(true, "Conectado a %s%s" % [REPO, "" if p.is_empty() else (" · permisos: " + ", ".join(p.keys().filter(func(k): return p[k])))])
		else:
			listo.call(false, "El token no tiene acceso (código %d)." % cod))
	h.request(API % REPO, _cabeceras())

# ------------------------------------------------------------------------------------------- revisiones

## decision: APROBAR | RECHAZAR | CORREGIR | RENDERIZAR | EXPORTAR
func enviar_revision(datos: Dictionary, listo: Callable) -> void:
	datos["app"] = str(ProjectSettings.get_setting("estudio/version", {}).get("app", 0))
	datos["enviado"] = Time.get_datetime_string_from_system(true) + "Z"
	if not tiene_token():
		listo.call(false, "Para aprobar o pedir cambios hay que vincular la cuenta en AJUSTES.")
		return
	_post_issue(datos, func(ok, texto):
		if not ok and texto.begins_with("Sin conexión"):
			var p := _leer(ARCH_PEND)
			var lista: Array = p.get("lista", [])
			lista.append(datos)
			_escribir(ARCH_PEND, {"lista": lista})
			listo.call(true, "Sin conexión: quedó guardado y se envía solo al volver la conexión.")
		else:
			listo.call(ok, texto))

func _post_issue(d: Dictionary, listo: Callable) -> void:
	var titulo := "[REVISIÓN] %s · %s v%d · %s" % [d.get("produccion", ""), d.get("escena", "-"), int(d.get("version", 0)), d.get("decision", "")]
	var cuerpo := "**%s** — %s %s v%d\n\n%s\n\n```json\n%s\n```\n\n_Enviado desde 3D Film Studio (Android)._" % [
		d.get("decision", ""), d.get("produccion", ""), d.get("escena", ""), int(d.get("version", 0)),
		str(d.get("nota", "")), JSON.stringify(d, "  ")]
	var h := HTTPRequest.new()
	add_child(h)
	h.request_completed.connect(func(res, cod, _hd, resp):
		h.queue_free()
		if res != HTTPRequest.RESULT_SUCCESS:
			listo.call(false, "Sin conexión.")
		elif cod == 201:
			var r = JSON.parse_string(resp.get_string_from_utf8())
			listo.call(true, "Enviado al estudio (pedido #%s)." % str(r.get("number", "?")) if r is Dictionary else "Enviado.")
		else:
			listo.call(false, "El estudio rechazó el pedido (código %d). Revisá el token en AJUSTES." % cod))
	h.request(API % REPO + "/issues", _cabeceras(), HTTPClient.METHOD_POST, JSON.stringify({"title": titulo, "body": cuerpo}))

# ------------------------------------------------------------------------------------------- dirección (EDITOR 3D)

## Envía al estudio datos de dirección: tipo = camara | guardar | nota | marcador.
## Se crea un Issue "[DIRECCIÓN] …" con el JSON; el flujo «Dirección desde el editor 3D» lo guarda en
## producciones/<produccion>/director/ y Claude lo aplica a la escena de producción.
func enviar_direccion(datos: Dictionary, listo: Callable) -> void:
	datos["clase"] = "direccion"
	datos["app"] = str(ProjectSettings.get_setting("estudio/version", {}).get("app", 0))
	datos["enviado"] = Time.get_datetime_string_from_system(true) + "Z"
	if not tiene_token():
		listo.call(false, "Para enviar al estudio hay que vincular la cuenta en AJUSTES (queda guardado en el teléfono).")
		return
	_post_direccion(datos, func(ok, texto):
		if not ok and texto.begins_with("Sin conexión"):
			var p := _leer(ARCH_PEND)
			var lista: Array = p.get("lista", [])
			lista.append(datos)
			_escribir(ARCH_PEND, {"lista": lista})
			listo.call(true, "Sin conexión: quedó guardado y se envía solo al volver la conexión.")
		else:
			listo.call(ok, texto))

func _post_direccion(d: Dictionary, listo: Callable) -> void:
	var tipo := str(d.get("tipo", "nota")).to_upper()
	var nombre := str(d.get("camara", {}).get("name", d.get("titulo", "")))
	var titulo := "[DIRECCIÓN] %s · %s v%d · %s%s" % [d.get("produccion", ""), d.get("escena", ""), int(d.get("version", 0)), tipo,
		(" · " + nombre) if nombre != "" else ""]
	var cuerpo := "%s\n\n```json\n%s\n```\n\n_Enviado desde el EDITOR 3D de 3D Film Studio._" % [str(d.get("texto", "")), JSON.stringify(d, "  ")]
	var h := HTTPRequest.new()
	add_child(h)
	h.request_completed.connect(func(res, cod, _hd, resp):
		h.queue_free()
		if res != HTTPRequest.RESULT_SUCCESS:
			listo.call(false, "Sin conexión.")
		elif cod == 201:
			var r = JSON.parse_string(resp.get_string_from_utf8())
			listo.call(true, "Enviado al estudio (#%s)." % str(r.get("number", "?")) if r is Dictionary else "Enviado.")
		else:
			listo.call(false, "El estudio rechazó el envío (código %d). Revisá el token en AJUSTES." % cod))
	h.request(API % REPO + "/issues", _cabeceras(), HTTPClient.METHOD_POST, JSON.stringify({"title": titulo, "body": cuerpo}))

## Historial de dirección de una producción: issues "[DIRECCIÓN] <pid> …" (abiertos = pendientes para Claude).
## listo.call(lista: Array) con {numero, titulo, estado, comentarios, fecha, cuerpo}
func historial_direccion(pid: String, listo: Callable) -> void:
	var h := HTTPRequest.new()
	add_child(h)
	h.request_completed.connect(func(res, cod, _hd, resp):
		h.queue_free()
		var out: Array = []
		if res == HTTPRequest.RESULT_SUCCESS and cod == 200:
			var r = JSON.parse_string(resp.get_string_from_utf8())
			if r is Array:
				for i in r:
					var t := str(i.get("title", ""))
					if t.begins_with("[DIRECCIÓN] " + pid) or t.begins_with("[REVISIÓN] " + pid):
						out.append({"numero": int(i.get("number", 0)), "titulo": t, "estado": str(i.get("state", "")),
							"comentarios": int(i.get("comments", 0)), "fecha": str(i.get("created_at", "")),
							"cuerpo": str(i.get("body", "")).get_slice("```", 0).strip_edges()})
		listo.call(out))
	var cab := _cabeceras() if tiene_token() else PackedStringArray(["Accept: application/vnd.github+json", "User-Agent: 3DFilmStudio-Android"])
	h.request(API % REPO + "/issues?state=all&per_page=60&sort=created&direction=desc", cab)

## Comentarios (respuestas del estudio) de un pedido. listo.call(lista: Array[{autor, fecha, texto}])
func comentarios(numero: int, listo: Callable) -> void:
	var h := HTTPRequest.new()
	add_child(h)
	h.request_completed.connect(func(res, cod, _hd, resp):
		h.queue_free()
		var out: Array = []
		if res == HTTPRequest.RESULT_SUCCESS and cod == 200:
			var r = JSON.parse_string(resp.get_string_from_utf8())
			if r is Array:
				for c in r:
					out.append({"autor": str(c.get("user", {}).get("login", "")), "fecha": str(c.get("created_at", "")),
						"texto": str(c.get("body", ""))})
		listo.call(out))
	var cab := _cabeceras() if tiene_token() else PackedStringArray(["Accept: application/vnd.github+json", "User-Agent: 3DFilmStudio-Android"])
	h.request(API % REPO + "/issues/%d/comments?per_page=50" % numero, cab)

func pendientes() -> int:
	return _leer(ARCH_PEND).get("lista", []).size()

func _reintentar_pendientes() -> void:
	var lista: Array = _leer(ARCH_PEND).get("lista", [])
	if lista.is_empty() or not tiene_token():
		return
	_escribir(ARCH_PEND, {"lista": []})
	for d in lista:
		var enviar: Callable = _post_direccion if str(d.get("clase", "")) == "direccion" else _post_issue
		enviar.call(d, func(ok, _t):
			if not ok:
				var p := _leer(ARCH_PEND)
				var l: Array = p.get("lista", [])
				l.append(d)
				_escribir(ARCH_PEND, {"lista": l}))

# ------------------------------------------------------------------------------------------- novedades

func clave_version(pid: String, eid: String, v: int) -> String:
	return "%s/%s/v%d" % [pid, eid, v]

func es_nuevo(clave: String) -> bool:
	return not _leer(ARCH_VISTOS).has(clave)

func marcar_visto(clave: String) -> void:
	var d := _leer(ARCH_VISTOS)
	d[clave] = Time.get_unix_time_from_system()
	_escribir(ARCH_VISTOS, d)
