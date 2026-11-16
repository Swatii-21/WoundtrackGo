"""UI helpers + session state. Only place that knows about st.session_state."""
import streamlit as st
from config import NAVY, TEAL, MINT
from backend.repository import DemoRepository

ss = st.session_state
def init_state():
    ss.setdefault("auth", False); ss.setdefault("visit", None)
    ss.setdefault("page", "Dashboard"); ss.setdefault("pid", 1); ss.setdefault("history", [])

def repo():
    if "_repo" not in ss:
        ss["_repo"] = DemoRepository()
    return ss["_repo"]


def pat(pid):
    return repo().patient(pid)


def go(page, pid=None, visit=None):
    cur = (ss.page, ss.pid, ss.visit)
    ss.page = page
    if pid is not None:
        ss.pid = pid
    ss.visit = visit
    if (ss.page, ss.pid, ss.visit) != cur:
        ss.history = (ss.history + [cur])[-30:]


def go_back():
    if ss.history:
        ss.page, ss.pid, ss.visit = ss.history.pop()


def H(s): return "".join(l.strip() for l in s.splitlines())

def LOGO(w=40):
    return H(f'''<svg viewBox="0 0 64 56" width="{w}"><path d="M32 54C8 36 2 24 2 15 2 7 8 2 15 2c7 0 13 4 17 10C36 6 42 2 49 2c7 0 13 5 13 13 0 9-6 21-30 39z" fill="{TEAL}"/>
<polyline points="10,28 22,28 27,18 33,40 38,26 42,28 54,28" fill="none" stroke="#fff" stroke-width="3.5" stroke-linejoin="round" stroke-linecap="round"/></svg>''')

def back(label, page):
    st.button(f"← {label}", key=f"back_{page}", on_click=go, args=(page,))

def card_h(t): st.markdown(f"<b style='font-size:16px;color:#12222d'>{t}</b>", unsafe_allow_html=True)
