"""Module d'importation de ressources pour l'application.
Gestion des fichiers externes et des images."""

import os
import zipfile
import pandas as pd
from PIL import Image, ImageTk


def importer_image_tk(nom_image, width=24, height=24):
    """Charge une image depuis le dossier assets et la convertit en PhotoImage pour Tkinter."""
    from src.utils.file_manager import get_project_root
    base_path = os.path.join(get_project_root(), "modules", "app_change_corr_params")
    path = os.path.join(base_path, "assets", "icons", nom_image)
    try:
        img = Image.open(path).resize((width, height), Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img)
    except OSError as error:
        print(f"Erreur lors du chargement de l'image {nom_image} : {error}")
        return None


def info_extract_courbe_numerique(zip_file):
    """Extrait les données de la courbe numérique et les
    paramètres de correction depuis un fichier zip."""
    with zipfile.ZipFile(zip_file, "r") as zip_ref:
        with zip_ref.open("data.csv") as file_csv:
            data_frame = pd.read_csv(file_csv)
        with zip_ref.open("params_correction.txt") as file_txt:
            texte = file_txt.read().decode("utf-8")
    vars_dict = {}
    for ligne in texte.splitlines():
        if "=" in ligne:
            key, val = ligne.split("=")
            try:
                vars_dict[key.strip()] = float(val.strip())
            except ValueError:
                vars_dict[key.strip()] = val.strip()
    return {"tamis": data_frame.iloc[:, 0].tolist(),
    "cumul": data_frame.iloc[:, 1].tolist()}, vars_dict
