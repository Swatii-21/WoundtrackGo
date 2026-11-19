"""Demo fallback only. The real pipeline is woundtrack.WoundTrackPipeline, reached through backend.twin_repository."""
from backend.models import demo


def run_models(img, date):
    return demo.run(img, date)
