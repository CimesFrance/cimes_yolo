"""Envoi d'e-mail via la configuration SMTP définie dans les paramètres de transmission."""

import os
import json
import smtplib
import ssl
from email.message import EmailMessage
from tkinter import messagebox


def envoyer_email_rapport(
    destinataire,
    chemin_pdf,
    subject="Rapport de Granulométrie",
    body="Veuillez trouver ci-joint le rapport de granulométrie généré par l'application.",
):
    """
    Envoie un email avec le fichier PDF en pièce jointe.
    Utilise la configuration SMTP sauvegardée dans CIMES_Settings/report_configuration.json.
    """
    # 1. Chargement de la configuration SMTP
    config_path = os.path.join(
        os.path.expanduser("~"), "CIMES_Settings", "report_configuration.json"
    )
    if not os.path.isfile(config_path):
        messagebox.showerror(
            "Configuration manquante",
            "Aucune configuration mail trouvée.\n"
            "Veuillez renseigner les paramètres SMTP dans Paramètres → Transmission.",
        )
        return False

    try:
        with open(config_path, encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible de lire la configuration mail :\n{e}")
        return False

    sender_email = cfg.get("mail_sender", "").strip()
    app_password = cfg.get("mail_password", "").strip()
    smtp_server  = cfg.get("mail_server",  "").strip()
    smtp_port    = cfg.get("mail_port",    "587").strip()
    security     = cfg.get("mail_security", "none").lower()

    if not sender_email or not smtp_server:
        messagebox.showerror(
            "Configuration incomplète",
            "Le serveur mail ou l'expéditeur n'est pas configuré.\n"
            "Veuillez compléter les paramètres SMTP dans Paramètres → Transmission.",
        )
        return False

    try:
        port = int(smtp_port)
    except ValueError:
        port = 587

    # 2. Création de l'email
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"]    = sender_email
    msg["To"]      = destinataire
    msg.set_content(body)

    # 3. Attachement du PDF
    if os.path.isfile(chemin_pdf):
        try:
            with open(chemin_pdf, "rb") as f:
                pdf_data = f.read()
            msg.add_attachment(
                pdf_data,
                maintype="application",
                subtype="pdf",
                filename=os.path.basename(chemin_pdf),
            )
        except Exception as e:
            print(f"[EMAIL] Erreur attachement PDF : {e}")
            return False
    else:
        print(f"[EMAIL] Fichier PDF introuvable : {chemin_pdf}")
        return False

    # 4. Envoi via SMTP
    try:
        print(f"[EMAIL] Connexion à {smtp_server}:{port} (sécurité={security})...")

        if security == "ssl":
            ctx = ssl.create_default_context()
            with smtplib.SMTP_SSL(smtp_server, port, context=ctx) as server:
                if app_password:
                    server.login(sender_email, app_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(smtp_server, port) as server:
                if security == "tls":
                    server.starttls()
                if app_password:
                    server.login(sender_email, app_password)
                server.send_message(msg)

        print(f"[EMAIL] E-mail envoyé avec succès à {destinataire}")
        return True

    except smtplib.SMTPAuthenticationError:
        messagebox.showerror(
            "Erreur d'authentification",
            "Mot de passe incorrect ou accès refusé par le serveur SMTP.\n"
            "Vérifiez l'expéditeur et le mot de passe dans les paramètres.",
        )
        return False
    except Exception as e:
        messagebox.showerror("Erreur d'envoi", f"Erreur lors de l'envoi :\n{e}")
        return False
