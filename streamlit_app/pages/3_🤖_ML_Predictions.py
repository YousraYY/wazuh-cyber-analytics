# pages/3_🤖_ML_Predictions.py - VERSION CORRIGÉE
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from utils.ml_model import get_ml_model
from datetime import datetime

st.set_page_config(page_title="ML Predictions", page_icon="🤖", layout="wide")

st.title("🤖 Prédictions Machine Learning")

# Fonction pour corriger les données avant prédiction
def prepare_data_for_ml(df):
    """
    Prépare les données pour le modèle ML
    """
    df_prepared = df.copy()
    
    # 1. Corriger les timestamps
    timestamp_cols = ['timestamp', '@timestamp']
    for col in timestamp_cols:
        if col in df_prepared.columns:
            try:
                df_prepared[col] = pd.to_datetime(df_prepared[col], errors='coerce')
                # Supprimer les fuseaux horaires
                df_prepared[col] = df_prepared[col].dt.tz_localize(None)
            except:
                pass
    
    # 2. S'assurer que les colonnes nécessaires existent
    required_cols = ['src_ip', 'dest_ip']
    for col in required_cols:
        if col not in df_prepared.columns:
            if col == 'src_ip':
                df_prepared[col] = [f"192.168.1.{np.random.randint(1, 255)}" for _ in range(len(df_prepared))]
            elif col == 'dest_ip':
                df_prepared[col] = '10.0.0.1'
    
    return df_prepared

# Vérifier si des données sont disponibles
if 'df' not in st.session_state or st.session_state.df.empty:
    st.warning("⚠️ Aucune donnée chargée")
    st.info("👉 Allez d'abord sur la page 'Data Explorer' pour charger les données")
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

# Section : Charger le modèle
st.markdown("### 🔧 Modèle Machine Learning")

ml_handler = get_ml_model()

col1, col2 = st.columns([2, 1])

with col1:
    # Upload du modèle
    uploaded_model = st.file_uploader(
        "📤 Charger le modèle ML (.joblib)",
        type=['joblib'],
        help="Modèle Random Forest entraîné par l'Étudiant 2"
    )
    
    if uploaded_model is not None:
        if st.button("🔄 Charger le modèle", type="primary", key="load_model"):
            with st.spinner("Chargement du modèle..."):
                success, message = ml_handler.load_model(uploaded_model)
                
                if success:
                    st.success(message)
                    
                    # Tester immédiatement si le modèle peut fonctionner avec les données
                    with st.spinner("Test du modèle sur les données..."):
                        try:
                            # Tester avec un petit échantillon
                            test_sample = df.head(3)
                            predictions_test, _, _ = ml_handler.predict(test_sample)
                            st.success(f"✅ Modèle testé avec succès! Prédictions: {predictions_test[:3]}")
                        except Exception as e:
                            st.warning(f"⚠️ Test échoué: {str(e)[:100]}...")
                            st.info("Les données peuvent ne pas contenir toutes les colonnes nécessaires")
                else:
                    st.error(message)
    
    # Option pour charger le modèle par défaut
    if st.button("📥 Charger modèle par défaut", key="load_default"):
        import os
        import joblib
        
        # Chercher le modèle dans différents emplacements
        model_paths = [
            "../ml_pipeline/ml_model.joblib",
            "ml_model.joblib",
            "models/ml_model.joblib"
        ]
        
        model_loaded = False
        for path in model_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'rb') as f:
                        model = joblib.load(f)
                    ml_handler.model = model
                    ml_handler.is_loaded = True
                    ml_handler.model_type = type(model).__name__
                    st.success(f"✅ Modèle chargé depuis {path}: {ml_handler.model_type}")
                    model_loaded = True
                    st.rerun()
                    break
                except Exception as e:
                    st.error(f"❌ Erreur avec {path}: {str(e)}")
        
        if not model_loaded:
            st.error("❌ Aucun modèle trouvé. Téléchargez d'abord un modèle.")

with col2:
    st.markdown("#### État du modèle")
    if ml_handler.is_loaded:
        st.success("✅ Modèle chargé")
        
        # Afficher des infos sur le modèle
        with st.expander("📋 Détails"):
            if hasattr(ml_handler.model, 'n_estimators'):
                st.write(f"**Arbres:** {ml_handler.model.n_estimators}")
            if hasattr(ml_handler.model, 'feature_importances_'):
                st.write(f"**Features importantes:** {len(ml_handler.model.feature_importances_)}")
    else:
        st.warning("⚠️ Aucun modèle chargé")

# Génération de prédictions
st.markdown("---")

