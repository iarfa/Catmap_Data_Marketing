# 📌 Projet d'API Streamlit pour Cartographie Interactive

## 🚀 Objectif du Projet
Développement d'une API avec **Streamlit** permettant l'affichage d'informations sur une **carte interactive** à partir de données issues de la base **SIREN** et d'autres sources **opendata**.

## 🎯 Fonctionnalités Principales
L'application offre trois types d'affichage sur la carte interactive :
1. **Points** : Affichage simple des entreprises.
2. **Points avec cercles de rayon R** : Affichage avec une zone de couverture définie autour des points.
3. **Isochrones** : Calcul des zones accessibles en fonction d'un temps ou d'une distance.

## 🔎 Modes de Recherche
L'utilisateur peut obtenir des résultats de trois manières différentes :
1. **Saisie d'une adresse** :
   - Conversion de l'adresse en coordonnées (x, y).
   - Sélection d'un secteur (villes concernées).
   - Affichage des entreprises selon les options ci-dessus.
2. **Sélection d'un secteur et d'une zone géographique** :
   - Définition manuelle d'un secteur.
   - Affichage des entreprises.
3. **Recherche par nom d'entreprise** :
   - Utilisation d'une API externe pour récupérer les coordonnées de l'entreprise.
   - Affichage des entreprises correspondantes.

## 📍 Technologies Utilisées
- **Langage** : Python 🐍
- **Framework UI** : Streamlit 🎨
- **Cartographie** : Folium 🗺️
- **Données routières** : OSMnx (graphes OSM) 🚗
- **Calcul d’isochrones** : OpenRouteService (ORS) avec une alternative en développement ⏳
- **Base de données** : En cours d’étude (PostgreSQL/PostGIS, SQLite, Parquet...)
- **Enrichissement des données** : Sources opendata 📊

## ⚠️ Problèmes Actuels
1. **Performance des isochrones** :
   - L’utilisation d’OSMnx pour charger les graphes routiers par département fonctionne mais ralentit le traitement avec un grand nombre de points.
   - Une alternative est en cours de développement pour optimiser les calculs.
2. **Stockage des données** :
   - Actuellement, les données sont envisagées en local.
   - Recherche d’une solution optimale (PostgreSQL/PostGIS, SQLite, fichiers Parquet...).
3. **Affichage d’un grand nombre de points** :
   - Folium peut être limité pour afficher trop de points simultanément.
   - Étude d’alternatives comme le clustering ou l'utilisation d'autres bibliothèques (Kepler.gl via Pydeck).

## 🛠️ Prochaines Étapes
- [ ] Définir la structure du projet.
- [ ] Choisir le mode de stockage des données.
- [ ] Optimiser le calcul des isochrones.
- [ ] Améliorer l’affichage de la carte pour les grands ensembles de données.
- [ ] Mettre en place une première version fonctionnelle.
- [ ] Ajouter des données opendata (stage à venir)

---
💡 **Objectif final** : Fournir une API fluide et performante pour la visualisation de données entreprises sur une carte interactive, avec un calcul optimisé des zones de couverture.

