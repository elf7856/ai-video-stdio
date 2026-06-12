"""Utilities for logging Google API errors without leaking credentials."""

import json
from typing import Any, Dict, Optional


_SENSITIVE_KEYWORDS = ("key", "token", "secret", "password", "credential", "authorization")


def _safe_value(value: Any, depth: int = 0) -> Any:
    if depth > 4:
        return str(value)[:500]

    if isinstance(value, dict):
        safe: Dict[str, Any] = {}
        for key, item in value.items():
            key_str = str(key)
            if any(part in key_str.lower() for part in _SENSITIVE_KEYWORDS):
                safe[key_str] = "[redacted]"
            else:
                safe[key_str] = _safe_value(item, depth + 1)
        return safe

    if isinstance(value, (list, tuple)):
        return [_safe_value(item, depth + 1) for item in value[:20]]

    if isinstance(value, (str, int, float, bool)) or value is None:
        return value

    return str(value)[:1000]


def format_google_api_error(exc: BaseException, context: Optional[Dict[str, Any]] = None) -> str:
    """Return a compact JSON error payload for quota/support debugging."""
    payload: Dict[str, Any] = {
        "error_type": exc.__class__.__name__,
        "message": str(exc),
    }
    if context:
        payload["context"] = _safe_value(context)

    for attr in ("code", "status", "reason"):
        if hasattr(exc, attr):
            payload[attr] = _safe_value(getattr(exc, attr))

    if getattr(exc, "args", None):
        payload["args"] = _safe_value(exc.args)

    details = getattr(exc, "details", None)
    if details:
        payload["details"] = _safe_value(details)

    response = getattr(exc, "response", None)
    if response is not None:
        payload["response"] = {
            "status_code": _safe_value(getattr(response, "status_code", None)),
            "headers": _safe_value(dict(getattr(response, "headers", {}) or {})),
        }
        text = getattr(response, "text", None)
        if text:
            payload["response"]["text"] = str(text)[:2000]

    return json.dumps(_safe_value(payload), ensure_ascii=False, default=str)
