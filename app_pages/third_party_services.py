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
        "app_pages/terms_of_service.py",
        label=translate("nav_terms"),
        icon=":material/description:",
    )

st.markdown(read_legal_document("THIRD_PARTY_SERVICES"))