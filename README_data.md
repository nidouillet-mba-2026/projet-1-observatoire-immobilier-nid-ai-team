# README Data - Contribution DVF Toulon

## Objectif de ma contribution

Mettre en place un pipeline simple et reproductible pour preparer un dataset DVF Toulon exploitable dans l'application.

Cette partie couvre:
- la preparation des donnees DVF,
- le filtrage metier (Toulon, types de biens),
- le nettoyage de base pour l'analyse.

## Fichiers concernes

- `analysis/prepare_dvf.py` : script de preparation/nettoyage DVF
- `donnees/ValeursFoncieres-2024.txt` : source brute locale (non versionnee)
- `donnees/ValeursFoncieres-2025-S1.txt` : source brute locale (non versionnee)
- `data/dvf_toulon.csv` : sortie finale consolidee
- `.gitignore` : ignore les gros fichiers bruts DVF

## Source des donnees

- Portail officiel: https://www.data.gouv.fr/datasets/demandes-de-valeurs-foncieres
- Filtre projet:
- code INSEE Toulon: `83137`
- types: `Appartement`, `Maison`
- periode: 2 dernieres annees de travail (2024 + 2025-S1 dans cette version)

## Ce que fait le script

1. Lit les fichiers DVF bruts au format texte (`|`) en chunks pour limiter la RAM.
2. Filtre sur Toulon (`83137`) et sur les types `Appartement`/`Maison`.
3. Renomme les colonnes utiles (`date_mutation`, `valeur_fonciere`, `surface_reelle_bati`, etc.).
4. Convertit les types:
- dates (`%d/%m/%Y`)
- montants francais (`123456,78` -> float)
- numeriques (surfaces, pieces)
5. Garde les ventes exploitables (`nature_mutation == Vente`) et supprime les lignes invalides.
6. Calcule `prix_m2`.
7. Filtre des valeurs aberrantes simples (`prix_m2` et `valeur_fonciere`).
8. Supprime des doublons transactionnels.
9. Exporte `data/dvf_toulon.csv`.

## Resultat obtenu

- Fichier final: `data/dvf_toulon.csv`
- Dataset unique consolide (au lieu de plusieurs fichiers annuels)
- Volume: largement superieur au minimum de 500 transactions

## Reproduire en local

Depuis la racine du repo:

```powershell
.\.venv\Scripts\python.exe analysis/prepare_dvf.py
```

Verification rapide:

```powershell
.\.venv\Scripts\python.exe -c "import pandas as pd; df=pd.read_csv('data/dvf_toulon.csv'); print(df.head()); print('rows:', len(df)); print(df['type_local'].value_counts())"
```

## Notes projet

- Les fichiers bruts DVF restent dans `donnees/` pour regeneration locale.
- Les gros fichiers bruts ne doivent pas etre pushes.
- Le fichier a utiliser dans l'app est `data/dvf_toulon.csv`.
