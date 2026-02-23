"""
  Données de tracking SkillCorner
"""
import requests
import pandas as pd
from requests.auth import HTTPBasicAuth
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SKILLCORNER_IDENTIFIANT, SKILLCORNER_MOT_DE_PASSE, SKILLCORNER_URL_BASE


def creer_session_skillcorner() -> requests.Session:
    """Crée une session authentifiée pour l'API SkillCorner."""
    session = requests.Session()
    session.auth = HTTPBasicAuth(SKILLCORNER_IDENTIFIANT, SKILLCORNER_MOT_DE_PASSE)
    return session


def recuperer_matchs_disponibles() -> pd.DataFrame:
    """
    Retourne la liste des matchs disponibles sur le compte SkillCorner.
    Chaque match aura un 'id' SkillCorner .
    """
    session = creer_session_skillcorner()
    url = f"{SKILLCORNER_URL_BASE}/matches/"
    reponse = session.get(url)
    reponse.raise_for_status()
    return pd.DataFrame(reponse.json()["results"])


def recuperer_tracking_match(id_match_skillcorner: int) -> pd.DataFrame:
    """
    Retourne les données physiques d'un match pour tous les joueurs.
    Colonnes importantes :
        - distance_totale    
        - sprints             
        - vitesse_max          
        - courses_haute_intensite 

        id_match_skillcorner : l'ID du match dans le système SkillCorner
    """
    session = creer_session_skillcorner()
    url = f"{SKILLCORNER_URL_BASE}/physical/"
    reponse = session.get(url, params={"match": id_match_skillcorner})
    reponse.raise_for_status()
    return pd.DataFrame(reponse.json()["results"])
