# Librairies
import streamlit as st
import pandas as pd
from page_insee import page_insee
from fonctions_cartographie import recherche_etablissements_osm

# Personnalisation de la page
def personnalisation_page():
    """
    Objectif :
        Personnaliser la page, les couleurs sont personnalisables ici : https://htmlcolorcodes.com/fr/
    """

    st.markdown(
        """
        <style>
            .title {
                color: #1f77b4;
                font-size: 40px;
                font-weight: bold; # Gras
            }
            .header {
                color: #ff7f0e;
                font-size: 30px;
                font-weight: bold;
            }
            .subheader {
                color: #2ca02c;
                font-size: 20px;
            }
            .footer {
                color: #1f77b4;
                font-size: 18px;
            }
        </style>
    """,
        unsafe_allow_html=True,
    )  # Permet d'afficher du html et CSS

# Affichage titre
def affichage_titre():
    """
    Objectif :
        Afficher le titre et la description
    """

    # Titre
    st.title("🌍 API étude sectorielle et concurrentielle Data Marketing")

    # Description
    st.markdown(
        '<p class="footer">Explorez les données, analysez les tendances du marché, et optimisez vos stratégies commerciales.</p>',
        unsafe_allow_html=True,
    )
    st.write("Bienvenue dans l'outil de Data Marketing. Choisissez une page dans le menu à gauche pour commencer.")

# Navigation entre les différentes pages
def navigation():
    """
    Objectif :
        Afficher un sélecteur pour naviguer entre les pages.
    """

    with st.sidebar:
        st.markdown("## 🧭 Navigation")
        page_selectionnee = st.radio(
            label="Choisissez une page :",
            options=["🏠 Accueil", "📊 Données INSEE", "🗺️ Données OSM"],
            index=0
        )

    if "Accueil" in page_selectionnee:
        return "accueil"
    elif "INSEE" in page_selectionnee:
        return "insee"
    elif "OSM" in page_selectionnee:
        return "osm"

