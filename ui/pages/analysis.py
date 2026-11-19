import datetime as dt
import numpy as np, pandas as pd, altair as alt, streamlit as st
from PIL import Image
from config import NAVY, TEAL, MINT, TISSUE
from ui.common import ss, H, LOGO, go, back, card_h, repo, pat
from backend.imaging import vimgs
from backend.models import run_models


def analysis():
    p = pat(ss.pid); vs = repo().visits(p["id"])
    if not vs: st.info("This patient has no visits yet."); return st.button("+ Add New Visit", on_click=go, args=("Add New Visit",))
    i = len(vs) - 1 if ss.visit is None else ss.visit; v = vimgs(p["id"], i, vs[i])
    st.caption(f"Visit {i + 1} – {v['date']}"); st.markdown("<h1 class='t'>AI Analysis Results</h1>", unsafe_allow_html=True); st.write("")
    A, B, C = st.columns([1.15, 1.15, .8])
    with A, st.container(key="card_a"):
        card_h("A. Boundary Segmentation"); st.markdown(H(f"<div style='display:flex;gap:8px;margin-top:8px'><img src='{v['img']}' style='width:50%;border-radius:8px'><img src='{v['mask']}' style='width:50%;border-radius:8px'></div><div style='display:flex;gap:40px;margin-top:10px'><span><small>Wound Area</small><br><b style='font-size:22px'>{v['px']:,} px</b></span><span><small>Relative Area</small><br><b style='font-size:22px'>{v['pct']}%</b></span></div>"), unsafe_allow_html=True)
    with B, st.container(key="card_b"):
        card_h("B. Tissue Segmentation"); rows = "".join(f"<div style='display:flex;justify-content:space-between;margin:5px 0'><span><span style='color:{c}'>■</span> {n}</span><b>{v[k]}%</b></div>" for n, k, c in TISSUE)
        st.markdown(H(f"<img src='{v['seg']}' style='width:100%;border-radius:8px;margin-top:8px'><div style='margin-top:10px'>{rows}</div><small style='color:#5b6b78'>Share of the tissue pixels found in the image.</small>"), unsafe_allow_html=True)
    with C, st.container(key="card_c"):
        card_h("C. Severity Classification"); conf = v["conf"]; dash = (conf or 0) / 100 * 157
        if v["grade"] is None:
            st.markdown(H("<div style='text-align:center;margin-top:14px'><b style='font-size:26px'>Not applicable</b><hr style='border:0;border-top:1px solid #dde7ea;margin:10px 0'><small>Severity grading is only available for diabetic foot ulcers.</small></div>"), unsafe_allow_html=True)
        else:
            st.markdown(H(f'''<div style="text-align:center;margin-top:14px"><b style="font-size:38px">Grade {v["grade"]}</b><hr style="border:0;border-top:1px solid #dde7ea;margin:10px 0">
            <small>Confidence</small><br><b style="font-size:20px">{f"{conf}%" if conf else "n/a"}</b>
            <svg viewBox="0 0 120 70" width="150"><path d="M10 62A50 50 0 0 1 110 62" fill="none" stroke="#DDE7EA" stroke-width="14" stroke-linecap="round"/>
            <path d="M10 62A50 50 0 0 1 110 62" fill="none" stroke="{TEAL}" stroke-width="14" stroke-linecap="round" stroke-dasharray="{dash} 157"/></svg></div>'''), unsafe_allow_html=True)
    demo = v.get("demo", ["boundary", "tissue", "severity"])
    if demo: st.warning("Demo output (not a real model result) for: " + ", ".join(demo))
    for w in v.get("warnings", []): st.warning(w)
    if v.get("notes"): st.caption(f"Notes: {v['notes']}")
    st.write(""); st.markdown("<div class='ok'>✓ Visit Analysis Completed Successfully</div>", unsafe_allow_html=True)


render = analysis
