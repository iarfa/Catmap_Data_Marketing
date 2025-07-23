# =======================
# 📦 Imports & Librairies
# =======================
import streamlit as st
import geopandas as gpd
from fonctions_basiques import (
    extraction_adresse_OSM,
    choix_centre_OSM,
    charger_communes,
    preparer_donnees_socio)
from fonctions_cartographie import (
    transfo_geodataframe,
    choix_carte_osm
)
from interface import (
    interface_recherche_osm,
    interface_selection_socio)

# Page OSM
def page_osm(path_communes, path_iris_socio):
    """
    Page dédiée à l'analyse via OpenStreetMap, enrichie des données socio-économiques.
    """
    st.title("🗺️ Analyse Concurrentielle via OpenStreetMap")

    # --- PARTIE 1 : RECHERCHE DES ÉTABLISSEMENTS ---
    df_communes = charger_communes(path_communes)
    df_etablissements_osm = interface_recherche_osm(df_communes)

    # --- PARTIE 2 : AFFICHAGE DES RÉSULTATS ---
    if df_etablissements_osm is not None and not df_etablissements_osm.empty:

        # --- A. Résultats de la recherche OSM ---
        st.header("Table des établissements")
        st.dataframe(df_etablissements_osm)

        # Traitements et préparation de la carte des concurrents
        df_etablissements_osm[["adresse_simplifiee", "precision_geocodage"]] = df_etablissements_osm.apply(
            extraction_adresse_OSM, axis=1
        )
        lat_centre_OSM, lon_centre_OSM = choix_centre_OSM(df_etablissements_osm)

        # --- B. Section d'enrichissement socio-économique ---
        # Préparation des données en arrière-plan
        try:
            df_iris_base = gpd.read_parquet(path_iris_socio)
            dict_geodatas = preparer_donnees_socio(df_iris_base)
        except FileNotFoundError:
            st.error(f"Fichier de données socio-économiques introuvable.")
            dict_geodatas = None

        if dict_geodatas:
            # L'interface s'affiche dans la sidebar et nous retourne les choix de l'utilisateur
            gdf_selectionne, indicateur, nom_indicateur, maille = interface_selection_socio(dict_geodatas)

            # --- MODIFIÉ : On n'affiche cette section que si l'utilisateur a activé une option ---
            if gdf_selectionne is not None and indicateur is not None:
                st.markdown("---")
                st.header("Analyse du Territoire")

                # Le nouveau titre, plus propre
                st.subheader(f"{nom_indicateur} à la maille {maille}")

                # Définition des colonnes à afficher
                cols_a_afficher = [indicateur]
                if 'NOM_COM' in gdf_selectionne.columns: cols_a_afficher.insert(0, 'NOM_COM')
                if 'CODE_DEPT' in gdf_selectionne.columns: cols_a_afficher.insert(0, 'CODE_DEPT')

                st.dataframe(
                    gdf_selectionne[cols_a_afficher].sort_values(by=indicateur, ascending=False).head(20)
                )

        # --- C. Carte des établissements concurrents ---
        st.markdown("---")
        st.header("Carte des Établissements")
        gdf_etablissements_osm = transfo_geodataframe(
            df_etablissements_osm,
            longitude_col="longitude", latitude_col="latitude"
        )
        choix_carte_osm(gdf_etablissements_osm, lat_centre_OSM, lon_centre_OSM)

    else:
        st.info("Veuillez lancer une recherche d'établissements pour commencer l'analyse.")