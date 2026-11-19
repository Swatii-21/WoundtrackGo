"""WoundTrack unified backend: boundary -> tissue -> severity -> digital twin -> rule engine.

Imports are lazy so that `woundtrack.twin_db` and `woundtrack.rules` (pure sqlite/pandas) work without torch.
"""
from __future__ import annotations

__all__ = ["WoundTrackPipeline", "PipelineConfig", "RULE_CONFIG"]


def __getattr__(name):
    if name == "WoundTrackPipeline":
        from .pipeline import WoundTrackPipeline
        return WoundTrackPipeline
    if name in ("PipelineConfig", "RULE_CONFIG"):
        from . import config
        return getattr(config, name)
    raise AttributeError(f"module 'woundtrack' has no attribute {name!r}")
