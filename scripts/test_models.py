"""Test the real models WITHOUT the UI (nothing is saved):

    python scripts/test_models.py path/to/wound.jpg [aetiology]

aetiology defaults to "Diabetic foot ulcer" (severity only runs for those); e.g. pass "Venous ulcers" to skip it.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from woundtrack import WoundTrackPipeline

pipe = WoundTrackPipeline()
a = pipe.analyse_image(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "Diabetic foot ulcer")
print("wound   :", a["wound"])
print("tissue  :", a["tissue"])
print("severity:", a["severity"])
for w in a["warnings"]:
    print("warning :", w)
