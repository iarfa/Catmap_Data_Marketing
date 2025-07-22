# Librairies
import streamlit as st
from page_insee import page_insee

# Personnalisation de la page
def personnalisation_page():
    """
    Objectif :
        Personnaliser la page, les couleurs sont personnalisables ici : https://htmlcolorcodes.com/fr/
    """

    st.markdown(
        """
        <style>
            .title {
                color: #1f77b4;
                font-size: 40px;
                font-weight: bold; # Gras
            }
            .header {
                color: #ff7f0e;
                font-size: 30px;
                font-weight: bold;
            }
            .subheader {
                color: #2ca02c;
                font-size: 20px;
            }
            .footer {
                color: #1f77b4;
                font-size: 18px;
            }
        </style>
    """,
        unsafe_allow_html=True,
    )  # Permet d'afficher du html et CSS

# Affichage titre
def affichage_titre():
    """
    Objectif :
        Afficher le titre et la description
    """

    # Titre
    st.title("🌍 API étude sectorielle et concurrentielle Data Marketing")

    # Description
    st.markdown(
        '<p class="footer">Explorez les données, analysez les tendances du marché, et optimisez vos stratégies commerciales.</p>',
        unsafe_allow_html=True,
    )
    st.write("Bienvenue dans l'outil de Data Marketing. Choisissez une page dans le menu à gauche pour commencer.")

# Navigation entre les différentes pages
def navigation():
    """
    Objectif :
        Afficher un sélecteur pour naviguer entre les pages.
    """

    with st.sidebar:
        st.markdown("## 🧭 Navigation")
        page_selectionnee = st.radio(
            label="Choisissez une page :",
            options=["🏠 Accueil", "📊 Données INSEE", "🗺️ Données OSM"],
            index=0
        )

    if "Accueil" in page_selectionnee:
        return "accueil"
    elif "INSEE" in page_selectionnee:
        return "insee"
    elif "OSM" in page_selectionnee:
        return "osm"
