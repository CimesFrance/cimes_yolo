"""
CIMES — Outil d'activation
Distribué avec l'installeur CIMES pour permettre au client d'obtenir
son empreinte machine et de l'envoyer à CimesFrance pour recevoir sa licence.

Peut être compilé en machine_id.exe via PyInstaller :
    python tools/build_machine_id.py
"""

import ctypes
import os
import sys
import tkinter as tk
import urllib.parse
import webbrowser

# Ajoute le dossier racine du projet au path pour accéder aux modules src
_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_script_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.license.machine_fingerprint import get_fingerprint_details  # noqa: E402

ACTIVATION_EMAIL = "activation@cimes.fr"


class MachineIdDialog(tk.Tk):
    """Interface d'obtention de l'empreinte machine."""

    def __init__(self):
        super().__init__()
        self.withdraw()  # Cacher la fenêtre pendant sa construction

        self.title("Activation de licence — CIMES")
        self.geometry("540x310")
        self.resizable(False, False)

        # Icône de l'application
        self._apply_icon()

    def _apply_icon(self):
        """Applique l'icône cimes-logo.ico sur la fenêtre et la barre des tâches."""
        icon_path = _find_icon_path()
        if icon_path:
            try:
                self.iconbitmap(icon_path)
                self.wm_iconbitmap(default=icon_path)
            except Exception as e:
                print(f"[Avertissement] iconbitmap a échoué : {e}")
        else:
            print("[Avertissement] cimes-logo.ico introuvable dans aucun emplacement connu.")

        # Centrer la fenêtre sur l'écran
        self.update_idletasks()
        x = (self.winfo_screenwidth()  // 2) - (540 // 2)
        y = (self.winfo_screenheight() // 2) - (310 // 2)
        self.geometry(f"+{x}+{y}")

        # Couleurs charte graphique CIMES
        self.bg_color     = "#2C3E50"
        self.accent_color = "#F76F00"
        self.configure(bg=self.bg_color)

        # Chargement de l'empreinte
        try:
            self._details = get_fingerprint_details()
        except Exception as exc:  # pylint: disable=broad-except
            self._details = {
                "fingerprint": "ERREUR",
                "disk_uuid":   str(exc),
                "cpu_id":      "—",
                "hostname":    "—",
            }

        self._create_widgets()
        self.deiconify()  # Afficher la fenêtre une fois prête

    def _create_widgets(self):
        # Frame principal avec marges
        main_frame = tk.Frame(self, bg=self.bg_color, padx=25, pady=25)
        main_frame.pack(fill="both", expand=True)

        # Titre principal 
        tk.Label(
            main_frame,
            text="🔑 Activation de Licence",
            font=("Segoe UI", 16, "bold"),
            bg=self.bg_color,
            fg="white",
            anchor="w",
        ).pack(fill="x", pady=(0, 15))

        # Message informatif 
        tk.Label(
            main_frame,
            text=(
                "Envoyez l'identifiant ci-dessous à CimesFrance pour recevoir votre fichier de licence."
            ),
            font=("Segoe UI", 10),
            bg=self.bg_color,
            fg="#ECF0F1",
            justify="left",
            anchor="w",
        ).pack(fill="x", pady=(0, 15))

        # Label de l'empreinte
        tk.Label(
            main_frame,
            text=f"Identifiant machine à envoyer à {ACTIVATION_EMAIL} :",
            font=("Segoe UI", 10, "bold"),
            bg=self.bg_color,
            fg="#ECF0F1",
            anchor="w",
        ).pack(fill="x", pady=(0, 5))

        # Champ empreinte 
        fp_var = tk.StringVar(value=self._details["fingerprint"])
        self.fp_entry = tk.Entry(
            main_frame,
            textvariable=fp_var,
            font=("Consolas", 14, "bold"),
            bg="white",
            fg="#2C3E50",
            bd=1,
            relief="solid",
            state="readonly",
            readonlybackground="white",
            justify="center",
        )
        self.fp_entry.pack(fill="x", ipady=8, pady=(0, 6))

        # Message de statut
        self.status_label = tk.Label(
            main_frame,
            text="",
            font=("Segoe UI", 9, "bold"),
            bg=self.bg_color,
            fg="#2ECC71",
            anchor="w",
        )
        self.status_label.pack(fill="x", pady=(4, 0))

        # Zone des boutons en bas
        btn_frame = tk.Frame(main_frame, bg=self.bg_color)
        btn_frame.pack(fill="x", side="bottom")

        # Bouton Copier
        self.copy_btn = tk.Button(
            btn_frame,
            text="Copier l'identifiant",
            font=("Segoe UI", 10, "bold"),
            bg=self.accent_color,
            fg="white",
            activebackground="#D35400",
            activeforeground="white",
            relief="flat",
            bd=0,
            command=self._copy_to_clipboard,
            padx=20,
            pady=6,
            cursor="hand2",
        )
        self.copy_btn.pack(side="left", padx=(0, 8))

        # Bouton Envoyer par e-mail
        tk.Button(
            btn_frame,
            text="Envoyer par e-mail",
            font=("Segoe UI", 10, "bold"),
            bg="#7F8C8D",
            fg="white",
            activebackground="#95A5A6",
            activeforeground="white",
            relief="flat",
            bd=0,
            command=self._open_email,
            padx=20,
            pady=6,
            cursor="hand2",
        ).pack(side="left")

    # Actions
    def _copy_to_clipboard(self) -> None:
        self.clipboard_clear()
        self.clipboard_append(self._details["fingerprint"])
        self.update()
        self.status_label.config(text="Identifiant copié dans le presse-papiers !", fg="#D35400")
        self.copy_btn.config(text="Copié !")
        self.after(2500, lambda: (
            self.copy_btn.config(text="Copier l'identifiant"),
            self.status_label.config(text=""),
        ))

    def _open_email(self) -> None:
        subject = urllib.parse.quote("Demande d'activation CIMES")
        body    = urllib.parse.quote(
            f"Bonjour,\n\n"
            f"Je souhaite activer ma licence CIMES.\n\n"
            f"Identifiant machine : {self._details['fingerprint']}\n"
        )
        webbrowser.open(f"mailto:{ACTIVATION_EMAIL}?subject={subject}&body={body}")
        self.status_label.config(
            text=f"Client e-mail ouvert. Envoyez le message à {ACTIVATION_EMAIL}.",
            fg="#D35400",
        )


# ─────────────────────────────────────────────────────────────────────────────
#  Point d'entrée
# ─────────────────────────────────────────────────────────────────────────────

def _find_icon_path():
    """Cherche le fichier cimes-logo.ico dans plusieurs emplacements."""
    candidates = []
    # Si exe compilé PyInstaller
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        candidates.append(os.path.join(exe_dir, "cimes-logo.ico"))
        if hasattr(sys, '_MEIPASS'):
            candidates.append(os.path.join(sys._MEIPASS, "cimes-logo.ico"))
    # En développement
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    candidates.append(os.path.join(project_root, "modules", "app_change_corr_params", "assets", "icons", "cimes-logo.ico"))
    candidates.append(os.path.join(project_root, "assets", "icons", "cimes-logo.ico"))
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


def main() -> None:
    # CRITIQUE : doit être appelé AVANT toute création de fenêtre Tk
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("cimes.license.activation.1.0")
    except Exception:
        pass

    app = MachineIdDialog()
    app.mainloop()


if __name__ == "__main__":
    main()
