# pages/1_📊_Data_Explorer.py
import streamlit as st
import pandas as pd
import numpy as np
from utils.wazuh_connector import get_wazuh_connector
from utils.data_processing import clean_dataframe, get_summary_stats
import plotly.express as px
from datetime import datetime, timedelta

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
    agent_cols = ['agent', 'agent.name', 'agent_id']
    agent_found = False
    
    for col in agent_cols:
        if col in df_enriched.columns:
            # Remplacer les valeurs 'unknown' ou NaN
            mask = (df_enriched[col].isna()) | (df_enriched[col].astype(str).str.lower() == 'unknown')
            if mask.any():
                df_enriched.loc[mask, col] = 'wazuh-agent-01'
            agent_found = True
    
    if not agent_found:
        df_enriched['agent'] = 'wazuh-agent-01'
    
    # 2. Source IP - Utiliser src_ip de Wazuh ou générer
    src_ip_cols = ['src_ip', 'source_ip', 'srcip', 'data.src_ip']
    src_ip_found = False
    
    for col in src_ip_cols:
        if col in df_enriched.columns:
            mask = (df_enriched[col].isna()) | (df_enriched[col].astype(str).str.lower() == 'unknown')
            if mask.any():
                # Générer des IPs réalistes
                ips = [f"192.168.{np.random.randint(1, 255)}.{np.random.randint(1, 255)}" 
                      for _ in range(mask.sum())]
                df_enriched.loc[mask, col] = ips
            src_ip_found = True
    
    if not src_ip_found:
        df_enriched['src_ip'] = [f"192.168.1.{np.random.randint(1, 255)}" for _ in range(len(df_enriched))]
    
    # 3. Destination IP
    dst_ip_cols = ['dest_ip', 'destination_ip', 'dstip', 'data.dest_ip']
    dst_ip_found = False
    
    for col in dst_ip_cols:
        if col in df_enriched.columns:
            mask = (df_enriched[col].isna()) | (df_enriched[col].astype(str).str.lower() == 'unknown')
            if mask.any():
                df_enriched.loc[mask, col] = '10.0.0.1'
            dst_ip_found = True
    
    if not dst_ip_found:
        df_enriched['dest_ip'] = '10.0.0.1'
    
    # 4. Règle (rule) - Essayer de garder la structure Wazuh
    if 'rule' not in df_enriched.columns:
        # Créer une structure de règle réaliste
        rule_data = []
        for i in range(len(df_enriched)):
            rule_data.append({
                'description': 'Security event detected',
                'level': np.random.randint(3, 12),
                'id': str(np.random.randint(1000, 9999))
            })
        df_enriched['rule'] = rule_data
    
    # 5. Timestamp - S'assurer qu'il y a un timestamp
    timestamp_cols = ['timestamp', '@timestamp', 'event_time']
    timestamp_found = False
    
    for col in timestamp_cols:
        if col in df_enriched.columns:
            try:
                df_enriched[col] = pd.to_datetime(df_enriched[col], errors='coerce')
                # Remplir les NaN avec des dates récentes
                if df_enriched[col].isna().any():
                    now = datetime.now()
                    random_times = [
                        now - timedelta(minutes=np.random.randint(0, 1440)) 
                        for _ in range(df_enriched[col].isna().sum())
                    ]
                    df_enriched.loc[df_enriched[col].isna(), col] = random_times
                timestamp_found = True
            except:
                pass
    
    if not timestamp_found:
        now = datetime.now()
        df_enriched['timestamp'] = [
            now - timedelta(minutes=np.random.randint(0, 1440)) 
            for _ in range(len(df_enriched))
        ]
    
    # 6. Type d'événement
    if 'type' not in df_enriched.columns and 'data.type' not in df_enriched.columns:
        event_types = ['ssh', 'http', 'firewall', 'auth', 'system']
        weights = [0.3, 0.3, 0.2, 0.1, 0.1]
        df_enriched['type'] = np.random.choice(event_types, size=len(df_enriched), p=weights)
    
    # 7. Action (si manquante)
    if 'action' not in df_enriched.columns:
        actions = ['allow', 'deny', 'alert']
        df_enriched['action'] = np.random.choice(actions, size=len(df_enriched), p=[0.6, 0.3, 0.1])
    
    # 8. Risk score (pour les prédictions ML)
    if 'risk_score' not in df_enriched.columns and 'data.risk' not in df_enriched.columns:
        # Générer des scores de risque réalistes
        df_enriched['risk_score'] = np.random.randint(0, 100, size=len(df_enriched))
    
    return df_enriched

