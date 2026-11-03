from pathlib import Path

import streamlit as st

from src.i18n import read_legal_document, translate


ROOT_DIR = Path(__file__).resolve().parents[1]

navigation = st.container(horizontal=True)
with navigation:
    st.page_link("app_pages/home.py", label=translate("nav_home"), icon=":material/home:")
    st.page_link(
        "app_pages/privacy_policy.py",
        label=translate("nav_privacy"),
        icon=":material/policy:",
    )
    st.page_link(
        "app_pages/third_party_services.py",
        label=translate("nav_third_party"),
        icon=":material/handshake:",
    )

st.markdown(read_legal_document("TERMS_OF_SERVICE"))