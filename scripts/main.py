# =======================
# 📦 Imports & Librairies
# =======================
from fonctions_basiques import (
    chargement_donnees,
    apercu_donnees,
    filtrer_donnees,
    choix_centre_departement
)
from fonctions_cartographie import (
    transfo_geodataframe,
    choix_carte,
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
df_etablissements_filtre = filtrer_donnees(df_etablissements)

# =======================
# 🗺️ Choix du centre de carte
# =======================
departement_choisi, lat_centre, lon_centre = choix_centre_departement(
    df_etablissements_filtre, df_centres_dep
)

# =======================
# 📍 Transformation GeoDataFrame
# =======================
gdf_etablissements = transfo_geodataframe(
    df_etablissements_filtre, longitude_col="longitude", latitude_col="latitude", crs="EPSG:4326"
)

# =======================
# 📍 Affichage de la carte
# =======================

choix_carte(df_etablissements_filtre,lat_centre,lon_centre)

