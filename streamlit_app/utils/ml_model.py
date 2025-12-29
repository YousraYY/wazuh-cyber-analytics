# utils/ml_model.py
import joblib
import pandas as pd
import numpy as np
import streamlit as st
from typing import Tuple

class MLModelHandler:
    """Gestionnaire du modèle ML de l'Étudiant 2"""
    
    def __init__(self):
        self.model = None
        self.is_loaded = False
        self.metrics = None
    
    def load_model(self, model_file) -> Tuple[bool, str]:
        """Charge le modèle depuis un fichier"""
        try:
            self.model = joblib.load(model_file)
            self.is_loaded = True
            return True, "✅ Modèle chargé avec succès"
        except Exception as e:
            self.is_loaded = False
            return False, f"❌ Erreur : {str(e)}"
    
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prépare les features EXACTEMENT comme dans train.py
        """
        df_prep = df.copy()
        
        # Feature engineering (MÊME LOGIQUE que train.py)
        if 'timestamp' in df_prep.columns:
            df_prep['timestamp'] = pd.to_datetime(df_prep['timestamp'], errors='coerce')
            df_prep['hour'] = df_prep['timestamp'].dt.hour.fillna(0).astype(int)
            df_prep['day'] = df_prep['timestamp'].dt.dayofweek.fillna(0).astype(int)
        else:
            df_prep['hour'] = 0
            df_prep['day'] = 0
        
        # IP features
        if 'agent' in df_prep.columns:
            # Extraire source_ip depuis agent.ip
            df_prep['source_ip'] = df_prep['agent'].apply(
                lambda x: x.get('ip', '') if isinstance(x, dict) else ''
            )
        
        if 'data' in df_prep.columns:
            # Extraire dest_ip depuis data
            df_prep['dest_ip'] = df_prep['data'].apply(
                lambda x: x.get('dstip', '') if isinstance(x, dict) else ''
            )
        
        # Créer les features IP
        if 'source_ip' in df_prep.columns and 'dest_ip' in df_prep.columns:
            df_prep['same_ip'] = (df_prep['source_ip'] == df_prep['dest_ip']).astype(int)
            df_prep['internal_src'] = df_prep['source_ip'].astype(str).str.startswith('192.168').astype(int)
            df_prep['internal_dst'] = df_prep['dest_ip'].astype(str).str.startswith('192.168').astype(int)
        else:
            df_prep['same_ip'] = 0
            df_prep['internal_src'] = 0
            df_prep['internal_dst'] = 0
        
        # Extraire protocol, action, log_type
        if 'data' in df_prep.columns:
            df_prep['protocol'] = df_prep['data'].apply(
                lambda x: x.get('protocol', 'unknown') if isinstance(x, dict) else 'unknown'
            )
            df_prep['action'] = df_prep['data'].apply(
                lambda x: x.get('action', 'unknown') if isinstance(x, dict) else 'unknown'
            )
        else:
            df_prep['protocol'] = 'unknown'
            df_prep['action'] = 'unknown'
        
        df_prep['log_type'] = 'wazuh'  # Type de log
        
        # bytes_transferred
        df_prep['bytes_transferred'] = 0  # Par défaut si pas disponible
        
        # Colonnes nécessaires pour le modèle
        required_cols = [
            'bytes_transferred',
            'hour',
            'day',
            'same_ip',
            'internal_src',
            'internal_dst',
            'protocol',
            'action',
            'log_type'
        ]
        
        # Vérifier que toutes les colonnes existent
        for col in required_cols:
            if col not in df_prep.columns:
                df_prep[col] = 0 if col in ['bytes_transferred', 'hour', 'day', 'same_ip', 'internal_src', 'internal_dst'] else 'unknown'
        
        return df_prep[required_cols]
    
    def predict(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Fait des prédictions avec le modèle
        
        Returns:
            (predictions, probabilities, risk_scores)
        """
        if not self.is_loaded:
            raise ValueError("Modèle non chargé")
        
        # Préparer les features
        df_features = self.prepare_features(df)
        
        # Prédictions
        predictions_binary = self.model.predict(df_features)
        probas = self.model.predict_proba(df_features)
        
        # Convertir 0/1 en labels
        predictions = np.where(predictions_binary == 0, 'Normal', 'Attack')
        
        # Risk scores (probabilité de la classe malveillante)
        risk_scores = (probas[:, 1] * 100).round(2)
        
        return predictions, probas, risk_scores


@st.cache_resource
def get_ml_model():
    """Singleton du modèle ML"""
    return MLModelHandler()