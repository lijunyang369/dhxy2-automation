from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class OCRServiceConfig:
    enabled: bool = False
    base_url: str = "http://127.0.0.1:18080"
    timeout_ms: int = 1500


@dataclass(frozen=True)
class OCRLineResult:
    text: str
    confidence: float
    bounds: tuple[int, int, int, int] | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "text": self.text,
            "confidence": self.confidence,
            "bounds": list(self.bounds) if self.bounds is not None else None,
        }


@dataclass(frozen=True)
class OCRReadTextResult:
    ok: bool
    text: str = ""
    confidence: float = 0.0
    provider: str = ""
    elapsed_ms: int = 0
    error_code: str | None = None
    error_detail: str | None = None
    request_id: str | None = None
    http_status: int | None = None
    endpoint: str | None = None
    request_payload: dict[str, object] | None = None
    raw_response: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "text": self.text,
            "confidence": self.confidence,
            "provider": self.provider,
            "elapsed_ms": self.elapsed_ms,
            "error_code": self.error_code,
            "error_detail": self.error_detail,
            "request_id": self.request_id,
            "http_status": self.http_status,
            "endpoint": self.endpoint,
            "request_payload": dict(self.request_payload or {}),
            "raw_response": self.raw_response,
        }


@dataclass(frozen=True)
class OCRReadLinesResult:
    ok: bool
    lines: tuple[OCRLineResult, ...] = ()
    provider: str = ""
    elapsed_ms: int = 0
    error_code: str | None = None
    error_detail: str | None = None
    request_id: str | None = None
    http_status: int | None = None
    endpoint: str | None = None
    request_payload: dict[str, object] | None = None
    raw_response: str | None = None
    merged_text: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "merged_text", "\n".join(line.text for line in self.lines if line.text.strip()))

    def to_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "lines": [line.to_dict() for line in self.lines],
            "merged_text": self.merged_text,
            "provider": self.provider,
            "elapsed_ms": self.elapsed_ms,
            "error_code": self.error_code,
            "error_detail": self.error_detail,
            "request_id": self.request_id,
            "http_status": self.http_status,
            "endpoint": self.endpoint,
            "request_payload": dict(self.request_payload or {}),
            "raw_response": self.raw_response,
        }
