"""Module gerant la fenetre principale de l'application de
réglage de paramètres granulométriques."""

# pylint: disable=import-error,too-many-ancestors

import os
import tkinter as tk
from tkinter import ttk
from modules.app_change_corr_params.src.ui.styles import StyleManager
from modules.app_change_corr_params.src.ui.graph import Graphe
from modules.app_change_corr_params.src.ui.components import ImportGranuloFrame, UneCourbeAffiche
from modules.app_change_corr_params.src.ui.correction_panel import CorrectFrame
from modules.app_change_corr_params.src.core.models import AppState
from modules.app_change_corr_params.src.utils.importers import importer_image_tk
from src.utils.file_manager import get_project_root


class CIMESApp(tk.Tk):
    """Creation de  la fenetre principale."""

    def __init__(self, parent=None):
        super().__init__()
        self.title("Cimes")
        icon_path = os.path.join(get_project_root(), "modules", "app_change_corr_params", "assets", "icons", "cimes-logo.ico")
        try:
            self.iconbitmap(icon_path, default=icon_path)
        except Exception:
            pass
        self.geometry("1100x800")
        self.minsize(1300, 900)
        self.state = AppState()
        self.style_manager = StyleManager(self)
        self._build_layout()

    def _build_layout(self):
        # Sidebar
        sidebar = tk.Frame(
            self, width=350, bg=self.style_manager.BG_SIDEBAR, padx=15, pady=15
        )
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        # Graph
        self.graph_view = Graphe(self, self.state)
        self.graph_view.pack(side="right", fill="both", expand=True)
        self.logo_entreprise_side = importer_image_tk("cimes-logo.png", width=250, height=100)
        if self.logo_entreprise_side:
            lbl_logo = tk.Label(
                sidebar,
                image=self.logo_entreprise_side,
                bg=self.style_manager.BG_SIDEBAR,
            )
            lbl_logo.pack(side="bottom", pady=(20, 0))
        # Composants de la sidebar
        # Importation
        ttk.Label(sidebar, text="Importation", style="Sidebar.Title.TLabel").pack(
            pady=(0, 10)
        )
        ImportGranuloFrame(sidebar, self.state, self.graph_view, "num").pack(
            fill="x", pady=5
        )
        ImportGranuloFrame(sidebar, self.state, self.graph_view, "tamis").pack(
            fill="x", pady=5
        )
        tk.Frame(sidebar, height=1, bg="#34495E").pack(fill="x", pady=15)
        # Gestion des courbes
        ttk.Label(sidebar, text="Gestion des Courbes", style="Sidebar.Title.TLabel"
        ).pack(pady=(0, 10))
        UneCourbeAffiche(sidebar, self.state.my_granulos.num, self.graph_view).pack(
            fill="x"
        )
        UneCourbeAffiche(
            sidebar, self.state.my_granulos.originale, self.graph_view
        ).pack(fill="x")
        UneCourbeAffiche(sidebar, self.state.my_granulos.prat, self.graph_view).pack(
            fill="x"
        )
        tk.Frame(sidebar, height=1, bg="#34495E").pack(fill="x", pady=15)
        # Correction
        CorrectFrame(sidebar, self.state, self.graph_view).pack(fill="x")
