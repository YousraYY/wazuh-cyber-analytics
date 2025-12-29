# pages/3_🤖_ML_Predictions.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils.ml_model import get_ml_model
from datetime import datetime

st.set_page_config(page_title="ML Predictions", page_icon="🤖", layout="wide")

st.title("🤖 Prédictions Machine Learning")

# Vérifier si des données sont disponibles
if 'df' not in st.session_state or st.session_state.df.empty:
    st.warning("⚠️ Aucune donnée chargée")
    st.info("👉 Allez d'abord sur la page 'Data Explorer' pour charger les données")
    st.stop()

df = st.session_state.df.copy()

# Section : Charger le modèle
st.markdown("### 🔧 Modèle Machine Learning")

ml_handler = get_ml_model()

col1, col2 = st.columns([2, 1])

with col1:
    # Upload du modèle
    uploaded_model = st.file_uploader(
        "📤 Charger le modèle ML (.joblib)",
        type=['joblib'],
        help="Modèle entraîné par l'Étudiant 2"
    )
    
    if uploaded_model:
        if st.button("🔄 Charger le modèle", type="primary"):
            with st.spinner("Chargement du modèle..."):
                success, message = ml_handler.load_model(uploaded_model)
                
                if success:
                    st.success(message)
                else:
                    st.error(message)

with col2:
    st.markdown("#### État du modèle")
    if ml_handler.is_loaded:
        st.success("✅ Modèle chargé")
    else:
        st.warning("⚠️ Aucun modèle")

# Génération de prédictions
st.markdown("---")

if ml_handler.is_loaded:
    st.markdown("### 🚀 Générer les prédictions avec le modèle ML")
    
    if st.button("🔮 Prédire avec le modèle ML", type="primary", key="real_predict"):
        with st.spinner("🔄 Génération des prédictions..."):
            try:
                # Utiliser le VRAI modèle
                predictions, probas, risk_scores = ml_handler.predict(df)
                
                # Ajouter au DataFrame
                df['ml_prediction'] = predictions
                df['risk_score'] = risk_scores
                df['confidence'] = probas.max(axis=1) * 100
                
                # Classification par risk score
                df['threat_level'] = df['risk_score'].apply(
                    lambda x: 'Normal' if x < 30 else 'Suspicious' if x < 70 else 'Critical'
                )
                
                # Sauvegarder
                st.session_state.df_predictions = df
                
                st.success("✅ Prédictions générées avec le modèle ML !")
                
            except Exception as e:
                st.error(f"❌ Erreur lors de la prédiction : {str(e)}")
                st.info("💡 Vérifiez que les données contiennent les colonnes nécessaires")

else:
    st.markdown("### 🎲 Simulation (pas de modèle chargé)")
    st.info("👆 Chargez le modèle ML ci-dessus pour utiliser les vraies prédictions")
    
    # Garder la simulation pour les tests
    if st.button("🚀 Générer des prédictions simulées", type="secondary"):
        with st.spinner("🔄 Génération des prédictions simulées..."):
            np.random.seed(42)
            
            predictions = np.random.choice(
                ['Normal', 'Attack'],
                size=len(df),
                p=[0.8, 0.2]
            )
            
            risk_scores = np.random.randint(0, 100, size=len(df))
            risk_scores[predictions == 'Normal'] = np.random.randint(0, 40, size=np.sum(predictions == 'Normal'))
            risk_scores[predictions == 'Attack'] = np.random.randint(60, 100, size=np.sum(predictions == 'Attack'))
            
            df['ml_prediction'] = predictions
            df['risk_score'] = risk_scores
            df['confidence'] = np.random.uniform(70, 99, size=len(df))
            
            st.session_state.df_predictions = df
            st.success("✅ Prédictions simulées générées !")

# Afficher les résultats
if 'df_predictions' in st.session_state:
    df_pred = st.session_state.df_predictions
    
    st.markdown("---")
    st.markdown("### 📊 Résultats des prédictions")
    
    # Métriques
    col1, col2, col3 = st.columns(3)
    
    total = len(df_pred)
    normal = (df_pred['ml_prediction'] == 'Normal').sum()
    attack = (df_pred['ml_prediction'] == 'Attack').sum()
    
    with col1:
        st.metric("📊 Total d'événements", total)
    
    with col2:
        st.metric("✅ Normal", normal, delta=f"{normal/total*100:.1f}%")
    
    with col3:
        st.metric("🔴 Attaques", attack, delta=f"{attack/total*100:.1f}%", delta_color="inverse")
    
    # Graphiques
    tab1, tab2, tab3 = st.tabs(["📊 Distribution", "🎯 Risk Scores", "💾 Export"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            # Distribution des prédictions
            pred_counts = df_pred['ml_prediction'].value_counts()
            
            fig = px.pie(
                values=pred_counts.values,
                names=pred_counts.index,
                title='Distribution des prédictions',
                color_discrete_map={
                    'Normal': '#28a745',
                    'Attack': '#dc3545'
                },
                hole=0.4
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Distribution des risk scores
            fig = px.histogram(
                df_pred,
                x='risk_score',
                color='ml_prediction',
                nbins=50,
                title='Distribution des Risk Scores',
                color_discrete_map={
                    'Normal': '#28a745',
                    'Attack': '#dc3545'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.markdown("#### 🔴 Top 20 événements à haut risque")
        
        # Colonnes à afficher
        display_cols = ['timestamp', 'ml_prediction', 'risk_score', 'confidence']
        
        # Ajouter rule description si disponible
        if 'rule' in df_pred.columns:
            try:
                df_pred['rule_desc'] = df_pred['rule'].apply(
                    lambda x: x.get('description', 'N/A')[:60] if isinstance(x, dict) else 'N/A'
                )
                display_cols.append('rule_desc')
            except:
                pass
        
        top_risks = df_pred.nlargest(20, 'risk_score')[display_cols]
        st.dataframe(top_risks, use_container_width=True)
    
    with tab3:
        st.markdown("#### 💾 Exporter les résultats")
        
        # Préparer l'export
        export_df = df_pred[['timestamp', 'ml_prediction', 'risk_score', 'confidence']].copy()
        
        # CSV
        csv = export_df.to_csv(index=False)
        st.download_button(
            "📥 Télécharger en CSV",
            csv,
            f"predictions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "text/csv"
        )
        
        # JSON pour Wazuh
        json_data = export_df.to_json(orient='records', date_format='iso')
        st.download_button(
            "📥 Télécharger en JSON",
            json_data,
            f"predictions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "application/json"
        )

else:
    st.info("👆 Générez des prédictions pour voir les résultats")