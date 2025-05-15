# Librairies
import os
import time
import folium
import geopandas as gpd
import networkx as nx
import numpy as np
import openrouteservice
import osmnx as ox
import pandas as pd
import requests
import streamlit as st
from shapely.geometry import Point, Polygon
from streamlit_folium import st_folium

# Clé d'API pour OpenRouteService (à obtenir sur le site https://account.heigit.org/manage/key)
API_KEY = "5b3ce3597851110001cf6248b6888bf013dd4b1c953908debff81ff1"
client = openrouteservice.Client(key=API_KEY)


# Fonction de transformation en geodatraframe pour la gestion de distance
def transfo_geodataframe(df, longitude_col, latitude_col, crs="EPSG:4326"):
    """
    Objectif :
        Transforme un DataFrame en un GeoDataFrame à partir de colonnes de longitude et latitude.

    Paramètres :
        df (pandas.DataFrame) : Le DataFrame d'entrée avec les données géographiques
        longitude_col (str) : Le nom de la colonne contenant les longitudes
        latitude_col (str) : Le nom de la colonne contenant les latitudes
        crs (str) : Le système de référence de coordonnées (par défaut "EPSG:4326")

    Sortie :
        gpd.GeoDataFrame : Le GeoDataFrame résultant avec les colonnes géométriques
    """
    return gpd.GeoDataFrame(
        df, geometry=gpd.points_from_xy(df[longitude_col], df[latitude_col]), crs=crs
    )


# =======================
# Section Calcul isochrones
# =======================

# Fonction de calcul isochrone (Polygone qui relie tous les points accessibles à N minutes) pour OpenRouteService
def isochrone_polygon(lat, lon, mode, time_limit_min):
    """
    Objectif :
        Récupère l'isochrone autour d'un point donné.

    Paramètres :
        lat (float) : Latitude du point
        lon (float) : Longitude du point
        mode (str) : Mode de transport ('foot-walking','foot-hiking','wheelchair','driving-car','driving-hgv','cycling-regular','cycling-road','cycling-mountain','cycling-electric')
        time_limit (int) : Temps en minutes, à convertir ensuite en secondes

    Sortie :
        Polygon : Polygone représentant l'isochrone
    """
    try:
        response = client.isochrones(
            locations=[(lon, lat)],  # OpenRouteService demande (longitude, latitude)
            profile=mode,  # Mode de déplacement
            range=[time_limit_min * 60],  # Temps limite en secondes
            units="m",
        )

        # Extraire la géométrie du polygone
        isochrone_coords = response["features"][0]["geometry"]["coordinates"][0]
        polygon = Polygon(isochrone_coords)

        return polygon

    # Affichage en cas d'erreur
    except openrouteservice.exceptions.ApiError as e:
        print(f"Erreur API : {e}")
        return None


# Fonction de calcul isochrone (Polygone qui relie tous les points accessibles à N minutes à la vitesse V) pour téléchargement OSM
def isochrone_OSM(graph, lat, lon, travel_time=10, speed_kmh=30):
    """
    Objectif :
        Récupère l'isochrone autour d'un point donné dans un réseau routier.

    Paramètres :
        graph (network.Graph) : Graphe routier à utiliser
        lat (float) : Latitude du point
        lon (float) : Longitude du point
        travel_time (int) : Temps en minutes, à convertir ensuite en secondes
        speed_kmh (int) : Vitesse en km/h

    Sortie :
        Polygon : Polygone représentant l'isochrone
    """
    try:
        # Trouver le nœud le plus proche dans le réseau routier
        center_node = ox.distance.nearest_nodes(graph, lon, lat)

        # Calculer la distance maximale pour l'isochrone
        max_distance = (travel_time / 60) * speed_kmh * 1000  # Convertir en mètres

        # Générer le sous-graph avec un rayon de distance maximale
        subgraph = nx.ego_graph(
            graph, center_node, radius=max_distance, distance="length"
        )

        # Convertir le sous-graph en GeoDataFrame et récupérer le polygone de l'isochrone
        isochrone = (
            ox.graph_to_gdfs(subgraph, nodes=False, edges=True).union_all().convex_hull
        )

        return isochrone

    except Exception as e:
        print(f"Erreur calcul : {e}")
        return None

