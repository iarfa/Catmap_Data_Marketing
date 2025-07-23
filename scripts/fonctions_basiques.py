# ==============================================
# 📦 Imports & Librairies
# ==============================================
import pandas as pd
import streamlit as st
import numpy as np

# ==============================================
# Section chargement des données
# ==============================================

@st.cache_data
def charger_etablissements(path_etablissement):
    """Charge les données des établissements depuis un fichier Parquet."""
    try:
        return pd.read_parquet(path_etablissement)
    except FileNotFoundError:
        st.error(f"Fichier des établissements introuvable : {path_etablissement}")
        return pd.DataFrame() # Retourne un dataframe vide en cas d'erreur

@st.cache_data
def charger_centres_departements(path_centres_dpt):
    """Charge les données des centres de départements depuis un fichier Excel."""
    try:
        return pd.read_excel(path_centres_dpt)
    except FileNotFoundError:
        st.error(f"Fichier des centres de départements introuvable : {path_centres_dpt}")
        return pd.DataFrame() # Retourne un dataframe vide en cas d'erreur

@st.cache_data
def charger_communes(path_communes):
    """Charge les données des communes depuis un fichier Excel."""
    try:
        df = pd.read_excel(path_communes)

        if 'Num_Dep' in df.columns:
            df['Num_Dep'] = df['Num_Dep'].astype(str)
        else:
            st.error("La colonne 'Num_Dep' est manquante dans le fichier des communes.")
            return pd.DataFrame()

        return df
    except FileNotFoundError:
        st.error(f"Fichier des communes introuvable : {path_communes}")
        return pd.DataFrame()

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

# Filtre des données (INSEE)
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

# Choix du centre département
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

# Préparation des données socio-économiques
def preparer_donnees_socio(df_iris_base):
    """
    Nettoie, enrichit (avec des proportions claires) et prépare les données socio-économiques
    pour les 3 niveaux d'analyse : IRIS, Commune, et Département.
    """
    df = df_iris_base.copy()

    # =================================================================
    # Étape 1 : Configuration centralisée des colonnes
    # =================================================================
    # Si vous ajoutez une colonne, vous n'aurez qu'à la modifier ici.

    COLS_COMPTAGE = [
        'Nb_menages_total', 'Pop_15_24_ans', 'Pop_25_54_ans', 'Pop_55_79_ans', 'Pop_80_ans_plus',
        'Nb_menages_sans_famille', 'Nb_menages_famille', 'Menages_couple_sans_enfant',
        'Menages_couple_avec_enfant', 'Menages_monoparental', 'Menages_agriculteurs_CS1',
        'Menages_artisans_commercants_CS2', 'Menages_cadres_prof_intelectuelles_CS3',
        'Menages_prof_intermediaires_CS4', 'Menages_employes_CS5', 'Menages_ouvriers_CS6',
        'Menages_retraites_CS7', 'Menages_autres_sans_act_pro_CS8'
    ]

    # Dictionnaires pour générer les proportions dynamiquement
    PROPORTIONS_POPULATION = {
        'Part_jeunes_15_24_ans_pct': 'Pop_15_24_ans',
        'Part_actifs_25_54_ans_pct': 'Pop_25_54_ans',
        'Part_seniors_55_79_ans_pct': 'Pop_55_79_ans',  # Nom plus clair que "actifs"
        'Part_seniors_80_ans_plus_pct': 'Pop_80_ans_plus'
    }

    PROPORTIONS_MENAGES = {
        'Part_menages_monoparentaux_pct': 'Menages_monoparental',
        'Part_agriculteurs_CS1_pct': 'Menages_agriculteurs_CS1',
        'Part_artisans_commercants_CS2_pct': 'Menages_artisans_commercants_CS2',
        'Part_cadres_CS3_pct': 'Menages_cadres_prof_intelectuelles_CS3',
        'Part_prof_intermediaires_CS4_pct': 'Menages_prof_intermediaires_CS4',
        'Part_employes_CS5_pct': 'Menages_employes_CS5',
        'Part_ouvriers_CS6_pct': 'Menages_ouvriers_CS6',
        'Part_retraites_CS7_pct': 'Menages_retraites_CS7',
        'Part_autres_CS8_pct': 'Menages_autres_sans_act_pro_CS8'
    }

    # =================================================================
    # Étape 2 : Nettoyage et Ingénierie de variables (dynamique)
    # =================================================================
    for col in COLS_COMPTAGE:
        if col in df.columns:
            df[col] = df[col].fillna(0).round(0).astype(int)

    df['Population_totale'] = df[list(PROPORTIONS_POPULATION.values())].sum(axis=1)
    pop_total_safe = df['Population_totale'].replace(0, np.nan)
    menages_total_safe = df['Nb_menages_total'].replace(0, np.nan)

    for new_col, source_col in PROPORTIONS_POPULATION.items():
        df[new_col] = (df[source_col] / pop_total_safe * 100).fillna(0)

    for new_col, source_col in PROPORTIONS_MENAGES.items():
        df[new_col] = (df[source_col] / menages_total_safe * 100).fillna(0)

    # =================================================================
    # Étape 3 : Agrégation aux mailles Commune et Département
    # =================================================================
    df['CODE_COM'] = df['IRIS'].str.slice(0, 5)
    df['CODE_DEPT'] = df['IRIS'].str.slice(0, 2)

    agg_funcs = {
        'NOM_COM': 'first', 'Taux_pauvrete': 'mean', 'Revenu_median': 'mean',
        'Population_totale': 'sum',
        **{col: 'sum' for col in COLS_COMPTAGE}
    }

    df_commune = df.dissolve(by='CODE_COM', aggfunc=agg_funcs, as_index=False)
    df_commune['CODE_DEPT'] = df_commune['CODE_COM'].str.slice(0, 2)
    df_departement = df_commune.dissolve(by='CODE_DEPT', aggfunc=agg_funcs, as_index=False)

    # =================================================================
    # Étape 4 : Recalcul des proportions pour les mailles agrégées
    # =================================================================
    for dframe in [df_commune, df_departement]:
        pop_total_safe = dframe['Population_totale'].replace(0, np.nan)
        menages_total_safe = dframe['Nb_menages_total'].replace(0, np.nan)

        for new_col, source_col in PROPORTIONS_POPULATION.items():
            dframe[new_col] = (dframe[source_col] / pop_total_safe * 100).fillna(0)

        for new_col, source_col in PROPORTIONS_MENAGES.items():
            dframe[new_col] = (dframe[source_col] / menages_total_safe * 100).fillna(0)

    return {
        "IRIS": df,
        "Commune": df_commune,
        "Département": df_departement
    }