# Carte des points OSM
def interface_recherche_osm(df_geo):
    """
    Affiche une interface complète et dynamique pour la recherche d'établissements OSM.

    Cette fonction gère la saisie des enseignes, la sélection géographique hiérarchique
    (Région, Département, Commune), lance la recherche et stocke les résultats
    dans l'état de la session Streamlit.

    Args:
        df_geo (pd.DataFrame): Un DataFrame contenant les données géographiques
                               avec les colonnes 'Nom_Region', 'Nom_Dep', 'Num_Dep', 'Nom_Ville'.

    Returns:
        pd.DataFrame: Le DataFrame des résultats de la recherche, potentiellement vide.
    """
    st.subheader("Recherche d'établissements via OpenStreetMap")

    # === Sécurité : Vérifier si les données géographiques sont chargées ===
    if df_geo is None or df_geo.empty:
        st.error(
            "Les données géographiques de référence (communes, départements...) n'ont pas pu être chargées. Le module de recherche est indisponible.")
        return pd.DataFrame()

    # =================================================================
    # ## 1. Saisie des noms d'établissements
    # =================================================================
    noms_etablissements_osm = st.text_input(
        "1️⃣ Entrez un ou plusieurs noms d'établissements (séparés par des virgules)",
        placeholder="Ex: Carrefour, Lidl, Auchan",
        value=st.session_state.get("noms_etablissements_osm", ""),
        help="Vous pouvez rechercher plusieurs enseignes en même temps."
    )
    noms_etablissements = [nom.strip() for nom in noms_etablissements_osm.split(",") if nom.strip()]

    # =================================================================
    # ## 2. Sélection de la zone géographique
    # =================================================================
    st.markdown("2️⃣ Choisissez la zone de recherche")

    maille_recherche = st.radio(
        "Choisir la maille :",
        ('Région', 'Département', 'Commune'),
        horizontal=True,
        key="maille_osm"
    )

    selection_geo = []  # Cette liste contiendra les noms de Régions, Départements ou Communes

    # --- Logique d'affichage dynamique des sélecteurs ---

    if maille_recherche == 'Région':
        regions_disponibles = sorted(df_geo['Nom_Region'].unique())
        selection_geo = st.multiselect("Choisissez une ou plusieurs régions", regions_disponibles,
                                       key="selection_region_osm")

    elif maille_recherche == 'Département':

        # Convertir la colonne en string pour un tri sans erreur
        df_geo['Num_Dep'] = df_geo['Num_Dep'].astype(str)

        # Crée un DataFrame unique des départements, trié par numéro
        df_deps = df_geo[['Num_Dep', 'Nom_Dep']].drop_duplicates().sort_values('Num_Dep')

        # Crée les étiquettes formatées "Numéro - Nom" pour l'affichage
        df_deps['label'] = df_deps['Num_Dep'].astype(str).str.zfill(2) + " - " + df_deps['Nom_Dep']
        options_deps = df_deps['label'].tolist()

        # Affiche le sélecteur avec les étiquettes triées
        selection_labels = st.multiselect("Choisissez un ou plusieurs départements", options_deps,
                                          key="selection_dep_osm")

        # Traduit les étiquettes sélectionnées (ex: "01 - Ain") en vrais noms (ex: "Ain") pour le filtrage
        selection_geo = df_deps[df_deps['label'].isin(selection_labels)]['Nom_Dep'].tolist()

    elif maille_recherche == 'Commune':
        # Pour les communes, on filtre d'abord par département pour une meilleure UX
        st.info("Pour trouver une commune, veuillez d'abord sélectionner son département.")

        df_deps = df_geo[['Num_Dep', 'Nom_Dep']].drop_duplicates().sort_values('Num_Dep')
        df_deps['label'] = df_deps['Num_Dep'].astype(str).str.zfill(2) + " - " + df_deps['Nom_Dep']
        options_deps = df_deps['label'].tolist()

        dep_pour_communes_labels = st.multiselect("D'abord, sélectionnez le(s) département(s)", options_deps,
                                                  key="dep_pour_commune_osm")

        if dep_pour_communes_labels:
            # Traduit les labels en noms de départements
            deps_selectionnes = df_deps[df_deps['label'].isin(dep_pour_communes_labels)]['Nom_Dep'].tolist()

            # Filtre les communes sur la base des départements choisis
            communes_disponibles = sorted(df_geo[df_geo['Nom_Dep'].isin(deps_selectionnes)]['Nom_Ville'].unique())
            selection_geo = st.multiselect("Puis, choisissez une ou plusieurs communes", communes_disponibles,
                                           key="selection_commune_osm")

    # =================================================================
    # ## 3. Bouton de recherche et exécution
    # =================================================================
    if st.button("Lancer la recherche", key="recherche_osm_nouveau", type="primary"):
        # Sauvegarde de l'input utilisateur
        st.session_state["noms_etablissements_osm"] = noms_etablissements_osm

        villes_a_chercher = []
        if selection_geo:
            if maille_recherche == 'Région':
                villes_a_chercher = df_geo[df_geo['Nom_Region'].isin(selection_geo)]['Nom_Ville'].tolist()
            elif maille_recherche == 'Département':
                villes_a_chercher = df_geo[df_geo['Nom_Dep'].isin(selection_geo)]['Nom_Ville'].tolist()
            elif maille_recherche == 'Commune':
                villes_a_chercher = selection_geo  # C'est déjà la liste des communes

        # Lancement de la requête API seulement si les inputs sont valides
        if noms_etablissements and villes_a_chercher:
            with st.spinner(
                    f"Recherche de '{', '.join(noms_etablissements)}' sur {len(villes_a_chercher)} commune(s)..."):
                df_resultats = recherche_etablissements_osm(noms_etablissements, villes_a_chercher)

            # Stockage des résultats dans la session
            st.session_state["df_etablissements_osm"] = df_resultats if df_resultats is not None else pd.DataFrame()
        else:
            st.warning("Veuillez entrer au moins un nom d’établissement ET sélectionner une zone géographique.")
            # On vide les résultats si la recherche est invalide
            st.session_state["df_etablissements_osm"] = pd.DataFrame()

    # =================================================================
    # ## 4. Valeur de retour
    # =================================================================
    # La fonction retourne toujours l'état actuel des résultats stockés en session
    return st.session_state.get("df_etablissements_osm", pd.DataFrame())

