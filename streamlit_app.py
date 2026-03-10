import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import subprocess
from pathlib import Path
import os
import re
import unicodedata
import requests
from bs4 import BeautifulSoup

# Configuration de la page
st.set_page_config(
    page_title="NidDouillet - Observatoire Immobilier Toulon",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={"About": "Application pour l'agence NidDouillet"}
)

# Styles personnalisés avancés
st.markdown("""
    <style>
    /* ===== FOND GÉNÉRAL ===== */
    .stApp {
        background-color: #F9FAF5;
    }
    .main {
        background-color: #F9FAF5;
        padding-top: 1rem;
    }
    
    /* ===== HEADER ===== */
    .header-container {
        display: flex;
        align-items: center;
        gap: 20px;
        padding: 20px;
        background: white;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        margin-bottom: 30px;
    }
    
    /* ===== SCORING BADGES ===== */
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
    
    /* ===== PRIX ===== */
    .price-main {
        font-size: 28px;
        font-weight: 700;
        color: #D84315;
        margin: 10px 0;
    }
    
    .price-per-m2 {
        color: #999;
        font-size: 14px;
    }
    
    .price-estimation {
        background: #F5F5F5;
        padding: 10px;
        border-radius: 8px;
        font-size: 13px;
        color: #666;
        margin-top: 8px;
    }
    
    /* ===== COMPARISON ===== */
    .comparison-positive {
        background: #E8F5E9;
        color: #2E7D32;
        padding: 10px;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 600;
    }
    
    .comparison-negative {
        background: #FFEBEE;
        color: #C62828;
        padding: 10px;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 600;
    }
    
    /* ===== FILTRES ===== */
    .filter-title {
        font-size: 18px;
        font-weight: 700;
        color: #333;
        margin-bottom: 20px;
    }
    
    /* ===== TAGS ===== */
    .info-tag {
        background: #F5F5F5;
        color: #666;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 12px;
        margin-right: 5px;
        display: inline-block;
    }
    
    /* ===== QUARTIER ===== */
    .quartier-section {
        background: #FFF;
        padding: 15px;
        border-radius: 8px;
        margin-top: 15px;
        border-top: 2px solid #F5F5F5;
    }
    
    .quartier-title {
        font-weight: 700;
        font-size: 14px;
        color: #333;
    }
    
    /* ===== ONGLETS ===== */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #F9FAF5 !important;
        border-bottom: 2px solid #E0E0E0 !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
        color: #666;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        color: #D84315 !important;
        border-bottom: 3px solid #D84315 !important;
    }
    
    /* ===== SIDEBAR ===== */
    .css-1d391kg, .css-12oz5g7 {
        background-color: #FAFAF8 !important;
    }
    
    /* ===== DIVIDERS ===== */
    hr {
        border: none;
        height: 1px;
        background: #E0E0E0;
        margin: 20px 0;
    }
    
    /* ===== FOOTER ===== */
    .footer {
        text-align: center;
        color: #999;
        font-size: 12px;
        padding: 30px 20px;
        border-top: 1px solid #E0E0E0;
        margin-top: 40px;
    }
    </style>
    """, unsafe_allow_html=True)

# Chemins des fichiers
DATA_DIR = Path("projet-1-observatoire-immobilier-nid-ai-team/data")
ANNONCES_CSV = DATA_DIR / "annonces.csv"
DVF_CSV = DATA_DIR / "dvf_toulon.csv"
SCRIPT_DIR = Path("projet-1-observatoire-immobilier-nid-ai-team/scripts")
SCRAPE_SCRIPT = SCRIPT_DIR / "run_scrape_multi_sites.py"
LOGO_PATH = BASE_DIR / "logo_niddouillet.png"

# Initialisation de la session
if "data_annonces" not in st.session_state:
    st.session_state.data_annonces = None
if "data_dvf" not in st.session_state:
    st.session_state.data_dvf = None

# Fonction pour charger les CSV
@st.cache_data
def load_annonces():
    if ANNONCES_CSV.exists():
        return pd.read_csv(ANNONCES_CSV)
    return None

@st.cache_data
def load_dvf():
    if DVF_CSV.exists():
        return pd.read_csv(DVF_CSV)
    return None