# Fonction pour formater les données Wazuh
def format_wazuh_data_for_display(df):
    """
    Formate les données Wazuh pour un affichage lisible
    """
    df_display = df.copy()
    
    # 1. Simplifier les colonnes complexes (dicts, listes)
    for col in df_display.columns:
        try:
            # Si c'est un dictionnaire, extraire les champs importants
            if isinstance(df_display[col].iloc[0], dict) and col == 'rule':
                # Créer des colonnes séparées pour les champs de règle
                df_display['rule_description'] = df_display[col].apply(
                    lambda x: x.get('description', 'N/A')[:50] + '...' if isinstance(x, dict) else str(x)[:50]
                )
                df_display['rule_level'] = df_display[col].apply(
                    lambda x: x.get('level', 0) if isinstance(x, dict) else 0
                )
                df_display['rule_id'] = df_display[col].apply(
                    lambda x: x.get('id', 'N/A') if isinstance(x, dict) else 'N/A'
                )
            elif isinstance(df_display[col].iloc[0], dict) and col == 'data':
                # Extraire les champs data importants
                df_display['data_type'] = df_display[col].apply(
                    lambda x: x.get('type', 'N/A') if isinstance(x, dict) else 'N/A'
                )
                df_display['data_src_ip'] = df_display[col].apply(
                    lambda x: x.get('src_ip', 'N/A') if isinstance(x, dict) else 'N/A'
                )
        except:
            pass
    
    # 2. Convertir les timestamps en string lisible
    timestamp_cols = ['timestamp', '@timestamp']
    for col in timestamp_cols:
        if col in df_display.columns and pd.api.types.is_datetime64_any_dtype(df_display[col]):
            df_display[col] = df_display[col].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    return df_display

# Sidebar - Filtres
with st.sidebar:
    st.header("⚙️ Paramètres")
    
    # Mode de chargement
    load_mode = st.radio(
        "Mode de chargement",
        ["📤 Depuis Wazuh", "🎲 Données simulées"],
        help="Charger les données depuis Wazuh ou générer des données simulées"
    )
    
    if load_mode == "📤 Depuis Wazuh":
        # Nombre de logs à récupérer
        num_logs = st.slider(
            "Nombre de logs",
            min_value=100,
            max_value=5000,
            value=1000,
            step=100
        )
        
        # Filtre de temps
        time_filter = st.selectbox(
            "Période",
            ["Dernière heure", "Dernières 24h", "Toutes les données"],
            index=2
        )
    
    else:  # Mode simulé
        num_logs = st.slider(
            "Nombre de logs",
            min_value=100,
            max_value=2000,
            value=500,
            step=100
        )
        
        # Types d'événements simulés
        st.subheader("🎭 Types d'événements")
        ssh_ratio = st.slider("SSH", 0.0, 1.0, 0.3, 0.1)
        http_ratio = st.slider("HTTP", 0.0, 1.0, 0.4, 0.1)
        firewall_ratio = st.slider("Firewall", 0.0, 1.0, 0.2, 0.1)
        other_ratio = 1.0 - (ssh_ratio + http_ratio + firewall_ratio)
        st.write(f"Autres: {other_ratio:.1%}")
    
    # Bouton de rafraîchissement
    refresh = st.button("🔄 Charger les données", type="primary", use_container_width=True)
    
    # Options d'enrichissement
    with st.expander("⚡ Options avancées"):
        auto_enrich = st.checkbox("Enrichir automatiquement les données", value=True,
                                 help="Ajoute des valeurs par défaut aux données manquantes")
        show_raw = st.checkbox("Afficher les données brutes", value=False,
                              help="Montre les données avant enrichissement")

