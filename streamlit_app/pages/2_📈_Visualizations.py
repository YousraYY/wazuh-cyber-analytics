import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(
    page_title="Visualisations",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Visualisations Avancées")

# =========================
# CHECK DATA
# =========================
if "df" not in st.session_state or st.session_state.df.empty:
    st.warning("⚠️ Aucune donnée chargée")
    st.info("👉 Chargez d'abord les données dans **Data Explorer**")
    st.stop()

df = st.session_state.df.copy()

# =========================
# TIMESTAMP NORMALIZATION (🔥 FIX)
# =========================
time_col = "@timestamp" if "@timestamp" in df.columns else "timestamp"

df[time_col] = pd.to_datetime(
    df[time_col],
    errors="coerce",
    utc=True
)

df = df.dropna(subset=[time_col])

# =========================
# SIDEBAR FILTER
# =========================
with st.sidebar:
    st.header("🔧 Filtres")

    min_date = df[time_col].min().date()
    max_date = df[time_col].max().date()

    start_date, end_date = st.date_input(
        "Plage de dates",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    start_dt = pd.Timestamp(start_date, tz="UTC")
    end_dt = pd.Timestamp(end_date, tz="UTC") + pd.Timedelta(days=1)

    df = df[(df[time_col] >= start_dt) & (df[time_col] < end_dt)]

    st.metric("Logs filtrés", len(df))

# =========================
# TABS
# =========================
tab1, tab2 = st.tabs(["⏰ Temporel", "📊 Statistiques"])

# =========================
# TAB 1 — TEMPORAL
# =========================
with tab1:
    st.subheader("⏰ Activité par heure")

    df["hour"] = df[time_col].dt.hour
    hourly = df.groupby("hour").size().reset_index(name="count")

    fig = px.bar(
        hourly,
        x="hour",
        y="count",
        title="Nombre d'événements par heure",
        labels={"hour": "Heure", "count": "Événements"}
    )
    st.plotly_chart(fig, use_container_width=True)

# =========================
# TAB 2 — STATS
# =========================
with tab2:
    col1, col2, col3 = st.columns(3)

    col1.metric("Total événements", len(df))
    col2.metric("IPs uniques", df.get("source_ip", df.get("src_ip")).nunique())
    col3.metric("Types uniques", df.get("log_type", df.get("type")).nunique())

# =========================
# EXPORT
# =========================
st.markdown("---")
csv = df.to_csv(index=False)
st.download_button(
    "📥 Télécharger CSV",
    csv,
    f"wazuh_visualisations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
    "text/csv"
)
