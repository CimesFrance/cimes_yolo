"""Module de définition des composants graphiques 
pour l'application de réglage de paramètres granulométriques."""

# pylint: disable=too-many-ancestors

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import numpy as np
from modules.app_change_corr_params.src.core.engine import inv_correct, calc_erreur  # pylint: disable=import-error
from modules.app_change_corr_params.src.utils.importers import info_extract_courbe_numerique, importer_image_tk  # pylint: disable=import-error

PARAM_FILE_PATH = "mesure/params_correction.txt"


def _update_global_error(app):
    """Met à jour le calcul de l'erreur globale entre la courbe numérique et pratique."""
    if app.my_granulos.num.granulo and app.my_granulos.prat.granulo:
        err = calc_erreur(
            np.array(app.my_granulos.num.granulo["x_axis"]),
            np.array(app.my_granulos.num.granulo["y_axis"]),
            np.array(app.my_granulos.prat.granulo["x_axis"]),
            np.array(app.my_granulos.prat.granulo["y_axis"]),
        )
        app.erreur.set(str(err))
        app.flag_affiche_erreur.set(True)


class UneCourbeAffiche(tk.Frame):
    """Composant pour afficher une courbe dans la sidebar
    avec son nom et une case à cocher pour l'affichage"""

    def __init__(self, parent, un_cumul, graphe, *args, **kwargs):
        super().__init__(parent, bg=parent["bg"], *args, **kwargs)
        self.un_cumul = un_cumul
        self.graphe = graphe
        # trace_add "write" : tkinter appelle automatiquement affiche_elt_courbe
        # chaque fois que show_courbe_elt change de valeur (ex: après un import).
        self.un_cumul.show_courbe_elt.trace_add("write", self.affiche_elt_courbe)
        self._une_courbe_frame_gui()

    def _une_courbe_frame_gui(self):
        self.color_square = tk.Label(
            self, bg=self.un_cumul.color, width=2, relief="flat", state="disabled"
        )
        self.label_check = ttk.Label(self, text=self.un_cumul.name, style="Sidebar.TLabel", state="disabled"
        )
        self.check = ttk.Checkbutton(
            self,
            variable=self.un_cumul.flag_affichage,
            command=self.maj_cumul,
            style="Sidebar.TCheckbutton",
            state="disabled",
        )
        self.color_square.pack(side="left", padx=5, pady=2)
        self.label_check.pack(side="left", padx=5, expand=True, fill="x")
        self.check.pack(side="right", padx=5)

    def affiche_elt_courbe(self, *_args):
        """Active ou désactive les éléments de la courbe selon l'état de la case à cocher"""
        # *_args : tkinter passe des arguments internes lors du callback (nom, index, mode)
        # On ne les utilise pas, donc on les ignore avec _args.
        etat = "normal" if self.un_cumul.show_courbe_elt.get() else "disabled"
        self.color_square.config(state=etat)
        self.label_check.config(state=etat)
        self.check.config(state=etat)

    def maj_cumul(self):
        """Met à jour les cumulatives dans le graphe lorsque l'affichage est modifié"""
        self.graphe._maj_cumuls()  # pylint: disable=protected-access


class ImportGranuloFrame(ttk.Frame):
    """Composant pour l'importation de courbes
    granulométriques numériques ou réelles"""

    def __init__(self, parent, app, graphe, type_import, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.app, self.graphe, self.type = app, graphe, type_import
        # le fond de la frame d'import à blanc
        self.config(style="Sidebar.TFrame")
        self.tk_img_dl = importer_image_tk("logodownload.png")
        self._setup_ui()

    def _setup_ui(self):
        logo_ref = (
            self.app.my_granulos.num.logo
            if self.type == "num"
            else self.app.my_granulos.prat.logo
        )
        txt = (
            "Importer Courbe Numérique"
            if self.type == "num"
            else "Importer Courbe Réelle"
        )
        # Ajout explicite du style Sidebar
        self.columnconfigure(1, weight=1)
        ttk.Label(self, image=logo_ref, style="Sidebar.TLabel").grid(
            row=0, column=0, padx=5
        )
        ttk.Label(self, text=txt, style="Sidebar.TLabel").grid(
            row=0, column=1, sticky="w"
        )
        ttk.Button(self, image=self.tk_img_dl, command=self._import, style="Icon.TButton"
        ).grid(row=0, column=2, padx=5, sticky="e")

    def _import(self):
        if self.type == "num":
            path = filedialog.askopenfilename(filetypes=[("ZIP", "*.zip")])
            if path:
                try:
                    granulo, c_var = info_extract_courbe_numerique(path)
                    self.app.my_granulos.num.granulo = {
                        "x_axis": granulo["tamis"],
                        "y_axis": granulo["cumul"],
                    }
                    self.app.var_correct["var_act"]["scale"].set(str(c_var["Scale"]))
                    self.app.var_correct["var_act"]["offset"].set(str(c_var["Offset"]))
                    inv_x = inv_correct(
                        granulo["tamis"], c_var["Scale"], c_var["Offset"]
                    )
                    self.app.my_granulos.originale.granulo = {
                        "x_axis": inv_x,
                        "y_axis": granulo["cumul"],
                    }
                    self.app.show_correct_frame_act.set(True)
                    self.app.my_granulos.num.show_courbe_elt.set(True)
                    self.app.my_granulos.originale.show_courbe_elt.set(True)
                    self.app.show_param_nv.set(True)
                    self.app.flag_affiche_btn_sauvegarde.set(True)
                except Exception as e:  # pylint: disable=broad-exception-caught
                    messagebox.showerror(
                        "Erreur d'import",
                        f"Le fichier ZIP sélectionné est invalide ou illisible.\n\nDétails : {e}",
                    )
                    return
        else:
            path = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx")])
            if path:
                try:
                    df = pd.read_excel(path)
                    self.app.my_granulos.prat.granulo = {
                        "x_axis": df.iloc[:, 0].tolist(),
                        "y_axis": df.iloc[:, 1].tolist(),
                    }
                    self.app.my_granulos.prat.show_courbe_elt.set(True)
                except Exception as e:  # pylint: disable=broad-exception-caught
                    messagebox.showerror(
                        "Erreur d'import",
                        f"Impossible de lire ce fichier Excel."
                        f"Vérifiez qu'il n'est pas déjà ouvert.\n\nDétails : {e}",
                    )
                    return
        _update_global_error(self.app)
        self.graphe._maj_cumuls()  # pylint: disable=protected-access