# Initialiser session state
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame()
    st.session_state.df_raw = pd.DataFrame()
    st.session_state.load_mode = ""

# Charger les données
if refresh or st.session_state.df.empty:
    with st.spinner("🔄 Chargement des données..."):
        if load_mode == "📤 Depuis Wazuh":
            try:
                connector = get_wazuh_connector()
                
                # Construire la requête selon le filtre de temps
                query = {"size": num_logs, "sort": [{"@timestamp": {"order": "desc"}}]}
                
                if time_filter == "Dernière heure":
                    query["query"] = {
                        "range": {
                            "@timestamp": {
                                "gte": "now-1h",
                                "lte": "now"
                            }
                        }
                    }
                elif time_filter == "Dernières 24h":
                    query["query"] = {
                        "range": {
                            "@timestamp": {
                                "gte": "now-24h",
                                "lte": "now"
                            }
                        }
                    }
                
                logs, error = connector.fetch_alerts(size=num_logs, query=query)
                
                if error:
                    st.error(f"❌ Erreur lors du chargement : {error}")
                    # Fallback aux données simulées
                    st.info("🔧 Utilisation de données simulées en attendant...")
                    raise Exception("Fallback to simulated")
                
                elif not logs:
                    st.warning("⚠️ Aucune donnée trouvée dans Wazuh")
                    st.info("💡 Génération de données simulées...")
                    raise Exception("Fallback to simulated")
                
                else:
                    # Convertir en DataFrame
                    df_raw = connector.logs_to_dataframe(logs)
                    st.session_state.df_raw = df_raw.copy()
                    
                    # Nettoyer les données
                    df = clean_dataframe(df_raw)
                    
                    if auto_enrich:
                        df = enrich_wazuh_data(df)
                    
                    st.session_state.df = df
                    st.session_state.load_mode = "wazuh"
                    
                    now = datetime.now()
                    st.success(f"✅ {len(df)} logs chargés depuis Wazuh")
                    st.caption(f"🕐 Dernière mise à jour : {now.strftime('%Y-%m-%d %H:%M:%S')}")
                    
            except Exception as e:
                # Fallback aux données simulées
                if "Fallback" not in str(e):
                    st.error(f"❌ Erreur: {str(e)}")
                
                # Générer des données simulées
                generate_simulated_data(num_logs, ssh_ratio, http_ratio, firewall_ratio)
                st.session_state.load_mode = "simulated"
                
        else:  # Mode simulé
            generate_simulated_data(num_logs, ssh_ratio, http_ratio, firewall_ratio)
            st.session_state.load_mode = "simulated"

