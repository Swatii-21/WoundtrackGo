"""End-to-end plumbing test using RANDOM dummy weights (predictions are meaningless; this checks that every stage
loads, runs, chains, writes to the twin, and feeds the rule engine). Run: python tests/test_pipeline.py"""
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

import make_dummy_weights  # noqa: E402
from woundtrack import PipelineConfig, WoundTrackPipeline  # noqa: E402
from woundtrack.config import _default_boundary  # noqa: E402

FAILS = []


def check(name, ok):
    print(("PASS" if ok else "FAIL"), "-", name)
    if not ok:
        FAILS.append(name)


with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    make_dummy_weights.main(tmp / "w")
    cfg = PipelineConfig(
        device="cpu",
        boundary_models=[(tmp / "w/boundary/boundary_model_final_all46.pth", "resnet34")],
        tissue_models=sorted((tmp / "w/tissue").glob("*.pt")),
        severity_weights=tmp / "w/severity/severity_final.pt",
        severity_meta=tmp / "w/severity/severity_final_meta.json",
        db_path=tmp / "twin.db", image_store=tmp / "imgs",
    )
    pipe = WoundTrackPipeline(cfg)
    check("3 tissue ensemble members loaded (incl. a Part-1 style checkpoint)", len(pipe.tissue.members) == 3)

    rng = np.random.default_rng(0)
    img = (rng.random((240, 320, 3)) * 255).astype(np.uint8)       # WoundsDB-sized photo
    big = (rng.random((3000, 4000, 3)) * 255).astype(np.uint8)     # phone-sized photo (gets downscaled)

    a = pipe.analyse_image(img, "Diabetic foot")
    check("analyse_image returns wound/tissue/severity", a["severity"] is not None and "area_pct" in a["wound"])
    check("mask is original image size", a["masks"]["wound"].shape == (240, 320))
    check("overlays are same size as image", a["images"]["tissue_overlay"].shape == img.shape)
    tp = sum(a["tissue"][k] or 0 for k in ("fibrin_pct", "granulation_pct", "callus_pct"))
    check("tissue percentages sum to ~100", a["tissue"]["tissue_px"] == 0 or abs(tp - 100) < 0.1)
    check("severity grade in 1..4", a["severity"]["grade_num"] in (1, 2, 3, 4))

    n = pipe.analyse_image(img, "Venous ulcers")
    check("non-DFU: severity skipped with a warning", n["severity"] is None and any("Severity not computed" in w for w in n["warnings"]))
    check("big photo is downscaled", pipe.analyse_image(big, "Diabetic foot")["image_w"] == 1600)

    r1 = pipe.process_visit(img, 501, 1, aetiology="Diabetic foot", age=60, sex="M")
    check("first visit stored, single_visit status", r1["progression"]["status"] == "single_visit")
    r2 = pipe.process_visit(img, 501, 30, aetiology="Diabetic foot")
    check("second visit: rule engine ran over 2 visits", r2["progression"]["visit_count"] == 2 and r2["progression"]["is_dfu"])
    check("history returns 2 rows", len(pipe.history(501)) == 2)
    check("overlay images written to disk", Path(pipe.history(501)[0]["tissue_overlay_path"]).exists())

    try:
        pipe.process_visit(img, 501, 30, aetiology="Diabetic foot")
        check("duplicate day rejected", False)
    except ValueError:
        check("duplicate day rejected", True)
    pipe.process_visit(img, 501, 30, aetiology="Diabetic foot", replace_existing=True)
    check("replace_existing overwrites", len(pipe.history(501)) == 2)

    v = pipe.process_visit(img, 502, 1, aetiology="Venous ulcers")
    v = pipe.process_visit(img, 502, 40, aetiology="Venous ulcers")
    check("venous patient: severity not stored", all(h["severity_grade"] is None for h in pipe.history(502)))
    check("venous patient: DFU benchmark not applied", v["progression"]["benchmark_interpretation"] == "illustrative_only_no_validated_threshold"
          or v["progression"]["status"] in ("interval_too_short",))

    w = pipe.process_visit(img, 503, 1)  # aetiology unknown
    check("unknown aetiology: severity skipped", w["analysis"]["severity"] is None)

if FAILS:
    print(f"\n{len(FAILS)} FAILED")
    sys.exit(1)
print("\nAll pipeline tests passed")