# Dictionnaire de configuration centralisé et exhaustif pour tous les indicateurs
INDICATEURS_CONFIG = {
    # --- Indicateurs Clés (une seule vue) ---
    "revenu_median": {
        "display": "Revenu médian (€)",
        "raw": "Revenu_median",
        "pct": None
    },
    "taux_pauvrete": {
        "display": "Taux de pauvreté (%)",
        "raw": "Taux_pauvrete",
        "pct": None
    },

    # --- Démographie (double vue : brut + %) ---
    "population_totale": {
        "display": "Population totale",
        "raw": "Population_totale",
        "pct": None  # Pas de sens d'avoir un % de la population totale
    },
    "pop_15_24": {
        "display": "Population 15-24 ans",
        "raw": "Pop_15_24_ans",
        "pct": "Part_jeunes_15_24_ans_pct"
    },
    "pop_25_54": {
        "display": "Population 25-54 ans",
        "raw": "Pop_25_54_ans",
        "pct": "Part_actifs_25_54_ans_pct"
    },
    "pop_55_79": {
        "display": "Population 55-79 ans",
        "raw": "Pop_55_79_ans",
        "pct": "Part_seniors_55_79_ans_pct"
    },
    "pop_80_plus": {
        "display": "Population 80 ans et plus",
        "raw": "Pop_80_ans_plus",
        "pct": "Part_seniors_80_ans_plus_pct"
    },

    # --- Ménages (double vue : brut + %) ---
    "menages_total": {
        "display": "Nombre total de ménages",
        "raw": "Nb_menages_total",
        "pct": None
    },
    "menages_monoparentaux": {
        "display": "Ménages monoparentaux",
        "raw": "Menages_monoparental",
        "pct": "Part_menages_monoparentaux_pct"
    },

    # --- CSP (double vue : brut + %) ---
    "agriculteurs": {
        "display": "Ménages - Agriculteurs (CSP1)",
        "raw": "Menages_agriculteurs_CS1",
        "pct": "Part_agriculteurs_CS1_pct"
    },
    "artisans": {
        "display": "Ménages - Artisans, commerçants (CSP2)",
        "raw": "Menages_artisans_commercants_CS2",
        "pct": "Part_artisans_commercants_CS2_pct"
    },
    "cadres": {
        "display": "Ménages - Cadres (CSP3)",
        "raw": "Menages_cadres_prof_intelectuelles_CS3",
        "pct": "Part_cadres_CS3_pct"
    },
    "prof_intermediaires": {
        "display": "Ménages - Prof. intermédiaires (CSP4)",
        "raw": "Menages_prof_intermediaires_CS4",
        "pct": "Part_prof_intermediaires_CS4_pct"
    },
    "employes": {
        "display": "Ménages - Employés (CSP5)",
        "raw": "Menages_employes_CS5",
        "pct": "Part_employes_CS5_pct"
    },
    "ouvriers": {
        "display": "Ménages - Ouvriers (CSP6)",
        "raw": "Menages_ouvriers_CS6",
        "pct": "Part_ouvriers_CS6_pct"
    },
    "retraites": {
        "display": "Ménages - Retraités (CSP7)",
        "raw": "Menages_retraites_CS7",
        "pct": "Part_retraites_CS7_pct"
    },
    "autres": {
        "display": "Ménages - Autres sans act. pro. (CSP8)",
        "raw": "Menages_autres_sans_act_pro_CS8",
        "pct": "Part_autres_CS8_pct"
    }
}

