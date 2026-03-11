import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import subprocess
from pathlib import Path
import sys
import re
import unicodedata

from analysis.regression import least_squares_fit, r_squared
from app.carte_quartiers import afficher_carte
from analysis.scoring import expected_price, opportunity_score, classify_property
from analysis.knn import find_similar_to_target
from analysis.stats import mean, median, variance, correlation
from analysis.enrichment import add_quartier_fallback

# Configuration

st.set_page_config(
    page_title="NidDouillet - Observatoire immobilier Toulon",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={"About": "Application pour l'agence NidDouillet"},
)

st.markdown(
    """
    <style>
    .stApp {
        background-color: #F9FAF5;
        color: #000000;
    }

    .main {
        background-color: #F9FAF5;
        padding-top: 1rem;
    }

    .score-badge-opportunity {
        background: #E8F5E9;
        color: #2E7D32;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        display: inline-block;
        margin: 5px 5px 5px 0;
    }

    .score-badge-market {
        background: #FFF8E1;
        color: #F57F17;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        display: inline-block;
        margin: 5px 5px 5px 0;
    }

    .score-badge-overvalued {
        background: #FFEBEE;
        color: #C62828;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        display: inline-block;
        margin: 5px 5px 5px 0;
    }

    .price-main {
        font-size: 28px;
        font-weight: 700;
        color: #D84315;
        margin: 10px 0;
    }

    .price-per-m2 {
        color: #999;
        font-size: 14px;
        margin-bottom: 8px;
    }

    .price-estimation {
        background: #F5F5F5;
        padding: 10px;
        border-radius: 8px;
        font-size: 13px;
        color: #666;
        margin-top: 8px;
    }

    .comparison-positive {
        background: #E8F5E9;
        color: #2E7D32;
        padding: 10px;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 600;
        margin-top: 8px;
    }

    .comparison-negative {
        background: #FFEBEE;
        color: #C62828;
        padding: 10px;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 600;
        margin-top: 8px;
    }

    .comparison-neutral {
        background: #FFF8E1;
        color: #F57F17;
        padding: 10px;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 600;
        margin-top: 8px;
    }

    .filter-title {
        font-size: 18px;
        font-weight: 700;
        color: #333;
        margin-bottom: 20px;
    }

    .info-tag {
        background: #F5F5F5;
        color: #666;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 12px;
        margin-right: 5px;
        display: inline-block;
    }

    .footer {
        text-align: center;
        color: #999;
        font-size: 12px;
        padding: 30px 20px;
        border-top: 1px solid #E0E0E0;
        margin-top: 40px;
    }

    .photo-link {
        text-decoration: none;
        color: #000000;
        text-align: center;
    }

    .stApp p,
    .stApp span,
    .stApp label,
    .stApp div,
    .stApp li,
    .stApp h1,
    .stApp h2,
    .stApp h3,
    .stApp h4,
    .stApp h5,
    .stApp h6,
    [data-testid="stMetric"],
    [data-testid="stMetric"] label,
    [data-testid="stMetric"] div,
    [data-testid="stMarkdownContainer"],
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] span,
    [data-testid="stMarkdownContainer"] li,
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3,
    [data-testid="stMarkdownContainer"] h4 {
        color: #000000 !important;
    }

    .stMultiSelect [data-baseweb="select"] > div,
    .stSelectbox [data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border-color: #D9D9D9 !important;
    }

    .stMultiSelect [data-baseweb="tag"],
    .stMultiSelect [data-baseweb="tag"] span,
    .stMultiSelect [data-baseweb="select"] input,
    .stSelectbox [data-baseweb="select"] input,
    .stSelectbox [data-baseweb="select"] span,
    .stSelectbox [data-baseweb="select"] svg,
    .stMultiSelect [data-baseweb="select"] svg,
    .stSlider [data-baseweb="slider"] *,
    .stSlider label,
    .stCheckbox label,
    .stCheckbox span {
        color: #000000 !important;
        fill: #000000 !important;
    }

    .stCheckbox > label > div[data-testid="stCheckbox"] {
        background-color: #FFFFFF !important;
        border-color: #D9D9D9 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Chemins

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
ANNONCES_CSV = DATA_DIR / "annonces.csv"
DVF_CSV = DATA_DIR / "dvf_toulon.csv"
SCRIPT_DIR = BASE_DIR / "scripts"
SCRAPE_SCRIPT = SCRIPT_DIR / "run_scrape_multi_sites.py"
LOGO_PATH = BASE_DIR / "logo_niddouillet.png"


# Contrat de données

REQUIRED_ANNONCES_COLUMNS = [
    "source",
    "titre",
    "prix_eur",
    "surface_m2",
    "quartier",
    "type_bien",
    "description",
    "url",
    "date_scrape",
]

REQUIRED_DVF_COLUMNS = [
    "date_mutation",
    "nature_mutation",
    "valeur_fonciere",
    "prix_m2",
    "code_postal",
    "nom_commune",
    "code_departement",
    "code_commune",
    "type_local",
    "surface_reelle_bati",
    "nombre_pieces_principales",
    "surface_terrain",
]


# Référentiel quartiers

QUARTIERS_REFERENCE = [
    "Aguillon",
    "Barbès-Valbourdin",
    "Cap Brun",
    "Centre-ville",
    "Champ de Mars",
    "La Rode",
    "La Roseraie",
    "Le Mourillon",
    "Les Lices",
    "Les Moulins",
    "Place d'Armes",
    "Pont du Las",
    "Porte d'Italie",
    "Saint-Jean du Var",
]


# Session

if "page" not in st.session_state:
    st.session_state.page = 1

if "scroll_to_top" not in st.session_state:
    st.session_state.scroll_to_top = False


# Utilitaires

def normalize_text(value):
    if value is None or pd.isna(value):
        return ""
    text = str(value).lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def validate_columns(df, required_columns, dataset_name):
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Colonnes manquantes dans {dataset_name} : {missing}")


def ensure_numeric(df, cols):
    result = df.copy()
    for col in cols:
        result[col] = pd.to_numeric(result[col], errors="coerce")
    return result


def detect_quartier_from_description(description, titre, url=None):
    text = normalize_text(f"{titre or ''} {description or ''} {url or ''}")
    if not text:
        return None

    quartier_patterns = {
        "Aguillon": ["aguillon"],
        "Barbès-Valbourdin": ["barbes valbourdin", "barbes", "valbourdin"],
        "Cap Brun": ["cap brun"],
        "Centre-ville": ["centre ville", "hyper centre", "centre historique", "centrevile"],
        "Champ de Mars": ["champ de mars", "champs de mars"],
        "La Rode": ["la rode"],
        "La Roseraie": ["la roseraie"],
        "Le Mourillon": ["mourillon", "mourilon"],
        "Les Lices": ["les lices", "lices"],
        "Les Moulins": ["les moulins", "moulins"],
        "Place d'Armes": ["place d armes", "place darmes"],
        "Pont du Las": ["pont du las", "pont dulas"],
        "Porte d'Italie": ["porte d italie", "porte italie"],
        "Saint-Jean du Var": ["saint jean du var", "st jean du var", "st jean var"],
    }

    for quartier, patterns in quartier_patterns.items():
        for pattern in patterns:
            if f" {pattern} " in f" {text} ":
                return quartier

    return None


def simplify_title(title):
    if not title or pd.isna(title):
        return "Bien immobilier"

    title = str(title).lower()

    type_mapping = {
        "appartement": "Appartement",
        "maison": "Maison",
        "studio": "Studio",
        "t1": "Studio",
        "t2": "2 pièces",
        "t3": "3 pièces",
        "t4": "4 pièces",
        "t5": "5 pièces",
        "duplex": "Duplex",
        "triplex": "Triplex",
        "loft": "Loft",
        "villa": "Villa",
        "chalet": "Chalet",
    }

    bien_type = "Bien immobilier"
    for key, value in type_mapping.items():
        if key in title:
            bien_type = value
            break

    pieces = ""
    for i in range(1, 8):
        if f" {i} " in title or f"{i}p" in title or f"{i} pieces" in normalize_text(title):
            pieces = f"{i} pièces"
            break

    return f"{bien_type} {pieces}" if pieces else bien_type


def safe_price_m2(price, surface):
    if pd.isna(price) or pd.isna(surface) or float(surface) <= 0:
        return None
    return float(price) / float(surface)


def format_eur(value):
    if value is None or pd.isna(value):
        return "N/A"
    return f"{float(value):,.0f}€".replace(",", " ")


def format_float(value, digits=2):
    if value is None or pd.isna(value):
        return "N/A"
    return f"{float(value):.{digits}f}"


def badge_html(label):
    if label == "Opportunité":
        return f'<div class="score-badge-opportunity">↗ {label}</div>'
    if label == "Surévalué":
        return f'<div class="score-badge-overvalued">↘ {label}</div>'
    return f'<div class="score-badge-market">→ {label}</div>'


def comparison_html(delta_pct):
    if delta_pct is None or pd.isna(delta_pct):
        return ""
    pct = float(delta_pct) * 100
    if pct > 10:
        return f"<div class='comparison-positive'>Sous le prix attendu de {pct:.1f}%</div>"
    if pct < -10:
        return f"<div class='comparison-negative'>Au-dessus du prix attendu de {abs(pct):.1f}%</div>"
    return f"<div class='comparison-neutral'>Écart limité de {abs(pct):.1f}% vs prix attendu</div>"


# Chargement

@st.cache_data
def load_annonces():
    if not ANNONCES_CSV.exists():
        return None
    df = pd.read_csv(ANNONCES_CSV)
    validate_columns(df, REQUIRED_ANNONCES_COLUMNS, "annonces.csv")
    return df


@st.cache_data
def load_dvf():
    if not DVF_CSV.exists():
        return None
    df = pd.read_csv(DVF_CSV)
    validate_columns(df, REQUIRED_DVF_COLUMNS, "dvf_toulon.csv")
    return df


@st.cache_data
def prepare_annonces(df):
    if df is None or df.empty:
        return df

    data = df.copy()
    data = ensure_numeric(data, ["prix_eur", "surface_m2"])

    data["quartier_detecte"] = data.apply(
        lambda row: detect_quartier_from_description(
            row.get("description"),
            row.get("titre"),
            row.get("url"),
        ),
        axis=1,
    )

    try:
        enriched = add_quartier_fallback(
            data,
            quartier_col="quartier",
            text_col="description",
            output_col="quartier_source",
        )
        if "quartier_source" in enriched.columns:
            data["quartier_source"] = enriched["quartier_source"]
        else:
            data["quartier_source"] = None
    except Exception:
        data["quartier_source"] = None

    data["quartier_final"] = data["quartier"]
    data["quartier_final"] = data["quartier_final"].where(
        data["quartier_final"].notna(), data["quartier_source"]
    )
    data["quartier_final"] = data["quartier_final"].where(
        data["quartier_final"].notna(), data["quartier_detecte"]
    )

    data["quartier_final"] = data["quartier_final"].apply(
        lambda x: x if x in QUARTIERS_REFERENCE else None
    )

    data["prix_m2"] = data.apply(
        lambda row: safe_price_m2(row.get("prix_eur"), row.get("surface_m2")),
        axis=1,
    )

    return data


@st.cache_data
def prepare_dvf(df):
    if df is None or df.empty:
        return df

    data = df.copy()
    data = ensure_numeric(data, ["valeur_fonciere", "prix_m2", "surface_reelle_bati"])

    data["prix_m2_dvf"] = data.apply(
        lambda row: safe_price_m2(row.get("valeur_fonciere"), row.get("surface_reelle_bati")),
        axis=1,
    )

    return data


@st.cache_data
def train_price_model(dvf_df):
    if dvf_df is None or dvf_df.empty:
        return None

    train = dvf_df.copy()
    train = train.dropna(subset=["surface_reelle_bati", "valeur_fonciere"]).copy()
    train = train[train["surface_reelle_bati"] > 0].copy()
    train = train[train["valeur_fonciere"] > 0].copy()

    if len(train) < 3:
        return None

    x = train["surface_reelle_bati"].astype(float).tolist()
    y = train["valeur_fonciere"].astype(float).tolist()

    alpha, beta = least_squares_fit(x, y)
    score_r2 = r_squared(alpha, beta, x, y)

    return {
        "alpha": alpha,
        "beta": beta,
        "r2": score_r2,
        "n": len(train),
    }


@st.cache_data
def score_annonces(annonces_df, model_info):
    if annonces_df is None or annonces_df.empty:
        return annonces_df

    data = annonces_df.copy()

    data["prix_attendu"] = None
    data["score_opportunite"] = None
    data["classement"] = None

    if model_info is None:
        return data

    alpha = model_info["alpha"]
    beta = model_info["beta"]

    def compute_expected(surface):
        if pd.isna(surface) or float(surface) <= 0:
            return None
        return expected_price(alpha, beta, float(surface))

    def compute_score(row):
        listed = row.get("prix_eur")
        expected = row.get("prix_attendu")
        if pd.isna(listed) or listed <= 0 or expected is None:
            return None
        return opportunity_score(float(expected), float(listed))

    def compute_class(row):
        listed = row.get("prix_eur")
        expected = row.get("prix_attendu")
        if pd.isna(listed) or listed <= 0 or expected is None:
            return None
        return classify_property(float(expected), float(listed))

    data["prix_attendu"] = data["surface_m2"].apply(compute_expected)
    data["score_opportunite"] = data.apply(compute_score, axis=1)
    data["classement"] = data.apply(compute_class, axis=1)

    return data


# Données globales

annonces_raw = load_annonces()
dvf_raw = load_dvf()

annonces_df = prepare_annonces(annonces_raw) if annonces_raw is not None else None
dvf_df = prepare_dvf(dvf_raw) if dvf_raw is not None else None
model_info = train_price_model(dvf_df) if dvf_df is not None else None
annonces_scored = score_annonces(annonces_df, model_info) if annonces_df is not None else None


# Header

col_logo, col_header = st.columns([0.4, 3])

with col_logo:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=80)

with col_header:
    st.markdown("<h1 style='color: #333; margin-bottom: 0;'>NidDouillet</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p style='color: #999; margin: 0; font-size: 14px;'>Marché immobilier toulonnais</p>",
        unsafe_allow_html=True,
    )

st.markdown("---")


# Navigation

tab1, tab2, tab3, tab_carte, tab4, tab5 = st.tabs(
    ["🔍 Recherche", "📍 Quartiers", "📊 Données", "🗺️ Carte", "🛠️ Outils", "ℹ️ À propos"]
)


# Tab 1

with tab1:
    st.markdown("<div class='filter-title'>🔍 Critères de recherche</div>", unsafe_allow_html=True)

    if annonces_scored is None or annonces_scored.empty:
        st.warning("⚠️ Aucune annonce disponible.")
    else:
        data = annonces_scored.copy()

        if st.session_state.get("scroll_to_top", False):
            components.html(
                """
                <script>
                setTimeout(function() {
                    const appContainer = window.parent.document.querySelector('[data-testid="stAppViewContainer"]');
                    if (appContainer) {
                        appContainer.scrollTo({ top: 0, behavior: 'smooth' });
                    }
                    window.parent.scrollTo({ top: 0, behavior: 'smooth' });
                }, 50);
                </script>
                """,
                height=0,
            )
            st.session_state.scroll_to_top = False

        annonces_par_page = 12

        quartiers_disponibles = QUARTIERS_REFERENCE.copy()
        types_disponibles = sorted(
            [t for t in data["type_bien"].dropna().astype(str).unique().tolist() if str(t).strip()]
        )
        labels_scoring = ["Tous", "Opportunité", "Prix marché", "Surévalué"]

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            selected_quartiers = st.multiselect(
                "Quartiers",
                options=quartiers_disponibles,
                default=[],
                placeholder="Sélectionne un ou plusieurs quartiers",
            )

        with col2:
            selected_type = st.selectbox(
                "Type de bien",
                ["Indifférent"] + types_disponibles,
            )

        with col3:
            prix_series = data["prix_eur"].dropna()
            max_prix = int(prix_series.max()) if not prix_series.empty else 500000
            max_prix = max(max_prix, 1000)
            prix_min, prix_max = st.slider(
                "Prix",
                min_value=0,
                max_value=max_prix,
                value=(0, min(500000, max_prix)),
                step=5000,
            )

        with col4:
            scoring_filter = st.selectbox("Scoring", labels_scoring)

        col5, col6, col7, col8 = st.columns(4)

        with col5:
            surface_series = data["surface_m2"].dropna()
            max_surface = int(surface_series.max()) if not surface_series.empty else 300
            max_surface = max(max_surface, 20)
            surface_min, surface_max = st.slider(
                "Surface",
                min_value=0,
                max_value=max_surface,
                value=(0, min(300, max_surface)),
                step=5,
            )

        with col6:
            tri = st.selectbox(
                "Trier par",
                [
                    "Pertinence",
                    "Prix croissant",
                    "Prix décroissant",
                    "Surface croissante",
                    "Surface décroissante",
                    "Meilleure opportunité",
                ],
            )

        with col7:
            show_only_modeled = st.checkbox("Seulement biens scorés", value=False)

        with col8:
            show_only_quartier = st.checkbox("Quartier détecté uniquement", value=False)

        filtered_df = data.copy()

        if selected_quartiers:
            filtered_df = filtered_df[filtered_df["quartier_final"].isin(selected_quartiers)]

        if selected_type != "Indifférent":
            filtered_df = filtered_df[filtered_df["type_bien"].astype(str) == selected_type]

        filtered_df = filtered_df[
            (filtered_df["prix_eur"].fillna(-1) >= prix_min)
            & (filtered_df["prix_eur"].fillna(-1) <= prix_max)
        ]

        filtered_df = filtered_df[
            (filtered_df["surface_m2"].fillna(-1) >= surface_min)
            & (filtered_df["surface_m2"].fillna(-1) <= surface_max)
        ]

        if scoring_filter != "Tous":
            filtered_df = filtered_df[filtered_df["classement"] == scoring_filter]

        if show_only_modeled:
            filtered_df = filtered_df[filtered_df["prix_attendu"].notna()]

        if show_only_quartier:
            filtered_df = filtered_df[filtered_df["quartier_final"].notna()]

        if tri == "Prix croissant":
            filtered_df = filtered_df.sort_values("prix_eur", ascending=True, na_position="last")
        elif tri == "Prix décroissant":
            filtered_df = filtered_df.sort_values("prix_eur", ascending=False, na_position="last")
        elif tri == "Surface croissante":
            filtered_df = filtered_df.sort_values("surface_m2", ascending=True, na_position="last")
        elif tri == "Surface décroissante":
            filtered_df = filtered_df.sort_values("surface_m2", ascending=False, na_position="last")
        elif tri == "Meilleure opportunité":
            filtered_df = filtered_df.sort_values("score_opportunite", ascending=False, na_position="last")

        total_annonces = len(filtered_df)
        total_pages = max(1, (total_annonces + annonces_par_page - 1) // annonces_par_page)

        if st.session_state.page > total_pages:
            st.session_state.page = total_pages

        start_idx = (st.session_state.page - 1) * annonces_par_page
        end_idx = start_idx + annonces_par_page
        page_df = filtered_df.iloc[start_idx:end_idx].copy()

        st.markdown(f"### {total_annonces} annonces trouvées")

        if model_info is not None:
            st.metric("Base de comparaison DVF", model_info["n"])

        if len(page_df) == 0:
            st.info("❌ Aucun bien ne correspond à vos critères.")
        else:
            cols = st.columns(2)

            for idx, (_, row) in enumerate(page_df.iterrows()):
                with cols[idx % 2]:
                    ad_url = row.get("url")
                    if ad_url and pd.notna(ad_url):
                        st.markdown(
                            f"""
                            <div style='background: linear-gradient(135deg, #E8A87C, #C38D9E); height: 200px; border-radius: 8px; display: flex; align-items: center; justify-content: center; margin-bottom: 15px;'>
                                <a href='{ad_url}' target='_blank' class='photo-link'>
                                    <div style='font-size: 48px; margin-bottom: 10px;'>📸</div>
                                    <p style='margin: 0; font-size: 16px; font-weight: 500;'>Visualiser les photos sur le site</p>
                                </a>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            """
                            <div style='background: #f0f0f0; height: 200px; border-radius: 8px; display: flex; align-items: center; justify-content: center; margin-bottom: 15px;'>
                                <div style='text-align: center; color: #999;'>
                                    <div style='font-size: 48px; margin-bottom: 10px;'>📷</div>
                                    <p style='margin: 0; font-size: 14px;'>Photos non disponibles</p>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                    if pd.notna(row.get("classement")):
                        st.markdown(badge_html(row["classement"]), unsafe_allow_html=True)

                    title = row.get("titre")
                    display_title = simplify_title(title) if title else "Bien immobilier"
                    st.markdown(f"#### {display_title}")

                    quartier_affiche = row.get("quartier_final")
                    if quartier_affiche and pd.notna(quartier_affiche):
                        st.markdown(
                            f"<span class='info-tag' style='background:#E3F2FD; color:#1565C0;'>📍 {quartier_affiche}</span>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            "<span class='info-tag' style='background:#FFEBEE; color:#C62828;'>Quartier non détecté</span>",
                            unsafe_allow_html=True,
                        )

                    st.markdown(
                        f"<div class='price-main'>{format_eur(row.get('prix_eur'))}</div>",
                        unsafe_allow_html=True,
                    )

                    if pd.notna(row.get("prix_m2")):
                        st.markdown(
                            f"<div class='price-per-m2'>{float(row['prix_m2']):,.0f}€/m²</div>".replace(",", " "),
                            unsafe_allow_html=True,
                        )

                    features = []
                    if pd.notna(row.get("surface_m2")):
                        features.append(f"<span class='info-tag'>📐 {float(row['surface_m2']):.0f} m²</span>")
                    if pd.notna(row.get("type_bien")):
                        features.append(f"<span class='info-tag'>🏠 {row['type_bien']}</span>")

                    if features:
                        st.markdown(" ".join(features), unsafe_allow_html=True)

                    if pd.notna(row.get("prix_attendu")):
                        st.markdown(
                            f"""
                            <div class='price-estimation'>
                                Prix attendu par régression : <strong>{format_eur(row.get('prix_attendu'))}</strong><br>
                                Score d'opportunité : <strong>{format_float(row.get('score_opportunite'), 3)}</strong>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            comparison_html(row.get("score_opportunite")),
                            unsafe_allow_html=True,
                        )

                    with st.expander("📋 Détails complets du bien"):
                        col_det1, col_det2 = st.columns(2)

                        all_keys = [k for k in row.index if pd.notna(row[k])]
                        half = len(all_keys) // 2

                        with col_det1:
                            for key in all_keys[:half]:
                                st.write(f"**{key}** : {row[key]}")

                        with col_det2:
                            for key in all_keys[half:]:
                                st.write(f"**{key}** : {row[key]}")

                    with st.expander("🔎 Biens similaires"):
                        target = {
                            "surface_m2": row.get("surface_m2"),
                            "prix_eur": row.get("prix_eur"),
                            "type_bien": row.get("type_bien"),
                        }

                        similar_df = None

                        try:
                            if annonces_scored is not None and len(annonces_scored) > 1:
                                base_knn = annonces_scored[
                                    ["surface_m2", "prix_eur", "type_bien", "titre", "quartier_final", "url"]
                                ].copy()
                                base_knn = base_knn.dropna(subset=["surface_m2", "prix_eur", "url"])

                                if len(base_knn) > 1:
                                    similar_df = find_similar_to_target(
                                        target,
                                        base_knn,
                                        k=5,
                                        filter_same_type=True,
                                    )
                        except Exception:
                            similar_df = None

                        if similar_df is None or similar_df.empty:
                            st.info("Pas assez d'annonces similaires avec lien disponible.")
                        else:
                            display_cols = [
                                col
                                for col in ["titre", "surface_m2", "prix_eur", "type_bien", "quartier_final", "url"]
                                if col in similar_df.columns
                            ]
                            display_df = similar_df[display_cols].copy()

                            if "prix_eur" in display_df.columns:
                                display_df["prix_eur"] = display_df["prix_eur"].apply(
                                    lambda x: f"{float(x):,.0f}€".replace(",", " ") if pd.notna(x) else "N/A"
                                )

                            if "surface_m2" in display_df.columns:
                                display_df["surface_m2"] = display_df["surface_m2"].apply(
                                    lambda x: f"{float(x):.0f} m²" if pd.notna(x) else "N/A"
                                )

                            display_df = display_df.rename(
                                columns={
                                    "titre": "Bien",
                                    "surface_m2": "Surface",
                                    "prix_eur": "Prix",
                                    "type_bien": "Type",
                                    "quartier_final": "Quartier",
                                    "url": "Lien",
                                }
                            )

                            st.dataframe(
                                display_df,
                                use_container_width=True,
                                hide_index=True,
                                column_config={
                                    "Lien": st.column_config.LinkColumn("Lien"),
                                },
                            )

            if total_pages > 1:
                st.markdown("---")
                col_pag1, col_pag2, col_pag3 = st.columns([1, 2, 1])

                with col_pag1:
                    if st.button("⬅️ Précédent") and st.session_state.page > 1:
                        st.session_state.page -= 1
                        st.session_state.scroll_to_top = True
                        st.rerun()

                with col_pag2:
                    st.markdown(
                        f"<center>Page {st.session_state.page} sur {total_pages}</center>",
                        unsafe_allow_html=True,
                    )

                with col_pag3:
                    if st.button("Suivant ➡️") and st.session_state.page < total_pages:
                        st.session_state.page += 1
                        st.session_state.scroll_to_top = True
                        st.rerun()

                st.markdown("---")


