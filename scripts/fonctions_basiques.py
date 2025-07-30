# ==============================================
# 📦 Imports & Librairies
# ==============================================
import pandas as pd
import streamlit as st
import numpy as np
import geopandas as gpd

# ==============================================
# Section chargement des données
# ==============================================

@st.cache_data(show_spinner=False)
def charger_etablissements(path_etablissement):
    """Charge les données des établissements depuis un fichier Parquet."""
    try:
        return pd.read_parquet(path_etablissement)
    except FileNotFoundError:
        st.error(f"Fichier des établissements introuvable : {path_etablissement}")
        return pd.DataFrame()

@st.cache_data(show_spinner=False)
def charger_centres_departements(path_centres_dpt):
    """Charge les données des centres de départements depuis un fichier Excel."""
    try:
        return pd.read_excel(path_centres_dpt)
    except FileNotFoundError:
        st.error(f"Fichier des centres de départements introuvable : {path_centres_dpt}")
        return pd.DataFrame()

@st.cache_data(show_spinner=False)
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

@st.cache_data(show_spinner=False)
def charger_donnees_iris_socio(path_iris_socio):
    """Charge le GeoDataFrame des données IRIS depuis un fichier Parquet."""
    try:
        return gpd.read_parquet(path_iris_socio)
    except FileNotFoundError:
        st.error(f"Fichier de données socio-économiques introuvable au chemin : {path_iris_socio}")
        return None

@st.cache_data(show_spinner=False)
def charger_coefficients_trafic(path_coeff_trafic):
    """Charge la table des coefficients de trafic par ville."""
    try:
        return pd.read_excel(path_coeff_trafic)
    except FileNotFoundError:
        st.warning(f"Fichier des coefficients de trafic introuvable : {path_coeff_trafic}. Le trafic ne sera pas simulé.")
        return pd.DataFrame(columns=['ville', 'coefficient'])

# ==============================================
# Fonctions pour la page INSEE (INCHANGÉES)
# ==============================================

def apercu_donnees(data, nb_lignes):
    st.markdown("<hr style='border:2px solid #ff7f0e;'>", unsafe_allow_html=True)
    st.header("📝 Aperçu des données")
    st.dataframe(data.head(nb_lignes))
    st.write(f"La table INSEE contient {data.shape[0]} lignes et {data.shape[1]} colonnes")

def filtrer_donnees(data):
    st.markdown("## 🎯 Filtrage des données")
    liste_categories = sorted(list(data["Intitules_NAF_VF"].dropna().unique()))
    choix_categories = st.multiselect("Choisissez une ou plusieurs catégorie(s)", liste_categories)
    liste_villes = sorted(list(data["libelleCommuneEtablissement"].dropna().unique()))
    choix_villes = st.multiselect("Choisissez une ou plusieurs ville(s)", liste_villes)
    data_filtree = data[
        (data["Intitules_NAF_VF"].isin(choix_categories))
        & (data["libelleCommuneEtablissement"].isin(choix_villes))
    ].reset_index(drop=True)
    return data_filtree

def choix_centre_departement(data, centres_departements):
    liste_deps = sorted(data["nom_dep"].dropna().unique())
    choix_dep = st.selectbox("Choisissez le département au centre de la carte", liste_deps)
    centre = centres_departements[centres_departements["Departement"] == choix_dep]
    if centre.empty:
        return None, None, None
    lat_centre = centre["Latitude_centre"].iloc[0]
    lon_centre = centre["Longitude_centre"].iloc[0]
    st.success(f"Centré sur {choix_dep} (lat: {lat_centre}, lon: {lon_centre})")
    return choix_dep, lat_centre, lon_centre

# ==============================================
# Fonctions pour la page OSM (OPTIMISÉES)
# ==============================================

def extraction_adresse_OSM(ligne_etab):
    """Extrait une adresse simplifiée et définit une précision de géocodage pour la sortie OSM."""
    adresse_ini = ligne_etab["adresse"].split(", ")
    if adresse_ini[0].isdigit():
        adresse_simp = ", ".join(adresse_ini[:4])
        precision_geocodage = "numero"
    else:
        adresse_simp = ", ".join(adresse_ini[:3])
        precision_geocodage = "voie"
    return pd.Series([adresse_simp, precision_geocodage])

def choix_centre_OSM(data):
    """Laisse à l'utilisateur le choix de la ville pour centrer la carte."""
    centre_ville = data.groupby("ville").first().reset_index()[["ville", "latitude", "longitude"]]
    centre_ville_utilisateur = st.selectbox("Choisissez une ville pour le centre de votre carte", centre_ville["ville"])
    coordonnees_centre = centre_ville[centre_ville["ville"] == centre_ville_utilisateur]
    lon_centre = coordonnees_centre["longitude"].iloc[0]
    lat_centre = coordonnees_centre["latitude"].iloc[0]
    return lat_centre, lon_centre

