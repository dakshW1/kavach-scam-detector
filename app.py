"""Kavach – offline scam message checker.  Run:  streamlit run app.py"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from kavach import netguard  # noqa: E402

netguard.enable()  # from here on, no outgoing internet connection is possible (see kavach/netguard.py)

import streamlit as st  # noqa: E402

from kavach import diary  # noqa: E402
from kavach.detector import get_model  # noqa: E402
from ui import batch, check, diary_page, fool, library_page, results  # noqa: E402
from ui.components import inject_css  # noqa: E402

st.set_page_config(page_title="Kavach – offline scam checker", page_icon="🛡️", layout="wide")
inject_css()


@st.cache_resource
def _warm():
    return get_model()


_warm()

with st.sidebar:
    st.markdown("### 🔒 Privacy")
    guard = netguard.self_test()
    st.markdown(
        f"<div class='kv-privacy'>"
        f"{'🟢' if guard else '🔴'} <b>Internet: {'BLOCKED' if guard else 'NOT BLOCKED'}</b><br>"
        f"<span class='kv-muted'>{len(netguard.blocked_attempts)} connection attempt(s) blocked this session</span><br>"
        f"{'🟡' if diary.is_enabled() else '⚪'} <b>Scam Diary: {'ON' if diary.is_enabled() else 'OFF'}</b><br>"
        f"<span class='kv-muted'>{'masked entries, saved only on this computer' if diary.is_enabled() else 'nothing is saved'}</span><br>"
        f"{'🟡' if netguard.allowed_log else '⚪'} <b>Online news search: {'used' if netguard.allowed_log else 'not used'}</b><br>"
        f"<span class='kv-muted'>{'only scam type + brand were sent' if netguard.allowed_log else 'only runs when you click it'}</span>"
        f"</div>", unsafe_allow_html=True)
    st.caption("Messages are analysed on this computer and never leave it.")

nav = st.navigation([
    st.Page(check.page, title="Check a message", icon="🛡️", url_path="check", default=True),
    st.Page(diary_page.page, title="Scam Diary", icon="📔", url_path="diary"),
    st.Page(library_page.page, title="Scam Library", icon="📚", url_path="library"),
    st.Page(fool.page, title="Try to fool it", icon="🧪", url_path="fool"),
    st.Page(batch.page, title="Batch check", icon="📋", url_path="batch"),
    st.Page(results.page, title="Results & privacy", icon="📊", url_path="results"),
])
nav.run()
