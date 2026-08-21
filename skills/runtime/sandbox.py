from __future__ import annotations

import json
import multiprocessing as mp
from pathlib import Path, PurePosixPath
import queue
import shutil
import tempfile
import threading
from typing import Any, Callable
from urllib.parse import urlparse

from .errors import PolicyError, ReplayError, SandboxCrash, SandboxTimeout
from .types import SandboxExecutionRequest, SandboxExecutionResult, SandboxPolicy, SandboxState


def _origin(uri: str) -> str:
    parsed = urlparse(uri)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise PolicyError("invalid credential-free HTTPS origin")
    port = f":{parsed.port}" if parsed.port else ""
    return f"https://{parsed.hostname.casefold()}{port}"


def _canonical_json_bytes(value: Any, *, error: str) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise PolicyError(error) from exc


def _worker(
    executor: Callable[[dict[str, Any], str | None, Path], Any],
    payload: dict[str, Any],
    secret_handle: str | None,
    instance_dir: str,
    result_queue: Any,
) -> None:
    try:
        result = executor(payload, secret_handle, Path(instance_dir))
        result_queue.put(("ok", result))
    except BaseException as exc:  # process boundary
        result_queue.put(("error", type(exc).__name__))


class SandboxPolicyEngine:
    def __init__(self, policy: SandboxPolicy) -> None:
        if policy.max_input_bytes <= 0 or policy.max_output_bytes <= 0 or policy.timeout_ms <= 0:
            raise ValueError("sandbox budgets must be positive")
        self.policy = policy
        self.allowed_origins = frozenset(_origin(value) for value in policy.allowed_origins)
        self.allowed_network_origins = frozenset(_origin(value) for value in policy.allowed_network_origins)

    def admit(self, request: SandboxExecutionRequest) -> None:
        if _origin(request.skill_ref.source_uri) not in self.allowed_origins:
            raise PolicyError("unallowlisted skill origin")
        if request.skill_ref.trust_state.value != "TRUSTED":
            raise PolicyError("skill is not trusted")
        script = PurePosixPath(request.script_name)
        if script.is_absolute() or not request.script_name or any(part in {"", ".", ".."} for part in script.parts):
            raise PolicyError("invalid sandbox script path")
        if script.suffix.casefold() not in {".html", ".js", ".mjs"}:
            raise PolicyError("sandbox script type denied")
        requested_network = tuple(_origin(origin) for origin in request.requested_network_origins)
        if any(origin not in self.allowed_network_origins for origin in requested_network):
            raise PolicyError("network origin denied")
        if any(bridge not in self.policy.allowed_bridges for bridge in request.requested_bridges):
            raise PolicyError("native bridge denied")
        if request.request_storage and not self.policy.allow_storage:
            raise PolicyError("storage denied")
        if request.request_camera and not self.policy.allow_camera:
            raise PolicyError("camera denied")
        if request.request_microphone and not self.policy.allow_microphone:
            raise PolicyError("microphone denied")
        if self.policy.require_strict_csp:
            csp = request.csp.casefold().replace('"', "'")
            if "default-src 'none'" not in csp or "unsafe-eval" in csp or "*" in csp:
                raise PolicyError("strict CSP required")
        encoded = _canonical_json_bytes(request.payload, error="sandbox input is not canonical JSON")
        if len(encoded) > self.policy.max_input_bytes:
            raise PolicyError("sandbox input exceeds byte budget")
        if request.secret_handle and request.secret_handle in encoded.decode("utf-8", errors="ignore"):
            raise PolicyError("secret handle must not enter model-visible payload")


class SandboxRunner:
    def __init__(self, policy: SandboxPolicy, *, instance_root: Path | None = None) -> None:
        self.policy = policy
        self.engine = SandboxPolicyEngine(policy)
        self.instance_root = Path(instance_root) if instance_root else Path(tempfile.mkdtemp(prefix="ai-edge-sandbox-root-"))
        self.instance_root.mkdir(parents=True, exist_ok=True)
        self._seen: set[str] = set()
        self._lock = threading.RLock()

    def run(self, request: SandboxExecutionRequest, executor: Callable[[dict[str, Any], str | None, Path], Any]) -> SandboxExecutionResult:
        self.engine.admit(request)
        with self._lock:
            if request.execution_id in self._seen:
                raise ReplayError("sandbox execution replay")
            self._seen.add(request.execution_id)
        instance = Path(tempfile.mkdtemp(prefix="instance-", dir=self.instance_root))
        ctx = mp.get_context("spawn")
        result_queue = ctx.Queue(maxsize=1)
        process = ctx.Process(target=_worker, args=(executor, dict(request.payload), request.secret_handle, str(instance), result_queue))
        state = SandboxState.FAILED
        output: Any = None
        error_code: str | None = None
        try:
            try:
                process.start()
            except Exception as exc:  # unpicklable executor or process creation failure
                raise SandboxCrash(type(exc).__name__) from exc
            process.join(self.policy.timeout_ms / 1000)
            if process.is_alive():
                process.terminate()
                process.join(1)
                if process.is_alive():
                    process.kill()
                    process.join(1)
                raise SandboxTimeout("sandbox execution timed out")
            try:
                kind, value = result_queue.get(timeout=0.5)
            except queue.Empty as exc:
                raise SandboxCrash("sandbox exited without a typed result") from exc
            if kind != "ok":
                raise SandboxCrash(str(value))
            encoded = _canonical_json_bytes(value, error="sandbox output is not canonical JSON")
            if len(encoded) > self.policy.max_output_bytes:
                raise PolicyError("sandbox output exceeds byte budget")
            if request.secret_handle and request.secret_handle in encoded.decode("utf-8", errors="ignore"):
                raise PolicyError("secret handle echoed by sandbox")
            if not isinstance(value, dict) or ("result" in value) == ("error" in value):
                raise PolicyError("sandbox result must contain exactly one of result or error")
            if "error" in value:
                state, error_code = SandboxState.FAILED, "SKILL_ERROR"
            else:
                state, output = SandboxState.SUCCEEDED, value["result"]
        except SandboxTimeout:
            state, error_code = SandboxState.TIMED_OUT, "TIMEOUT"
        except (SandboxCrash, PolicyError) as exc:
            state, error_code = SandboxState.FAILED, type(exc).__name__
        finally:
            if process.is_alive():
                process.terminate()
                process.join(1)
            shutil.rmtree(instance, ignore_errors=True)
            result_queue.cancel_join_thread()
            result_queue.close()
        cleanup_complete = not instance.exists()
        return SandboxExecutionResult(
            execution_id=request.execution_id,
            skill_id=request.skill_ref.skill_id,
            source_sha256=request.skill_ref.source_sha256,
            state=state,
            output=output,
            error_code=error_code,
            cleanup_complete=cleanup_complete,
        )

    def close(self) -> None:
        shutil.rmtree(self.instance_root, ignore_errors=True)
