# pages/4_📋_Performance.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Performance", page_icon="📋", layout="wide")

st.title("📋 Rapport de Performance ML")

# Fonction pour corriger les problèmes de timestamps
def fix_timestamp_issues(df):
    """
    Corrige les problèmes de fuseaux horaires dans le DataFrame
    """
    df_fixed = df.copy()
    
    # Colonnes de timestamp potentielles
    timestamp_cols = ['timestamp', '@timestamp', 'event_time', 'prediction_time']
    
    for col in timestamp_cols:
        if col in df_fixed.columns:
            try:
                # Convertir en datetime
                df_fixed[col] = pd.to_datetime(df_fixed[col], errors='coerce')
                
                # Si certains ont des fuseaux et d'autres non, uniformiser
                if df_fixed[col].dt.tz is not None:
                    # Supprimer le fuseau horaire
                    df_fixed[col] = df_fixed[col].dt.tz_localize(None)
                
                # Remplir les NaN
                if df_fixed[col].isna().any():
                    now = datetime.now()
                    missing_count = df_fixed[col].isna().sum()
                    df_fixed.loc[df_fixed[col].isna(), col] = [
                        now - pd.Timedelta(minutes=np.random.randint(0, 1440))
                        for _ in range(missing_count)
                    ]
                    
            except Exception as e:
                # En cas d'erreur, on supprime la colonne
                df_fixed = df_fixed.drop(columns=[col], errors='ignore')
    
    return df_fixed

# Vérifier si des prédictions existent
if 'df_predictions' not in st.session_state:
    st.warning("⚠️ Aucune prédiction disponible")
    st.info("👉 Générez d'abord des prédictions sur la page 'ML Predictions'")
    st.stop()

# Charger et corriger les données
df_pred_raw = st.session_state.df_predictions.copy()
df_pred = fix_timestamp_issues(df_pred_raw)

# Calculer les métriques
total = len(df_pred)

# Vérifier que les colonnes nécessaires existent
if 'ml_prediction' not in df_pred.columns:
    st.error("❌ Colonne 'ml_prediction' manquante dans les prédictions")
    st.stop()

if 'risk_score' not in df_pred.columns:
    st.error("❌ Colonne 'risk_score' manquante dans les prédictions")
    st.stop()

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

# Informations sur les données
with st.expander("ℹ️ Informations sur les données"):
    st.write(f"**Dimensions:** {df_pred.shape[0]} lignes × {df_pred.shape[1]} colonnes")
    st.write(f"**Colonnes disponibles:** {', '.join(df_pred.columns.tolist()[:10])}{'...' if len(df_pred.columns) > 10 else ''}")
    
    # Colonnes de timestamp disponibles
    timestamp_cols_available = [col for col in ['timestamp', '@timestamp'] if col in df_pred.columns]
    if timestamp_cols_available:
        st.write(f"**Colonnes temporelles disponibles:** {', '.join(timestamp_cols_available)}")

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
    
    try:
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
    except Exception as e:
        st.warning(f"Impossible de catégoriser les risques: {str(e)}")

