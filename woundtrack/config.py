"""Central configuration. Every path and threshold lives here, nothing is hard-coded elsewhere."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
WEIGHTS_ROOT = Path(os.environ.get("WOUNDTRACK_WEIGHTS", PACKAGE_ROOT / "weights"))


def _default_boundary():
    # Default: the model trained on FUSeg + all labelled WoundsDB images (Model 1, notebook WOUNDTRACK_PRO).
    # To use the FUSeg-only model instead, point to final_boundary_model.pth.
    # To use the R34+R50 ensemble, list both: [(r34_path, "resnet34"), (r50_path, "resnet50")].
    return [(WEIGHTS_ROOT / "boundary" / "boundary_model_final_all46.pth", "resnet34")]


def _default_tissue():
    return sorted((WEIGHTS_ROOT / "tissue").glob("*.pt"))


@dataclass
class PipelineConfig:
    # ---- device ----
    device: str = "auto"  # "auto" | "cpu" | "cuda"

    # ---- input handling ----
    max_input_side: int = 1600  # larger photos are downscaled first (saves memory; area % is unaffected)

    # ---- Model 1: wound boundary ----
    boundary_models: list = field(default_factory=_default_boundary)  # [(checkpoint_path, encoder_name), ...]
    boundary_size: int = 512
    boundary_threshold: float = 0.5
    min_wound_px: int = 300  # below this the wound counts as "not detected" (value used in the Model 1 notebook)

    # ---- Model 2: tissue (ensemble of the top-3 models) ----
    tissue_models: list = field(default_factory=_default_tissue)
    tissue_size: int = 512
    tissue_tta: bool = False  # the validation winner in the notebook used no TTA
    # False = whole image, exactly as the tissue model was trained and evaluated.
    # True  = count tissue pixels only inside the Model 1 wound mask.
    tissue_restrict_to_mask: bool = False

    # ---- Model 3: severity (diabetic foot only) ----
    severity_weights: Path = WEIGHTS_ROOT / "severity" / "severity_final.pt"
    severity_meta: Path = WEIGHTS_ROOT / "severity" / "severity_final_meta.json"
    severity_size: int = 224
    severity_low_conf: float = 0.5  # below this the grade is flagged "low confidence"

    # ---- digital twin ----
    db_path: Path = PACKAGE_ROOT / "data" / "digital_twin.db"
    image_store: Path = PACKAGE_ROOT / "data" / "visit_images"

    # ---- which area number the rule engine compares across visits ----
    #   "area_pct": wound pixels as % of the image (robust to resolution; still needs the same camera distance)
    #   "area_px" : raw wound pixels (only valid when every photo has the same resolution AND distance)
    area_metric: str = "area_pct"


# Rule-engine thresholds, copied unchanged from WoundTrack_rule_engine_updated.ipynb (Nov 2026).
RULE_CONFIG = {
    "bench_par": 50,          # DFU only. Sheehan 2003: 50% area reduction at ~4 weeks
    "window": (21, 35),       # days after first visit that count as "about 4 weeks"
    "min_interval_days": 21,  # closer visits are too short to judge healing
    "area_tol": 5,            # % change smaller than this = no clear change (noise guard)
    "tissue_tol": 5,          # percentage-point change smaller than this = no clear change
    "sev_jump": 2,            # DFU only: change of this many grades or more counts; one grade = model noise
    "dfu_grade_note": 3,      # DFU only: note when latest grade is this or higher
}
