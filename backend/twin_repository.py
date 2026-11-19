"""Repository backed by the real digital twin + models. NO streamlit here.

Same methods as DemoRepository (patients, patient, add_patient, visits, total_visits, last_visit) plus
add_visit_from_image(), progression() and progress_label(). Each repository opens its OWN sqlite connection, so
Streamlit sessions (one thread each) never share one; the heavy models are shared through the service.

Visit dicts keep the keys the pages already use (date, pct, px, gran, grade, conf, img, mask, seg, demo) with two
deliberate changes: tissue keys are gran / fibrin / callus (the model predicts fibrin and callus, not slough and
necrotic), and grade / conf are None when severity does not apply (non-diabetic-foot wounds).
"""
import base64
import functools
import io
import os
from datetime import date, datetime

from PIL import Image

from woundtrack import twin_db

AETIOLOGY = {"DFU": "Diabetic foot ulcer", "VLU": "Venous ulcers", "Pressure Ulcer": "Pressure ulcers", "Other": "Other"}
FULL = {"DFU": "Diabetic Foot Ulcer", "VLU": "Venous Leg Ulcer", "Pressure Ulcer": "Pressure Ulcer", "Other": "Other"}
DISPLAY = (256, 256)
DATE_FMT = "%d %b %Y"


@functools.lru_cache(maxsize=512)
def _data_uri(path, mtime, nearest):
    """Stored picture -> small PNG data URI for the UI. Keyed by mtime so a replaced visit is re-read.
    A missing file gives a neutral grey tile, never a synthetic wound picture."""
    try:
        img = Image.open(path).convert("RGB")
    except (OSError, ValueError, TypeError):
        img = Image.new("RGB", DISPLAY, (225, 230, 232))
    img = img.resize(DISPLAY, Image.NEAREST if nearest else Image.BILINEAR)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _uri(path, nearest=False):
    if not path or not os.path.exists(path):
        return _data_uri("", 0, nearest)
    return _data_uri(path, os.stat(path).st_mtime_ns, nearest)


def _round(v, nd=1):
    return None if v is None else round(float(v), nd)


class TwinRepository:
    def __init__(self, service):
        self.svc = service
        self.conn = twin_db.connect(service.cfg.db_path)   # this session's own connection

    # ------------------------------------------------------------------ patients
    def _patient_dict(self, row):
        dx = row.get("diagnosis") or "Other"
        return dict(
            id=row["patient_id"], name=row.get("name") or f"Patient {row['patient_id']}", age=int(row["age"]) if row.get("age") is not None else "-",
            gender=row.get("sex") or "-", dx=dx, full=FULL.get(dx, dx), loc=row.get("wound_location") or "-",
            risk=row.get("risk_level") or "Unrated",
        )

    def patients(self):
        ids = [r[0] for r in self.conn.execute("SELECT patient_id FROM patient ORDER BY patient_id")]
        return [self._patient_dict(twin_db.get_patient(self.conn, i)) for i in ids]

    def patient(self, pid):
        row = twin_db.get_patient(self.conn, pid)
        if row is None:
            raise KeyError(f"No patient with id {pid}")
        return self._patient_dict(row)

    def add_patient(self, data):
        dx = data.get("dx", "Other")
        return twin_db.add_patient(
            self.conn, None, data.get("age"), data.get("gender"), AETIOLOGY.get(dx, dx),
            name=data.get("name"), wound_location=data.get("loc"), risk_level=data.get("risk"), diagnosis=dx,
        )

    # ------------------------------------------------------------------ visits
    def _visit_dict(self, r):
        iso = r.get("visit_date")
        detected = r.get("wound_detected") in (None, 1)
        conf = r.get("severity_conf")
        warnings = [] if detected else ["No wound was detected on this visit, so its area is excluded from the rule comparison."]
        return dict(
            visit_id=r["visit_id"], day=r["day"],
            date=datetime.strptime(iso, "%Y-%m-%d").strftime(DATE_FMT) if iso else f"Day {r['day']}",
            pct=_round(r.get("area_pct")) or 0.0, px=int(r.get("area_px") or 0),
            gran=_round(r.get("granulation_pct")) or 0.0, fibrin=_round(r.get("fibrin_pct")) or 0.0, callus=_round(r.get("callus_pct")) or 0.0,
            grade=r.get("severity_grade"), conf=None if conf is None else round(float(conf) * 100, 1),
            detected=detected, notes=r.get("notes") or "", warnings=warnings, demo=[],
            img=_uri(r.get("photo_path")), mask=_uri(r.get("mask_path"), True), seg=_uri(r.get("tissue_map_path"), True),
        )

    def visits(self, pid):
        return [self._visit_dict(r) for r in twin_db.history(self.conn, pid)]

    def total_visits(self):
        return self.conn.execute("SELECT COUNT(*) FROM visit").fetchone()[0]

    def last_visit(self, pid):
        vs = self.visits(pid)
        return vs[-1]["date"] if vs else "-"

    def add_visit_from_image(self, pid, image: Image.Image, visit_date, notes=None):
        """Run the three models on `image`, store the visit and return (index_of_new_visit, warnings).
        Raises ValueError if the patient already has a visit on that date."""
        import numpy as np

        p = self.patient(pid)
        out = self.svc.process_visit(
            np.asarray(image.convert("RGB")), pid, visit_date=visit_date, aetiology=AETIOLOGY.get(p["dx"], p["dx"]),
            notes=(notes or "").strip() or None, conn=self.conn,
        )
        idx = next(i for i, r in enumerate(twin_db.history(self.conn, pid)) if r["visit_id"] == out["visit_id"])
        return idx, out["analysis"]["warnings"]

    # ------------------------------------------------------------------ rule engine
    def progression(self, pid):
        return self.svc.get_progression(pid, conn=self.conn)

    def progress_label(self, pid):
        pr = self.progression(pid)
        if pr["status"] in ("insufficient_data", "single_visit"):
            return "Not enough data"
        if pr["status"] == "interval_too_short":
            return "Too early to judge"
        rule = next((r for r in pr["rules"] if r["rule"] == "overall_area_change"), {})
        return {"decreased": "Area decreasing ↗", "increased": "Area increasing ↘"}.get(rule.get("interpretation"), "No clear change")
