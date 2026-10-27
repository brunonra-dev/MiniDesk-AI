# MiniDesk AI

Proyecto de aprendizaje: escribir solicitudes, analizarlas con IA y guardarlas en SQLite. La etapa 1 preparó Vue y `GET /health`; la etapa 2 agregó SQLite. La etapa 3 permite crear y listar tickets mediante HTTP.

## Carpetas y archivos

- `frontend/`: proyecto del navegador. `package.json` declara dependencias y comandos; `package-lock.json` fija las versiones instaladas. `vite.config.ts` habilita Vue y `tsconfig.json` configura TypeScript.
- `frontend/src/`: código de la interfaz. `main.ts` crea la aplicación Vue y la monta en el elemento `#app` de `index.html`. `App.vue` contiene la pantalla inicial.
- `frontend/node_modules/`: dependencias descargadas por npm; no se guarda en Git.
- `frontend/dist/`: archivos generados por `npm.cmd run build`; tampoco se guardan en Git.
- `backend/`: código Python. `main.py` define la API y los modelos Pydantic; `database.py` inicializa SQLite, guarda y lista tickets. `requirements.txt` declara FastAPI y uvicorn. `test_database.py` y `test_tickets.py` verifican la base y la validación con `unittest`, incluido en Python.
- `backend/minidesk.db`: archivo de la base SQLite, generado localmente y excluido de Git junto con sus archivos auxiliares.
- `backend/.venv/`: entorno virtual que se crea al instalar el backend. Aísla sus paquetes de otros proyectos, de forma parecida a tener dependencias locales en `node_modules`.
- `backend/__pycache__/`: caché que Python puede generar al importar módulos; se excluye de Git.
- `.gitignore`: evita incluir dependencias, archivos generados y secretos en Git. Los archivos `.env` están excluidos. Esta etapa no necesita variables de entorno ni claves.

## Ejecutar los servidores en Windows / PowerShell

