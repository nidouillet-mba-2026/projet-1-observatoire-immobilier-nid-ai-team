[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/JY1xUUGg)
# Projet 1 : Observatoire du Marche Immobilier Toulonnais

## Objectif

Construire une application web deployee qui analyse le marche immobilier toulonnais en temps reel, avec des algorithmes statistiques implementes from scratch.

## Evaluation automatique

A chaque `git push`, le CI evalue automatiquement votre travail.
Consultez l'onglet **Actions** > dernier workflow > **Job Summary** pour voir votre score.

**Score CI : jusqu'a 55 / 100** — les 45 points restants sont evalues en soutenance.

## Prérequis

- **Python** >= 3.1
- **pip** (gestionnaire de paquets Python)
- **Git** (pour cloner le dépôt)
- ~500 MB d'espace disque libre (données + dépendances)

### Dépendances principales

Le projet repose sur :
- **Streamlit** : framework pour l'interface web
- **Pandas** : analyse et manipulation de données
- **Pytest** : tests unitaires
- **BeautifulSoup4**  : scraping web
- **Playwright** : scraping web 

Tous les packages requis sont dans `requirements.txt`.

## Structure du projet

```
.
├── analysis/
│   ├── enrichment.py
│   ├── knn.py
│   ├── regression.py
│   ├── scoring.py
│   └── stats.py
│
├── data/
│   ├── annonces.csv
│   └── dvf_toulon.csv
│
├── scripts/
│   └── run_scrape_multi_sites.py
│
├── tests/
│   ├── tests_unitaires_analysis/
│   │   ├── test_enrichment.py
│   │   ├── test_knn.py
│   │   └── test_scoring.py
│   │
│   ├── generate_report.py
│   ├── test_auto_eval.py
│   ├── test_regression.py
│   └── test_stats.py
│
├── config.py
├── logo_niddouillet.png
├── README.md
├── requirements.txt
├── streamlit_app.py
├── test_quartiers.py
└── .gitignore
```

## Installation

1. Cloner le projet
Télécharger le dépôt Git sur votre machine :

git clone <url-du-repository>
cd <nom-du-repository>

2. Vérifier la version de Python
Le projet nécessite Python 3.10 ou supérieur.

3. Créer un environnement virtuel (recommandé)
Afin d’éviter les conflits de bibliothèques, il est recommandé de créer un environnement virtuel.
Créer l’environnement :
python -m venv venv

4. Activer l’environnement virtuel
Sur macOS / Linux
source venv/bin/activate

Sur Windows
venv\Scripts\activate

5. installer les dépendances requises 
pip install -r requirements.txt

6. Lancer l'application
Avant de lancer l'application, assurez-vous que :
Depuis la racine du projet, exécuter :
streamlit run app/streamlit_app.py

L’application démarre alors automatiquement dans le navigateur à l’adresse :
http://localhost:8501

7. Lancer l'application
Depuis la racine du projet, exécuter :
streamlit run app/streamlit_app.py
L’application démarre automatiquement dans votre navigateur à l’adresse :
http://localhost:8501
 

## Architecture

Le projet est organisé en plusieurs parties :

- `analysis/` : modules Python contenant les fonctions statistiques, de régression et de scoring développées from scratch.
- `app/` : code de l'application Streamlit qui constitue l'interface utilisateur.
- `data/` : jeux de données (DVF, annonces) utilisés pour l'analyse.
- `tests/` : tests unitaires et d'évaluation continue.


L'application s'affichera automatiquement dans votre navigateur à l'adresse :
```
http://localhost:8501
```

### Utilisation

- **Naviguer** : utilisez les onglets en haut pour accéder aux différentes sections
- **Filtrer** : modifiez les filtres dans le sidebar et l'app recalculera automatiquement
- **Télécharger** : les résultats peuvent être téléchargés en CSV depuis chaque onglet

### Arrêter l'application

Pour arrêter le serveur Streamlit, appuyez sur **Ctrl+C** dans le terminal.


### Port personnalisé

Si le port 8501 est déjà utilisé, vous pouvez changer le port :

```bash
streamlit run app/streamlit_app.py --server.port=8502
```

## Environment / Configuration

### Variables d'environnement optionnelles

Le projet fonctionne sans configuration particulière, mais vous pouvez personnaliser certains paramètres :

#### Pour l'enrichissement IA (Ollama)

Si vous utilisez la fonction d'enrichissement via Ollama (génération automatique d'attributs à partir des annonces) :

