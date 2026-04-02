from __future__ import annotations

import json
import unittest
from io import BytesIO
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from src.perception.ocr_client import OCRServiceClient
from src.perception.ocr_models import OCRServiceConfig


class _FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


class OCRServiceClientTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.client = OCRServiceClient(
            OCRServiceConfig(
                enabled=True,
                base_url="http://127.0.0.1:18080",
                timeout_ms=1500,
            )
        )

    def test_read_text_returns_structured_success_result(self) -> None:
        payload = {
            "text": "第4回合",
            "confidence": 0.98,
            "provider": "paddle",
            "elapsed_ms": 128,
        }
        with patch("src.perception.ocr_client.urllib_request.urlopen", return_value=_FakeResponse(payload)):
            result = self.client.read_text("sample.png", allowlist="0123456789第回合", request_id="req-1")

        self.assertTrue(result.ok)
        self.assertEqual("第4回合", result.text)
        self.assertEqual(0.98, result.confidence)
        self.assertEqual("paddle", result.provider)
        self.assertEqual("req-1", result.request_id)
        self.assertEqual(200, result.http_status)
        self.assertEqual("http://127.0.0.1:18080/v1/ocr/read-text", result.endpoint)
        self.assertEqual("sample.png", result.request_payload["image_path"])
        self.assertIn("\\u7b2c4\\u56de\\u5408", result.raw_response or "")

    def test_read_lines_returns_structured_line_results(self) -> None:
        payload = {
            "lines": [
                {"text": "法术", "confidence": 0.91, "bounds": [1, 2, 30, 18]},
                {"text": "道具", "confidence": 0.88, "bounds": [31, 2, 60, 18]},
            ],
            "provider": "paddle",
            "elapsed_ms": 220,
        }
        with patch("src.perception.ocr_client.urllib_request.urlopen", return_value=_FakeResponse(payload)):
            result = self.client.read_lines("sample.png", request_id="req-2")

        self.assertTrue(result.ok)
        self.assertEqual("法术\n道具", result.merged_text)
        self.assertEqual((1, 2, 30, 18), result.lines[0].bounds)
        self.assertEqual("req-2", result.request_id)
        self.assertEqual(200, result.http_status)
        self.assertEqual("http://127.0.0.1:18080/v1/ocr/read-lines", result.endpoint)

    def test_http_error_is_mapped_to_structured_failure(self) -> None:
        http_error = HTTPError(
            url="http://127.0.0.1:18080/v1/ocr/read-text",
            code=502,
            msg="Bad Gateway",
            hdrs=None,
            fp=BytesIO(b'{"detail":"provider timeout"}'),
        )
        with patch("src.perception.ocr_client.urllib_request.urlopen", side_effect=http_error):
            result = self.client.read_text("sample.png")

        self.assertFalse(result.ok)
        self.assertEqual("ocr_failed", result.error_code)
        self.assertIn("provider timeout", result.error_detail or "")
        self.assertEqual(502, result.http_status)
        self.assertIn("provider timeout", result.raw_response or "")

    def test_connection_error_is_mapped_to_service_unavailable(self) -> None:
        with patch("src.perception.ocr_client.urllib_request.urlopen", side_effect=URLError("connection refused")):
            result = self.client.read_lines("sample.png")

        self.assertFalse(result.ok)
        self.assertEqual("service_unavailable", result.error_code)


if __name__ == "__main__":
    unittest.main()
