# Librairies
import os
import time
import folium
import geopandas as gpd
# import networkx as nx # Semble inutilisé
import numpy as np
# import openrouteservice # Nous utilisons requests pour l'ORS local
import osmnx as ox  # Utilisé dans isochrone_OSM (inchangée)
import pandas as pd
import requests  # Important pour appeler votre ORS local
import json  # Pour construire le payload de la requête
import streamlit as st
from shapely.geometry import Point, Polygon  # Utilisé dans isochrone_polygon (inchangée)
from streamlit_folium import st_folium


# Clé d'API pour OpenRouteService (utilisée par la fonction isochrone_polygon existante)
# API_KEY = "VOTRE_CLE_API_OPENROUTESERVICE_PUBLIQUE_SI_NECESSAIRE_AILLEURS"
# client = openrouteservice.Client(key=API_KEY) # Utilisé par isochrone_polygon


# Fonction de transformation en geodatraframe (INCHANGÉE)
def transfo_geodataframe(df, longitude_col, latitude_col, crs="EPSG:4326"):
    return gpd.GeoDataFrame(
        df, geometry=gpd.points_from_xy(df[longitude_col], df[latitude_col]), crs=crs
    )


# =======================
# Section Calcul isochrones (fonctions ORS publiques ou OSMnx inchangées)
# =======================
# Vos fonctions isochrone_polygon et isochrone_OSM restent ici si vous les utilisez ailleurs.
# Pour l'affichage avec l'ORS local, nous faisons l'appel API directement dans les fonctions d'affichage.

# ==============================================
# Section base INSEE - Fonctions d'affichage
# ==============================================

# Affichage de la carte (uniquement des points) - INSEE (INCHANGÉE)
def affichage_carte_points(data, lat_centre, lon_centre):
    if lat_centre is None or lon_centre is None:
        st.warning("Veuillez sélectionner une zone pour afficher la carte.")
        return  # Ajout d'un return pour ne rien faire si pas de centre
    if data.empty:
        st.info("Aucun établissement à afficher sur la carte.")
        return

    carte = folium.Map(location=[lat_centre, lon_centre], zoom_start=12)
    for _, ligne in data.iterrows():
        # Assurer la robustesse en cas de colonnes manquantes ou de NaN
        lat = ligne.get('latitude')
        lon = ligne.get('longitude')
        if pd.isna(lat) or pd.isna(lon):
            st.warning(
                f"Coordonnées manquantes pour {ligne.get('denominationUniteLegale', 'un établissement')}. Il sera ignoré.")
            continue

        popup_info = f"""
        <b>Nom entreprise :</b> {ligne.get('denominationUniteLegale', 'N/A')}<br>
        <b>SIREN :</b> {ligne.get('siren', 'N/A')}<br>
        <b>SIRET :</b> {ligne.get('siret', 'N/A')}<br>
        <b>Date création :</b> {ligne.get('dateCreationEtablissement', 'N/A')}<br>
        <b>Adresse :</b> {ligne.get('adresse', 'N/A')}<br>
        <b>Précision géocodage :</b> {ligne.get('precision_geocodage', 'N/A')}
        """
        folium.CircleMarker(
            location=[lat, lon],
            radius=7,
            color='blue',
            fill=True,
            fill_color='blue',
            fill_opacity=0.6,
            popup=folium.Popup(popup_info, max_width=300)
        ).add_to(carte)
    st_folium(carte, width=800, height=600, returned_objects=[])


