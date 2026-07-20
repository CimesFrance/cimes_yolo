"""Paramètres de transmission : configuration SMTP et rapport PDF."""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os

from src.ui.widgets.ui_utils import COLOR_CARD_BG, create_setting_header, add_tooltip
from src.utils.email_sender import envoyer_email_rapport


def create_transmission_settings(view):
    """Construit le frame 'Transmission' et le retourne."""
    # pylint: disable=too-many-statements,too-many-locals
    frame = ttk.Frame(view.param_content_frame, style="Card.TFrame")
    create_setting_header(frame, "Configuration de la messagerie")
    inner = tk.Frame(frame, bg=COLOR_CARD_BG, padx=40, pady=20)
    inner.pack(fill="both", expand=True)

    # ── Nom du poste ──────────────────────────────────────────────────────────
    poste_row = tk.Frame(inner, bg=COLOR_CARD_BG)
    poste_row.pack(fill="x", pady=(0, 14))
    tk.Label(
        poste_row,
        text="Nom du poste",
        bg=COLOR_CARD_BG,
        fg="#111827",
        font=("Segoe UI", 10, "bold"),
        width=16,
        anchor="w",
    ).pack(side="left")
    ttk.Entry(
        poste_row,
        textvariable=view.app.mail_poste_var,
        width=40,
        font=("Segoe UI", 10),
    ).pack(side="left")

    ttk.Separator(inner, orient="horizontal").pack(fill="x", pady=(4, 14))

    # ── Mode d'envoi ──────────────────────────────────────────────────────────
    mode_frame = tk.Frame(inner, bg=COLOR_CARD_BG)
    mode_frame.pack(fill="x", pady=(0, 14))
    ttk.Radiobutton(
        mode_frame,
        text="Pas de mail",
        value="none",
        variable=view.app.mail_mode_var,
        command=lambda: _toggle_smtp_block(view),
    ).pack(side="left", padx=(0, 20))
    ttk.Radiobutton(
        mode_frame,
        text="Mail d'erreur",
        value="error",
        variable=view.app.mail_mode_var,
        command=lambda: _toggle_smtp_block(view),
    ).pack(side="left", padx=(0, 20))
    ttk.Radiobutton(
        mode_frame,
        text="Erreur + Résultat",
        value="error_result",
        variable=view.app.mail_mode_var,
        command=lambda: _toggle_smtp_block(view),
    ).pack(side="left")

    # ── Options rapport PDF ───────────────────────────────────────────────────
    tk.Label(
        inner,
        text="Configuration du rapport PDF",
        bg=COLOR_CARD_BG,
        fg="#111827",
        anchor="w",
        font=("Segoe UI", 11, "bold"),
    ).pack(fill="x", pady=(0, 10))

    options_grid = tk.Frame(inner, bg=COLOR_CARD_BG)
    options_grid.pack(fill="x", pady=(0, 12))
    col1 = tk.Frame(options_grid, bg=COLOR_CARD_BG)
    col1.pack(side="left", fill="both", expand=True)
    ttk.Checkbutton(
        col1,
        text="Image capturée",
        variable=view.app.report_options["include_captured_image"],
    ).pack(anchor="w", pady=2)
    ttk.Checkbutton(
        col1,
        text="Image segmentée",
        variable=view.app.report_options["include_segmented_image"],
    ).pack(anchor="w", pady=2)
    ttk.Checkbutton(
        col1,
        text="Courbe granulométrique",
        variable=view.app.report_options["include_granulometric_curve"],
    ).pack(anchor="w", pady=2)
    col2 = tk.Frame(options_grid, bg=COLOR_CARD_BG)
    col2.pack(side="left", fill="both", expand=True, padx=(20, 0))
    ttk.Checkbutton(
        col2,
        text="Courbe de distribution",
        variable=view.app.report_options["include_distribution_curve"],
    ).pack(anchor="w", pady=2)
    ttk.Checkbutton(
        col2,
        text="Tableau statistique",
        variable=view.app.report_options["include_statistics"],
    ).pack(anchor="w", pady=2)
    ttk.Checkbutton(
        col2,
        text="Courbe corrigée",
        variable=view.app.show_corrected_curve_var,
    ).pack(anchor="w", pady=2)

    # Zone commentaire
    comment_frame = tk.Frame(inner, bg=COLOR_CARD_BG)
    comment_frame.pack(fill="x", pady=(10, 10))
    tk.Label(
        comment_frame,
        text="Commentaire (optionnel)",
        bg=COLOR_CARD_BG,
        fg="#4b5563",
        font=("Segoe UI", 10, "bold"),
    ).pack(anchor="w")
    view.comment_text = tk.Text(
        comment_frame,
        height=4,
        font=("Segoe UI", 10),
        relief="solid",
        bd=1,
        highlightbackground="#d1d5db",
        highlightcolor="#3b82f6",
        highlightthickness=1,
        padx=8,
        pady=8,
    )
    view.comment_text.pack(fill="x", pady=(5, 0))
    if view.app.report_options["custom_comment"].get():
        view.comment_text.insert("1.0", view.app.report_options["custom_comment"].get())

    # ── Bloc SMTP d'envoi du mail (visible seulement si mode != none) ─────────────────────────
    view.smtp_block = tk.Frame(
        inner,
        bg="#f9fafb",
        bd=1,
        relief="solid",
    )
    view.smtp_block.pack(fill="x", pady=(0, 16))

    smtp_inner = tk.Frame(view.smtp_block, bg="#f9fafb", padx=14, pady=12)
    smtp_inner.pack(fill="x")

    def _smtp_row(label_text, var, show=False, tooltip_text=None):
        """Crée une ligne label + Entry dans le bloc SMTP."""
        row = tk.Frame(smtp_inner, bg="#f9fafb")
        row.pack(fill="x", pady=4)
        lbl = tk.Label(
            row,
            text=label_text,
            bg="#f9fafb",
            fg="#374151",
            font=("Segoe UI", 10),
            width=16,
            anchor="w",
        )
        lbl.pack(side="left")
        if tooltip_text:
            add_tooltip(lbl, tooltip_text)
        entry = ttk.Entry(
            row,
            textvariable=var,
            width=46,
            font=("Segoe UI", 10),
            show="*" if show else "",
        )
        entry.pack(side="left")
        return entry

    _smtp_row(
        "Destinataires",
        view.app.mail_recipients_var,
        tooltip_text=(
            "Adresses e-mail séparées par un point-virgule ;\n"
            "Ex : alice@societe.fr;bob@societe.fr"
        ),
    )
    _smtp_row("Serveur mail", view.app.mail_server_var)
    _smtp_row("Port", view.app.mail_port_var)
    _smtp_row("Expéditeur", view.app.mail_sender_var)
    _smtp_row("Mot de passe", view.app.mail_password_var, show=True)

    # Sécurité : SSL / TLS / Aucune
    sec_row = tk.Frame(smtp_inner, bg="#f9fafb")
    sec_row.pack(fill="x", pady=(8, 2))
    tk.Label(
        sec_row,
        text="Sécurité",
        bg="#f9fafb",
        fg="#374151",
        font=("Segoe UI", 10),
        width=16,
        anchor="w",
    ).pack(side="left")
    for lbl_text, val in [("SSL", "ssl"), ("TLS", "tls"), ("Aucune", "none")]:
        ttk.Radiobutton(
            sec_row,
            text=lbl_text,
            value=val,
            variable=view.app.mail_security_var,
        ).pack(side="left", padx=(0, 14))

    # ── Boutons Sauvegarder / Envoyer ─────────────────────────────────────────
    btn_row = tk.Frame(inner, bg=COLOR_CARD_BG)
    view.btn_row = btn_row
    btn_row.pack(pady=(0, 10))
    ttk.Button(
        btn_row,
        text="Sauvegarder",
        style="ParamSave.TButton",
        command=lambda: _save_transmission_config(view),
    ).pack(side="left", padx=(0, 10))
    ttk.Button(
        btn_row,
        text=" Envoyer",
        style="ParamAction.TButton",
        command=lambda: _send_email(view),
    ).pack(side="left")

    # Init affichage du bloc SMTP
    _toggle_smtp_block(view)

    # Charger la config sauvegardée
    _load_transmission_config(view)

    return frame


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _toggle_smtp_block(view):
    """Affiche/masque le bloc SMTP selon le mode sélectionné."""
    if view.app.mail_mode_var.get() == "none":
        view.smtp_block.pack_forget()
    else:
        view.smtp_block.pack(fill="x", pady=(0, 16), before=view.btn_row)


