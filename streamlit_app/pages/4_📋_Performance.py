# pages/4_📋_Performance.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Performance", page_icon="📋", layout="wide")

st.title("📋 Rapport de Performance ML")

# Vérifier si des prédictions existent
if 'df_predictions' not in st.session_state:
    st.warning("⚠️ Aucune prédiction disponible")
    st.info("👉 Générez d'abord des prédictions sur la page 'ML Predictions'")
    st.stop()

df_pred = st.session_state.df_predictions

# Calculer les métriques
total = len(df_pred)
normal = (df_pred['ml_prediction'] == 'Normal').sum()
attack = (df_pred['ml_prediction'] == 'Attack').sum()

# Métriques globales
st.markdown("### 🎯 Métriques Globales")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("📊 Total événements", total)

with col2:
    detection_rate = (attack / total * 100) if total > 0 else 0
    st.metric("🔍 Taux de détection", f"{detection_rate:.1f}%")

with col3:
    avg_risk = df_pred['risk_score'].mean()
    st.metric("⚠️ Risk score moyen", f"{avg_risk:.1f}")

with col4:
    high_risk = (df_pred['risk_score'] >= 70).sum()
    st.metric("🔴 Événements critiques", high_risk)

# Tabs
tab1, tab2, tab3 = st.tabs(["📊 Distribution", "📈 Analyse temporelle", "💾 Rapport"])

