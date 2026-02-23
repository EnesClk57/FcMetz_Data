"""
  statsbomb/evenements.py — Récupération des événements
  Un "événement" = chaque action du match : passe, tir,
  dribble, faute, coup de pied arrêté...
"""
import pandas as pd
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import STATSBOMB_URL_BASE
from statsbomb.connexion import creer_session, faire_requete


def recuperer_evenements(id_match: int) -> pd.DataFrame:
    """
    Retourne tous les événements d'un match.
        id_match : identifiant unique du match
    """
    session = creer_session()
    url = f"{STATSBOMB_URL_BASE}/v8/events/{id_match}"
    donnees = faire_requete(session, url)
    df = pd.DataFrame(donnees)

    # Extraction du nom du type d'événement (objet imbriqué)
    df["type_evenement"] = df["type"].apply(lambda x: x["name"] if isinstance(x, dict) else x)

    # Extraction du nom du joueur
    df["joueur"] = df["player"].apply(lambda x: x["name"] if isinstance(x, dict) else None)

    # Extraction de l'équipe
    df["equipe"] = df["team"].apply(lambda x: x["name"] if isinstance(x, dict) else None)

    return df


def filtrer_par_type(df_evenements: pd.DataFrame, type_evenement: str) -> pd.DataFrame:
    """
    Filtre les événements par type.

    Exemples de types : 'Pass', 'Shot', 'Dribble', 'Foul Committed'

    Paramètres :
        df_evenements  : DataFrame retourné par recuperer_evenements()
        type_evenement : le type d'événement souhaité 
    """
    return df_evenements[df_evenements["type_evenement"] == type_evenement].copy()
