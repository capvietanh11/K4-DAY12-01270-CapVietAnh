"""CP1 - Structured logging."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone


def utc_now_iso() -> str:
    """Thoi diem hien tai theo ISO-8601, mui gio UTC."""
    return datetime.now(timezone.utc).isoformat()


def emit(event: str, severity: str = "INFO", **fields) -> str:
    """Ghi mot dong log JSON ra stdout va tra ve chuoi do."""
    payload = {
        "event": event,
        "severity": severity.upper(),
        "ts": utc_now_iso(),
        **fields,
    }
    line = json.dumps(payload, ensure_ascii=False)
    print(line, file=sys.stdout)
    return line
