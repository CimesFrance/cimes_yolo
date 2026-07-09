"""Module contenant les composants liés à l'interface de correction des paramètres."""

# pylint: disable=too-many-ancestors

import os
from tkinter import ttk, messagebox
import numpy as np
from scipy.optimize import minimize
from modules.app_change_corr_params.src.core.engine import correct, erreur_minim  # pylint: disable=import-error
from modules.app_change_corr_params.src.ui.components import PARAM_FILE_PATH, _update_global_error  # pylint: disable=import-error


class BarreCorrectFrameNv(ttk.Frame):
    """Composant pour la saisie manuelle des nouveaux paramètres"""

    def __init__(self, parent, app, graphe, *args, **kwargs):
        super().__init__(parent, style="Sidebar.TFrame", *args, **kwargs)
        self.app = app
        self.graphe = graphe
        self.var_nv = app.var_correct["var_nv"]
        # trace_add : quand show_param_nv change (après un import ZIP),
        # _update_state est appelé automatiquement pour activer/griser les champs.
        self.app.show_param_nv.trace_add("write", self._update_state)
        self._build_ui()

    def _build_ui(self):
        ttk.Label(self, 
            text="Correction Manuelle",
            style="Sidebar.Title.TLabel",
        ).pack(pady=(0, 10))
        
        inner = ttk.Frame(self, style="Sidebar.TFrame")
        inner.pack(anchor="center")
        
        # Scale
        ttk.Label(inner, text="Scale:", style="Sidebar.TLabel").grid(row=0, column=0)
        self.ent_scale = ttk.Entry(inner, textvariable=self.var_nv["scale"], width=8)
        self.ent_scale.grid(row=1, column=0, padx=5)
        # Offset
        ttk.Label(inner, text="Offset:", style="Sidebar.TLabel").grid(row=0, column=1)
        self.ent_offset = ttk.Entry(inner, textvariable=self.var_nv["offset"], width=8)
        self.ent_offset.grid(row=1, column=1, padx=5)
        # Bouton Valider
        self.btn_valider = ttk.Button(inner, text="Appliquer", command=self._validate_change
        )
        self.btn_valider.grid(row=1, column=2, padx=5)
        self._update_state()

    def _update_state(self, *_args):
        state = "normal" if self.app.show_param_nv.get() else "disabled"
        self.ent_scale.config(state=state)
        self.ent_offset.config(state=state)
        self.btn_valider.config(state=state)

    def _validate_change(self):
        try:
            scale = float(self.var_nv["scale"].get())
            offset = float(self.var_nv["offset"].get())
            # Sécurité scale
            if scale <= 0:
                scale = 0.001
            orig = self.app.my_granulos.originale.granulo
            # Mise à jour de la courbe numérique
            self.app.my_granulos.num.granulo["x_axis"] = correct(
                orig["x_axis"], scale, offset
            )
            # Recalcul de l'erreur
            _update_global_error(self.app)
            self.graphe._maj_cumuls()  # pylint: disable=protected-access
        except ValueError:
            messagebox.showwarning(
                "Format invalide",
                "Veuillez entrer des chiffres "
                "valides pour le Scale et l'Offset (ex: 1.25).",
                parent=self,
            )


