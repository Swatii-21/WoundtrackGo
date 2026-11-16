import datetime as dt
import numpy as np, pandas as pd, altair as alt, streamlit as st
from PIL import Image
from config import NAVY, TEAL, MINT
from ui.common import ss, H, LOGO, go, back, card_h, repo, pat
from backend.imaging import vimgs
from backend.models import run_models


def progression():
    a, b, c = st.columns([3, 1.4, 1.2]); a.markdown("<h1 class='t'>Progression Tracking</h1>", unsafe_allow_html=True)
    pid = b.selectbox("Patient", [p["id"] for p in repo().patients()], index=[p["id"] for p in repo().patients()].index(ss.pid), format_func=lambda i: pat(i)["name"], label_visibility="collapsed"); ss.pid = pid
    rng = c.selectbox("Range", ["Last 4 Visits", "All Visits"], label_visibility="collapsed"); vs = repo().visits(pid)
    if rng.startswith("Last"): vs = vs[-4:]
    if len(vs) < 1: return st.info("No visits recorded for this patient yet.")
    df = pd.DataFrame([dict(Visit=f"Visit {i + 1}\n{' '.join(v['date'].split()[:2])}", V=f"V{i + 1}", Area=v["pct"], G=v["gran"], S=v["slough"], N=v["necro"], Grade=v["grade"]) for i, v in enumerate(vs)])
    cfg = lambda ch: ch.properties(height=230, background="transparent").configure_view(strokeWidth=0).configure_axis(grid=True, gridColor="#E6EEF0", domain=False)
    x1, x2, x3 = st.columns(3)
    with x1, st.container(key="card_p1"):
        card_h("Wound Area Trend"); ln = alt.Chart(df).encode(x=alt.X("Visit:N", sort=None, axis=alt.Axis(labelAngle=0, title=None)), y=alt.Y("Area:Q", scale=alt.Scale(domain=[0, 25]), axis=alt.Axis(title=None, format=".0f")))
        st.altair_chart(cfg(ln.mark_line(color="#2E9E7F", point=alt.OverlayMarkDef(color="#2E9E7F", size=70)) + ln.mark_text(dy=-14, color="#14544A").encode(text=alt.Text("Area:Q", format=".1f"))), use_container_width=True)
    with x2, st.container(key="card_p2"):
        card_h("Tissue Composition"); m = df.melt(id_vars=["V"], value_vars=["G", "S", "N"], var_name="T", value_name="P"); m["T"] = m["T"].map({"G": "Granulation", "S": "Slough", "N": "Necrotic"}); m["o"] = m["T"].map({"Granulation": 0, "Slough": 1, "Necrotic": 2})
        st.altair_chart(cfg(alt.Chart(m).mark_bar(size=34).encode(x=alt.X("V:N", sort=None, axis=alt.Axis(labelAngle=0, title=None)), y=alt.Y("P:Q", scale=alt.Scale(domain=[0, 100]), axis=alt.Axis(title=None)),
                        color=alt.Color("T:N", scale=alt.Scale(domain=["Granulation", "Slough", "Necrotic"], range=["#3BB273", "#F5C842", "#E5483D"]), legend=alt.Legend(orient="bottom", title=None)), order=alt.Order("o:Q", sort="descending"))), use_container_width=True)
    with x3, st.container(key="card_p3"):
        card_h("Severity Across Visits"); bar = alt.Chart(df).encode(x=alt.X("V:N", sort=None, axis=alt.Axis(labelAngle=0, title=None)), y=alt.Y("Grade:Q", scale=alt.Scale(domain=[0, 4]), axis=alt.Axis(title=None, tickMinStep=1)))
        st.altair_chart(cfg(bar.mark_bar(size=34, color="#3F7BE0") + bar.mark_text(dy=-8).encode(text="Grade:Q")), use_container_width=True)
    st.write(""); d = vs[-1]["pct"] - vs[0]["pct"]
    msg = "Only one visit is recorded, so no trend can be described yet." if len(vs) < 2 else f"The wound area has {'decreased' if d < 0 else 'increased' if d > 0 else 'not changed'} over the last {len(vs)} visits{', suggesting positive healing progress' if d < 0 else ''}. Severity is Grade {vs[-1]['grade']}."
    st.markdown(f"<div class='ok' style='text-align:left'><b>Progression Summary</b><br><span style='font-weight:400'>{msg}</span></div>", unsafe_allow_html=True)
    st.caption("Area is % of the image (not cm²) and camera angle may differ between visits. Visual, non-clinical impression.")


render = progression
