import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from dotenv import dotenv_values

ENV_PATH = Path(__file__).resolve().parent / ".env"
TEST_PROMPT = "Respondé con una sola frase corta en español confirmando que recibiste este mensaje."


class GeminiError(Exception):
    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code


def test_connection() -> dict[str, str]:
    config = dotenv_values(ENV_PATH)
    api_key = (config.get("GEMINI_API_KEY") or "").strip()
    model = (config.get("GEMINI_MODEL") or "").strip()
    if not api_key or not model:
        raise GeminiError(503, "Completá GEMINI_API_KEY y GEMINI_MODEL en backend/.env.")

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{quote(model, safe='')}:generateContent"
    )
    body = {"contents": [{"role": "user", "parts": [{"text": TEST_PROMPT}]}]}
    request = Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        method="POST",
    )
    try:
        with urlopen(request, timeout=20) as response:
            payload = json.load(response)
    except HTTPError as error:
        status = 429 if error.code == 429 else 502
        raise GeminiError(
            status,
            f"Gemini devolvió HTTP {error.code}. Revisá la clave, el modelo y la cuota del proyecto.",
        ) from None
    except TimeoutError:
        raise GeminiError(504, "Gemini no respondió dentro del tiempo de espera.") from None
    except URLError:
        raise GeminiError(502, "No se pudo conectar con Gemini. Revisá la conexión a Internet.") from None
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise GeminiError(502, "Gemini devolvió una respuesta JSON inválida.") from None

    try:
        candidate = payload["candidates"][0]
        if candidate.get("finishReason") != "STOP":
            raise GeminiError(502, "Gemini no devolvió una respuesta de texto completa.")
        text = "".join(
            part["text"] for part in candidate["content"]["parts"]
            if "text" in part and not part.get("thought", False)
        ).strip()
    except (KeyError, IndexError, TypeError, AttributeError):
        raise GeminiError(502, "Gemini no devolvió una respuesta de texto válida.") from None
    if not text:
        raise GeminiError(502, "Gemini no devolvió texto; la respuesta puede estar bloqueada.")
    return {"model": model, "text": text}