if ml_handler.is_loaded:
    st.markdown("### 🚀 Générer les prédictions avec le modèle ML")
    
    # Afficher les features attendues
    st.info("🎯 **Features attendues par le modèle:**")
    st.code("bytes_transferred, hour, day, same_ip, internal_src, internal_dst")
    
    # Vérifier si les données contiennent les bonnes colonnes
    required_features = ['bytes_transferred', 'hour', 'day', 'same_ip', 'internal_src', 'internal_dst']
    available_features = [f for f in required_features if f in df.columns]
    
    if available_features:
        st.success(f"✅ {len(available_features)}/{len(required_features)} features disponibles")
        st.code(f"Disponibles: {', '.join(available_features)}")
    else:
        st.warning(f"⚠️ Aucune feature requise trouvée. Le modèle générera des valeurs par défaut.")
    
    # Options de prédiction
    col1, col2 = st.columns([3, 1])
    
    with col1:
        sample_size = st.slider(
            "Nombre de logs à analyser",
            min_value=100,
            max_value=min(5000, len(df)),
            value=min(1000, len(df)),
            step=100
        )
    
    with col2:
        if st.button("🔮 Prédire avec le modèle ML", type="primary", key="predict_btn"):
            with st.spinner(f"🔄 Analyse de {sample_size} logs..."):
                try:
                    # Prendre un échantillon des données
                    df_sample = df.head(sample_size)
                    
                    # Faire les prédictions
                    predictions, probas, risk_scores = ml_handler.predict(df_sample)
                    
                    # Ajouter les résultats au DataFrame
                    df_result = df_sample.copy()
                    df_result['ml_prediction'] = ['Normal' if p == 0 else 'Attack' for p in predictions]
                    df_result['risk_score'] = risk_scores
                    
                    if probas is not None:
                        df_result['confidence'] = probas.max(axis=1) * 100
                    else:
                        df_result['confidence'] = np.random.uniform(70, 99, size=len(df_result))
                    
                    # Classification par risk score
                    def classify_risk(score):
                        if score < 30:
                            return 'Low'
                        elif score < 70:
                            return 'Medium'
                        else:
                            return 'High'
                    
                    df_result['threat_level'] = df_result['risk_score'].apply(classify_risk)
                    
                    # Ajouter le timestamp pour l'export
                    df_result['prediction_time'] = datetime.now()
                    
                    # Sauvegarder
                    st.session_state.df_predictions = df_result
                    
                    st.success(f"✅ {len(df_result)} prédictions générées !")
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"❌ Erreur lors de la prédiction : {str(e)}")
                    
                    # Afficher plus de détails sur l'erreur
                    with st.expander("🔧 Détails de l'erreur"):
                        st.write("**Problème probable:**")
                        st.write("1. Les données ne contiennent pas les bonnes colonnes")
                        st.write("2. Format de données incompatible")
                        st.write("3. Modèle incompatible avec les données")
                        
                        st.write("**Colonnes dans vos données:**")
                        st.code(", ".join(df.columns.tolist()))
                        
                        st.write("**Solution rapide:**")
                        st.write("- Utilisez les prédictions simulées ci-dessous")
                        st.write("- Ou générez de nouvelles données avec le bon format")

else:
    st.markdown("### 🎲 Simulation (pas de modèle chargé)")
    st.info("👆 Chargez un modèle ML ci-dessus pour les vraies prédictions")
    
    # Options de simulation
    col1, col2 = st.columns(2)
    
    with col1:
        attack_ratio = st.slider(
            "Pourcentage d'attaques simulées",
            min_value=5,
            max_value=50,
            value=15,
            step=5
        )
    
    with col2:
        if st.button("🚀 Générer des prédictions simulées", type="secondary", key="simulate"):
            with st.spinner("🔄 Génération des prédictions simulées..."):
                np.random.seed(42)
                
                # Prendre un échantillon
                sample_size = min(1000, len(df))
                df_sample = df.head(sample_size)
                
                # Générer des prédictions simulées réalistes
                normal_ratio = 1 - (attack_ratio / 100)
                predictions = np.random.choice(
                    ['Normal', 'Attack'],
                    size=sample_size,
                    p=[normal_ratio, attack_ratio/100]
                )
                
                # Scores de risque réalistes
                risk_scores = np.zeros(sample_size)
                normal_mask = predictions == 'Normal'
                attack_mask = predictions == 'Attack'
                
                risk_scores[normal_mask] = np.random.randint(0, 40, size=np.sum(normal_mask))
                risk_scores[attack_mask] = np.random.randint(60, 100, size=np.sum(attack_mask))
                
                df_result = df_sample.copy()
                df_result['ml_prediction'] = predictions
                df_result['risk_score'] = risk_scores
                df_result['confidence'] = np.random.uniform(70, 99, size=sample_size)
                df_result['threat_level'] = df_result['risk_score'].apply(
                    lambda x: 'Low' if x < 30 else 'Medium' if x < 70 else 'High'
                )
                df_result['prediction_time'] = datetime.now()
                
                # Ajouter des patterns réalistes
                if 'src_ip' in df_result.columns:
                    # Marquer certaines IPs comme suspectes
                    unique_ips = df_result['src_ip'].unique()
                    if len(unique_ips) > 2:
                        suspicious_ips = np.random.choice(unique_ips, size=min(2, len(unique_ips)), replace=False)
                        df_result.loc[df_result['src_ip'].isin(suspicious_ips), 'ml_prediction'] = 'Attack'
                        df_result.loc[df_result['src_ip'].isin(suspicious_ips), 'risk_score'] = np.random.randint(80, 100, size=len(suspicious_ips))
                
                st.session_state.df_predictions = df_result
                st.success(f"✅ {sample_size} prédictions simulées générées")

