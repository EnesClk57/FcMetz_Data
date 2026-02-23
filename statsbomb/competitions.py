"""
 Récupération des compétitions
"""

import pandas as pd
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import STATSBOMB_URL_BASE, LIGUE1_NOM_COMPETITION, LIGUE1_PAYS
from statsbomb.connexion import creer_session, faire_requete


def recuperer_toutes_competitions() -> pd.DataFrame:
    """Retourne toutes les compétitions disponibles  ."""
    session = creer_session()
    url = f"{STATSBOMB_URL_BASE}/v4/competitions"
    donnees = faire_requete(session, url)
    return pd.DataFrame(donnees)


def recuperer_saisons_ligue1() -> pd.DataFrame:
    """
    Filtre et retourne uniquement les saisons de Ligue 1 masculine
    disponibles .
    """
    competitions = recuperer_toutes_competitions()

    ligue1 = competitions[
        (competitions["country_name"].str.lower() == LIGUE1_PAYS.lower()) &
        (competitions["competition_name"].str.contains(LIGUE1_NOM_COMPETITION, case=False)) &
        (competitions["competition_gender"].str.lower() == "male")
    ].copy()

    return ligue1.sort_values("season_id", ascending=False).reset_index(drop=True)


def recuperer_saison_recente_ligue1() -> dict:
    """
    Retourne les infos de la saison Ligue 1 la plus récente.
    Format : {"competition_id": ..., "season_id": ..., "season_name": ...}
    """
    saisons = recuperer_saisons_ligue1()

    if saisons.empty:
        raise ValueError("Aucune saison Ligue 1 trouvée. Vérifiez vos accès StatsBomb.")

    saison = saisons.iloc[0]
    return {
        "competition_id": saison["competition_id"],
        "season_id":      saison["season_id"],
        "season_name":    saison["season_name"],
    }