# Affichage de la carte avec un cercle de rayon R mètres - INSEE (INCHANGÉE)
def affichage_carte_cercles(data, lat_centre, lon_centre):
    if lat_centre is None or lon_centre is None:
        st.warning("Veuillez sélectionner une zone pour afficher la carte.")
        return
    if data.empty:
        st.info("Aucun établissement à afficher sur la carte.")
        return

    carte = folium.Map(location=[lat_centre, lon_centre], zoom_start=12)
    rayon_influence = st.slider(
        "Rayon d'influence autour des établissements (en mètres)",
        min_value=50, max_value=2000, value=200, step=50,
        key="slider_insee_cercles"  # Clé unique pour ce slider
    )
    for _, ligne in data.iterrows():
        lat = ligne.get('latitude')  # Utiliser .get() pour éviter KeyError si la colonne n'existe pas
        lon = ligne.get('longitude')

        # Si latitude/longitude ne sont pas directes, essayer geometry (si c'est un GeoDataFrame)
        if pd.isna(lat) and 'geometry' in ligne and hasattr(ligne.geometry, 'y'):
            lat = ligne.geometry.y
        if pd.isna(lon) and 'geometry' in ligne and hasattr(ligne.geometry, 'x'):
            lon = ligne.geometry.x

        if pd.isna(lat) or pd.isna(lon):
            st.warning(
                f"Coordonnées manquantes pour {ligne.get('denominationUniteLegale', 'un établissement')}. Il sera ignoré.")
            continue

        popup_info = f"""
        <b>Nom entreprise :</b> {ligne.get('denominationUniteLegale', 'N/A')}<br>
        <b>SIREN :</b> {ligne.get('siren', 'N/A')}<br>
        <b>SIRET :</b> {ligne.get('siret', 'N/A')}<br>
        <b>Date création :</b> {ligne.get('dateCreationEtablissement', 'N/A')}<br>
        <b>Adresse :</b> {ligne.get('adresse', 'N/A')}<br>
        <b>Précision géocodage :</b> {ligne.get('precision_geocodage', 'N/A')}
        """
        folium.Circle(
            location=[lat, lon], radius=rayon_influence, color='red',
            fill=True, fill_color='red', fill_opacity=0.3
        ).add_to(carte)
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_info, max_width=300),
            icon=folium.Icon(color="red", icon="cloud")
        ).add_to(carte)
    st_folium(carte, width=800, height=600, returned_objects=[])


