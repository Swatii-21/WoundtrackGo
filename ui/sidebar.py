import streamlit as st
from config import NAVY, TEAL
from ui.common import ss, H, LOGO, go


def render():
    NAV = [("Dashboard", "dashboard"), ("Add Patient", "add_circle"), ("Patient Profile", "person"), ("AI Analysis", "center_focus_strong"), ("Progression Tracking", "show_chart")]
    active = {"Add New Visit": "Patient Profile"}.get(ss.page, ss.page)
    with st.sidebar:
        st.markdown(H(f'<div style="display:flex;gap:10px;align-items:center;margin:4px 0 22px">{LOGO(34)}<b style="font-size:18px">WoundTrack</b></div>'), unsafe_allow_html=True)
        css = ""
        for i, (lbl, ic) in enumerate(NAV):
            st.button(lbl, key=f"nav{i}", icon=f":material/{ic}:", on_click=go, args=(lbl,), use_container_width=True)
            if lbl == active: css += f".st-key-nav{i} button{{background:#1F8A79 !important}}"
        st.markdown(f"<style>{css}</style><div style='height:260px'></div>", unsafe_allow_html=True)
        st.markdown("<div style='display:flex;gap:10px;align-items:center'><span class='av'>DS</span><b>Dr. Sharma</b></div>", unsafe_allow_html=True)
        st.button("Logout", key="logout", icon=":material/logout:", on_click=lambda: ss.update(auth=False, page="Dashboard", history=[]))