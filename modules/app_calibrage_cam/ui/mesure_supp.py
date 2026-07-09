"""
Module orchestrateur des mesures supplémentaires pour la barre latérale.
"""

from tkinter import ttk
from modules.app_calibrage_cam.ui.une_mesure import UneMesure

class MesureSupp:
    """Classe pour gérer les mesures supplémentaires"""
    def __init__(self, app):
        self.app = app
        self.mesures_supp_frame = None
        self.btn_ajouter = None
        self.btn_supprimer = None
        # Les 3 mesures supplémentaires existent TOUJOURS en mémoire.
        # "Ajouter" ne crée pas une mesure : il active une mesure pré-existante
        # en mettant created=True et flag_affiche_frame=True.
        self.mes_mesures_supp = {
            "Mesure_supp_1": UneMesure ("Mesure N°1", "green", 1, self.app),
            "Mesure_supp_2": UneMesure ("Mesure N°2", "blue", 2, self.app),
            "Mesure_supp_3": UneMesure ("Mesure N°3", "yellow", 3, self.app),
        }
        self.app.flag_mesures_supp_affiche.trace_add("write", self.display_state)

    def mesures_supp_gui(self):
        """Construit l'interface graphique des mesures supplémentaires"""
        if self.mesures_supp_frame is not None:
            self.btn_ajouter = ttk.Button(
                self.mesures_supp_frame,
                text="Ajouter",
                command=self._ajouter_mesure,
                style="TButton",
            )
            self.btn_supprimer = ttk.Button(
                self.mesures_supp_frame,
                text="Supprimer",
                command=self._supprimer_mesure,
                style="Secondary.TButton",
            )
            self.btn_ajouter.grid(row=0, column=0, sticky="we", padx=2, pady=(0, 10))
            self.btn_supprimer.grid(row=0, column=1, sticky="we", padx=2, pady=(0, 10))
            for i, (_cle, mesure) in enumerate(self.mes_mesures_supp.items(), start=1):
                mesure.mesure_gui()
                mesure.mesure_frame.grid(
                    row=i, column=0, columnspan=2, sticky="nsew", padx=2, pady=2
                )
            self.mesures_supp_frame.columnconfigure(0, weight=1)
            self.mesures_supp_frame.columnconfigure(1, weight=1)

    def display_state(self, *_args):
        """Met à jour l'affichage des mesures supplémentaires"""
        etat = "normal" if self.app.flag_mesures_supp_affiche.get() else "disabled"
        self.btn_ajouter.config(state=etat)
        self.btn_supprimer.config(state=etat)

    def _ajouter_mesure(self):
        """Active la mesure supplémentaire correspondant au radio sélectionné."""
        num = self.app.choix_mesure.get()  # Numéro du radio sélectionné
        key = f"Mesure_supp_{num}"
        if num > 0 and key in self.mes_mesures_supp:
            self.mes_mesures_supp[key].longueur.set("0.00")
            self.mes_mesures_supp[key].flag_affiche_frame.set(True)  # Active l'UI
            self.mes_mesures_supp[key].created = True  # Autorise les clics

    def _supprimer_mesure(self):
        """Désactive la mesure supplémentaire sélectionnée.
        Remet les coordonnées à zéro et grise l'affichage dans la sidebar."""
        num = self.app.choix_mesure.get()
        key = f"Mesure_supp_{num}"
        if num > 0 and key in self.mes_mesures_supp:
            m = self.mes_mesures_supp[key]
            m.longueur.set("- - -")
            m.flag_affiche_frame.set(False)  # Grise l'UI
            m.created = False                # Bloque les clics canvas
            m.supprimer_pts()                # Remet les coordonnées des points à zéro
            # Toggle modif_canvas pour forcer un re-rendu du canvas
            # (efface les points/lignes de la mesure supprimée)
            current = self.app.modif_canvas.get()
            self.app.modif_canvas.set(not current)
