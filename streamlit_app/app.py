# app.py
import streamlit as st
from utils.wazuh_connector import get_wazuh_connector
from config import APP_TITLE, APP_ICON, LAYOUT

st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout=LAYOUT,
    initial_sidebar_state="expanded"
)

st.markdown(
    f"<h1 style='text-align:center'>{APP_ICON} Wazuh ML Analytics</h1>",
    unsafe_allow_html=True
)

with st.sidebar:
    st.markdown("## 🔌 État de la connexion")

    connector = get_wazuh_connector()
    ok, msg = connector.test_api()

    if ok:
        st.success("✅ API Wazuh connectée")
    else:
        st.warning("⚠️ API indisponible (OpenSearch OK)")

st.markdown("""
### 🎯 Bienvenue

- 📊 Explorer les données Wazuh  
- 📈 Visualiser les tendances  
- 🤖 Appliquer le ML  
""")