def _save_transmission_config(view):
    """Valide et sauvegarde la configuration de transmission."""
    mode = view.app.mail_mode_var.get()

    if mode != "none":
        if not view.app.mail_recipients_var.get().strip():
            messagebox.showerror(
                "Erreur", "Veuillez renseigner au moins un destinataire."
            )
            return
        if not view.app.mail_server_var.get().strip():
            messagebox.showerror(
                "Erreur", "Veuillez renseigner l'adresse du serveur mail."
            )
            return
        if not view.app.mail_sender_var.get().strip():
            messagebox.showerror(
                "Erreur", "Veuillez renseigner l'adresse de l'expéditeur."
            )
            return

    comment = view.comment_text.get("1.0", tk.END).strip()
    view.app.report_options["custom_comment"].set(comment)

    config = {
        # Mail
        "mail_poste": view.app.mail_poste_var.get(),
        "mail_mode": view.app.mail_mode_var.get(),
        "mail_recipients": view.app.mail_recipients_var.get(),
        "mail_server": view.app.mail_server_var.get(),
        "mail_port": view.app.mail_port_var.get(),
        "mail_sender": view.app.mail_sender_var.get(),
        "mail_password": view.app.mail_password_var.get(),
        "mail_security": view.app.mail_security_var.get(),
        # Rapport
        "include_captured_image": view.app.report_options[
            "include_captured_image"
        ].get(),
        "include_segmented_image": view.app.report_options[
            "include_segmented_image"
        ].get(),
        "include_granulometric_curve": view.app.report_options[
            "include_granulometric_curve"
        ].get(),
        "include_distribution_curve": view.app.report_options[
            "include_distribution_curve"
        ].get(),
        "include_statistics": view.app.report_options["include_statistics"].get(),
        "custom_comment": comment,
        "dna_correction_enabled": view.app.show_corrected_curve_var.get(),
    }

    try:
        save_dir = os.path.join(os.path.expanduser("~"), "CIMES_Settings")
        os.makedirs(save_dir, exist_ok=True)
        with open(
            os.path.join(save_dir, "report_configuration.json"), "w", encoding="utf-8"
        ) as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        messagebox.showinfo("Succès", "Configuration sauvegardée avec succès !")
    except Exception as e:  # pylint: disable=broad-exception-caught
        messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde : {str(e)}")


