import datetime as dt
import numpy as np, pandas as pd, altair as alt, streamlit as st
from PIL import Image
from config import NAVY, TEAL, MINT
from ui.common import ss, H, LOGO, go, back, card_h, repo, pat
from backend.imaging import vimgs
from backend.models import run_models


def dashboard():
    st.text_input("s", placeholder="Search patients...", label_visibility="collapsed", key="gs")
    a, b = st.columns([4, 1]); a.markdown("<h1 class='t'>Welcome back, Dr. Sharma!</h1><span style='color:#5b6b78'>Here's an overview of your patients</span>", unsafe_allow_html=True)
    b.button("+ Add Patient", on_click=go, args=("Add Patient",), use_container_width=True)
    P = repo().patients(); tv = repo().total_visits()
    K = [("groups", "#DCF1EC", TEAL, "Total Patients", len(P)), ("warning", "#FDE3E1", "#D9342B", "High Risk Patients", sum(p["risk"] == "High" for p in P)),
         ("calendar_month", "#DDEBFB", "#2F6FD0", "Total Visits", tv), ("check_circle", "#DCF1EC", "#2E9E7F", "Recent Activity", "2 Today")]
    for c, (ic, bg, fg, t, v) in zip(st.columns(4), K):
        c.markdown(H(f"<div class='kpi'><div class='ic' style='background:{bg}'><span class='ms' style='color:{fg}'>{ic}</span></div><div><small>{t}</small><b>{v}</b></div></div>"), unsafe_allow_html=True)
    st.write("")
    with st.container(key="card_list"):
        x, y = st.columns([3, 1.3]); x.markdown("<b style='font-size:18px'>Patients List</b>", unsafe_allow_html=True)
        q = y.text_input("f", placeholder="Search by name...", label_visibility="collapsed", key="nm")
        W = [2.3, .7, 1, 1.7, 1.2, 1.4, 1.5]
        for c, t in zip(st.columns(W), ["Patient Name", "Age", "Gender", "Diagnosis", "Risk Level", "Last Visit", "Actions"]): c.markdown(f"<div class='th'>{t}</div>", unsafe_allow_html=True)
        for p in [p for p in P if q.lower() in p["name"].lower()]:
            c = st.columns(W, vertical_alignment="center"); ini = "".join(w[0] for w in p["name"].split()[:2])
            c[0].markdown(f"<span class='av'>{ini}</span>{p['name']}", unsafe_allow_html=True); c[1].markdown(str(p["age"])); c[2].markdown(p["gender"]); c[3].markdown(p["dx"])
            c[4].markdown(f"<span class='pill {p['risk']}'>{p['risk']}</span>", unsafe_allow_html=True); c[5].markdown(repo().last_visit(p["id"]))
            c[6].button("View Profile", key=f"vp{p['id']}", on_click=go, args=("Patient Profile", p["id"]), use_container_width=True)
    st.caption("Demo data. Wound assessments are visual, non-clinical impressions.")


render = dashboard