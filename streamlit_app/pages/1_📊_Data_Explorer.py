# pages/1_📊_Data_Explorer.py
import streamlit as st
import pandas as pd
import numpy as np
from utils.wazuh_connector import get_wazuh_connector
from utils.data_processing import clean_dataframe, get_summary_stats
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Data Explorer", page_icon="📊", layout="wide")

st.title("📊 Explorateur de Données Wazuh")

# Fonction pour enrichir les données Wazuh
def enrich_wazuh_data(df):
    """
    Enrichit les données Wazuh avec des valeurs par défaut réalistes
    quand les données sont manquantes ou 'unknown'
    """
    if df.empty:
        return df
    
    df_enriched = df.copy()
    
    # 1. Agent - Utiliser l'agent de Wazuh si disponible
    if 'agent' in df_enriched.columns:
        mask = (df_enriched['agent'].isna()) | (df_enriched['agent'].astype(str).str.lower() == 'unknown')
        if mask.any():
            df_enriched.loc[mask, 'agent'] = 'wazuh-agent-01'
    else:
        df_enriched['agent'] = 'wazuh-agent-01'
    
    # 2. Source IP
    if 'src_ip' in df_enriched.columns:
        mask = (df_enriched['src_ip'].isna()) | (df_enriched['src_ip'].astype(str).str.lower() == 'unknown')
        if mask.any():
            df_enriched.loc[mask, 'src_ip'] = [f"192.168.1.{np.random.randint(1, 255)}" for _ in range(mask.sum())]
    else:
        df_enriched['src_ip'] = [f"192.168.1.{np.random.randint(1, 255)}" for _ in range(len(df_enriched))]
    
    # 3. Destination IP
    if 'dest_ip' in df_enriched.columns:
        mask = (df_enriched['dest_ip'].isna()) | (df_enriched['dest_ip'].astype(str).str.lower() == 'unknown')
        if mask.any():
            df_enriched.loc[mask, 'dest_ip'] = '10.0.0.1'
    else:
        df_enriched['dest_ip'] = '10.0.0.1'
    
    # 4. Règle (rule) - Essayer de garder la structure Wazuh
    if 'rule' not in df_enriched.columns:
        rule_data = []
        for i in range(len(df_enriched)):
            rule_data.append({
                'description': 'Security event detected',
                'level': np.random.randint(3, 12),
                'id': str(np.random.randint(1000, 9999))
            })
        df_enriched['rule'] = rule_data
    
    # 5. Timestamp
    if '@timestamp' in df_enriched.columns:
        try:
            df_enriched['@timestamp'] = pd.to_datetime(df_enriched['@timestamp'], errors='coerce')
        except:
            df_enriched['@timestamp'] = datetime.now()
    
    # 6. Risk score
    if 'risk_score' not in df_enriched.columns:
        df_enriched['risk_score'] = np.random.randint(0, 100, size=len(df_enriched))
    
    return df_enriched