# Tab 2

with tab2:
    st.markdown("### 📍 Analyse par quartier")

    if annonces_scored is None or annonces_scored.empty:
        st.warning("⚠️ Données annonces indisponibles.")
    else:
        quartier_df = annonces_scored.copy()
        quartier_df = quartier_df[quartier_df["quartier_final"].notna()].copy()

        if quartier_df.empty:
            st.info("Aucun quartier exploitable détecté.")
        else:
            group = (
                quartier_df.groupby("quartier_final", dropna=True)
                .agg(
                    annonces=("quartier_final", "count"),
                    prix_moyen=("prix_eur", "mean"),
                    surface_moyenne=("surface_m2", "mean"),
                    prix_m2_moyen=("prix_m2", "mean"),
                    score_moyen=("score_opportunite", "mean"),
                )
                .reset_index()
                .sort_values("prix_m2_moyen", ascending=False, na_position="last")
            )

            col1, col2 = st.columns([1, 2])

            with col1:
                quartier_select = st.selectbox(
                    "Sélectionner un quartier",
                    group["quartier_final"].tolist(),
                )

            selected_stats = group[group["quartier_final"] == quartier_select].iloc[0]

            with col2:
                m1, m2, m3, m4 = st.columns(4)
                with m1:
                    st.metric("Annonces", int(selected_stats["annonces"]))
                with m2:
                    st.metric("Prix moyen", format_eur(selected_stats["prix_moyen"]))
                with m3:
                    st.metric("Surface moyenne", f"{selected_stats['surface_moyenne']:.1f} m²")
                with m4:
                    val = selected_stats["prix_m2_moyen"]
                    st.metric("Prix moyen au m²", f"{val:,.0f}€/m²".replace(",", " "))

            st.markdown("#### Vue d'ensemble des quartiers")
            st.dataframe(group, use_container_width=True)

            chart_df = group.set_index("quartier_final")[["prix_m2_moyen"]]
            st.markdown("#### Prix moyen au m² par quartier")
            st.bar_chart(chart_df)

            selected_ads = quartier_df[quartier_df["quartier_final"] == quartier_select].copy()

            if not selected_ads.empty:
                st.markdown("#### Répartition des prix dans le quartier")
                hist_source = selected_ads["prix_eur"].dropna()
                if not hist_source.empty:
                    counts = pd.cut(hist_source, bins=min(10, max(2, len(hist_source.unique())))).value_counts().sort_index()
                    counts_df = counts.rename_axis("tranche_prix").reset_index(name="annonces")
                    counts_df["tranche_prix"] = counts_df["tranche_prix"].astype(str)
                    st.dataframe(counts_df, use_container_width=True)