# ===================================================
# NOUVELLE FONCTION : Affichage Isochrones pour INSEE
# ===================================================
def affichage_isochrones_insee(data, lat_centre, lon_centre):
    """
    Objectif :
        Afficher une carte des établissements INSEE avec leurs isochrones de temps de trajet en voiture.

    Paramètres :
        data (pd.DataFrame) : DataFrame contenant les établissements INSEE.
                               Doit avoir 'latitude', 'longitude', 'denominationUniteLegale', 'adresse'.
        lat_centre (float) : Latitude du centre de la carte.
        lon_centre (float) : Longitude du centre de la carte.
    """
    if lat_centre is None or lon_centre is None:
        st.warning("Veuillez sélectionner une zone pour afficher la carte.")
        return
    if data.empty:
        st.info("Aucun établissement (données INSEE) à afficher sur la carte.")
        return

    # Slider pour choisir le temps de trajet
    temps_trajet_minutes = st.slider(
        "Temps de trajet pour l'isochrone (en minutes)",
        min_value=5, max_value=30, value=15, step=5,
        key="slider_isochrones_insee"  # Clé unique pour ce slider
    )
    temps_trajet_secondes = temps_trajet_minutes * 60

    # Préparation des localisations pour l'API ORS
    locations_for_api = []
    valid_data_for_map = []  # Pour stocker les lignes avec des coordonnées valides
    for index, ligne in data.iterrows():
        lat = ligne.get('latitude')
        lon = ligne.get('longitude')
        if pd.notna(lat) and pd.notna(lon):
            locations_for_api.append([lon, lat])  # ORS attend [longitude, latitude]
            valid_data_for_map.append(ligne)
        else:
            st.warning(
                f"Coordonnées manquantes ou invalides pour {ligne.get('denominationUniteLegale', 'un établissement INSEE')}. Il sera ignoré pour les isochrones.")

    if not locations_for_api:
        st.warning("Aucun établissement INSEE avec des coordonnées valides pour calculer les isochrones.")
        return

    # Convertir valid_data_for_map en DataFrame pour faciliter l'itération plus tard
    df_valid_data = pd.DataFrame(valid_data_for_map)

    # Configuration de la requête à l'ORS local
    ors_url_local = "http://localhost:8080/ors/v2/isochrones/driving-car"
    payload = {
        "locations": locations_for_api,
        "range": [temps_trajet_secondes],
        "range_type": "time",
        "attributes": ["area", "reachfactor"],
        "smoothing": 25
    }
    headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'Accept': 'application/json, application/geo+json'
    }

    isochrones_geojson_features = []
    isochrones_data_response = None  # Pour stocker toute la réponse ORS
    with st.spinner(f"Calcul des isochrones INSEE de {temps_trajet_minutes} minutes en cours..."):
        try:
            response = requests.post(ors_url_local, json=payload, headers=headers, timeout=90)
            response.raise_for_status()
            isochrones_data_response = response.json()  # Stocker la réponse complète
            if isochrones_data_response.get("features"):
                isochrones_geojson_features = isochrones_data_response["features"]
                st.success(f"{len(isochrones_geojson_features)} isochrones INSEE calculées.")
            else:
                st.warning("Aucune 'feature' isochrone retournée par l'API ORS pour les données INSEE.")
        except requests.exceptions.Timeout:
            st.error(
                f"ERREUR : La requête ORS a expiré (timeout de 90s) pour les données INSEE. Le service est peut-être surchargé.")
            return
        except requests.exceptions.ConnectionError:
            st.error(
                "ERREUR : Impossible de se connecter à votre service Openrouteservice local sur http://localhost:8080.")
            return
        except requests.exceptions.HTTPError as e:
            st.error(f"ERREUR HTTP de l'API ORS locale pour les données INSEE : {e}")
            try:
                error_content = e.response.json()
                st.error(f"Détail de l'erreur ORS : {error_content.get('error', {}).get('message', e.response.text)}")
                if error_content.get('error', {}).get('code') == 3004:
                    st.error("Vérifiez le paramètre 'maximum_locations' dans votre fichier ors-config.yml.")
            except json.JSONDecodeError:
                st.error(f"Contenu brut de la réponse d'erreur ORS : {e.response.text}")
            return
        except Exception as e:
            st.error(f"Une erreur inattendue est survenue lors du calcul des isochrones INSEE : {e}")
            return

    # Couleurs et légende (pourrait être basé sur Intitules_NAF_VF si souhaité)
    # Pour l'instant, une couleur unique ou un cycle simple.
    couleurs_insee = ['purple', 'darkpurple', 'pink', 'cadetblue', 'lightgray']  # Palette différente pour INSEE

    # Utiliser une colonne unique pour la légende pour l'instant, ou adapter si besoin
    # Pour la simplicité, on ne fait pas de légende par type d'établissement INSEE ici,
    # mais on pourrait l'ajouter en se basant sur 'Intitules_NAF_VF' comme pour OSM.

    col_map, col_legende = st.columns([3, 1])  # Maintenir la structure avec légende

    with col_map:
        carte = folium.Map(location=[lat_centre, lon_centre], zoom_start=11)

        idx_feature = 0
        for _, ligne in df_valid_data.iterrows():  # Itérer sur les données valides
            lat = ligne['latitude']  # On sait qu'elles sont valides ici
            lon = ligne['longitude']
            nom_entreprise = ligne.get('denominationUniteLegale', 'N/A')

            color = couleurs_insee[idx_feature % len(couleurs_insee)]  # Cycle de couleurs

            popup_info = f"""
                <b>Nom entreprise :</b> {nom_entreprise}<br>
                <b>SIREN :</b> {ligne.get('siren', 'N/A')}<br>
                <b>Adresse :</b> {ligne.get('adresse', 'N/A')}<br>
                <b>Isochrone :</b> {temps_trajet_minutes} minutes
                """

            folium.CircleMarker(
                location=[lat, lon], radius=5, color=color, fill=True,
                fill_color=color, fill_opacity=0.9, tooltip=nom_entreprise,
                popup=folium.Popup(popup_info, max_width=300)
            ).add_to(carte)

            if idx_feature < len(isochrones_geojson_features):
                feature_isochrone = isochrones_geojson_features[idx_feature]
                folium.GeoJson(
                    feature_isochrone,
                    name=f"Isochrone {nom_entreprise}",
                    style_function=lambda x, c=color: {
                        "fillColor": c, "color": c, "weight": 2, "fillOpacity": 0.25
                    }
                ).add_to(carte)
                idx_feature += 1

        if isochrones_data_response and isochrones_data_response.get("bbox"):
            bbox = isochrones_data_response["bbox"]
            map_bounds = [[bbox[1], bbox[0]], [bbox[3], bbox[2]]]
            try:
                carte.fit_bounds(map_bounds)
            except Exception as e_fit:
                st.warning(f"Impossible d'ajuster les limites de la carte INSEE automatiquement: {e_fit}")

        st_folium(carte, width=700, height=600, returned_objects=[])

    with col_legende:
        st.markdown("#### Isochrones INSEE")
        st.markdown(f"Temps de trajet : **{temps_trajet_minutes} minutes**")
        # Une légende simple ici, car on n'a pas de "type" d'établissement pour la couleur
        # Si vous voulez une légende plus détaillée, il faudrait adapter la logique de coloration
        # en fonction d'une colonne (ex: NAF) et l'afficher ici.
        st.markdown(
            f'<span style="color:purple; font-size:22px;">&#9632;</span> <span style="font-size:20px;">Zone d\'accessibilité</span>',
            unsafe_allow_html=True)


