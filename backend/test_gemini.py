import io
import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from fastapi import HTTPException

import gemini
import main


class GeminiConnectionTests(unittest.TestCase):
    config = {"GEMINI_API_KEY": "test-key-not-a-secret", "GEMINI_MODEL": "gemini-test"}

    def test_sends_a_text_request_and_returns_response_text(self):
        payload = {
            "candidates": [{
                "finishReason": "STOP",
                "content": {"parts": [
                    {"text": "Mensaje "},
                    {"thought": True, "text": "interno"},
                    {"text": "recibido."},
                ]},
            }]
        }
        with patch.object(gemini, "dotenv_values", return_value=self.config), patch.object(
            gemini, "urlopen", return_value=io.BytesIO(json.dumps(payload).encode())
        ) as urlopen:
            result = gemini.test_connection()

        request = urlopen.call_args.args[0]
        self.assertEqual(result, {"model": "gemini-test", "text": "Mensaje recibido."})
        self.assertEqual(request.method, "POST")
        self.assertEqual(request.full_url, "https://generativelanguage.googleapis.com/v1beta/models/gemini-test:generateContent")
        self.assertNotIn("test-key-not-a-secret", request.full_url)
        self.assertEqual(request.get_header("X-goog-api-key"), "test-key-not-a-secret")
        self.assertEqual(request.get_header("Content-type"), "application/json")
        self.assertEqual(json.loads(request.data), {"contents": [{"role": "user", "parts": [{"text": gemini.TEST_PROMPT}]}]})
        self.assertEqual(urlopen.call_args.kwargs["timeout"], 20)

    def test_rejects_missing_configuration_before_network(self):
        with patch.object(gemini, "dotenv_values", return_value={}), patch.object(
            gemini, "urlopen"
        ) as urlopen, self.assertRaises(gemini.GeminiError) as raised:
            gemini.test_connection()

        self.assertEqual(raised.exception.status_code, 503)
        urlopen.assert_not_called()

    def test_translates_network_and_api_errors_without_exposing_bodies(self):
        cases = [
            (HTTPError("https://example.invalid", 429, "rate", None, io.BytesIO(b"DUMMY_SECRET_MARKER")), 429),
            (HTTPError("https://example.invalid", 403, "forbidden", None, io.BytesIO(b"DUMMY_SECRET_MARKER")), 502),
            (HTTPError("https://example.invalid", 404, "not found", None, io.BytesIO(b"DUMMY_SECRET_MARKER")), 502),
            (TimeoutError(), 504),
            (URLError("network unavailable"), 502),
        ]
        for error, status in cases:
            with self.subTest(error=type(error).__name__), patch.object(
                gemini, "dotenv_values", return_value=self.config
            ), patch.object(gemini, "urlopen", side_effect=error), self.assertRaises(
                gemini.GeminiError
            ) as raised:
                gemini.test_connection()
            self.assertEqual(raised.exception.status_code, status)
            self.assertNotIn("DUMMY_SECRET_MARKER", str(raised.exception))

    def test_rejects_invalid_or_incomplete_responses(self):
        cases = [
            b"not json",
            json.dumps({"candidates": []}).encode(),
            json.dumps({"candidates": [{"finishReason": "SAFETY"}]}).encode(),
            json.dumps({"candidates": [{"finishReason": "STOP", "content": {}}]}).encode(),
            json.dumps({"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": "  "}]}}]}).encode(),
        ]
        for payload in cases:
            with self.subTest(payload=payload[:20]), patch.object(
                gemini, "dotenv_values", return_value=self.config
            ), patch.object(gemini, "urlopen", return_value=io.BytesIO(payload)), self.assertRaises(
                gemini.GeminiError
            ) as raised:
                gemini.test_connection()
            self.assertEqual(raised.exception.status_code, 502)


class GeminiEndpointTests(unittest.TestCase):
    def test_endpoint_maps_gemini_error_to_http_error(self):
        with patch.object(gemini, "test_connection", side_effect=gemini.GeminiError(503, "Missing config")), self.assertRaises(
            HTTPException
        ) as raised:
            main.test_gemini()

        self.assertEqual(raised.exception.status_code, 503)
        self.assertEqual(raised.exception.detail, "Missing config")


if __name__ == "__main__":
    unittest.main()
