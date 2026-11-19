"""Digital twin database (SQLite). Same tables and rules as the rule-engine notebook
(patient, visit, UNIQUE(patient_id, day)), plus extra columns for pipeline outputs and traceability."""
from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS patient (
    patient_id      INTEGER PRIMARY KEY,
    age             REAL,
    sex             TEXT,
    wound_aetiology TEXT
);

CREATE TABLE IF NOT EXISTS visit (
    visit_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id          INTEGER NOT NULL REFERENCES patient(patient_id),
    day                 INTEGER NOT NULL,
    duration_months     REAL,
    treatment_technique TEXT,
    wound_area          REAL,      -- the metric chosen in PipelineConfig.area_metric (what the rules read)
    granulation_pct     REAL,
    fibrin_pct          REAL,
    callus_pct          REAL,
    severity_grade      INTEGER,
    photo_path          TEXT,
    thermal_path        TEXT,
    stereo_path         TEXT,
    depth_path          TEXT,
    -- extra columns added by the unified backend
    area_px             INTEGER,
    area_pct            REAL,      -- wound pixels as % of the image
    image_h             INTEGER,
    image_w             INTEGER,
    wound_detected      INTEGER,   -- 0 when Model 1 found (almost) nothing; wound_area is then NULL
    severity_conf       REAL,
    boundary_overlay_path TEXT,
    tissue_overlay_path   TEXT,
    created_at          TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (patient_id, day)
);
"""

# Columns added on top of the base schema. Applied to new AND existing databases (see _ensure_columns), so an
# older digital_twin.db keeps working after an upgrade.
EXTRA_COLUMNS = {
    "patient": {
        "name": "TEXT",
        "wound_location": "TEXT",
        "risk_level": "TEXT",      # clinician-entered (High / Medium / Low), never computed by the models
        "diagnosis": "TEXT",       # short label shown in the UI (DFU, VLU, ...)
    },
    "visit": {
        "visit_date": "TEXT",      # ISO calendar date of the visit; `day` is derived from it
        "notes": "TEXT",
        "mask_path": "TEXT",
        "tissue_map_path": "TEXT",
    },
}


def _ensure_columns(conn):
    for table, cols in EXTRA_COLUMNS.items():
        have = {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
        for col, typ in cols.items():
            if col not in have:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {typ}")
    conn.commit()


# Fields a caller may set when creating a visit.
VISIT_FIELDS = {
    "duration_months", "treatment_technique", "wound_area", "granulation_pct", "fibrin_pct", "callus_pct",
    "severity_grade", "photo_path", "thermal_path", "stereo_path", "depth_path",
    "area_px", "area_pct", "image_h", "image_w", "wound_detected", "severity_conf",
    "boundary_overlay_path", "tissue_overlay_path", "visit_date", "notes", "mask_path", "tissue_map_path",
}
# Fields written by the models.
RESULT_FIELDS = {
    "wound_area", "granulation_pct", "fibrin_pct", "callus_pct", "severity_grade",
    "area_px", "area_pct", "wound_detected", "severity_conf", "boundary_overlay_path", "tissue_overlay_path",
    "mask_path", "tissue_map_path",
}
PATIENT_FIELDS = {"age", "sex", "wound_aetiology", "name", "wound_location", "risk_level", "diagnosis"}


def connect(db_path) -> sqlite3.Connection:
    """Open (and create if needed) the digital twin. check_same_thread=False so Streamlit reruns can reuse it."""
    if str(db_path) != ":memory:":
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")  # SQLite ignores foreign keys unless this is on
    conn.executescript(SCHEMA)
    conn.commit()
    _ensure_columns(conn)
    return conn


def add_patient(conn, patient_id=None, age=None, sex=None, wound_aetiology=None, **extra):
    """Create a patient and return its id. patient_id=None lets SQLite assign the next id."""
    bad = set(extra) - PATIENT_FIELDS
    if bad:
        raise ValueError(f"Unknown patient field(s): {bad}")
    cols = ["patient_id", "age", "sex", "wound_aetiology"] + list(extra)
    vals = [patient_id, age, sex, wound_aetiology] + list(extra.values())
    cur = conn.execute(f"INSERT INTO patient ({', '.join(cols)}) VALUES ({', '.join(['?'] * len(cols))})", vals)
    conn.commit()
    return cur.lastrowid if patient_id is None else patient_id


def get_patient(conn, patient_id) -> dict | None:
    cur = conn.execute("SELECT * FROM patient WHERE patient_id = ?", (patient_id,))
    row = cur.fetchone()
    return dict(zip([c[0] for c in cur.description], row)) if row else None


def ensure_patient(conn, patient_id, age=None, sex=None, wound_aetiology=None) -> bool:
    """Create the patient if new; otherwise only fill details that are still empty. Returns True if created."""
    row = conn.execute("SELECT age, sex, wound_aetiology FROM patient WHERE patient_id = ?", (patient_id,)).fetchone()
    if row is None:
        add_patient(conn, patient_id, age, sex, wound_aetiology)
        return True
    for col, old, new in zip(("age", "sex", "wound_aetiology"), row, (age, sex, wound_aetiology)):
        if old is None and new is not None:
            conn.execute(f"UPDATE patient SET {col} = ? WHERE patient_id = ?", (new, patient_id))
    conn.commit()
    return False


def add_visit(conn, patient_id, day, **fields):
    bad = set(fields) - VISIT_FIELDS
    if bad:
        raise ValueError(f"Unknown field(s): {bad}")
    if not conn.execute("SELECT 1 FROM patient WHERE patient_id = ?", (patient_id,)).fetchone():
        raise ValueError(f"Patient {patient_id} does not exist")

    cols = ["patient_id", "day"] + list(fields)
    vals = [patient_id, day] + list(fields.values())
    sql = f"INSERT INTO visit ({', '.join(cols)}) VALUES ({', '.join(['?'] * len(cols))})"
    try:
        cur = conn.execute(sql, vals)
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        raise ValueError(f"Patient {patient_id} already has a visit on day {day}")
    return cur.lastrowid


def update_visit_results(conn, visit_id, **fields):
    bad = set(fields) - RESULT_FIELDS
    if bad:
        raise ValueError(f"Not a model-output field: {bad}")
    sets = ", ".join(f"{k} = ?" for k in fields)
    cur = conn.execute(f"UPDATE visit SET {sets} WHERE visit_id = ?", list(fields.values()) + [visit_id])
    if cur.rowcount == 0:
        raise ValueError(f"Visit {visit_id} not found")
    conn.commit()


def shift_days(conn, patient_id, delta):
    """Add `delta` days to every visit of a patient (used when a visit is back-dated before the first one).
    Two steps through negative values, because UNIQUE(patient_id, day) is checked row by row."""
    if not delta:
        return
    conn.execute("UPDATE visit SET day = -day WHERE patient_id = ?", (patient_id,))
    conn.execute("UPDATE visit SET day = -day + ? WHERE patient_id = ?", (delta, patient_id))
    conn.commit()


def dated_visits(conn, patient_id):
    """[(day, date_iso)] for visits that have a calendar date, oldest first."""
    return conn.execute(
        "SELECT day, visit_date FROM visit WHERE patient_id = ? AND visit_date IS NOT NULL ORDER BY day", (patient_id,)
    ).fetchall()


def visit_exists(conn, patient_id, day) -> int | None:
    r = conn.execute("SELECT visit_id FROM visit WHERE patient_id = ? AND day = ?", (patient_id, day)).fetchone()
    return r[0] if r else None


def delete_visit(conn, visit_id):
    conn.execute("DELETE FROM visit WHERE visit_id = ?", (visit_id,))
    conn.commit()


def list_patients(conn):
    return conn.execute("SELECT patient_id, age, sex, wound_aetiology FROM patient ORDER BY patient_id").fetchall()


def history(conn, patient_id):
    """All visits for a patient as a list of dicts (for tables and charts), oldest first."""
    cur = conn.execute(
        """SELECT visit_id, day, wound_area, area_px, area_pct, granulation_pct, fibrin_pct, callus_pct,
                  severity_grade, severity_conf, wound_detected, treatment_technique, duration_months,
                  photo_path, boundary_overlay_path, tissue_overlay_path, visit_date, notes, mask_path,
                  tissue_map_path, image_h, image_w
           FROM visit WHERE patient_id = ? ORDER BY day""",
        (patient_id,),
    )
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]
