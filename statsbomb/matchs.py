"""
  Récupération des matchs
"""

import pandas as pd
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import STATSBOMB_URL_BASE
from statsbomb.connexion import creer_session, faire_requete


def recuperer_matchs(id_competition: int, id_saison: int) -> pd.DataFrame:
    """
    Retourne tous les matchs d'une compétition et saison.
        id_competition : ex. l'ID de la Ligue 1
        id_saison      : ex. l'ID de la saison 2023/2024
    """
    session = creer_session()
    url = f"{STATSBOMB_URL_BASE}/v6/competitions/{id_competition}/seasons/{id_saison}/matches"
    donnees = faire_requete(session, url)
    df = pd.DataFrame(donnees)

    # Extraction des champs imbriqués pour faciliter la lecture
    df["equipe_domicile"]   = df["home_team"].apply(lambda x: x["home_team_name"])
    df["equipe_exterieur"]  = df["away_team"].apply(lambda x: x["away_team_name"])
    df["stade"]             = df["stadium"].apply(lambda x: x["name"] if isinstance(x, dict) else None)
    df["arbitre"]           = df["referee"].apply(lambda x: x["name"] if isinstance(x, dict) else None)

    colonnes = [
        "match_id", "match_date", "kick_off",
        "equipe_domicile", "home_score",
        "equipe_exterieur", "away_score",
        "stade", "arbitre", "match_week"
    ]
    return df[colonnes].sort_values("match_date").reset_index(drop=True)
