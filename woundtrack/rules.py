"""Rule engine: evidence-tagged, descriptive rules over a patient's visit history.

Ported UNCHANGED from WoundTrack_rule_engine_updated.ipynb (Nov 2026), cells 20-21. Only the CONFIG source
changed (it now lives in config.RULE_CONFIG). Do not edit thresholds here, edit them in config.py.

Evidence review (copied from the notebook):

    # Rule engine: evidence review and rules (updated Nov 2026)

    Every rule below is tagged with how well the literature supports it. Only rule 1 is a validated clinical benchmark. The rest are descriptive, and the code treats them that way.

    | # | Rule in the engine | Evidence status | Basis |
    |---|---|---|---|
    | 1 | **DFU only:** less than 50% area reduction after about 4 weeks flags a stalled wound for reassessment | **Supported** | Sheehan et al., Diabetes Care 2003;26(6):1879-82 (203 patients; midpoint between healers and non-healers was 53%; mean 4-week reduction 82% in healers vs 25% in non-healers). Post hoc analysis, Ostomy Wound Manage 2010;56(3):44-50 (PMID 20368673): with at least 50% reduction about 52 to 57% healed by week 12, with less than 50% only 2 to 5%. Single-centre cohort of 704 patients (PMID 18394932): 12-week healing 52.3% vs 18.4%. Used as a reassessment trigger in consensus guidance (Wound Healing Foundation consensus, PMC9305950). |
    | 2 | "Area is getting smaller" means improvement | **Not supported as a bare statement** | The evidence is for *percent* reduction against a threshold. In venous ulcers, absolute area change had no predictive value while percent change did (Kantor and Margolis, Br J Dermatol 2000;142:960-4). The engine therefore reports direction only as a description (5% tolerance) and never calls it healing on its own. |
    | 3 | Four-week benchmark for non-DFU wounds (venous, lymphatic, ischaemic, etc.) | **Not validated at 50%** | Four-week percent area reduction is also prognostic in venous leg ulcers (Kantor and Margolis 2000: AUC 0.75, PPV 68%, NPV 75%; Gelfand et al., J Invest Dermatol 2002, doi:10.1046/j.1523-1747.2002.19629.x), but the cut-points reported differ from 50%. The engine shows the 4-week change as **illustrative only** for non-DFU wounds and applies no threshold. No evidence was reviewed for lymphatic or ischaemic ulcers. |
    | 4 | Granulation up and fibrin (slough) down means a better wound bed | **Clinical teaching, weak as a quantitative predictor** | Wound-bed guidance describes more granulation and epithelial tissue with less slough as a healing bed (Wounds UK tissue-type guide). But in 31 pressure ulcers, granulation as a percentage of wound area showed no relationship with closure (Wyffels and Edsberg, Adv Skin Wound Care 2011;24(10)). The engine reports tissue direction only, with no cut-offs. The 5 percentage point tolerance is a noise guard, not a clinical value. |
    | 5 | Callus decreasing is favourable | **No source found** | Not verified in this review. Callus is reported for DFU only and is never used for a verdict. |
    | 6 | Higher severity grade means worse | **Supported for prognosis, not for tracking healing** | Higher Wagner grade is associated with higher amputation risk (for example, grades III to V carried 3.59 times the amputation risk of grades I and II in Praveena et al., Int Surg J 2018). Wagner grades depth, infection and gangrene, not healing progress, and the University of Texas system predicted outcome better in a head-to-head comparison (Diabetes Care 2001;24(1):84-8). A grade change between visits is therefore a flag, not a healing measure. |
    | 7 | Severity is computed for diabetic foot only | **Required** | Wagner-Meggitt is a diabetic foot system. Other etiologies are skipped. |

    **Engineering choices that are not clinical values:** the 21 to 35 day window, the 5% area tolerance, the 5 point tissue tolerance, "a change of 2 or more grades counts as a change" (one grade is treated as model noise, per Section 9.10 of the project context), and the grade 3 note.

    **Caveats that apply to every result:**
    - The 50% benchmark was derived under *standard of care* (offloading, debridement, infection control, perfusion). The database has no record of whether that was delivered.
    - Meeting 50% does not guarantee healing, and missing it is a prompt to reassess, not a diagnosis.
    - Percent area change from 2D photos is only valid if the pixel scale is the same at every visit (same camera distance, or a calibration reference, or the stereo/depth data). Check this before trusting any area number.
    - The patient table stores one etiology per patient (taken from the first visit). Case 5 has lymphatic and diabetic scenes, so it is treated as non-DFU here. Moving etiology to the visit table would fix this.
"""
from __future__ import annotations

