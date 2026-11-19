"""WoundTrack entry point: page config, CSS, router. Run: streamlit run app.py"""
import streamlit as st
st.set_page_config(page_title="WoundTrack", layout="wide", initial_sidebar_state="expanded")

from ui.styles import CSS
from ui.common import ss, init_state, go_back, go, repo, is_demo, demo_reason
from ui import sidebar
from ui.pages import login, dashboard, add_patient, profile, new_visit, analysis, progression

PAGES = {"Dashboard": dashboard, "Add Patient": add_patient, "Patient Profile": profile,
         "Add New Visit": new_visit, "AI Analysis": analysis, "Progression Tracking": progression}

NEEDS_PATIENT = {"Patient Profile", "Add New Visit", "AI Analysis", "Progression Tracking"}

init_state()
st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)
if not ss.auth:
    login.render()
else:
    sidebar.render()
    if ss.history:
        st.button("← Back", key="global_back", on_click=go_back)
    if is_demo():
        st.warning("DEMO MODE: the trained models could not be loaded, so all numbers and pictures are placeholders, not real "
                   f"results. Reason: {demo_reason()}")
    if ss.page in NEEDS_PATIENT and not any(p["id"] == ss.pid for p in repo().patients()):
        known = repo().patients()
        if known:
            ss.pid = known[0]["id"]
        else:
            st.info("No patients yet. Add a patient first.")
            st.button("+ Add Patient", on_click=go, args=("Add Patient",))
            st.stop()
    PAGES[ss.page].render()