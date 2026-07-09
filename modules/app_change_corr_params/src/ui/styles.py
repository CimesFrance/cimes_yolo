"""Module de gestion des styles de l'application."""

# pylint: disable=too-few-public-methods
from tkinter import ttk


class StyleManager:
    """Classe pour gérer les styles de l'application."""
    # --- Palette de couleurs centrale ---
    BG_MAIN = "#F5F6FA"
    BG_SIDEBAR = "#2C3E50"
    PRIMARY = "#2C3E50"
    ACCENT = "#D35400"
    ACCENT_HOVER = "#BA4A00"
    TEXT = "#2F3640"
    BORDER = "#DCDDE1"

    def __init__(self, root):
        """Initialise le gestionnaire de styles et applique le thème."""
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self._configure_styles()
        root.configure(bg=self.BG_MAIN)

    def _configure_styles(self):
        """Configure tous les styles ttk de l'application."""
        # --- Frames ---
        self.style.configure("TFrame", background=self.BG_MAIN)
        self.style.configure("Sidebar.TFrame", background=self.BG_SIDEBAR, relief="flat")
        # --- Labels ---
        self.style.configure(
            "TLabel",
            background=self.BG_MAIN,
            foreground=self.TEXT,
            font=("Segoe UI", 10),
        )
        self.style.configure(
            "Sidebar.TLabel",
            background=self.BG_SIDEBAR,
            foreground="white",
            font=("Segoe UI", 10),
        )
        # style.map avec 'disabled'/'!disabled' : force la couleur même quand
        # le widget est grisé. Sans ça, tkinter appliquerait ses propres couleurs
        # par défaut sur les éléments désactivés.
        self.style.map(
            "Sidebar.TLabel",
            background=[("disabled", self.BG_SIDEBAR), ("!disabled", self.BG_SIDEBAR)],
            foreground=[("disabled", "white"), ("!disabled", "white")],
        )
        # --- Cases à cocher ---
        self.style.configure(
            "Sidebar.TCheckbutton",
            background=self.BG_SIDEBAR,
            foreground="white",
        )
        self.style.map(
            "Sidebar.TCheckbutton",
            background=[("disabled", self.BG_SIDEBAR), ("!disabled", self.BG_SIDEBAR)],
            foreground=[("disabled", "white"), ("!disabled", "white")],
        )
        # --- Labels titre ---
        self.style.configure(
            "Title.TLabel",
            font=("Segoe UI", 12, "bold"),
            foreground=self.PRIMARY,
        )
        self.style.configure(
            "Sidebar.Title.TLabel",
            background=self.BG_SIDEBAR,
            font=("Segoe UI", 12, "bold"),
            foreground="white",
        )
        # --- Boutons standard ---
        self.style.configure("TButton", font=("Segoe UI", 9, "bold"))
        # Trois états gérés ici :
        # 'disabled' → bouton grisé
        # 'active'   → bouton survolé par la souris
        # '!disabled'→ bouton normal
        self.style.map(
            "TButton",
            background=[
                ("disabled", "#7F8C8D"),
                ("active", self.ACCENT_HOVER),
                ("!disabled", self.ACCENT),
            ],
            foreground=[("disabled", "#BDC3C7"), ("!disabled", "white")],
        )
        # --- Bouton icône ---
        self.style.configure(
            "Icon.TButton",
            background=self.BG_SIDEBAR,
            borderwidth=0,
            relief="flat",
            focuscolor="none",
            padding=0,
        )
        #configuration du hover
        self.style.map(
            "Icon.TButton",
            background=[("active", "#34495E"), ("!disabled", self.BG_SIDEBAR)],
            relief=[("pressed", "flat")],
        )