class CorrectFrame(ttk.Frame):
    """Conteneur global pour la zone de correction"""

    def __init__(self, parent, app, graphe, *args, **kwargs):
        super().__init__(parent, style="Sidebar.TFrame", *args, **kwargs)
        self.app = app
        self.graphe = graphe
        self._build_ui()

    def _build_ui(self):
        ttk.Label(self, text="Correction Automatique", style="Sidebar.Title.TLabel").pack(
            pady=(0, 10)
        )
        
        # Bouton Auto-Ajuster (pleine largeur)
        self.btn_auto = ttk.Button(self, text="Auto-Ajuster", command=self._auto)
        self.btn_auto.pack(fill="x", pady=5)
        # Séparateur
        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=10)
        # Section Manuelle
        self.manual_f = BarreCorrectFrameNv(self, self.app, self.graphe)
        self.manual_f.pack(fill="x")
        # Bouton Sauvegarde
        self.btn_save = ttk.Button(self, text="Sauvegarder Paramètres", command=self._save_params
        )
        self.btn_save.config(state="disabled")
        self.btn_save.pack(fill="x", pady=(15, 5))

        # Label confirmation sauvegarde
        self.lbl_save_info = ttk.Label(self, text="", style="Sidebar.TLabel", justify="center", font=("Segoe UI", 11, "bold")
        )
        self.lbl_save_info.pack(pady=5)
        # Charge les paramètres si existants
        self._load_saved_params()
        # Traces pour l'état des boutons
        # trace_add : quand flag_affiche_erreur passe à True (les deux courbes
        # sont importées), les boutons Auto-Ajuster et Sauvegarder se déverrouillent.
        self.app.flag_affiche_erreur.trace_add("write", self._toggle_buttons)

    def _toggle_buttons(self, *_args):
        state = "normal" if self.app.flag_affiche_erreur.get() else "disabled"
        self.btn_auto.config(state=state)
        self.btn_save.config(state=state)

    def _auto(self):
        orig = self.app.my_granulos.originale.granulo
        prat = self.app.my_granulos.prat.granulo
        # Vérification avant de lancer les calculs
        if orig is None or prat is None:
            messagebox.showwarning(
                "Importation requise",
                "Veuillez d'abord importer la courbe numérique et"
                " la courbe réelle avant de lancer l'auto-ajustement.",
                parent=self,
            )
            return
        try:
            res = minimize(
                erreur_minim,   # Fonction à minimiser, calcule l'erreur pour un scale/offset
                [1.0, 0.0],     # Point de départ : scale=1 (pas de changement), offset=0
                args=(
                    np.array(orig["x_axis"]),
                    np.array(orig["y_axis"]),
                    np.array(prat["x_axis"]),
                    np.array(prat["y_axis"]),
                ),
                # bounds : scale doit rester > 0, un scale négatif inverserait la courbe
                # offset peut prendre n'importe quelle valeur (None = pas de limite).
                bounds=[(1e-6, None), (None, None)],
            )
            s, o = res.x
            self.app.var_correct["var_nv"]["scale"].set(str(round(s, 3)))
            self.app.var_correct["var_nv"]["offset"].set(str(round(o, 3)))
            # Appliquer le résultat
            self.app.my_granulos.num.granulo["x_axis"] = correct(orig["x_axis"], s, o)
            # Recalcul erreur
            _update_global_error(self.app)
            self.graphe._maj_cumuls()  # pylint: disable=protected-access
        except Exception as e:  # pylint: disable=broad-exception-caught
            messagebox.showerror(
                "Échec de l'optimisation",
                f"L'algorithme de calcul n'a pas pu faire converger "
                f"les deux courbes.\n\nDétails : {e}",
                parent=self,
            )

    def _save_params(self):
        """
        Sauvegarde les paramètres actuels (Scale et Offset)
        dans un fichier texte pour persistance entre les sessions.
        """
        try:
            scale_val = self.app.var_correct["var_nv"]["scale"].get()
            offset_val = self.app.var_correct["var_nv"]["offset"].get()
            # Validation avant sauvegarde
            try:
                float(scale_val)
                float(offset_val)
            except ValueError:
                messagebox.showwarning(
                    "Format invalide",
                    "Valeurs de Scale ou Offset incorrectes. "
                    "entrez une valeur de type int ou float.",
                    parent=self,
                )
                return

            os.makedirs(os.path.dirname(PARAM_FILE_PATH), exist_ok=True)

            with open(PARAM_FILE_PATH, "w", encoding="utf-8") as f:
                f.write(f"Scale = {scale_val}\nOffset = {offset_val}\n")

            self.lbl_save_info.config(
                text=
                f"Nouveaux paramètres sauvegardés\nScale: {scale_val} "
                f" |  Offset: {offset_val}",
                foreground="#FFFFFF",
            )
        except Exception:  # pylint: disable=broad-exception-caught
            self.lbl_save_info.config(
                text="Erreur de sauvegarde", foreground="#E74C3C"
            )

    def _load_saved_params(self):
        """
        Charge les derniers paramètres sauvegardés depuis le fichier texte
        et met à jour l'interface utilisateur.
        """
        if os.path.exists(PARAM_FILE_PATH):
            try:
                with open(PARAM_FILE_PATH, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                scale_val, offset_val = "1.0", "0.0"
                for line in lines:
                    if line.startswith("Scale"):
                        scale_val = line.split("=")[1].strip()
                    elif line.startswith("Offset"):
                        offset_val = line.split("=")[1].strip()
                self.lbl_save_info.config(
                    text=
                    f"Derniers paramètres sauvegardés:\nScale: {scale_val}"
                    f"  |  Offset: {offset_val}",
                    foreground="#FFFFFF",
                )
            except Exception:  # pylint: disable=broad-exception-caught
                pass
