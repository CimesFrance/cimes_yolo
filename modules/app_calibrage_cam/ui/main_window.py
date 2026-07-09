"""Module de gestion de la fenetre principale"""

import os
import tkinter as tk
from modules.app_calibrage_cam.core.state import AppState
from modules.app_calibrage_cam.ui.canvas_view import FenetreImage
from modules.app_calibrage_cam.ui.components import Interraction
from modules.app_calibrage_cam.ui.styles import StyleManager
from src.utils.file_manager import get_project_root


class ApplicationCalibrage(tk.Tk):
    """Fenêtre principale de l'application de calibration"""
    def __init__(self, parent=None):
        super().__init__()
        self.app = AppState()
        self.title("Cimes")
        icon_path = os.path.join(get_project_root(), "modules", "app_change_corr_params", "assets", "icons", "cimes-logo.ico")
        try:
            self.iconbitmap(icon_path)
        except Exception:
            pass
        self.geometry("1300x900")
        self.minsize(1300, 900)
        self.resizable(True, True)
        # Application du StyleManager
        self.style_manager = StyleManager(self)
        # Layout principal
        self.sidebar = Interraction(
            self, self.app, width=350, bg=self.style_manager.BG_SIDEBAR
        )
        self.canvas_view = FenetreImage(
            self, self.app, bg=self.style_manager.BG_MAIN, bd=0, highlightthickness=0
        )
        # Sidebar à gauche
        self.sidebar.grid(row=0, column=0, sticky="ns", padx=0, pady=0)
        self.sidebar.pack_propagate(False)
        self.sidebar.grid_propagate(False)
        # Canvas à droite
        self.canvas_view.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
