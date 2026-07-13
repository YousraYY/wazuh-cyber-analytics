import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

from utils.wazuh_connector import get_wazuh_connector
from utils.data_processing import clean_dataframe, get_summary_stats


# ==========================================================
# SIMULATED DATA
# ==========================================================
def generate_simulated_data(num_logs, ssh_ratio, http_ratio, firewall_ratio):
    other_ratio = max(0.0, 1.0 - (ssh_ratio + http_ratio + firewall_ratio))
    event_types = ["ssh", "http", "firewall", "system"]
    ratios = [ssh_ratio, http_ratio, firewall_ratio, other_ratio]

    events = np.random.choice(event_types, size=num_logs, p=ratios)
    base_time = datetime.now() - timedelta(hours=24)

    rows = []
    for i, ev in enumerate(events):
        rows.append({
            "@timestamp": base_time + timedelta(minutes=i),
            "type": ev,
            "src_ip": f"192.168.{np.random.randint(1,255)}.{np.random.randint(1,255)}",
            "dest_ip": "10.0.0.1",
            "agent": f"agent-{np.random.randint(1,10)}",
            "risk_score": np.random.randint(0, 100)
        })

    df_raw = pd.DataFrame(rows)
    df = clean_dataframe(df_raw)

    st.session_state.df_raw = df_raw
    st.session_state.df = df
    st.session_state.load_mode = "simulated"

    st.success(f"✅ {len(df)} logs simulés générés")
    st.caption(f"🕒 Généré le {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


# ==========================================================
# CSV LOADER
# ==========================================================
def load_csv_data(uploaded_file):
    df_raw = pd.read_csv(uploaded_file)

    rename_map = {
        "timestamp": "@timestamp",
        "time": "@timestamp",
        "source_ip": "src_ip",
        "destination_ip": "dest_ip",
        "severity": "risk_score"
    }
    df_raw.rename(columns=rename_map, inplace=True)

    defaults = {
        "@timestamp": datetime.now(),
        "type": "csv_event",
        "src_ip": "0.0.0.0",
        "dest_ip": "0.0.0.0",
        "agent": "csv-agent",
        "risk_score": 0
    }

    for col, default in defaults.items():
        if col not in df_raw.columns:
            df_raw[col] = default

    df = clean_dataframe(df_raw)

    st.session_state.df_raw = df_raw
    st.session_state.df = df
    st.session_state.load_mode = "csv"

    st.success(f"✅ {len(df)} lignes chargées depuis le CSV")


# ==========================================================
# PAGE CONFIG
# ==========================================================
st.set_page_config(
    page_title="Data Explorer",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Explorateur de Données Wazuh")


# ==========================================================
# SIDEBAR
# ==========================================================
with st.sidebar:
    st.header("⚙️ Paramètres")

    load_mode = st.radio(
        "Mode de chargement",
        ["📤 Depuis Wazuh", "🎲 Données simulées", "📄 Fichier CSV"]
    )

    num_logs = st.slider(
        "Nombre de logs",
        100, 2000, 500, 100
    )

    uploaded_file = None
    if load_mode == "📄 Fichier CSV":
        uploaded_file = st.file_uploader("Importer un fichier CSV", type=["csv"])

    if load_mode == "🎲 Données simulées":
        st.subheader("🎭 Répartition des événements")
        ssh_ratio = st.slider("SSH", 0.0, 1.0, 0.3, 0.1)
        http_ratio = st.slider("HTTP", 0.0, 1.0, 0.4, 0.1)
        firewall_ratio = st.slider("Firewall", 0.0, 1.0, 0.2, 0.1)
    else:
        ssh_ratio = http_ratio = firewall_ratio = 0.0


    refresh = st.button("🔄 Charger les données", use_container_width=True)


# ==========================================================
# SESSION STATE INIT
# ==========================================================
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame()
    st.session_state.last_update = None


# ==========================================================
# LOAD DATA (🔥 FIXED LOGIC 🔥)
# ==========================================================
if refresh or st.session_state.df.empty:

    with st.spinner("Chargement des données..."):

        if load_mode == "📤 Depuis Wazuh":
            connector = get_wazuh_connector()
            logs, error = connector.fetch_alerts(size=num_logs)

            if error:
                st.error(f"❌ OpenSearch error: {error}")
                st.stop()

            if not logs:
                st.warning("⚠️ Aucun log trouvé dans Wazuh (index vide)")
                st.stop()

            df_raw = connector.logs_to_dataframe(logs)
            df = clean_dataframe(df_raw)

            st.session_state.df_raw = df_raw
            st.session_state.df = df
            st.session_state.load_mode = "wazuh"

            st.success(f"✅ {len(df)} logs chargés depuis Wazuh (OpenSearch)")

        elif load_mode == "📄 Fichier CSV":
            if uploaded_file is None:
                st.info("📂 Veuillez importer un fichier CSV")
                st.stop()
            load_csv_data(uploaded_file)

        else:
            generate_simulated_data(num_logs, ssh_ratio, http_ratio, firewall_ratio)



# ==========================================================
# DISPLAY
# ==========================================================
df = st.session_state.df

if df.empty:
    st.info("👈 Cliquez sur **Charger les données**")
    st.stop()


# ==========================================================
# STATUS BANNER
# ==========================================================
if st.session_state.load_mode == "wazuh":
    st.success("🟢 Données réelles depuis Wazuh (OpenSearch)")
elif st.session_state.load_mode == "csv":
    st.info("📄 Données chargées depuis un fichier CSV")
else:
    st.warning("🟡 Données simulées utilisées")


# ==========================================================
# METRICS
# ==========================================================
stats = get_summary_stats(df)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total logs", stats["total_records"])
col2.metric("IPs uniques", stats.get("unique_sources", 0))
col3.metric("Types", stats.get("unique_types", 0))
col4.metric("Risk moyen", f"{stats.get('avg_risk', 0):.1f}")


# ==========================================================
# TABS
# ==========================================================
tab1, tab2, tab3 = st.tabs(["📋 Tableau", "📊 Visualisations", "💾 Export"])

with tab1:
    st.dataframe(df.head(200), use_container_width=True)

with tab2:
    if "type" in df.columns:
        st.plotly_chart(
            px.bar(df["type"].value_counts(), title="Types d'événements"),
            use_container_width=True
        )

    if "risk_score" in df.columns:
        st.plotly_chart(
            px.histogram(df, x="risk_score", nbins=20,
                         title="Distribution des Risk Scores"),
            use_container_width=True
        )

with tab3:
    st.download_button(
        "📥 Télécharger CSV",
        df.to_csv(index=False),
        "wazuh_data.csv",
        "text/csv"
    )