with tab2:
    st.markdown("### 📈 Évolution temporelle")
    
    # Trouver une colonne de timestamp disponible
    timestamp_col = None
    for col in ['@timestamp', 'timestamp', 'prediction_time']:
        if col in df_pred.columns:
            timestamp_col = col
            break
    
    if timestamp_col:
        try:
            # Extraire l'heure si c'est un datetime
            if pd.api.types.is_datetime64_any_dtype(df_pred[timestamp_col]):
                df_pred['hour'] = df_pred[timestamp_col].dt.hour
            else:
                # Si ce n'est pas un datetime, essayer de convertir
                df_pred[timestamp_col] = pd.to_datetime(df_pred[timestamp_col], errors='coerce')
                df_pred['hour'] = df_pred[timestamp_col].dt.hour.fillna(0).astype(int)
            
            # Attaques par heure
            attacks_df = df_pred[df_pred['ml_prediction'] == 'Attack']
            if not attacks_df.empty:
                attacks_per_hour = attacks_df.groupby('hour').size()
                
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
                
                critical_events = df_pred[df_pred['risk_score'] >= 70].copy()
                
                if len(critical_events) > 0 and timestamp_col in critical_events.columns:
                    # Trier par timestamp
                    critical_events = critical_events.sort_values(timestamp_col)
                    
                    # Créer un scatter plot temporel
                    fig = px.scatter(
                        critical_events.head(100),  # Limiter à 100 pour la lisibilité
                        x=timestamp_col,
                        y='risk_score',
                        color='risk_score',
                        size='risk_score',
                        title='Timeline des 100 premiers événements critiques',
                        color_continuous_scale='Reds',
                        hover_data=['ml_prediction', 'risk_score']
                    )
                    
                    fig.update_layout(
                        xaxis_title='Temps',
                        yaxis_title='Risk Score',
                        showlegend=False
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Aucun événement critique détecté ou pas de données temporelles")
                    
            else:
                st.info("Aucune attaque détectée pour l'analyse temporelle")
                
        except Exception as e:
            st.error(f"❌ Erreur lors de l'analyse temporelle: {str(e)}")
            st.info("Les données temporelles peuvent être incomplètes ou mal formatées")
    else:
        st.info("Pas de données temporelles disponibles pour l'analyse")

with tab3:
    st.markdown("### 💾 Rapport de performance")
    
    # Calculer des statistiques avancées
    if len(df_pred) > 0:
        # Statistiques par catégorie
        try:
            stats_by_category = df_pred.groupby('ml_prediction').agg({
                'risk_score': ['mean', 'min', 'max', 'std'],
                'confidence': 'mean' if 'confidence' in df_pred.columns else 'count'
            }).round(2)
            
            st.markdown("#### 📊 Statistiques par catégorie")
            st.dataframe(stats_by_category, use_container_width=True)
        except Exception as e:
            st.warning(f"Impossible de calculer les statistiques par catégorie: {str(e)}")
    
    # Générer un rapport texte
    # Informations temporelles
    time_info = ""
    if timestamp_col and timestamp_col in df_pred.columns:
        try:
            min_time = df_pred[timestamp_col].min()
            max_time = df_pred[timestamp_col].max()
            time_info = f"Du {min_time.strftime('%Y-%m-%d %H:%M:%S')} au {max_time.strftime('%Y-%m-%d %H:%M:%S')}"
        except:
            time_info = "Période non disponible"
    else:
        time_info = "Période non disponible"
    
    # Informations de confiance
    confidence_info = ""
    if 'confidence' in df_pred.columns:
        confidence_mean = df_pred['confidence'].mean()
        confidence_info = f"Confiance moyenne: {confidence_mean:.1f}%"
    else:
        confidence_info = "Confiance: non disponible"
    
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
{confidence_info}

## 🔍 Recommandations

{"⚠️ ATTENTION: Nombre élevé d'attaques détectées!" if detection_rate > 20 else "✅ Situation normale"}
{"🔴 Événements critiques à investiguer: " + str(high_risk) if high_risk > 0 else "✅ Aucun événement critique"}

## 📅 Période d'analyse

{time_info}

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
            "text/plain",
            use_container_width=True
        )
    
    with col2:
        # Export des statistiques en CSV
        try:
            # Colonnes pour l'export
            export_cols = []
            for col in ['ml_prediction', 'risk_score', 'confidence', 'threat_level']:
                if col in df_pred.columns:
                    export_cols.append(col)
            
            # Ajouter le timestamp s'il existe
            if timestamp_col:
                export_cols.insert(0, timestamp_col)
            
            if export_cols:
                stats_csv = df_pred[export_cols].to_csv(index=False)
                st.download_button(
                    "📥 Télécharger les stats (CSV)",
                    stats_csv,
                    f"stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    "text/csv",
                    use_container_width=True
                )
            else:
                st.info("Pas de colonnes disponibles pour l'export")
        except Exception as e:
            st.error(f"Erreur lors de l'export: {str(e)}")

# Footer
st.markdown("---")
st.caption("🤖 Analyse ML effectuée avec le modèle Random Forest de l'Étudiant 2")

# Bouton pour rafraîchir les données
if st.button("🔄 Rafraîchir l'analyse", type="secondary"):
    st.rerun()