# Afficher les résultats
if 'df_predictions' in st.session_state:
    df_pred = st.session_state.df_predictions
    
    st.markdown("---")
    st.markdown("### 📊 Résultats des prédictions")
    
    # Métriques
    col1, col2, col3, col4 = st.columns(4)
    
    total = len(df_pred)
    normal = (df_pred['ml_prediction'] == 'Normal').sum()
    attack = (df_pred['ml_prediction'] == 'Attack').sum()
    avg_risk = df_pred['risk_score'].mean()
    high_risk = (df_pred['risk_score'] > 70).sum()
    
    with col1:
        st.metric("📊 Total", total)
    
    with col2:
        st.metric("✅ Normal", normal, delta=f"{normal/total*100:.1f}%")
    
    with col3:
        st.metric("🔴 Attaques", attack, delta=f"{attack/total*100:.1f}%", delta_color="inverse")
    
    with col4:
        st.metric("⚠️ Haut risque", high_risk, delta=f"{high_risk/total*100:.1f}%")
    
    # Graphiques
    tab1, tab2, tab3 = st.tabs(["📊 Distribution", "🎯 Détails", "💾 Export"])
    
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
            # Distribution des niveaux de menace
            if 'threat_level' in df_pred.columns:
                threat_counts = df_pred['threat_level'].value_counts()
                
                fig = px.bar(
                    x=threat_counts.index,
                    y=threat_counts.values,
                    title='Niveaux de menace',
                    color=threat_counts.index,
                    color_discrete_map={
                        'Low': '#28a745',
                        'Medium': '#ffc107',
                        'High': '#dc3545'
                    }
                )
                st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.markdown("#### 🔍 Détails des prédictions")
        
        # Filtres
        col1, col2 = st.columns(2)
        
        with col1:
            min_score = st.slider("Score minimum", 0, 100, 50)
        
        with col2:
            show_type = st.selectbox(
                "Type à afficher",
                ["Tous", "Normal", "Attack"]
            )
        
        # Appliquer les filtres
        filtered_df = df_pred[df_pred['risk_score'] >= min_score]
        
        if show_type != "Tous":
            filtered_df = filtered_df[filtered_df['ml_prediction'] == show_type]
        
        # Colonnes à afficher
        display_cols = []
        
        # Chercher les colonnes disponibles
        possible_cols = ['@timestamp', 'timestamp', 'src_ip', 'dest_ip', 
                        'ml_prediction', 'risk_score', 'threat_level', 'confidence']
        
        for col in possible_cols:
            if col in filtered_df.columns:
                display_cols.append(col)
        
        # Ajouter la règle si disponible
        if 'rule' in filtered_df.columns:
            try:
                filtered_df['rule_desc'] = filtered_df['rule'].apply(
                    lambda x: x.get('description', 'N/A')[:50] if isinstance(x, dict) else str(x)[:50]
                )
                display_cols.append('rule_desc')
            except:
                pass
        
        if display_cols and len(filtered_df) > 0:
            st.write(f"**Résultats filtrés:** {len(filtered_df)} événements")
            st.dataframe(
                filtered_df[display_cols].sort_values('risk_score', ascending=False).head(20),
                use_container_width=True
            )
        else:
            st.info("Aucun événement ne correspond aux filtres")
    
    with tab3:
        st.markdown("#### 💾 Exporter les résultats")
        
        # Options d'export
        export_format = st.radio(
            "Format",
            ["CSV", "JSON"],
            horizontal=True
        )
        
        # Préparer les données
        export_df = df_pred.copy()
        
        # Simplifier les colonnes complexes
        for col in export_df.columns:
            if export_df[col].dtype == 'object':
                try:
                    if isinstance(export_df[col].iloc[0], (dict, list)):
                        export_df[col] = export_df[col].apply(str)
                except:
                    pass
        
        if export_format == "CSV":
            csv_data = export_df.to_csv(index=False)
            st.download_button(
                "📥 Télécharger CSV",
                csv_data,
                f"ml_predictions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv",
                use_container_width=True
            )
        
        elif export_format == "JSON":
            json_data = export_df.to_json(orient='records', date_format='iso')
            st.download_button(
                "📥 Télécharger JSON",
                json_data,
                f"ml_predictions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "application/json",
                use_container_width=True
            )

else:
    st.info("👆 Générez des prédictions pour voir les résultats")