"""
 Connexion à l'API StatsBomb
"""
import requests
from requests.auth import HTTPBasicAuth
import sys
import os

# On remonte d'un niveau pour accéder à config.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import STATSBOMB_IDENTIFIANT, STATSBOMB_MOT_DE_PASSE, STATSBOMB_URL_BASE

def creer_session() -> requests.Session:
    """
    Crée et retourne une session HTTP authentifiée pour l'API StatsBomb.
    Une session réutilise la connexion , ce qui est plus rapide qu'une requête isolée.
    """
    session = requests.Session()
    session.auth = HTTPBasicAuth(STATSBOMB_IDENTIFIANT, STATSBOMB_MOT_DE_PASSE)
    return session

def faire_requete(session: requests.Session, url: str) -> list | dict:
    """
    Effectue une requête GET et retourne les données JSON.
        session : la session authentifiée
        url     : l'URL complète à appeler
    Retourne :
        Les données JSON sous forme de liste ou dictionnaire
    """
    reponse = session.get(url)

    # On lève une erreur explicite si la requête échoue 
    reponse.raise_for_status()

    return reponse.json()