# Interface de sélection socio
def interface_recherche_osm(df_geo):
    """
    Affiche l'interface de recherche d'établissements OSM avec un tri corrigé.
    """
    st.subheader("1. Recherche d'établissements")
    noms_etablissements_osm = st.text_input(
        "Noms d'établissements (séparés par des virgules)",
        placeholder="Ex: Carrefour, Lidl",
        value=st.session_state.get("noms_etablissements_osm", "")
    )
    noms_etablissements = [nom.strip() for nom in noms_etablissements_osm.split(",") if nom.strip()]

    st.markdown("Zone de recherche")
    maille_recherche = st.radio(
        "Choisir la maille :", ('Région', 'Département', 'Commune'),
        horizontal=True, key="maille_osm"
    )
    selection_geo = []

    if maille_recherche == 'Région':
        regions_disponibles = sorted(df_geo['Nom_Region'].unique())
        selection_geo = st.multiselect("Choisissez une ou plusieurs régions", regions_disponibles)

    elif maille_recherche == 'Département':
        df_deps = df_geo[['Num_Dep', 'Nom_Dep']].drop_duplicates().sort_values('Num_Dep')
        df_deps['label'] = df_deps['Num_Dep'].astype(str).str.zfill(2) + " - " + df_deps['Nom_Dep']
        options_deps = df_deps['label'].tolist()
        selection_labels = st.multiselect("Choisissez un ou plusieurs départements", options_deps)
        selection_geo = df_deps[df_deps['label'].isin(selection_labels)]['Nom_Dep'].tolist()

    elif maille_recherche == 'Commune':
        df_deps = df_geo[['Num_Dep', 'Nom_Dep']].drop_duplicates().sort_values('Num_Dep')
        df_deps['label'] = df_deps['Num_Dep'].astype(str).str.zfill(2) + " - " + df_deps['Nom_Dep']
        options_deps = df_deps['label'].tolist()
        dep_pour_communes_labels = st.multiselect("D'abord, sélectionnez un ou plusieurs départements", options_deps)
        if dep_pour_communes_labels:
            deps_selectionnes = df_deps[df_deps['label'].isin(dep_pour_communes_labels)]['Nom_Dep'].tolist()
            communes_disponibles = sorted(df_geo[df_geo['Nom_Dep'].isin(deps_selectionnes)]['Nom_Ville'].unique())
            selection_geo = st.multiselect("Puis, choisissez une ou plusieurs communes", communes_disponibles)

    if st.button("Lancer la recherche", key="recherche_osm_nouveau", type="primary"):
        st.session_state["noms_etablissements_osm"] = noms_etablissements_osm
        villes_a_chercher = []
        if selection_geo:
            if maille_recherche == 'Région':
                villes_a_chercher = df_geo[df_geo['Nom_Region'].isin(selection_geo)]['Nom_Ville'].tolist()
            elif maille_recherche == 'Département':
                villes_a_chercher = df_geo[df_geo['Nom_Dep'].isin(selection_geo)]['Nom_Ville'].tolist()
            elif maille_recherche == 'Commune':
                villes_a_chercher = selection_geo
        if noms_etablissements and villes_a_chercher:
            with st.spinner(f"Recherche en cours..."):
                df_resultats = recherche_etablissements_osm(noms_etablissements, villes_a_chercher)
            st.session_state["df_etablissements_osm"] = df_resultats if df_resultats is not None else pd.DataFrame()
        else:
            st.warning("Veuillez entrer un nom d’établissement ET sélectionner une zone.")

    return st.session_state.get("df_etablissements_osm", pd.DataFrame())


def interface_selection_socio(dict_geodatas):
    """
    Affiche l'interface de sélection socio-économique dans la sidebar
    et retourne les données déjà filtrées par département.
    """
    gdf_socio_filtre, colonne_a_afficher, nom_indicateur_final, maille_choisie = None, None, None, None

    st.sidebar.subheader("📊 Analyse du Territoire")
    if st.sidebar.toggle("Enrichir avec des données de territoire"):

        nom_affiche_choisi = st.sidebar.selectbox("Choisissez un indicateur :",
                                                  [v['display'] for v in INDICATEURS_CONFIG.values()])
        config_choisie = next(c for c in INDICATEURS_CONFIG.values() if c['display'] == nom_affiche_choisi)
        colonne_a_afficher, nom_indicateur_final = config_choisie['raw'], config_choisie['display']

        if config_choisie['pct'] is not None:
            type_affichage = st.sidebar.radio("Afficher en :", ("Valeur absolue", "Pourcentage (%)"), horizontal=True)
            if type_affichage == "Pourcentage (%)":
                colonne_a_afficher, nom_indicateur_final = config_choisie['pct'], f"{config_choisie['display']} (%)"

        maille_disponible = ['Commune', 'Département'] if colonne_a_afficher in ['Revenu_median',
                                                                                 'Taux_pauvrete'] else ['IRIS',
                                                                                                        'Commune',
                                                                                                        'Département']
        index_defaut = 0 if len(maille_disponible) == 2 else 1
        maille_choisie = st.sidebar.radio("Niveau d'analyse :", maille_disponible, index=index_defaut, horizontal=True)

        gdf_a_afficher = dict_geodatas[maille_choisie]

        df_deps = dict_geodatas['Département']
        if 'label' not in df_deps.columns:
            df_deps['label'] = df_deps['CODE_DEPT'] + ' - ' + df_deps['NOM_COM']

        deps_selectionnes = st.sidebar.multiselect("Filtrer sur un ou plusieurs départements :",
                                                   options=df_deps['label'])

        if deps_selectionnes:
            codes_deps = [d.split(' - ')[0] for d in deps_selectionnes]
            gdf_socio_filtre = gdf_a_afficher[gdf_a_afficher['CODE_DEPT'].isin(codes_deps)]
        else:
            st.sidebar.info("Sélectionnez au moins un département pour afficher les données sur la carte.")

    return gdf_socio_filtre, colonne_a_afficher, nom_indicateur_final, maille_choisie