```bash
# Définir l'URL du serveur Ollama (par défaut : http://localhost:11434)
export OLLAMA_BASE_URL="http://localhost:11434"
```

**Note :** Ollama est optionnel. L'app fonctionne sans lui, mais certaines fonctionnalités d'enrichissement seront désactivées.

#### Installation d'Ollama (optionnel)

Si vous souhaitez activer l'enrichissement IA :

1. Installez [Ollama](https://ollama.ai) sur votre machine
2. Lancez le serveur : `ollama serve`
3. Téléchargez un modèle LLM (ex: `ollama pull llama3`)

### Fichiers de configuration

- `config.py` : chemins des fichiers (données, logo)
- `requirements.txt` : dépendances Python
- `.streamlit/config.toml` (optionnel) : configuration Streamlit avancée

### Données

Les fichiers de données doivent être dans le répertoire `data/` :

- `data/dvf_toulon.csv` — données DVF (Demandes de Valeurs Foncières)
- `data/annonces.csv` — annonces immobilières scrapées

Si ces fichiers manquent, l'app affichera une erreur mais continuera de fonctionner (certains onglets seront inactifs).

## Application deployée

**URL :** <(https://nid-ia-team.streamlit.app/)>

*(https://github.com/Aidan-Bouaicha/deploy-nidia)*

## Tests

### Lancer les tests unitaires

```bash
# Lancer tous les tests
pytest

# Lancer les tests d'une module spécifique
pytest tests/test_stats.py
pytest tests/test_regression.py
pytest tests/tests_unitaires_analysis/

Les résultats des tests s'affichent automatiquement. Consultez `tests/test_auto_eval.py` pour l'évaluation continue (CI/CD).


## Répartition du travail
|Emma BEN BOUJMAA | Data Engineer | Données et scraping |
| Aurélie RAMBOUT | AI Engineer / Data Scientist | Élaboration de l'algorithme et des badges |
| Aidan BOUAÏCHA | Frontend / DevOps | Backend et réactivité du site (filtres, performance) |
| Julie LA PORTA | Product Owner / UX Designer | Présentation, vision du projet |
| Julien CARCENAC | Frontend / UI Developer | Carte interactive et affichage des quartiers |

## Fonctionnalités / Features

L'application offre les capacités suivantes :

-  **Analyse statistique** des prix et tendances du marché immobilier toulonnais
-  **Filtrage avancé** par prix, surface, localisation, type de bien
-  **Scoring d'opportunité** : identifie les biens sous-évalués ou surévalués
-  **Carte interactive** de Toulon avec quartiers et détails par localisation
-  **Régression linéaire** basée sur des algorithmes from scratch (pas de scikit-learn)
-  **Données en temps réel** : DVF + annonces scrapées
-  **Interface réactive** : mise à jour instantanée lors des changements de filtres
-  **Badges visuels** : Opportunité / Surévalué / Marché Normal

## Roadmap / Améliorations futures

Voici les améliorations envisagées pour les prochaines versions :

-  **API REST** pour accéder aux données programmatiquement
-  **Version mobile** (responsive design amélioré)
-  **Machine Learning avancé** : prédiction de prix, clustering de quartiers
-  **Chatbot IA** pour conseiller les acheteurs/vendeurs
-  **Notifications** : alerter l'utilisateur quand une bonne opportunité apparaît
-  **Expansion géographique** : couvrir d'autres villes françaises
-  **Rapports PDF** : télécharger une analyse complète à conserver
-  **Authentification utilisateur** : sauvegarder ses favoris et recherches

## Donnees

- **DVF** : téléchargées depuis https://files.data.gouv.fr/geo-dvf/latest/csv/83/ (données historiques de Toulon, >= 500 transactions)
- **Annonces** : collectées via scraping Python sur SeLoger en temps réel (script `scripts/run_scrape_multi_sites.py`)

### Sources de données détaillées

| Source | Type | Fréquence | Couverture |
|--------|------|-----------|-----------|
| DVF (data.gouv.fr) | Historique officiel | Mise à jour annuelle | Transactions immobilières des 2 dernières années (2024-2025) |
| SeLoger | Annonces actuelles | Quotidien (via script) | Annonces actives de Toulon |

### Exécuter le scraping

Pour mettre à jour les annonces manuellement :

```bash
python scripts/run_scrape_multi_sites.py
```

Les données scrapées sont sauvegardées dans `data/annonces.csv`.


