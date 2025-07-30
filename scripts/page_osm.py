import streamlit as st
from streamlit_folium import st_folium
from fonctions_basiques import charger_communes, extraction_adresse_OSM, choix_centre_OSM, charger_donnees_iris_socio, \
    charger_coefficients_trafic, preparer_donnees_socio
from fonctions_cartographie import transfo_geodataframe, creer_carte_enrichie
from interface import interface_recherche_osm, interface_selection_socio


def page_osm(path_communes, path_iris_socio, path_coeff_trafic):
    """Page principale pour l'analyse concurrentielle et territoriale via OpenStreetMap."""
    st.title("🗺️ Analyse Concurrentielle via OpenStreetMap")

    # --- Chargement des données de référence (mis en cache) ---
    with st.spinner("Chargement des données"):
        df_coefficients = charger_coefficients_trafic(path_coeff_trafic)
        df_communes = charger_communes(path_communes)
        df_iris_base = charger_donnees_iris_socio(path_iris_socio)

    if df_communes.empty or df_iris_base is None:
        st.error("Le chargement des données de base a échoué. L'application ne peut pas continuer.")
        return

    # --- Pré-calcul des données socio (rapide grâce au cache) ---
    dict_geodatas = preparer_donnees_socio(df_iris_base, df_communes)

    # --- Interface de sélection dans la sidebar ---
    gdf_socio_filtre, indicateur, nom_indicateur, maille = interface_selection_socio(dict_geodatas)

    # --- PARTIE 1 : RECHERCHE DES ÉTABLISSEMENTS ---
    with st.expander("🚀 Lancer une nouvelle analyse", expanded=True):
        df_etablissements_osm = interface_recherche_osm(df_communes)

    # --- PARTIE 2 : AFFICHAGE DES RÉSULTATS ---
    if df_etablissements_osm is not None and not df_etablissements_osm.empty:
        st.header("Résultats de l'analyse")

        df_etablissements_osm[["adresse_simplifiee", "precision_geocodage"]] = df_etablissements_osm.apply(
            extraction_adresse_OSM, axis=1)
        lat_centre_OSM, lon_centre_OSM = choix_centre_OSM(df_etablissements_osm)
        gdf_etablissements_osm = transfo_geodataframe(df_etablissements_osm, "longitude", "latitude")

        st.markdown("---")
        st.subheader("Carte Interactive")
        if nom_indicateur and maille: st.write(f"Avec couche de données : **{nom_indicateur}** (maille {maille})")

        # --- Sélecteurs pour le mode d'affichage ---
        st.markdown("**Mode d'affichage des concurrents :**")
        mode_affichage = st.radio("Choisir le type de visualisation :",
                                  ('Points', 'Cercles d\'influence', 'Isochrones'), horizontal=True,
                                  label_visibility="collapsed")

        rayon_cercles, temps_isochrones = None, None
        if mode_affichage == 'Cercles d\'influence':
            rayon_cercles = st.slider("Rayon d'influence (m) :", 100, 5000, 1000, 100)
        elif mode_affichage == 'Isochrones':
            temps_isochrones = st.slider("Temps de trajet en voiture (min) :", 1, 20, 5, 1)

        # --- Création et affichage de la carte et des légendes ---
        map_object, legend_enseignes, legend_socio_color, legend_socio_single = creer_carte_enrichie(
            gdf_etablissements=gdf_etablissements_osm, lat_centre=lat_centre_OSM, lon_centre=lon_centre_OSM,
            gdf_socio=gdf_socio_filtre, colonne_socio=indicateur, nom_indicateur_socio=nom_indicateur,
            mode_affichage_etablissements=mode_affichage, rayon_cercles=rayon_cercles,
            temps_isochrones=temps_isochrones, df_coefficients=df_coefficients
        )

        col_carte, col_legende = st.columns([3, 1])
        with col_carte:
            st_folium(map_object, width=800, height=600, returned_objects=[])

        with col_legende:
            st.write("**Légende**")
            if legend_enseignes:
                st.write("**Enseignes**")
                for nom, color in legend_enseignes.items():
                    st.markdown(f'<span style="color:{color}; font-size:22px;">●</span> {nom}', unsafe_allow_html=True)
            if legend_socio_color or legend_socio_single:
                st.markdown("<hr style='margin:0.5em 0;'>", unsafe_allow_html=True)
            if legend_socio_color:
                st.write(f"**{legend_socio_color.caption}**")
                gradient_hex = [legend_socio_color(x) for x in legend_socio_color.index]
                st.markdown(
                    f'<div style="height: 25px; border: 1px solid #ccc; border-radius: 5px; background: linear-gradient(to right, {", ".join(gradient_hex)});"/>',
                    unsafe_allow_html=True)
                c1, c2 = st.columns(2);
                c1.markdown(f"<small>{legend_socio_color.vmin:,.0f}".replace(",", " ") + "</small>",
                            unsafe_allow_html=True);
                c2.markdown(
                    f'<div style="text-align: right;"><small>{"{:,}".format(round(legend_socio_color.vmax)).replace(",", " ")}</small></div>',
                    unsafe_allow_html=True)
            elif legend_socio_single:
                st.write(f"**{legend_socio_single['label']}**");
                st.markdown(f"Valeur unique : **{'{:,.0f}'.format(legend_socio_single['value']).replace(',', ' ')}**")

        if st.checkbox("Afficher le détail des établissements (tableau)"):
            st.dataframe(df_etablissements_osm.drop(columns=['geometry']))
    else:
        st.info("👋 Bienvenue ! Lancez une recherche dans le panneau ci-dessus pour commencer.")