"""Boîte de dialogue d'activation de licence."""

import tkinter as tk
from tkinter import ttk
import os

class LicenseActivationDialog(tk.Tk):
    def __init__(self, mac_address, on_activate_callback):
        super().__init__()
        self.withdraw()  # Cacher la fenêtre pendant sa construction
        self.mac_address = mac_address
        self.on_activate_callback = on_activate_callback
        self.result = False
        
        self.title("Activation de licence — CIMES")
        self.geometry("520x350")
        self.resizable(False, False)
        
        # Icône de l'application
        try:
            from src.utils.file_manager import get_project_root
            icon_path = os.path.join(get_project_root(), "assets", "icons", "cimes-logo.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path, default=icon_path)
            else:
                # Tentative avec le chemin fourni dans l'exemple
                icon_path = os.path.join(get_project_root(), "modules", "app_change_corr_params", "assets", "icons", "cimes-logo.ico")
                self.iconbitmap(icon_path, default=icon_path)
        except Exception:
            pass
            
        # Centrer la fenêtre sur l'écran
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"+{x}+{y}")
        
        # Styles et Couleurs
        self.bg_color = "#2C3E50"  # COLOR_BG_DARK
        self.accent_color = "#F76F00"  # COLOR_ACCENT
        self.configure(bg=self.bg_color)
        
        self._create_widgets()
        self.deiconify()  # Afficher la fenêtre une fois qu'elle est prête
        
    def _create_widgets(self):
        # Frame principal avec marges
        main_frame = tk.Frame(self, bg=self.bg_color, padx=25, pady=25)
        main_frame.pack(fill="both", expand=True)
        
        # Titre principal
        title_label = tk.Label(
            main_frame,
            text="🔑 Activation de Licence",
            font=("Segoe UI", 16, "bold"),
            bg=self.bg_color,
            fg="white",
            anchor="w"
        )
        title_label.pack(fill="x", pady=(0, 15))
        
        # Message informatif
        msg_text = (
            "Cette machine n'a pas encore de licence active.\n"
            "Veuillez saisir votre clé de licence reçue par email pour activer l'application."
        )
        msg_label = tk.Label(
            main_frame,
            text=msg_text,
            font=("Segoe UI", 10),
            bg=self.bg_color,
            fg="#ECF0F1",
            justify="left",
            anchor="w"
        )
        msg_label.pack(fill="x", pady=(0, 15))
        
        # Label de saisie clé
        key_label = tk.Label(
            main_frame,
            text="Clé de licence (ex: CIMES-XXXX-YYYY-ZZZZ) :",
            font=("Segoe UI", 10, "bold"),
            bg=self.bg_color,
            fg="#ECF0F1",
            anchor="w"
        )
        key_label.pack(fill="x", pady=(0, 5))
        
        # Champ d'entrée moderne
        self.key_entry = tk.Entry(
            main_frame,
            font=("Consolas", 11),
            bg="white",
            fg="#2C3E50",
            bd=1,
            relief="solid",
            insertbackground="#2C3E50"
        )
        self.key_entry.pack(fill="x", ipady=6, pady=(0, 10))
        self.key_entry.focus_set()
        
        # Message de statut dynamique (Erreur / Succès / Info)
        self.status_label = tk.Label(
            main_frame,
            text="",
            font=("Segoe UI", 9, "bold"),
            bg=self.bg_color,
            fg="#E74C3C",
            anchor="w",
            wraplength=470
        )
        self.status_label.pack(fill="x", pady=(0, 15))
        
        # Zone des boutons en bas
        btn_frame = tk.Frame(main_frame, bg=self.bg_color)
        btn_frame.pack(fill="x", side="bottom")
        
        # Bouton Annuler / Quitter
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
            cursor="hand2"
        )
        cancel_btn.pack(side="left")
        
        # Bouton Activer
        self.activate_btn = tk.Button(
            btn_frame,
            text="Activer l'application",
            font=("Segoe UI", 10, "bold"),
            bg=self.accent_color,
            fg="white",
            activebackground="#D35400",
            activeforeground="white",
            relief="flat",
            bd=0,
            command=self._on_activate,
            padx=20,
            pady=6,
            cursor="hand2"
        )
        self.activate_btn.pack(side="right")
        
    def _on_activate(self):
        key = self.key_entry.get().strip()
        if not key:
            self.status_label.config(text="Veuillez saisir une clé de licence.", fg="#E74C3C")
            return
            
        self.status_label.config(text="Validation de la clé en cours...", fg="#F1C40F")
        self.update()
        
        # On désactive les boutons pendant la validation
        self.activate_btn.config(state="disabled")
        
        # Appel asynchrone pour ne pas bloquer l'UI
        self.after(100, self._perform_activation, key)
        
    def _perform_activation(self, key):
        success, message = self.on_activate_callback(key)
        
        self.activate_btn.config(state="normal")
        
        if success:
            self.result = True
            # Montrer un message de succès temporaire
            self.status_label.config(text="Licence activée avec succès ! Démarrage...", fg="#2ECC71")
            self.update()
            self.after(1000, self.destroy)
        else:
            self.status_label.config(text=message, fg="#E74C3C")
            
    def _on_cancel(self):
        self.result = False
        self.destroy()