Requisitos: Node.js compatible con Vite (20.19+ o 22.12+) y Python 3.10 o posterior. Los comandos parten de la raíz del repositorio, en dos terminales distintas. El requisito de Node está documentado en la [guía oficial de Vite](https://vite.dev/guide/).

**Terminal 1: frontend**

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

Abrí la dirección que imprime Vite, normalmente `http://localhost:5173`. Usamos `npm.cmd` para evitar el bloqueo de `npm.ps1` por la política de PowerShell.

**Terminal 2: backend**

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Si Windows reconoce `py` en lugar de `python`, usá `py -3 -m venv .venv` en el primer comando de Python. Después se usa directamente el ejecutable del entorno; no hace falta activarlo ni cambiar la política de PowerShell.

`-m` ejecuta un módulo de Python con el intérprete elegido. Así pip y uvicorn usan las dependencias de este entorno.

Detené cada servidor con `Ctrl+C` en su terminal.

## FastAPI, uvicorn y el recorrido de los datos

FastAPI es un framework para construir APIs en Python. Una API expone direcciones que otros programas pueden consultar mediante HTTP. Un endpoint combina un método, como `GET`, con una ruta, como `/health`.

Uvicorn es el servidor: escucha las conexiones HTTP y se comunica con FastAPI mediante el protocolo ASGI. FastAPI decide qué función debe atender cada petición. `main:app` significa «importá el archivo `main.py` y usá su objeto `app`». `--reload` reinicia el servidor cuando cambia el código; sirve durante el desarrollo. Ver la [documentación oficial de FastAPI sobre el servidor](https://fastapi.tiangolo.com/deployment/manually/).

En `backend/main.py`:

```python
from fastapi import FastAPI

app = FastAPI(title="MiniDesk AI")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

- `from ... import ...` importa una clase, similar a un `import` de TypeScript.
- `app = FastAPI(...)` crea la aplicación.
- `@app.get("/health")` es un decorador: registra la función que aparece debajo para las peticiones `GET /health`.
- `def` declara una función. La sangría delimita su cuerpo en lugar de las llaves de TypeScript.
- `-> dict[str, str]` indica que devuelve un diccionario con claves y valores de texto, parecido a `Record<string, string>`. Es una anotación de tipos, no una conversión.
- `{"status": "ok"}` es un diccionario Python. FastAPI lo convierte en una respuesta JSON.

Cuando abrís `http://127.0.0.1:8000/health`, el navegador envía una petición `GET`. Uvicorn la recibe, FastAPI llama a `health()` y devuelve HTTP `200 OK` con `{"status":"ok"}`. `GET` se usa para consultar información. Este endpoint solo confirma que la aplicación responde.

El frontend tiene un recorrido separado: Vite sirve `index.html` y transforma los archivos TypeScript y Vue para que el navegador pueda ejecutarlos. `main.ts` monta `App.vue`, que muestra el título. Todavía no hace peticiones al backend.

## Comprobación manual

1. Abrí la URL de Vite: debe aparecer **MiniDesk AI** con el texto de inicio.
2. Con uvicorn en ejecución, abrí `http://127.0.0.1:8000/health`: debe aparecer `{"status":"ok"}`.
3. También podés comprobar la respuesta en otra terminal:

```powershell
Invoke-WebRequest http://127.0.0.1:8000/health | Select-Object StatusCode, Content
```

El resultado esperado es código `200` y el JSON anterior. Es una expectativa para tu prueba, no evidencia de que se haya ejecutado.

4. Abrí `http://127.0.0.1:8000/docs`: FastAPI genera una página donde podés desplegar `GET /health`, pulsar **Try it out** y luego **Execute**.
5. Para comprobar tipos y generar el frontend, desde `frontend/`:

```powershell
npm.cmd run build
```

## Verificaciones realizadas en la etapa 1

- `npm.cmd install`: completado, con 45 paquetes instalados y `package-lock.json` generado.
- `npm.cmd run build`: pasó la comprobación de TypeScript y la compilación de Vite.
- Vite se inició temporalmente: `/`, `/src/main.ts` y `/src/App.vue` respondieron HTTP 200. Se comprobaron el título y los módulos transformados. El servidor de prueba se detuvo después.
- `git diff --check`: pasó. También se comprobó que Git ignora las dependencias, la compilación y los archivos `.env`.
- Backend pendiente de ejecución: no se encontró un intérprete Python utilizable en el PATH ni en las ubicaciones habituales revisadas. No se instalaron sus dependencias ni se comprobó `/health` por HTTP. Los pasos de arriba permiten hacerlo cuando Python esté disponible.
- No se hizo una prueba visual en un navegador.

## Etapa 2: SQLite y la tabla tickets

### Recorrido de inicio

Uvicorn carga `main:app`. Antes de atender peticiones, FastAPI ejecuta la función `lifespan` de `backend/main.py`. Allí se llama a `init_db()` de `backend/database.py`: abre la base, crea la tabla si falta, confirma la operación y cierra la conexión. Si la inicialización falla, el arranque también falla y el error queda visible.

`@asynccontextmanager` permite definir las tareas de inicio y cierre de la aplicación. Lo que está antes de `yield` se ejecuta al iniciar; FastAPI funciona mientras ese contexto está abierto. `async def` declara una función asíncrona, un concepto relacionado con las funciones `async` de TypeScript. La pequeña inicialización SQLite de esta etapa es síncrona.

### Cómo se crea el archivo .db

En `database.py`, `Path(__file__).resolve().parent / "minidesk.db"` construye una ruta absoluta junto a ese archivo Python. `__file__` indica el archivo del módulo y `/` une partes de una ruta cuando usamos `Path`; acá no es una división.

`sqlite3.connect(DB_PATH)` abre una conexión y crea el archivo si no existe. No necesitás instalar SQLite con pip ni levantar otro servidor. El archivo almacena tanto la estructura como los datos. Ver la [documentación de sqlite3 de Python](https://docs.python.org/3/library/sqlite3.html).

`connection.execute(...)` envía una instrucción SQL. `commit()` confirma los cambios pendientes. `with closing(...)` garantiza que la conexión se cierre al salir, incluso si ocurre un error. Se usa porque `with sqlite3.connect(...)` por sí solo controla la transacción, pero no cierra la conexión.

El bloque `if __name__ == "__main__"` permite ejecutar `database.py` directamente para inicializar la base. No se ejecuta cuando `main.py` importa el módulo.

### CREATE TABLE, tipos y clave primaria

Esta es la instrucción que ejecuta `init_db()`:

```sql
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY,
    description TEXT NOT NULL,
    category TEXT,
    priority TEXT,
    summary TEXT
);
```

- `CREATE TABLE` crea la estructura de una tabla. Cada fila representará un ticket; cada columna, uno de sus campos.
- `IF NOT EXISTS` evita un error si la tabla ya existe. Permite reiniciar sin borrar filas. No modifica una tabla existente si más adelante cambiamos esta definición.
- `INTEGER` representa enteros; `TEXT` representa texto. La prioridad será texto, por ejemplo `alta`, cuando implementemos su asignación.
- `PRIMARY KEY` identifica cada fila de forma única. En SQLite, con esta declaración exacta `INTEGER PRIMARY KEY`, omitir `id` al insertar permite que SQLite genere un entero. No necesitamos `AUTOINCREMENT`; los identificadores borrados podrían reutilizarse.
- `NOT NULL` exige que `description` tenga un valor. No impide una cadena vacía: esa validación corresponderá a la entrada de solicitudes.
- Las otras tres columnas permiten `NULL`, que representa la ausencia de un valor. Es parecido a `null` en TypeScript; no es lo mismo que una cadena vacía.

La tabla define cómo se guardan los datos. Se parece a describir campos con un tipo de TypeScript, pero las restricciones de la base se aplican cuando ejecutamos SQL, no solo durante una comprobación de tipos.

SQLite usa tipado flexible por defecto: declarar `TEXT` o `INTEGER` establece una afinidad de tipo, no las mismas reglas estrictas de TypeScript ni de otros motores. La clave primaria entera y `NOT NULL` sí tienen las restricciones descritas. Ver [tipos de SQLite](https://www.sqlite.org/datatype3.html) y [CREATE TABLE](https://www.sqlite.org/lang_createtable.html).

### SQLite, SQL y otros motores

SQL es el lenguaje: `CREATE TABLE`, `SELECT` e `INSERT` son instrucciones SQL. SQLite es un motor que interpreta ese lenguaje. Python es quien le envía esas instrucciones mediante `sqlite3`.

SQLite guarda la base en un archivo y trabaja dentro del proceso Python. Otros motores que también usan SQL, como PostgreSQL o MySQL, normalmente requieren un servidor aparte. Comparten muchas instrucciones, pero tienen diferencias en tipos, generación de identificadores y otras características; no todo SQL es intercambiable entre motores.

### Crear y consultar manualmente

Desde `backend/`, con el entorno preparado como en la etapa 1:

```powershell
.\.venv\Scripts\python.exe database.py
```

Debe imprimir la ruta de `minidesk.db`. También se inicializa automáticamente al arrancar uvicorn con el comando habitual.

Para consultar sin agregar un endpoint ni instalar herramientas, abrí el intérprete:

```powershell
.\.venv\Scripts\python.exe
```

Pegá estas líneas Python, una por vez:

```python
import sqlite3
from database import DB_PATH
connection = sqlite3.connect(DB_PATH.as_uri() + "?mode=ro", uri=True)
print(connection.execute("PRAGMA table_info(tickets)").fetchall())
print(connection.execute("SELECT id, description, category, priority, summary FROM tickets").fetchall())
connection.close()
exit()
```

`mode=ro` abre la base en modo de solo lectura: si todavía no existe, falla en vez de crear accidentalmente un archivo vacío. `PRAGMA table_info(tickets)` muestra sus columnas; es una instrucción específica de SQLite. `SELECT` consulta las columnas indicadas y `fetchall()` recoge las filas como una lista de tuplas Python. Una tupla agrupa valores por posición, comparable a una tupla de TypeScript.

La primera consulta debe mostrar las cinco columnas. La segunda debe devolver `[]` en una base recién creada: la tabla existe, pero todavía no insertamos tickets.

Para repetir las pruebas automáticas, desde `backend/`:

```powershell
.\.venv\Scripts\python.exe -m unittest -v test_database
```

La prueba usa una base temporal: comprueba la estructura, el identificador generado, el rechazo de una descripción `NULL` y que una segunda inicialización conserve los datos. Sus filas de prueba no se guardan en `minidesk.db`.

### Verificaciones realizadas en la etapa 2

- Se encontró Python 3.15.2 y se creó `backend/.venv/`. FastAPI y uvicorn se instalaron allí; la limitación de ejecución de la etapa 1 quedó resuelta.
- Se ejecutó `database.py`: generó `backend/minidesk.db` mediante el módulo nativo `sqlite3`.
- `python -m unittest -v test_database`: una prueba pasó. Comprueba las columnas, la clave primaria, la generación del identificador, la descripción obligatoria y la conservación de filas al reinicializar.
- Se ejecutó el ciclo de inicio de FastAPI con una base temporal: creó el archivo y una tabla vacía correctamente.
- Se inició uvicorn temporalmente y `GET /health` respondió HTTP 200 con `{"status":"ok"}`. El servidor de prueba se detuvo.
- Se consultó la base real en modo de solo lectura: se encontraron las cinco columnas y cero filas, `[]`.
- `git diff --check` pasó. Git ignora la base, los archivos auxiliares y el entorno virtual.
- No se repitieron pruebas del frontend porque esta etapa no lo modifica.

## Etapa 3: crear y listar tickets por HTTP

### Métodos HTTP y códigos de respuesta

`GET /tickets` consulta los tickets guardados. No agrega filas y devuelve HTTP `200 OK` con un array JSON; si no hay tickets devuelve `[]`.

`POST /tickets` crea un ticket a partir del cuerpo JSON de la petición. Devuelve HTTP `201 Created` y el ticket guardado. Repetir un POST válido crea otra fila; repetir un GET solo vuelve a consultar.

`GET /health` sigue disponible. Esta etapa no agrega otros métodos HTTP.

### JSON y validación con Pydantic

La entrada de `POST /tickets` es:

```json
{"description": "No puedo acceder al correo"}
```

En `backend/main.py`, `TicketCreate` hereda de `BaseModel`, de Pydantic. Una clase agrupa datos y comportamiento; en Python, `class TicketCreate(BaseModel)` expresa herencia. El modelo define el contrato de entrada:

```python
class TicketCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    description: str = Field(min_length=1, max_length=5000)
```

`description` es obligatorio y debe ser texto. Se quitan los espacios de los extremos antes de comprobar la longitud: una descripción con solo espacios se rechaza. El texto resultante debe tener entre 1 y 5000 caracteres. `extra="forbid"` rechaza campos que no declaramos, como un `id` enviado por el cliente.

Se parece a definir un tipo de TypeScript, con una diferencia: Pydantic comprueba los datos durante la ejecución. Un tipo o interfaz de TypeScript por sí solo no valida el JSON que llega por la red. `Field` declara restricciones; no es una columna SQL. Ver [campos de modelos en FastAPI](https://fastapi.tiangolo.com/tutorial/body-fields/).

En la ruta, `ticket: TicketCreate` le indica a FastAPI que lea el cuerpo JSON y lo valide con ese modelo. Si falla, responde `422` con detalles del campo y no ejecuta la función que guarda el ticket.

```python
@app.post("/tickets", response_model=Ticket, status_code=201)
def create_ticket(ticket: TicketCreate):
    return database.create_ticket(ticket.description)
```

El modelo `Ticket` define la salida: `id`, `description`, `category`, `priority` y `summary`. Los últimos tres permiten `None` en Python, que se convierte en `null` en JSON. Todavía no hay análisis de IA. `response_model` también permite documentar y validar la forma de la respuesta.

### Cómo se guarda y se vuelve a leer

1. `/docs` o cualquier cliente envía un POST con `Content-Type: application/json` y el texto JSON en el cuerpo HTTP.
2. Uvicorn recibe la conexión. FastAPI interpreta el JSON y Pydantic construye `TicketCreate` si es válido.
3. La función de la ruta pasa `ticket.description` a `database.create_ticket()`.
4. Esa función abre una conexión SQLite y ejecuta el `INSERT` parametrizado. SQLite genera el `id`; las columnas no enviadas quedan en `NULL`.
5. Con `cursor.lastrowid`, obtiene el identificador generado y consulta esa fila. `commit()` confirma la escritura y la conexión se cierra al salir del bloque.
6. El diccionario Python pasa por el modelo de salida `Ticket` y FastAPI lo convierte en JSON con estado `201`.

La inserción en `backend/database.py` usa:

```python
cursor = connection.execute(
    "INSERT INTO tickets (description) VALUES (?)", (description,)
)
```

`?` marca el lugar de un valor. El valor se envía aparte, en una tupla Python; la coma de `(description,)` crea una tupla de un elemento. No se arma SQL concatenando el texto del usuario. Así una comilla o un texto como `'); DROP TABLE tickets; --` se trata como datos, sin ejecutarse como SQL. La búsqueda por el identificador también usa `WHERE id = ?`. Ver [parámetros de sqlite3](https://docs.python.org/3/library/sqlite3.html).

Para listar, `database.list_tickets()` ejecuta un `SELECT` con `ORDER BY id`, del identificador menor al mayor. Esta consulta es fija y no recibe valores externos, por eso no necesita parámetros. `sqlite3.Row` permite acceder a cada columna por su nombre y `dict(row)` convierte cada fila en un diccionario. FastAPI devuelve la lista como un array JSON.

### Probar desde /docs

Desde la raíz del proyecto:

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Abrí `http://127.0.0.1:8000/docs` y seguí estos pasos:

1. Desplegá **GET /tickets**, pulsá **Try it out** y **Execute**. Debe responder `200`; si no hay datos, verás `[]`.
2. Desplegá **POST /tickets**, pulsá **Try it out** y reemplazá el cuerpo por `{"description": "No puedo acceder al correo"}`. Pulsá **Execute**.
3. Debe responder `201` con esta forma; el `id` depende de los datos que ya tengas:

```json
{
  "id": 1,
  "description": "No puedo acceder al correo",
  "category": null,
  "priority": null,
  "summary": null
}
```

4. Ejecutá **GET /tickets** otra vez: el ticket debe aparecer en el array.
5. Probá POST con `{"description": "   "}` o `{}`: debe responder `422`. Repetí GET para comprobar que esas peticiones inválidas no agregaron filas.
6. Detené el servidor con `Ctrl+C`, volvé a iniciarlo y ejecutá GET: el ticket debe seguir guardado en `backend/minidesk.db`.

Estas pruebas manuales sí crean tickets en tu base local cuando enviás un POST válido. No hay un endpoint de borrado en esta etapa.

Para repetir las pruebas automáticas, desde `backend/`:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
```

### Verificaciones realizadas en la etapa 3

- `python -m unittest discover -v`: cuatro pruebas pasaron, incluyendo persistencia, estructura de tabla, validación y texto similar a una inyección SQL.
- Con uvicorn y una base temporal, `POST /tickets` respondió `201` y `GET /tickets` respondió `200`. Se comprobó el listado vacío y luego el orden de dos tickets.
- Siete cuerpos inválidos devolvieron `422` sin agregar filas: campo ausente, nulo, numérico, vacío, solo espacios, demasiado largo y con un campo extra.
- Se verificó el recorte de espacios, los tres campos de análisis en `null` y el almacenamiento literal de texto similar a SQL.
- Tras reiniciar el servidor de prueba, ambos tickets seguían guardados en la base temporal. `/health` respondió `200`.
- `/docs` y `/openapi.json` respondieron `200`; el esquema incluía ambos métodos de `/tickets`. No se hizo la interacción visual de botones en un navegador; los pasos manuales están indicados arriba.
- La revisión del código no encontró problemas. `git diff --check` pasó.
- Las verificaciones no insertaron datos en `backend/minidesk.db`. No se repitieron pruebas del frontend porque no se modificó.

### Límite de esta etapa

Se agregan solamente creación y listado por API, validación y SQL parametrizado. Gemini y la conexión del frontend siguen pendientes.

**Pregunta conceptual:** ¿por qué enviamos la descripción aparte del SQL, en lugar de concatenarla dentro del `INSERT`?

La etapa termina acá. Una respuesta a la pregunta no inicia la siguiente; para eso tenés que escribir **CONTINUAR**.
