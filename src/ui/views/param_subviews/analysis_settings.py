"""Paramètres d'analyse : correction DNA, segmentation YOLO-OBB."""

import tkinter as tk
import os
import sys
from tkinter import ttk, messagebox
from src.ui.widgets.ui_utils import (
    COLOR_CARD_BG,
    COLOR_ACCENT,
    create_setting_header,
    add_tooltip,
)


def create_analysis_settings(view):
    """Construit le frame 'Analyse' et le retourne."""
    # pylint: disable=too-many-locals
    frame = ttk.Frame(view.param_content_frame, style="Card.TFrame")
    create_setting_header(frame, "Paramètres d'Analyse Granulométrique")
    inner = tk.Frame(frame, bg=COLOR_CARD_BG, padx=40, pady=20)
    inner.pack(fill="both", expand=True)
    # Correction DNA
    dna_header = tk.Frame(inner, bg=COLOR_CARD_BG)
    dna_header.pack(fill="x", pady=(0, 10))
    tk.Label(
        dna_header,
        text="Correction de la courbe granulométrique",
        bg=COLOR_CARD_BG,
        fg="#111827",
        anchor="w",
        font=("Segoe UI", 11, "bold"),
    ).pack(side="left")
    add_tooltip(
        dna_header,
        "La correction compense les biais systématiques\n"
        "introduits par le système optique lors de la mesure des grains.\n\n"
        "Ces paramètres sont calculés automatiquement par le module\n"
        "'Modifier correction'.",
    ).pack(side="left")
    corr_frame = tk.Frame(inner, bg=COLOR_CARD_BG)
    corr_frame.pack(fill="x", pady=(5, 20))
    ttk.Checkbutton(
        corr_frame,
        text="Afficher la courbe corrigée",
        variable=view.app.show_corrected_curve_var,
        command=lambda: _update_curve_display(view),
    ).pack(anchor="w", pady=(0, 10))
    param_frame = tk.Frame(corr_frame, bg=COLOR_CARD_BG)
    param_frame.pack(fill="x", pady=(5, 0))
    tk.Label(
        param_frame,
        text="Paramètres de correction:",
        bg=COLOR_CARD_BG,
        font=("Segoe UI", 10, "bold"),
    ).pack(anchor="w", pady=(0, 5))
    params_grid = tk.Frame(param_frame, bg=COLOR_CARD_BG)
    params_grid.pack(fill="x", pady=(0, 10))
    scale_f = tk.Frame(params_grid, bg=COLOR_CARD_BG)
    scale_f.pack(side="left", padx=(0, 20))
    tk.Label(scale_f, text="Scale:", bg=COLOR_CARD_BG, font=("Segoe UI", 10)).pack(
        side="left"
    )
    tk.Label(
        scale_f,
        textvariable=view.app.correction_granulo["scale"],
        bg=COLOR_CARD_BG,
        font=("Segoe UI", 10, "bold"),
        fg=COLOR_ACCENT,
    ).pack(side="left", padx=(5, 0))
    offset_f = tk.Frame(params_grid, bg=COLOR_CARD_BG)
    offset_f.pack(side="left")
    tk.Label(offset_f, text="Offset:", bg=COLOR_CARD_BG, font=("Segoe UI", 10)).pack(
        side="left"
    )
    tk.Label(
        offset_f,
        textvariable=view.app.correction_granulo["offset"],
        bg=COLOR_CARD_BG,
        font=("Segoe UI", 10, "bold"),
        fg=COLOR_ACCENT,
    ).pack(side="left", padx=(5, 0))
    tk.Label(
        corr_frame,
        text="La correction applique une transformation linéaire\n"
        "aux tailles de tamis pour améliorer la précision des mesures.",
        bg=COLOR_CARD_BG,
        fg="#6b7280",
        font=("Segoe UI", 9, "italic"),
        justify="left",
    ).pack(anchor="w", pady=(5, 10))
    ttk.Separator(inner, orient="horizontal").pack(fill="x", pady=(5, 15))
    # Segmentation YOLO-OBB
    tk.Label(
        inner,
        text="Outil d'analyse des images",
        bg=COLOR_CARD_BG,
        fg="#111827",
        anchor="w",
        font=("Segoe UI", 11, "bold"),
    ).pack(fill="x", pady=(0, 10))

    def _get_base_dir():
        """chemin absolu vers le modele de yolo obb"""
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            return sys._MEIPASS  # pylint: disable=protected-access
        return os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )

    try:
        import ultralytics  # pylint: disable=unused-import,import-outside-toplevel

        _model_path = os.path.join(_get_base_dir(), "best.pt")
        yolo_available = os.path.isfile(_model_path)
    except ImportError:
        yolo_available = False
    yolo_status = "OPÉRATIONNEL" if yolo_available else "NON DISPONIBLE"
    yolo_color = "#10b981" if yolo_available else "#dc2626"
    status_frame = tk.Frame(inner, bg=COLOR_CARD_BG)
    status_frame.pack(fill="x", pady=(5, 0))
    tk.Label(
        status_frame, text="Statut: ", bg=COLOR_CARD_BG, font=("Segoe UI", 10)
    ).pack(side="left")
    tk.Label(
        status_frame,
        text=yolo_status,
        bg=COLOR_CARD_BG,
        fg=yolo_color,
        font=("Segoe UI", 10, "bold"),
    ).pack(side="left", padx=(5, 0))
    if not yolo_available:
        tk.Label(
            inner,
            text="Installez ultralytics et vérifiez le chemin du modèle best.pt",
            bg=COLOR_CARD_BG,
            fg="#dc2626",
            font=("Segoe UI", 9, "italic"),
            wraplength=400,
            justify="left",
        ).pack(anchor="w", pady=(5, 10))

    button_frame = tk.Frame(inner, bg=COLOR_CARD_BG)
    button_frame.pack(fill="x", pady=(10, 0))
    ttk.Separator(inner, orient="horizontal").pack(fill="x", pady=(10, 20))
    button_frame2 = tk.Frame(inner, bg=COLOR_CARD_BG)
    button_frame2.pack(fill="x")
    ttk.Button(
        button_frame2,
        text="Appliquer les paramètres",
        style="ParamAction.TButton",
        command=lambda: _apply_analysis_settings(view),
    ).pack(side="left")
    return frame


def _update_curve_display(view):
    """
    Mise à jour de l'affichage de la courbe granulométrique.

    Args:
        view: Vue principale de l'application.
    """
    if hasattr(view.app, "curve_view") and view.app.curve_view.frame.winfo_ismapped():
        view.app.curve_view._update_curve_view()  # pylint: disable=protected-access
    if view.app.capture_history and view.app.current_capture_index >= 0:
        capture = view.app.capture_history[view.app.current_capture_index]
        if len(capture.get("tamis_exp", [])) > 0:
            if hasattr(view.app, "measure_view"):
                view.app.measure_view._display_granulometric_curve(  # pylint: disable=protected-access
                    capture["tamis_exp"],
                    capture.get("cumulative_raw", []),
                    (
                        capture.get("cumulative_corrected", [])
                        if view.app.show_corrected_curve_var.get()
                        else None
                    ),
                )


def _apply_analysis_settings(view):
    """
    Applique les paramètres d'analyse.

    Args:
        view: Vue principale de l'application.
    """
    messagebox.showinfo(
        "Succès",
        f"Paramètres d'analyse appliqués :\n"
        f"- Correction DNA : "
        f"{'Activée' if view.app.show_corrected_curve_var.get() else 'Désactivée'}",
    )
