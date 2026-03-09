import json
import re
from typing import Any

import pandas as pd
import requests

DEFAULT_OLLAMA_URL = "http://localhost:11434/api/generate"


def ask_llm(
    prompt: str,
    model: str = "llama3",
    url: str = DEFAULT_OLLAMA_URL,
    timeout: int = 60,
) -> str:
    """Appelle un LLM local (Ollama) et retourne la réponse texte."""
    response = requests.post(
        url,
        json={"model": model, "prompt": prompt, "stream": False},
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json().get("response", "")


def _extract_json_object(text: str) -> dict[str, Any]:
    """Extrait le premier objet JSON trouvé dans un texte."""
    text = text.strip()

    # Cas simple: la réponse est déjà un JSON valide.
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass

    # Cas fréquent: JSON entouré d'explications.
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError("Aucun objet JSON détecté dans la réponse LLM.")

    obj = json.loads(match.group(0))
    if not isinstance(obj, dict):
        raise ValueError("Le JSON extrait n'est pas un objet.")
    return obj


def _first_existing_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    lowered = {c.lower(): c for c in df.columns}
    for col in candidates:
        if col.lower() in lowered:
            return lowered[col.lower()]
    return None


def _detect_quartier_column(df: pd.DataFrame) -> str | None:
    return _first_existing_column(
        df,
        [
            "quartier",
            "district",
            "arrondissement",
            "zone",
            "secteur",
            "localisation",
            "ville_quartier",
        ],
    )


def _detect_text_columns(df: pd.DataFrame) -> list[str]:
    candidates = [
        "description",
        "texte",
        "titre",
        "title",
        "annonce",
        "resume_annonce",
    ]
    result = []
    lowered = {c.lower(): c for c in df.columns}
    for col in candidates:
        if col.lower() in lowered:
            result.append(lowered[col.lower()])
    return result


def extract_structured_from_text(
    texte_annonce: str,
    model: str = "llama3",
) -> dict[str, Any]:
    """
    Extrait des champs structurés depuis le texte d'une annonce.

    Retourne un dict avec des valeurs typées (ou None si inconnu).
    """
    if not isinstance(texte_annonce, str) or not texte_annonce.strip():
        return {
            "type_bien": None,
            "surface_m2": None,
            "pieces": None,
            "chambres": None,
            "etage": None,
            "ascenseur": None,
            "balcon_ou_terrasse": None,
            "parking": None,
            "travaux_a_prevoir": None,
            "dpe": None,
            "prix_eur": None,
            "charges_eur_mois": None,
            "quartier": None,
            "atouts": [],
            "inconvenients": [],
        }

    prompt = f"""
Tu es un extracteur d'informations immobilières.
Réponds UNIQUEMENT avec un objet JSON valide (pas de markdown, pas de texte autour).
Si l'information est absente, mets null.

Schéma attendu:
{{
  "type_bien": "appartement|maison|studio|autre|null",
  "surface_m2": number|null,
  "pieces": integer|null,
  "chambres": integer|null,
  "etage": integer|null,
  "ascenseur": boolean|null,
  "balcon_ou_terrasse": boolean|null,
  "parking": boolean|null,
  "travaux_a_prevoir": boolean|null,
  "dpe": "A|B|C|D|E|F|G|null",
  "prix_eur": number|null,
  "charges_eur_mois": number|null,
  "quartier": string|null,
  "atouts": [string],
  "inconvenients": [string]
}}

Texte annonce:
\"\"\"{texte_annonce}\"\"\"
""".strip()

    raw = ask_llm(prompt, model=model)
    try:
        data = _extract_json_object(raw)
    except (ValueError, json.JSONDecodeError):
        data = {}

    defaults: dict[str, Any] = {
        "type_bien": None,
        "surface_m2": None,
        "pieces": None,
        "chambres": None,
        "etage": None,
        "ascenseur": None,
        "balcon_ou_terrasse": None,
        "parking": None,
        "travaux_a_prevoir": None,
        "dpe": None,
        "prix_eur": None,
        "charges_eur_mois": None,
        "quartier": None,
        "atouts": [],
        "inconvenients": [],
    }
    for key, value in defaults.items():
        data.setdefault(key, value)

    if not isinstance(data.get("atouts"), list):
        data["atouts"] = []
    if not isinstance(data.get("inconvenients"), list):
        data["inconvenients"] = []

    return data


def enrich_annonces_structured(
    df_annonces: pd.DataFrame,
    text_col: str | None = None,
    model: str = "llama3",
) -> pd.DataFrame:
    """
    Ajoute des colonnes structurées extraites du texte annonce.
    """
    df = df_annonces.copy()
    if df.empty:
        return df

    if text_col is None:
        text_cols = _detect_text_columns(df)
        if not text_cols:
            raise ValueError(
                "Aucune colonne texte détectée. Passe text_col explicitement."
            )
        text_col = text_cols[0]

    extracted_rows = []
    for txt in df[text_col].fillna("").astype(str):
        extracted_rows.append(extract_structured_from_text(txt, model=model))

    extracted_df = pd.DataFrame(extracted_rows)
    return pd.concat([df.reset_index(drop=True), extracted_df.reset_index(drop=True)], axis=1)


def summarize_by_quartier(
    df_annonces: pd.DataFrame,
    quartier_col: str | None = None,
    text_col: str | None = None,
    max_annonces_per_quartier: int = 30,
    model: str = "llama3",
) -> pd.DataFrame:
    """
    Génère un résumé IA par quartier à partir des annonces.

    Retourne une DataFrame:
    - quartier
    - nb_annonces
    - resume
    - profil_acheteur
    - points_forts (liste)
    - points_faibles (liste)
    """
    df = df_annonces.copy()
    if df.empty:
        return pd.DataFrame(
            columns=[
                "quartier",
                "nb_annonces",
                "resume",
                "profil_acheteur",
                "points_forts",
                "points_faibles",
            ]
        )

    if quartier_col is None:
        quartier_col = _detect_quartier_column(df)
    if quartier_col is None:
        raise ValueError(
            "Aucune colonne quartier détectée. Passe quartier_col explicitement."
        )

    if text_col is None:
        text_cols = _detect_text_columns(df)
        if not text_cols:
            raise ValueError(
                "Aucune colonne texte détectée. Passe text_col explicitement."
            )
        text_col = text_cols[0]

    results: list[dict[str, Any]] = []

    grouped = df.groupby(quartier_col, dropna=False)
    for quartier, group in grouped:
        q_name = str(quartier) if pd.notna(quartier) else "Inconnu"
        sample = group[text_col].fillna("").astype(str).head(max_annonces_per_quartier).tolist()
        sample = [s.strip() for s in sample if s.strip()]
        corpus = "\n\n---\n\n".join(sample)

        if not corpus:
            results.append(
                {
                    "quartier": q_name,
                    "nb_annonces": len(group),
                    "resume": "Aucune description exploitable.",
                    "profil_acheteur": None,
                    "points_forts": [],
                    "points_faibles": [],
                }
            )
            continue

        prompt = f"""
Tu es analyste immobilier local.
À partir des annonces ci-dessous pour un quartier, génère UNIQUEMENT un JSON valide.

Schéma:
{{
  "resume": "3 à 5 phrases factuelles",
  "profil_acheteur": "profil acheteur/investisseur le plus adapté",
  "points_forts": ["..."],
  "points_faibles": ["..."]
}}

Quartier: {q_name}
Annonces:
\"\"\"{corpus}\"\"\"
""".strip()

        raw = ask_llm(prompt, model=model)
        try:
            data = _extract_json_object(raw)
        except (ValueError, json.JSONDecodeError):
            data = {
                "resume": "Résumé indisponible (réponse LLM non structurée).",
                "profil_acheteur": None,
                "points_forts": [],
                "points_faibles": [],
            }

        results.append(
            {
                "quartier": q_name,
                "nb_annonces": len(group),
                "resume": data.get("resume"),
                "profil_acheteur": data.get("profil_acheteur"),
                "points_forts": data.get("points_forts", []),
                "points_faibles": data.get("points_faibles", []),
            }
        )

    return pd.DataFrame(results)
