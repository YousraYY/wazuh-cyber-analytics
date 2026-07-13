
import streamlit as st
from utils.wazuh_ml_sender import send_ml_alerts_to_wazuh
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

st.set_page_config(
    page_title="ML Predictions",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Prédictions Machine Learning")

# ==========================================================
# CHECK DATA
# ==========================================================
if "df" not in st.session_state or st.session_state.df.empty:
    st.warning("⚠️ Aucune donnée chargée")
    st.info("👉 Allez d'abord sur la page **Data Explorer**")
    st.stop()

# Préparer les données
df_original = st.session_state.df.copy()
df = prepare_data_for_ml(df_original)

# Afficher un aperçu des données
with st.expander("🔍 Aperçu des données préparées"):
    st.write(f"**Dimensions:** {df.shape[0]} lignes × {df.shape[1]} colonnes")
    st.write("**Colonnes disponibles:**")
    st.code(", ".join(df.columns.tolist()))
    
    # Vérifier les types de données
    st.write("**Types de données:**")
    type_info = pd.DataFrame({
        'Colonne': df.columns,
        'Type': df.dtypes.astype(str),
        'Valeurs uniques': df.nunique()
    })
    st.dataframe(type_info.head(10), use_container_width=True)

# ==========================================================
# MODEL STATUS
# ==========================================================
st.markdown("### 🔧 Modèle Machine Learning")

try:
    import joblib
    joblib_available = True
except ImportError:
    joblib_available = False

uploaded_model = st.file_uploader(
    "📤 Charger un modèle ML (.joblib) (optionnel)",
    type=["joblib"]
)

if uploaded_model and joblib_available:
    st.success("✅ Modèle ML chargé")
elif not joblib_available:
    st.warning("⚠️ joblib non installé → mode simulation")
else:
    st.info("ℹ️ Aucun modèle chargé → mode simulation")

# ==========================================================
# LOAD / GENERATE PREDICTIONS BUTTON  ✅ IMPORTANT
# ==========================================================
st.markdown("---")

if st.button("🚀 Charger / Générer les prédictions", type="primary"):
    with st.spinner("🔄 Génération des prédictions..."):

        df_pred = df.copy()

        # ------------------------------
        # REAL MODEL
        # ------------------------------
        if uploaded_model and joblib_available:
            try:
                model = joblib.load(uploaded_model)

                numeric_df = df_pred.select_dtypes(include=[np.number]).fillna(0)

                preds = model.predict(numeric_df)

                if hasattr(model, "predict_proba"):
                    probs = model.predict_proba(numeric_df).max(axis=1)
                else:
                    probs = np.random.uniform(0.7, 0.99, size=len(df_pred))

                df_pred["ml_prediction"] = np.where(preds == 1, "Attack", "Normal")
                df_pred["confidence"] = (probs * 100).round(2)
                df_pred["risk_score"] = (df_pred["confidence"]).astype(int)

                st.success("✅ Prédictions ML réelles générées")

            except Exception as e:
                st.error(f"❌ Erreur modèle ML : {e}")
                st.info("👉 Passage automatique en simulation")

                uploaded_model = None  # fallback

        # ------------------------------
        # SIMULATION MODE
        # ------------------------------
        if not uploaded_model:
            np.random.seed(42)

            df_pred["ml_prediction"] = np.random.choice(
                ["Normal", "Attack"],
                size=len(df_pred),
                p=[0.8, 0.2]
            )

            df_pred["risk_score"] = np.where(
                df_pred["ml_prediction"] == "Normal",
                np.random.randint(0, 40, size=len(df_pred)),
                np.random.randint(60, 100, size=len(df_pred))
            )

            df_pred["confidence"] = np.random.uniform(70, 99, size=len(df_pred)).round(2)

            st.success("✅ Prédictions simulées générées")

        # SAVE RESULTS
        st.session_state.df_predictions = df_pred


# ==========================================================
# RESULTS (ONLY IF EXIST)
# ==========================================================
if "df_predictions" not in st.session_state:
    st.info("👆 Cliquez sur **Charger / Générer les prédictions**")
    st.stop()

df_pred = st.session_state.df_predictions

st.markdown("---")
st.markdown("### 📊 Résultats des prédictions")

# ==========================================================
# METRICS
# ==========================================================
total = len(df_pred)
normal = (df_pred["ml_prediction"] == "Normal").sum()
attack = (df_pred["ml_prediction"] == "Attack").sum()

c1, c2, c3 = st.columns(3)
c1.metric("📊 Total événements", total)
c2.metric("✅ Normaux", normal, f"{normal/total*100:.1f}%")
c3.metric("🔴 Attaques", attack, f"{attack/total*100:.1f}%")

# ==========================================================
# TABS
# ==========================================================
tab1, tab2, tab3 = st.tabs(["📊 Distribution", "🎯 Top risques", "💾 Export"])

with tab1:
    fig = px.pie(
        df_pred,
        names="ml_prediction",
        title="Distribution des prédictions",
        color="ml_prediction",
        color_discrete_map={"Normal": "#28a745", "Attack": "#dc3545"}
    )
    st.plotly_chart(fig, use_container_width=True)

    fig = px.histogram(
        df_pred,
        x="risk_score",
        color="ml_prediction",
        nbins=40,
        title="Distribution des Risk Scores",
        color_discrete_map={"Normal": "#28a745", "Attack": "#dc3545"}
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.dataframe(
        df_pred.sort_values("risk_score", ascending=False)
        .head(20)[["ml_prediction", "risk_score", "confidence"]],
        use_container_width=True
    )

with tab3:
    csv = df_pred.to_csv(index=False)
    st.download_button(
        "📥 Télécharger CSV",
        csv,
        f"ml_predictions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        "text/csv"
    )

# ==========================================================
# SEND ML ALERTS TO WAZUH
# ==========================================================
st.markdown("---")
st.markdown("### 🚨 Envoyer les alertes ML vers Wazuh")

st.info(
    "Les alertes seront envoyées vers l'index **wazuh-ml-alerts** "
    "avec les champs ML (prediction, risk_score, confidence)."
)

if st.button("📤 Envoyer les alertes ML à Wazuh", type="secondary"):
    with st.spinner("📡 Envoi des alertes vers Wazuh..."):

        # SAFETY CHECK
        required_cols = {"ml_prediction", "risk_score", "confidence"}
        if not required_cols.issubset(df_pred.columns):
            st.error("❌ Prédictions ML manquantes — générez-les d'abord")
            st.stop()

        sent, failed = send_ml_alerts_to_wazuh(df_pred)

    st.success(f"✅ {sent} alertes envoyées à Wazuh")
    if failed > 0:
        st.warning(f"⚠️ {failed} alertes ont échoué")

