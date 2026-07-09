"""Module de gestion d'une mesure individuelle (distance entre 2 points)
Chaque mesure est représentée par une instance de la classe "UneMesure"""

import json
import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
from modules.app_calibrage_cam.core.state import PointModel
from src.utils.file_manager import save_conversion_parameter

# pylint: disable=too-many-instance-attributes
class UneMesure :
    """Classe représentant une mesure de distance entre 2 points sur l'image.
    Chaque mesure a : - un titre (ex: "Mesure N°1")
    - une couleur d'affichage (ex: rouge)
    - un numéro d'identification (ex: 1)
    - des points de mesure (pt1 et pt2) avec leurs coordonnées en image et en canvas
    - une valeur de longueur calculée
    - des contrôles d'affichage (checkbox pour afficher les points,
    radio pour sélectionner la mesure active)"""
    def __init__(self, title, color, num, app):
        self.title = title
        self.title_label = None
        self.check_affichage = None
        self.label_afficheur_longueure = None
        self.afficheur_longueure = None
        self.pastille = None
        self.dash = None
        self.lbl_val = None
        self.lbl_unit = None
        self.radio_saisir = None
        self.btn_save = None
        self.btm = None
        self.color = color
        self.flag_affiche_ptligne = tk.BooleanVar(value=True)  #Checkbox "Afficher" cochée
        self.flag_affiche_frame = tk.BooleanVar(value=False)   #Section UI active/inactive
        self.num = num  # 0 = échelle, 1-3 = mesures supplémentaires
        self.longueur = tk.StringVar(value="0.00")  # Valeur affichée en mm
        self.mesure_frame = None  # Widget Tk parent
        self.app = app
        self.pts = {"pt1": PointModel(color), "pt2": PointModel(color)}
        self.created = False
        self.flag_affiche_frame.trace_add("write", self.display_state)

    def mesure_gui(self):
        """Construit l'interface graphique de la mesure"""
        if self.mesure_frame:
            self.mesure_frame.configure(bg="#2C3E50", pady=5)
            # Header : Nom + Pastille
            top = tk.Frame(self.mesure_frame, bg="#2C3E50")
            top.pack(fill="x")
            self.title_label = ttk.Label(top, text=self.title, style="Sidebar.Subtitle.TLabel"
            )
            self.title_label.pack(side="left")
            self.pastille = tk.Frame(top, bg=self.color, width=10, height=10)
            self.pastille.pack(side="right", padx=5)
            # Dashboard : Valeur en gros
            self.dash = tk.Frame(self.mesure_frame, bg="#34495E", pady=10)
            self.dash.pack(fill="x", pady=5)
            self.lbl_val = ttk.Label(
                self.dash, textvariable=self.longueur, style="Value.TLabel"
            )
            self.lbl_val.pack(side="left", padx=10)
            self.lbl_unit = ttk.Label(self.dash, text="mm", style="Unit.TLabel")
            self.lbl_unit.pack(side="right", padx=10)
            # Contrôles discrets
            self.btm = tk.Frame(self.mesure_frame, bg="#2C3E50")
            self.btm.pack(fill="x")
            self.check_affichage = ttk.Checkbutton(
                self.btm,
                text="Afficher",
                variable=self.flag_affiche_ptligne,
                style="Sidebar.TCheckbutton",
                command=self._affiche_mesure,
            )
            self.check_affichage.pack(side="left")
            self.radio_saisir = ttk.Radiobutton(
                self.btm,
                text="Saisir",
                value=self.num,
                variable=self.app.choix_mesure,
                style="Sidebar.TRadiobutton",
            )
            self.radio_saisir.pack(side="right")
            if self.num != 0:
                is_active = self.flag_affiche_frame.get()
                etat = "normal" if is_active else "disabled"
                self.title_label.config(state=etat)
                self.check_affichage.config(state=etat)
                self.lbl_val.config(state=etat)


    def _affiche_mesure(self):
        """Active ou désactive l'affichage de la mesure.
        On "toggle" modif_canvas pour forcer un re-rendu du canvas."""
        current = self.app.modif_canvas.get()
        self.app.modif_canvas.set(not current)

    def display_state(self, *_args):
        """Met à jour l'affichage de la mesure"""
        is_active = self.flag_affiche_frame.get()
        etat = "normal" if is_active else "disabled"
        if hasattr(self, "title_label") and self.title_label:
            self.title_label.config(state=etat)
            self.check_affichage.config(state=etat)
            self.radio_saisir.config(
                state="normal"
            )  # Toujours actif pour cibler l'ajout
            self.lbl_val.config(state=etat)
            # Styles dynamiques
            dash_bg = "#34495E" if is_active else "#2C3E50"
            val_style = "Value.TLabel" if is_active else "DisabledValue.TLabel"
            unit_style = "Unit.TLabel" if is_active else "DisabledUnit.TLabel"
            pastille_co = self.color if is_active else "#7F8C8D"
            self.dash.config(bg=dash_bg)
            self.lbl_val.config(style=val_style)
            self.lbl_unit.config(style=unit_style)
            self.pastille.config(bg=pastille_co)

    def add_pt(self, event):
        """Ajoute un point à la mesure.

        Conversion inverse des coordonnées :
            img_x = (canvas_x - origine_x) / zoom
            img_y = (canvas_y - origine_y) / zoom

        C'est l'inverse de la formule dans canvas_view._dessiner_mesure().
        Le premier point non-créé est utilisé (pt1 d'abord, puis pt2)."""
        orig = self.app.img.coord_origine.get()
        zoom = self.app.zoom_factor.get()
        # Conversion : coordonnées écran → coordonnées image source
        x_img = (event.x - orig["x"]) / zoom
        y_img = (event.y - orig["y"]) / zoom
        # Remplir le premier point disponible (pt1 puis pt2)
        for pt in self.pts.values():
            if not pt.created:
                pt.coord_pt_img = {"x": x_img, "y": y_img}
                pt.created = True
                break
        # Quand les 2 points sont posés, calculer la distance
        if self.pts["pt1"].created and self.pts["pt2"].created:
            self.created = True
            self.longueur.set(str(self.calcul_distance()))

    def supprimer_pts(self):
        """Supprime les points de la mesure"""
        for pt in self.pts.values():
            pt.supprimer_pt()

    def maj_pos_pts(self):
        """Met à jour la position des points"""
        orig = self.app.img.coord_origine.get()
        zoom = self.app.zoom_factor.get()
        for pt in self.pts.values():
            if pt.created:
                pt.coord_pt_canvas["x"] = (pt.coord_pt_img["x"] * zoom) + orig["x"]
                pt.coord_pt_canvas["y"] = (pt.coord_pt_img["y"] * zoom) + orig["y"]

    def deplacer_pts(self, key_pt, event, deb_deplc_pt):
        """Déplace un point de la mesure"""
        zoom = self.app.zoom_factor.get()
        dx_img = (event.x - deb_deplc_pt[0]) / zoom
        dy_img = (event.y - deb_deplc_pt[1]) / zoom
        self.pts[key_pt].coord_pt_img["x"] += dx_img
        self.pts[key_pt].coord_pt_img["y"] += dy_img
        if self.pts["pt1"].created and self.pts["pt2"].created:
            self.longueur.set(str(self.calcul_distance()))

    def calcul_distance(self):
        """Calcule la distance réelle (mm) entre les deux points."""
        if not (self.pts["pt1"].created and self.pts["pt2"].created):
            return 0.00
        p1, p2 = self.pts["pt1"].coord_pt_img, self.pts["pt2"].coord_pt_img
        # distance en pixels sur l'image source
        dist_px = np.sqrt((p1["x"] - p2["x"]) ** 2 + (p1["y"] - p2["y"]) ** 2)
        # conversion pixels → mm
        dist_reelle = dist_px * self.app.facteur_conversion.get()
        return round(dist_reelle, 2)

    def sauvegarder_mesure(self):
        """Sauvegarde persistante de la mesure principale.
        Seuls les paramètres de calibrage sont persistés ;
        les coordonnées des points ne sont pas sauvegardées
        afin que les mesures ne réapparaissent pas au redémarrage."""
        # Validation de la saisie avant sauvegarde
        try:
            float(self.app.distance_saisie.get())
        except ValueError:
            messagebox.showerror(
                "Erreur de validation",
                "Impossible de sauvegarder : la longueur réelle doit être une valeur numérique."
            )
            return

        data = {
            "facteur_conversion": self.app.facteur_conversion.get(),
            "distance_saisie": self.app.distance_saisie.get(),
            "longueur": self.longueur.get()
        }
        try:
            with open("mesure_config.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            
            # Mise à jour également du paramètre global pour l'application principale
            save_conversion_parameter(self.app.facteur_conversion.get())
            
            messagebox.showinfo("Succès",
            "Les informations de la mesure ont bien été sauvegardées !")
        # pylint: disable=broad-exception-caught
        except Exception as e:
            print("Erreur de sauvegarde:", e)
            messagebox.showerror("Erreur", f"Échec de la sauvegarde : {str(e)}")