# Tab 3

with tab3:
    st.markdown("### 📊 Consultation des données et statistiques")

    if annonces_scored is not None and not annonces_scored.empty:
        st.markdown("#### Statistiques des annonces")

        annonces_stats = annonces_scored.dropna(subset=["prix_eur", "surface_m2"]).copy()
        if not annonces_stats.empty:
            prices = annonces_stats["prix_eur"].astype(float).tolist()
            surfaces = annonces_stats["surface_m2"].astype(float).tolist()

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("Prix moyen", format_eur(mean(prices)))
            with c2:
                st.metric("Prix médian", format_eur(median(prices)))
            with c3:
                st.metric("Variance prix", f"{variance(prices):,.0f}".replace(",", " "))
            with c4:
                st.metric("Corrélation surface/prix", f"{correlation(surfaces, prices):.3f}")

    if dvf_df is not None and not dvf_df.empty:
        st.markdown("#### Statistiques DVF")

        dvf_stats = dvf_df.dropna(subset=["valeur_fonciere", "surface_reelle_bati"]).copy()
        if not dvf_stats.empty:
            prices = dvf_stats["valeur_fonciere"].astype(float).tolist()
            surfaces = dvf_stats["surface_reelle_bati"].astype(float).tolist()

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("Valeur foncière moyenne", format_eur(mean(prices)))
            with c2:
                st.metric("Valeur foncière médiane", format_eur(median(prices)))
            with c3:
                st.metric("Variance DVF", f"{variance(prices):,.0f}".replace(",", " "))
            with c4:
                st.metric("Corrélation surface/valeur", f"{correlation(surfaces, prices):.3f}")

    st.markdown("---")

    data_choice = st.radio(
        "Sélectionnez un dataset",
        ["📰 Annonces (scraping)", "📊 Transactions DVF"],
        horizontal=True,
    )

    if data_choice == "📰 Annonces (scraping)":
        if annonces_scored is not None:
            st.success(f"✅ {len(annonces_scored)} annonces chargées")
            st.dataframe(annonces_scored, use_container_width=True)
            csv = annonces_scored.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Télécharger en CSV", csv, "annonces.csv", "text/csv")
        else:
            st.warning("⚠️ Fichier annonces introuvable.")
    else:
        if dvf_df is not None:
            st.success(f"✅ {len(dvf_df)} transactions chargées")
            st.dataframe(dvf_df, use_container_width=True)
            csv = dvf_df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Télécharger en CSV", csv, "dvf_toulon.csv", "text/csv")
        else:
            st.warning("⚠️ Fichier DVF introuvable.")


