"""Module de gestion des imports de l'application.
"""

import os
import zipfile
from PIL import Image, ImageTk
import pandas as pd


def importer_image_tk(nom_image):
    """Charge une image depuis le dossier assets, peu importe d'où est appelé le script."""
    from src.utils.file_manager import get_project_root
    racine_projet = os.path.join(get_project_root(), "modules", "app_calibrage_cam")
    chemin_fichier = os.path.join(racine_projet, "assets", nom_image)

    if not os.path.exists(chemin_fichier):
        print(f"Erreur : Le fichier {chemin_fichier} est introuvable.")
        return None

    img = Image.open(chemin_fichier)
    img = img.resize((24, 24), Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(img)


def info_extract_courbe_numerique(zip_file):
    """Extrait les informations de la courbe numérique du fichier zip."""
    with zipfile.ZipFile(zip_file, "r") as z:
        #Lire le CSV directement dans un DataFrame
        with z.open("data.csv") as f:
            df = pd.read_csv(f)
        #Lire le TXT directement dans une variable
        with z.open("params_correction.txt") as f:
            texte = f.read().decode("utf-8")  # convertir les bytes en string
    variables = {}
    for ligne in texte.splitlines():
        # ignorer les lignes vides
        if ligne.strip():
            # séparer par le '='
            nom, val = ligne.split("=")
            nom = nom.strip()  # enlever espaces autour du nom
            val = val.strip()  # enlever espaces autour de la valeur
            # convertir en float si possible
            try:
                val = float(val)
            except ValueError:
                pass  # garder en string si ce n'est pas un nombre
            variables[nom] = val
    granulometrie = {
        "tamis": df["Tamis(mm)"].tolist(),
        "cumul": df["Cumul(%)"].tolist(),
    }
    return granulometrie, variables
