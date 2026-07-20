"""
Script de génération de licence CIMES.

Génère un fichier de licence '.lic' chiffré/signé cryptographiquement en RSA.
Ce fichier contient la liste des empreintes machine autorisées pour le multi-poste.

Usage :
    python tools/issue_license.py --client "Carriere Martin" --fingerprints "A3F2-9C7B-E401-5D88,B7C1-4D2A-F908-3E55" --max-postes 3 --expires 2027-07-16 --output CIMES_Martin.lic
"""

import argparse
from datetime import datetime
import json
import os
import sys

try:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives.serialization import load_pem_private_key
except ImportError:
    print("[ERREUR] Le paquet 'cryptography' est requis.")
    print("uv add cryptography")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Générateur de licences CIMES")
    parser.add_argument("--client", required=True, help="Nom de l'entreprise cliente")
    parser.add_argument(
        "--fingerprints",
        required=True,
        help="Liste d'empreintes machine séparées par des virgules",
    )
    parser.add_argument(
        "--max-postes", type=int, default=1, help="Nombre maximal de postes autorisés"
    )
    parser.add_argument(
        "--expires", required=True, help="Date d'expiration au format YYYY-MM-DD"
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Nom ou chemin du fichier de licence généré (.lic)",
    )
    parser.add_argument(
        "--private-key",
        default="keys/private_key.pem",
        help="Chemin vers la clé privée PEM",
    )

    args = parser.parse_args()

    # 1. Valider la clé privée
    if not os.path.exists(args.private_key):
        print(f"[ERREUR] Clé privée introuvable à : {args.private_key}")
        print("         Générez-en une d'abord avec : python tools/generate_keypair.py")
        sys.exit(1)

    # 2. Valider la date d'expiration
    try:
        expires_date = datetime.strptime(args.expires, "%Y-%m-%d")
        expires_str = expires_date.strftime("%Y-%m-%d")
    except ValueError:
        print("[ERREUR] La date d'expiration doit être au format YYYY-MM-DD.")
        sys.exit(1)

    # 3. Préparer les empreintes, suppression des espaces et conversion en majuscules
    fps = [fp.strip().upper() for fp in args.fingerprints.split(",") if fp.strip()]
    if not fps:
        print("[ERREUR] Vous devez spécifier au moins une empreinte machine valide.")
        sys.exit(1)

    if len(fps) > args.max_postes:
        print(
            f"[AVERTISSEMENT] Le nombre d'empreintes fournies ({len(fps)}) dépasse le max-postes ({args.max_postes})."
        )

    # 4. Charger la clé privée RSA
    try:
        with open(args.private_key, "rb") as key_file:
            private_key = load_pem_private_key(key_file.read(), password=None)
    except Exception as e:
        print(f"[ERREUR] Échec du chargement de la clé privée : {e}")
        sys.exit(1)

    # 5. Construire les données de licence
    license_data = {
        "client": args.client,
        "fingerprints": fps,
        "max_postes": args.max_postes,
        "expires_at": expires_str,
        "issued_at": datetime.now().strftime("%Y-%m-%d"),
    }

    # 6. Sérialiser les données de manière canonique (tri des clés) pour la signature
    canonical_data = json.dumps(license_data, sort_keys=True)

    # 7. Signer numériquement les données avec la clé privée RSA
    try:
        signature = private_key.sign(
            canonical_data.encode("utf-8"),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256(),
        )
    except Exception as e:
        print(f"[ERREUR] Échec de la signature des données : {e}")
        sys.exit(1)

    # 8. Ajouter la signature encodée en hexadécimal dans le fichier final
    license_data["signature"] = signature.hex()

    # 9. Sauvegarder le fichier de licence au format JSON
    try:
        with open(args.output, "w", encoding="utf-8") as lic_file:
            json.dump(license_data, lic_file, indent=4, ensure_ascii=False)
        print(f"Licence générée avec succès dans : {args.output}")
        print(f"   Entreprise  : {args.client}")
        print(f"   Postes Max  : {args.max_postes} (Enregistrés: {len(fps)})")
        print(f"   Expiration  : {expires_str}")
        print(f"   Signature   : {license_data['signature'][:20]}...")
    except Exception as e:
        print(f"[ERREUR] Impossible d'écrire le fichier de licence : {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
