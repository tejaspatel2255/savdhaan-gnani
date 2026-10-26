"""Error classes and HTTP status mapping for Gnani API calls."""

from typing import Any, Dict, Optional


class GnaniError(Exception):
    """Base exception for Gnani API interactions and Savdhaan quota/connection errors."""

    def __init__(
        self,
        message: str,
        code: str,
        status: Optional[int] = None,
        recoverable: bool = False,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status = status
        self.recoverable = recoverable

    @classmethod
    def from_http(cls, status: int, body: Any = None) -> "GnaniError":
        """Map an HTTP response status and optional body to a GnaniError instance.

        Codes strictly match docs/EVENTS.md:
        - 400 -> bad_request
        - 403 -> credits ('Forbidden: the API key, organisation status or credits may be the problem')
        - 429 -> rate_limited
        - 500, 503 -> network (recoverable)
        - anything else -> internal
        """
        err_msg = ""
        if isinstance(body, dict):
            error_obj = body.get("error", {})
            if isinstance(error_obj, dict):
                err_msg = error_obj.get("message", "")
            elif isinstance(error_obj, str):
                err_msg = error_obj
            if not err_msg:
                err_msg = body.get("message", "")
        elif isinstance(body, str):
            err_msg = body

        if status == 400:
            msg = err_msg or "Invalid request parameters"
            return cls(message=msg, code="bad_request", status=status, recoverable=False)

        if status == 403:
            return cls(
                message="Forbidden: the API key, organisation status or credits may be the problem",
                code="credits",
                status=status,
                recoverable=False,
            )

        if status == 429:
            msg = err_msg or "Rate limit exceeded"
            return cls(message=msg, code="rate_limited", status=status, recoverable=True)

        if status in (500, 503):
            msg = err_msg or f"Gnani server error ({status})"
            return cls(message=msg, code="network", status=status, recoverable=True)

        msg = err_msg or f"Unexpected HTTP status {status}"
        return cls(message=msg, code="internal", status=status, recoverable=False)

    def to_event(self) -> Dict[str, Any]:
        """Convert error to docs/EVENTS.md error payload."""
        return {
            "code": self.code,
            "message": self.message,
            "recoverable": self.recoverable,
        }
