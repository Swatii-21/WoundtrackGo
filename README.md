# WoundTrack (Streamlit)

Run: pip install -r requirements.txt -r requirements-models.txt, then streamlit run app.py
(without requirements-models.txt the app runs in labelled DEMO MODE)
Demo login: any email + password demo123

## Structure
```
app.py                      entry point + router (shows a DEMO MODE banner if the models cannot load)
config.py                   colours + tissue legend
woundtrack/                 the unified backend (models, digital twin, rule engine). No streamlit.
  segmentation.py           Model 1  wound boundary + area
  tissue.py                 Model 2  tissue ensemble (granulation / fibrin / callus)
  severity.py               Model 3  severity grade (diabetic foot ulcers only)
  twin_db.py                SQLite digital twin (patients, visits)
  rules.py                  rule engine (progression rules, from the rule-engine notebook)
  pipeline.py               WoundTrackPipeline: image -> models -> twin -> rules
backend/                    glue between the UI and woundtrack/. No streamlit.
  service.py                loads the pipeline once; falls back to demo mode if weights are missing
  twin_repository.py        the repository the UI uses (real data)
  repository.py, demo_data.py, imaging.py, models/   demo mode only
ui/                         streamlit only (pages, styles, session state)
tests/                      rule-engine tests, pipeline tests, UI integration tests
weights/                    trained model files (see weights/README.txt)
data/                       created at runtime: digital_twin.db and stored visit images
```

## How a visit flows
Add New Visit -> `repo().add_visit_from_image(...)` -> `WoundTrackPipeline.process_visit`:
boundary model -> tissue ensemble -> severity (only if the patient's diagnosis is DFU) -> saved as a visit in the
digital twin -> rule engine over the patient's visits -> shown on AI Analysis and Progression Tracking.

## Things to know
- Tissue classes are **Granulation, Fibrin, Callus** (what the model predicts). They are not slough/necrotic.
- Severity is **not applicable** for non-diabetic-foot wounds and the screens say so.
- Wound area is a % of the image (no scale in the photos), so compare visits taken from a similar distance.
- Patient "risk level" is entered by the clinician. The models do not compute it.
- Login is still the demo login (any email + password `demo123`); it is not real authentication.
- Run the tests: `python tests/test_rules.py`, `python tests/test_pipeline.py`, `python tests/test_integration.py`.

## 🚀 Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/Swatii-21/WoundtrackGo.git
cd WoundtrackGo
```

### 2. Create a virtual environment

For macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

For Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt -r requirements-models.txt
```

Then copy the trained weights into `weights/` (see `weights/README.txt`).

### 4. Run the application

```bash
python -m streamlit run app.py
```

The application will open in your browser at:

`http://localhost:8501`

## 📁 Project Structure

- `app.py` – Main Streamlit application
- `backend/` – Backend logic and model pipeline
- `backend/models/` – Wound analysis models
- `ui/` – Application pages and UI components
- `assets/` – Images and visual assets
- `scripts/` – Utility and testing scripts
- `weights/` – Model weights directory

## 🛠️ Tech Stack

- Python
- Streamlit
- Machine Learning
- Computer Vision
