"""The UI only calls run_models(). Everything model-related lives in this package."""
from backend.models.pipeline import get_pipeline


def run_models(img, date):
    return get_pipeline().run(img, date)