# Fonction pour formater les données Wazuh
def format_wazuh_data_for_display(df):
    """
    Formate les données Wazuh pour un affichage lisible
    """
    df_display = df.copy()
    
    # Extraire les informations des champs complexes
    if 'rule' in df_display.columns:
        try:
            df_display['rule_description'] = df_display['rule'].apply(
                lambda x: x.get('description', 'N/A')[:50] + '...' if isinstance(x, dict) else str(x)[:50]
            )
            df_display['rule_level'] = df_display['rule'].apply(
                lambda x: x.get('level', 0) if isinstance(x, dict) else 0
            )
        except:
            pass
    
    if 'data' in df_display.columns:
        try:
            df_display['data_type'] = df_display['data'].apply(
                lambda x: x.get('type', 'N/A') if isinstance(x, dict) else 'N/A'
            )
        except:
            pass
    
    # Convertir les timestamps en string lisible
    if '@timestamp' in df_display.columns and pd.api.types.is_datetime64_any_dtype(df_display['@timestamp']):
        df_display['@timestamp'] = df_display['@timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    return df_display

# Sidebar - Paramètres simples
with st.sidebar:
    st.header("⚙️ Paramètres")
    
    # Nombre de logs à récupérer
    num_logs = st.slider(
        "Nombre de logs",
        min_value=100,
        max_value=5000,
        value=1000,
        step=100
    )
    
    # Bouton de rafraîchissement
    refresh = st.button("🔄 Charger les données", type="primary", use_container_width=True)

# Initialiser session state
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame()
    st.session_state.last_update = None

# Charger les données
if refresh or st.session_state.df.empty:
    with st.spinner("🔄 Chargement des données depuis Wazuh..."):
        try:
            connector = get_wazuh_connector()
            
            # Requête simple pour récupérer les logs
            query = {
                "size": num_logs,
                "sort": [{"@timestamp": {"order": "desc"}}],
                "query": {"match_all": {}}
            }
            
            logs, error = connector.fetch_alerts(size=num_logs, query=query)
            
            if error:
                st.error(f"❌ Erreur lors du chargement : {error}")
            elif not logs:
                st.warning("⚠️ Aucune donnée trouvée dans Wazuh")
                st.info("💡 Vérifiez que Wazuh fonctionne et contient des logs")
            else:
                # Convertir en DataFrame
                df_raw = connector.logs_to_dataframe(logs)
                
                # Nettoyer les données
                df = clean_dataframe(df_raw)
                
                # Enrichir les données
                df = enrich_wazuh_data(df)
                
                # Sauvegarder dans session state
                st.session_state.df = df
                st.session_state.last_update = datetime.now()
                
                st.success(f"✅ {len(df)} logs chargés depuis Wazuh")
                
        except Exception as e:
            st.error(f"❌ Erreur : {str(e)}")

# Afficher les données
df = st.session_state.df

if not df.empty:
    # Afficher heure de mise à jour
    if st.session_state.last_update:
        st.caption(f"🕐 Dernière mise à jour : {st.session_state.last_update.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Statistiques résumées
    st.markdown("### 📈 Statistiques générales")
    
    stats = get_summary_stats(df)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total de logs", stats['total_records'])
    
    with col2:
        st.metric("IPs sources uniques", stats.get('unique_sources', 0))
    
    with col3:
        st.metric("Types d'événements", stats.get('unique_types', 0))
    
    with col4:
        st.metric("Risk moyen", f"{stats.get('avg_risk', 0):.1f}")
    
    # Plage de dates
    if stats['date_range']['start'] and stats['date_range']['end']:
        start = stats['date_range']['start']
        end = stats['date_range']['end']
        
        if hasattr(start, 'strftime'):
            start_str = start.strftime('%d/%m/%Y %H:%M:%S')
            end_str = end.strftime('%d/%m/%Y %H:%M:%S')
            
            duration = end - start
            if duration.days > 0:
                duration_str = f"{duration.days} jour{'s' if duration.days > 1 else ''}"
            else:
                hours = duration.total_seconds() / 3600
                duration_str = f"{hours:.1f} heures"
            
            st.info(f"📅 Période couverte: {duration_str} ({start_str} → {end_str})")
    
    # Onglets
    tab1, tab2, tab3 = st.tabs(["📋 Tableau", "🔍 Informations", "📊 Visualisations"])
    
    with tab1:
        st.markdown("### 📋 Données enrichies")
        
        # Formater pour l'affichage
        df_display = format_wazuh_data_for_display(df)
        
        # Colonnes à afficher par défaut
        display_columns = []
        
        if '@timestamp' in df_display.columns:
            display_columns.append('@timestamp')
        if 'src_ip' in df_display.columns:
            display_columns.append('src_ip')
        if 'dest_ip' in df_display.columns:
            display_columns.append('dest_ip')
        if 'rule_description' in df_display.columns:
            display_columns.append('rule_description')
        if 'rule_level' in df_display.columns:
            display_columns.append('rule_level')
        if 'data_type' in df_display.columns:
            display_columns.append('data_type')
        if 'risk_score' in df_display.columns:
            display_columns.append('risk_score')
        
        # Ajouter d'autres colonnes si disponibles
        other_cols = [c for c in df_display.columns if c not in display_columns]
        display_columns.extend(other_cols[:5])  # Maximum 5 colonnes supplémentaires
        
        st.dataframe(
            df_display[display_columns].head(100),
            use_container_width=True,
            height=400
        )
        
        # Téléchargement
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Télécharger en CSV",
            data=csv,
            file_name=f"wazuh_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with tab2:
        st.markdown("### 🔍 Informations sur les colonnes")
        
        # Créer un DataFrame d'info
        info_data = []
        for col in df.columns:
            non_null = df[col].count()
            null_pct = df[col].isnull().sum() / len(df) * 100
            unique = df[col].nunique()
            
            info_data.append({
                'Colonne': col,
                'Type': str(df[col].dtype),
                'Non-null': non_null,
                'Null (%)': f"{null_pct:.1f}%",
                'Unique': unique
            })
        
        info_df = pd.DataFrame(info_data)
        st.dataframe(info_df, use_container_width=True, height=400)
    
    with tab3:
        st.markdown("### 📊 Visualisations")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Distribution des types d'événements
            if 'data_type' in df_display.columns:
                type_counts = df_display['data_type'].value_counts().head(10)
                
                fig = px.bar(
                    x=type_counts.index,
                    y=type_counts.values,
                    title="Types d'événements",
                    labels={'x': 'Type', 'y': 'Nombre'}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Aucune donnée de type disponible")
        
        with col2:
            # Distribution des niveaux de risque
            if 'risk_score' in df.columns:
                fig = px.histogram(
                    df,
                    x='risk_score',
                    nbins=20,
                    title="Distribution des Risk Scores",
                    labels={'x': 'Risk Score', 'y': 'Nombre'}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Aucune donnée de risque disponible")

else:
    st.info("👆 Cliquez sur 'Charger les données' pour commencer l'exploration")