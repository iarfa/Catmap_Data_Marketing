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
    charger_coefficients_trafic,
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


def page_osm(path_communes, path_iris_socio, path_coeff_trafic):
    """
    Page principale pour l'analyse concurrentielle et territoriale via OpenStreetMap.
    """
    st.title("🗺️ Analyse Concurrentielle via OpenStreetMap")

    # --- Chargement des données de référence ---
    df_coefficients = charger_coefficients_trafic(path_coeff_trafic)
    df_communes = charger_communes(path_communes)
    if df_communes.empty:
        st.warning("Chargement des données géographiques (communes) échoué.")
        return

    # --- PARTIE 1 : RECHERCHE DES ÉTABLISSEMENTS ---
    df_etablissements_osm = interface_recherche_osm(df_communes)

    # --- PARTIE 2 : AFFICHAGE DES RÉSULTATS ---
    if df_etablissements_osm is not None and not df_etablissements_osm.empty:
        st.header("1. Établissements Concurrents Trouvés")
        if st.checkbox("Afficher le détail des établissements (tableau)"):
            st.dataframe(df_etablissements_osm)

        df_etablissements_osm[["adresse_simplifiee", "precision_geocodage"]] = df_etablissements_osm.apply(
            extraction_adresse_OSM, axis=1)
        lat_centre_OSM, lon_centre_OSM = choix_centre_OSM(df_etablissements_osm)

        # --- Sélection des données socio-économiques ---
        gdf_socio_filtre, indicateur, nom_indicateur, maille = None, None, None, None
        df_iris_base = charger_donnees_iris_socio(path_iris_socio)
        if df_iris_base is not None:
            dict_geodatas = preparer_donnees_socio(df_iris_base, df_communes)
            gdf_socio_filtre, indicateur, nom_indicateur, maille = interface_selection_socio(dict_geodatas)

        st.markdown("---")
        st.header("Carte Interactive")

        if nom_indicateur and maille:
            st.subheader(f"{nom_indicateur} à la maille {maille}")

        # --- Sélecteurs pour le mode d'affichage de la carte ---
        st.markdown("**Mode d'affichage des concurrents :**")
        mode_affichage = st.radio(
            "Choisir le type de visualisation :", ('Points', 'Cercles d\'influence', 'Isochrones'),
            horizontal=True, label_visibility="collapsed"
        )
        rayon_cercles, temps_isochrones = None, None
        if mode_affichage == 'Cercles d\'influence':
            rayon_cercles = st.slider("Rayon d'influence (m) :", 100, 5000, 1000, 100)
        elif mode_affichage == 'Isochrones':
            temps_isochrones = st.slider("Temps de trajet (min) :", 2, 20, 10, 1)

        # --- Création et affichage de la carte et des légendes ---
        gdf_etablissements_osm = transfo_geodataframe(df_etablissements_osm, "longitude", "latitude")

        map_object, legend_enseignes, legend_socio_color, legend_socio_single = creer_carte_enrichie(
            gdf_etablissements=gdf_etablissements_osm, lat_centre=lat_centre_OSM, lon_centre=lon_centre_OSM,
            gdf_socio=gdf_socio_filtre, colonne_socio=indicateur, nom_indicateur_socio=nom_indicateur,
            mode_affichage_etablissements=mode_affichage, rayon_cercles=rayon_cercles,
            temps_isochrones=temps_isochrones,
            df_coefficients=df_coefficients
        )

        col_carte, col_legende = st.columns([4, 1])
        with col_carte:
            st_folium(map_object, width=700, height=500, returned_objects=[])

        with col_legende:
            st.write("**Légende des enseignes**")
            if legend_enseignes:
                for nom, color in legend_enseignes.items():
                    st.markdown(f'<span style="color:{color}; font-size:22px;">●</span> {nom}', unsafe_allow_html=True)

            if legend_socio_color:
                st.markdown("<hr style='margin:0.5em 0;'>", unsafe_allow_html=True)
                st.write(f"**{legend_socio_color.caption}**")
                gradient_hex = [legend_socio_color(x) for x in legend_socio_color.index]
                css_gradient = ", ".join(gradient_hex)
                st.markdown(
                    f"""<div style="height: 25px; border: 1px solid #ccc; border-radius: 5px; background: linear-gradient(to right, {css_gradient});"></div>""",
                    unsafe_allow_html=True)
                min_val = f"{legend_socio_color.vmin:,.0f}".replace(",", " ")
                max_val = f"{legend_socio_color.vmax:,.0f}".replace(",", " ")
                c1, c2 = st.columns(2)
                c1.markdown(f'<div style="text-align: left; font-size: 14px;">{min_val}</div>', unsafe_allow_html=True)
                c2.markdown(f'<div style="text-align: right; font-size: 14px;">{max_val}</div>', unsafe_allow_html=True)

            elif legend_socio_single:
                st.markdown("<hr style='margin:0.5em 0;'>", unsafe_allow_html=True)
                st.write(f"**{legend_socio_single['label']}**")
                val = f"{legend_socio_single['value']:,.0f}".replace(",", " ")
                st.markdown(
                    f'<span style="background-color: #800026; color:white; border-radius: 5px; padding: 2px 5px;">&nbsp;{val}&nbsp;</span>',
                    unsafe_allow_html=True)

    else:
        st.info("Veuillez lancer une recherche d'établissements pour commencer l'analyse.")