# ===================================================
# MODIFICATION : Choix du type de carte pour INSEE
# ===================================================
def choix_carte(data, lat_centre, lon_centre):
    """
    Objectif :
        Afficher une carte parmi les différentes options disponibles (points, cercles, isochrones) pour INSEE.

    Paramètres :
        data : Table filtrée par l'utilisateur (avec colonnes 'latitude', 'longitude', etc.)
        lat_centre : Latitude du centre de la carte
        lon_centre : Longitude du centre de la carte
    """

    # Initialisation de l'état si non défini
    if "affichage_mode_insee" not in st.session_state:  # Clé de session spécifique à INSEE
        st.session_state["affichage_mode_insee"] = "points"  # Par défaut sur points

    st.subheader("Choisissez un type d'affichage pour la carte des établissements INSEE :")

    # Boutons dans trois colonnes
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Points Simples", key="btn_insee_points"):  # Clé de bouton unique
            st.session_state["affichage_mode_insee"] = "points"

    with col2:
        if st.button("Cercles d'influence", key="btn_insee_cercles"):  # Clé de bouton unique
            st.session_state["affichage_mode_insee"] = "cercles"

    with col3:
        if st.button("Isochrones", key="btn_insee_isochrones"):  # Clé de bouton unique
            st.session_state["affichage_mode_insee"] = "isochrones"

    # Vérification des données et du centre avant d'appeler les fonctions d'affichage
    if data is None or data.empty:
        st.info("Aucun établissement INSEE trouvé pour les critères de filtrage actuels.")
        return
    if lat_centre is None or lon_centre is None:
        st.warning("Veuillez sélectionner un département pour centrer la carte avant de choisir un type d'affichage.")
        return

    # Affichage de la carte selon le mode choisi
    if st.session_state["affichage_mode_insee"] == "points":
        affichage_carte_points(data, lat_centre, lon_centre)
    elif st.session_state["affichage_mode_insee"] == "cercles":
        affichage_carte_cercles(data, lat_centre, lon_centre)
    elif st.session_state["affichage_mode_insee"] == "isochrones":
        affichage_isochrones_insee(data, lat_centre, lon_centre)


# =======================
# Section OSM (fonctions existantes inchangées ici, mais la nouvelle `choix_carte_osm` est ci-dessous)
# =======================

