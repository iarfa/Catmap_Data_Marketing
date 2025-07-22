# =======================
# 📦 Imports & Librairies
# =======================
import streamlit as st
from fonctions_basiques import (
    charger_etablissements,
    charger_centres_departements,
    apercu_donnees,
    filtrer_donnees,
    choix_centre_departement
)
from fonctions_cartographie import (
    transfo_geodataframe,
    choix_carte
)

# =======================
# 📄 Fonction principale de la page INSEE
# =======================
def page_insee(path_etablissement, path_centres_departements):
    """
    Objectif :
        Page dédiée aux données INSEE : aperçu, filtrage, carte.
    """

    # Titre
    st.header("📊 Analyse des données INSEE")

    # =======================
    # 📥 Chargement des données
    # =======================

    # Chemins
    df_etablissements = charger_etablissements(path_etablissement)
    df_centres_dep = charger_centres_departements(path_centres_departements)

    # Chargement des données
    if df_etablissements.empty or df_centres_dep.empty:
        st.warning("Chargement des données échoué. Impossible d'afficher la page.")
        return

    # =======================
    # 👁️ Aperçu des données
    # =======================
    apercu_donnees(df_etablissements, 3)

    # =======================
    # 🧼 Filtrage utilisateur
    # =======================
    df_etablissements_filtre = filtrer_donnees(df_etablissements)

    # =======================
    # 🗺️ Choix du centre de carte
    # =======================
    departement_choisi, lat_centre, lon_centre = choix_centre_departement(
        df_etablissements_filtre, df_centres_dep
    )

    # =======================
    # 📍 Transformation GeoDataFrame
    # =======================
    #gdf_etablissements = transfo_geodataframe(
    #    df_etablissements_filtre, longitude_col="longitude", latitude_col="latitude", crs="EPSG:4326"
    #)

    # =======================
    # 🗺️ Affichage de la carte
    # =======================
    choix_carte(df_etablissements_filtre, lat_centre, lon_centre)