# Fonction pour obtenir le scoring
def get_scoring(prix_m2_bien, prix_m2_moyen):
    """Retourne le scoring du bien: 'Opportunité', 'Prix marché' ou 'Surévalué'"""
    ratio = prix_m2_bien / prix_m2_moyen if prix_m2_moyen > 0 else 1
    if ratio < 0.95:
        return "Opportunité", "opportunity"
    elif ratio <= 1.05:
        return "Prix Marché", "market"
    else:
        return "Surévalué", "overvalued"

# ==================== HEADER ====================
col_logo, col_header = st.columns([0.4, 3])
with col_logo:
    st.image("projet-1-observatoire-immobilier-nid-ai-team/logo_niddouillet.png", width=80)
with col_header:
    st.markdown("<h1 style='color: #333; margin-bottom: 0px;'>NidDouillet</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #999; margin: 0; font-size: 14px;'>Marché immobilier toulonnais</p>", unsafe_allow_html=True)

st.markdown("---")

# ==================== FONCTIONS UTILITAIRES ====================

def simplify_title(title):
    """Simplifie le titre d'une annonce immobilière"""
    if not title or pd.isna(title):
        return "Bien immobilier"

    title = str(title).lower()

    # Dictionnaire de correspondances pour simplifier
    type_mapping = {
        'appartement': 'Appartement',
        'maison': 'Maison',
        'studio': 'Studio',
        't1': 'Studio',
        't2': '2 pièces',
        't3': '3 pièces',
        't4': '4 pièces',
        't5': '5 pièces',
        'duplex': 'Duplex',
        'triplex': 'Triplex',
        'loft': 'Loft',
        'villa': 'Villa',
        'chalet': 'Chalet'
    }

    # Chercher le type de bien
    bien_type = "Bien immobilier"
    for key, value in type_mapping.items():
        if key in title:
            bien_type = value
            break

    # Chercher le nombre de pièces
    pieces = ""
    for i in range(1, 8):
        if f' {i} ' in title or f'{i}p' in title or f'{i} pièces' in title:
            pieces = f"{i} pièces"
            break

    # Combiner
    if pieces:
        return f"{bien_type} {pieces}"
    else:
        return bien_type

def normalize_text(value):
    if value is None:
        return ""
    text = str(value).lower()
    text = unicodedata.normalize('NFD', text)
    text = ''.join(ch for ch in text if unicodedata.category(ch) != 'Mn')
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def detect_quartier_from_description(description, titre, url=None):
    """Détecte le quartier à partir de la description, du titre et de l'URL."""
    text = normalize_text(f"{titre or ''} {description or ''} {url or ''}")
    if not text:
        return None

    quartier_patterns = {
        "Centre-ville": ["centre ville", "hyper centre", "centre historique", "centrevile"],
        "Le Mourillon": ["mourillon", "mourilon"],
        "Place d'Armes": ["place d armes", "place darmes"],
        "Porte d'Italie": ["porte d italie", "porte italie"],
        "Pont du Las": ["pont du las", "pont dulas"],
        "Saint-Jean du Var": ["saint jean du var", "st jean du var", "st jean var"],
        "Champs-de-Mars": ["champs de mars", "champ de mars"],
        "Les Lices": ["les lices", "lices"],
    }

    for quartier, patterns in quartier_patterns.items():
        for pattern in patterns:
            if f" {pattern} " in f" {text} ":
                return quartier

    return None

# ==================== NAVIGATION ====================
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔍 Recherche", "📍 Quartiers", "📊 Données", "🛠️ Outils", "ℹ️ À propos"])