from .config import RULE_CONFIG as CONFIG

import math
import pandas as pd

NUM_KEYS = ("day", "wound_area", "granulation_pct", "fibrin_pct", "callus_pct", "severity_grade")

def get_visits(conn, patient_id):
    cur = conn.execute(
        '''SELECT day, wound_area, granulation_pct, fibrin_pct, callus_pct, severity_grade
           FROM visit WHERE patient_id = ? ORDER BY day''', (patient_id,))
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]

def get_aetiology(conn, patient_id):
    r = conn.execute("SELECT wound_aetiology FROM patient WHERE patient_id = ?", (patient_id,)).fetchone()
    return r[0] if r else None

def _valid_number(value):
    try:
        return value is not None and not pd.isna(value) and math.isfinite(float(value))
    except (TypeError, ValueError):
        return False

def _number(value):
    return float(value) if _valid_number(value) else None

def _pct_area_reduction(baseline_area, later_area):
    # Positive = area got smaller; negative = area got larger.
    if baseline_area is None or later_area is None or baseline_area <= 0:
        return None
    return (baseline_area - later_area) / baseline_area * 100.0

def _direction(first, last, tolerance):
    if first is None or last is None:
        return "not available"
    delta = last - first
    if delta > tolerance:
        return "increased"
    if delta < -tolerance:
        return "decreased"
    return "showed no clear change"

def _is_dfu(aetiology):
    text = str(aetiology or "").strip().lower()
    return ("diabetic" in text and ("foot" in text or "ulcer" in text)) or text in {"dfu"}

