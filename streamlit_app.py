import streamlit as st
import pandas as pd
import subprocess
from pathlib import Path
import os

# Configuration de la page
st.set_page_config(
    page_title="Observatoire Immobilier Toulon",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "Application pour l'agence NidDouillet"}
)

# Styles personnalisés
st.markdown("""
    <style>
    .main {
        padding-top: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
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

# Header principal
st.title("🏘️ Observatoire du Marché Immobilier Toulonnais")
st.markdown("**Application dédiée à l'agence NidDouillet** - Outil d'aide aux jeunes couples primo-accédants")

# Navigation avec tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Accueil", "📋 Données", "🔍 Filtres & Analyse", "⚙️ Outils"])

# ==================== TAB 1: ACCUEIL ====================
with tab1:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("💰 Budget Max", "450 000 €")
    with col2:
        st.metric("📍 Zone", "Toulon (83)")
    with col3:
        st.metric("📈 Marché", "2 ans de données")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📌 À propos")
        st.write("""
        Cette application vous aide à :
        - **Visualiser** le marché immobilier toulonnais
        - **Filtrer** les biens par budget, surface, quartier
        - **Analyser** les prix au m² et distributions
        - **Scorer** les opportunités d'achat
        - **Mettre à jour** les données en temps réel
        """)
    
    with col2:
        st.subheader("🎯 Fonctionnalités")
        try:
            annonces_df = load_annonces()
            dvf_df = load_dvf()
            
            if annonces_df is not None and dvf_df is not None:
                col_a, col_b = st.columns(2)
                with col_a:
                    st.write(f"**Annonces actuelles:** {len(annonces_df)}")
                    st.write(f"**Transactions DVF:** {len(dvf_df)}")
                with col_b:
                    if len(annonces_df) > 0 and 'prix_eur' in annonces_df.columns:
                        prix_min = annonces_df['prix_eur'].min()
                        prix_max = annonces_df['prix_eur'].max()
                        st.write(f"**Prix annonces:** {prix_min:,.0f}€ - {prix_max:,.0f}€")
        except:
            st.info("Chargement des données...")

# ==================== TAB 2: DONNÉES ====================
with tab2:
    st.subheader("📋 Consultation des Données")
    
    data_choice = st.radio("Sélectionnez un dataset :", 
                          ["📰 Annonces (Scraping)", "📊 Transactions DVF"],
                          horizontal=True)
    
    if data_choice == "📰 Annonces (Scraping)":
        try:
            df = load_annonces()
            if df is not None:
                st.success(f"✅ {len(df)} annonces chargées")
                
                # Filtres rapides
                col1, col2 = st.columns(2)
                with col1:
                    if 'prix_eur' in df.columns:
                        prix_filter = st.slider("Filtrer par prix (€)", 
                                               int(df['prix_eur'].min()),
                                               int(df['prix_eur'].max()),
                                               (int(df['prix_eur'].min()), int(df['prix_eur'].max())))
                        df = df[(df['prix_eur'] >= prix_filter[0]) & (df['prix_eur'] <= prix_filter[1])]
                
                with col2:
                    if 'type_bien' in df.columns:
                        types = df['type_bien'].dropna().unique().tolist()
                        if types:
                            selected_type = st.multiselect("Type de bien :", types, default=types)
                            df = df[df['type_bien'].isin(selected_type)]
                
                # Affichage du tableau
                st.dataframe(df, use_container_width=True)
                
                # Export
                csv = df.to_csv(index=False)
                st.download_button("⬇️ Télécharger en CSV",
                                 csv, "annonces.csv", "text/csv")
            else:
                st.warning("⚠️ Fichier annonces.csv non trouvé")
        except Exception as e:
            st.error(f"❌ Erreur : {str(e)}")
    
    else:  # DVF
        try:
            df = load_dvf()
            if df is not None:
                st.success(f"✅ {len(df)} transactions chargées")
                
                # Filtres rapides
                col1, col2 = st.columns(2)
                with col1:
                    if 'valeur_fonciere' in df.columns:
                        prix_filter = st.slider("Filtrer par prix (€)",
                                               int(df['valeur_fonciere'].min()),
                                               int(df['valeur_fonciere'].max()),
                                               (int(df['valeur_fonciere'].min()), int(df['valeur_fonciere'].max())))
                        df = df[(df['valeur_fonciere'] >= prix_filter[0]) & (df['valeur_fonciere'] <= prix_filter[1])]
                
                with col2:
                    if 'type_local' in df.columns:
                        types = df['type_local'].dropna().unique().tolist()
                        if types:
                            selected_type = st.multiselect("Type de bien :", types, default=types)
                            df = df[df['type_local'].isin(selected_type)]
                
                # Affichage du tableau
                st.dataframe(df, use_container_width=True)
                
                # Export
                csv = df.to_csv(index=False)
                st.download_button("⬇️ Télécharger en CSV",
                                 csv, "dvf_toulon.csv", "text/csv")
            else:
                st.warning("⚠️ Fichier dvf_toulon.csv non trouvé")
        except Exception as e:
            st.error(f"❌ Erreur : {str(e)}")

# ==================== TAB 3: FILTRES & ANALYSE ====================
with tab3:
    st.subheader("🔍 Recherche & Filtrage Avancé")
    
    try:
        annonces_df = load_annonces()
        dvf_df = load_dvf()
        
        if annonces_df is not None:
            # Initialiser les colonnes de filtre
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                budget_min, budget_max = st.slider(
                    "Budget (€)",
                    0, 500000, (0, 450000),
                    step=10000
                )
            
            with col2:
                surface_min, surface_max = st.slider(
                    "Surface (m²)",
                    0, 200,
                    (0, 200),
                    step=5
                )
            
            with col3:
                if 'quartier' in annonces_df.columns:
                    quartiers = annonces_df['quartier'].dropna().unique().tolist()
                    selected_quartier = st.multiselect(
                        "Quartier(s)",
                        quartiers,
                        default=quartiers[:3] if len(quartiers) > 3 else quartiers
                    )
            
            with col4:
                if 'type_bien' in annonces_df.columns:
                    types = annonces_df['type_bien'].dropna().unique().tolist()
                    selected_type = st.multiselect(
                        "Type de bien",
                        types,
                        default=types
                    )
            
            # Appliquer les filtres
            filtered_df = annonces_df.copy()
            
            if 'prix_eur' in filtered_df.columns:
                filtered_df = filtered_df[
                    (filtered_df['prix_eur'] >= budget_min) &
                    (filtered_df['prix_eur'] <= budget_max)
                ]
            
            if 'surface_m2' in filtered_df.columns:
                filtered_df = filtered_df[
                    (filtered_df['surface_m2'] >= surface_min) &
                    (filtered_df['surface_m2'] <= surface_max)
                ]
            
            if 'quartier' in filtered_df.columns and col3:
                filtered_df = filtered_df[filtered_df['quartier'].isin(selected_quartier)]
            
            if 'type_bien' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['type_bien'].isin(selected_type)]
            
            st.divider()
            
            # Affichage des résultats
            st.write(f"**{len(filtered_df)} bien(s) trouvé(s)**")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if len(filtered_df) > 0 and 'prix_eur' in filtered_df.columns:
                    st.metric("Prix moyen", f"{filtered_df['prix_eur'].mean():,.0f}€")
            with col2:
                if len(filtered_df) > 0 and 'surface_m2' in filtered_df.columns:
                    st.metric("Surface moy.", f"{filtered_df['surface_m2'].mean():.1f}m²")
            with col3:
                if len(filtered_df) > 0 and 'prix_eur' in filtered_df.columns and 'surface_m2' in filtered_df.columns:
                    prix_m2 = (filtered_df['prix_eur'] / filtered_df['surface_m2']).mean()
                    st.metric("Prix/m² moy.", f"{prix_m2:,.0f}€/m²")
            
            st.divider()
            
            # Tableau des résultats
            if len(filtered_df) > 0:
                st.dataframe(filtered_df, use_container_width=True)
                
                csv = filtered_df.to_csv(index=False)
                st.download_button("⬇️ Exporter les résultats",
                                 csv, "resultats_recherche.csv", "text/csv")
            else:
                st.info("❌ Aucun bien ne correspond à ces critères")
        else:
            st.warning("⚠️ Chargement des données...")
    
    except Exception as e:
        st.error(f"❌ Erreur : {str(e)}")

# ==================== TAB 4: OUTILS ====================
with tab4:
    st.subheader("⚙️ Outils d'Administration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("""
        **🔄 Mise à Jour des Données**
        
        Cliquez sur le bouton ci-dessous pour lancer le scraping et mettre à jour les annonces actuelles.
        Cette opération peut prendre quelques minutes.
        """)
        
        if st.button("🚀 Lancer le Scraping", key="scrape_btn"):
            st.warning("⏳ Scraping en cours... Cela peut prendre quelques minutes.")
            try:
                # Exécuter le script de scraping
                result = subprocess.run(
                    ["python", str(SCRAPE_SCRIPT)],
                    cwd=str(SCRIPT_DIR.parent.parent),
                    capture_output=True,
                    text=True,
                    timeout=600
                )
                
                if result.returncode == 0:
                    st.success("✅ Scraping terminé avec succès !")
                    st.write("**Résultat :**")
                    st.code(result.stdout)
                    # Vider le cache pour recharger les données
                    st.cache_data.clear()
                else:
                    st.error("❌ Erreur lors du scraping")
                    st.write("**Erreur :**")
                    st.code(result.stderr)
            except subprocess.TimeoutExpired:
                st.error("❌ Le scraping a dépassé le délai imparti (10 min)")
            except Exception as e:
                st.error(f"❌ Erreur : {str(e)}")
    
    with col2:
        st.info("""
        **📊 Statistiques du Projet**
        """)
        
        try:
            annonces_df = load_annonces()
            dvf_df = load_dvf()
            
            if annonces_df is not None:
                st.metric("Annonces en base", len(annonces_df))
            if dvf_df is not None:
                st.metric("Transactions DVF", len(dvf_df))
            
            st.divider()
            
            st.write("**Fichiers disponibles :**")
            if ANNONCES_CSV.exists():
                st.success(f"✅ annonces.csv ({ANNONCES_CSV.stat().st_size // 1024} KB)")
            else:
                st.error("❌ annonces.csv")
            
            if DVF_CSV.exists():
                st.success(f"✅ dvf_toulon.csv ({DVF_CSV.stat().st_size // 1024} KB)")
            else:
                st.error("❌ dvf_toulon.csv")
            
            if SCRAPE_SCRIPT.exists():
                st.success(f"✅ Script de scraping disponible")
            else:
                st.error("❌ Script de scraping")
        except Exception as e:
            st.warning(f"Impossible de charger les statistiques : {str(e)}")

# Footer
st.divider()
st.markdown("""
    <div style="text-align: center; color: #888; font-size: 12px; padding-top: 20px;">
    <p>🏠 Observatoire du Marché Immobilier Toulonnais | Agence NidDouillet | 2026</p>
    </div>
    """, unsafe_allow_html=True)
