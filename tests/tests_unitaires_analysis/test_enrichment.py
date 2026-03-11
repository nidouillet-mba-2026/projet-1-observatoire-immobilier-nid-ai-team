import pandas as pd
import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from analysis import enrichment

def test_extract_json_object_with_plain_json():
    text = '{"surface_m2": 45, "pieces": 2}'
    result = enrichment._extract_json_object(text)
    assert result["surface_m2"] == 45
    assert result["pieces"] == 2


def test_extract_json_object_with_wrapped_json():
    text = 'Voici la réponse : {"quartier": "Centre", "prix_eur": 150000} merci'
    result = enrichment._extract_json_object(text)
    assert result["quartier"] == "Centre"
    assert result["prix_eur"] == 150000


def test_extract_json_object_raises_when_no_json():
    with pytest.raises(ValueError):
        enrichment._extract_json_object("aucun objet json ici")


def test_first_existing_column_detects_column_case_insensitive():
    df = pd.DataFrame(columns=["Titre", "Description", "Prix"])
    result = enrichment._first_existing_column(df, ["description", "texte"])
    assert result == "Description"


def test_detect_quartier_column_returns_matching_name():
    df = pd.DataFrame(columns=["prix", "Quartier", "surface"])
    assert enrichment._detect_quartier_column(df) == "Quartier"


def test_detect_text_columns_returns_existing_text_columns():
    df = pd.DataFrame(columns=["Titre", "Description", "prix"])
    result = enrichment._detect_text_columns(df)
    assert "Titre" in result
    assert "Description" in result


def test_extract_structured_from_text_returns_defaults_for_empty_text():
    result = enrichment.extract_structured_from_text("")
    assert result["type_bien"] is None
    assert result["surface_m2"] is None
    assert result["atouts"] == []
    assert result["inconvenients"] == []


def test_extract_structured_from_text_uses_mocked_llm(monkeypatch):
    def fake_ask_llm(prompt, model="llama3"):
        return """
        {
          "type_bien": "appartement",
          "surface_m2": 52,
          "pieces": 3,
          "chambres": 2,
          "etage": 1,
          "ascenseur": true,
          "balcon_ou_terrasse": false,
          "parking": true,
          "travaux_a_prevoir": false,
          "dpe": "C",
          "prix_eur": 180000,
          "charges_eur_mois": 80,
          "quartier": "Centre",
          "atouts": ["lumineux"],
          "inconvenients": ["bruit"]
        }
        """

    monkeypatch.setattr(enrichment, "ask_llm", fake_ask_llm)

    result = enrichment.extract_structured_from_text("Appartement T3 lumineux", model="llama3")

    assert result["type_bien"] == "appartement"
    assert result["surface_m2"] == 52
    assert result["quartier"] == "Centre"
    assert result["atouts"] == ["lumineux"]


def test_extract_structured_from_text_falls_back_to_defaults_if_bad_llm(monkeypatch):
    def fake_ask_llm(prompt, model="llama3"):
        return "réponse invalide"

    monkeypatch.setattr(enrichment, "ask_llm", fake_ask_llm)

    result = enrichment.extract_structured_from_text("Texte annonce")

    assert result["type_bien"] is None
    assert result["atouts"] == []
    assert result["inconvenients"] == []


def test_enrich_annonces_structured_returns_same_df_if_empty():
    df = pd.DataFrame()
    result = enrichment.enrich_annonces_structured(df)
    assert result.empty


def test_enrich_annonces_structured_raises_if_no_text_column():
    df = pd.DataFrame({"prix": [100000], "surface": [50]})
    with pytest.raises(ValueError):
        enrichment.enrich_annonces_structured(df)


def test_enrich_annonces_structured_adds_columns(monkeypatch):
    df = pd.DataFrame({
        "description": ["T2 avec balcon", "Studio centre-ville"]
    })

    def fake_extract(text, model="llama3"):
        return {
            "type_bien": "appartement",
            "surface_m2": 40,
            "pieces": 2,
            "chambres": 1,
            "etage": None,
            "ascenseur": None,
            "balcon_ou_terrasse": True,
            "parking": False,
            "travaux_a_prevoir": False,
            "dpe": "D",
            "prix_eur": 100000,
            "charges_eur_mois": 50,
            "quartier": "Centre",
            "atouts": ["balcon"],
            "inconvenients": [],
        }

    monkeypatch.setattr(enrichment, "extract_structured_from_text", fake_extract)

    result = enrichment.enrich_annonces_structured(df)

    assert "type_bien" in result.columns
    assert "surface_m2" in result.columns
    assert len(result) == 2


def test_summarize_by_quartier_returns_empty_schema_on_empty_df():
    df = pd.DataFrame()
    result = enrichment.summarize_by_quartier(df)
    assert list(result.columns) == [
        "quartier",
        "nb_annonces",
        "resume",
        "profil_acheteur",
        "points_forts",
        "points_faibles",
    ]
    assert result.empty


def test_summarize_by_quartier_raises_if_no_quartier_column():
    df = pd.DataFrame({"description": ["abc"]})
    with pytest.raises(ValueError):
        enrichment.summarize_by_quartier(df)


def test_summarize_by_quartier_raises_if_no_text_column():
    df = pd.DataFrame({"quartier": ["Centre"]})
    with pytest.raises(ValueError):
        enrichment.summarize_by_quartier(df)


def test_summarize_by_quartier_builds_summary(monkeypatch):
    df = pd.DataFrame({
        "quartier": ["Centre", "Centre", "Est"],
        "description": [
            "Appartement lumineux proche commerces",
            "Studio à rénover",
            "Maison avec jardin",
        ],
    })

    def fake_ask_llm(prompt, model="llama3"):
        return """
        {
          "resume": "Quartier dynamique avec offre variée.",
          "profil_acheteur": "Primo-accédant",
          "points_forts": ["commerces", "transport"],
          "points_faibles": ["bruit"]
        }
        """

    monkeypatch.setattr(enrichment, "ask_llm", fake_ask_llm)

    result = enrichment.summarize_by_quartier(df)

    assert len(result) == 2
    assert set(result["quartier"]) == {"Centre", "Est"}
    assert "resume" in result.columns
    assert "points_forts" in result.columns