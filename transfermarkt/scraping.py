"""
-  Prérequis : pip install requests beautifulsoup4
- On récupère les valeurs marchandes des joueurs de Ligue 1
  depuis le site Transfermarkt.
      - délai entre chaque requête 
      - en-tête "User-Agent" 
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# simuler un vrai navigateur (sinon Transfermarkt bloque)
ENTETES = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

URL_LIGUE1 = "https://www.transfermarkt.fr/ligue-1/startseite/wettbewerb/FR1"

def recuperer_equipes_ligue1() -> list[dict]:
    """
    Scrape et retourne la liste des équipes de Ligue 1
    avec leur URL Transfermarkt et leur valeur totale d'effectif.
    """
    reponse = requests.get(URL_LIGUE1, headers=ENTETES)
    reponse.raise_for_status()

    # On parse le HTML de la page
    soup = BeautifulSoup(reponse.text, "html.parser")

    equipes = []
    tableau = soup.find("table", class_="items")

    if not tableau:
        raise ValueError("Structure HTML Transfermarkt non trouvée.")

    for ligne in tableau.find_all("tr", class_=["odd", "even"]):
        cellules = ligne.find_all("td")
        if len(cellules) < 3:
            continue

        # Il y a 2 liens /startseite/verein/ par ligne : 1 avec image (logo), 1 avec texte
        liens = ligne.find_all("a", href=lambda h: h and "/startseite/verein/" in h)
        lien_equipe = next((l for l in liens if l.get_text(strip=True)), None)
        if not lien_equipe:
            continue

        equipes.append({
            "equipe":            lien_equipe.get_text(strip=True),
            "url_transfermarkt": "https://www.transfermarkt.fr" + lien_equipe["href"],
        })

    return equipes


def recuperer_joueurs_equipe(url_equipe: str, delai_secondes: float = 1.5) -> pd.DataFrame:
    """
    Scrape et retourne les joueurs d'une équipe avec leur valeur marchande.
        url_equipe      : URL Transfermarkt de l'équipe
        delai_secondes  : pause avant la requête pour ne pas surcharger le site
    """
    time.sleep(delai_secondes)  # Pause de politesse

    reponse = requests.get(url_equipe, headers=ENTETES)
    reponse.raise_for_status()

    soup = BeautifulSoup(reponse.text, "html.parser")
    joueurs = []

    tableau = soup.find("table", class_="items")
    if not tableau:
        return pd.DataFrame()

    for ligne in tableau.find_all("tr", class_=["odd", "even"]):
        cellules = ligne.find_all("td")
        if len(cellules) < 6:
            continue

        # Sélecteur robuste basé sur l'URL plutôt que la classe CSS (qui change)
        nom = ligne.find("a", href=lambda h: h and "/profil/spieler/" in h)
        valeur = cellules[-1].get_text(strip=True)  

        if nom:
            joueurs.append({
                "joueur":           nom.get_text(strip=True),
                "valeur_marchande": valeur,
            })

    return pd.DataFrame(joueurs)


def recuperer_tous_joueurs_ligue1() -> pd.DataFrame:
    """
    Récupère les joueurs et valeurs marchandes de toutes les équipes de Ligue 1..
    """
    equipes = recuperer_equipes_ligue1()
    print(f" {len(equipes)} équipes trouvées. Scraping en cours...")

    tous_joueurs = []

    for i, equipe in enumerate(equipes, 1):
        print(f"  ({i}/{len(equipes)}) {equipe['equipe']}...")
        df_equipe = recuperer_joueurs_equipe(equipe["url_transfermarkt"])
        df_equipe["equipe"] = equipe["equipe"]
        tous_joueurs.append(df_equipe)

    return pd.concat(tous_joueurs, ignore_index=True)