# ==================== TAB 1: RECHERCHE ====================
with tab1:
    # Section Filtres
    st.markdown("<div class='filter-title'>🔍 Critères de recherche</div>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    try:
        annonces_df = load_annonces()
        
        if annonces_df is not None:
            # Améliorer la détection des quartiers
            annonces_df['quartier_detecte'] = annonces_df.apply(
                lambda row: detect_quartier_from_description(
                    row.get('description'),
                    row.get('titre'),
                    row.get('url')
                ),
                axis=1
            )
            
            # Initialiser session_state pour les détails et la pagination
            if 'open_details' not in st.session_state:
                st.session_state.open_details = {}
            if 'page' not in st.session_state:
                st.session_state.page = 1
            if 'scroll_to_top' not in st.session_state:
                st.session_state.scroll_to_top = False
            
            # Nombre d'annonces par page
            annonces_par_page = 12
            
            # Filtres
            with col1:
                # Liste des quartiers demandés
                quartiers_defaut = [
                    "Centre-ville",
                    "Le Mourillon",
                    "Place d'Armes",
                    "Porte d'Italie",
                    "Pont du Las",
                    "Saint-Jean du Var",
                    "Champs-de-Mars",
                    "Les Lices"
                ]
                selected_quartiers = st.multiselect(
                    "Quartiers",
                    options=quartiers_defaut,
                    default=[],
                    placeholder="Selectionne un ou plusieurs quartiers"
                )
            
            with col2:
                types = ["Indifférent"] + sorted([str(t) for t in annonces_df['type_bien'].dropna().unique().tolist()])
                selected_type = st.selectbox("Type de bien", types)
            
            with col3:
                if 'prix_eur' in annonces_df.columns:
                    prix_min, prix_max = st.slider(
                        "Prix : 0€ - 1000 000€",
                        0, int(annonces_df['prix_eur'].max()),
                        (0, 500000)
                    )
            
            with col4:
                if 'surface_m2' in annonces_df.columns:
                    surface_min, surface_max = st.slider(
                        "Surface : 0m² - 300m²",
                        0, 300,
                        (0, 300)
                    )
            
            # Appliquer les filtres
            filtered_df = annonces_df.copy()
            
            if selected_quartiers:
                filtered_df = filtered_df[filtered_df['quartier_detecte'].isin(selected_quartiers)]
            
            if selected_type != "Indifférent":
                filtered_df = filtered_df[filtered_df['type_bien'] == selected_type]
            
            if 'prix_eur' in filtered_df.columns:
                filtered_df = filtered_df[
                    (filtered_df['prix_eur'] >= prix_min) &
                    (filtered_df['prix_eur'] <= prix_max)
                ]
            
            if 'surface_m2' in filtered_df.columns:
                filtered_df = filtered_df[
                    (filtered_df['surface_m2'] >= surface_min) &
                    (filtered_df['surface_m2'] <= surface_max)
                ]
            
            # Pagination
            total_annonces = len(filtered_df)
            total_pages = (total_annonces + annonces_par_page - 1) // annonces_par_page
            
            # Sélectionner les annonces de la page actuelle
            start_idx = (st.session_state.page - 1) * annonces_par_page
            end_idx = start_idx + annonces_par_page
            page_df = filtered_df.iloc[start_idx:end_idx]

            # Scroll vers le haut des annonces après changement de page
            if st.session_state.get('scroll_to_top', False):
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
            
            # Résultats
            st.markdown(f"### {len(page_df)} annonces affichées (sur {total_annonces} au total)")
            
            if len(page_df) > 0:
                # Calculer le prix moyen au m² pour le scoring
                if 'prix_eur' in page_df.columns and 'surface_m2' in page_df.columns:
                    page_df['prix_m2'] = page_df['prix_eur'] / page_df['surface_m2']
                    prix_m2_moyen = page_df['prix_m2'].mean()
                else:
                    prix_m2_moyen = 0
                
                # Afficher les cartes
                cols = st.columns(2)
                for idx, (_, row) in enumerate(page_df.iterrows()):
                    with cols[idx % 2]:
                        # Lien vers les photos sur le site
                        ad_url = row.get('url')
                        if ad_url and pd.notna(ad_url):
                            st.markdown(f"""
                            <div style='background: linear-gradient(135deg, #E8A87C, #C38D9E); height: 200px; border-radius: 8px; display: flex; align-items: center; justify-content: center; margin-bottom: 15px;'>
                                <a href='{ad_url}' target='_blank' style='text-decoration: none; color: white; text-align: center;'>
                                    <div style='font-size: 48px; margin-bottom: 10px;'>📸</div>
                                    <p style='margin: 0; font-size: 16px; font-weight: 500;'>Visualiser les photos sur le site</p>
                                </a>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown("""
                            <div style='background: #f0f0f0; height: 200px; border-radius: 8px; display: flex; align-items: center; justify-content: center; margin-bottom: 15px;'>
                                <div style='text-align: center; color: #999;'>
                                    <div style='font-size: 48px; margin-bottom: 10px;'>📷</div>
                                    <p style='margin: 0; font-size: 14px;'>Photos non disponibles</p>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # Scoring
                        if prix_m2_moyen > 0:
                            score_text, score_type = get_scoring(row['prix_m2'] if 'prix_m2' in row else 0, prix_m2_moyen)
                            if score_type == "opportunity":
                                st.markdown(f'<div class="score-badge-opportunity">↗ {score_text}</div>', unsafe_allow_html=True)
                            elif score_type == "market":
                                st.markdown(f'<div class="score-badge-market">— {score_text}</div>', unsafe_allow_html=True)
                            else:
                                st.markdown(f'<div class="score-badge-overvalued">↘ {score_text}</div>', unsafe_allow_html=True)
                        
                        # Titre simplifié
                        titre_simplifie = simplify_title(row.get('titre', 'Sans titre'))
                        st.markdown(f"<h4 style='margin: 10px 0;'>{titre_simplifie}</h4>", unsafe_allow_html=True)
                        
                        # Localisation
                        quartier_affiche = row.get('quartier_detecte')
                        if pd.notna(quartier_affiche) and str(quartier_affiche).strip():
                            st.markdown(f"📍 {quartier_affiche}")
                        else:
                            st.markdown(
                                "<span class='info-tag' style='background:#FFEBEE; color:#C62828;'>Quartier non detecte</span>",
                                unsafe_allow_html=True,
                            )
                        
                        # Prix
                        st.markdown(f"<div class='price-main'>{row.get('prix_eur', 0):,.0f}€</div>", unsafe_allow_html=True)
                        if 'prix_m2' in row:
                            st.markdown(f"<div class='price-per-m2'>{row['prix_m2']:,.0f}€/m²</div>", unsafe_allow_html=True)
                        
                        # Caractéristiques
                        features = []
                        if 'surface_m2' in row and pd.notna(row['surface_m2']):
                            features.append(f"<span class='info-tag'>📐 {row['surface_m2']:.0f}m²</span>")
                        if 'type_bien' in row and pd.notna(row['type_bien']):
                            features.append(f"<span class='info-tag'>🏠 {row['type_bien']}</span>")
                        
                        if features:
                            st.markdown(" ".join(features), unsafe_allow_html=True)
                        
                        # Détails avec expander
                        with st.expander("📋 Détails complets du bien"):
                            col_det1, col_det2 = st.columns(2)
                            with col_det1:
                                for key in row.index[:len(row)//2]:
                                    if pd.notna(row[key]):
                                        st.write(f"**{key}** : {row[key]}")
                            with col_det2:
                                for key in row.index[len(row)//2:]:
                                    if pd.notna(row[key]):
                                        st.write(f"**{key}** : {row[key]}")
            
            # Contrôles de pagination (en bas des résultats)
            if total_pages > 1:
                st.markdown("---")
                col_pag1, col_pag2, col_pag3 = st.columns([1, 2, 1])
                with col_pag1:
                    if st.button("⬅️ Précédent") and st.session_state.page > 1:
                        st.session_state.page -= 1
                        st.session_state.scroll_to_top = True
                        st.rerun()
                
                with col_pag2:
                    st.markdown(f"<center>Page {st.session_state.page} sur {total_pages} ({total_annonces} annonces)</center>", unsafe_allow_html=True)
                
                with col_pag3:
                    if st.button("Suivant ➡️") and st.session_state.page < total_pages:
                        st.session_state.page += 1
                        st.session_state.scroll_to_top = True
                        st.rerun()
                st.markdown("---")

            if len(page_df) == 0:
                st.info("❌ Aucun bien ne correspond à vos critères")
        else:
            st.warning("⚠️ Chargement des données...")
    
    except Exception as e:
        st.error(f"❌ Erreur : {str(e)}")

# ==================== TAB 2: QUARTIERS ====================
with tab2:
    st.markdown("### 📍 Carte des quartiers de Toulon")
    st.info("🗺️ Cliquez sur les quartiers pour les sélectionner")
    
    try:
        annonces_df = load_annonces()
        dvf_df = load_dvf()
        
        if annonces_df is not None and dvf_df is not None:
            # Récupérer les quartiers et leurs statistiques
            quartiers_stats = {}
            for quartier in annonces_df['quartier'].dropna().unique():
                q_annonces = annonces_df[annonces_df['quartier'] == quartier]
                q_dvf = dvf_df[dvf_df['nom_commune'] == 'TOULON']
                
                quartiers_stats[quartier] = {
                    'annonces': len(q_annonces),
                    'prix_moyen': q_annonces['prix_eur'].mean() if len(q_annonces) > 0 else 0,
                }
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Liste des quartiers
                st.markdown("#### Quartiers disponibles")
                quartier_select = st.selectbox(
                    "Sélectionner un quartier",
                    list(quartiers_stats.keys()),
                    label_visibility="collapsed"
                )
            
            with col2:
                st.markdown("#### Informations")
                if quartier_select in quartiers_stats:
                    stats = quartiers_stats[quartier_select]
                    st.metric("Annonces", stats['annonces'])
                    st.metric("Prix moyen", f"{stats['prix_moyen']:,.0f}€")
    
    except Exception as e:
        st.error(f"❌ Erreur : {str(e)}")

# ==================== TAB 3: DONNÉES ====================
with tab3:
    st.markdown("### 📋 Consultation des Données")
    
    data_choice = st.radio("Sélectionnez un dataset :", 
                          ["📰 Annonces (Scraping)", "📊 Transactions DVF"],
                          horizontal=True)
    
    if data_choice == "📰 Annonces (Scraping)":
        try:
            df = load_annonces()
            if df is not None:
                st.success(f"✅ {len(df)} annonces chargées")
                st.dataframe(df, use_container_width=True)
                
                csv = df.to_csv(index=False)
                st.download_button("⬇️ Télécharger en CSV", csv, "annonces.csv", "text/csv")
            else:
                st.warning("⚠️ Fichier non trouvé")
        except Exception as e:
            st.error(f"❌ Erreur : {str(e)}")
    else:
        try:
            df = load_dvf()
            if df is not None:
                st.success(f"✅ {len(df)} transactions chargées")
                st.dataframe(df, use_container_width=True)
                
                csv = df.to_csv(index=False)
                st.download_button("⬇️ Télécharger en CSV", csv, "dvf_toulon.csv", "text/csv")
            else:
                st.warning("⚠️ Fichier non trouvé")
        except Exception as e:
            st.error(f"❌ Erreur : {str(e)}")

# ==================== TAB 4: OUTILS ====================
with tab4:
    st.markdown("### ⚙️ Outils d'Administration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("**🔄 Mise à Jour des Données**\n\nLancez le scraping pour mettre à jour les annonces.")
        
        if st.button("🚀 Lancer le Scraping", key="scrape_btn"):
            st.warning("⏳ Scraping en cours...")
            try:
                result = subprocess.run(
                    [sys.executable, str(SCRAPE_SCRIPT)],
                    cwd=str(BASE_DIR),
                    capture_output=True,
                    text=True,
                    timeout=600
                )
                
                if result.returncode == 0:
                    st.success("✅ Scraping terminé !")
                    st.cache_data.clear()
                else:
                    st.error("❌ Erreur lors du scraping")
            except Exception as e:
                st.error(f"❌ Erreur : {str(e)}")
    
    with col2:
        st.info("**📊 Statistiques du Projet**")
        try:
            annonces_df = load_annonces()
            dvf_df = load_dvf()
            
            if annonces_df is not None:
                st.metric("Annonces", len(annonces_df))
            if dvf_df is not None:
                st.metric("Transactions DVF", len(dvf_df))
        except Exception as e:
            st.warning(f"Impossible de charger : {str(e)}")

# ==================== TAB 5: À PROPOS ====================
with tab5:
    st.markdown("### ℹ️ À propos")
    
    st.markdown("""
    **Observatoire du Marché Immobilier Toulonnais**
    
    Application développée pour l'agence NidDouillet afin d'aider les jeunes couples primo-accédants 
    à trouver leur bien immobilier à Toulon.
    
    #### 🎯 Fonctionnalités
    - 🔍 Recherche et filtrage avancé
    - 📍 Analyse par quartier
    - 🏠 Scores d'opportunité
    - 📊 Données DVF real-time
    - 💾 Export des résultats
    
    #### 💰 Budget cible
    - Max 500 000€
    - Tous types de biens
    - Quartiers de Toulon
    
    ---
    
    🏠 **Agence NidDouillet** | Observatoire Immobilier Toulonnais | 2026
    """)

st.markdown("---")
st.markdown("<div class='footer'>🏠 Observatoire du Marché Immobilier Toulonnais | Agence NidDouillet | 2026</div>", unsafe_allow_html=True)
