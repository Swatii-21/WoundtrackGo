"""Boots every Streamlit page with Streamlit's test harness (no browser). Real mode uses RANDOM dummy weights.

    python tests/test_ui.py
"""
import os
import sys
import tempfile
from datetime import date
from pathlib import Path

import numpy as np
from PIL import Image
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

import make_dummy_weights  # noqa: E402
from backend.twin_repository import TwinRepository  # noqa: E402
from woundtrack import PipelineConfig, WoundTrackPipeline  # noqa: E402

PAGES = ["Dashboard", "Add Patient", "Patient Profile", "Add New Visit", "AI Analysis", "Progression Tracking"]
FAILS = []


def check(name, ok):
    print(("PASS" if ok else "FAIL"), "-", name)
    if not ok:
        FAILS.append(name)


def run(page, repo=None, pid=1, visit=None):
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120)
    at.session_state["auth"] = True
    at.session_state["page"], at.session_state["pid"], at.session_state["visit"] = page, pid, visit
    if repo is not None:
        at.session_state["_repo"] = repo
    return at.run()


def texts(at):
    out = [m.value for m in at.markdown] + [i.value for i in at.info] + [w.value for w in at.warning] + [c.value for c in at.caption]
    return "\n".join(out)


def photo(seed):
    return Image.fromarray((np.random.default_rng(seed).random((240, 320, 3)) * 255).astype(np.uint8))


with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    make_dummy_weights.main(tmp / "w")
    cfg = PipelineConfig(
        device="cpu", boundary_models=[(tmp / "w/boundary/boundary_model_final_all46.pth", "resnet34")],
        tissue_models=sorted((tmp / "w/tissue").glob("*.pt")),
        severity_weights=tmp / "w/severity/severity_final.pt", severity_meta=tmp / "w/severity/severity_final_meta.json",
        db_path=tmp / "twin.db", image_store=tmp / "imgs",
    )
    svc = WoundTrackPipeline(cfg)

    # ---------------- real mode, empty database
    empty = TwinRepository(svc)
    for pg in ("Patient Profile", "Add New Visit", "AI Analysis", "Progression Tracking"):
        at = run(pg, empty)
        check(f"empty DB, {pg}: friendly message, no crash", not at.exception and "No patients yet" in texts(at))
    at = run("Dashboard", empty)
    check("empty DB, Dashboard renders", not at.exception)

    # ---------------- real mode, with data
    repo = TwinRepository(svc)
    dfu = repo.add_patient(dict(name="Priya Sharma", age=62, gender="Female", dx="DFU", full="DFU", loc="Right Foot", risk="High"))
    vlu = repo.add_patient(dict(name="Rajesh Kumar", age=58, gender="Male", dx="VLU", full="VLU", loc="Left Ankle", risk="Medium"))
    for i, d in enumerate([date(2026, 10, 1), date(2026, 10, 15), date(2026, 11, 5)]):
        repo.add_visit_from_image(dfu, photo(i), d)
    for i, d in enumerate([date(2026, 10, 3), date(2026, 11, 20)]):
        repo.add_visit_from_image(vlu, photo(10 + i), d)

    for pg in PAGES:
        at = run(pg, repo, pid=dfu)
        check(f"real mode, DFU patient, {pg}: renders without exception", not at.exception)
        check(f"real mode, {pg}: no demo banner", "DEMO MODE" not in texts(at))
    at = run("AI Analysis", repo, pid=dfu)
    t = texts(at)
    check("analysis (DFU): shows a grade and Fibrin/Callus, no Slough/Necrotic", "Grade" in t and "Fibrin" in t and "Callus" in t and "Slough" not in t and "Necrotic" not in t)
    at = run("AI Analysis", repo, pid=vlu)
    check("analysis (VLU): severity shown as not applicable", "Not applicable" in texts(at))
    at = run("Progression Tracking", repo, pid=dfu)
    check("progression (DFU): rule-engine summary shown", "Progression Summary" in texts(at) and "wound area" in texts(at).lower())
    at = run("Progression Tracking", repo, pid=vlu)
    check("progression (VLU): renders, severity chart replaced by a note", not at.exception and "only available for diabetic foot ulcers" in texts(at))
    at = run("Patient Profile", repo, pid=dfu)
    check("profile: Overall Progress comes from the rule engine", not at.exception and any(s in texts(at) for s in ("Area decreasing", "Area increasing", "No clear change", "Too early", "Not enough data")))
    at = run("AI Analysis", repo, pid=dfu, visit=0)
    check("analysis: opening a specific visit index works", not at.exception and "Visit 1" in texts(at))

    # ---------------- demo mode (no weights in ./weights)
    for pg in PAGES:
        at = run(pg, None, pid=1)
        check(f"demo mode, {pg}: renders without exception", not at.exception)
    at = run("Dashboard", None)
    check("demo mode: DEMO MODE banner is shown", "DEMO MODE" in texts(at))

if FAILS:
    print(f"\n{len(FAILS)} FAILED")
    sys.exit(1)
print("\nAll UI tests passed")