# =======================
# Section base INSEE
# =======================

# Affichage de la carte (uniquement des points)
def affichage_carte_points(data, lat_centre, lon_centre):
    """
    Objectif :
        Afficher une carte des points pour la table filtrée dans Streamlit

    Paramètres :
        data : Table filtrée par l'utilisateur
        lat_centre : Latitude centre de la carte
        lon_centre : Longitude centre de la carte

    Sortie :
        Carte interactive des établissements
    """
    if lat_centre is None or lon_centre is None:
        st.warning("Veuillez sélectionner une zone pour afficher la carte.")

    else :

        # Initialisation de la carte
        carte = folium.Map(location=[lat_centre, lon_centre], zoom_start=12)

        # Ajout des marqueurs
        for _, ligne in data.iterrows():
            lat, lon = ligne['latitude'], ligne['longitude']
            popup_info = f"""
            <b>Nom entreprise :</b> {ligne['denominationUniteLegale']}<br>
            <b>SIREN :</b> {ligne['siren']}<br>
            <b>SIRET :</b> {ligne['siret']}<br>
            <b>Date création :</b> {ligne['dateCreationEtablissement']}<br>
            <b>Adresse :</b> {ligne['adresse']}<br>
            <b>Précision géocodage :</b> {ligne['precision_geocodage']}
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

        # Affichage via Streamlit
        st_folium(carte, width=800, height=600)


# Affichage de la carte avec un cercle de rayon R mètres
def affichage_carte_cercles(data, lat_centre, lon_centre):
    """
    Objectif :
        Afficher une carte des établissements avec un cercle d'influence de rayon R

    Paramètres :
        data : Table filtrée par l'utilisateur (avec colonnes 'latitude', 'longitude', etc.)
        lat_centre : Latitude du centre de la carte
        lon_centre : Longitude du centre de la carte

    Sortie :
        Carte interactive des établissements avec cercles
    """
    if lat_centre is None or lon_centre is None:
        st.warning("Veuillez sélectionner une zone pour afficher la carte.")
        return

    # Initialisation de la carte
    carte = folium.Map(location=[lat_centre, lon_centre], zoom_start=12)

    # Sélection du rayon d'influence
    rayon_influence = st.slider(
        "Rayon d'influence autour des établissements (en mètres)",
        min_value=50,
        max_value=2000,
        value=200,
        step=50,
        key="slider_insee"
    )

    # Ajout des cercles + marqueurs
    for _, ligne in data.iterrows():
        lat = ligne.get('latitude') or ligne.geometry.y
        lon = ligne.get('longitude') or ligne.geometry.x

        popup_info = f"""
        <b>Nom entreprise :</b> {ligne['denominationUniteLegale']}<br>
        <b>SIREN :</b> {ligne['siren']}<br>
        <b>SIRET :</b> {ligne['siret']}<br>
        <b>Date création :</b> {ligne['dateCreationEtablissement']}<br>
        <b>Adresse :</b> {ligne['adresse']}<br>
        <b>Précision géocodage :</b> {ligne['precision_geocodage']}
        """

        # Cercle de rayon paramétré
        folium.Circle(
            location=[lat, lon],
            radius=rayon_influence,
            color='red',
            fill=True,
            fill_color='red',
            fill_opacity=0.3
        ).add_to(carte)

        # Marqueur avec popup
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_info, max_width=300),
            icon=folium.Icon(color="red", icon="cloud")
        ).add_to(carte)

    # Affichage dans Streamlit
    st_folium(carte, width=800, height=600)

# Choisir le type de carte à afficher
def choix_carte(data, lat_centre, lon_centre):
    """
    Objectif :
        Afficher une carte parmi les différentes options disponibles (points, cercles)

    Paramètres :
        data : Table filtrée par l'utilisateur (avec colonnes 'latitude', 'longitude', etc.)
        lat_centre : Latitude du centre de la carte
        lon_centre : Longitude du centre de la carte

    Sortie :
        Carte interactive dans Streamlit (cercles ou points)
    """

    # Initialisation de l'état si non défini
    if "affichage_mode" not in st.session_state:
        st.session_state["affichage_mode"] = None

    st.subheader("Afficher la carte des établissements")

    # Boutons dans deux colonnes
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Afficher les points uniquement",key="siren_points"):
            st.session_state["affichage_mode"] = "points"

    with col2:
        if st.button("Afficher les cercles d'influence",key="siren_cercles"):
            st.session_state["affichage_mode"] = "cercles"

    # Vérification des coordonnées
    if lat_centre is None or lon_centre is None:
        st.warning("Veuillez sélectionner une zone pour afficher la carte.")
        return

    # Affichage de la carte selon le mode choisi
    if st.session_state["affichage_mode"] == "points":
        affichage_carte_points(data, lat_centre, lon_centre)

    elif st.session_state["affichage_mode"] == "cercles":
        # Sélection du rayon avec un slider
        affichage_carte_cercles(data, lat_centre, lon_centre)

# =======================
# Section OSM
# =======================

# Rechercher les établissements via open street map
def recherche_etablissements_osm(noms_etablissements, villes, max_etablissements=1000):
    """
    Objectif :
        Recherche des établissements correspondant à un mot-clé dans plusieurs villes
        en utilisant l'API Nominatim d'OpenStreetMap.

    Paramètres :
        nom_etablissements : Liste des établissements choisis par l'utilisateur
        villes : Liste des villes choisies par l'utilisateur
        max_etablissements : Nombre maximum d'établissements à afficher (par défaut 100, limite de 1000 sur l'API)

    Sortie :
        Dataframe avec le nom de l'établissement, l'adresse et les coordonnées géographiques
    """

    # Paramétrage : Pour l'instant uniquement en France
    pays = "France"

    # URL Nominatim OSM
    url = "https://nominatim.openstreetmap.org/search"

    # Définition de l'user agent pour accéder à l'API (obligatoire)
    headers = {"User-Agent": "CATMAP_Data_Marketing"}

    # Initialisaiton
    donnees = []

    # Boucle sur les établissements et sur les villes choisies par l'utilisateur
    for nom in noms_etablissements:
        for ville in villes:
            # Requête
            query = f"{nom}, {ville}, {pays}"

            # Paramétrage
            params = {
                "q": query,
                "format": "json",
                "limit": max_etablissements,
                "addressdetails": 1
            }

            # Lancement de la requête
            response = requests.get(url, params=params, headers=headers)

            # Message si erreur
            if response.status_code != 200:
                st.warning(f"Erreur pour la requête '{query}' : code {response.status_code}")
                continue

            # Récupération du résultat
            resultats = response.json()

            # Contrôle sur le nombre de requêtes
            if len(resultats) >= 1000: # Limite de 1000
                st.warning(f"⚠️ Trop de résultats pour '{query}' (limitée à 1000) — affinez votre recherche.")

            # Traitement des résultats
            for resultat in resultats:
                display = resultat.get("display_name", "")
                lat = float(resultat.get("lat", 0))
                lon = float(resultat.get("lon", 0))

                # Séparation du nom de l'établissement et de l'adresse
                if "," in display:
                    nom_osm, adresse = display.split(",", 1)
                else:
                    nom_osm, adresse = display, ""

                # Mise à jour des données
                donnees.append({
                    "nom_etablissement": nom,
                    "ville": ville,
                    "nom OSM": nom_osm.strip(),
                    "adresse": adresse.strip(),
                    "latitude": lat,
                    "longitude": lon
                })

    # Transformation en data frame
    df = pd.DataFrame(donnees)

    # Dernière vérification
    if df.empty:
        st.info("Aucun établissement trouvé avec les critères fournis.")
    else:
        st.success(f"{len(df)} établissements trouvés.")
        st.dataframe(df)

    return df

# Choix de l'utilisateur pour la recherche OSM
def interface_recherche_osm():
    """
    Objectif :
        Définir l'interface permettant à l'utilisateur de choisir le nom de l'établissement et les villes associées

    Sortie :
        Dataframe avec le nom de l'établissement, l'adresse et les coordonnées géographiques
    """
    # Affichage
    st.subheader("Recherche d'établissements via OpenStreetMap")

    # Nom des établissements à définir par l'utilisateur
    noms_etablissements_osm = st.text_input(
        "Entrez un ou plusieurs noms d'établissements (séparés par des virgules)",
        placeholder="Ex : Carrefour, Lidl, Auchan",
        value=st.session_state.get("noms_etablissements_osm", "")
    )

    # Nom des villes à définir par l'utilisateur
    villes_osm = st.text_input(
        "Entrez une ou plusieurs villes (séparées par des virgules)",
        placeholder="Ex : Paris, Lyon, Marseille",
        value=st.session_state.get("villes_osm", "")
    )

    # Extraction des valeurs nettoyées
    noms_etablissements = [nom.strip() for nom in noms_etablissements_osm.split(",") if nom.strip()]
    villes = [ville.strip() for ville in villes_osm.split(",") if ville.strip()]

    # Bouton de recherche
    if st.button("Lancer la recherche", key="recherche_osm"):
        st.session_state["noms_etablissements_osm"] = noms_etablissements_osm
        st.session_state["villes_osm"] = villes_osm

        if noms_etablissements and villes:
            df_resultats = recherche_etablissements_osm(noms_etablissements, villes)
            if df_resultats is not None and not df_resultats.empty:
                st.session_state["df_etablissements_osm"] = df_resultats
                st.success(f"{len(df_resultats)} établissements trouvés.")
            else:
                st.session_state["df_etablissements_osm"] = None
                st.warning("Aucun établissement trouvé.")
        else:
            st.warning("Veuillez entrer au moins un nom d’établissement et une ville.")

    # Affichage des résultats en session (même après clic bouton)
    return st.session_state.get("df_etablissements_osm", None)


def affichage_carte_points_osm(data, lat_centre, lon_centre):
    """
    Objectif :
        Afficher une carte des points pour la table filtrée dans Streamlit

    Paramètres :
        data : Table filtrée par l'utilisateur
        lat_centre : Latitude centre de la carte
        lon_centre : Longitude centre de la carte

    Sortie :
        Carte interactive des établissements
    """
    if lat_centre is None or lon_centre is None:
        st.warning("Veuillez sélectionner une zone pour afficher la carte.")
        return

    couleurs = [
        'red', 'blue', 'green', 'orange', 'purple', 'darkred', 'cadetblue',
        'darkgreen', 'darkblue', 'pink', 'lightblue', 'lightgreen', 'beige',
        'gray', 'black'
    ]

    etablissements_uniques = data['nom_etablissement'].unique()
    type_to_color = {nom: couleurs[i % len(couleurs)] for i, nom in enumerate(etablissements_uniques)}

    # Création des colonnes : carte + légende
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
                location=[lat, lon],
                radius=7,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.6,
                popup=folium.Popup(popup_info, max_width=300)
            ).add_to(carte)

        st_folium(carte, width=700, height=600)

    with col2:
        st.markdown("#### Légende")  # titre un peu plus petit
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

# Affichage de la carte avec un cercle de rayon R mètres
def affichage_carte_cercles_osm(data, lat_centre, lon_centre):
    """
    Objectif :
        Afficher une carte des établissements avec un cercle d'influence de rayon R

    Paramètres :
        data : Table filtrée par l'utilisateur (avec colonnes 'latitude', 'longitude', etc.)
        lat_centre : Latitude du centre de la carte
        lon_centre : Longitude du centre de la carte

    Sortie :
        Carte interactive des établissements avec cercles
    """
    if lat_centre is None or lon_centre is None:
        st.warning("Veuillez sélectionner une zone pour afficher la carte.")
        return

    couleurs = [
        'red', 'blue', 'green', 'orange', 'purple', 'darkred', 'cadetblue',
        'darkgreen', 'darkblue', 'pink', 'lightblue', 'lightgreen', 'beige',
        'gray', 'black'
    ]

    etablissements_uniques = data['nom_etablissement'].unique()
    type_to_color = {nom: couleurs[i % len(couleurs)] for i, nom in enumerate(etablissements_uniques)}

    rayon_influence = st.slider(
        "Rayon d'influence autour des établissements (en mètres)",
        min_value=50,
        max_value=2000,
        value=200,
        step=50,
        key="slider_osm"
    )

    col1, col2 = st.columns([3, 1])

    with col1:
        carte = folium.Map(location=[lat_centre, lon_centre], zoom_start=12)

        for _, ligne in data.iterrows():
            lat = ligne.get('latitude') or ligne.geometry.y
            lon = ligne.get('longitude') or ligne.geometry.x
            nom = ligne['nom_etablissement']
            color = type_to_color.get(nom, 'red')

            popup_info = f"""
                <b>Nom entreprise :</b> {nom}<br>
                <b>Adresse :</b> {ligne['adresse']}<br>
                <b>Précision géocodage :</b> {ligne['precision_geocodage']}
                """

            folium.Circle(
                location=[lat, lon],
                radius=rayon_influence,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.3
            ).add_to(carte)

            # Cercle plus petit coloré en overlay au centre (remplace Marker)
            folium.CircleMarker(
                location=[lat, lon],
                radius=6,  # plus petit que le cercle d'influence
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.9,
                popup=folium.Popup(popup_info, max_width=300)
            ).add_to(carte)

        st_folium(carte, width=700, height=600)

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

# Choisir le type de carte à afficher
def choix_carte_osm(data, lat_centre, lon_centre):
    """
    Objectif :
        Afficher une carte parmi les différentes options disponibles (points, cercles)

    Paramètres :
        data : Table filtrée par l'utilisateur (avec colonnes 'latitude', 'longitude', etc.)
        lat_centre : Latitude du centre de la carte
        lon_centre : Longitude du centre de la carte

    Sortie :
        Carte interactive dans Streamlit (cercles ou points)
    """

    # Vérification des coordonnées du centre de la carte
    if lat_centre is None or lon_centre is None:
        st.warning("Veuillez sélectionner une zone pour afficher la carte.")
        return

    # Initialisation de l'état si non défini
    if "affichage_mode" not in st.session_state:
        st.session_state["affichage_mode"] = None

    st.subheader("Afficher la carte des établissements")

    # Boutons dans deux colonnes
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Afficher les points uniquement",key="btn_osm_points"):
            st.session_state["affichage_mode"] = "points"

    with col2:
        if st.button("Afficher les cercles d'influence",key="btn_osm_cercles"):
            st.session_state["affichage_mode"] = "cercles"

    # Vérification des coordonnées
    if lat_centre is None or lon_centre is None:
        st.warning("Veuillez sélectionner une zone pour afficher la carte.")
        return

    # Affichage de la carte selon le mode choisi
    if st.session_state["affichage_mode"] == "points":
        affichage_carte_points_osm(data, lat_centre, lon_centre)

    elif st.session_state["affichage_mode"] == "cercles":
        # Sélection du rayon avec un slider
        affichage_carte_cercles_osm(data, lat_centre, lon_centre)