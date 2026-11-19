"""Loads the real WoundTrack pipeline once per process. NO streamlit here.

If the weights (or torch) are missing the UI falls back to demo mode and shows a banner, so the screens can still be
developed without the model files. Set WOUNDTRACK_REQUIRE_MODELS=1 in production to fail loudly instead.
"""
import logging
import os
import threading

log = logging.getLogger("woundtrack")
_LOCK = threading.Lock()
_STATE = {"tried": False, "service": None, "error": None}


def get_service():
    """The shared WoundTrackPipeline, or None if it could not be loaded (see service_error())."""
    with _LOCK:
        if not _STATE["tried"]:
            _STATE["tried"] = True
            try:
                from woundtrack import WoundTrackPipeline   # imports torch; kept lazy so demo mode needs no torch
                _STATE["service"] = WoundTrackPipeline()
            except Exception as e:                           # missing weights, missing torch, bad checkpoint...
                if os.environ.get("WOUNDTRACK_REQUIRE_MODELS") == "1":
                    raise
                _STATE["error"] = f"{type(e).__name__}: {e}"
                log.warning("Real models unavailable, using demo mode (%s)", _STATE["error"])
    return _STATE["service"]


def service_error():
    return _STATE["error"]