# Rechercher les établissements via open street map (INCHANGÉE)
def recherche_etablissements_osm(noms_etablissements, villes, max_etablissements=1000):
    pays = "France"
    url = "https://nominatim.openstreetmap.org/search"
    headers = {"User-Agent": "CATMAP_Data_Marketing_Streamlit_App"}
    donnees = []
    for nom in noms_etablissements:
        for ville in villes:
            query = f"{nom}, {ville}, {pays}"
            params = {"q": query, "format": "json", "limit": max_etablissements, "addressdetails": 1}
            try:
                response = requests.get(url, params=params, headers=headers, timeout=10)
                response.raise_for_status()
                resultats = response.json()
                if len(resultats) >= 1000:
                    st.warning(f"⚠️ Trop de résultats pour '{query}' (limitée à 1000) — affinez votre recherche.")
                for resultat in resultats:
                    display = resultat.get("display_name", "")
                    lat = float(resultat.get("lat", 0))
                    lon = float(resultat.get("lon", 0))
                    if "," in display:
                        nom_osm, adresse = display.split(",", 1)
                    else:
                        nom_osm, adresse = display, ""
                    donnees.append({
                        "nom_etablissement": nom, "ville": ville, "nom OSM": nom_osm.strip(),
                        "adresse": adresse.strip(), "latitude": lat, "longitude": lon
                    })
            except requests.exceptions.RequestException as e:
                st.error(f"Erreur de requête Nominatim pour '{query}': {e}")
                continue
            except json.JSONDecodeError:
                st.error(
                    f"Erreur de décodage JSON pour '{query}'. Réponse brute: {response.text if 'response' in locals() else 'N/A'}")
                continue
    df = pd.DataFrame(donnees)
    if df.empty:
        st.info("Aucun établissement trouvé avec les critères fournis.")
    else:
        st.success(f"{len(df)} établissements trouvés.")
    return df


# Choix de l'utilisateur pour la recherche OSM (INCHANGÉE)
def interface_recherche_osm():
    st.subheader("Recherche d'établissements via OpenStreetMap")
    noms_etablissements_osm = st.text_input(
        "Entrez un ou plusieurs noms d'établissements (séparés par des virgules)",
        placeholder="Ex : Carrefour, Lidl, Auchan",
        value=st.session_state.get("noms_etablissements_osm", "")
    )
    villes_osm = st.text_input(
        "Entrez une ou plusieurs villes (séparées par des virgules)",
        placeholder="Ex : Paris, Lyon, Marseille",
        value=st.session_state.get("villes_osm", "")
    )
    noms_etablissements = [nom.strip() for nom in noms_etablissements_osm.split(",") if nom.strip()]
    villes = [ville.strip() for ville in villes_osm.split(",") if ville.strip()]
    if st.button("Lancer la recherche", key="recherche_osm"):
        st.session_state["noms_etablissements_osm"] = noms_etablissements_osm
        st.session_state["villes_osm"] = villes_osm
        if noms_etablissements and villes:
            with st.spinner("Recherche des établissements OSM en cours..."):
                df_resultats = recherche_etablissements_osm(noms_etablissements, villes)
            if df_resultats is not None and not df_resultats.empty:
                st.session_state["df_etablissements_osm"] = df_resultats
            else:
                st.session_state["df_etablissements_osm"] = pd.DataFrame()
        else:
            st.warning("Veuillez entrer au moins un nom d’établissement et une ville.")
    return st.session_state.get("df_etablissements_osm", pd.DataFrame())


