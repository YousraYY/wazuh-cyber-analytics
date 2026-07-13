# utils/field_extractor.py - NOUVEAU FICHIER
import json
import pandas as pd
import streamlit as st

def extract_nested_field(df, field_path):
    """
    Extraire un champ imbriqué d'un DataFrame
    Exemple: 'agent.id' ou 'rule.description'
    """
    if df.empty:
        return pd.Series([], dtype=object)
    
    values = []
    for item in df.iloc[:, 0] if len(df.columns) == 1 else df.itertuples(index=False):
        try:
            # Convertir en dict si c'est une string JSON
            if isinstance(item, str) and (item.startswith('{') or item.startswith('[')):
                data = json.loads(item)
            elif hasattr(item, '__dict__'):
                data = item.__dict__
            else:
                data = item
            
            # Naviguer dans le chemin
            keys = field_path.split('.')
            current = data
            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    current = None
                    break
            
            values.append(current)
        except:
            values.append(None)
    
    return pd.Series(values, name=field_path)

def get_available_fields(df, sample_size=5):
    """
    Détecter automatiquement les champs disponibles dans les logs
    """
    if df.empty:
        return []
    
    fields = set()
    
    # Prendre un échantillon
    sample = df.head(sample_size)
    
    for idx, row in sample.iterrows():
        for col in df.columns:
            value = row[col]
            if isinstance(value, str):
                try:
                    data = json.loads(value)
                    if isinstance(data, dict):
                        # Extraire les clés du dict
                        extract_dict_fields(data, '', fields)
                except:
                    # Si ce n'est pas du JSON, c'est juste une valeur simple
                    if value and value != 'unknown':
                        fields.add(col)
            elif isinstance(value, dict):
                extract_dict_fields(value, '', fields)
    
    return sorted(list(fields))

def extract_dict_fields(data, prefix, fields_set):
    """Helper pour extraire récursivement les champs d'un dict"""
    for key, value in data.items():
        field_name = f"{prefix}.{key}" if prefix else key
        fields_set.add(field_name)
        
        if isinstance(value, dict):
            extract_dict_fields(value, field_name, fields_set)
        elif isinstance(value, list) and value and isinstance(value[0], dict):
            # Si c'est une liste de dicts, prendre le premier
            extract_dict_fields(value[0], field_name, fields_set)