def analyse_patient_progression(conn, patient_id, config=CONFIG):
    '''Rule-based description of one patient's wound progression. Not an outcome predictor.

    Per-visit inputs: wound_area, granulation_pct, fibrin_pct, callus_pct, severity_grade.
    `day` is days from the patient's first recorded visit.
    Area must be in the same scale at every visit (see the caveats in the evidence table).

    - DFU only: 4-week area benchmark (50%), severity grade rules, callus trend.
    - All etiologies: area direction, granulation and fibrin direction.
    - Non-DFU: 4-week change shown as illustrative, no threshold, no severity.
    - Visits closer than config['min_interval_days'] are never given a healing verdict.
    '''
    aetiology = get_aetiology(conn, patient_id)
    is_dfu = _is_dfu(aetiology)
    visits = get_visits(conn, patient_id)
    for v in visits:
        for k in NUM_KEYS:
            v[k] = _number(v.get(k))
    visits = sorted([v for v in visits if v["day"] is not None], key=lambda v: v["day"])
    n = len(visits)
    base = {"patient_id": patient_id, "aetiology": aetiology, "is_dfu": is_dfu, "visit_count": n}

    if n == 0:
        return {**base, "status": "insufficient_data", "flags": [], "rules": [],
                "summary": "No usable visit records (visit dates may be missing)."}
    if n == 1:
        return {**base, "status": "single_visit", "flags": [], "rules": [],
                "summary": "Only one visit is available. A wound progression trend cannot yet be assessed."}

    first, last = visits[0], visits[-1]
    span = last["day"] - first["day"]
    interval_ok = span >= config["min_interval_days"]
    parts, rules, flags = [], [], []

    # Rule 1: area change, first to last visit (descriptive)
    reduction = _pct_area_reduction(first["wound_area"], last["wound_area"])
    if reduction is None:
        parts.append("Area change could not be calculated because an area measurement is missing or the baseline area is zero.")
        area_dir = "not available"
    elif not interval_ok:
        area_dir = "interval_too_short"
        parts.append(
            f"Only {span:.0f} days separate the first and last visit, which is too short to judge healing "
            f"(published area benchmarks use about 4 weeks). Area went from {first['wound_area']:.2f} to "
            f"{last['wound_area']:.2f} ({reduction:+.1f}%, positive means smaller). This is a measurement, not a healing verdict.")
    else:
        if reduction > config["area_tol"]:
            area_dir = "decreased"
        elif reduction < -config["area_tol"]:
            area_dir = "increased"
            flags.append("area_increased")
        else:
            area_dir = "showed no clear change"
        size_word = "smaller" if reduction >= 0 else "larger"
        parts.append(
            f"Wound area {area_dir} from {first['wound_area']:.2f} to {last['wound_area']:.2f} over {span:.0f} days "
            f"({abs(reduction):.1f}% {size_word} than at the first visit).")
    rules.append({"rule": "overall_area_change", "span_days": span,
                  "area_reduction_pct": None if reduction is None else round(reduction, 2),
                  "interpretation": area_dir,
                  "note": "Descriptive. Evidence supports percent change against a threshold, not direction alone."})

    # Rule 2: 4-week benchmark. Validated for DFU only.
    lo, hi = config["window"]
    cands = [v for v in visits[1:] if lo <= v["day"] - first["day"] <= hi and v["wound_area"] is not None]
    bench_visit = min(cands, key=lambda v: abs(v["day"] - first["day"] - 28)) if cands else None
    par = _pct_area_reduction(first["wound_area"], bench_visit["wound_area"]) if bench_visit else None
    bench_interp = None

    if is_dfu:
        if bench_visit is None:
            bench_interp = "no_visit_in_window"
            parts.append(f"DFU record, but no visit with an area measurement falls {lo} to {hi} days after baseline, so the 4-week benchmark was not assessed.")
        elif par is None:
            bench_interp = "not_assessable"
            parts.append("The 4-week DFU benchmark could not be calculated because the baseline area is missing or zero.")
        elif par >= config["bench_par"]:
            bench_interp = "benchmark_met"
            parts.append(f"At day {bench_visit['day']:.0f} the area was {par:.1f}% smaller, meeting the {config['bench_par']}% four-week DFU benchmark. "
                         "This is a favourable sign, not a guarantee of healing (roughly half to 60% of such ulcers heal by 12 weeks in published cohorts).")
        else:
            bench_interp = "below_benchmark_reassess"
            flags.append("below_4wk_benchmark")
            parts.append(f"At day {bench_visit['day']:.0f} the area was {par:.1f}% smaller, below the {config['bench_par']}% four-week DFU benchmark. "
                         "Published guidance treats this as a prompt to reassess the treatment plan, assuming standard of care was delivered. It is not a diagnosis.")
        rules.append({"rule": "dfu_four_week_area_benchmark", "benchmark_pct": config["bench_par"],
                      "visit_day": None if bench_visit is None else bench_visit["day"],
                      "observed_area_reduction_pct": None if par is None else round(par, 2),
                      "interpretation": bench_interp,
                      "source": "Sheehan et al., Diabetes Care 2003;26(6):1879-82"})
    else:
        bench_interp = "illustrative_only_no_validated_threshold"
        if par is not None:
            parts.append(f"Non-DFU wound ({aetiology}): the 50% four-week threshold was not applied because it is validated for diabetic foot ulcers. "
                         f"For illustration, area at day {bench_visit['day']:.0f} was {par:.1f}% smaller than baseline.")
        else:
            parts.append(f"Non-DFU wound ({aetiology}): the DFU four-week benchmark was not applied.")
        rules.append({"rule": "four_week_change_non_dfu", "observed_area_reduction_pct": None if par is None else round(par, 2),
                      "interpretation": bench_interp,
                      "note": "Four-week percent change is prognostic in venous ulcers, but cut-points differ from 50%. No threshold applied."})

    # Rule 3: tissue direction (descriptive, no clinical cut-offs)
    tdir = {}
    for key, label in (("granulation_pct", "granulation"), ("fibrin_pct", "fibrin"), ("callus_pct", "callus")):
        if key == "callus_pct" and not is_dfu:
            tdir[key] = "not_interpreted_non_dfu"
            continue
        s, e = first[key], last[key]
        tdir[key] = _direction(s, e, config["tissue_tol"])
        if s is None or e is None:
            parts.append(f"{label.capitalize()} trend unavailable because measurements are missing.")
        elif interval_ok:
            parts.append(f"{label.capitalize()} {tdir[key]} from {s:.1f}% to {e:.1f}% ({e - s:+.1f} percentage points).")
    tissue_pattern = "not_assessed"
    if interval_ok and tdir["granulation_pct"] != "not available" and tdir["fibrin_pct"] != "not available":
        g, f = tdir["granulation_pct"], tdir["fibrin_pct"]
        if g == "increased" and f == "decreased":
            tissue_pattern = "consistent_with_wound_bed_progress"
        elif g == "decreased" and f == "increased":
            tissue_pattern = "consistent_with_wound_bed_regression"
            flags.append("tissue_regression_pattern")
        else:
            tissue_pattern = "mixed_or_no_clear_change"
        parts.append(f"Tissue pattern: {tissue_pattern.replace('_', ' ')} (descriptive, not a validated predictor of closure).")
    rules.append({"rule": "tissue_composition_direction", **{k.replace('_pct', ''): v for k, v in tdir.items()},
                  "pattern": tissue_pattern, "tolerance_percentage_points": config["tissue_tol"],
                  "note": "Descriptive only. Granulation percentage has not been shown to predict closure in all wound types."})

    # Rule 4: severity grade. Diabetic foot only.
    if not is_dfu:
        sev_dir = "not_applicable_non_dfu"
        rules.append({"rule": "severity_grade_direction", "interpretation": sev_dir,
                      "note": "Wagner-Meggitt is a diabetic foot system. Not computed for other etiologies."})
    else:
        s0, s1 = first["severity_grade"], last["severity_grade"]
        if s0 is None or s1 is None:
            sev_dir = "not available"
            parts.append("Severity-grade change could not be assessed because a grade is missing.")
        else:
            d = s1 - s0
            if d >= config["sev_jump"]:
                sev_dir = "worsened"
                flags.append("severity_worsened")
                parts.append(f"Severity grade rose from {s0:g} to {s1:g}, a change of {config['sev_jump']} or more grades. Flag for clinical review.")
            elif d <= -config["sev_jump"]:
                sev_dir = "improved"
                parts.append(f"Severity grade fell from {s0:g} to {s1:g}, a change of {config['sev_jump']} or more grades.")
            else:
                sev_dir = "stable"
                parts.append(f"Severity grade went from {s0:g} to {s1:g}, treated as stable because a one-grade difference is within model noise.")
            if s1 >= config["dfu_grade_note"]:
                flags.append("high_grade")
                parts.append(f"Latest grade is {s1:g}. If the classes map to Wagner grades, grade {config['dfu_grade_note']} or higher is associated with higher amputation risk in published cohorts.")
        rules.append({"rule": "severity_grade_direction", "first_grade": s0, "latest_grade": s1, "interpretation": sev_dir,
                      "assumption": "Higher grade means more severe. Grade change is a flag, not a healing measure. Verify the class mapping of the severity model."})

    if not interval_ok:
        status = "interval_too_short"
    elif n == 2:
        status = "two_visits_direction_only"
        parts.append("Only two visits: this describes direction of change, not a longitudinal trend.")
    else:
        status = "three_or_more_visits_trend"
        parts.append(f"{n} visits available. This is a rule-based description, not a healing-outcome prediction.")

    return {**base, "status": status, "span_days": span,
            "area_reduction_pct_first_to_last": None if reduction is None else round(reduction, 2),
            "benchmark_interpretation": bench_interp, "tissue_directions": tdir, "tissue_pattern": tissue_pattern,
            "severity_direction": sev_dir, "flags": flags, "rules": rules, "summary": " ".join(parts)}
