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
    st.write(f"Votre table contient {data.shape[0]} lignes et {data.shape[1]} colonnes")


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