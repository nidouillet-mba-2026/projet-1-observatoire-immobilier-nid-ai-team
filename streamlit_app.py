import streamlit as st
import pandas as pd
import subprocess
from pathlib import Path
import os
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

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
    
    /* ===== CARTES DE PROPRIÉTÉS ===== */
    .property-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        margin-bottom: 20px;
        border-left: 4px solid #E8A87C;
        transition: transform 0.2s;
    }
    
    .property-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.12);
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
    .filter-section {
        background: white;
        padding: 25px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        margin-bottom: 30px;
    }
    
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

# Fonction pour récupérer l'URL de la première image d'une annonce
@st.cache_data
def get_image_url(ad_url):
    """Récupère l'URL de la première image trouvée sur la page de l'annonce avec Playwright"""
    if not ad_url or pd.isna(ad_url):
        return None
    
    try:
        with sync_playwright() as p:
            # Lancer Chrome
            browser = p.chromium.launch(headless=True, args=['--disable-gpu', '--no-sandbox'])
            context = browser.new_context()
            page = context.new_page()
            
            # Aller à la page avec timeout court
            page.goto(ad_url, wait_until="load", timeout=20000)
            
            # Attendre que les images se chargent
            page.wait_for_load_state("networkidle", timeout=10000)
            
            # Chercher les images de propriété
            img_selectors = [
                "img[class*='photo']",
                "img[class*='image']",
                "img[class*='main']",
                "img[alt*='propriété']",
                "img[alt*='bien']",
                "img",
            ]
            
            for selector in img_selectors:
                try:
                    img = page.locator(selector).first
                    if img.is_visible():
                        src = img.get_attribute("src")
                        if src and src.startswith("http"):
                            browser.close()
                            return src
                except:
                    continue
            
            browser.close()
    except Exception as e:
        pass
    
    return None

# ==================== HEADER ====================
col_logo, col_header = st.columns([0.4, 3])
with col_logo:
    st.image("projet-1-observatoire-immobilier-nid-ai-team/logo_niddouillet.png", width=80)
with col_header:
    st.markdown("<h1 style='color: #333; margin-bottom: 0px;'>NidDouillet</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #999; margin: 0; font-size: 14px;'>Marché immobilier toulonnais</p>", unsafe_allow_html=True)

st.markdown("---")

# ==================== NAVIGATION ====================
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔍 Recherche", "📍 Quartiers", "📊 Données", "🛠️ Outils", "ℹ️ À propos"])

# ==================== TAB 1: RECHERCHE ====================
with tab1:
    # Section Filtres
    st.markdown("<div class='filter-section'>", unsafe_allow_html=True)
    st.markdown("<div class='filter-title'>🔍 Critères de recherche</div>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    try:
        annonces_df = load_annonces()
        
        if annonces_df is not None:
            # Initialiser session_state pour les détails
            if 'open_details' not in st.session_state:
                st.session_state.open_details = {}
            
            # Filtres
            with col1:
                quartiers = ["Tous les quartiers"] + sorted([str(q) for q in annonces_df['quartier'].dropna().unique().tolist()])
                selected_quartier = st.selectbox("Quartiers", quartiers)
            
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
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Appliquer les filtres
            filtered_df = annonces_df.copy()
            
            if selected_quartier != "Tous les quartiers":
                filtered_df = filtered_df[filtered_df['quartier'] == selected_quartier]
            
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
            
            # Résultats
            st.markdown(f"### {len(filtered_df)} résultats")
            
            if len(filtered_df) > 0:
                # Calculer le prix moyen au m² pour le scoring
                if 'prix_eur' in filtered_df.columns and 'surface_m2' in filtered_df.columns:
                    filtered_df['prix_m2'] = filtered_df['prix_eur'] / filtered_df['surface_m2']
                    prix_m2_moyen = filtered_df['prix_m2'].mean()
                else:
                    prix_m2_moyen = 0
                
                # Afficher les cartes
                cols = st.columns(2)
                for idx, (_, row) in enumerate(filtered_df.iterrows()):
                    with cols[idx % 2]:
                        # Carte
                        st.markdown('<div class="property-card">', unsafe_allow_html=True)
                        
                        # Image du bien
                        st.markdown("<p style='color: #999; font-size: 12px;'>📷 Chargement de l'image...</p>", unsafe_allow_html=True)
                        image_url = get_image_url(row.get('url'))
                        if image_url:
                            try:
                                st.image(image_url, use_column_width=True, caption="")
                            except:
                                st.markdown("<div style='background: #f0f0f0; height: 200px; border-radius: 8px; display: flex; align-items: center; justify-content: center;'><p>🏠 Image indisponible</p></div>", unsafe_allow_html=True)
                        else:
                            st.markdown("<div style='background: #f0f0f0; height: 200px; border-radius: 8px; display: flex; align-items: center; justify-content: center;'><p style='color: #999;'>🖼️ Pas d'image</p></div>", unsafe_allow_html=True)
                        
                        # Scoring
                        if prix_m2_moyen > 0:
                            score_text, score_type = get_scoring(row['prix_m2'] if 'prix_m2' in row else 0, prix_m2_moyen)
                            if score_type == "opportunity":
                                st.markdown(f'<div class="score-badge-opportunity">↗ {score_text}</div>', unsafe_allow_html=True)
                            elif score_type == "market":
                                st.markdown(f'<div class="score-badge-market">— {score_text}</div>', unsafe_allow_html=True)
                            else:
                                st.markdown(f'<div class="score-badge-overvalued">↘ {score_text}</div>', unsafe_allow_html=True)
                        
                        # Titre
                        st.markdown(f"<h4 style='margin: 10px 0;'>{row.get('titre', 'Sans titre')[:60]}</h4>", unsafe_allow_html=True)
                        
                        # Localisation
                        if pd.notna(row.get('quartier')):
                            st.markdown(f"📍 {row['quartier']}")
                        
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
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                        
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
            else:
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
                    ["python", str(SCRAPE_SCRIPT)],
                    cwd=str(SCRIPT_DIR.parent.parent),
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
