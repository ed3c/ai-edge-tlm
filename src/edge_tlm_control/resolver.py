from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping

CONTEXT_ID = "CDX-AI-EDGE-001"
RESOLVER_KEYS = ("CODEXDOC_CONTROL_PLANE_URI", "CODEXDOC_LEDGER_URI")


@dataclass(frozen=True)
class ResolverPresence:
    context_id: str
    state: str
    present_keys: tuple[str, ...]
    missing_keys: tuple[str, ...]
    carrier_required: bool = True

    def as_public_dict(self) -> dict[str, object]:
        return {
            "context_id": self.context_id,
            "state": self.state,
            "present_keys": list(self.present_keys),
            "missing_keys": list(self.missing_keys),
            "carrier_required": self.carrier_required,
        }


def inspect_resolver_presence(env: Mapping[str, str] | None = None) -> ResolverPresence:
    source = os.environ if env is None else env
    present = tuple(key for key in RESOLVER_KEYS if bool(source.get(key)))
    missing = tuple(key for key in RESOLVER_KEYS if key not in present)
    if not present:
        state = "ABSENT"
    elif missing:
        state = "PARTIAL"
    else:
        state = "READY_FOR_SIGNED_IN_CARRIER"
    return ResolverPresence(CONTEXT_ID, state, present, missing)
