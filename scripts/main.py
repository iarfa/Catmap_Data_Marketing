# =======================
# 📦 Imports & Librairies
# =======================
from functions_basics import (
    chargement_donnees,
    apercu_donnes,
    filtrer_donnees,
    choix_centre_departement
)
from functions_cartographie import (
    transfo_geodataframe,
    isochrone_polygon,
    isochrone_OSM
)
from interface import personnalisation_page, affichage_titre

# =======================
# 📁 Chemins des fichiers
# =======================
path_etablissement = (
    "../data/Fichier_final_etablissements_commerces_alimentaire_non_alimentaire.parquet"
)
path_centres_departements = "../data/Centres_departements.xlsx"

# =======================
# 🎨 Style et titre de la page
# =======================
personnalisation_page()
affichage_titre()


# =======================
# 📥 Chargement des données
# =======================
df_etablissements, df_centres_dep = chargement_donnees(
    path_etablissement, path_centres_departements
)

# =======================
# 👁️ Aperçu des données
# =======================
apercu_donnees(df_etablissements, 3)

# =======================
# 🧼 Filtrage utilisateur
# =======================
df_filtre = filtrer_donnees(df_etablissements)

# =======================
# 🗺️ Choix du centre de carte
# =======================
lat_centre, lon_centre, departement_choisi = choix_centre_departement(
    df_filtre, df_centres_dep
)

# =======================
# 📍 Transformation GeoDataFrame
# =======================
gdf_etablissements = transfo_geodataframe(
    df_filtre, longitude_col="longitude", latitude_col="latitude", crs="EPSG:4326"
)
