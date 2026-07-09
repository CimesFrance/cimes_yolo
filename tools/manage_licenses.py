"""
Script CLI d'administration des licences CIMES.
Permet d'ajouter, consulter et révoquer des licences via le serveur Flask.

Usage :
    python tools/manage_licenses.py add    --mac 48:89:e7:d5:fc:87 --key CIMES-XXXX-YYYY-ZZZZ --expires 2027-12-31
    python tools/manage_licenses.py check  --mac 48:89:e7:d5:fc:87
    python tools/manage_licenses.py revoke --mac 48:89:e7:d5:fc:87

"""

import argparse
import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

# Configuration au serveur
_root = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=_root / ".env", override=False)

SERVER_URL = os.environ.get("LICENSE_SERVER_URL", "http://localhost:5000").rstrip("/")
API_KEY = os.environ.get("API_SECRET_KEY", "changeme")

HEADERS = {
    "X-API-KEY": API_KEY,
    "Content-Type": "application/json",
}


# Helpers
def _print_response(resp: requests.Response) -> None:
    """Affiche la réponse JSON de manière lisible."""
    try:
        data = resp.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception:  # pylint: disable=broad-except
        print(resp.text)


def _normalize_mac(mac: str) -> str:
    """Normalise l'adresse MAC."""
    return mac.strip().lower().replace("-", ":").replace(".", ":")

# Commandes
def cmd_add(args: argparse.Namespace) -> None:
    """Ajoute ou met à jour une licence."""
    mac = _normalize_mac(args.mac)
    payload = {
        "mac": mac,
        "license_key": args.key,
        "expires": args.expires,
    }
    print(f"Ajout de la licence pour {mac}...")
    resp = requests.post(f"{SERVER_URL}/add-license", json=payload, headers=HEADERS, timeout=10)
    _print_response(resp)


def cmd_check(args: argparse.Namespace) -> None:
    """Vérifie une licence."""
    mac = _normalize_mac(args.mac)
    print(f"Vérification de la licence pour {mac}...")
    resp = requests.post(f"{SERVER_URL}/check-license", json={"mac": mac}, headers=HEADERS, timeout=10)
    data = resp.json()

    valid = data.get("valid", False)
    icon = "✅" if valid else "❌"
    print(f"\n{icon} Statut       : {'Valide' if valid else 'Invalide'}")
    print(f"   Clé          : {data.get('license_key') or 'N/A'}")
    print(f"   Expiration   : {data.get('expires') or 'N/A'}")
    print(f"   Jours restants: {data.get('days_remaining', 'N/A')}")
    print(f"   Message      : {data.get('message', '')}")


def cmd_revoke(args: argparse.Namespace) -> None:
    """Révoque une licence."""
    mac = _normalize_mac(args.mac)
    print(f"Révocation de la licence pour {mac}...")
    resp = requests.delete(
        f"{SERVER_URL}/revoke-license",
        json={"mac": mac},
        headers=HEADERS,
        timeout=10,
    )
    _print_response(resp)

# Parseur d'arguments
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="manage_licenses",
        description="Administration des licences CIMES via l'API Flask.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- add ---
    add_parser = subparsers.add_parser("add", help="Ajouter ou mettre à jour une licence")
    add_parser.add_argument("--mac",     required=True, help="Adresse MAC")
    add_parser.add_argument("--key",     required=True, help="Clé de licence")
    add_parser.add_argument("--expires", required=True, help="Date d'expiration")

    # --- check ---
    check_parser = subparsers.add_parser("check", help="Vérifier une licence par MAC")
    check_parser.add_argument("--mac", required=True, help="Adresse MAC à vérifier")

    # --- revoke ---
    revoke_parser = subparsers.add_parser("revoke", help="Révoquer une licence")
    revoke_parser.add_argument("--mac", required=True, help="Adresse MAC à révoquer")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.command == "add":
            cmd_add(args)
        elif args.command == "check":
            cmd_check(args)
        elif args.command == "revoke":
            cmd_revoke(args)
    except requests.exceptions.ConnectionError:
        print(f"Impossible de joindre le serveur : {SERVER_URL}")
        print("Vérifiez que le serveur Flask est démarré et que LICENSE_SERVER_URL est correct.")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print("Délai d'attente dépassé.")
        sys.exit(1)


if __name__ == "__main__":
    main()
