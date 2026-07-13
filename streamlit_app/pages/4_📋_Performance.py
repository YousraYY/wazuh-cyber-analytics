import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Performance", page_icon="📋", layout="wide")

st.title("📋 Rapport de Performance ML")

# =========================
# CHECK DATA
# =========================
if "df_predictions" not in st.session_state:
    st.warning("⚠️ Aucune prédiction disponible")
    st.info("👉 Générez d'abord des prédictions sur la page **ML Predictions**")
    st.stop()

df_pred = st.session_state.df_predictions.copy()

# =========================
# TIMESTAMP HANDLING (CRITICAL FIX)
# =========================
if "@timestamp" in df_pred.columns:
    TIME_COL = "@timestamp"
elif "timestamp" in df_pred.columns:
    TIME_COL = "timestamp"
else:
    TIME_COL = None

if TIME_COL:
    df_pred[TIME_COL] = pd.to_datetime(df_pred[TIME_COL], errors="coerce")

# =========================
# METRICS
# =========================
total = len(df_pred)
normal = (df_pred["ml_prediction"] == "Normal").sum()
attack = (df_pred["ml_prediction"] == "Attack").sum()
avg_risk = df_pred["risk_score"].mean()
high_risk = (df_pred["risk_score"] >= 70).sum()
detection_rate = (attack / total * 100) if total else 0

st.markdown("### 🎯 Métriques Globales")

c1, c2, c3, c4 = st.columns(4)
c1.metric("📊 Total événements", total)
c2.metric("🔍 Taux de détection", f"{detection_rate:.1f}%")
c3.metric("⚠️ Risk moyen", f"{avg_risk:.1f}")
c4.metric("🔴 Événements critiques", high_risk)

# =========================
# TABS
# =========================
tab1, tab2, tab3 = st.tabs([
    "📊 Distribution",
    "📈 Analyse temporelle",
    "💾 Rapport"
])

# =========================
# TAB 1 – DISTRIBUTION
# =========================
with tab1:
    st.markdown("### 📊 Distribution des prédictions")

    col1, col2 = st.columns(2)

    with col1:
        fig = px.pie(
            df_pred,
            names="ml_prediction",
            title="Normal vs Attack",
            color="ml_prediction",
            color_discrete_map={
                "Normal": "#2ecc71",
                "Attack": "#e74c3c"
            }
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.histogram(
            df_pred,
            x="risk_score",
            nbins=25,
            title="Distribution des Risk Scores"
        )
        st.plotly_chart(fig, use_container_width=True)

# =========================
# TAB 2 – TEMPORAL
# =========================
with tab2:
    st.markdown("### 📈 Analyse temporelle")

    if TIME_COL:
        df_time = df_pred.dropna(subset=[TIME_COL]).copy()
        df_time["hour"] = df_time[TIME_COL].dt.hour

        attacks_per_hour = (
            df_time[df_time["ml_prediction"] == "Attack"]
            .groupby("hour")
            .size()
            .reset_index(name="count")
        )

        fig = px.line(
            attacks_per_hour,
            x="hour",
            y="count",
            title="Attaques par heure",
            markers=True
        )
        st.plotly_chart(fig, use_container_width=True)

        # Timeline events critiques
        critical = df_time[df_time["risk_score"] >= 70].sort_values(TIME_COL)

        if not critical.empty:
            fig = px.scatter(
                critical.head(100),
                x=TIME_COL,
                y="risk_score",
                size="risk_score",
                color="risk_score",
                title="Timeline des événements critiques",
                color_continuous_scale="Reds"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucun événement critique")
    else:
        st.warning("Aucune colonne temporelle disponible")

# =========================
# TAB 3 – REPORT & EXPORT
# =========================
with tab3:
    st.markdown("### 💾 Rapport de performance")

    report = f"""
# Rapport ML – Wazuh

Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Total événements: {total}
Normaux: {normal}
Attaques: {attack}
Taux de détection: {detection_rate:.1f}%

Risk score moyen: {avg_risk:.2f}
Événements critiques: {high_risk}
"""

    st.code(report, language="markdown")

    export_cols = ["ml_prediction", "risk_score", "confidence"]
    if TIME_COL:
        export_cols.insert(0, TIME_COL)

    csv = df_pred[export_cols].to_csv(index=False)
    st.download_button(
        "📥 Télécharger CSV",
        csv,
        f"performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        "text/csv"
    )

# =========================
# FOOTER
# =========================
st.markdown("---")
st.caption("🤖 Analyse ML – Wazuh Cyber Analytics")
