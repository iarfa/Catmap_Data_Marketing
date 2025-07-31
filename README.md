🗺️ API d'Analyse Géospatiale et Concurrentielle
🚀 Objectif du Projet
Développer une application web d'aide à la décision pour les entreprises disposant de réseaux physiques (commerces, agences). L'outil remplace les analyses basées sur l'intuition par une approche pilotée par la donnée géospatiale, permettant d'effectuer des études concurrentielles et des diagnostics de territoire précis.

🎯 Fonctionnalités Clés
L'application est construite autour de plusieurs modules d'analyse interactifs :

Recherche de Concurrents : Recherche multi-enseignes via OpenStreetMap sur des zones géographiques définies (Région, Département, Commune).

Visualisation Multi-Modes : Chaque concurrent peut être visualisé de trois manières sur la carte :

Points simples : Localisation précise.

Cercles d'influence : Zone de chalandise simple (rayon en mètres).

Isochrones : Zone de chalandise réelle (temps de trajet en voiture), calculée via une instance OpenRouteService et ajustée par un coefficient de trafic pour simuler les conditions réelles.

Analyse Socio-Économique : Superposition d'une couche de données choroplèthe pour analyser le contexte local. L'analyse est multi-échelles (IRIS, Commune, Département) et multi-indicateurs (revenus, démographie, CSP, etc.).

Enrichissement par Points d'Intérêt (POI) : Affichage des générateurs de flux (gares, écoles, hôpitaux...) autour des zones d'étude pour qualifier l'environnement commercial.

🛠️ Stack Technique
Langage : Python 🐍

Framework UI : Streamlit 🎨

Analyse de Données : Pandas, GeoPandas, NumPy

Cartographie Interactive : Folium & streamlit-folium 🗺️

Moteur d'Isochrones : Instance OpenRouteService auto-hébergée sur Docker 🐳

Requêtes API : requests (pour interroger les API OpenStreetMap).

📂 Sources de Données (Open Data)
Concurrents & POI : OpenStreetMap (via les API Nominatim et Overpass).

Données Socio-Démographiques : Fichiers des carreaux IRIS de l'INSEE.

Fonds de carte & Géométries : IGN (via le fichier des communes de France).

Simulation de trafic : Coefficients de temps de trajet basés sur les données des grandes agglomérations.

🏗️ Architecture du Code
Le projet est structuré en modules avec des responsabilités claires pour faciliter la maintenance et l'évolutivité :

main.py : Point d'entrée de l'application et gestionnaire de la navigation.

page_osm.py : Script principal de la page d'analyse, orchestrant les appels aux modules.

fonctions_basiques.py : Fonctions de chargement et de préparation des données (sans interface).

fonctions_cartographie.py : Fonctions de création de la carte et d'interaction avec les API géospatiales (ORS, Overpass).

interface.py : Fonctions construisant les composants UI avec Streamlit (sidebar, sélecteurs...).

config.py : Fichier central pour les dictionnaires et variables de configuration (ex: POI).