# Affichage de la carte des points OSM (INCHANGÉE)
def affichage_carte_points_osm(data, lat_centre, lon_centre):
    if lat_centre is None or lon_centre is None:
        st.warning("Veuillez sélectionner une zone pour afficher la carte.")
        return
    if data.empty:
        st.info("Aucun établissement à afficher sur la carte.")
        return

    couleurs = ['red', 'blue', 'green', 'orange', 'purple', 'darkred', 'cadetblue',
                'darkgreen', 'darkblue', 'pink', 'lightblue', 'lightgreen', 'beige',
                'gray', 'black']
    etablissements_uniques = data['nom_etablissement'].unique()
    type_to_color = {nom: couleurs[i % len(couleurs)] for i, nom in enumerate(etablissements_uniques)}

    col1, col2 = st.columns([3, 1])
    with col1:
        carte = folium.Map(location=[lat_centre, lon_centre], zoom_start=12)
        for _, ligne in data.iterrows():
            lat, lon = ligne['latitude'], ligne['longitude']
            nom = ligne['nom_etablissement']
            color = type_to_color.get(nom, 'blue')
            popup_info = f"""
            <b>Nom entreprise :</b> {nom}<br>
            <b>Adresse :</b> {ligne['adresse']}<br>
            <b>Précision géocodage :</b> {ligne['precision_geocodage']}
            """
            folium.CircleMarker(
                location=[lat, lon], radius=7, color=color, fill=True,
                fill_color=color, fill_opacity=0.6,
                popup=folium.Popup(popup_info, max_width=300)
            ).add_to(carte)
        st_folium(carte, width=700, height=600, returned_objects=[])
    with col2:
        st.markdown("#### Légende")
        max_legende = 20
        for i, (nom, color) in enumerate(type_to_color.items()):
            if i >= max_legende:
                st.markdown("*... (limité à 20)*")
                break
            st.markdown(
                f'<span style="color:{color}; font-size:22px;">&#9679;</span> '
                f'<span style="font-size:20px;">{nom}</span>',
                unsafe_allow_html=True
            )


# Affichage de la carte avec cercles OSM (INCHANGÉE)
def affichage_carte_cercles_osm(data, lat_centre, lon_centre):
    if lat_centre is None or lon_centre is None:
        st.warning("Veuillez sélectionner une zone pour afficher la carte.")
        return
    if data.empty:
        st.info("Aucun établissement à afficher sur la carte.")
        return

    couleurs = ['red', 'blue', 'green', 'orange', 'purple', 'darkred', 'cadetblue',
                'darkgreen', 'darkblue', 'pink', 'lightblue', 'lightgreen', 'beige',
                'gray', 'black']
    etablissements_uniques = data['nom_etablissement'].unique()
    type_to_color = {nom: couleurs[i % len(couleurs)] for i, nom in enumerate(etablissements_uniques)}

    rayon_influence = st.slider(
        "Rayon d'influence autour des établissements (en mètres)",
        min_value=50, max_value=2000, value=200, step=50, key="slider_osm_cercles"  # Clé unique
    )
    col1, col2 = st.columns([3, 1])
    with col1:
        carte = folium.Map(location=[lat_centre, lon_centre], zoom_start=12)
        for _, ligne in data.iterrows():
            lat = ligne.get('latitude')
            lon = ligne.get('longitude')
            nom = ligne['nom_etablissement']
            if pd.isna(lat) or pd.isna(lon):
                st.warning(
                    f"Coordonnées manquantes pour {nom} à l'adresse {ligne.get('adresse', 'N/A')}. Cet établissement ne sera pas affiché.")
                continue
            color = type_to_color.get(nom, 'red')
            popup_info = f"""
                <b>Nom entreprise :</b> {nom}<br>
                <b>Adresse :</b> {ligne['adresse']}<br>
                <b>Précision géocodage :</b> {ligne['precision_geocodage']}
                """
            folium.Circle(
                location=[lat, lon], radius=rayon_influence, color=color,
                fill=True, fill_color=color, fill_opacity=0.3
            ).add_to(carte)
            folium.CircleMarker(
                location=[lat, lon], radius=6, color=color, fill=True,
                fill_color=color, fill_opacity=0.9,
                popup=folium.Popup(popup_info, max_width=300)
            ).add_to(carte)
        st_folium(carte, width=700, height=600, returned_objects=[])
    with col2:
        st.markdown("#### Légende")
        max_legende = 20
        for i, (nom, color) in enumerate(type_to_color.items()):
            if i >= max_legende:
                st.markdown("*... (limité à 20)*")
                break
            st.markdown(
                f'<span style="color:{color}; font-size:22px;">&#9679;</span> '
                f'<span style="font-size:20px;">{nom}</span>',
                unsafe_allow_html=True
            )


