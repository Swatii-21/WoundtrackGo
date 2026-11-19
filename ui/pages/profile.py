import datetime as dt
import numpy as np, pandas as pd, altair as alt, streamlit as st
from PIL import Image
from config import NAVY, TEAL, MINT
from ui.common import ss, H, LOGO, go, back, card_h, repo, pat, progress_label
from backend.imaging import vimgs
from backend.models import run_models


def profile():
    p = pat(ss.pid); vs = repo().visits(p["id"])
    a, b = st.columns([5, 1]); b.button("View Report", key="rep", on_click=go, args=("Progression Tracking", p["id"]), use_container_width=True)
    with st.container(key="card_head"):
        st.markdown(H(f'''<div style="display:flex;gap:18px;align-items:center"><span class="av" style="width:64px;height:64px;font-size:20px">{"".join(w[0] for w in p["name"].split()[:2])}</span><div>
        <b style="font-size:22px">{p["name"]}</b> <span class="pill {p["risk"]}">{p["risk"]} Risk</span>
        <div style="display:flex;gap:40px;margin-top:8px;font-size:14px"><span><small>Age</small><br><b>{p["age"]}</b></span><span><small>Gender</small><br><b>{p["gender"]}</b></span>
        <span><small>Diagnosis</small><br><b>{p["full"]}</b></span><span><small>Wound Location</small><br><b>{p["loc"]}</b></span></div></div></div>'''), unsafe_allow_html=True)
    st.write(""); L, R = st.columns([1.1, 1])
    with L, st.container(key="card_hist"):
        card_h("Visit History")
        if not vs: st.info("No visits yet. Add the first visit.")
        items = "".join(f"<div class='it'><b>Visit {i + 1} • {v['date']}</b>{'<span class=badge>Latest</span>' if i == len(vs) - 1 else ''}<br><img src='{vimgs(p['id'], i, v)['img']}' width=56 height=42 style='border-radius:6px;object-fit:cover;margin-top:4px'></div>" for i, v in reversed(list(enumerate(vs))))
        st.markdown(f"<div class='tl'>{items}</div>", unsafe_allow_html=True)
        if vs:
            for c, i in zip(st.columns(len(vs)), reversed(range(len(vs)))): c.button(f"View {i + 1}", key=f"vv{i}", on_click=go, args=("AI Analysis", p["id"], i), use_container_width=True)
    with R, st.container(key="card_sum"):
        card_h("Patient Summary"); trend = progress_label(p["id"])
        for t, v in [("Total Visits", len(vs)), ("Current Risk Level", p["risk"]), ("Overall Progress", trend)]:
            st.markdown(f"<div class='chk'><span class='ms'>check_circle</span><div><small>{t}</small><br><b>{v}</b></div></div>", unsafe_allow_html=True)
        st.button("+ Add New Visit", on_click=go, args=("Add New Visit",), use_container_width=True)


render = profile