with tab1:
    st.markdown("### 📊 Distribution des prédictions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Pie chart
        pred_counts = df_pred['ml_prediction'].value_counts()
        
        fig = px.pie(
            values=pred_counts.values,
            names=pred_counts.index,
            title='Répartition Normal vs Attack',
            color_discrete_map={
                'Normal': '#28a745',
                'Attack': '#dc3545'
            }
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Histogramme des risk scores
        fig = px.histogram(
            df_pred,
            x='risk_score',
            nbins=20,
            title='Distribution des Risk Scores',
            color_discrete_sequence=['#ff7f0e']
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Tableau de distribution détaillée
    st.markdown("#### 📋 Distribution détaillée par niveau de risque")
    
    df_pred['risk_category'] = pd.cut(
        df_pred['risk_score'],
        bins=[0, 30, 70, 100],
        labels=['Faible (0-30)', 'Moyen (30-70)', 'Élevé (70-100)']
    )
    
    risk_dist = df_pred['risk_category'].value_counts().sort_index()
    
    dist_df = pd.DataFrame({
        'Catégorie': risk_dist.index,
        'Nombre': risk_dist.values,
        'Pourcentage': (risk_dist.values / total * 100).round(1)
    })
    
    st.dataframe(dist_df, use_container_width=True)

with tab2:
    st.markdown("### 📈 Évolution temporelle")
    
    if 'timestamp' in df_pred.columns:
        df_pred['timestamp'] = pd.to_datetime(df_pred['timestamp'], errors='coerce')
        df_pred['hour'] = df_pred['timestamp'].dt.hour
        
        # Attaques par heure
        attacks_per_hour = df_pred[df_pred['ml_prediction'] == 'Attack'].groupby('hour').size()
        
        # Convertir en DataFrame pour Plotly
        df_plot = pd.DataFrame({
            'Heure': attacks_per_hour.index,
            'Nombre d\'attaques': attacks_per_hour.values
        })
        
        fig = px.line(
            df_plot,
            x='Heure',
            y='Nombre d\'attaques',
            title='Nombre d\'attaques par heure',
            markers=True
        )
        
        fig.update_layout(
            xaxis_title='Heure du jour',
            yaxis_title='Nombre d\'attaques détectées',
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Statistiques supplémentaires
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if len(attacks_per_hour) > 0:
                peak_hour = attacks_per_hour.idxmax()
                peak_count = attacks_per_hour.max()
                st.metric(
                    "🔥 Heure de pic",
                    f"{peak_hour}h",
                    f"{peak_count} attaques"
                )
            else:
                st.metric("🔥 Heure de pic", "N/A")
        
        with col2:
            total_attacks = attacks_per_hour.sum()
            st.metric(
                "📊 Total attaques",
                total_attacks
            )
        
        with col3:
            if len(attacks_per_hour) > 0:
                avg_per_hour = attacks_per_hour.mean()
                st.metric(
                    "📈 Moyenne/heure",
                    f"{avg_per_hour:.1f}"
                )
            else:
                st.metric("📈 Moyenne/heure", "0")
        
        # Timeline des événements critiques
        st.markdown("#### 🔴 Timeline des événements critiques (risk ≥ 70)")
        
        critical_events = df_pred[df_pred['risk_score'] >= 70].sort_values('timestamp')
        
        if len(critical_events) > 0:
            # Créer un scatter plot temporel
            fig = px.scatter(
                critical_events.head(100),  # Limiter à 100 pour la lisibilité
                x='timestamp',
                y='risk_score',
                color='risk_score',
                size='risk_score',
                title='Timeline des 100 premiers événements critiques',
                color_continuous_scale='Reds',
                hover_data=['ml_prediction']
            )
            
            fig.update_layout(
                xaxis_title='Temps',
                yaxis_title='Risk Score',
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucun événement critique détecté")
            
    else:
        st.info("Pas de données temporelles disponibles")

with tab3:
    st.markdown("### 💾 Rapport de performance")
    
    # Calculer des statistiques avancées
    if len(df_pred) > 0:
        # Statistiques par catégorie
        stats_by_category = df_pred.groupby('ml_prediction').agg({
            'risk_score': ['mean', 'min', 'max', 'std'],
            'confidence': 'mean'
        }).round(2)
        
        st.markdown("#### 📊 Statistiques par catégorie")
        st.dataframe(stats_by_category, use_container_width=True)
    
    # Générer un rapport texte
    report = f"""
# Rapport d'Analyse ML - Wazuh Cybersécurité
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 Résumé Exécutif

Total d'événements analysés: {total}
- Événements normaux: {normal} ({normal/total*100:.1f}%)
- Attaques détectées: {attack} ({attack/total*100:.1f}%)

## ⚠️ Analyse des Risques

Risk Score Statistics:
- Score moyen: {avg_risk:.2f}/100
- Score minimum: {df_pred['risk_score'].min():.2f}
- Score maximum: {df_pred['risk_score'].max():.2f}
- Écart-type: {df_pred['risk_score'].std():.2f}

Distribution par niveau:
- Risque faible (0-30): {(df_pred['risk_score'] < 30).sum()} événements
- Risque moyen (30-70): {((df_pred['risk_score'] >= 30) & (df_pred['risk_score'] < 70)).sum()} événements
- Risque élevé (70-100): {(df_pred['risk_score'] >= 70).sum()} événements

## 🎯 Performance du Modèle

Taux de détection: {detection_rate:.1f}%
Confiance moyenne: {df_pred['confidence'].mean():.1f}%

## 🔍 Recommandations

{"⚠️ ATTENTION: Nombre élevé d'attaques détectées!" if detection_rate > 20 else "✅ Situation normale"}
{"🔴 Événements critiques à investiguer: " + str(high_risk) if high_risk > 0 else "✅ Aucun événement critique"}

## 📅 Période d'analyse

{'Du ' + str(df_pred['timestamp'].min()) + ' au ' + str(df_pred['timestamp'].max()) if 'timestamp' in df_pred.columns else 'Période non disponible'}

---
Rapport généré automatiquement par le système Wazuh ML Analytics
    """
    
    st.code(report, language='markdown')
    
    # Télécharger le rapport
    col1, col2 = st.columns(2)
    
    with col1:
        st.download_button(
            "📥 Télécharger le rapport (TXT)",
            report,
            f"rapport_performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "text/plain"
        )
    
    with col2:
        # Export des statistiques en CSV
        stats_csv = df_pred[['timestamp', 'ml_prediction', 'risk_score', 'confidence']].to_csv(index=False)
        st.download_button(
            "📥 Télécharger les stats (CSV)",
            stats_csv,
            f"stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "text/csv"
        )

# Footer
st.markdown("---")
st.caption("🤖 Analyse ML effectuée avec le modèle Random Forest de l'Étudiant 2")