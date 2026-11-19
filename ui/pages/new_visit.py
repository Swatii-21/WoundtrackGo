import datetime as dt
import numpy as np, pandas as pd, altair as alt, streamlit as st
from PIL import Image, ImageOps
from config import NAVY, TEAL, MINT
from ui.common import ss, H, LOGO, go, back, card_h, repo, pat
from backend.imaging import vimgs


def new_visit():
    p = pat(ss.pid); L, R = st.columns([1.1, 1])
    with L, st.container(key="card_nv"):
        card_h(f"Add New Visit · {p['name']}"); d = st.date_input("Visit Date", dt.date.today(), format="DD/MM/YYYY")
        up = st.file_uploader("Upload Wound Image", type=["jpg", "jpeg", "png"])
        notes = st.text_area("Notes (Optional)", placeholder="Any additional notes...")
        if st.button("Run Analysis →", use_container_width=True):
            if up is None: st.warning("Upload a wound image first.")
            else:
                idx = None
                try:
                    with st.spinner("Analysing the wound image..."):
                        img = ImageOps.exif_transpose(Image.open(up))        # phone photos carry a rotation flag
                        idx, _ = repo().add_visit_from_image(p["id"], img, d, notes)
                except ValueError as e:                                     # e.g. a visit already exists on that date
                    st.error(str(e))
                if idx is not None:
                    go("AI Analysis", p["id"], idx); st.rerun()
    with R, st.container(key="card_next"):
        card_h("What happens next?"); st.caption("Our AI models will analyse the wound:")
        for t, s in [("Boundary Segmentation", "(Total area & mask)"), ("Tissue Segmentation", "(Granulation, Fibrin, Callus)"), ("Severity Classification", "(Grade 1-4, diabetic foot ulcers only)")]:
            st.markdown(f"<div class='chk'><span class='ms'>check_circle</span><div><b>{t}</b><br>{s}</div></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align:center;padding:30px'><span class='ms' style='font-size:110px;color:#7DB7D6'>biotech</span></div>", unsafe_allow_html=True)


render = new_visit
