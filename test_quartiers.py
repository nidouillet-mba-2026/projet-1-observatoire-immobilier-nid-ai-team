import pandas as pd
from pathlib import Path

# Simuler le chargement des données
DATA_DIR = Path("donnees")
ANNONCES_CSV = DATA_DIR / "annonces.csv"

print("=== Test des quartiers disponibles ===")

try:
    if ANNONCES_CSV.exists():
        annonces_df = pd.read_csv(ANNONCES_CSV)

        # Simuler la détection des quartiers
        def detect_quartier_from_description(description, titre):
            if not description and not titre:
                return None
            text = f"{str(titre or '')} {str(description or '')}".lower()
            quartiers_toulon = {
                'centre-ville': ['centre', 'centre-ville'],
                'toulon': ['toulon'],
                'hyères': ['hyères', 'hyeres'],
                'la seyne': ['seyne', 'la seyne'],
                'six fours': ['six fours', 'six-fours'],
            }
            for quartier, keywords in quartiers_toulon.items():
                for keyword in keywords:
                    if keyword in text:
                        return quartier.title()
            return None

        annonces_df['quartier_detecte'] = annonces_df.apply(
            lambda row: row['quartier'] if pd.notna(row['quartier']) and str(row['quartier']).strip()
            else detect_quartier_from_description(row.get('description'), row.get('titre')),
            axis=1
        )

        # Liste complète des quartiers
        quartiers_defaut = [
            "Centre-ville", "Saint Jean du Var", "La Valette", "La Garde", "Le Pradet",
            "Carqueiranne", "Hyères", "La Crau", "La Farlède", "Pierrefeu", "Cuers",
            "Solliès", "La Seyne", "Six Fours", "Sanary", "Bandol", "Cassis",
            "Marseille", "Nice", "Aix", "Avignon", "Toulon"
        ]

        quartiers_detectes = sorted([str(q) for q in annonces_df['quartier_detecte'].dropna().unique().tolist() if q])
        quartiers_uniques = sorted(list(set(quartiers_defaut + quartiers_detectes)))

        print(f"Nombre total de quartiers disponibles: {len(quartiers_uniques)}")
        print("Liste des quartiers:")
        for i, quartier in enumerate(quartiers_uniques[:15], 1):
            print(f"  {i}. {quartier}")

        if len(quartiers_uniques) > 15:
            print(f"  ... et {len(quartiers_uniques) - 15} autres quartiers")

    else:
        print("❌ Fichier annonces.csv non trouvé")

except Exception as e:
    print(f"❌ Erreur: {e}")

print("\n✅ Test terminé")
