# MiniDesk AI

Proyecto de aprendizaje: escribir solicitudes, analizarlas con IA y guardarlas en SQLite. En la etapa 1 solo preparamos Vue y una API con `GET /health`.

## Carpetas y archivos

- `frontend/`: proyecto del navegador. `package.json` declara dependencias y comandos; `package-lock.json` fija las versiones instaladas. `vite.config.ts` habilita Vue y `tsconfig.json` configura TypeScript.
- `frontend/src/`: código de la interfaz. `main.ts` crea la aplicación Vue y la monta en el elemento `#app` de `index.html`. `App.vue` contiene la pantalla inicial.
- `frontend/node_modules/`: dependencias descargadas por npm; no se guarda en Git.
- `frontend/dist/`: archivos generados por `npm.cmd run build`; tampoco se guardan en Git.
- `backend/`: código Python. `main.py` define la API y `requirements.txt` declara FastAPI y uvicorn.
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

## Verificaciones realizadas

- `npm.cmd install`: completado, con 45 paquetes instalados y `package-lock.json` generado.
- `npm.cmd run build`: pasó la comprobación de TypeScript y la compilación de Vite.
- Vite se inició temporalmente: `/`, `/src/main.ts` y `/src/App.vue` respondieron HTTP 200. Se comprobaron el título y los módulos transformados. El servidor de prueba se detuvo después.
- `git diff --check`: pasó. También se comprobó que Git ignora las dependencias, la compilación y los archivos `.env`.
- Backend pendiente de ejecución: no se encontró un intérprete Python utilizable en el PATH ni en las ubicaciones habituales revisadas. No se instalaron sus dependencias ni se comprobó `/health` por HTTP. Los pasos de arriba permiten hacerlo cuando Python esté disponible.
- No se hizo una prueba visual en un navegador.

## Límite de esta etapa

Solo se preparan los dos proyectos y `/health`. SQLite, Gemini, el formulario y la conexión entre frontend y backend corresponden a etapas posteriores.

**Pregunta conceptual:** ¿qué hace uvicorn y qué hace FastAPI cuando llega una petición a `/health`?

La etapa termina acá. Una respuesta a la pregunta no inicia la siguiente; para eso tenés que escribir **CONTINUAR**.
