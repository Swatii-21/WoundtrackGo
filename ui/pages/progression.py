import datetime as dt
import numpy as np, pandas as pd, altair as alt, streamlit as st
from PIL import Image
from config import NAVY, TEAL, MINT, TISSUE
from ui.common import ss, H, LOGO, go, back, card_h, repo, pat
from backend.imaging import vimgs


def progression():
    a, b, c = st.columns([3, 1.4, 1.2]); a.markdown("<h1 class='t'>Progression Tracking</h1>", unsafe_allow_html=True)
    pid = b.selectbox("Patient", [p["id"] for p in repo().patients()], index=[p["id"] for p in repo().patients()].index(ss.pid), format_func=lambda i: pat(i)["name"], label_visibility="collapsed"); ss.pid = pid
    rng = c.selectbox("Range", ["Last 4 Visits", "All Visits"], label_visibility="collapsed"); vs = repo().visits(pid)
    if rng.startswith("Last"): vs = vs[-4:]
    if len(vs) < 1: return st.info("No visits recorded for this patient yet.")
    df = pd.DataFrame([dict(Visit=f"Visit {i + 1}\n{' '.join(v['date'].split()[:2])}", V=f"V{i + 1}", Area=v["pct"], G=v["gran"], F=v["fibrin"], C=v["callus"], Grade=v["grade"]) for i, v in enumerate(vs)])
    cfg = lambda ch: ch.properties(height=230, background="transparent").configure_view(strokeWidth=0).configure_axis(grid=True, gridColor="#E6EEF0", domain=False)
    amax = max(25, int(df["Area"].max() * 1.15) + 1)                      # the old fixed 0-25 axis clipped larger wounds
    x1, x2, x3 = st.columns(3)
    with x1, st.container(key="card_p1"):
        card_h("Wound Area Trend"); ln = alt.Chart(df).encode(x=alt.X("Visit:N", sort=None, axis=alt.Axis(labelAngle=0, title=None)), y=alt.Y("Area:Q", scale=alt.Scale(domain=[0, amax]), axis=alt.Axis(title=None, format=".0f")))
        st.altair_chart(cfg(ln.mark_line(color="#2E9E7F", point=alt.OverlayMarkDef(color="#2E9E7F", size=70)) + ln.mark_text(dy=-14, color="#14544A").encode(text=alt.Text("Area:Q", format=".1f"))), use_container_width=True)
    with x2, st.container(key="card_p2"):
        names = {"G": TISSUE[0][0], "F": TISSUE[1][0], "C": TISSUE[2][0]}
        card_h("Tissue Composition"); m = df.melt(id_vars=["V"], value_vars=["G", "F", "C"], var_name="T", value_name="P"); m["T"] = m["T"].map(names); m["o"] = m["T"].map({n: i for i, n in enumerate(names.values())})
        st.altair_chart(cfg(alt.Chart(m).mark_bar(size=34).encode(x=alt.X("V:N", sort=None, axis=alt.Axis(labelAngle=0, title=None)), y=alt.Y("P:Q", scale=alt.Scale(domain=[0, 100]), axis=alt.Axis(title=None)),
                        color=alt.Color("T:N", scale=alt.Scale(domain=[t[0] for t in TISSUE], range=[t[2] for t in TISSUE]), legend=alt.Legend(orient="bottom", title=None)), order=alt.Order("o:Q", sort="descending"))), use_container_width=True)
    with x3, st.container(key="card_p3"):
        card_h("Severity Across Visits")
        if df["Grade"].isna().all():
            st.caption("Severity grading is only available for diabetic foot ulcers.")
        else:
            bar = alt.Chart(df).encode(x=alt.X("V:N", sort=None, axis=alt.Axis(labelAngle=0, title=None)), y=alt.Y("Grade:Q", scale=alt.Scale(domain=[0, 4]), axis=alt.Axis(title=None, tickMinStep=1)))
            st.altair_chart(cfg(bar.mark_bar(size=34, color="#3F7BE0") + bar.mark_text(dy=-8).encode(text="Grade:Q")), use_container_width=True)
    st.write("")
    r = repo()
    if hasattr(r, "progression"):                                          # real digital twin: rule engine output (all visits)
        pr = r.progression(pid); msg = pr["summary"]
    else:                                                                  # demo mode: the old simple description
        d = vs[-1]["pct"] - vs[0]["pct"]
        msg = "Only one visit is recorded, so no trend can be described yet." if len(vs) < 2 else f"The wound area has {'decreased' if d < 0 else 'increased' if d > 0 else 'not changed'} over the last {len(vs)} visits{', suggesting positive healing progress' if d < 0 else ''}."
        pr = None
    st.markdown(f"<div class='ok' style='text-align:left'><b>Progression Summary</b><br><span style='font-weight:400'>{msg}</span></div>", unsafe_allow_html=True)
    if pr and pr["flags"]:
        st.warning("Flags: " + ", ".join(f.replace("_", " ") for f in pr["flags"]))
    if pr and pr["rules"]:
        with st.expander("Rule details (what the summary is based on)"):
            st.json(pr["rules"])
    st.caption("Area is % of the image (not cm²) and camera distance may differ between visits. Rule-based description, not a healing prediction or diagnosis.")


render = progression
