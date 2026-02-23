#!/usr/bin/env python3
"""
Pipeline d'ingestion — charge les données StatsBomb dans DuckDB.
Les ingestions SkillCorner, Transfermarkt et la fonction main()
sont documentées dans le README (non implémentées par manque de temps).
"""

import os
import sys
import duckdb
import pandas as pd

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from statsbomb.competitions import recuperer_saison_recente_ligue1
from statsbomb.matchs import recuperer_matchs

DB_CHEMIN = "donnees/football.duckdb"


# ─── Connexion et utilitaires
def creer_connexion() -> duckdb.DuckDBPyConnection:
    """
    Crée le dossier donnees/ si absent, puis ouvre (ou crée) le fichier
    DuckDB. Retourne la connexion à utiliser dans toutes les fonctions
    d'ingestion.
    """
    os.makedirs("donnees", exist_ok=True)
    return duckdb.connect(DB_CHEMIN)


# ─── StatsBomb et utilitaires
def ingerer_competitions(con: duckdb.DuckDBPyConnection, saison: dict) -> None:
    """
    Récupère la saison Ligue 1 la plus récente via l'API StatsBomb et
    l'insère dans la table competitions.
    Utilise CREATE OR REPLACE pour que le pipeline soit relançable sans erreur.
    """
    print(" Compétitions StatsBomb...")
    df = pd.DataFrame([saison])
    con.register("_competitions", df)
    con.execute("CREATE OR REPLACE TABLE competitions AS SELECT * FROM _competitions")
    print(f"  {len(df)} saison(s) chargée(s)")


def ingerer_matchs(con: duckdb.DuckDBPyConnection, saison: dict) -> pd.DataFrame:
    """
    Récupère tous les matchs de la saison via l'API StatsBomb et les insère
    dans la table matches. Retourne le DataFrame pour permettre aux fonctions
    suivantes d'itérer sur les match_id (notamment pour les événements).
    """
    print(" Matchs StatsBomb...")
    df = recuperer_matchs(saison["competition_id"], saison["season_id"])
    con.register("_matchs", df)
    con.execute("CREATE OR REPLACE TABLE matches AS SELECT * FROM _matchs")
    print(f"  {len(df)} matchs chargés")
    return df


def _aplatir_evenements(df: pd.DataFrame, match_id: int) -> pd.DataFrame:
    """
    Fonction utilitaire appelée par ingerer_evenements() (voir README).
    Les événements StatsBomb contiennent des colonnes imbriquées (dicts, listes).
    Cette fonction les aplatit en colonnes simples exploitables en SQL :
      - player_id_statsbomb  : extrait de la colonne 'player' (dict)
      - team_id_statsbomb    : extrait de la colonne 'team' (dict)
      - location_x/y         : extrait de la colonne 'location' ([x, y])
    Le match_id est ajouté manuellement car il n'est pas présent dans la
    réponse de l'API StatsBomb events.
    """
    out = pd.DataFrame()
    out["event_id"]            = df["id"]
    out["match_id"]            = match_id
    out["period"]              = df.get("period")
    out["minute"]              = df.get("minute")
    out["second"]              = df.get("second")
    out["type_evenement"]      = df.get("type_evenement")
    out["joueur"]              = df.get("joueur")
    out["player_id_statsbomb"] = df["player"].apply(
        lambda x: x.get("id") if isinstance(x, dict) else None
    )
    out["equipe"]              = df.get("equipe")
    out["team_id_statsbomb"]   = df["team"].apply(
        lambda x: x.get("id") if isinstance(x, dict) else None
    )
    out["location_x"]          = df["location"].apply(
        lambda x: x[0] if isinstance(x, list) and len(x) >= 1 else None
    )
    out["location_y"]          = df["location"].apply(
        lambda x: x[1] if isinstance(x, list) and len(x) >= 2 else None
    )
    return out
