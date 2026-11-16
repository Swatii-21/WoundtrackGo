import datetime as dt
import numpy as np, pandas as pd, altair as alt, streamlit as st
from PIL import Image
from config import NAVY, TEAL, MINT
from ui.common import ss, H, LOGO, go, back, card_h, repo, pat
from backend.imaging import vimgs
from backend.models import run_models


def add_patient():
    st.markdown("<h1 class='t'>Add Patient</h1>", unsafe_allow_html=True); st.write("")
    with st.container(key="card_add"):
        a, b = st.columns(2); n = a.text_input("Full name"); age = b.number_input("Age", 1, 120, 50)
        c, d = st.columns(2); g = c.selectbox("Gender", ["Female", "Male", "Other"]); dx = d.selectbox("Diagnosis", ["DFU", "VLU", "Pressure Ulcer", "Other"])
        e, f = st.columns(2); loc = e.text_input("Wound location"); rk = f.selectbox("Risk level", ["High", "Medium", "Low"])
        if st.button("Save patient"):
            if not n.strip(): st.error("Enter the patient's name.")
            else:
                pid = repo().add_patient(dict(name=n.strip(), age=int(age), gender=g, dx=dx, full=dx, loc=loc or "-", risk=rk)); go("Patient Profile", pid); st.rerun()


render = add_patient