# Affichage Isochrones OSM (fonction créée précédemment, INCHANGÉE)
def affichage_isochrones_osm(data, lat_centre, lon_centre):
    if lat_centre is None or lon_centre is None:
        st.warning("Veuillez sélectionner une zone pour afficher la carte.")
        return
    if data.empty:
        st.info("Aucun établissement à afficher sur la carte.")
        return
    temps_trajet_minutes = st.slider(
        "Temps de trajet pour l'isochrone (en minutes)",
        min_value=5, max_value=30, value=15, step=5,
        key="slider_isochrones_osm"
    )
    temps_trajet_secondes = temps_trajet_minutes * 60
    locations_for_api = []
    valid_data_for_map = []
    for index, ligne in data.iterrows():
        lat = ligne.get('latitude')
        lon = ligne.get('longitude')
        if pd.notna(lat) and pd.notna(lon):
            locations_for_api.append([lon, lat])
            valid_data_for_map.append(ligne)
        else:
            st.warning(
                f"Coordonnées manquantes ou invalides pour {ligne.get('nom_etablissement', 'un établissement')}. Il sera ignoré.")
    if not locations_for_api:
        st.warning("Aucun établissement avec des coordonnées valides pour calculer les isochrones.")
        return
    df_valid_data_osm = pd.DataFrame(valid_data_for_map)

    ors_url_local = "http://localhost:8080/ors/v2/isochrones/driving-car"
    payload = {
        "locations": locations_for_api, "range": [temps_trajet_secondes],
        "range_type": "time", "attributes": ["area", "reachfactor"], "smoothing": 25
    }
    headers = {'Content-Type': 'application/json; charset=utf-8', 'Accept': 'application/json, application/geo+json'}
    isochrones_geojson_features = []
    isochrones_data = None
    with st.spinner(f"Calcul des isochrones de {temps_trajet_minutes} minutes en cours..."):
        try:
            response = requests.post(ors_url_local, json=payload, headers=headers, timeout=90)
            response.raise_for_status()
            isochrones_data = response.json()
            if isochrones_data.get("features"):
                isochrones_geojson_features = isochrones_data["features"]
                st.success(f"{len(isochrones_geojson_features)} isochrones calculées.")
            else:
                st.warning("Aucune 'feature' isochrone retournée par l'API ORS.")
        except requests.exceptions.Timeout:
            st.error(f"ERREUR : La requête ORS a expiré (timeout de 90s).")
            return
        except requests.exceptions.ConnectionError:
            st.error("ERREUR : Impossible de se connecter à votre service Openrouteservice local.")
            return
        except requests.exceptions.HTTPError as e:
            st.error(f"ERREUR HTTP de l'API ORS locale : {e}")
            try:
                error_content = e.response.json()
                st.error(f"Détail de l'erreur ORS : {error_content.get('error', {}).get('message', e.response.text)}")
                if error_content.get('error', {}).get('code') == 3004:
                    st.error("Vérifiez 'maximum_locations' dans ors-config.yml.")
            except json.JSONDecodeError:
                st.error(f"Contenu brut de la réponse d'erreur ORS : {e.response.text}")
            return
        except Exception as e:
            st.error(f"Une erreur inattendue est survenue : {e}")
            return
    couleurs = ['red', 'blue', 'green', 'orange', 'purple', 'darkred', 'cadetblue',
                'darkgreen', 'darkblue', 'pink', 'lightblue', 'lightgreen', 'beige',
                'gray', 'black']
    etablissements_uniques = df_valid_data_osm['nom_etablissement'].unique()
    type_to_color = {nom: couleurs[i % len(couleurs)] for i, nom in enumerate(etablissements_uniques)}
    col1, col2 = st.columns([3, 1])
    with col1:
        carte = folium.Map(location=[lat_centre, lon_centre], zoom_start=11)
        idx_feature = 0
        for _, ligne in df_valid_data_osm.iterrows():
            lat = ligne['latitude']
            lon = ligne['longitude']
            nom = ligne.get('nom_etablissement')
            color = type_to_color.get(nom, 'gray')
            popup_info = f"<b>Nom :</b> {nom}<br><b>Adresse :</b> {ligne.get('adresse', 'N/A')}<br><b>Isochrone :</b> {temps_trajet_minutes} minutes"
            folium.CircleMarker(
                location=[lat, lon], radius=5, color=color, fill=True,
                fill_color=color, fill_opacity=0.9, tooltip=nom,
                popup=folium.Popup(popup_info, max_width=300)
            ).add_to(carte)
            if idx_feature < len(isochrones_geojson_features):
                feature_isochrone = isochrones_geojson_features[idx_feature]
                folium.GeoJson(
                    feature_isochrone, name=f"Isochrone {nom}",
                    style_function=lambda x, c=color: {"fillColor": c, "color": c, "weight": 2, "fillOpacity": 0.25}
                ).add_to(carte)
                idx_feature += 1
            else:
                st.warning(f"Isochrone manquante pour {nom}.")
        if isochrones_data and isochrones_data.get("bbox"):
            bbox = isochrones_data["bbox"]
            map_bounds = [[bbox[1], bbox[0]], [bbox[3], bbox[2]]]
            try:
                carte.fit_bounds(map_bounds)
            except Exception as e_fit:
                st.warning(f"Impossible d'ajuster les limites de la carte automatiquement: {e_fit}")
        st_folium(carte, width=700, height=600, returned_objects=[])
    with col2:
        st.markdown("#### Légende")
        max_legende = 20
        for i, (nom_leg, color_leg) in enumerate(type_to_color.items()):
            if i >= max_legende:
                st.markdown("*... (limité à 20)*")
                break
            st.markdown(
                f'<span style="color:{color_leg}; font-size:22px;">&#9679;</span> '
                f'<span style="font-size:20px;">{nom_leg}</span>',
                unsafe_allow_html=True
            )


