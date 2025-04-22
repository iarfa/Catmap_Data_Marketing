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
