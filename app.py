import streamlit as st
import importlib.util
import os
import uuid

st.set_page_config(
    page_title="🏸 เชียงใหม่แบดมินตัน",
    page_icon="🏸",
    layout="wide",
    menu_items={},
)

from database import init_db
from utils.styles import apply_styles

init_db()
apply_styles()

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False
if "voted_players" not in st.session_state:
    st.session_state.voted_players = set()
if "active_tab" not in st.session_state:
    try:
        st.session_state.active_tab = int(st.query_params.get("tab", 0))
    except (ValueError, TypeError):
        st.session_state.active_tab = 0

TABS = [
    ("🏸", "0_information.py", "ข้อมูลทั่วไป / Information"),
    ("🔥", "1_Ranking.py", "อันดับ / Ranking"),
    ("🔍", "2_Match_Finder.py", "จับคู่แข่งขัน / Match Finder"),
    ("🙋‍♂️", "3_Protest.py", "ประท้วง / Protest"),
    ("🔧", "4_Admin.py", "ติดต่อสอบถาม / Admin"),
]


@st.cache_resource
def load_page(filename):
    path = os.path.join(os.path.dirname(__file__), "pages", filename)
    spec = importlib.util.spec_from_file_location(filename, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── Sidebar navigation ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏸 เชียงใหม่แบดมินตัน")
    st.divider()
    for i, (emoji, _, name) in enumerate(TABS):
        active = st.session_state.active_tab == i
        btn_type = "primary" if active else "secondary"
        if st.button(f"{emoji} {name}", use_container_width=True, type=btn_type, key=f"tab_{i}"):
            st.session_state.active_tab = i
            st.query_params["tab"] = str(i)
            st.rerun()

# ── Render only active tab ────────────────────────────────────────────────────
_, filename, _ = TABS[st.session_state.active_tab]
mod = load_page(filename)
mod.render()