# Fonction pour générer des données simulées
def generate_simulated_data(num_logs, ssh_ratio, http_ratio, firewall_ratio):
    """Génère des données de logs simulées réalistes"""
    
    # Calculer les ratios
    other_ratio = max(0, 1.0 - (ssh_ratio + http_ratio + firewall_ratio))
    ratios = [ssh_ratio, http_ratio, firewall_ratio, other_ratio]
    event_types = ['ssh', 'http', 'firewall', 'system']
    
    # Générer les événements
    events = np.random.choice(event_types, size=num_logs, p=ratios)
    
    # Préparer les données
    data = []
    base_time = datetime.now() - timedelta(hours=24)
    
    for i, event_type in enumerate(events):
        timestamp = base_time + timedelta(minutes=i*0.5)
        
        if event_type == 'ssh':
            entry = {
                '@timestamp': timestamp.isoformat(),
                'agent': {'name': f'agent-{np.random.randint(1, 10)}', 'id': str(np.random.randint(100, 999))},
                'rule': {
                    'description': 'SSH authentication attempt',
                    'level': np.random.choice([3, 5, 7], p=[0.7, 0.2, 0.1]),
                    'id': '5712'
                },
                'data': {
                    'type': 'ssh',
                    'src_ip': f"192.168.{np.random.randint(1, 255)}.{np.random.randint(1, 255)}",
                    'dest_ip': f"10.0.0.{np.random.randint(1, 50)}",
                    'user': np.random.choice(['root', 'admin', 'ubuntu', 'user1']),
                    'action': np.random.choice(['accepted', 'failed'], p=[0.8, 0.2])
                },
                'risk_score': np.random.randint(0, 100)
            }
            
        elif event_type == 'http':
            entry = {
                '@timestamp': timestamp.isoformat(),
                'agent': {'name': f'web-server-{np.random.randint(1, 5)}', 'id': str(np.random.randint(200, 299))},
                'rule': {
                    'description': 'HTTP request',
                    'level': np.random.choice([2, 4, 6], p=[0.8, 0.15, 0.05]),
                    'id': '31101'
                },
                'data': {
                    'type': 'http',
                    'src_ip': f"10.1.{np.random.randint(1, 255)}.{np.random.randint(1, 255)}",
                    'dest_ip': f"10.0.0.{np.random.randint(80, 90)}",
                    'method': np.random.choice(['GET', 'POST', 'PUT']),
                    'url': np.random.choice(['/', '/admin', '/api/data', '/login']),
                    'status': np.random.choice([200, 200, 200, 404, 500])
                },
                'risk_score': np.random.randint(0, 100)
            }
            
        elif event_type == 'firewall':
            entry = {
                '@timestamp': timestamp.isoformat(),
                'agent': {'name': f'firewall-{np.random.randint(1, 3)}', 'id': str(np.random.randint(300, 399))},
                'rule': {
                    'description': 'Firewall event',
                    'level': np.random.choice([5, 8, 10], p=[0.6, 0.3, 0.1]),
                    'id': '5103'
                },
                'data': {
                    'type': 'firewall',
                    'src_ip': f"203.0.113.{np.random.randint(1, 255)}",
                    'dest_ip': f"10.0.0.{np.random.randint(1, 255)}",
                    'action': np.random.choice(['allow', 'deny'], p=[0.7, 0.3]),
                    'protocol': np.random.choice(['TCP', 'UDP', 'ICMP'])
                },
                'risk_score': np.random.randint(20, 100)
            }
            
        else:  # system
            entry = {
                '@timestamp': timestamp.isoformat(),
                'agent': {'name': f'server-{np.random.randint(1, 5)}', 'id': str(np.random.randint(400, 499))},
                'rule': {
                    'description': 'System event',
                    'level': np.random.randint(2, 6),
                    'id': '1000'
                },
                'data': {
                    'type': 'system',
                    'message': np.random.choice(['Service started', 'Disk space warning', 'User login'])
                },
                'risk_score': np.random.randint(0, 50)
            }
        
        data.append(entry)
    
    # Créer le DataFrame
    df_raw = pd.DataFrame(data)
    st.session_state.df_raw = df_raw.copy()
    
    # Nettoyer et enrichir
    df = clean_dataframe(df_raw)
    if auto_enrich:
        df = enrich_wazuh_data(df)
    
    st.session_state.df = df
    
    now = datetime.now()
    st.success(f"✅ {len(df)} logs simulés générés")
    st.caption(f"🕐 Généré le : {now.strftime('%Y-%m-%d %H:%M:%S')}")

# Afficher les données
df = st.session_state.df
df_raw = st.session_state.df_raw

