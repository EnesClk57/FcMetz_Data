# Projet FC Metz — Base de données multi-sources Ligue 1

Centralisation et structuration des données football Ligue 1 à partir de trois sources : **StatsBomb** (événements), **SkillCorner** (données physiques) et **Transfermarkt** (valeurs marchandes).

---

## Installation

**Prérequis : Python 3.10 ou supérieur**

Installer les dépendances :

```bash
pip install requests pandas beautifulsoup4 duckdb
```

| Bibliothèque | Rôle |
|---|---|
| `requests` | Appels HTTP vers les APIs StatsBomb et SkillCorner |
| `pandas` | Manipulation des données sous forme de tableaux |
| `beautifulsoup4` | Parsing HTML pour le scraping Transfermarkt |
| `duckdb` | Base de données analytique locale |

## Configuration

1. renommé  le fichier config.example.py en config.py  :

```bash
cp config.example.py config.py
```

2. Ouvrir `config.py` et renseigner ses identifiants StatsBomb et SkillCorner.

---

Le fichier `notebook.ipynb` sert de fichier de test : il démontre que chaque source est correctement accessible et retourne des données cohérentes (StatsBomb, SkillCorner, Transfermarkt), indépendamment du pipeline.

## État du pipeline

Le fichier `pipeline.py` contient les fonctions d'ingestion **StatsBomb** (compétitions et matchs) ainsi que le helper d'aplatissement des événements. Les autres fonctions n'ont pas été implémentées par manque de temps — leur logique est détaillée ci-dessous.

**Fonctions implémentées :**
- `creer_connexion()` — ouvre/crée le fichier DuckDB
- `ingerer_competitions()` → table `competitions`
- `ingerer_matchs()` → table `matches`
- `_aplatir_evenements()` — helper pour aplatir les colonnes imbriquées StatsBomb

---

## Fonctions non implémentées (manque de temps)

### `ingerer_evenements(con, df_matchs, max_matchs=None)` → table `events`

Aurait itéré sur chaque ligne du DataFrame `df_matchs` pour appeler `recuperer_evenements(match_id)` match par match. Chaque réponse de l'API retourne les actions du match sous forme d'objets JSON imbriqués — d'où la nécessité du helper `_aplatir_evenements()` déjà écrit, qui extrait les colonnes exploitables (`player_id_statsbomb`, `team_id_statsbomb`, `location_x/y`). Les DataFrames aplatis auraient été concaténés puis chargés dans DuckDB en une seule opération.

Le paramètre `max_matchs` aurait permis de limiter l'ingestion pour les tests (306 matchs × ~3 000 événements = ~900 000 lignes au total).

### `ingerer_donnees_physiques(con)` → table `physical_data`

Aurait récupéré la liste des matchs disponibles via `recuperer_matchs_disponibles()`, puis appelé `recuperer_tracking_match(id)` pour chacun. L'API SkillCorner retourne directement un tableau plat (pas de colonnes imbriquées), donc aucun aplatissement nécessaire — un simple `pd.concat` suivi d'un `CREATE OR REPLACE TABLE` aurait suffi. Environ 414 matchs × 25 joueurs = ~10 000 lignes.

### `ingerer_transfermarkt(con)` → table `transfermarkt_players`

Aurait appelé `recuperer_tous_joueurs_ligue1()` du module `transfermarkt/scraping.py`, qui scrape les 18 équipes de Ligue 1 et retourne un DataFrame `(joueur, valeur_marchande, equipe)`. Ce DataFrame aurait été chargé directement dans DuckDB.

### `afficher_resume(con)`

Aurait simplement affiché le nombre de lignes de chaque table après ingestion pour vérifier que le pipeline s'est bien exécuté.

---

## Schéma de la base de données

```
competitions ──► matches ──► events          (StatsBomb)
                              ↑ non implémentée

physical_data                                (SkillCorner — non implémentée)

transfermarkt_players                        (Transfermarkt — non implémentée)
```

### Table `competitions` 
| Colonne | Type | Description |
|---|---|---|
| competition_id | INTEGER | ID StatsBomb de la compétition |
| season_id | INTEGER | ID StatsBomb de la saison |
| season_name | VARCHAR | ex. "2025/2026" |

