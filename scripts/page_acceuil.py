# =======================
# 📦 Imports & Librairies
# =======================
import streamlit as st

# Page d'acceuil
def page_accueil():
    """
    Objectif :
        Afficher une page d'accueil de l'application.
    """
    st.title("🌍 API étude sectorielle et concurrentielle Data Marketing")

    st.markdown("""
    Explorez les données, analysez les tendances du marché,  
    et optimisez vos stratégies commerciales.

    ---  
    👋 **Bienvenue dans l'outil de Data Marketing.**  
    Utilisez le menu à gauche pour naviguer entre les pages disponibles :  
    - 📊 Données INSEE  
    - 🗺️ Données OSM
    """)