"""Test the models WITHOUT the UI:  python scripts/test_models.py path/to/wound.jpg"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import Image
from backend.models.pipeline import get_pipeline

p = get_pipeline()
print("status:", p.status)
for k, e in p.errors.items(): print(f"  {k}: {e}")
r = p.run(Image.open(sys.argv[1]), "test")
print({k: v for k, v in r.items() if k not in ("img", "mask", "seg")})
print("stages using DEMO output:", r["demo"] or "none (all real models)")
