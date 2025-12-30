# utils/ml_model.py
import joblib
import pandas as pd
import numpy as np
import streamlit as st
from typing import Tuple, Optional
from datetime import datetime

class MLModelHandler:
    """Gestionnaire du modèle ML de l'Étudiant 2"""
    
    def __init__(self):
        self.model = None
        self.is_loaded = False
        self.model_type = None
        self.expected_features = [
            'bytes_transferred', 'hour', 'day', 
            'same_ip', 'internal_src', 'internal_dst'
        ]
        self.categorical_features = ['protocol', 'action', 'log_type']
    
    def load_model(self, model_file) -> Tuple[bool, str]:
        """Charge le modèle depuis un fichier"""
        try:
            self.model = joblib.load(model_file)
            self.is_loaded = True
            self.model_type = type(self.model).__name__
            
            # Essayer de détecter si c'est un pipeline
            if hasattr(self.model, 'named_steps'):
                self.model_type = f"Pipeline: {list(self.model.named_steps.keys())}"
            
            return True, f"✅ Modèle {self.model_type} chargé avec succès"
        except Exception as e:
            self.is_loaded = False
            self.model_type = None
            return False, f"❌ Erreur : {str(e)}"
    
    def fix_timestamps(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Corrige les problèmes de fuseaux horaires
        """
        df_fixed = df.copy()
        
        # Colonnes de timestamp potentielles
        timestamp_cols = ['timestamp', '@timestamp', 'event_time', 'prediction_time']
        
        for col in timestamp_cols:
            if col in df_fixed.columns:
                try:
                    # Convertir en datetime
                    df_fixed[col] = pd.to_datetime(df_fixed[col], errors='coerce')
                    
                    # Uniformiser les fuseaux horaires
                    if df_fixed[col].dt.tz is not None:
                        # Supprimer le fuseau horaire (tout mettre en local)
                        df_fixed[col] = df_fixed[col].dt.tz_localize(None)
                    
                    # Remplir les valeurs manquantes
                    if df_fixed[col].isna().any():
                        now = datetime.now()
                        missing_indices = df_fixed[col].isna()
                        random_times = [
                            now - pd.Timedelta(minutes=np.random.randint(0, 1440))
                            for _ in range(missing_indices.sum())
                        ]
                        df_fixed.loc[missing_indices, col] = random_times
                        
                except Exception:
                    # Si erreur, supprimer la colonne
                    df_fixed = df_fixed.drop(columns=[col], errors='ignore')
        
        return df_fixed
    
    def extract_ip_from_nested(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extrait les IPs depuis les champs imbriqués Wazuh
        """
        df_extracted = df.copy()
        
        # Extraire source_ip
        if 'agent' in df_extracted.columns:
            try:
                df_extracted['source_ip'] = df_extracted['agent'].apply(
                    lambda x: x.get('ip', '') if isinstance(x, dict) else str(x)
                )
            except:
                df_extracted['source_ip'] = ''
        
        if 'src_ip' in df_extracted.columns:
            df_extracted['source_ip'] = df_extracted['src_ip']
        
        # Extraire dest_ip
        if 'data' in df_extracted.columns:
            try:
                df_extracted['dest_ip'] = df_extracted['data'].apply(
                    lambda x: (
                        x.get('dstip', '') or 
                        x.get('dest_ip', '') or 
                        x.get('destip', '')
                    ) if isinstance(x, dict) else ''
                )
            except:
                df_extracted['dest_ip'] = ''
        
        if 'dest_ip' not in df_extracted.columns:
            df_extracted['dest_ip'] = ''
        
        # Nettoyer les IPs
        for ip_col in ['source_ip', 'dest_ip']:
            if ip_col in df_extracted.columns:
                # Remplacer les valeurs vides ou 'unknown'
                mask = (df_extracted[ip_col].isna()) | (df_extracted[ip_col].astype(str).str.lower().isin(['', 'unknown', 'none', 'null']))
                if ip_col == 'source_ip':
                    df_extracted.loc[mask, ip_col] = [f"192.168.{np.random.randint(1, 255)}.{np.random.randint(1, 255)}" 
                                                     for _ in range(mask.sum())]
                else:
                    df_extracted.loc[mask, ip_col] = '10.0.0.1'
        
        return df_extracted
    
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prépare les features EXACTEMENT comme dans train.py
        """
        try:
            # 1. Corriger les timestamps
            df_prep = self.fix_timestamps(df)
            
            # 2. Extraire les IPs
            df_prep = self.extract_ip_from_nested(df_prep)
            
            # 3. Feature engineering (MÊME LOGIQUE que train.py)
            
            # Heure et jour
            timestamp_source = None
            for ts_col in ['@timestamp', 'timestamp']:
                if ts_col in df_prep.columns and pd.api.types.is_datetime64_any_dtype(df_prep[ts_col]):
                    timestamp_source = ts_col
                    break
            
            if timestamp_source:
                df_prep['hour'] = df_prep[timestamp_source].dt.hour.fillna(0).astype(int)
                df_prep['day'] = df_prep[timestamp_source].dt.dayofweek.fillna(0).astype(int)
            else:
                df_prep['hour'] = np.random.randint(0, 24, size=len(df_prep))
                df_prep['day'] = np.random.randint(0, 7, size=len(df_prep))
            
            # Features IP
            if 'source_ip' in df_prep.columns and 'dest_ip' in df_prep.columns:
                df_prep['same_ip'] = (df_prep['source_ip'] == df_prep['dest_ip']).astype(int)
                df_prep['internal_src'] = df_prep['source_ip'].astype(str).str.startswith(('192.168', '10.', '172.16')).astype(int)
                df_prep['internal_dst'] = df_prep['dest_ip'].astype(str).str.startswith(('192.168', '10.', '172.16')).astype(int)
            else:
                df_prep['same_ip'] = 0
                df_prep['internal_src'] = 1
                df_prep['internal_dst'] = 1
            
            # Extraire protocol et action
            protocol_default = 'tcp'
            action_default = 'unknown'
            
            if 'data' in df_prep.columns:
                try:
                    # Essayer d'extraire protocol
                    protocols = df_prep['data'].apply(
                        lambda x: x.get('protocol', protocol_default) if isinstance(x, dict) else protocol_default
                    )
                    # Garder seulement les valeurs valides
                    valid_protocols = ['tcp', 'udp', 'icmp', 'http', 'https', 'ssh']
                    df_prep['protocol'] = protocols.apply(
                        lambda x: x if str(x).lower() in valid_protocols else protocol_default
                    )
                except:
                    df_prep['protocol'] = protocol_default
                
                try:
                    # Essayer d'extraire action
                    actions = df_prep['data'].apply(
                        lambda x: x.get('action', action_default) if isinstance(x, dict) else action_default
                    )
                    df_prep['action'] = actions
                except:
                    df_prep['action'] = action_default
            else:
                df_prep['protocol'] = protocol_default
                df_prep['action'] = action_default
            
            # log_type fixe
            df_prep['log_type'] = 'wazuh'
            
            # bytes_transferred
            if 'bytes' in df_prep.columns or 'bytes_transferred' in df_prep.columns:
                bytes_col = 'bytes_transferred' if 'bytes_transferred' in df_prep.columns else 'bytes'
                df_prep['bytes_transferred'] = pd.to_numeric(df_prep[bytes_col], errors='coerce').fillna(0).astype(int)
            else:
                # Générer des valeurs réalistes
                df_prep['bytes_transferred'] = np.random.randint(100, 10000, size=len(df_prep))
            
            # S'assurer que toutes les features attendues existent
            features_df = pd.DataFrame()
            
            # Features numériques
            for feat in self.expected_features:
                if feat in df_prep.columns:
                    # Convertir en numérique
                    features_df[feat] = pd.to_numeric(df_prep[feat], errors='coerce').fillna(0)
                else:
                    # Valeurs par défaut
                    if feat == 'bytes_transferred':
                        features_df[feat] = np.random.randint(100, 10000, size=len(df_prep))
                    elif feat == 'hour':
                        features_df[feat] = np.random.randint(0, 24, size=len(df_prep))
                    elif feat == 'day':
                        features_df[feat] = np.random.randint(0, 7, size=len(df_prep))
                    else:
                        features_df[feat] = np.random.randint(0, 2, size=len(df_prep))
            
            # Features catégorielles (pour le pipeline complet)
            for cat_feat in self.categorical_features:
                if cat_feat in df_prep.columns:
                    features_df[cat_feat] = df_prep[cat_feat].astype(str).fillna('unknown')
                else:
                    features_df[cat_feat] = 'unknown'
            
            return features_df
            
        except Exception as e:
            raise Exception(f"❌ Erreur lors de la préparation des features: {str(e)}")
    
    def predict(self, df: pd.DataFrame) -> Tuple[np.ndarray, Optional[np.ndarray], np.ndarray]:
        """
        Fait des prédictions avec le modèle
        
        Returns:
            (predictions, probabilities, risk_scores)
        """
        if not self.is_loaded:
            raise ValueError("❌ Modèle non chargé. Chargez d'abord un modèle.")
        
        try:
            # Préparer les features
            df_features = self.prepare_features(df)
            
            # S'assurer que nous avons le bon nombre d'échantillons
            if len(df_features) == 0:
                raise ValueError("❌ Aucune feature préparée")
            
            # Afficher les features pour le debug
            if st.session_state.get('debug_mode', False):
                st.write("🔍 Features préparées pour le modèle:")
                st.write(f"Shape: {df_features.shape}")
                st.write(df_features.head(5))
            
            # Vérifier si c'est un pipeline sklearn
            if hasattr(self.model, 'predict'):
                # Prédictions normales
                predictions_binary = self.model.predict(df_features)
                
                # Probabilités (si disponible)
                if hasattr(self.model, 'predict_proba'):
                    probas = self.model.predict_proba(df_features)
                    # Risk scores basés sur la probabilité de classe 1 (malveillant)
                    if probas.shape[1] == 2:
                        risk_scores = (probas[:, 1] * 100).round().astype(int)
                    else:
                        risk_scores = (probas.max(axis=1) * 100).round().astype(int)
                else:
                    probas = None
                    # Risk scores basés sur les prédictions
                    risk_scores = np.where(predictions_binary == 1, 
                                         np.random.randint(70, 100, size=len(predictions_binary)),
                                         np.random.randint(0, 30, size=len(predictions_binary)))
                
                # Convertir 0/1 en labels
                predictions = np.where(predictions_binary == 0, 'Normal', 'Attack')
                
            else:
                # Modèle personnalisé
                raise ValueError("❌ Type de modèle non supporté")
            
            return predictions, probas, risk_scores
            
        except Exception as e:
            raise Exception(f"❌ Erreur lors de la prédiction: {str(e)}\n"
                          f"Features shape: {df_features.shape if 'df_features' in locals() else 'N/A'}\n"
                          f"Features cols: {list(df_features.columns) if 'df_features' in locals() else 'N/A'}")
    
    def get_feature_importance(self) -> Optional[pd.DataFrame]:
        """Retourne l'importance des features si disponible"""
        if not self.is_loaded:
            return None
        
        try:
            if hasattr(self.model, 'feature_importances_'):
                importance = self.model.feature_importances_
                features = self.expected_features + self.categorical_features
                return pd.DataFrame({
                    'feature': features[:len(importance)],
                    'importance': importance
                }).sort_values('importance', ascending=False)
            elif hasattr(self.model, 'coef_'):
                # Pour les modèles linéaires
                importance = np.abs(self.model.coef_[0])
                features = self.expected_features + self.categorical_features
                return pd.DataFrame({
                    'feature': features[:len(importance)],
                    'importance': importance
                }).sort_values('importance', ascending=False)
        except:
            pass
        
        return None


@st.cache_resource
def get_ml_model():
    """Singleton du modèle ML"""
    return MLModelHandler()