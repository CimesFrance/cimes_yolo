"""Boîte de dialogue d'activation de licence par fichier .lic."""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog
import webbrowser
import urllib.parse

from .machine_fingerprint import compute_fingerprint

ACTIVATION_EMAIL = "activation@cimes.fr"


class LicenseActivationDialog(tk.Tk):
    """Dialogue Tkinter demandant à l'utilisateur de sélectionner son fichier de licence."""

    def __init__(self, on_activate_callback=None):
        super().__init__()
        self.withdraw()  # Cacher la fenêtre pendant sa construction
        self.on_activate_callback = on_activate_callback
        self.result = False

        self.title("Activation de licence — CIMES")
        self.geometry("540x360")
        self.resizable(False, False)

        # Hack d'icône Windows pour la barre des tâches
        try:
            import ctypes

            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "cimes.license.activation.1.0"
            )
        except Exception:
            pass

        # Icône de l'application
        self._apply_icon()

        # Centrer la fenêtre sur l'écran
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"+{x}+{y}")

        # Style & Couleurs
        self.bg_color = "#2C3E50"  # COLOR_BG_DARK
        self.accent_color = "#F76F00"  # COLOR_ACCENT
        self.configure(bg=self.bg_color)

        # Empreinte machine
        try:
            self.machine_fp = compute_fingerprint()
        except Exception as exc:
            self.machine_fp = "ERREUR"

        self._create_widgets()
        self.deiconify()  # Afficher la fenêtre une fois prête

    def _apply_icon(self):
        """Cherche et applique l'icône de l'application."""
        try:
            from src.utils.file_manager import get_project_root

            icon_path = os.path.join(
                get_project_root(),
                "modules",
                "app_change_corr_params",
                "assets",
                "icons",
                "cimes-logo.ico",
            )
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
                self.wm_iconbitmap(default=icon_path)
        except Exception:
            pass

    def _create_widgets(self):
        # Frame principal avec marges
        main_frame = tk.Frame(self, bg=self.bg_color, padx=25, pady=25)
        main_frame.pack(fill="both", expand=True)

        # ── Titre principal ──────────────────────────────────────────────────
        title_label = tk.Label(
            main_frame,
            text="🔑 Activation de Licence",
            font=("Segoe UI", 16, "bold"),
            bg=self.bg_color,
            fg="white",
            anchor="w",
        )
        title_label.pack(fill="x", pady=(0, 10))

        # ── Message d'instruction ───────────────────────────────────────────
        msg_text = (
            "Cette machine n'a pas encore de licence active.\n"
            "Veuillez sélectionner le fichier de licence (.lic) que vous avez reçu par e-mail."
        )
        msg_label = tk.Label(
            main_frame,
            text=msg_text,
            font=("Segoe UI", 10),
            bg=self.bg_color,
            fg="#ECF0F1",
            justify="left",
            anchor="w",
        )
        msg_label.pack(fill="x", pady=(0, 15))

        # ── Cadre d'empreinte machine ────────────────────────────────────────
        fp_frame = tk.LabelFrame(
            main_frame,
            text=" Identifiant unique de cette machine ",
            font=("Segoe UI", 8, "bold"),
            bg=self.bg_color,
            fg=self.accent_color,
            bd=1,
            relief="solid",
        )
        fp_frame.pack(fill="x", pady=(0, 20), ipady=8, padx=1)

        # Ligne de contenu de l'identifiant
        fp_content = tk.Frame(fp_frame, bg=self.bg_color)
        fp_content.pack(fill="x", padx=10)

        self.fp_label = tk.Label(
            fp_content,
            text=self.machine_fp,
            font=("Consolas", 12, "bold"),
            bg=self.bg_color,
            fg="white",
            anchor="w",
        )
        self.fp_label.pack(side="left")

        # Bouton Copier l'empreinte
        self.copy_btn = tk.Button(
            fp_content,
            text="Copier",
            font=("Segoe UI", 8, "bold"),
            bg="#7F8C8D",
            fg="white",
            activebackground="#95A5A6",
            activeforeground="white",
            relief="flat",
            bd=0,
            command=self._copy_fingerprint,
            padx=10,
            pady=2,
            cursor="hand2",
        )
        self.copy_btn.pack(side="right")

        # Bouton Envoyer par e-mail
        self.mail_btn = tk.Button(
            fp_content,
            text="Envoyer par mail",
            font=("Segoe UI", 8, "bold"),
            bg="#7F8C8D",
            fg="white",
            activebackground="#95A5A6",
            activeforeground="white",
            relief="flat",
            bd=0,
            command=self._open_email,
            padx=10,
            pady=2,
            cursor="hand2",
        )
        self.mail_btn.pack(side="right", padx=(0, 6))

        # ── Message de statut dynamique (Erreur / Succès) ───────────────────
        self.status_label = tk.Label(
            main_frame,
            text="",
            font=("Segoe UI", 9, "bold"),
            bg=self.bg_color,
            fg="#E74C3C",
            anchor="w",
            wraplength=470,
        )
        self.status_label.pack(fill="x", pady=(0, 15))

        # ── Zone des boutons en bas ──────────────────────────────────────────
        btn_frame = tk.Frame(main_frame, bg=self.bg_color)
        btn_frame.pack(fill="x", side="bottom")

        # Bouton Quitter
        cancel_btn = tk.Button(
            btn_frame,
            text="Quitter",
            font=("Segoe UI", 10, "bold"),
            bg="#7F8C8D",
            fg="white",
            activebackground="#95A5A6",
            activeforeground="white",
            relief="flat",
            bd=0,
            command=self._on_cancel,
            padx=20,
            pady=6,
            cursor="hand2",
        )
        cancel_btn.pack(side="left")

        # Bouton Sélectionner et Activer
        self.activate_btn = tk.Button(
            btn_frame,
            text="Importer un fichier de licence (.lic)",
            font=("Segoe UI", 10, "bold"),
            bg=self.accent_color,
            fg="white",
            activebackground="#D35400",
            activeforeground="white",
            relief="flat",
            bd=0,
            command=self._on_select_file,
            padx=20,
            pady=6,
            cursor="hand2",
        )
        self.activate_btn.pack(side="right")

    def _copy_fingerprint(self):
        self.clipboard_clear()
        self.clipboard_append(self.machine_fp)
        self.update()
        self.copy_btn.config(text="Copié !")
        self.after(2000, lambda: self.copy_btn.config(text="Copier"))

    def _open_email(self):
        subject = urllib.parse.quote("Demande d'activation CIMES")
        body = urllib.parse.quote(
            f"Bonjour,\n\n"
            f"Je souhaite activer ma licence CIMES.\n\n"
            f"Identifiant machine : {self.machine_fp}\n\n"
            f"Cordialement,"
        )
        webbrowser.open(f"mailto:{ACTIVATION_EMAIL}?subject={subject}&body={body}")

    def _on_select_file(self):
        # Ouvrir le sélecteur de fichier
        lic_file = filedialog.askopenfilename(
            parent=self,
            title="Sélectionner le fichier de licence CIMES",
            filetypes=[("Fichiers de licence", "*.lic")],
        )

        if not lic_file:
            return

        self.status_label.config(
            text="Validation du fichier de licence en cours...", fg="#F1C40F"
        )
        self.update()

        self.activate_btn.config(state="disabled")
        self.after(100, self._perform_activation, lic_file)

    def _perform_activation(self, filepath):
        success, message = self.on_activate_callback(filepath)
        self.activate_btn.config(state="normal")

        if success:
            self.result = True
            self.status_label.config(
                text="Licence activée avec succès ! Démarrage...", fg="#2ECC71"
            )
            self.update()
            self.after(1000, self.destroy)
        else:
            self.status_label.config(text=message, fg="#E74C3C")

    def _on_cancel(self):
        self.result = False
        self.destroy()
