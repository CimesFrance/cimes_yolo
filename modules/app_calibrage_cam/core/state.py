"""
Module de gestion de l'état de l'application.
Contient les classes ImageModel, PointModel, et AppState qui centralisent les données et
l'état de l'application pour une gestion plus propre et réactive."""

import json
import os
import tkinter as tk
from modules.app_calibrage_cam.core.custom_vars import JSONVar  #Variable pour stocker des dicts
from src.utils.file_manager import load_conversion_param

# pylint: disable=too-few-public-methods
class ImageModel:
    """Classe pour stocker les données de l'image."""
    def __init__(self):
        self.id_img = None
        self.tk_img = None
        # Position du coin haut-gauche de l'image dans le canvas (en pixels écran).
        # trace_add à chaque modification.
        self.coord_origine = JSONVar(value={"x": 0, "y": 0})
        self.import_img = None  # Objet PIL.Image de l'image source
        self.img_path = tk.StringVar(value="")

    def reboot(self):
        """Réinitialise l'image."""
        self.id_img = None
        self.tk_img = None
        self.coord_origine.set({"x": 0, "y": 0})
        self.import_img = None


# pylint: disable=too-few-public-methods
class PointModel:
    """Classe pour stocker les données d'un point.

    Deux systèmes de coordonnées coexistent :
    - coord_pt_img   : position sur l'IMAGE SOURCE (pixels réels, invariante au zoom)
    - coord_pt_canvas : position à l'ÉCRAN (pixels canvas, recalculée à chaque re-rendu)

    Seul coord_pt_img est persisté ; coord_pt_canvas est éphémère."""
    def __init__(self, color):
        self.color = color
        self.coord_pt_img = {"x": 0, "y": 0}     #Coordonnées sur l'image source (persistantes)
        self.coord_pt_canvas = {"x": 0, "y": 0}   #Coordonnées écran (recalculées à chaque rendu)
        self.taille = 5    #Rayon de détection de clic en pixels canvas
        self.id = None
        # created = True signifie que ce point a été posé sur l'image
        # et doit être dessiné sur le canvas lors du prochain re-rendu.
        self.created = False

    def supprimer_pt(self):
        """Supprime le point."""
        self.coord_pt_img = {"x": 0, "y": 0}
        self.coord_pt_canvas = {"x": 0, "y": 0}
        self.id = None
        self.created = False


# pylint: disable=too-many-instance-attributes
class AppState:
    """Classe pour stocker l'état de l'application."""
    def __init__(self):
        # pylint: disable=import-outside-toplevel
        from modules.app_calibrage_cam.ui.une_mesure import UneMesure  # Import local
        from modules.app_calibrage_cam.ui.mesure_supp import MesureSupp
        self.img = ImageModel()
        self.zoom_factor = tk.DoubleVar(value=1.0)  # Facteur de zoom actuel (1.0 = 100%)
        # Ratio mm/pixel calculé lors de l'étalonnage. Toutes les mesures
        # utilisent ce facteur : distance_mm = distance_pixels × facteur_conversion
        # Initialisation avec la valeur globale par défaut
        self.facteur_conversion = tk.DoubleVar(value=float(load_conversion_param()))
        self.distance_saisie = tk.StringVar(value="0.00")  # Valeur saisie par l'utilisateur (mm)
        # Index de la mesure active (0 = échelle, 1-3 = mesures supplémentaires).
        # Détermine sur quelle mesure les clics canvas agissent.
        self.choix_mesure = tk.IntVar(value=0)
        self.flag_mesures_supp_affiche = tk.BooleanVar(value=True)
        self.flage_changer_echelle_affiche = tk.BooleanVar(value=False)
        # Active/désactive la section étalonnage dans la sidebar
        self.flag_echelle_frame = tk.BooleanVar(value=False)
        self.flag_save_btn_affiche = tk.BooleanVar(value=False)
        # Signal de re-rendu du canvas.
        # Sa valeur (True/False) n'a aucune importance : c'est le changement
        # de valeur qui déclenche le trace_add → _maj_fenetre() dans canvas_view.
        # On le "toggle" pour forcer un redessin.
        self.modif_canvas = tk.BooleanVar(value=True)
        self.mesure_echelle = UneMesure (
            title="Mesure Echelle", color="red", num=0, app=self
        )
        self._load_mesure_principale()
        self.mesure_supp = MesureSupp(app=self)
        self.list_mesures = [
            self.mesure_echelle,
            self.mesure_supp.mes_mesures_supp["Mesure_supp_1"],
            self.mesure_supp.mes_mesures_supp["Mesure_supp_2"],
            self.mesure_supp.mes_mesures_supp["Mesure_supp_3"],
        ]

    def _load_mesure_principale(self):
        """Charge les données de la mesure échelle depuis mesure_config.json.
        Toutes les valeurs sont restaurées en mémoire et l'UI est activée."""
        if os.path.exists("mesure_config.json"):
            try:
                with open("mesure_config.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                # On charge d'abord le facteur global, puis on le surcharge par mesure_config si présent
                global_factor = float(load_conversion_param())
                self.facteur_conversion.set(data.get("facteur_conversion", global_factor))
                self.distance_saisie.set(data.get("distance_saisie", "0.00"))
                longueur = data.get("longueur", "0.00")
                self.mesure_echelle.longueur.set(longueur)
                # Restauration des coordonnées en mémoire
                pt1_data = data.get("pt1", {"x": 0, "y": 0})
                self.mesure_echelle.pts["pt1"].coord_pt_img = pt1_data
                pt2_data = data.get("pt2", {"x": 0, "y": 0})
                self.mesure_echelle.pts["pt2"].coord_pt_img = pt2_data
                # created=False : les points ne sont PAS redessinés sur le canvas
                self.mesure_echelle.pts["pt1"].created = False
                self.mesure_echelle.pts["pt2"].created = False
                self.mesure_echelle.created = False
                # Activation de l'UI si des données valides existent
                has_data = (longueur != "0.00" or
                            self.facteur_conversion.get() != 1.0)
                if has_data:
                    self.flag_echelle_frame.set(True)
            # pylint: disable=broad-exception-caught
            except Exception as e:
                print("Erreur de chargement de la configuration:", e)
