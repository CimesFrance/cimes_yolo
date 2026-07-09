"""Module de définition des modèles de données pour l'application
 de réglage de paramètres granulométriques.
Ce module contient les classes de données utilisées pour stocker les informations
sur les cumuls granulométriques, ainsi que l'état global de l'application."""

# pylint: disable=too-few-public-methods

import tkinter as tk
from modules.app_change_corr_params.src.utils.importers import importer_image_tk  # pylint: disable=import-error


class Cumul:
    """Modèle de données pour un cumul granulométrique unique"""

    def __init__(self, name, color, granulo=None, logo=None):
        self.name = name
        self.color = color
        self.granulo = granulo
        self.logo = logo
        # Par défaut à 1 : la courbe est affichée dès qu'elle est importée.
        self.flag_affichage = tk.IntVar(value=1)
        # Contrôle si les widgets de la sidebar (case à cocher, label) sont
        # cliquables ou grisés. False = grisé,
        # True = actif.
        self.show_courbe_elt = tk.BooleanVar(value=False)


class MesCumuls:
    """Conteneur pour les trois types de courbes de l'application"""

    def __init__(self):
        self.num = Cumul(
            name="Courbe numérique corrigée",
            color="#E74C3C",
            logo=importer_image_tk("photo camera.png"),
        )
        self.originale = Cumul(name="Courbe numérique originale", color="#F1C40F")
        self.prat = Cumul(
            name="Courbe réelle tamisée",
            color="#27AE60",
            logo=importer_image_tk("logo tamis.png"),
        )


class AppState:
    """Gestionnaire d'état global partagé entre les vues"""

    def __init__(self):
        self.my_granulos = MesCumuls()
        self.var_correct = {
            "var_act": {
                "scale": tk.StringVar(value="1.00"),
                "offset": tk.StringVar(value="0.00"),
            },
            "var_nv": {
                "scale": tk.StringVar(value="1.00"),
                "offset": tk.StringVar(value="0.00"),
            },
        }
        # Valeur numérique de l'erreur affichée dans l'interface
        self.erreur = tk.StringVar(value="0.00")
        # Active la section "paramètres actuels" dans la sidebar (après import ZIP)
        self.show_correct_frame_act = tk.BooleanVar(value=False)
        # Devient True quand les deux courbes sont importées → déverrouille
        # les boutons Auto-Ajuster et Sauvegarder
        self.flag_affiche_erreur = tk.BooleanVar(value=False)
        # Active les champs Scale/Offset manuels (après import ZIP)
        self.show_param_nv = tk.BooleanVar(value=False)
        # Déverrouille le bouton de sauvegarde quand les paramètres sont prêts
        self.flag_affiche_btn_sauvegarde = tk.BooleanVar(value=False)
