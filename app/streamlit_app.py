import streamlit as st

st.set_page_config(page_title="Observatoire Immobilier Toulon", layout="wide")

st.title("Observatoire du Marche Immobilier Toulonnais")
st.write(
    "Application en cours de construction pour l'agence NidDouillet. "
    "Cette version initialise le socle technique et sera enrichie etape par etape."
)

st.subheader("Prochaines etapes")
st.markdown("- Integrer les donnees DVF et annonces")
st.markdown("- Ajouter filtres budget/surface/quartier/type")
st.markdown("- Ajouter visualisations prix au m2 et distribution")
st.markdown("- Ajouter scoring d'opportunite")
