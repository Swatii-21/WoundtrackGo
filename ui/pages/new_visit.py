import datetime as dt
import numpy as np, pandas as pd, altair as alt, streamlit as st
from PIL import Image
from config import NAVY, TEAL, MINT
from ui.common import ss, H, LOGO, go, back, card_h, repo, pat
from backend.imaging import vimgs
from backend.models import run_models


def new_visit():
    p = pat(ss.pid); L, R = st.columns([1.1, 1])
    with L, st.container(key="card_nv"):
        card_h(f"Add New Visit · {p['name']}"); d = st.date_input("Visit Date", dt.date.today(), format="DD/MM/YYYY")
        up = st.file_uploader("Upload Wound Image", type=["jpg", "jpeg", "png"]); st.text_area("Notes (Optional)", placeholder="Any additional notes...")
        if st.button("Run Analysis →", use_container_width=True):
            if up is None: st.warning("Upload a wound image first.")
            else:
                repo().add_visit(p["id"], run_models(Image.open(up), d.strftime("%d %b %Y"))); go("AI Analysis", p["id"], len(repo().visits(p["id"])) - 1); st.rerun()
    with R, st.container(key="card_next"):
        card_h("What happens next?"); st.caption("Our AI models will analyse the wound:")
        for t, s in [("Boundary Segmentation", "(Total area & mask)"), ("Tissue Segmentation", "(Granulation, Slough, Necrotic)"), ("Severity Classification", "(Risk Level)")]:
            st.markdown(f"<div class='chk'><span class='ms'>check_circle</span><div><b>{t}</b><br>{s}</div></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align:center;padding:30px'><span class='ms' style='font-size:110px;color:#7DB7D6'>biotech</span></div>", unsafe_allow_html=True)


render = new_visit
