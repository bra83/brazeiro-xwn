"""Minimal Android-facing entrypoint for embedding Barbara through a Python runtime.

The Kotlin/Java host only exchanges UTF-8 JSON strings with this module.  It does not
need to know Barbara's internal classes, which lets the motor evolve independently.
"""
from __future__ import annotations

from threading import RLock
from .bridge import HostBridge
from .engine import BarbaraEngine
from .gemini import GeminiProvider

_lock = RLock()
_bridge: HostBridge | None = None
_config: tuple | None = None


def configure(*, api_key=None, model='gemini-3.5-flash-lite', rag_db_path=None, use_gemini=True):
    """Configure one process-local Barbara bridge and return a small status dict.

    Android should call this once from Application startup (or lazily on first turn).
    Repeating the exact configuration is idempotent. Changing it rebuilds the bridge.
    """
    global _bridge, _config
    if not isinstance(use_gemini, bool):
        raise ValueError('invalid_use_gemini')
    if model is not None and (not isinstance(model, str) or not model.strip()):
        raise ValueError('invalid_model')
    if rag_db_path is not None and (not isinstance(rag_db_path, str) or not rag_db_path.strip()):
        raise ValueError('invalid_rag_db_path')
    cfg = (api_key, model, rag_db_path, use_gemini)
    with _lock:
        if _bridge is None or _config != cfg:
            provider = GeminiProvider(api_key=api_key, model=model) if use_gemini else None
            _bridge = HostBridge(BarbaraEngine(provider=provider, rag_db_path=rag_db_path))
            _config = cfg
    return {'configured': True, 'model': model if use_gemini else None, 'rag_persistent': rag_db_path is not None}


def reset_for_tests():
    global _bridge, _config
    with _lock:
        _bridge = None
        _config = None


def _require_bridge() -> HostBridge:
    with _lock:
        if _bridge is None:
            raise RuntimeError('barbara_android_not_configured')
        return _bridge


def new_campaign(campaign_id, system_id, **initial):
    return _require_bridge().new_campaign(campaign_id, system_id, **initial)


def turn(state_json, request_json):
    """Return a JSON string containing both updated state and turn result."""
    return _require_bridge().turn_json(state_json, request_json)
