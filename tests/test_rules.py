"""Rule-engine tests: the exact scenarios from WoundTrack_rule_engine_updated.ipynb, run against the packaged
rules.py and twin_db.py (in-memory database). Run: python tests/test_rules.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from woundtrack.rules import analyse_patient_progression
from woundtrack import twin_db

tc = twin_db.connect(":memory:")
add_patient, add_visit, update_visit_results = twin_db.add_patient, twin_db.add_visit, twin_db.update_visit_results
FAILS = []


def make(pid, aet, rows):
    # rows: list of (day, area, gran, fib, callus, grade)
    add_patient(tc, pid, wound_aetiology=aet)
    for day, a, g, f, c, s in rows:
        vid = add_visit(tc, pid, day)
        if a is not None:
            update_visit_results(tc, vid, wound_area=a, granulation_pct=g, fibrin_pct=f, callus_pct=c, severity_grade=s)


def check(name, ok):
    print(("PASS" if ok else "FAIL"), "-", name)
    if not ok:
        FAILS.append(name)


make(1, "Venous ulcers", [(1, 100, 20, 60, 0, 3), (28, 70, 35, 45, 0, 3), (60, 40, 50, 30, 0, 2)])
make(2, "Diabetic foot", [(1, 50, 40, 30, 5, 1), (30, 80, 20, 50, 10, 3)])
make(3, "Diabetic foot", [(1, 100, 20, 60, 10, 2), (28, 45, 40, 40, 4, 2)])
make(4, "Diabetic foot", [(1, 100, 30, 50, 5, 2), (7, 60, 30, 50, 5, 2)])
make(5, "Ischaemia", [(1, None, None, None, None, None)])
make(6, "Venous ulcers", [(1, None, None, None, None, None), (50, None, None, None, None, None)])
make(7, "Diabetic foot", [(1, 100, 30, 50, 5, 2), (28, 51, 30, 50, 5, 2)])   # 49% reduction
make(8, "Diabetic foot", [(1, 100, 30, 50, 5, 2), (28, 50, 30, 50, 5, 2)])   # exactly 50%
make(9, "Diabetic foot", [(1, 100, 30, 50, 5, 2), (265, 40, 30, 50, 5, 2)])  # no visit in window

r = {p: analyse_patient_progression(tc, p) for p in range(1, 10)}
check("venous: severity NOT computed", r[1]["severity_direction"] == "not_applicable_non_dfu" and "severity" not in r[1]["summary"].lower())
check("venous: 50% DFU benchmark NOT applied, 4-week change illustrative", r[1]["benchmark_interpretation"] == "illustrative_only_no_validated_threshold")
check("venous: callus not interpreted", r[1]["tissue_directions"]["callus_pct"] == "not_interpreted_non_dfu")
check("venous: tissue pattern shows progress", r[1]["tissue_pattern"] == "consistent_with_wound_bed_progress")
check("DFU worsening: below benchmark flag", "below_4wk_benchmark" in r[2]["flags"])
check("DFU worsening: area increased flag", "area_increased" in r[2]["flags"])
check("DFU worsening: severity worsened + high grade", "severity_worsened" in r[2]["flags"] and "high_grade" in r[2]["flags"])
check("DFU worsening: tissue regression flag", "tissue_regression_pattern" in r[2]["flags"])
check("DFU 55% at day 28: benchmark met", r[3]["benchmark_interpretation"] == "benchmark_met")
check("DFU one grade-free change: severity stable", r[3]["severity_direction"] == "stable")
check("DFU 7 days apart: interval too short, no verdict", r[4]["status"] == "interval_too_short" and r[4]["benchmark_interpretation"] != "benchmark_met")
check("single visit handled", r[5]["status"] == "single_visit")
check("no measurements handled without crash", r[6]["status"] in ("two_visits_direction_only",) and r[6]["area_reduction_pct_first_to_last"] is None)
check("49% reduction: below benchmark", r[7]["benchmark_interpretation"] == "below_benchmark_reassess")
check("exactly 50% reduction: benchmark met", r[8]["benchmark_interpretation"] == "benchmark_met")
check("DFU with no visit in 21-35 day window: not assessed", r[9]["benchmark_interpretation"] == "no_visit_in_window")

try:
    add_visit(tc, 1, 1)
    check("duplicate day rejected by the twin", False)
except ValueError:
    check("duplicate day rejected by the twin", True)

if FAILS:
    print(f"\n{len(FAILS)} FAILED"); sys.exit(1)
print("\nAll rule-engine tests passed")
