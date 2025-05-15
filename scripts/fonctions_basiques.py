# Librairies
import pandas as pd
import streamlit as st


# Chargement des données
def chargement_donnees(path_etablissement, path_centres_dpt):
    """
    Objectif :
        Charger les données établissements et centres de département

    Paramètres :
        path_etablissement : Chemin du fichier d'établissements
        path_centres_dpt : Chemin du fichier de centres de départements

    Sortie :
        etablissements, centres_departements : Fichiers chargés
    """

    # Chargement
    etablissements = pd.read_parquet(path_etablissement)
    centres_departements = pd.read_excel(path_centres_dpt)

    # Sortie
    return etablissements, centres_departements


# Aperçu des données
def apercu_donnees(data, nb_lignes):
    """
    Objectif :
        Charger un aperçu des données

    Paramètres :
        data : Fichier d'établissements
        nb_lignes : Nombre de lignes à afficher

    Sortie :
        Aperçu du fichier
    """

    st.markdown("<hr style='border:2px solid #ff7f0e;'>", unsafe_allow_html=True)
    st.header("📝 Aperçu des données")
    st.dataframe(data.head(nb_lignes))
    st.write(f"La table INSEE contient {data.shape[0]} lignes et {data.shape[1]} colonnes")


def filtrer_donnees(data):
    """
    Objectif :
        Filtrer les données en fonction de la catégorie d'établissemnt et de la ville

    Paramètres :
        data : Fichier établissements

    Sortie :
        data_filtree : Fichier établissements filtré sur les catégories d'établissements et sur les villes
    """

    st.markdown("## 🎯 Filtrage des données")

    liste_categories = sorted(list(data["Intitules_NAF_VF"].dropna().unique()))
    choix_categories = st.multiselect(
        "Choisissez une ou plusieurs catégorie(s)", liste_categories
    )

    liste_villes = sorted(list(data["libelleCommuneEtablissement"].dropna().unique()))
    choix_villes = st.multiselect("Choisissez une ou plusieurs ville(s)", liste_villes)

    # Filtre des données
    data_filtree = data[
        (data["Intitules_NAF_VF"].isin(choix_categories))
        & (data["libelleCommuneEtablissement"].isin(choix_villes))
    ].reset_index(drop=True)

    # Sortie
    return data_filtree


def choix_centre_departement(data, centres_departements):
    """
    Objectif :
        Centré la carte sur un département

    Paramètres :
        data : Fichier établissements
        centres_departements : Fichier des départements avec leur centre associé

    Sortie :
        choix_dep : Département retenu par l'utilisateur
        lat_centre : Latitude centrale du département retenu par l'utilisateur
        lon_centre : Longitude centrale du département retenu par l'utilisateur
    """

    # Choix du département parmi la liste
    liste_deps = sorted(data["nom_dep"].dropna().unique())
    choix_dep = st.selectbox(
        "Choisissez le département au centre de la carte", liste_deps
    )

    # Filtre sur le choix du département
    centre = centres_departements[centres_departements["Departement"] == choix_dep]

    # Vérification que le filtre a renvoyé des résultats
    if centre.empty:
        #st.error(f"Aucun centre trouvé pour le département {choix_dep}. Veuillez vérifier les données.")
        return None, None, None  # Retourner None pour éviter l'erreur

    # Extraction longitude et latitude
    lat_centre = centre["Latitude_centre"].iloc[0]
    lon_centre = centre["Longitude_centre"].iloc[0]

    # Affichage
    st.success(f"Centré sur {choix_dep} (lat: {lat_centre}, lon: {lon_centre})")

    # Sortie
    return choix_dep, lat_centre, lon_centre

# Extraire l'adresse et ajouter la précision de géocodage de la sortie API OSM
def extraction_adresse_OSM(ligne_etab):
    """
    Objectif :
        Extraire une adresse simplifiée et définir une précision de géocodage pour la sortie OSM

    Paramètres :
        ligne_etab : Une ligne du fichier

    Sortie :
        adresse_simplifiee : Nouvelle colonne contenant les adresses simplifiées
        precision_geocodage : Précision géocodage (numéro ou voie)
    """

    # Séparation de l'adresse par ,
    adresse_ini = ligne_etab["adresse"].split(", ")

    # Extraction de l'adresse simplifiée (3 premières caractères si pas de numéro, 4 sinon)
    if adresse_ini[0].isdigit():
        adresse_simp = ", ".join(adresse_ini[:4])
        precision_geocodage = "numero"
    else:
        adresse_simp = ", ".join(adresse_ini[:3])
        precision_geocodage = "voie"

    return pd.Series([adresse_simp,precision_geocodage])

# Choix du centre de département sur la sortie OSM
def choix_centre_OSM(data):
    """
    Objectif :
        Laisser à l'utilisateur de choisir le centre de la carte après sortie OSM

    Paramètres :
        data : Sortie dataframe OSM

    Sortie :
        lat_centre : Latitude centrale du département retenu par l'utilisateur
        lon_centre : Longitude centrale du département retenu par l'utilisateur
    """

    # Transformation du dataframe et conservation de la première ligne comme centre de carte potentiel
    centre_ville = data.groupby("ville").first().reset_index()[["ville", "latitude", "longitude"]]

    # Selectionner une ville parmi la liste
    centre_ville_utilisateur = st.selectbox("Choisissez une ville pour le centre de votre carte", centre_ville["ville"])

    # Recherche des coordonnées associées
    coordonnees_centre = centre_ville[centre_ville["ville"] == centre_ville_utilisateur]

    # Extraction de la longitude et latitude
    lon_centre = coordonnees_centre["longitude"].iloc[0]
    lat_centre = coordonnees_centre["latitude"].iloc[0]

    return lat_centre, lon_centre