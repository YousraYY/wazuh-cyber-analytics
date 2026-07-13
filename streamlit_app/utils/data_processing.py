# utils/data_processing.py - VERSION CORRIGÉE
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def clean_dataframe(df):
    """Nettoyer le DataFrame"""
    if df.empty:
        return df
    
    try:
        # ÉTAPE 1 : Convertir tous les dicts/listes en strings
        for col in df.columns:
            df[col] = df[col].apply(
                lambda x: json.dumps(x, sort_keys=True) 
                if isinstance(x, (dict, list)) 
                else x
            )
        
        # ÉTAPE 2 : Supprimer les doublons
        df = df.drop_duplicates()
        
        # ÉTAPE 3 : Gérer les valeurs manquantes
        # D'abord trouver quelles colonnes nous intéressent
        col_mapping = {}
        for col in df.columns:
            # Chercher les colonnes de source
            if any(keyword in col.lower() for keyword in ['source', 'src', 'ip']):
                col_mapping[col] = 'unknown_ip'
            # Chercher les colonnes d'action
            elif any(keyword in col.lower() for keyword in ['action', 'status']):
                col_mapping[col] = 'unknown'
        
        # Remplacer les NaN
        for col in df.columns:
            if df[col].dtype == 'object':
                default_value = col_mapping.get(col, 'unknown')
                df[col] = df[col].fillna(default_value)
            else:
                df[col] = df[col].fillna(0)
        
        return df
        
    except Exception as e:
        print(f"⚠️ Erreur lors du nettoyage : {e}")
        # Retourner le DataFrame non nettoyé plutôt que d'échouer
        return df


def extract_features(df):
    """Extraire des features pour le ML"""
    if df.empty:
        return df
    
    # Créer une copie
    df_features = df.copy()
    
    # Chercher les colonnes timestamp
    timestamp_found = False
    for ts_col in ['timestamp', '@timestamp']:
        if ts_col in df_features.columns:
            try:
                # Convertir en datetime
                df_features[ts_col] = pd.to_datetime(
                    df_features[ts_col], 
                    errors='coerce',
                    format='ISO8601'
                )
                
                # Extraire features temporelles
                df_features['hour'] = df_features[ts_col].dt.hour
                df_features['day_of_week'] = df_features[ts_col].dt.dayofweek
                df_features['is_weekend'] = df_features['day_of_week'].isin([5, 6]).astype(int)
                df_features['is_business_hours'] = df_features['hour'].between(9, 17).astype(int)
                
                timestamp_found = True
                break
            except:
                continue
    
    if not timestamp_found:
        # Si pas de timestamp, créer des features factices
        np.random.seed(42)
        df_features['hour'] = np.random.randint(0, 24, len(df_features))
        df_features['day_of_week'] = np.random.randint(0, 7, len(df_features))
        df_features['is_weekend'] = (df_features['day_of_week'] >= 5).astype(int)
        df_features['is_business_hours'] = df_features['hour'].between(9, 17).astype(int)
    
    # Extraire d'autres features utiles
    for col in df_features.columns:
        # Extraire le niveau de risque si présent
        if any(keyword in col.lower() for keyword in ['risk', 'level', 'severity']):
            try:
                df_features[f'{col}_numeric'] = pd.to_numeric(
                    df_features[col], 
                    errors='coerce'
                ).fillna(0)
            except:
                pass
    
    return df_features


def filter_by_date_range(df, start_date, end_date):
    """Filtrer par plage de dates"""
    if df.empty:
        return df
    
    # Chercher les colonnes timestamp
    for ts_col in ['timestamp', '@timestamp']:
        if ts_col in df.columns:
            try:
                # S'assurer que la colonne est en datetime UTC
                df[ts_col] = pd.to_datetime(df[ts_col], errors='coerce', utc=True)
                
                # Convertir start_date et end_date en datetime avec fuseau
                start_dt = pd.to_datetime(start_date).tz_localize('UTC')
                end_dt = pd.to_datetime(end_date).tz_localize('UTC')
                
                mask = (df[ts_col] >= start_dt) & (df[ts_col] <= end_dt)
                return df[mask]
            except:
                continue
    
    return df


def get_summary_stats(df):
    """Obtenir des statistiques résumées"""
    if df.empty:
        return {}
    
    stats = {
        'total_records': len(df),
        'columns': len(df.columns),
        'dtypes': str(df.dtypes.value_counts().to_dict())
    }
    
    # Chercher dynamiquement les colonnes intéressantes
    for col in df.columns:
        # Chercher les IPs sources
        if any(keyword in col.lower() for keyword in ['source', 'src', 'ip']):
            try:
                stats['unique_sources'] = df[col].nunique()
                break
            except:
                pass
    
    for col in df.columns:
        # Chercher les actions
        if any(keyword in col.lower() for keyword in ['action', 'status']):
            try:
                stats['unique_actions'] = df[col].nunique()
                break
            except:
                pass
    
    # Chercher la plage de dates
    for ts_col in ['timestamp', '@timestamp']:
        if ts_col in df.columns:
            try:
                df[ts_col] = pd.to_datetime(df[ts_col], errors='coerce')
                valid_dates = df[ts_col].dropna()
                if len(valid_dates) > 0:
                    stats['date_range'] = {
                        'start': valid_dates.min(),
                        'end': valid_dates.max()
                    }
                break
            except:
                pass
    
    # Ajouter des métriques basées sur le contenu
    stats['memory_usage_mb'] = df.memory_usage(deep=True).sum() / 1024 / 1024
    stats['null_percentage'] = (df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100)
    
    return stats


def flatten_nested_columns(df):
    """Aplatir les colonnes avec des dictionnaires imbriqués (optionnel)"""
    if df.empty:
        return df
    
    flattened_data = []
    
    for idx, row in df.iterrows():
        flat_row = {}
        for key, value in row.items():
            if isinstance(value, dict):
                # Aplatir le dictionnaire
                for subkey, subvalue in value.items():
                    flat_key = f"{key}_{subkey}"
                    flat_row[flat_key] = subvalue
            elif isinstance(value, list):
                # Garder les listes comme strings
                flat_row[key] = str(value)
            else:
                flat_row[key] = value
        
        flattened_data.append(flat_row)
    
    return pd.DataFrame(flattened_data)