# Choix du type de carte OSM (fonction créée précédemment, INCHANGÉE)
def choix_carte_osm(data, lat_centre, lon_centre):
    if lat_centre is None or lon_centre is None:
        st.warning("Veuillez sélectionner une ville pour centrer la carte avant de choisir un type d'affichage.")
    if "affichage_mode_osm" not in st.session_state:
        st.session_state["affichage_mode_osm"] = "points"
    st.subheader("Choisissez un type d'affichage pour la carte des établissements OSM :")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Points Simples", key="btn_osm_points"):
            st.session_state["affichage_mode_osm"] = "points"
    with col2:
        if st.button("Cercles d'influence", key="btn_osm_cercles"):
            st.session_state["affichage_mode_osm"] = "cercles"
    with col3:
        if st.button("Isochrones", key="btn_osm_isochrones"):
            st.session_state["affichage_mode_osm"] = "isochrones"
    if data is None or data.empty:
        if st.session_state.get("df_etablissements_osm") is not None:
            st.info(
                "Aucun établissement trouvé pour les critères de recherche actuels. Modifiez votre recherche pour afficher une carte.")
        return
    if lat_centre is None or lon_centre is None:
        st.warning("Le centre de la carte n'est pas défini. Veuillez sélectionner une ville.")
        return
    if st.session_state["affichage_mode_osm"] == "points":
        affichage_carte_points_osm(data, lat_centre, lon_centre)
    elif st.session_state["affichage_mode_osm"] == "cercles":
        affichage_carte_cercles_osm(data, lat_centre, lon_centre)
    elif st.session_state["affichage_mode_osm"] == "isochrones":
        affichage_isochrones_osm(data, lat_centre, lon_centre)
