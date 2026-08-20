from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class WebViewPolicy:
    allowed_origins: frozenset[str]
    allow_network: bool = False
    allow_native_bridge: bool = False
    max_execution_ms: int = 5_000
    require_csp: bool = True

    def admit_url(self, url: str) -> bool:
        parsed = urlparse(url)
        if parsed.scheme not in {"https", "app"}:
            return False
        origin = f"{parsed.scheme}://{parsed.netloc}" if parsed.netloc else "app://local"
        return origin in self.allowed_origins

    def validate_csp(self, csp: str | None) -> bool:
        if not self.require_csp:
            return True
        if not csp:
            return False
        normalized = " ".join(csp.lower().split())
        return "default-src 'none'" in normalized and "object-src 'none'" in normalized
