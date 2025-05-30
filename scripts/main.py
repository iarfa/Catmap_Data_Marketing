# =======================
# 📦 Imports & Librairies
# =======================
from interface import personnalisation_page, navigation
from page_insee import page_insee
from page_osm import page_osm
from page_acceuil import page_accueil

# =======================
# 📁 Chemins des fichiers
# =======================
path_etablissement = (
    "../data/Fichier_final_etablissements_commerces_alimentaire_non_alimentaire.parquet"
)
path_centres_departements = "../data/Centres_departements.xlsx"

# =======================
# 🎨 Personnalisation de la page
# =======================
personnalisation_page()

# ===================
# 🚀 Navigation
# ===================
page = navigation()

if page == "accueil":
    page_accueil()
elif page == "insee":
    page_insee()
elif page == "osm":
    page_osm()

