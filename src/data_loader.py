""" Ce fichier contient les fonctions de chargement des configurations et des données"""

# fonction de chargement des configurations
def load_config():
    import os
    import yaml

    # Obtenir le chemin d'accès d'un fichier présent dans le meme répertoire que ce script (le fichier config.yaml en l'occurrence)
    config_path = os.path.abspath('config/config.yaml')
    
    # chargement des configurations
    with open (config_path, 'r') as file:
        config = yaml.safe_load(file)

    return config


# Fonction pour charger les données
def load_data(config):
    import pandas as pd
    path = config['data']['raw_path']
    
    return pd.read_excel(path)

















