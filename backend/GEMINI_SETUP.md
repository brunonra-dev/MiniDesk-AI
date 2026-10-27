# Etapa 5: prueba mínima de Gemini

Esta prueba manda una frase fija desde FastAPI a Gemini. No lee, clasifica ni modifica solicitudes; tampoco guarda la respuesta en SQLite.

## 1. Conseguir la clave sin compartirla

1. Entrá a [Google AI Studio — API keys](https://aistudio.google.com/api-keys) con tu cuenta de Google.
2. Revisá el proyecto y su plan. Para esta etapa usá uno que figure como gratuito, sin activar facturación.
3. Pulsá **Create API key** y elegí ese proyecto. Las claves nuevas se crean mediante el mecanismo de autenticación actual de Google. Si falta permiso para crearla, elegí un proyecto propio que puedas administrar. Ver [guía oficial de claves](https://ai.google.dev/gemini-api/docs/api-key).
4. Copiá la clave directamente al archivo local `backend/.env`, en tu editor. No la pegues en el chat, en el frontend ni en un comando de terminal.

El archivo `.env` local ya está creado con valores vacíos. `.env.example` es la plantilla sin secretos que sí puede guardarse en Git. Si clonás el proyecto en otra computadora, desde `backend/` podés crear el archivo privado sin sobrescribir uno existente:

```powershell
if (!(Test-Path -LiteralPath .env)) { Copy-Item -LiteralPath .env.example -Destination .env }
```

## 2. Elegir el modelo gratuito de tu proyecto

Abrí [AI Studio — Rate limits](https://aistudio.google.com/rate-limit) y seleccioná el mismo proyecto donde creaste la clave. Confirmá el plan **Free** y buscá modelos de generación de texto con cuota mayor que cero. `RPM` son peticiones por minuto; `RPD`, peticiones por día. Copiá el identificador exacto de uno de esos modelos. Las cuotas pueden variar según el proyecto; la lista general de modelos no demuestra que puedas usarlos gratis. Consultá la [explicación de los límites](https://aistudio.google.com/docs/rate-limits) y compará con la [tabla oficial de precios](https://ai.google.dev/gemini-api/docs/pricing).

Completá las dos variables de `.env` en tu editor:

```dotenv
GEMINI_API_KEY=
GEMINI_MODEL=
```

Después de cada `=` va el valor correspondiente. En `GEMINI_MODEL` usá el ID, no el nombre de presentación, y sin el prefijo `models/`. No hay un modelo predeterminado ni un cambio automático a otro modelo. Debés elegir el que esté habilitado para tu cuenta.

Podés compartir el identificador del modelo para revisarlo, pero nunca la clave. La implementación no puede determinar por sí sola si tu proyecto tiene facturación o cuota gratuita: esa comprobación se hace en tu cuenta.

Para esta prueba se eligió `gemini-3.5-flash-lite`, confirmado en la [documentación del modelo](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite). Según la tabla de tu proyecto que compartiste, tiene límites de 15 peticiones por minuto, 250 000 tokens por minuto y 500 peticiones por día. Se configuró solamente `GEMINI_MODEL` en el `.env` privado; la clave existente quedó intacta.

Git ya ignora `.env`. Para comprobarlo desde la raíz sin mostrar su contenido:

```powershell
git check-ignore backend/.env
```

Debe imprimir `backend/.env`. No uses nombres `VITE_` para la clave: esas variables pertenecen al frontend y pueden terminar en los archivos que recibe el navegador.

## 3. Ejecutar la prueba desde FastAPI

Desde la raíz del proyecto:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Si el servidor ya está en ejecución, no inicies otro en el mismo puerto. Instalá primero la dependencia nueva, `python-dotenv`, y reiniciá el backend si no se recuperó automáticamente.

1. Abrí `http://127.0.0.1:8000/docs`.
2. Desplegá **POST /gemini/test**.
3. Pulsá **Try it out** y luego **Execute**. No lleva cuerpo JSON ni pide la clave.
4. Esperá la respuesta. Cada ejecución intenta hacer una llamada a Gemini y consume cuota si llega a procesarse; no hay reintentos automáticos.

Con configuración válida y cuota disponible, esperamos HTTP `200` y un JSON con esta forma:

```json
{
  "model": "el-identificador-que-configuraste",
  "text": "Una frase corta generada por Gemini."
}
```

Este ejemplo describe el formato; no es una respuesta real obtenida de tu cuenta. El texto puede variar entre ejecuciones. Si falta alguna variable, la API responde `503` sin contactar a Google.

## 4. La llamada HTTP y la autenticación

Hay dos peticiones distintas. Primero el navegador envía `POST /gemini/test` a nuestra API local. Después FastAPI actúa como cliente HTTP y hace un POST por HTTPS a Google:

```text
https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent
```

En `backend/gemini.py`, `Request` construye la petición y `urlopen` la envía. Es el equivalente aproximado de crear opciones para `fetch` y ejecutarlo, pero acá ocurre en Python, dentro del backend. La ruta de FastAPI es una función síncrona; FastAPI la ejecuta en su grupo de hilos para no bloquear el bucle asíncrono principal mientras espera la red.

Los encabezados son:

- `Content-Type: application/json`: describe el formato del cuerpo.
- `x-goog-api-key`: contiene la clave leída de `.env`. Identifica el proyecto y permite a Google comprobar permisos y cuota. No la enviamos como parámetro de la URL ni la devolvemos al navegador.

El cuerpo contiene `contents`, una lista de mensajes. Cada mensaje tiene un rol y partes; nuestra única parte es texto:

```json
{
  "contents": [{
    "role": "user",
    "parts": [{
      "text": "Respondé con una sola frase corta en español confirmando que recibiste este mensaje."
    }]
  }]
}
```

`json.dumps(...)` convierte el diccionario Python en texto JSON, como `JSON.stringify` en TypeScript. `.encode("utf-8")` lo convierte en bytes, que son lo que se transmite por la red. HTTPS cifra el transporte. El protocolo y la estructura se documentan en la [referencia de generateContent](https://ai.google.dev/api/generate-content) y la [autenticación de Gemini](https://ai.google.dev/api).

## 5. Cómo interpretamos el resultado

Google responde con un JSON que contiene `candidates`. Tomamos el primer candidato, comprobamos que terminó con `finishReason: "STOP"` y unimos sus partes de texto. Si hubiera partes marcadas como pensamiento interno, no se incluyen en la respuesta.

`json.load(response)` convierte los bytes JSON en valores Python, parecido a `await response.json()` en JavaScript. El endpoint devuelve solamente `model` y `text`; el modelo Pydantic `GeminiTestResult`, en `main.py`, define esa salida.

El recorrido completo es: `/docs` → FastAPI → lectura privada de `.env` → POST HTTPS a Gemini → JSON de Google → extracción de texto → JSON local → `/docs`. SQLite no participa.

`dotenv_values` lee el archivo en cada prueba y devuelve un diccionario de configuración. Sus valores no se agregan a la respuesta ni se imprimen. Por eso podés corregir `.env` y volver a ejecutar la prueba sin depender de que el recargador detecte ese archivo.

## 6. Errores comunes

- **HTTP local 503, configuración incompleta:** falta la clave o el modelo en `backend/.env`. No se hizo una llamada externa.
- **Gemini HTTP 400:** puede haber una clave inválida, una petición incorrecta o falta de disponibilidad del nivel gratuito. Revisá el proyecto y el modelo en AI Studio. Nuestra API lo presenta como `502` e indica el código original.
- **Gemini HTTP 401 o 403:** revisá autenticación, permisos, restricciones de la clave y acceso del proyecto. Nuestra API devuelve `502` sin exponer el cuerpo de error de Google.
- **Gemini HTTP 404:** el identificador, la versión de API o el método no corresponde a un modelo accesible. Comprobá el ID exacto y que admita generación de texto. Nuestra API devuelve `502`.
- **HTTP 429:** se agotó una cuota o se enviaron demasiadas peticiones. Revisá los límites en AI Studio y esperá según corresponda; crear otra clave del mismo proyecto no implica otra cuota. Conservamos `429` en la respuesta local.
- **HTTP local 504:** se alcanzó el tiempo de espera de red configurado en 20 segundos.
- **HTTP local 502 por conexión:** revisá Internet, DNS o certificados. No deshabilites la verificación HTTPS.
- **Gemini HTTP 500 o 503:** puede ser un problema temporal del servicio; nuestra API responde `502`. Podés volver a probar más tarde.
- **HTTP local 502 por respuesta sin texto o incompleta:** puede haber bloqueo de contenido, interrupción o un formato inesperado. No lo presentamos como una generación exitosa.

Los errores de Google se traducen a mensajes controlados. No devolvemos sus cuerpos completos ni imprimimos excepciones con la clave. Ver la [guía oficial de errores](https://ai.google.dev/gemini-api/docs/troubleshooting).

## 7. Pruebas y estado actual

Desde `backend/`:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
```

Las once pruebas pasaron. Las nuevas pruebas usan claves ficticias claramente identificadas como datos de prueba y respuestas simuladas: no leen tu `.env`, no se conectan a Google y no consumen cuota. Comprueban autenticación por encabezado, el cuerpo HTTP, extracción del texto y los errores.

También se ejecutó uvicorn sobre una base temporal y se hicieron peticiones HTTP locales reales: configuración vacía → `503`; respuesta de Gemini simulada → `200` con `model` y `text`; ruta presente en OpenAPI y tickets sin cambios. En esa prueba no se leyó el `.env` privado ni se contactó a Google.

Se verificó que `backend/.env` está ignorado y no está seguido por Git. La revisión del código no encontró problemas. No se modificaron el frontend ni las operaciones de tickets.

Se hizo una llamada real a Gemini ejecutando directamente `main.test_gemini()`, la función utilizada por el endpoint. Usó la clave local sin mostrarla y el modelo `gemini-3.5-flash-lite`. La respuesta extraída fue `Mensaje recibido.`. La prueba no accedió a SQLite ni modificó tickets.

La conexión al servidor local del puerto 8000 agotó el tiempo de espera tanto para `/gemini/test` como para `/health`. Por eso esta llamada real se comprobó mediante la función, no desde `/docs`. No se reinició ni se detuvo el servidor existente. Para repetirla desde `/docs`, primero necesitás recuperar o reiniciar ese backend con el comando de la sección 3.

**Pregunta conceptual:** ¿por qué la clave se agrega en FastAPI y no en el `fetch` que ejecuta Vue?

Esta etapa se detiene acá. Si aparece un error al configurar o probar Gemini, lo corregimos dentro de esta misma etapa. Solo **CONTINUAR** autoriza pasar a la siguiente.