# Tab Carte
with tab_carte:
    annonces_carte = load_annonces()
    afficher_carte(annonces_carte)

# Tab 4

with tab4:
    st.markdown("### 🛠️ Outils d'administration")

    col1, col2 = st.columns(2)

    with col1:
        st.info("**🔄 Mise à jour des données**\n\nLance le scraping pour mettre à jour les annonces.")

        if st.button("🚀 Lancer le scraping", key="scrape_btn"):
            if not SCRAPE_SCRIPT.exists():
                st.error("❌ Script de scraping introuvable.")
            else:
                st.warning("⏳ Scraping en cours...")
                try:
                    result = subprocess.run(
                        [sys.executable, str(SCRAPE_SCRIPT)],
                        cwd=str(BASE_DIR),
                        capture_output=True,
                        text=True,
                        timeout=600,
                    )

                    if result.returncode == 0:
                        st.success("✅ Scraping terminé.")
                        st.cache_data.clear()
                    else:
                        st.error("❌ Erreur lors du scraping.")
                        if result.stderr:
                            st.code(result.stderr)
                except Exception as e:
                    st.error(f"❌ Erreur : {str(e)}")

    with col2:
        st.info("**📊 État du projet**")

        if annonces_scored is not None:
            st.metric("Annonces", len(annonces_scored))
        else:
            st.metric("Annonces", 0)

        if dvf_df is not None:
            st.metric("Transactions DVF", len(dvf_df))
        else:
            st.metric("Transactions DVF", 0)

        if model_info is not None:
            st.metric("Base de comparaison DVF", model_info["n"])
        else:
            st.metric("Base de comparaison DVF", "N/A")


# Tab 5

with tab5:
    st.markdown("### ℹ️ À propos")

    st.markdown(
        """
        **Observatoire du marché immobilier toulonnais**

        Application développée pour l'agence NidDouillet afin d'aider les jeunes couples primo-accédants
        à trouver leur bien immobilier à Toulon.

        #### Fonctionnalités
        - Recherche et filtrage avancé
        - Analyse par quartier
        - Score d'opportunité via régression linéaire from scratch
        - Consultation des transactions DVF
        - Comparaison avec biens similaires via k-NN
        - Export des résultats

        #### Ce que fait l'application
        - Charge les annonces et les transactions DVF
        - Entraîne une régression simple prix ~ surface
        - Estime un prix attendu pour chaque annonce
        - Classe les biens en opportunité, prix marché ou surévalué
        - Affiche des statistiques descriptives et des tendances par quartier

        ---
        🏠 **Agence NidDouillet** | Observatoire immobilier toulonnais | 2026
        """
    )

st.markdown("---")
st.markdown(
    "<div class='footer'>🏠 Observatoire immobilier toulonnais | Agence NidDouillet | 2026</div>",
    unsafe_allow_html=True,
)
