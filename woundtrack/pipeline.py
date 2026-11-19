"""The unified WoundTrack pipeline.

    image -> Model 1 (wound boundary, area)
          -> Model 2 (tissue ensemble: fibrin / granulation / callus %)
          -> Model 3 (severity grade, diabetic foot only)
          -> digital twin (one row per visit)
          -> rule engine (compares this visit with the patient's earlier visits)

Models are loaded once and are read-only at inference time, so one pipeline can be shared by many sessions.
Database access goes through a sqlite3 connection: pass `conn=` to use your own (e.g. one per Streamlit
session), otherwise the pipeline's own connection is used.

    pipe = WoundTrackPipeline()
    out = pipe.process_visit(image, patient_id=7, visit_date=date(2026, 11, 3), aetiology="Diabetic foot ulcer")
    out["analysis"]     # per-image results + overlays
    out["progression"]  # rule-engine output for this patient
"""
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import torch

from . import rules, twin_db
from .config import RULE_CONFIG, PipelineConfig
from .segmentation import BoundarySegmenter
from .severity import SeverityClassifier
from .tissue import TissueEnsemble
from .utils import boundary_overlay, load_rgb, save_rgb, tissue_color_map, tissue_overlay


def _as_date(value) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


class WoundTrackPipeline:
    def __init__(self, config: PipelineConfig | None = None, rule_config: dict | None = None):
        self.cfg = config or PipelineConfig()
        self.rule_cfg = rule_config or RULE_CONFIG
        if self.cfg.area_metric not in ("area_pct", "area_px"):
            raise ValueError("area_metric must be 'area_pct' or 'area_px'")

        dev = self.cfg.device
        self.device = torch.device("cuda" if (dev == "auto" and torch.cuda.is_available()) else ("cpu" if dev == "auto" else dev))

        c = self.cfg
        self.boundary = BoundarySegmenter(c.boundary_models, self.device, c.boundary_size, c.boundary_threshold, c.min_wound_px)
        self.tissue = TissueEnsemble(c.tissue_models, self.device, c.tissue_size, c.tissue_tta)
        self.severity = SeverityClassifier(c.severity_weights, c.severity_meta, self.device, c.severity_size, c.severity_low_conf)
        self.conn = twin_db.connect(c.db_path)

    # ------------------------------------------------------------------ stateless analysis
    def analyse_image(self, image, aetiology: str | None = None) -> dict:
        """Run the three models on one image. Nothing is written to the database."""
        rgb = load_rgb(image, self.cfg.max_input_side)
        warnings: list[str] = []

        # Model 1: boundary + area
        seg = self.boundary.predict(rgb)
        if not seg["detected"]:
            warnings.append(
                f"No wound detected (mask is {seg['area_px']} px, below the {self.cfg.min_wound_px} px minimum). "
                "Area is not stored for rule comparison on this visit."
            )

        # Model 2: tissue (whole image by default, exactly as trained)
        mask_for_tissue = seg["mask"] if self.cfg.tissue_restrict_to_mask else None
        tis = self.tissue.predict(rgb, wound_mask=mask_for_tissue)
        if tis["tissue_px"] == 0:
            warnings.append("No tissue pixels were predicted, so tissue percentages are empty.")

        # Model 3: severity, diabetic foot only
        is_dfu = rules._is_dfu(aetiology)
        if is_dfu:
            sev = self.severity.predict(rgb)
            if sev["low_confidence"]:
                warnings.append(f"Severity confidence is low ({sev['confidence']:.2f}). Treat the grade with caution.")
        else:
            sev = None
            warnings.append(
                "Severity not computed: the grading model applies to diabetic foot ulcers only."
                if aetiology else "Severity not computed: wound aetiology was not provided."
            )

        h, w = rgb.shape[:2]
        return {
            "image_h": h, "image_w": w,
            "wound": {k: seg[k] for k in ("area_px", "area_frac", "max_prob", "detected")}
                     | {"area_pct": round(seg["area_frac"] * 100.0, 3)},
            "tissue": {k: tis[k] for k in ("tissue_px", "fibrin_pct", "granulation_pct", "callus_pct")},
            "severity": sev,
            "warnings": warnings,
            "images": {
                "original": rgb,
                "boundary_overlay": boundary_overlay(rgb, seg["mask"]),
                "tissue_overlay": tissue_overlay(rgb, tis["label_map"]),
                "tissue_map": tissue_color_map(tis["label_map"]),
                "mask": (seg["mask"] * 255).astype("uint8"),
            },
            "masks": {"wound": seg["mask"], "tissue_labels": tis["label_map"]},
        }

    # ------------------------------------------------------------------ day numbering
    @staticmethod
    def resolve_day(conn, patient_id: int, day: int | None, visit_date) -> tuple[int, int, str | None]:
        """Work out (day, shift, iso_date) for a new visit WITHOUT writing anything.

        `day` counts from the patient's first visit (first = day 1). When a calendar `visit_date` is given instead,
        the day is derived from it. If the date is earlier than the patient's first visit, every existing visit is
        shifted forward by `shift` days so that the new visit becomes day 1.
        """
        if visit_date is None:
            if day is None:
                raise ValueError("Give either `day` or `visit_date`")
            return int(day), 0, None
        d = _as_date(visit_date)
        dated = twin_db.dated_visits(conn, patient_id)
        if not dated:
            if twin_db.history(conn, patient_id):
                raise ValueError("This patient has visits without calendar dates; give `day` explicitly.")
            return 1, 0, d.isoformat()
        first_day, first_iso = dated[0]
        first_date = date.fromisoformat(first_iso)
        if d >= first_date:
            return first_day + (d - first_date).days, 0, d.isoformat()
        shift = (first_date - d).days
        return first_day, shift, d.isoformat()  # existing visits move up by `shift`; the new one takes the old first day

    # ------------------------------------------------------------------ full visit flow
    def process_visit(
        self, image, patient_id: int, day: int | None = None, aetiology: str | None = None, age: float | None = None,
        sex: str | None = None, duration_months: float | None = None, treatment_technique: str | None = None,
        replace_existing: bool = False, save_images: bool = True, visit_date=None, notes: str | None = None,
        conn=None,
    ) -> dict:
        """Analyse an image, store it as a visit in the digital twin, and run the rules for this patient.

        Give `day` (days since the first visit, first = 1) or a calendar `visit_date`.
        """
        conn = conn or self.conn
        patient_id = int(patient_id)
        day, shift, iso_date = self.resolve_day(conn, patient_id, day, visit_date)

        # A back-dated visit (shift > 0) lands before every existing visit, so it can never duplicate one.
        existing = None if shift else twin_db.visit_exists(conn, patient_id, day)
        if existing and not replace_existing:
            raise ValueError(f"Patient {patient_id} already has a visit on day {day}. Use replace_existing=True to overwrite it.")

        # The patient table stores ONE aetiology per patient (first visit wins). Use the stored one if present.
        stored = conn.execute("SELECT wound_aetiology FROM patient WHERE patient_id = ?", (patient_id,)).fetchone()
        effective_aetiology = (stored[0] if stored and stored[0] else None) or aetiology

        analysis = self.analyse_image(image, effective_aetiology)  # run models BEFORE touching the DB

        # Scale caution: same camera distance is assumed between visits.
        prev = [p for p in twin_db.history(conn, patient_id) if p["day"] != day]
        if prev and prev[-1]["image_h"] and (prev[-1]["image_h"], prev[-1]["image_w"]) != (analysis["image_h"], analysis["image_w"]):
            analysis["warnings"].append(
                "Image size differs from the previous visit. Area is compared as a % of the image, which is only "
                "valid if the camera distance was similar."
            )

        twin_db.ensure_patient(conn, patient_id, age, sex, aetiology)
        if existing:
            twin_db.delete_visit(conn, existing)
        if shift:
            twin_db.shift_days(conn, patient_id, shift)

        paths = {}
        if save_images:
            base = Path(self.cfg.image_store) / f"patient_{patient_id}" / f"{iso_date or f'day_{day}'}"
            im = analysis["images"]
            paths = {
                "photo_path": save_rgb(base / "photo.jpg", im["original"]),
                "boundary_overlay_path": save_rgb(base / "boundary_overlay.jpg", im["boundary_overlay"]),
                "tissue_overlay_path": save_rgb(base / "tissue_overlay.jpg", im["tissue_overlay"]),
                "tissue_map_path": save_rgb(base / "tissue_map.png", im["tissue_map"]),
                "mask_path": save_rgb(base / "mask.png", im["mask"][..., None].repeat(3, -1)),
            }

        wd, ts, sv = analysis["wound"], analysis["tissue"], analysis["severity"]
        area_value = (wd["area_pct"] if self.cfg.area_metric == "area_pct" else wd["area_px"]) if wd["detected"] else None
        visit_id = twin_db.add_visit(
            conn, patient_id, day,
            duration_months=duration_months, treatment_technique=treatment_technique, visit_date=iso_date, notes=notes,
            wound_area=area_value, area_px=wd["area_px"], area_pct=wd["area_pct"],
            image_h=analysis["image_h"], image_w=analysis["image_w"], wound_detected=int(wd["detected"]),
            granulation_pct=ts["granulation_pct"], fibrin_pct=ts["fibrin_pct"], callus_pct=ts["callus_pct"],
            severity_grade=sv["grade_num"] if sv else None, severity_conf=sv["confidence"] if sv else None,
            **{k: v for k, v in paths.items() if k in twin_db.VISIT_FIELDS},
        )

        return {
            "patient_id": patient_id, "day": day, "visit_id": visit_id, "visit_date": iso_date,
            "aetiology_used": effective_aetiology,
            "analysis": analysis,
            "progression": self.get_progression(patient_id, conn=conn),
        }

    # ------------------------------------------------------------------ twin access
    def get_progression(self, patient_id: int, conn=None) -> dict:
        return rules.analyse_patient_progression(conn or self.conn, int(patient_id), self.rule_cfg)

    def history(self, patient_id: int, conn=None) -> list[dict]:
        return twin_db.history(conn or self.conn, int(patient_id))

    def patients(self, conn=None):
        return twin_db.list_patients(conn or self.conn)
