"""Frontend <-> backend integration tests, using RANDOM dummy weights (checks plumbing, not model quality).

    python tests/test_integration.py
"""
import sys
import tempfile
from datetime import date
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

import make_dummy_weights  # noqa: E402
from backend.twin_repository import TwinRepository  # noqa: E402
from woundtrack import PipelineConfig, WoundTrackPipeline  # noqa: E402

FAILS = []


def check(name, ok):
    print(("PASS" if ok else "FAIL"), "-", name)
    if not ok:
        FAILS.append(name)


def photo(seed, size=(240, 320)):
    return Image.fromarray((np.random.default_rng(seed).random((*size, 3)) * 255).astype(np.uint8))


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
    svc = WoundTrackPipeline(cfg)
    repo = TwinRepository(svc)

    # ---------------- patients
    check("empty database: no patients, 0 visits", repo.patients() == [] and repo.total_visits() == 0)
    dfu = repo.add_patient(dict(name="Priya Sharma", age=62, gender="Female", dx="DFU", full="DFU", loc="Right Foot", risk="High"))
    vlu = repo.add_patient(dict(name="Rajesh Kumar", age=58, gender="Male", dx="VLU", full="VLU", loc="Left Ankle", risk="Medium"))
    p = repo.patient(dfu)
    check("patient dict has the keys the pages use", all(k in p for k in ("id", "name", "age", "gender", "dx", "full", "loc", "risk")))
    check("DFU full name expanded", p["full"] == "Diabetic Foot Ulcer" and p["risk"] == "High" and p["loc"] == "Right Foot")
    check("ids are assigned in order", (dfu, vlu) == (1, 2))

    # ---------------- visits (DFU)
    i0, w0 = repo.add_visit_from_image(dfu, photo(1), date(2026, 10, 10), "first visit")
    i1, _ = repo.add_visit_from_image(dfu, photo(2), date(2026, 11, 10))
    check("visit indices are 0 then 1", (i0, i1) == (0, 1))
    vs = repo.visits(dfu)
    v = vs[1]
    need = ("date", "pct", "px", "gran", "fibrin", "callus", "grade", "conf", "img", "mask", "seg", "demo", "notes", "warnings")
    check("visit dict has every key the pages read", all(k in v for k in need))
    check("date is formatted like the UI expects", v["date"] == "10 Nov 2026" and vs[0]["notes"] == "first visit")
    check("day numbering: 31 days apart", [x["day"] for x in vs] == [1, 32])
    check("images are data URIs", all(v[k].startswith("data:image/png;base64,") for k in ("img", "mask", "seg")))
    check("DFU gets a grade 1-4 and a 0-100 confidence", v["grade"] in (1, 2, 3, 4) and 0 <= v["conf"] <= 100)
    check("tissue values are numbers", all(isinstance(v[k], float) for k in ("gran", "fibrin", "callus")))
    check("not marked as demo", v["demo"] == [])
    check("last_visit / total_visits", repo.last_visit(dfu) == "10 Nov 2026" and repo.total_visits() == 2)

    # ---------------- back-dated visit becomes first, existing days shift
    ib, _ = repo.add_visit_from_image(dfu, photo(3), date(2026, 10, 1))
    days = [x["day"] for x in repo.visits(dfu)]
    check("back-dated visit is index 0 and days shifted", ib == 0 and days == [1, 10, 41])
    check("dates still ordered", [x["date"] for x in repo.visits(dfu)] == ["01 Oct 2026", "10 Oct 2026", "10 Nov 2026"])

    # ---------------- same date twice is refused, nothing changes
    try:
        repo.add_visit_from_image(dfu, photo(4), date(2026, 10, 10))
        check("duplicate date refused", False)
    except ValueError as e:
        check("duplicate date refused with a readable message", "already has a visit" in str(e))
    check("refused duplicate left data intact", len(repo.visits(dfu)) == 3)

    # ---------------- non-DFU: severity not applicable
    repo.add_visit_from_image(vlu, photo(5), date(2026, 10, 12))
    iv, wv = repo.add_visit_from_image(vlu, photo(6), date(2026, 11, 20))
    vv = repo.visits(vlu)[iv]
    check("VLU: grade and conf are None", vv["grade"] is None and vv["conf"] is None)
    check("VLU: a 'severity not computed' warning is returned", any("Severity not computed" in w for w in wv))

    # ---------------- rule engine
    pr = repo.progression(dfu)
    check("progression returns summary/flags/rules", all(k in pr for k in ("summary", "flags", "rules")) and pr["is_dfu"] and pr["visit_count"] == 3)
    check("progress label is a string", isinstance(repo.progress_label(dfu), str))
    check("single-visit patient says not enough data", repo.progress_label(repo.add_patient(dict(name="N", age=40, gender="Male", dx="Other", full="Other", loc="-", risk="Low"))) == "Not enough data")
    check("VLU: DFU benchmark not applied", not repo.progression(vlu)["is_dfu"])

    # ---------------- missing image file does not crash and is not a fake wound
    import os
    os.remove(repo.visits(dfu)[0].get("img") and svc.history(dfu, conn=repo.conn)[0]["photo_path"])
    check("deleted photo gives a placeholder instead of an error", repo.visits(dfu)[0]["img"].startswith("data:image/png"))

    # ---------------- two sessions (two connections) see the same data
    repo2 = TwinRepository(svc)
    check("a second repository (second session) sees the same patients", [p["id"] for p in repo2.patients()] == [p["id"] for p in repo.patients()])

    # ---------------- an old database without the new columns is upgraded, not broken
    import sqlite3
    old = tmp / "old.db"
    c = sqlite3.connect(old)
    c.executescript("CREATE TABLE patient(patient_id INTEGER PRIMARY KEY, age REAL, sex TEXT, wound_aetiology TEXT);"
                    "CREATE TABLE visit(visit_id INTEGER PRIMARY KEY AUTOINCREMENT, patient_id INTEGER, day INTEGER, wound_area REAL,"
                    "granulation_pct REAL, fibrin_pct REAL, callus_pct REAL, severity_grade INTEGER, UNIQUE(patient_id, day));"
                    "INSERT INTO patient VALUES (9, 50, 'F', 'Diabetic foot ulcer'); INSERT INTO visit(patient_id, day, wound_area) VALUES (9, 1, 5.0);")
    c.commit(); c.close()
    from woundtrack import twin_db
    up = twin_db.connect(old)
    cols = {r[1] for r in up.execute("PRAGMA table_info(visit)")}
    check("old database is migrated in place", {"visit_date", "notes", "mask_path"} <= cols and up.execute("SELECT COUNT(*) FROM visit").fetchone()[0] == 1)

if FAILS:
    print(f"\n{len(FAILS)} FAILED")
    sys.exit(1)
print("\nAll integration tests passed")