def _load_transmission_config(view):
    """Charge la configuration SMTP depuis le fichier JSON si présent."""
    config_path = os.path.join(
        os.path.expanduser("~"), "CIMES_Settings", "report_configuration.json"
    )
    if not os.path.isfile(config_path):
        return
    try:
        with open(config_path, encoding="utf-8") as f:
            cfg = json.load(f)

        view.app.mail_poste_var.set(cfg.get("mail_poste", ""))
        view.app.mail_mode_var.set(cfg.get("mail_mode", "none"))
        view.app.mail_recipients_var.set(cfg.get("mail_recipients", ""))
        view.app.mail_server_var.set(cfg.get("mail_server", ""))
        view.app.mail_port_var.set(cfg.get("mail_port", "587"))
        view.app.mail_sender_var.set(cfg.get("mail_sender", ""))
        view.app.mail_password_var.set(cfg.get("mail_password", ""))
        view.app.mail_security_var.set(cfg.get("mail_security", "none"))

        for key in (
            "include_captured_image",
            "include_segmented_image",
            "include_granulometric_curve",
            "include_distribution_curve",
            "include_statistics",
        ):
            if key in cfg:
                view.app.report_options[key].set(cfg[key])

        if "dna_correction_enabled" in cfg:
            view.app.show_corrected_curve_var.set(cfg["dna_correction_enabled"])

        comment = cfg.get("custom_comment", "")
        view.app.report_options["custom_comment"].set(comment)
        if comment and hasattr(view, "comment_text"):
            view.comment_text.delete("1.0", tk.END)
            view.comment_text.insert("1.0", comment)

        _toggle_smtp_block(view)
    except Exception:  # pylint: disable=broad-exception-caught
        pass  # Config corrompue → valeurs par défaut


def _send_email(view):
    """Envoie un e-mail de rapport au(x) destinataire(s) configuré(s)."""
    mode = view.app.mail_mode_var.get()
    if mode == "none":
        messagebox.showwarning(
            "Envoi désactivé",
            "Le mode d'envoi est réglé sur 'Pas de mail'.\n"
            "Sélectionnez 'Mail d'erreur' ou 'Erreur + Résultat' pour activer l'envoi.",
        )
        return

    recipients_raw = view.app.mail_recipients_var.get().strip()
    if not recipients_raw:
        messagebox.showerror("Erreur", "Veuillez renseigner au moins un destinataire.")
        return

    # Récupérer le dernier PDF généré si disponible
    pdf_path = getattr(view.app, "last_pdf_path", None)
    if not pdf_path or not os.path.isfile(pdf_path):
        results_dir = view.app.results_path_var.get()
        pdf_path = _find_latest_pdf(results_dir)

    if not pdf_path:
        messagebox.showerror(
            "Aucun rapport",
            "Aucun rapport PDF trouvé.\n"
            "Générez d'abord un rapport depuis la vue Courbes.",
        )
        return

    # Sauvegarder la config avant d'envoyer
    _save_transmission_config(view)

    # Envoyer à chaque destinataire
    recipients = [
        r.strip() for r in recipients_raw.replace(";", ",").split(",") if r.strip()
    ]
    success_count = 0
    for recipient in recipients:
        ok = envoyer_email_rapport(
            destinataire=recipient,
            chemin_pdf=pdf_path,
            subject=f"Rapport CIMES — {view.app.mail_poste_var.get() or 'Poste'}",
            body=(
                "Veuillez trouver ci-joint le rapport de granulométrie généré par CIMES.\n"
                f"Poste : {view.app.mail_poste_var.get() or 'N/A'}\n"
            ),
        )
        if ok:
            success_count += 1

    if success_count == len(recipients):
        messagebox.showinfo(
            "Envoi réussi",
            f"E-mail envoyé avec succès à {success_count} destinataire(s).",
        )
    elif success_count > 0:
        messagebox.showwarning(
            "Envoi partiel",
            f"{success_count}/{len(recipients)} e-mail(s) envoyé(s).",
        )


def _find_latest_pdf(directory):
    """Retourne le chemin du PDF le plus récent dans le répertoire donné."""
    if not os.path.isdir(directory):
        return None
    pdfs = []
    for root, _, files in os.walk(directory):
        for fname in files:
            if fname.lower().endswith(".pdf"):
                pdfs.append(os.path.join(root, fname))
    if not pdfs:
        return None
    return max(pdfs, key=os.path.getmtime)
