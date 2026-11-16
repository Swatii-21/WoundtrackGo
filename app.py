"""WoundTrack entry point: page config, CSS, router. Run: streamlit run app.py"""
import streamlit as st
st.set_page_config(page_title="WoundTrack", layout="wide", initial_sidebar_state="expanded")

from ui.styles import CSS
from ui.common import ss, init_state, go_back
from ui import sidebar
from ui.pages import login, dashboard, add_patient, profile, new_visit, analysis, progression

PAGES = {"Dashboard": dashboard, "Add Patient": add_patient, "Patient Profile": profile,
         "Add New Visit": new_visit, "AI Analysis": analysis, "Progression Tracking": progression}

init_state()
st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)
if not ss.auth:
    login.render()
else:
    sidebar.render()
    if ss.history:
        st.button("← Back", key="global_back", on_click=go_back)
    PAGES[ss.page].render()