### Table `matches` 
| Colonne | Type | Description |
|---|---|---|
| match_id | INTEGER | ID StatsBomb (clé primaire) |
| match_date | DATE | Date du match |
| equipe_domicile | VARCHAR | Nom équipe à domicile |
| equipe_exterieur | VARCHAR | Nom équipe à l'extérieur |
| home_score / away_score | INTEGER | Score |
| match_week | INTEGER | Journée de championnat |
| stade / arbitre | VARCHAR | Infos match |

### Table `events` (non implémentée)
| Colonne | Type | Description |
|---|---|---|
| event_id | VARCHAR | UUID StatsBomb de l'événement |
| match_id | INTEGER | Lien vers `matches` |
| period / minute / second | INTEGER | Timing de l'action |
| type_evenement | VARCHAR | Pass, Shot, Dribble, Pressure... |
| joueur | VARCHAR | Nom du joueur |
| player_id_statsbomb | INTEGER | ID joueur StatsBomb |
| equipe | VARCHAR | Nom de l'équipe |
| team_id_statsbomb | INTEGER | ID équipe StatsBomb |
| location_x / location_y | FLOAT | Position sur le terrain (0-120 / 0-80) |

### Table `physical_data` (non implémentée)
| Colonne | Type | Description |
|---|---|---|
| player_id | INTEGER | ID joueur SkillCorner |
| player_name | VARCHAR | Nom du joueur |
| player_birthdate | DATE | Date de naissance |
| match_id | INTEGER | ID match SkillCorner |
| match_date | DATE | Date du match |
| team_name | VARCHAR | Équipe |
| + ~35 métriques physiques | FLOAT | distance, sprints, vitesse max, HSR, COD... |

### Table `transfermarkt_players` (non implémentée)
| Colonne | Type | Description |
|---|---|---|
| joueur | VARCHAR | Nom du joueur (tel que Transfermarkt l'affiche) |
| valeur_marchande | VARCHAR | ex. "45,00 Mio. €" |
| equipe | VARCHAR | Nom de l'équipe |

---

## Choix techniques

### Pourquoi DuckDB ?

DuckDB est une base de données **analytique orientée colonne** (OLAP), sans serveur, stockée dans un seul fichier. C'est le choix idéal pour ce projet car :

- **Zéro infrastructure** : un fichier `.duckdb`, pas de serveur à lancer
- **Intégration pandas native** : `CREATE TABLE AS SELECT * FROM dataframe` fonctionne directement
- **Performances analytiques** : optimisé pour les agrégations et jointures sur de grands volumes
- **SQL standard** : compatible avec toutes les requêtes d'analyse habituelles
- **Portabilité** : le fichier `.duckdb` peut être partagé tel quel

Pour ce type de projet (agrégations de stats, jointures entre sources, requêtes ad hoc), DuckDB est bien plus adapté qu'une base transactionnelle comme PostgreSQL ou SQLite.

---

## Stratégie de correspondance des IDs joueurs (non implémentée)

C'est **le défi principal** du projet : StatsBomb, SkillCorner et Transfermarkt ont chacun leurs propres identifiants de joueurs, sans clé commune.

### Approche envisagée

**1. SkillCorner - StatsBomb**
- Les deux sources exposent `player_name` et `player_birthdate`
- Jointure par `(nom_normalisé, date_de_naissance)` — clé quasi-unique
- En cas d'ambiguïté : déduplication par `team_name` sur le même match

**2. - Transfermarkt**
- Transfermarkt n'expose pas de date de naissance dans le scraping de base
- Enrichir le scraping pour récupérer la page joueur (`/profil/spieler/{id}`) qui contient la date de naissance
- Puis jointure par `(nom_normalisé, date_de_naissance)` identique

**3. Gestion des cas complexes**
- Noms composés dans un ordre différent (ex. "Kang-In Lee" vs "Lee Kang-In")
- Prénoms abrégés ou absents
- Solution : **matching flou** avec la librairie `rapidfuzz` (ratio de similarité > 85 %)

```python
from rapidfuzz import fuzz
score = fuzz.token_sort_ratio("Lucas Hernandez", "Lucas François Hernández Pi")
#  nécessite un seuil adapté + vérification croisée par équipe
```

**Table de correspondance manuelle** : pour les ~5 % de cas non résolus automatiquement, maintenir une table `id_mapping` gérée manuellement.

---