if not df.empty:
    # Afficher le mode de chargement
    source_badge = "🔵 Wazuh" if st.session_state.load_mode == "wazuh" else "🟡 Simulé"
    st.markdown(f"**Source des données:** {source_badge}")
    
    # Afficher les données brutes si demandé
    if show_raw and not df_raw.empty:
        with st.expander("🔍 Données brutes (avant enrichissement)"):
            st.write(f"**Structure:** {len(df_raw)} lignes, {len(df_raw.columns)} colonnes")
            st.dataframe(df_raw.head(5), use_container_width=True)
    
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
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Tableau", "🔍 Colonnes", "📊 Visualisations", "💾 Export"])
    
    with tab1:
        st.markdown("### 📋 Données enrichies")
        
        # Formater pour l'affichage
        df_display = format_wazuh_data_for_display(df)
        
        # Sélectionner les colonnes à afficher
        all_columns = df_display.columns.tolist()
        default_cols = []
        
        # Colonnes prioritaires pour l'affichage
        priority_cols = ['timestamp', '@timestamp', 'agent', 'rule_description', 
                        'data_type', 'src_ip', 'dest_ip', 'risk_score']
        
        for col in priority_cols:
            if col in all_columns:
                default_cols.append(col)
        
        # Ajouter jusqu'à 10 colonnes max
        remaining_cols = [c for c in all_columns if c not in default_cols]
        default_cols.extend(remaining_cols[:10 - len(default_cols)])
        
        selected_columns = st.multiselect(
            "Colonnes à afficher",
            all_columns,
            default=default_cols
        )
        
        if selected_columns:
            st.dataframe(
                df_display[selected_columns].head(100),
                use_container_width=True,
                height=400
            )
    
    with tab2:
        st.markdown("### 🔍 Informations sur les colonnes")
        
        # Créer un DataFrame d'info
        info_data = []
        for col in df.columns:
            # Échantillon de valeurs
            sample_values = df[col].dropna().unique()[:3]
            sample_str = ', '.join([str(v)[:30] for v in sample_values])[:50]
            
            info_data.append({
                'Colonne': col,
                'Type': str(df[col].dtype),
                'Non-null': df[col].count(),
                'Null (%)': f"{df[col].isnull().sum() / len(df) * 100:.1f}%",
                'Unique': df[col].nunique(),
                'Exemples': sample_str + '...' if len(sample_str) >= 50 else sample_str
            })
        
        info_df = pd.DataFrame(info_data)
        st.dataframe(info_df, use_container_width=True, height=400)
    
    with tab3:
        st.markdown("### 📊 Visualisations")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Distribution des types d'événements
            if 'data_type' in df_display.columns or 'type' in df.columns:
                type_col = 'data_type' if 'data_type' in df_display.columns else 'type'
                if type_col in df_display.columns:
                    type_counts = df_display[type_col].value_counts().head(10)
                    
                    fig = px.bar(
                        x=type_counts.index,
                        y=type_counts.values,
                        title="Types d'événements",
                        labels={'x': 'Type', 'y': 'Nombre'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
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
        
        # Timeline des événements
        if '@timestamp' in df.columns or 'timestamp' in df.columns:
            timestamp_col = '@timestamp' if '@timestamp' in df.columns else 'timestamp'
            
            if pd.api.types.is_datetime64_any_dtype(df[timestamp_col]):
                # Agrégation par heure
                df['hour'] = df[timestamp_col].dt.floor('H')
                hourly_counts = df.groupby('hour').size().reset_index(name='count')
                
                fig = px.line(
                    hourly_counts,
                    x='hour',
                    y='count',
                    title="Événements par heure",
                    labels={'x': 'Heure', 'y': 'Nombre d\'événements'}
                )
                st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        st.markdown("### 💾 Export des données")
        
        # Options d'export
        export_format = st.radio(
            "Format d'export",
            ["CSV", "JSON", "Excel"],
            horizontal=True
        )
        
        export_df = df.copy()
        
        # Préparer pour l'export
        for col in export_df.columns:
            if export_df[col].dtype == 'object':
                try:
                    if isinstance(export_df[col].iloc[0], (dict, list)):
                        export_df[col] = export_df[col].apply(str)
                except:
                    pass
        
        # Boutons d'export
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if export_format == "CSV":
                csv_data = export_df.to_csv(index=False)
                st.download_button(
                    "📥 Télécharger CSV",
                    csv_data,
                    f"wazuh_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    "text/csv",
                    use_container_width=True
                )
        
        with col2:
            if export_format == "JSON":
                json_data = export_df.to_json(orient='records', date_format='iso')
                st.download_button(
                    "📥 Télécharger JSON",
                    json_data,
                    f"wazuh_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    "application/json",
                    use_container_width=True
                )
        
        with col3:
            if export_format == "Excel":
                try:
                    import io
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        export_df.to_excel(writer, index=False, sheet_name='Wazuh_Data')
                    
                    st.download_button(
                        "📥 Télécharger Excel",
                        buffer.getvalue(),
                        f"wazuh_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                except ImportError:
                    st.warning("Installer: `pip install openpyxl`")

else:
    st.info("👆 Cliquez sur 'Charger les données' pour commencer l'exploration")