@st.cache_data(show_spinner=False)
def preparer_donnees_socio(_df_iris_base, _df_communes_france):
    """
    Nettoie, enrichit, simplifie et prépare les données socio-économiques pour
    les 3 niveaux d'analyse. Le résultat est mis en cache pour des performances optimales.
    """
    df = _df_iris_base.copy()
    try:
        df['geometry'] = df['geometry'].simplify(tolerance=100, preserve_topology=True)
    except Exception as e:
        st.warning(f"Avertissement lors de la simplification des géométries : {e}")

    df_ref_deps = _df_communes_france[['Num_Dep', 'Nom_Dep']].drop_duplicates()
    df_ref_deps['Num_Dep'] = df_ref_deps['Num_Dep'].astype(str).str.zfill(2)

    COLS_COMPTAGE = [
        'Nb_menages_total', 'Pop_15_24_ans', 'Pop_25_54_ans', 'Pop_55_79_ans', 'Pop_80_ans_plus',
        'Nb_menages_sans_famille', 'Nb_menages_famille', 'Menages_couple_sans_enfant',
        'Menages_couple_avec_enfant', 'Menages_monoparental', 'Menages_agriculteurs_CS1',
        'Menages_artisans_commercants_CS2', 'Menages_cadres_prof_intelectuelles_CS3',
        'Menages_prof_intermediaires_CS4', 'Menages_employes_CS5', 'Menages_ouvriers_CS6',
        'Menages_retraites_CS7', 'Menages_autres_sans_act_pro_CS8'
    ]
    PROPORTIONS_POPULATION = {
        'Part_jeunes_15_24_ans_pct': 'Pop_15_24_ans', 'Part_actifs_25_54_ans_pct': 'Pop_25_54_ans',
        'Part_seniors_55_79_ans_pct': 'Pop_55_79_ans', 'Part_seniors_80_ans_plus_pct': 'Pop_80_ans_plus'
    }
    PROPORTIONS_MENAGES = {
        'Part_menages_monoparentaux_pct': 'Menages_monoparental',
        'Part_agriculteurs_CS1_pct': 'Menages_agriculteurs_CS1',
        'Part_artisans_commercants_CS2_pct': 'Menages_artisans_commercants_CS2',
        'Part_cadres_CS3_pct': 'Menages_cadres_prof_intelectuelles_CS3',
        'Part_prof_intermediaires_CS4_pct': 'Menages_prof_intermediaires_CS4',
        'Part_employes_CS5_pct': 'Menages_employes_CS5',
        'Part_ouvriers_CS6_pct': 'Menages_ouvriers_CS6', 'Part_retraites_CS7_pct': 'Menages_retraites_CS7',
        'Part_autres_CS8_pct': 'Menages_autres_sans_act_pro_CS8'
    }

    for col in COLS_COMPTAGE:
        if col in df.columns:
            df[col] = df[col].fillna(0).round(0).astype(int)

    df['Population_totale'] = df[['Pop_15_24_ans', 'Pop_25_54_ans', 'Pop_55_79_ans', 'Pop_80_ans_plus']].sum(axis=1)
    pop_total_safe = df['Population_totale'].replace(0, np.nan)
    menages_total_safe = df['Nb_menages_total'].replace(0, np.nan)

    for new_col, source_col in PROPORTIONS_POPULATION.items():
        df[new_col] = (df[source_col] / pop_total_safe * 100)
    for new_col, source_col in PROPORTIONS_MENAGES.items():
        df[new_col] = (df[source_col] / menages_total_safe * 100)

    df['CODE_COM'] = df['IRIS'].str.slice(0, 5)
    df['CODE_DEPT'] = df['IRIS'].str.slice(0, 2)
    df = df.merge(df_ref_deps, left_on='CODE_DEPT', right_on='Num_Dep', how='left')
    df.drop(columns=['Num_Dep'], inplace=True, errors='ignore')

    agg_funcs = {
        'NOM_COM': 'first', 'Nom_Dep': 'first', 'Taux_pauvrete': 'mean', 'Revenu_median': 'mean',
        'Population_totale': 'sum', **{col: 'sum' for col in COLS_COMPTAGE}
    }

    df_commune = df.dissolve(by='CODE_COM', aggfunc=agg_funcs, as_index=False)
    df_commune['CODE_DEPT'] = df_commune['CODE_COM'].str.slice(0, 2)
    df_departement = df_commune.dissolve(by='CODE_DEPT', aggfunc=agg_funcs, as_index=False)
    df_departement['NOM_COM'] = df_departement['Nom_Dep']

    for dframe in [df_commune, df_departement]:
        pop_total_safe = dframe['Population_totale'].replace(0, np.nan)
        menages_total_safe = dframe['Nb_menages_total'].replace(0, np.nan)
        for new_col, source_col in PROPORTIONS_POPULATION.items():
            dframe[new_col] = (dframe[source_col] / pop_total_safe * 100)
        for new_col, source_col in PROPORTIONS_MENAGES.items():
            dframe[new_col] = (dframe[source_col] / menages_total_safe * 100)
        if 'Revenu_median' in dframe.columns: dframe['Revenu_median'] = dframe['Revenu_median'].round(0)
        if 'Taux_pauvrete' in dframe.columns: dframe['Taux_pauvrete'] = dframe['Taux_pauvrete'].round(1)
        proportion_cols = list(PROPORTIONS_POPULATION.keys()) + list(PROPORTIONS_MENAGES.keys())
        for col in proportion_cols:
            if col in dframe.columns: dframe[col] = dframe[col].round(1)

    return {"IRIS": df, "Commune": df_commune, "Département": df_departement}