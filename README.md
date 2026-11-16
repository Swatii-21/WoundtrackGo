# WoundTrack (Streamlit)

Run: pip install -r requirements.txt, then streamlit run app.py
Demo login: any email + password demo123

## Structure
app.py                  entry point + router
config.py               colours
backend/                NO streamlit imports; this is where integration happens
  models.py             predict_boundary / predict_tissue / predict_severity / run_models  (Person A, B, C)
  repository.py         data access (DemoRepository, swap for Person D's DB)
  demo_data.py, imaging.py   demo only
ui/                     streamlit only
  common.py             session state, repo(), go()
  styles.py, sidebar.py
  pages/                one file per screen, each exposes render()

## Integration points
1. Models: edit only backend/models.py. Keep run_models() returning
   date, pct, px, gran, slough, necro, grade, conf, img, mask, seg.
2. Database: write a class with the same methods as DemoRepository
   (patients, patient, add_patient, visits, add_visit, total_visits, last_visit)
   and return it from repo() in ui/common.py.
