from __future__ import annotations

import base64
import io
import json
import uuid
from pathlib import Path
from urllib import error as urllib_error
from urllib import request as urllib_request

from PIL import Image

from .ocr_models import OCRLineResult, OCRReadLinesResult, OCRReadTextResult, OCRServiceConfig


class OCRServiceClient:
    def __init__(self, config: OCRServiceConfig) -> None:
        self._config = config

    @property
    def config(self) -> OCRServiceConfig:
        return self._config

    def read_text(
        self,
        image_path: str | Path,
        *,
        allowlist: str | None = None,
        request_id: str | None = None,
    ) -> OCRReadTextResult:
        request_token = request_id or self._new_request_id()
        payload = self._build_payload(image_path=image_path, allowlist=allowlist)
        endpoint = f"{self._config.base_url.rstrip('/')}/v1/ocr/read-text"
        response = self._request_json(
            path="/v1/ocr/read-text",
            payload=payload,
            request_id=request_token,
        )
        if not response["ok"]:
            return OCRReadTextResult(
                ok=False,
                error_code=str(response["error_code"]),
                error_detail=str(response["error_detail"]),
                request_id=request_token,
                http_status=_optional_int(response.get("http_status")),
                endpoint=endpoint,
                request_payload=payload,
                raw_response=str(response.get("raw_response", "")),
            )

        body = response["body"]
        if not isinstance(body, dict):
            return OCRReadTextResult(
                ok=False,
                error_code="invalid_response",
                error_detail="response body is not a JSON object",
                request_id=request_token,
                http_status=_optional_int(response.get("http_status")),
                endpoint=endpoint,
                request_payload=payload,
                raw_response=str(response.get("raw_response", "")),
            )

        return OCRReadTextResult(
            ok=True,
            text=str(body.get("text", "")),
            confidence=float(body.get("confidence", 0.0)),
            provider=str(body.get("provider", "")),
            elapsed_ms=int(body.get("elapsed_ms", 0)),
            request_id=request_token,
            http_status=_optional_int(response.get("http_status")),
            endpoint=endpoint,
            request_payload=payload,
            raw_response=str(response.get("raw_response", "")),
        )

    def read_text_from_image(
        self,
        image: Image.Image,
        *,
        allowlist: str | None = None,
        request_id: str | None = None,
    ) -> OCRReadTextResult:
        request_token = request_id or self._new_request_id()
        payload = self._build_image_payload(image=image, allowlist=allowlist)
        endpoint = f"{self._config.base_url.rstrip('/')}/v1/ocr/read-text"
        response = self._request_json(
            path="/v1/ocr/read-text",
            payload=payload,
            request_id=request_token,
        )
        if not response["ok"]:
            return OCRReadTextResult(
                ok=False,
                error_code=str(response["error_code"]),
                error_detail=str(response["error_detail"]),
                request_id=request_token,
                http_status=_optional_int(response.get("http_status")),
                endpoint=endpoint,
                request_payload=payload,
                raw_response=str(response.get("raw_response", "")),
            )

        body = response["body"]
        if not isinstance(body, dict):
            return OCRReadTextResult(
                ok=False,
                error_code="invalid_response",
                error_detail="response body is not a JSON object",
                request_id=request_token,
                http_status=_optional_int(response.get("http_status")),
                endpoint=endpoint,
                request_payload=payload,
                raw_response=str(response.get("raw_response", "")),
            )

        return OCRReadTextResult(
            ok=True,
            text=str(body.get("text", "")),
            confidence=float(body.get("confidence", 0.0)),
            provider=str(body.get("provider", "")),
            elapsed_ms=int(body.get("elapsed_ms", 0)),
            request_id=request_token,
            http_status=_optional_int(response.get("http_status")),
            endpoint=endpoint,
            request_payload=payload,
            raw_response=str(response.get("raw_response", "")),
        )

    def read_lines(
        self,
        image_path: str | Path,
        *,
        allowlist: str | None = None,
        request_id: str | None = None,
    ) -> OCRReadLinesResult:
        request_token = request_id or self._new_request_id()
        payload = self._build_payload(image_path=image_path, allowlist=allowlist)
        endpoint = f"{self._config.base_url.rstrip('/')}/v1/ocr/read-lines"
        response = self._request_json(
            path="/v1/ocr/read-lines",
            payload=payload,
            request_id=request_token,
        )
        if not response["ok"]:
            return OCRReadLinesResult(
                ok=False,
                error_code=str(response["error_code"]),
                error_detail=str(response["error_detail"]),
                request_id=request_token,
                http_status=_optional_int(response.get("http_status")),
                endpoint=endpoint,
                request_payload=payload,
                raw_response=str(response.get("raw_response", "")),
            )

        body = response["body"]
        if not isinstance(body, dict):
            return OCRReadLinesResult(
                ok=False,
                error_code="invalid_response",
                error_detail="response body is not a JSON object",
                request_id=request_token,
                http_status=_optional_int(response.get("http_status")),
                endpoint=endpoint,
                request_payload=payload,
                raw_response=str(response.get("raw_response", "")),
            )

        lines_payload = body.get("lines", [])
        if not isinstance(lines_payload, list):
            return OCRReadLinesResult(
                ok=False,
                error_code="invalid_response",
                error_detail="lines field is not a list",
                request_id=request_token,
                http_status=_optional_int(response.get("http_status")),
                endpoint=endpoint,
                request_payload=payload,
                raw_response=str(response.get("raw_response", "")),
            )

        lines: list[OCRLineResult] = []
        for entry in lines_payload:
            if not isinstance(entry, dict):
                continue
            raw_bounds = entry.get("bounds")
            bounds = None
            if isinstance(raw_bounds, list) and len(raw_bounds) == 4:
                bounds = tuple(int(value) for value in raw_bounds)
            lines.append(
                OCRLineResult(
                    text=str(entry.get("text", "")),
                    confidence=float(entry.get("confidence", 0.0)),
                    bounds=bounds,
                )
            )

        return OCRReadLinesResult(
            ok=True,
            lines=tuple(lines),
            provider=str(body.get("provider", "")),
            elapsed_ms=int(body.get("elapsed_ms", 0)),
            request_id=request_token,
            http_status=_optional_int(response.get("http_status")),
            endpoint=endpoint,
            request_payload=payload,
            raw_response=str(response.get("raw_response", "")),
        )

    def _build_payload(self, *, image_path: str | Path, allowlist: str | None) -> dict[str, object]:
        payload: dict[str, object] = {
            "image_path": str(Path(image_path)),
            "profile": "default",
        }
        if allowlist:
            payload["allowlist"] = allowlist
        return payload

    def _build_image_payload(self, *, image: Image.Image, allowlist: str | None) -> dict[str, object]:
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        payload: dict[str, object] = {
            "image_base64": base64.b64encode(buffer.getvalue()).decode("ascii"),
            "profile": "default",
        }
        if allowlist:
            payload["allowlist"] = allowlist
        return payload

    def _request_json(self, *, path: str, payload: dict[str, object], request_id: str) -> dict[str, object]:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        endpoint = f"{self._config.base_url.rstrip('/')}{path}"
        request = urllib_request.Request(
            url=endpoint,
            data=body,
            headers={
                "Content-Type": "application/json",
                "X-Request-ID": request_id,
            },
            method="POST",
        )
        timeout_seconds = max(0.1, self._config.timeout_ms / 1000.0)
        try:
            with urllib_request.urlopen(request, timeout=timeout_seconds) as response:
                status_code = int(getattr(response, "status", 200))
                raw_body = response.read().decode("utf-8")
        except urllib_error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace") if exc.fp is not None else str(exc)
            return {
                "ok": False,
                "error_code": self._map_http_error(exc.code),
                "error_detail": detail,
                "http_status": int(exc.code),
                "raw_response": detail,
            }
        except (urllib_error.URLError, TimeoutError, OSError, ValueError) as exc:
            return {
                "ok": False,
                "error_code": "service_unavailable",
                "error_detail": str(exc),
                "http_status": None,
                "raw_response": None,
            }

        try:
            parsed = json.loads(raw_body)
        except json.JSONDecodeError:
            return {
                "ok": False,
                "error_code": "invalid_response",
                "error_detail": raw_body,
                "http_status": status_code,
                "raw_response": raw_body,
            }

        return {
            "ok": True,
            "http_status": status_code,
            "raw_response": raw_body,
            "body": parsed,
        }

    @staticmethod
    def _map_http_error(status_code: int) -> str:
        mapping = {
            400: "invalid_request",
            404: "missing_image",
            502: "ocr_failed",
            500: "service_error",
        }
        return mapping.get(int(status_code), "service_error")

    @staticmethod
    def _new_request_id() -> str:
        return f"dhxy2-automation-{uuid.uuid4().hex}"


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    return int(value)
