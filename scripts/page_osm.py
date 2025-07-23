import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from streamlit_folium import st_folium

# Imports depuis vos modules personnalisés
from fonctions_basiques import (
    charger_communes,
    extraction_adresse_OSM,
    choix_centre_OSM,
    charger_donnees_iris_socio,
    preparer_donnees_socio
)
from fonctions_cartographie import (
    transfo_geodataframe,
    creer_carte_enrichie
)
from interface import (
    interface_recherche_osm,
    interface_selection_socio
)


def page_osm(path_communes, path_iris_socio):
    st.title("🗺️ Analyse Concurrentielle via OpenStreetMap")

    df_communes = charger_communes(path_communes)
    if df_communes.empty:
        st.warning("Chargement des données géographiques (communes) échoué.")
        return

    df_etablissements_osm = interface_recherche_osm(df_communes)

    if df_etablissements_osm is not None and not df_etablissements_osm.empty:
        st.header("1. Établissements Concurrents Trouvés")
        st.dataframe(df_etablissements_osm)
        df_etablissements_osm[["adresse_simplifiee", "precision_geocodage"]] = df_etablissements_osm.apply(
            extraction_adresse_OSM, axis=1)
        lat_centre_OSM, lon_centre_OSM = choix_centre_OSM(df_etablissements_osm)

        st.markdown("---")
        st.header("2. Analyse du Territoire")

        gdf_socio_filtre, indicateur, nom_indicateur = None, None, None
        df_iris_base = charger_donnees_iris_socio(path_iris_socio)
        if df_iris_base is not None:
            dict_geodatas = preparer_donnees_socio(df_iris_base, df_communes)
            gdf_selectionne, indicateur, nom_indicateur, maille = interface_selection_socio(dict_geodatas)
            if gdf_selectionne is not None:
                df_deps = dict_geodatas['Département']
                df_deps['label'] = df_deps['CODE_DEPT'] + '_' + df_deps['NOM_COM']
                deps_selectionnes = st.multiselect("Filtrer la vue socio-économique :", options=df_deps['label'])
                if deps_selectionnes:
                    codes_deps = [d.split('_')[0] for d in deps_selectionnes]
                    gdf_socio_filtre = gdf_selectionne[gdf_selectionne['CODE_DEPT'].isin(codes_deps)]
                    st.subheader(f"{nom_indicateur} à la maille {maille}")
                    cols = [col for col in ['NOM_COM', 'CODE_DEPT', indicateur] if col in gdf_socio_filtre.columns]
                    st.dataframe(gdf_socio_filtre[cols].sort_values(by=indicateur, ascending=False).head(10))
                else:
                    st.info("Sélectionnez au moins un département pour afficher l'analyse.")

        st.markdown("---")
        st.header("3. Carte Interactive")

        gdf_etablissements_osm = transfo_geodataframe(df_etablissements_osm, "longitude", "latitude")

        map_object, legend_dict = creer_carte_enrichie(
            gdf_etablissements=gdf_etablissements_osm, lat_centre=lat_centre_OSM, lon_centre=lon_centre_OSM,
            gdf_socio=gdf_socio_filtre, colonne_socio=indicateur, nom_indicateur_socio=nom_indicateur
        )

        col_carte, col_legende = st.columns([4, 1])
        with col_carte:
            st_folium(map_object, width=700, height=500, returned_objects=[])

        with col_legende:
            st.write("**Légende des enseignes**")
            if legend_dict:
                for nom, color in legend_dict.items():
                    st.markdown(f'<span style="color:{color}; font-size:22px;">●</span> {nom}', unsafe_allow_html=True)

    else:
        st.info("Veuillez lancer une recherche d'établissements pour commencer l'analyse.")